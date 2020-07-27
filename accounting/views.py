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
import re

from django.conf import settings
from django.db.models import Sum, Case, When, F, Q
from django.db.models.functions import TruncMonth, Coalesce
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import dateformat, timezone
from django.utils.translation import pgettext
from django.views.decorators.http import require_GET

from .models import Record, Transaction, Account, RecordSummary
from .utils import ReportUrl, get_cash_accounts, get_ledger_accounts, \
    find_imbalanced, find_order_holes
from mia_core.digest_auth import digest_login_required
from mia_core.period import Period
from mia_core.utils import Pagination, get_multi_lingual_search


# noinspection PyUnusedLocal
@require_GET
@digest_login_required
def home(request):
    """The accounting home page.

    Args:
        request (HttpRequest) The request.

    Returns:
        HttpResponseRedirect: The redirection to the default
            accounting report.
    """
    return HttpResponseRedirect(reverse("accounting:cash.home"))


# noinspection PyUnusedLocal
@require_GET
@digest_login_required
def cash_default(request):
    """The default cash account.

    Args:
        request (HttpRequest) The request.

    Returns:
        HttpResponseRedirect: The redirection to the default account
            and month.
    """
    account = Account.objects.get(
        code=settings.ACCOUNTING["DEFAULT_CASH_ACCOUNT"])
    period_spec = dateformat.format(timezone.localdate(), "Y-m")
    return HttpResponseRedirect(
        reverse("accounting:cash", args=(account, period_spec)))


@require_GET
@digest_login_required
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
        balance_before = Record.objects\
            .filter(
                Q(transaction__date__lt=period.start),
                (Q(account__code__startswith="11") |
                 Q(account__code__startswith="12") |
                 Q(account__code__startswith="21") |
                 Q(account__code__startswith="21")))\
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
        balance_before = Record.objects\
            .filter(
                transaction__date__lt=period.start,
                account__code__startswith=account.code)\
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
        transaction=Transaction(date=records[-1].transaction.date),
        account=account,
        summary=pgettext("Accounting|", "Total"),
        balance=balance
    )
    record_sum.credit_amount = sum([
        x.amount for x in records if x.is_credit])
    record_sum.debit_amount = sum([
        x.amount for x in records if not x.is_credit])
    records.insert(0, Record(
        transaction=Transaction(date=period.start),
        account=Account.objects.get(code="3351"),
        is_credit=balance_before >= 0,
        amount=abs(balance_before),
        balance=balance_before))
    records.append(record_sum)
    pagination = Pagination(request, records, True)
    records = pagination.items
    find_imbalanced(records)
    find_order_holes(records)
    accounts = get_cash_accounts()
    shortcut_accounts = settings.ACCOUNTING["CASH_SHORTCUT_ACCOUNTS"]
    return render(request, "accounting/cash.html", {
        "item_list": records,
        "pagination": pagination,
        "account": account,
        "period": period,
        "reports": ReportUrl(cash=account, period=period),
        "shortcut_accounts": [x for x in accounts
                              if x.code in shortcut_accounts],
        "all_accounts": [x for x in accounts
                         if x.code not in shortcut_accounts],
    })


# noinspection PyUnusedLocal
@require_GET
@digest_login_required
def cash_summary_default(request):
    """The default cash account summary.

    Args:
        request (HttpRequest) The request.

    Returns:
        HttpResponseRedirect: The redirection to the default account.
    """
    account = Account.objects.get(
        code=settings.ACCOUNTING["DEFAULT_CASH_ACCOUNT"])
    return HttpResponseRedirect(
        reverse("accounting:cash-summary", args=(account,)))


