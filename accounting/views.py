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
import json
import re

from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Case, When, F, Q, Max, Count, BooleanField, \
    ExpressionWrapper
from django.db.models.functions import TruncMonth, Coalesce, Now
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _, gettext_noop
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import RedirectView, ListView, DetailView

from mia_core import stored_post
from mia_core.digest_auth import login_required
from mia_core.period import Period
from mia_core.utils import Pagination, get_multi_lingual_search, UrlBuilder, \
    strip_post, new_pk, PaginationException
from mia_core.views import DeleteView
from . import utils
from .forms import AccountForm, TransactionForm, RecordForm
from .models import Record, Transaction, Account


@method_decorator(require_GET, name="dispatch")
@method_decorator(login_required, name="dispatch")
class CashDefaultView(RedirectView):
    """The default cash account."""
    query_string = True
    pattern_name = "accounting:cash"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["account"] = utils.get_default_cash_account()
        kwargs["period"] = Period.default_spec()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
@login_required
def cash(request, account, period):
    """The cash account.

    Args:
        request (HttpRequest) The request.
        account (Account): The account.
        period (Period): The period.

    Returns:
        HttpResponse: The response.
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
                 Q(account__code__startswith="21"))) \
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
@method_decorator(login_required, name="dispatch")
class CashSummaryDefaultView(RedirectView):
    """The default cash account summary."""
    query_string = True
    pattern_name = "accounting:cash-summary"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["account"] = utils.get_default_cash_account()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
@login_required
def cash_summary(request, account):
    """The cash account summary.

    Args:
        request (HttpRequest) The request.
        account (Account): The account.

    Returns:
        HttpResponse: The response.
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
@method_decorator(login_required, name="dispatch")
class LedgerDefaultView(RedirectView):
    """The default ledger."""
    query_string = True
    pattern_name = "accounting:ledger"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["account"] = utils.get_default_ledger_account()
        kwargs["period"] = Period.default_spec()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
@login_required
def ledger(request, account, period):
    """The ledger.

    Args:
        request (HttpRequest) The request.
        account (Account): The account.
        period (Period): The period.

    Returns:
        HttpResponse: The response.
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
@method_decorator(login_required, name="dispatch")
class LedgerSummaryDefaultView(RedirectView):
    """The default ledger summary."""
    query_string = True
    pattern_name = "accounting:ledger-summary"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["account"] = utils.get_default_ledger_account()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
@login_required
def ledger_summary(request, account):
    """The ledger summary report.

    Args:
        request (HttpRequest) The request.
        account (Account): The account.

    Returns:
        HttpResponse: The response.
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
@method_decorator(login_required, name="dispatch")
class JournalDefaultView(RedirectView):
    """The default journal."""
    query_string = True
    pattern_name = "accounting:journal"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["period"] = Period.default_spec()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
@login_required
def journal(request, period):
    """The journal.

    Args:
        request (HttpRequest) The request.
        period (Period): The period.

    Returns:
        HttpResponse: The response.
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
@method_decorator(login_required, name="dispatch")
class TrialBalanceDefaultView(RedirectView):
    """The default trial balance."""
    query_string = True
    pattern_name = "accounting:trial-balance"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["period"] = Period.default_spec()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
@login_required
def trial_balance(request, period):
    """The trial balance.

    Args:
        request (HttpRequest) The request.
        period (Period): The period.

    Returns:
        HttpResponse: The response.
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
@method_decorator(login_required, name="dispatch")
class IncomeStatementDefaultView(RedirectView):
    """The default income statement."""
    query_string = True
    pattern_name = "accounting:income-statement"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["period"] = Period.default_spec()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
@login_required
def income_statement(request, period):
    """The income statement.

    Args:
        request (HttpRequest) The request.
        period (Period): The period.

    Returns:
        HttpResponse: The response.
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
@method_decorator(login_required, name="dispatch")
class BalanceSheetDefaultView(RedirectView):
    """The default balance sheet."""
    query_string = True
    pattern_name = "accounting:balance-sheet"

    def get_redirect_url(self, *args, **kwargs):
        kwargs["period"] = Period.default_spec()
        return super().get_redirect_url(*args, **kwargs)


@require_GET
@login_required
def balance_sheet(request, period):
    """The balance sheet.

    Args:
        request (HttpRequest) The request.
        period (Period): The period.

    Returns:
        HttpResponse: The response.
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
        account.url = reverse("accounting:ledger", args=(account, period))
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
            "accounting:income-statement", args=(period.period_before(),))
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
            "accounting:income-statement", args=(period,))
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


@require_GET
@login_required
def search(request):
    """The search.

    Args:
        request (HttpRequest) The request.

    Returns:
        HttpResponse: The response.
    """
    # The accounting records
    query = request.GET.get("q")
    if query is None:
        records = []
    else:
        records = Record.objects.filter(
            get_multi_lingual_search("account__title", query)
            | Q(account__code__icontains=query)
            | Q(summary__icontains=query)
            | Q(transaction__notes__icontains=query))
    try:
        pagination = Pagination(request, records, True)
    except PaginationException as e:
        return redirect(e.url)
    return render(request, "accounting/search.html", {
        "record_list": pagination.items,
        "pagination": pagination,
    })


