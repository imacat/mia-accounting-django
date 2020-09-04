# The accounting application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/6/30

#  Copyright (c) 2020 imacat.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""The view controllers of the accounting application.

"""
import datetime
import json
import re
from decimal import Decimal
from typing import Dict, Optional, List

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Case, When, F, Q, Count, BooleanField, \
    ExpressionWrapper, Exists, OuterRef, Value, CharField
from django.db.models.functions import TruncMonth, Coalesce, Left, StrIndex
from django.http import JsonResponse, HttpResponseRedirect, Http404, \
    HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _, gettext_noop, gettext
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView, DetailView, TemplateView

from mia_core.period import Period
from mia_core.utils import Pagination, PaginationException, add_default_libs, \
    parse_date
from mia_core.views import DeleteView, FormView, RedirectView
from . import utils
from .forms import AccountForm, TransactionForm, TransactionSortForm
from .models import Record, Transaction, Account

add_default_libs("bootstrap4", "font-awesome-5", "i18n")


@method_decorator(require_GET, name="dispatch")
class CashDefaultView(RedirectView):
    """The default cash account."""
    query_string = True
    pattern_name = "accounting:cash"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["account"] = utils.get_default_cash_account()
        kwargs["period"] = Period.default_spec()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
def cash(request: HttpRequest, account: Account,
         period: Period) -> HttpResponse:
    """The cash account.

    Args:
        request: The request.
        account: The account.
        period: The period.

    Returns:
        The response.
    """
    # The accounting records
    if account.code == "0":
        records = list(
            Record.objects
            .filter(
                Q(transaction__in=Transaction.objects.filter(
                    Q(date__gte=period.start),
                    Q(date__lte=period.end),
                    (Q(record__account__code__startswith="11") |
                     Q(record__account__code__startswith="12") |
                     Q(record__account__code__startswith="21") |
                     Q(record__account__code__startswith="22")))),
                ~Q(account__code__startswith="11"),
                ~Q(account__code__startswith="12"),
                ~Q(account__code__startswith="21"),
                ~Q(account__code__startswith="22"))
            .order_by("transaction__date", "transaction__ord",
                      "is_credit", "ord"))
        balance_before = Record.objects \
            .filter(
                Q(transaction__date__lt=period.start),
                (Q(account__code__startswith="11") |
                 Q(account__code__startswith="12") |
                 Q(account__code__startswith="21") |
                 Q(account__code__startswith="22"))) \
            .aggregate(
                balance=Coalesce(Sum(Case(
                    When(is_credit=True, then=-1),
                    default=1) * F("amount")), 0))["balance"]
    else:
        records = list(
            Record.objects
            .filter(
                Q(transaction__in=Transaction.objects.filter(
                    Q(date__gte=period.start),
                    Q(date__lte=period.end),
                    Q(record__account__code__startswith=account.code))),
                ~Q(account__code__startswith=account.code))
            .order_by("transaction__date", "transaction__ord",
                      "is_credit", "ord"))
        balance_before = Record.objects \
            .filter(
                transaction__date__lt=period.start,
                account__code__startswith=account.code) \
            .aggregate(
                balance=Coalesce(Sum(Case(When(
                    is_credit=True, then=-1),
                    default=1) * F("amount")), 0))["balance"]
    balance = balance_before
    for record in records:
        sign = 1 if record.is_credit else -1
        balance = balance + sign * record.amount
        record.balance = balance
    record_sum = Record(
        transaction=(Transaction(date=records[-1].transaction.date)
                     if len(records) > 0
                     else Transaction(date=timezone.localdate())),
        account=account,
        summary=_("Total"),
    )
    record_sum.balance = balance
    record_sum.credit_amount = sum([
        x.amount for x in records if x.is_credit])
    record_sum.debit_amount = sum([
        x.amount for x in records if not x.is_credit])
    record_balance_before = Record(
        transaction=Transaction(date=period.start),
        account=Account.objects.get(code=Account.ACCUMULATED_BALANCE),
        is_credit=balance_before >= 0,
        amount=abs(balance_before),
    )
    record_balance_before.balance = balance_before
    records.insert(0, record_balance_before)
    records.append(record_sum)
    try:
        pagination = Pagination(request, records, True)
    except PaginationException as e:
        return redirect(e.url)
    records = pagination.items
    utils.find_imbalanced(records)
    utils.find_order_holes(records)
    accounts = utils.get_cash_accounts()
    shortcut_accounts = utils.get_cash_shortcut_accounts()
    return render(request, "accounting/report-cash.html", {
        "record_list": records,
        "pagination": pagination,
        "shortcut_accounts": [x for x in accounts
                              if x.code in shortcut_accounts],
        "all_accounts": [x for x in accounts
                         if x.code not in shortcut_accounts],
    })


@method_decorator(require_GET, name="dispatch")
class CashSummaryDefaultView(RedirectView):
    """The default cash account summary."""
    query_string = True
    pattern_name = "accounting:cash-summary"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["account"] = utils.get_default_cash_account()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
def cash_summary(request: HttpRequest, account: Account) -> HttpResponse:
    """The cash account summary.

    Args:
        request: The request.
        account: The account.

    Returns:
        The response.
    """
    # The account
    accounts = utils.get_cash_accounts()
    # The month summaries
    if account.code == "0":
        months = [utils.MonthlySummary(**x) for x in Record.objects
                  .filter(
                    Q(transaction__in=Transaction.objects.filter(
                        Q(record__account__code__startswith="11") |
                        Q(record__account__code__startswith="12") |
                        Q(record__account__code__startswith="21") |
                        Q(record__account__code__startswith="22"))),
                    ~Q(account__code__startswith="11"),
                    ~Q(account__code__startswith="12"),
                    ~Q(account__code__startswith="21"),
                    ~Q(account__code__startswith="22"))
                  .annotate(month=TruncMonth("transaction__date"))
                  .values("month")
                  .order_by("month")
                  .annotate(
                    debit=Coalesce(
                        Sum(Case(When(is_credit=False, then=F("amount")))),
                        0),
                    credit=Coalesce(
                        Sum(Case(When(is_credit=True, then=F("amount")))),
                        0),
                    balance=Sum(Case(
                        When(is_credit=False, then=-F("amount")),
                        default=F("amount"))))]
    else:
        months = [utils.MonthlySummary(**x) for x in Record.objects
                  .filter(
                    Q(transaction__in=Transaction.objects.filter(
                        record__account__code__startswith=account.code)),
                    ~Q(account__code__startswith=account.code))
                  .annotate(month=TruncMonth("transaction__date"))
                  .values("month")
                  .order_by("month")
                  .annotate(
                    debit=Coalesce(
                        Sum(Case(When(is_credit=False, then=F("amount")))),
                        0),
                    credit=Coalesce(
                        Sum(Case(When(is_credit=True, then=F("amount")))),
                        0),
                    balance=Sum(Case(
                        When(is_credit=False, then=-F("amount")),
                        default=F("amount"))))]
    cumulative_balance = 0
    for month in months:
        cumulative_balance = cumulative_balance + month.balance
        month.cumulative_balance = cumulative_balance
    months.append(utils.MonthlySummary(
        label=_("Total"),
        credit=sum([x.credit for x in months]),
        debit=sum([x.debit for x in months]),
        balance=sum([x.balance for x in months]),
        cumulative_balance=cumulative_balance,
    ))
    try:
        pagination = Pagination(request, months, True)
    except PaginationException as e:
        return redirect(e.url)
    shortcut_accounts = utils.get_cash_shortcut_accounts()
    return render(request, "accounting/report-cash-summary.html", {
        "month_list": pagination.items,
        "pagination": pagination,
        "shortcut_accounts": [x for x in accounts if
                              x.code in shortcut_accounts],
        "all_accounts": [x for x in accounts if
                         x.code not in shortcut_accounts],
    })


@method_decorator(require_GET, name="dispatch")
class LedgerDefaultView(RedirectView):
    """The default ledger."""
    query_string = True
    pattern_name = "accounting:ledger"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["account"] = utils.get_default_ledger_account()
        kwargs["period"] = Period.default_spec()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
def ledger(request: HttpRequest, account: Account,
           period: Period) -> HttpResponse:
    """The ledger.

    Args:
        request: The request.
        account: The account.
        period: The period.

    Returns:
        The response.
    """
    # The accounting records
    records = list(
        Record.objects
        .filter(
            transaction__date__gte=period.start,
            transaction__date__lte=period.end,
            account__code__startswith=account.code)
        .order_by("transaction__date", "transaction__ord", "is_credit",
                  "ord"))
    if re.match("^[1-3]", account.code) is not None:
        balance = Record.objects \
            .filter(
                transaction__date__lt=period.start,
                account__code__startswith=account.code) \
            .aggregate(
                balance=Coalesce(Sum(Case(When(
                    is_credit=True, then=-1),
                    default=1) * F("amount")), 0))["balance"]
        record_brought_forward = Record(
            transaction=Transaction(date=period.start),
            account=account,
            summary=_("Brought Forward"),
            is_credit=balance < 0,
            amount=abs(balance),
        )
        record_brought_forward.balance = balance
    else:
        balance = 0
        record_brought_forward = None
    for record in records:
        balance = balance + \
                  (-1 if record.is_credit else 1) * record.amount
        record.balance = balance
    if record_brought_forward is not None:
        records.insert(0, record_brought_forward)
    try:
        pagination = Pagination(request, records, True)
    except PaginationException as e:
        return redirect(e.url)
    records = pagination.items
    utils.find_imbalanced(records)
    utils.find_order_holes(records)
    utils.find_payable_records(account, records)
    utils.find_existing_equipments(account, records)
    return render(request, "accounting/report-ledger.html", {
        "record_list": records,
        "pagination": pagination,
        "accounts": utils.get_ledger_accounts(),
    })


@method_decorator(require_GET, name="dispatch")
class LedgerSummaryDefaultView(RedirectView):
    """The default ledger summary."""
    query_string = True
    pattern_name = "accounting:ledger-summary"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["account"] = utils.get_default_ledger_account()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
def ledger_summary(request: HttpRequest, account: Account) -> HttpResponse:
    """The ledger summary report.

    Args:
        request: The request.
        account: The account.

    Returns:
        The response.
    """
    # The month summaries
    months = [utils.MonthlySummary(**x) for x in Record.objects
              .filter(account__code__startswith=account.code)
              .annotate(month=TruncMonth("transaction__date"))
              .values("month")
              .order_by("month")
              .annotate(
                    debit=Coalesce(
                        Sum(Case(When(is_credit=False, then=F("amount")))),
                        0),
                    credit=Coalesce(
                        Sum(Case(When(is_credit=True, then=F("amount")))),
                        0),
                    balance=Sum(Case(
                        When(is_credit=False, then=F("amount")),
                        default=-F("amount"))))]
    cumulative_balance = 0
    for month in months:
        cumulative_balance = cumulative_balance + month.balance
        month.cumulative_balance = cumulative_balance
    months.append(utils.MonthlySummary(
        label=_("Total"),
        credit=sum([x.credit for x in months]),
        debit=sum([x.debit for x in months]),
        balance=sum([x.balance for x in months]),
        cumulative_balance=cumulative_balance,
    ))
    try:
        pagination = Pagination(request, months, True)
    except PaginationException as e:
        return redirect(e.url)
    return render(request, "accounting/report-ledger-summary.html", {
        "month_list": pagination.items,
        "pagination": pagination,
        "accounts": utils.get_ledger_accounts(),
    })


@method_decorator(require_GET, name="dispatch")
class JournalDefaultView(RedirectView):
    """The default journal."""
    query_string = True
    pattern_name = "accounting:journal"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["period"] = Period.default_spec()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
def journal(request: HttpRequest, period: Period) -> HttpResponse:
    """The journal.

    Args:
        request: The request.
        period: The period.

    Returns:
        The response.
    """
    # The accounting records
    records = Record.objects \
        .filter(
            transaction__date__gte=period.start,
            transaction__date__lte=period.end) \
        .order_by("transaction__date", "transaction__ord", "is_credit", "ord")
    # The brought-forward records
    brought_forward_accounts = Account.objects \
        .filter(
            Q(code__startswith="1")
            | Q(code__startswith="2")
            | Q(code__startswith="3")) \
        .annotate(balance=Sum(
            Case(
                When(record__is_credit=True, then=-1),
                default=1
            ) * F("record__amount"),
            filter=Q(record__transaction__date__lt=period.start))) \
        .filter(~Q(balance=0))
    debit_records = [Record(
        transaction=Transaction(date=period.start),
        account=x,
        is_credit=False,
        amount=x.balance
    ) for x in brought_forward_accounts if x.balance > 0]
    credit_records = [Record(
        transaction=Transaction(date=period.start),
        account=x,
        is_credit=True,
        amount=-x.balance
    ) for x in brought_forward_accounts if x.balance < 0]
    sum_debits = sum([x.amount for x in debit_records])
    sum_credits = sum([x.amount for x in credit_records])
    if sum_debits < sum_credits:
        debit_records.append(Record(
            transaction=Transaction(date=period.start),
            account=Account.objects.get(code=Account.ACCUMULATED_BALANCE),
            is_credit=False,
            amount=sum_credits - sum_debits
        ))
    elif sum_debits > sum_credits:
        credit_records.append(Record(
            transaction=Transaction(date=period.start),
            account=Account.objects.get(code=Account.ACCUMULATED_BALANCE),
            is_credit=True,
            amount=sum_debits - sum_credits
        ))
    records = list(debit_records) + list(credit_records) + list(records)
    try:
        pagination = Pagination(request, records, True)
    except PaginationException as e:
        return redirect(e.url)
    return render(request, "accounting/report-journal.html", {
        "record_list": pagination.items,
        "pagination": pagination,
    })


@method_decorator(require_GET, name="dispatch")
class TrialBalanceDefaultView(RedirectView):
    """The default trial balance."""
    query_string = True
    pattern_name = "accounting:trial-balance"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["period"] = Period.default_spec()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
def trial_balance(request: HttpRequest, period: Period) -> HttpResponse:
    """The trial balance.

    Args:
        request: The request.
        period: The period.

    Returns:
        The response.
    """
    # The accounts
    nominal = list(
        Account.objects
        .filter(
            Q(record__transaction__date__gte=period.start),
            Q(record__transaction__date__lte=period.end),
            ~(Q(code__startswith="1")
              | Q(code__startswith="2")
              | Q(code__startswith="3")))
        .annotate(
            amount=Sum(Case(
                When(record__is_credit=True, then=-1),
                default=1) * F("record__amount")))
        .filter(Q(amount__isnull=False), ~Q(amount=0))
        .annotate(
            debit_amount=Case(
                When(amount__gt=0, then=F("amount")),
                default=None),
            credit_amount=Case(
                When(amount__lt=0, then=-F("amount")),
                default=None))
        .order_by("code"))
    real = list(
        Account.objects
        .filter(
            Q(record__transaction__date__lte=period.end),
            (Q(code__startswith="1")
             | Q(code__startswith="2")
             | Q(code__startswith="3")),
            ~Q(code=Account.ACCUMULATED_BALANCE))
        .annotate(
            amount=Sum(Case(
                When(record__is_credit=True, then=-1),
                default=1) * F("record__amount")))
        .filter(Q(amount__isnull=False), ~Q(amount=0))
        .annotate(
            debit_amount=Case(
                When(amount__gt=0, then=F("amount")),
                default=None),
            credit_amount=Case(
                When(amount__lt=0, then=-F("amount")),
                default=None))
        .order_by("code"))
    balance = Record.objects \
        .filter(
            (Q(transaction__date__lt=period.start)
             & ~(Q(account__code__startswith="1")
                 | Q(account__code__startswith="2")
                 | Q(account__code__startswith="3")))
            | (Q(transaction__date__lte=period.end)
               & Q(account__code=Account.ACCUMULATED_BALANCE))) \
        .aggregate(
            balance=Sum(Case(
                When(is_credit=True, then=-1),
                default=1) * F("amount")))["balance"]
    if balance is not None and balance != 0:
        brought_forward = Account.objects.get(
            code=Account.ACCUMULATED_BALANCE)
        if balance > 0:
            brought_forward.debit_amount = balance
            brought_forward.credit_amount = None
        else:
            brought_forward.debit_amount = None
            brought_forward.credit_amount = -balance
        real.append(brought_forward)
    accounts = nominal + real
    accounts.sort(key=lambda x: x.code)
    total_account = Account()
    total_account.title = _("Total")
    total_account.debit_amount = sum([x.debit_amount for x in accounts
                                      if x.debit_amount is not None])
    total_account.credit_amount = sum([x.credit_amount for x in accounts
                                       if x.credit_amount is not None])
    return render(request, "accounting/report-trial-balance.html", {
        "account_list": accounts,
        "total_item": total_account,
    })


@method_decorator(require_GET, name="dispatch")
class IncomeStatementDefaultView(RedirectView):
    """The default income statement."""
    query_string = True
    pattern_name = "accounting:income-statement"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["period"] = Period.default_spec()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
def income_statement(request: HttpRequest, period: Period) -> HttpResponse:
    """The income statement.

    Args:
        request: The request.
        period: The period.

    Returns:
        The response.
    """
    # The accounts
    accounts = list(
        Account.objects
        .filter(
            Q(record__transaction__date__gte=period.start),
            Q(record__transaction__date__lte=period.end),
            ~(Q(code__startswith="1")
              | Q(code__startswith="2")
              | Q(code__startswith="3")))
        .annotate(
            amount=Sum(Case(
                When(record__is_credit=True, then=1),
                default=-1) * F("record__amount")))
        .filter(Q(amount__isnull=False), ~Q(amount=0))
        .order_by("code"))
    groups = list(Account.objects.filter(
        code__in=[x.code[:2] for x in accounts]))
    sections = list(Account.objects.filter(
        Q(code="4") | Q(code="5") | Q(code="6")
        | Q(code="7") | Q(code="8") | Q(code="9")).order_by("code"))
    cumulative_accounts = {
        "5": Account(title=_("Gross Income")),
        "6": Account(title=_("Operating Income")),
        "7": Account(title=_("Before Tax Income")),
        "8": Account(title=_("After Tax Income")),
        "9": Account.objects.get(code=Account.NET_CHANGE),
    }
    cumulative_total = 0
    for section in sections:
        section.groups = [x for x in groups
                          if x.code[:1] == section.code]
        for group in section.groups:
            group.details = [x for x in accounts
                             if x.code[:2] == group.code]
            group.amount = sum([x.amount
                                for x in group.details])
        section.amount = sum([x.amount for x in section.groups])
        cumulative_total = cumulative_total + section.amount
        if section.code in cumulative_accounts:
            section.cumulative_total \
                = cumulative_accounts[section.code]
            section.cumulative_total.amount = cumulative_total
        else:
            section.cumulative_total = None
        section.has_next = True
    sections[-1].has_next = False
    return render(request, "accounting/report-income-statement.html", {
        "section_list": sections,
    })


@method_decorator(require_GET, name="dispatch")
class BalanceSheetDefaultView(RedirectView):
    """The default balance sheet."""
    query_string = True
    pattern_name = "accounting:balance-sheet"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["period"] = Period.default_spec()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
def balance_sheet(request: HttpRequest, period: Period) -> HttpResponse:
    """The balance sheet.

    Args:
        request: The request.
        period: The period.

    Returns:
        The response.
    """
    # The accounts
    accounts = list(
        Account.objects
        .filter(
            Q(record__transaction__date__lte=period.end),
            (Q(code__startswith="1")
             | Q(code__startswith="2")
             | Q(code__startswith="3")),
            ~Q(code=Account.ACCUMULATED_BALANCE))
        .annotate(
            amount=Sum(Case(
                When(record__is_credit=True, then=-1),
                default=1) * F("record__amount")))
        .filter(Q(amount__isnull=False), ~Q(amount=0))
        .order_by("code"))
    for account in accounts:
        account.url = reverse("accounting:ledger", args=[account, period],
                              current_app=request.resolver_match.namespace)
    balance = Record.objects \
        .filter(
            Q(transaction__date__lt=period.start)
            & ~((Q(account__code__startswith="1")
                 | Q(account__code__startswith="2")
                 | Q(account__code__startswith="3"))
                & ~Q(account__code=Account.ACCUMULATED_BALANCE))) \
        .aggregate(
            balance=Sum(Case(
                When(is_credit=True, then=-1),
                default=1) * F("amount")))["balance"]
    if balance is not None and balance != 0:
        brought_forward = Account.objects.get(
            code=Account.ACCUMULATED_BALANCE)
        brought_forward.amount = balance
        brought_forward.url = reverse(
            "accounting:income-statement", args=[period.period_before()],
            current_app=request.resolver_match.namespace)
        accounts.append(brought_forward)
    balance = Record.objects \
        .filter(
            Q(transaction__date__gte=period.start)
            & Q(transaction__date__lte=period.end)
            & ~((Q(account__code__startswith="1")
                 | Q(account__code__startswith="2")
                 | Q(account__code__startswith="3"))
                & ~Q(account__code=Account.ACCUMULATED_BALANCE))) \
        .aggregate(
            balance=Sum(Case(
                When(is_credit=True, then=-1),
                default=1) * F("amount")))["balance"]
    if balance is not None and balance != 0:
        net_change = Account.objects.get(code=Account.NET_CHANGE)
        net_change.amount = balance
        net_change.url = reverse(
            "accounting:income-statement", args=[period],
            current_app=request.resolver_match.namespace)
        accounts.append(net_change)
    for account in [x for x in accounts if x.code[0] in "23"]:
        account.amount = -account.amount
    groups = list(Account.objects.filter(
        code__in=[x.code[:2] for x in accounts]))
    sections = list(Account.objects.filter(
        Q(code="1") | Q(code="2") | Q(code="3")).order_by("code"))
    for section in sections:
        section.groups = [x for x in groups
                          if x.code[:1] == section.code]
        for group in section.groups:
            group.details = [x for x in accounts
                             if x.code[:2] == group.code]
            group.amount = sum([x.amount
                                for x in group.details])
        section.amount = sum([x.amount for x in section.groups])
    by_code = {x.code: x for x in sections}
    return render(request, "accounting/report-balance-sheet.html", {
        "assets": by_code["1"],
        "liabilities": by_code["2"],
        "owners_equity": by_code["3"],
    })


@method_decorator(require_GET, name="dispatch")
class SearchListView(TemplateView):
    """The search."""
    template_name = "accounting/search.html"

    def get_context_data(self, **kwargs):
        records = self._get_records()
        try:
            pagination = Pagination(self.request, records, True)
        except PaginationException as e:
            return redirect(e.url)
        context = super().get_context_data(**kwargs)
        context["record_list"] = pagination.items
        context["pagination"] = pagination
        return context

    def _get_records(self) -> List[Record]:
        """Returns the search result."""
        query = self.request.GET.get("q")
        if query is None:
            return []
        terms = self._parse_search_terms(query)
        if len(terms) == 0:
            return []
        conditions = [self._get_conditions_for_term(x) for x in terms]
        if len(conditions) == 1:
            return Record.objects.filter(conditions[0])
        combined = conditions[0]
        for x in conditions[1:]:
            combined = combined & x
        return Record.objects.filter(combined)

    @staticmethod
    def _get_conditions_for_term(term: str) -> Q:
        """Returns the search conditions for a term.

        Args:
            term: The term.

        Returns:
            The search conditions for this term.
        """
        conditions =\
            Q(account__in=Account.objects.filter(
                Q(title_l10n__icontains=term)
                | Q(l10n_set__value__icontains=term)
                | Q(code=term)))\
            | Q(summary__icontains=term)\
            | Q(transaction__notes__icontains=term)
        if re.match("^[0-9]+(?:\\.[0-9]+)?$", term):
            conditions = conditions | Q(amount=Decimal(term))
        if re.match("^[1-9][0-8]{9}$", term):
            conditions = conditions\
                         | Q(pk=int(term))\
                         | Q(transaction__pk=int(term))\
                         | Q(account__pk=int(term))
        try:
            conditions = conditions | Q(transaction__date=parse_date(term))
        except ValueError:
            pass
        try:
            date = datetime.datetime.strptime(term, "%Y")
            conditions = conditions\
                         | Q(transaction__date__year=date.year)
        except ValueError:
            pass
        try:
            date = datetime.datetime.strptime(term, "%Y/%m")
            conditions = conditions\
                         | (Q(transaction__date__year=date.year)
                            & Q(transaction__date__month=date.month))
        except ValueError:
            pass
        try:
            date = datetime.datetime.strptime(term, "%m/%d")
            conditions = conditions\
                         | (Q(transaction__date__month=date.month)
                            & Q(transaction__date__day=date.day))
        except ValueError:
            pass
        return conditions

    @staticmethod
    def _parse_search_terms(query: str) -> List[str]:
        """Parses the search query and returns the search terms.  The search
        terms are separated by spaces but quoted with double quotes.

        Args:
            query: The search query

        Returns:
            The search terms.
        """
        query = query.strip()
        terms = []
        while True:
            m = re.match("^([^\"\\s]+)\\s*(.*)$", query)
            if m is not None:
                terms.append(m[1])
                query = m[2]
                continue
            m = re.match("^\"([^\"]*)\"\\s*(.*)$", query)
            if m is not None:
                if m[1] != "":
                    terms.append(m[1])
                query = m[2]
                continue
            m = re.match("^\"([^\"]*)", query)
            if m is not None:
                if m[1] != "":
                    terms.append(m[1])
            break
        return terms


@method_decorator(require_GET, name="dispatch")
class TransactionView(DetailView):
    """The view of the details of an accounting transaction."""
    context_object_name = "txn"

    def get_object(self, queryset=None):
        return self.kwargs["txn"]

    def get_template_names(self):
        model_name = self.object.__class__.__name__.lower()
        txn_type = self.kwargs["txn_type"]
        return [F"accounting/{model_name}_{txn_type}_detail.html"]


class TransactionFormView(FormView):
    """The form to create or update an accounting transaction."""
    model = Transaction
    form_class = TransactionForm
    not_modified_message = gettext_noop("This transaction was not modified.")
    success_message = gettext_noop("This transaction was saved successfully.")
    DEFAULT_REGULAR_ACCOUNTS = {
        "debit": [
            (gettext_noop("Pension"),
             gettext_noop("Pension for (last_month_name)"),
             "1314"),
            (gettext_noop("Health insurance"),
             gettext_noop("Health insurance for (last_month_name)"),
             "6262"),
            (gettext_noop("Electricity bill"),
             gettext_noop("Electricity bill for (last_bimonthly_from_name)"
                          "-(last_bimonthly_to_name)"),
             "6261"),
            (gettext_noop("Water bill"),
             gettext_noop("Water bill for (last_bimonthly_from_name)"
                          "-(last_bimonthly_to_name)"),
             "6261"),
            (gettext_noop("Gas bill"),
             gettext_noop("Gas bill for (last_bimonthly_from_name)"
                          "-(last_bimonthly_to_name)"),
             "6261"),
            (gettext_noop("Phone bill"),
             gettext_noop("Phone bill for (last_month_name)"),
             "6261"),
        ],
        "credit": [
            (gettext_noop("Payroll"),
             gettext_noop("Payroll for (last_month_name)"),
             "4611"),
        ],
    }

    def get_context_data(self, **kwargs):
        """Returns the context data for the template."""
        context = super().get_context_data(**kwargs)
        context["summary_categories"] = self._get_summary_categories()
        context["regular_accounts"] = self._get_regular_accounts()
        context["new_record_template"] = self._get_new_record_template_json()
        return context

    @staticmethod
    def _get_summary_categories() -> str:
        """Finds and returns the summary categories and their corresponding
        account hints as JSON.

        Returns:
            The summary categories and their account hints, by their record
            types and category types.
        """
        rows = Record.objects \
            .filter(Q(summary__contains="—"),
                    ~Q(account__code__startswith="114"),
                    ~Q(account__code__startswith="214"),
                    ~Q(account__code__startswith="128"),
                    ~Q(account__code__startswith="228")) \
            .annotate(rec_type=Case(When(is_credit=True, then=Value("credit")),
                                    default=Value("debit"),
                                    output_field=CharField()),
                      cat_type=Case(
                          When(summary__regex=".+—.+—.+→.+",
                               then=Value("bus")),
                          When(summary__regex=".+—.+[→↔].+",
                               then=Value("travel")),
                          default=Value("general"),
                          output_field=CharField()),
                      category=Left("summary",
                                    StrIndex("summary", Value("—")) - 1,
                                    output_field=CharField())) \
            .values("rec_type", "cat_type", "category", "account__code") \
            .annotate(count=Count("category")) \
            .order_by("rec_type", "cat_type", "category", "-count",
                      "account__code")
        # Sorts the rows by the record type and the category type
        categories = {}
        for row in rows:
            key = "%s-%s" % (row["rec_type"], row["cat_type"])
            if key not in categories:
                categories[key] = {}
            if row["category"] not in categories[key]:
                categories[key][row["category"]] = []
            categories[key][row["category"]].append(row)
        for key in categories:
            # Keeps only the first account with most records
            categories[key] = [categories[key][x][0] for x in categories[key]]
            # Sorts the categories by the frequency
            categories[key].sort(key=lambda x: (-x["count"], x["category"]))
            # Keeps only the category and the account
            categories[key] = [[x["category"], x["account__code"]]
                               for x in categories[key]]
        # Converts the dictionary to a list, as the category may not be
        # US-ASCII
        return json.dumps(categories)

    @staticmethod
    def _get_regular_accounts() -> str:
        """Returns the regular account data, as JSON.

        Returns:
            Two lists of the (title, format pattern, account code) tuple,
            sorted by debit or credit.
        """
        try:
            regular = settings.REGULAR_ACCOUNTS
            regular = {t: [{"title": x[0],
                            "format": x[1],
                            "account": x[2]} for x in regular[t]]
                       for t in regular}
        except AttributeError:
            regular = TransactionFormView.DEFAULT_REGULAR_ACCOUNTS
            regular = {t: [{"title": gettext(x[0]),
                            "format": gettext(x[1]),
                            "account": x[2]} for x in regular[t]]
                       for t in regular}
        return json.dumps(regular)

    def _get_new_record_template_json(self) -> str:
        context = {"record_type": "TTT", "no": "NNN"}
        template_name = "accounting/include/record_form-transfer.html"\
            if self.txn_type == "transfer"\
            else "accounting/include/record_form-non-transfer.html"
        return json.dumps(render_to_string(template_name, context))

    def get_template_name(self) -> str:
        """Returns the name of the template."""
        model_name = self.model.__name__.lower()
        return F"accounting/{model_name}_{self.txn_type}_form.html"

    def make_form_from_post(self, post: Dict[str, str]) -> TransactionForm:
        """Creates and returns the form from the POST data."""
        return TransactionForm.from_post(post, self.txn_type, self.object)

    def make_form_from_model(self, obj: Transaction) -> TransactionForm:
        """Creates and returns the form from a data model."""
        return TransactionForm.from_model(obj, self.txn_type)

    def fill_model_from_form(self, obj: Transaction,
                             form: TransactionForm) -> None:
        """Fills in the data model from the form."""
        obj.fill_from_post(form.data, self.request, self.txn_type)

    def get_object(self) -> Optional[Account]:
        """Returns the current object, or None on a create form."""
        return self.kwargs.get("txn")

    def get_success_url(self) -> str:
        """Returns the URL on success."""
        return reverse("accounting:transactions.detail",
                       args=[self.txn_type, self.object],
                       current_app=self.request.resolver_match.namespace)

    @property
    def txn_type(self) -> str:
        """Returns the transaction type of this form."""
        return self.kwargs["txn_type"]


@method_decorator(require_POST, name="dispatch")
class TransactionDeleteView(DeleteView):
    """The view to delete an accounting transaction."""
    success_message = gettext_noop(
            "This transaction was deleted successfully.")

    def get_object(self, queryset=None):
        return self.kwargs["txn"]

    def get_success_url(self):
        return self.request.GET.get("r")\
               or reverse("accounting:home",
                          current_app=self.request.resolver_match.namespace)


class TransactionSortFormView(FormView):
    """The form to sort the transactions in a same day."""
    template_name = "accounting/transaction_sort_form.html"
    form_class = TransactionSortForm
    not_modified_message = gettext_noop(
        "The transaction orders were not modified.")
    success_message = gettext_noop(
        "The transaction orders were saved successfully.")

    def get_form(self, **kwargs):
        """Returns the form for the template."""
        form = super().get_form()
        if form.txn_list is None:
            form.date = self.kwargs["date"]
            form.txn_list = Transaction.objects.filter(date=form.date)\
                .order_by("ord").all()
        if len(form.txn_list) < 2:
            raise Http404
        return form

    def make_form_from_post(self, post: Dict[str, str]) -> TransactionSortForm:
        """Creates and returns the form from the POST data."""
        return TransactionSortForm.from_post(self.kwargs["date"], post)

    def form_valid(self, form: TransactionSortForm) -> HttpResponseRedirect:
        """Handles the action when the POST form is valid."""
        modified = [x for x in form.txn_orders if x.txn.ord != x.order]
        if len(modified) == 0:
            message = self.get_not_modified_message(form.cleaned_data)
        else:
            with transaction.atomic():
                for x in modified:
                    Transaction.objects.filter(pk=x.txn.pk).update(ord=x.order)
            message = self.get_success_message(form.cleaned_data)
        messages.success(self.request, message)
        return redirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Returns the URL on success."""
        return self.request.GET.get("r")\
            or reverse("accounting:home",
                       current_app=self.request.resolver_match.namespace)