@require_GET
@digest_login_required
def cash_summary(request, account):
    """The cash account summary.

    Args:
        request (HttpRequest) The request.
        account (Account): The account.

    Returns:
        HttpResponse: The response.
    """
    # The account
    accounts = get_cash_accounts()
    # The month summaries
    if account.code == "0":
        months = [RecordSummary(**x) for x in Record.objects
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
        months = [RecordSummary(**x) for x in Record.objects
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
    months.append(RecordSummary(
        label=pgettext("Accounting|", "Total"),
        credit=sum([x.credit for x in months]),
        debit=sum([x.debit for x in months]),
        balance=sum([x.balance for x in months]),
        cumulative_balance=cumulative_balance,
    ))
    pagination = Pagination(request, months, True)
    shortcut_accounts = settings.ACCOUNTING["CASH_SHORTCUT_ACCOUNTS"]
    return render(request, "accounting/cash-summary.html", {
        "item_list": pagination.items,
        "pagination": pagination,
        "account": account,
        "reports": ReportUrl(cash=account),
        "shortcut_accounts": [x for x in accounts if
                              x.code in shortcut_accounts],
        "all_accounts": [x for x in accounts if
                         x.code not in shortcut_accounts],
    })


# noinspection PyUnusedLocal
@require_GET
@digest_login_required
def ledger_default(request):
    """The default ledger.

    Args:
        request (HttpRequest) The request.

    Returns:
        HttpResponseRedirect: The redirection to the default account
            and month.
    """
    account = Account.objects.get(
        code=settings.ACCOUNTING["DEFAULT_LEDGER_ACCOUNT"])
    period_spec = dateformat.format(timezone.localdate(), "Y-m")
    return HttpResponseRedirect(
        reverse("accounting:ledger", args=(account, period_spec)))


@require_GET
@digest_login_required
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
        .order_by("transaction__date", "transaction__ord", "is_credit", "ord"))
    if re.match("^[1-3]", account.code) is not None:
        balance = Record.objects\
            .filter(
                transaction__date__lt=period.start,
                account__code__startswith=account.code)\
            .aggregate(
                balance=Coalesce(Sum(Case(When(
                    is_credit=True, then=-1),
                    default=1) * F("amount")), 0))["balance"]
        record_brought_forward = Record(
            transaction=Transaction(date=period.start),
            account=account,
            summary=pgettext("Accounting|", "Brought Forward"),
            is_credit=balance < 0,
            amount=abs(balance),
            balance=balance,
        )
    else:
        balance = 0
        record_brought_forward = None
    for record in records:
        balance = balance + \
                  (-1 if record.is_credit else 1) * record.amount
        record.balance = balance
    if record_brought_forward is not None:
        records.insert(0, record_brought_forward)
    pagination = Pagination(request, records, True)
    records = pagination.items
    find_imbalanced(records)
    find_order_holes(records)
    return render(request, "accounting/ledger.html", {
        "item_list": records,
        "pagination": pagination,
        "account": account,
        "period": period,
        "reports": ReportUrl(ledger=account, period=period),
        "accounts": get_ledger_accounts(),
    })


# noinspection PyUnusedLocal
@require_GET
@digest_login_required
def ledger_summary_default(request):
    """The default ledger summary.

    Args:
        request (HttpRequest) The request.

    Returns:
        HttpResponseRedirect: The redirection to the default account.
    """
    account = Account.objects.get(
        code=settings.ACCOUNTING["DEFAULT_LEDGER_ACCOUNT"])
    return HttpResponseRedirect(
        reverse("accounting:ledger-summary", args=(account,)))


@require_GET
@digest_login_required
def ledger_summary(request, account):
    """The ledger summary report.

    Args:
        request (HttpRequest) The request.
        account (Account): The account.

    Returns:
        HttpResponse: The response.
    """
    # The month summaries
    months = [RecordSummary(**x) for x in Record.objects
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
    months.append(RecordSummary(
        label=pgettext("Accounting|", "Total"),
        credit=sum([x.credit for x in months]),
        debit=sum([x.debit for x in months]),
        balance=sum([x.balance for x in months]),
        cumulative_balance=cumulative_balance,
    ))
    pagination = Pagination(request, months, True)
    return render(request, "accounting/ledger-summary.html", {
        "item_list": pagination.items,
        "pagination": pagination,
        "account": account,
        "reports": ReportUrl(ledger=account),
        "accounts": get_ledger_accounts(),
    })


# noinspection PyUnusedLocal
@require_GET
@digest_login_required
def journal_default(request):
    """The default journal.

    Args:
        request (HttpRequest) The request.

    Returns:
        HttpResponseRedirect: The redirection to the default month.
    """
    period_spec = dateformat.format(timezone.localdate(), "Y-m")
    return HttpResponseRedirect(
        reverse("accounting:journal", args=(period_spec,)))


@require_GET
@digest_login_required
def journal(request, period):
    """The journal.

    Args:
        request (HttpRequest) The request.
        period (Period): The period.

    Returns:
        HttpResponse: The response.
    """
    # The accounting records
    records = Record.objects\
        .filter(
            transaction__date__gte=period.start,
            transaction__date__lte=period.end)\
        .order_by("transaction__date", "transaction__ord", "is_credit", "ord")
    # The brought-forward records
    brought_forward_accounts = Account.objects\
        .filter(
            Q(code__startswith="1")
            | Q(code__startswith="2")
            | Q(code__startswith="3"))\
        .annotate(balance=Sum(
            Case(
                When(record__is_credit=True, then=-1),
                default=1
            ) * F("record__amount"),
            filter=Q(record__transaction__date__lt=period.start)))\
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
            account=Account.objects.get(code="3351"),
            is_credit=False,
            amount=sum_credits - sum_debits
        ))
    elif sum_debits > sum_credits:
        credit_records.append(Record(
            transaction=Transaction(date=period.start),
            account=Account.objects.get(code="3351"),
            is_credit=True,
            amount=sum_debits - sum_credits
        ))
    records = list(debit_records) + list(credit_records)\
        + list(records)
    pagination = Pagination(request, records, True)
    return render(request, "accounting/journal.html", {
        "item_list": pagination.items,
        "pagination": pagination,
        "reports": ReportUrl(period=period),
        "period": period,
    })