@method_decorator(require_GET, name="dispatch")
@method_decorator(login_required, name="dispatch")
class TransactionView(DetailView):
    """The view of the details of an accounting transaction."""
    context_object_name = "txn"

    def get_object(self, queryset=None):
        return self.request.resolver_match.kwargs["txn"]

    def get_template_names(self):
        return ["accounting/transaction_detail-%s.html"
                % (self.request.resolver_match.kwargs["txn_type"],)]


@require_GET
@login_required
def txn_form(request, txn_type, txn=None):
    """The view to edit an accounting transaction.

    Args:
        request (HttpRequest): The request.
        txn_type (str): The transaction type.
        txn (Transaction): The transaction.

    Returns:
        HttpResponse: The response.
    """
    previous_post = stored_post.get_previous_post(request)
    if previous_post is not None:
        form = TransactionForm(previous_post)
    elif txn is not None:
        form = utils.make_txn_form_from_model(txn_type, txn)
    else:
        form = TransactionForm()
        form.debit_records.append(RecordForm())
        form.credit_records.append(RecordForm())
    form.transaction = txn
    form.txn_type = txn_type
    new_record_context = {"record": RecordForm(),
                          "record_type": "TTT",
                          "no": "NNN",
                          "order": ""}
    if txn_type == "transfer":
        new_record_template = json.dumps(render_to_string(
            "accounting/include/record_form-transfer.html",
            new_record_context))
    else:
        new_record_template = json.dumps(render_to_string(
            "accounting/include/record_form-non-transfer.html",
            new_record_context))
    return render(request, F"accounting/transaction_form-{txn_type}.html", {
        "form": form,
        "summary_categories": utils.get_summary_categories,
        "new_record_template": new_record_template,
    })


@require_POST
@login_required
def txn_store(request, txn_type, txn=None):
    """The view to store an accounting transaction.

    Args:
        request (HttpRequest): The request.
        txn_type (str): The transaction type.
        txn (Transaction): The transaction.

    Returns:
        HttpResponse: The response.
    """
    post = request.POST.dict()
    strip_post(post)
    utils.sort_post_txn_records(post)
    form = TransactionForm(post)
    form.transaction = txn
    form.txn_type = txn_type
    #form = utils.make_txn_form_from_post(post, txn_type, txn)
    if not form.is_valid():
        if txn is None:
            url = reverse("accounting:transactions.create", args=(txn_type,))
        else:
            url = reverse("accounting:transactions.edit", args=(txn_type, txn))
        url = str(UrlBuilder(url).query(r=request.GET.get("r")))
        return stored_post.error_redirect(request, url, post)

    if txn is None:
        txn = Transaction()
    old_date = txn.date
    utils.fill_txn_from_post(txn_type, txn, post)
    if not txn.is_dirty(check_relationship=True):
        messages.success(request, gettext_noop(
            "This transaction was not modified."))
        url = reverse("accounting:transactions.detail", args=(txn_type, txn))
        return redirect(str(UrlBuilder(url).query(r=request.GET.get("r"))))

    # Prepares the data
    user = request.user
    if txn.pk is None:
        txn.pk = new_pk(Transaction)
        txn.created_at = Now()
        txn.created_by = user
    txn.updated_at = Now()
    txn.updated_by = user
    txn_to_sort = []
    if txn.date != old_date:
        if old_date is not None:
            txn_same_day = list(
                Transaction.objects
                .filter(Q(date=old_date), ~Q(pk=txn.pk))
                .order_by("ord"))
            for i in range(len(txn_same_day)):
                txn_same_day[i].ord = i + 1
                if txn_same_day[i].is_dirty():
                    txn_to_sort.append(txn_same_day[i])
        max_ord = Transaction.objects\
            .filter(date=txn.date)\
            .aggregate(max=Max("ord"))["max"]
        txn.ord = 1 if max_ord is None else max_ord + 1
    for record in txn.records:
        if record.pk is None:
            record.pk = new_pk(Record)
            record.created_at = Now()
            record.created_by = user
        record.updated_at = Now()
        record.updated_by = user
    to_keep = [x.pk for x in txn.records if x.pk is not None]
    to_delete = [x for x in txn.record_set.all() if x.pk not in to_keep]
    # Runs the update
    with transaction.atomic():
        txn.save()
        for record in to_delete:
            record.delete()
        for record in txn.records:
            record.save()
        for x in txn_to_sort:
            x.save()
    messages.success(request, gettext_noop(
        "This transaction was saved successfully."))
    url = reverse("accounting:transactions.detail", args=(txn_type, txn))
    return redirect(str(UrlBuilder(url).query(r=request.GET.get("r"))))