@method_decorator(require_GET, name="dispatch")
class AccountListView(ListView):
    """The view to list the accounts."""
    queryset = Account.objects\
        .annotate(is_parent_and_in_use=ExpressionWrapper(
            Exists(Account.objects.filter(parent=OuterRef("pk")))
            & Exists(Record.objects.filter(account=OuterRef("pk"))),
            output_field=BooleanField()))\
        .order_by("code")


@method_decorator(require_GET, name="dispatch")
class AccountView(DetailView):
    """The view of an account."""
    def get_object(self, queryset=None):
        return self.kwargs["account"]


class AccountFormView(FormView):
    """The form to create or update an account."""
    model = Account
    form_class = AccountForm
    not_modified_message = gettext_noop("This account was not modified.")
    success_message = gettext_noop("This account was saved successfully.")

    def make_form_from_post(self, post: Dict[str, str]) -> AccountForm:
        """Creates and returns the form from the POST data."""
        form = AccountForm(post)
        form.account = self.object
        return form

    def make_form_from_model(self, obj: Account) -> AccountForm:
        """Creates and returns the form from a data model."""
        form = AccountForm({
            "code": obj.code,
            "title": obj.title,
        })
        form.account = obj
        return form

    def get_object(self) -> Optional[Account]:
        """Returns the current object, or None on a create form."""
        return self.kwargs.get("account")

    def get_success_url(self) -> str:
        """Returns the URL on success."""
        return reverse("accounting:accounts.detail", args=[self.object],
                       current_app=self.request.resolver_match.namespace)