# noinspection PyUnusedLocal
@require_GET
@digest_login_required
def trial_balance_default(request):
    """The default trial balance.

    Args:
        request (HttpRequest) The request.

    Returns:
        HttpResponseRedirect: The redirection to the default month.
    """
    period_spec = dateformat.format(timezone.localdate(), "Y-m")
    return HttpResponseRedirect(
        reverse("accounting:trial-balance", args=(period_spec,)))


@require_GET
@digest_login_required
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
            balance=Sum(Case(
                When(record__is_credit=True, then=-1),
                default=1) * F("record__amount")))
        .filter(balance__isnull=False)
        .annotate(
            debit=Case(
                When(balance__gt=0, then=F("balance")),
                default=None),
            credit=Case(
                When(balance__lt=0, then=-F("balance")),
                default=None))
        .order_by("code"))
    real = list(
        Account.objects
        .filter(
            Q(record__transaction__date__lte=period.end),
            (Q(code__startswith="1")
             | Q(code__startswith="2")
             | Q(code__startswith="3")),
            ~Q(code="3351"))
        .annotate(
            balance=Sum(Case(
                When(record__is_credit=True, then=-1),
                default=1) * F("record__amount")))
        .filter(balance__isnull=False)
        .annotate(
            debit=Case(
                When(balance__gt=0, then=F("balance")),
                default=None),
            credit=Case(
                When(balance__lt=0, then=-F("balance")),
                default=None))
        .order_by("code"))
    balance = Record.objects\
        .filter(
            (Q(transaction__date__lt=period.start)
             & ~(Q(account__code__startswith="1")
                 | Q(account__code__startswith="2")
                 | Q(account__code__startswith="3")))
            | (Q(transaction__date__lte=period.end)
               & Q(account__code="3351")))\
        .aggregate(
            balance=Sum(Case(
                When(is_credit=True, then=-1),
                default=1) * F("amount")))["balance"]
    if balance is not None and balance != 0:
        brought_forward = Account.objects.get(code="3351")
        if balance > 0:
            brought_forward.debit = balance
            brought_forward.credit = 0
        else:
            brought_forward.debit = None
            brought_forward.credit = -balance
        real.append(brought_forward)
    accounts = nominal + real
    accounts.sort(key=lambda x: x.code)
    total_account = Account()
    total_account.title = pgettext("Accounting|", "Total")
    total_account.debit = sum([x.debit for x in accounts
                               if x.debit is not None])
    total_account.credit = sum([x.credit for x in accounts
                                if x.credit is not None])
    return render(request, "accounting/trial-balance.html", {
        "item_list": accounts,
        "total_item": total_account,
        "reports": ReportUrl(period=period),
        "period": period,
    })


# noinspection PyUnusedLocal
@require_GET
@digest_login_required
def income_statement_default(request):
    """The default income statement.

    Args:
        request (HttpRequest) The request.

    Returns:
        HttpResponseRedirect: The redirection to the default month.
    """
    period_spec = dateformat.format(timezone.localdate(), "Y-m")
    return HttpResponseRedirect(
        reverse("accounting:income-statement", args=(period_spec,)))


@require_GET
@digest_login_required
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
            balance=Sum(Case(
                When(record__is_credit=True, then=1),
                default=-1) * F("record__amount")))
        .filter(balance__isnull=False)
        .order_by("code"))
    groups = list(Account.objects.filter(
        code__in=[x.code[:2] for x in accounts]))
    sections = list(Account.objects.filter(
        Q(code="4") | Q(code="5") | Q(code="6")
        | Q(code="7") | Q(code="8") | Q(code="9")).order_by("code"))
    cumulative_accounts = {
        "5": Account(title=pgettext("Accounting|", "Gross Income")),
        "6": Account(title=pgettext("Accounting|", "Operating Income")),
        "7": Account(title=pgettext("Accounting|", "Before Tax Income")),
        "8": Account(title=pgettext("Accounting|", "After Tax Income")),
        "9": Account.objects.get(code="3353"),
    }
    cumulative_total = 0
    for section in sections:
        section.groups = [x for x in groups
                          if x.code[:1] == section.code]
        for group in section.groups:
            group.details = [x for x in accounts
                             if x.code[:2] == group.code]
            group.balance = None
            group.total = sum([x.balance
                               for x in group.details])
        section.balance = None
        section.total = sum([x.total for x in section.groups])
        cumulative_total = cumulative_total + section.total
        if section.code in cumulative_accounts:
            section.cumulative_total\
                = cumulative_accounts[section.code]
            section.cumulative_total.balance = None
            section.cumulative_total.total = cumulative_total
        else:
            section.cumulative_total = None
        section.has_next = True
    sections[-1].has_next = False
    return render(request, "accounting/income-statement.html", {
        "item_list": sections,
        "reports": ReportUrl(period=period),
        "period": period,
    })