@method_decorator(require_POST, name="dispatch")
@method_decorator(login_required, name="dispatch")
class TransactionDeleteView(DeleteView):
    """The view to delete an accounting transaction."""
    success_message = gettext_noop(
            "This transaction was deleted successfully.")

    def get_object(self, queryset=None):
        return self.request.resolver_match.kwargs["txn"]

    def get_success_url(self):
        return self.request.GET.get("r") or reverse("accounting:home")


@login_required
def txn_sort(request, date):
    """The view for the form to sort the transactions in a same day.

    Args:
        request (HttpRequest): The request.
        date (datetime.date): The day.

    Returns:
        HttpResponse: The response.

    Raises:
        Http404: When ther are less than two transactions in this day.
    """
    transactions = Transaction.objects.filter(date=date).order_by("ord")
    if len(transactions) < 2:
        raise Http404
    if request.method != "POST":
        return render(request, "accounting/transaction-sort.html", {
            "txn_list": transactions,
            "date": date,
        })
    else:
        post = request.POST.dict()
        errors = {}
        for txn in transactions:
            key = F"transaction-{txn.pk}-ord"
            if key not in post:
                errors[key] = gettext_noop("Invalid arguments.")
            elif not re.match("^[1-9][0-9]*", post[key]):
                errors[key] = gettext_noop("Invalid order.")

        if len(errors) > 0:
            return stored_post.error_redirect(
                request, reverse("accounting:transactions.sort"), post)

        keys = [F"transaction-{x.pk}-ord" for x in transactions]
        keys.sort(key=lambda x: int(post[x]))
        for i in range(len(keys)):
            post[keys[i]] = i + 1
        for txn in transactions:
            txn.ord = post[F"transaction-{txn.pk}-ord"]
        modified = [x for x in transactions if x.is_dirty()]

        if len(modified) == 0:
            messages.success(request, gettext_noop(
                "The transaction orders were not modified."))
            return redirect(request.GET.get("r") or reverse("accounting:home"))

        with transaction.atomic():
            for txn in modified:
                txn.save()
        messages.success(request, gettext_noop(
            "The transaction orders were saved successfully."))
        return redirect(request.GET.get("r") or reverse("accounting:home"))


@method_decorator(require_GET, name="dispatch")
@method_decorator(login_required, name="dispatch")
class AccountListView(ListView):
    """The view to list the accounts."""
    queryset = Account.objects\
        .annotate(child_count=Count("child_set"),
                  record_count=Count("record"))\
        .annotate(is_parent_and_in_use=ExpressionWrapper(
            Q(child_count__gt=0) & Q(record_count__gt=0),
            output_field=BooleanField()))\
        .order_by("code")


@method_decorator(require_GET, name="dispatch")
@method_decorator(login_required, name="dispatch")
class AccountView(DetailView):
    """The view of an account."""
    def get_object(self, queryset=None):
        return self.request.resolver_match.kwargs["account"]


@require_GET
@login_required
def account_form(request, account=None):
    """The view to edit an accounting transaction.

    Args:
        request (HttpRequest): The request.
        account (Account): The account.

    Returns:
        HttpResponse: The response.
    """
    previous_post = stored_post.get_previous_post(request)
    if previous_post is not None:
        form = AccountForm(previous_post)
    elif account is not None:
        form = AccountForm({
            "code": account.code,
            "title": account.title,
        })
    else:
        form = AccountForm()
    form.account = account
    return render(request, "accounting/account_form.html", {
        "form": form,
    })


@require_POST
@login_required
def account_store(request, account=None):
    """The view to store an account.

    Args:
        request (HttpRequest): The request.
        account (Account): The account.

    Returns:
        HttpResponseRedirect: The response.
    """
    post = request.POST.dict()
    strip_post(post)
    form = AccountForm(post)
    form.account = account
    if not form.is_valid():
        if account is None:
            url = reverse("accounting:accounts.create")
        else:
            url = reverse("accounting:accounts.edit", args=(account,))
        return stored_post.error_redirect(request, url, post)
    if account is None:
        account = Account()
    account.code = form["code"].value()
    account.title = form["title"].value()
    if not account.is_dirty():
        message = gettext_noop("This account was not modified.")
    else:
        account.save(current_user=request.user)
        message = gettext_noop("This account was saved successfully.")
    messages.success(request, message)
    return redirect("accounting:accounts.detail", account)


@require_POST
@login_required
def account_delete(request, account):
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
@login_required
def api_account_list(request):
    """The API view to return all the accounts.

    Args:
        request (HttpRequest): The request.

    Returns:
        JsonResponse: The response.
    """
    return JsonResponse({x.code: x.title for x in Account.objects.all()})


@require_GET
@login_required
def api_account_options(request):
    """The API view to return the account options.

    Args:
        request (HttpRequest): The request.

    Returns:
        JsonResponse: The response.
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