@require_POST
def account_delete(request: HttpRequest,
                   account: Account) -> HttpResponseRedirect:
    """The view to delete an account.

    Args:
        request (HttpRequest): The request.
        account (Account): The account.

    Returns:
        HttpResponseRedirect: The response.
    """
    if account.is_in_use:
        message = gettext_noop("This account is in use.")
        messages.error(request, message)
        return redirect("accounting:accounts.detail", account)
    account.delete()
    message = gettext_noop("This account was deleted successfully.")
    messages.success(request, message)
    return redirect("accounting:accounts")


@require_GET
def api_account_list(request: HttpRequest) -> JsonResponse:
    """The API view to return all the accounts.

    Args:
        request: The request.

    Returns:
        The response.
    """
    return JsonResponse({x.code: x.title for x in Account.objects.all()})


@require_GET
def api_account_options(request: HttpRequest) -> JsonResponse:
    """The API view to return the account options.

    Args:
        request: The request.

    Returns:
        The response.
    """
    accounts = Account.objects\
        .annotate(children_count=Count("child_set"))\
        .filter(children_count=0)\
        .annotate(record_count=Count("record"))\
        .annotate(is_in_use=Case(
            When(record_count__gt=0, then=True),
            default=False,
            output_field=BooleanField()))\
        .order_by("code")
    for x in accounts:
        x.is_for_debit = re.match("^([1235689]|7[5678])", x.code) is not None
        x.is_for_credit = re.match("^([123489]|7[1234])", x.code) is not None
    return JsonResponse({
        "header_in_use": _("---Accounts In Use---"),
        "debit_in_use": [x.option_data for x in accounts
                         if x.is_for_debit and x.is_in_use],
        "credit_in_use": [x.option_data for x in accounts
                          if x.is_for_credit and x.is_in_use],
        "header_not_in_use": _("---Accounts Not In Use---"),
        "debit_not_in_use": [x.option_data for x in accounts
                             if x.is_for_debit and not x.is_in_use],
        "credit_not_in_use": [x.option_data for x in accounts
                              if x.is_for_credit and not x.is_in_use],
    })