# noinspection PyUnusedLocal
@require_GET
@digest_login_required
def balance_sheet_default(request):
    """The default balance sheet.

    Args:
        request (HttpRequest) The request.

    Returns:
        HttpResponseRedirect: The redirection to the default month.
    """
    period_spec = dateformat.format(timezone.localdate(), "Y-m")
    return HttpResponseRedirect(
        reverse("accounting:balance-sheet", args=(period_spec,)))


@require_GET
@digest_login_required
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
            ~Q(code="3351"))
        .annotate(
            balance=Sum(Case(
                When(record__is_credit=True, then=-1),
                default=1) * F("record__amount")))
        .filter(balance__isnull=False)
        .order_by("code"))
    for account in accounts:
        account.url = reverse("accounting:ledger", args=(account, period))
    balance = Record.objects\
        .filter(
            Q(transaction__date__lt=period.start)
            & ~((Q(account__code__startswith="1")
                 | Q(account__code__startswith="2")
                 | Q(account__code__startswith="3"))
                & ~Q(account__code="3351")))\
        .aggregate(
            balance=Sum(Case(
                When(is_credit=True, then=-1),
                default=1) * F("amount")))["balance"]
    if balance is not None and balance != 0:
        brought_forward = Account.objects.get(code="3351")
        brought_forward.balance = balance
        brought_forward.url = reverse(
            "accounting:income-statement", args=(period,))
        accounts.append(brought_forward)
    balance = Record.objects\
        .filter(
            Q(transaction__date__gte=period.start)
            & Q(transaction__date__lte=period.end)
            & ~((Q(account__code__startswith="1")
                 | Q(account__code__startswith="2")
                 | Q(account__code__startswith="3"))
                & ~Q(account__code="3351")))\
        .aggregate(
            balance=Sum(Case(
                When(is_credit=True, then=-1),
                default=1) * F("amount")))["balance"]
    if balance is not None and balance != 0:
        net_income = Account.objects.get(code="3353")
        net_income.balance = balance
        net_income.url = reverse(
            "accounting:income-statement", args=(period,))
        accounts.append(net_income)
    for account in [x for x in accounts if x.code[0] in "23"]:
        account.balance = -account.balance
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
            group.balance = sum([x.balance
                                 for x in group.details])
        section.balance = sum([x.balance for x in section.groups])
    by_code = {x.code: x for x in sections}
    return render(request, "accounting/balance-sheet.html", {
        "assets": by_code["1"],
        "liabilities": by_code["2"],
        "owners_equity": by_code["3"],
        "reports": ReportUrl(period=period),
        "period": period,
    })


@require_GET
@digest_login_required
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
            | Q(transaction__note__icontains=query))
    pagination = Pagination(request, records, True)
    return render(request, "accounting/search.html", {
        "item_list": pagination.items,
        "pagination": pagination,
        "reports": ReportUrl(),
    })


@require_GET
@digest_login_required
def transaction_show(request, type, transaction):
    """The view of an accounting transaction.

    Args:
        request (HttpRequest): The request.
        type (str): The transaction type.
        transaction (Transaction): The transaction.

    Returns:
        HttpResponse: The response.
    """
    return render(request, F"accounting/transactions/{type}/show.html", {
        "transaction_type": type,
        "item": transaction,
    })


@require_GET
@digest_login_required
def transaction_create(request, type):
    """The view to create an accounting transaction.

    Args:
        request (HttpRequest): The request.
        type (str): The transaction type.

    Returns:
        HttpResponse: The response.
    """
    transaction = Transaction()
    if len(transaction.debit_records) == 0:
        transaction.records.append(Record(ord=1, is_credit=False))
    if len(transaction.credit_records) == 0:
        transaction.records.append(Record(ord=1, is_credit=True))
    return render(request, F"accounting/transactions/{type}/edit.html", {
        "transaction_type": type,
        "item": transaction,
    })
