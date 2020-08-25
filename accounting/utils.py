# The accounting application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/7/13

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

"""The utilities of the accounting application.

"""
import datetime
from typing import Union, Tuple, List, Optional, Iterable

from django.conf import settings
from django.db.models import Q, Sum, Case, When, F, Count, Max, Min
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from mia_core.period import Period
from mia_core.templatetags.mia_core import smart_month
from mia_core.utils import new_pk
from .models import Account, Transaction, Record

AccountData = Tuple[Union[str, int], str, str, str]
RecordData = Tuple[Union[str, int], Optional[str], float]

DEFAULT_CASH_ACCOUNT = "1111"
CASH_SHORTCUT_ACCOUNTS = ["0", "1111"]
DEFAULT_LEDGER_ACCOUNT = "1111"
PAYABLE_ACCOUNTS = ["2141", "21413"]
EQUIPMENT_ACCOUNTS = ["1441"],


class MonthlySummary:
    """A summary record.

    Args:
        month: The month.
        label: The text label.
        credit: The credit amount.
        debit: The debit amount.
        balance: The balance.
        cumulative_balance: The cumulative balance.

    Attributes:
        month (datetime.date): The month.
        label (str): The text label.
        credit (int): The credit amount.
        debit (int): The debit amount.
        balance (int): The balance.
        cumulative_balance (int): The cumulative balance.
    """

    def __init__(self, month: datetime.date = None, label: str = None,
                 credit: int = None, debit: int = None, balance: int = None,
                 cumulative_balance: int = None):
        self.month = month
        self.label = label
        self.credit = credit
        self.debit = debit
        self.balance = balance
        self.cumulative_balance = cumulative_balance
        if self.label is None and self.month is not None:
            self.label = smart_month(self.month)


class ReportUrl:
    """The URL of the accounting reports.

    Args:
        namespace: The namespace of the current application.
        cash: The currently-specified account of the
            cash account or cash summary.
        ledger: The currently-specified account of the
            ledger or leger summary.
        period: The currently-specified period.
    """

    def __init__(self, namespace: str, cash: Account = None,
                 ledger: Account = None, period: Period = None,):
        self._period = Period() if period is None else period
        self._cash = get_default_cash_account() if cash is None else cash
        self._ledger = get_default_ledger_account()\
            if ledger is None else ledger
        self._namespace = namespace

    def cash(self) -> str:
        return reverse("accounting:cash", args=[self._cash, self._period],
                       current_app=self._namespace)

    def cash_summary(self) -> str:
        return reverse("accounting:cash-summary", args=[self._cash],
                       current_app=self._namespace)

    def ledger(self) -> str:
        return reverse("accounting:ledger", args=[self._ledger, self._period],
                       current_app=self._namespace)

    def ledger_summary(self) -> str:
        return reverse("accounting:ledger-summary", args=[self._ledger],
                       current_app=self._namespace)

    def journal(self) -> str:
        return reverse("accounting:journal", args=[self._period],
                       current_app=self._namespace)

    def trial_balance(self) -> str:
        return reverse("accounting:trial-balance", args=[self._period],
                       current_app=self._namespace)

    def income_statement(self) -> str:
        return reverse("accounting:income-statement", args=[self._period],
                       current_app=self._namespace)

    def balance_sheet(self) -> str:
        return reverse("accounting:balance-sheet", args=[self._period],
                       current_app=self._namespace)


class DataFiller:
    """The helper to populate the accounting data.

    Args:
        user: The user in action.

    Attributes:
        user (User): The user in action.
    """

    def __init__(self, user):
        self.user = user

    def add_accounts(self, accounts: List[AccountData]) -> None:
        """Adds accounts.

        Args:
            accounts (tuple[tuple[any]]): Tuples of
                (code, English, Traditional Chinese, Simplified Chinese)
                of the accounts.
        """
        for data in accounts:
            code = data[0]
            if isinstance(code, int):
                code = str(code)
            parent = None if len(code) == 1\
                else Account.objects.get(code=code[:-1])
            account = Account(parent=parent, code=code, current_user=self.user)
            account.set_l10n_in("title", "en", data[1])
            account.set_l10n_in("title", "zh-hant", data[2])
            account.set_l10n_in("title", "zh-hans", data[3])
            account.save()

    def add_transfer_transaction(self, date: Union[datetime.date, int],
                                 debit: List[RecordData],
                                 credit: List[RecordData]) -> None:
        """Adds a transfer transaction.

        Args:
            date: The date, or the number of days from
                today.
            debit: Tuples of (account, summary, amount) of the debit records.
            credit: Tuples of (account, summary, amount) of the credit records.
        """
        if isinstance(date, int):
            date = timezone.localdate() + timezone.timedelta(days=date)
        order = Transaction.objects.filter(date=date).count() + 1
        transaction = Transaction(pk=new_pk(Transaction), date=date, ord=order,
                                  current_user=self.user)
        transaction.save()
        order = 1
        for data in debit:
            account = data[0]
            if isinstance(account, str):
                account = Account.objects.get(code=account)
            elif isinstance(account, int):
                account = Account.objects.get(code=str(account))
            transaction.record_set.create(pk=new_pk(Record), is_credit=False,
                                          ord=order, account=account,
                                          summary=data[1], amount=data[2],
                                          current_user=self.user)
            order = order + 1
        order = 1
        for data in credit:
            account = data[0]
            if isinstance(account, str):
                account = Account.objects.get(code=account)
            elif isinstance(account, int):
                account = Account.objects.get(code=str(account))
            transaction.record_set.create(pk=new_pk(Record), is_credit=True,
                                          ord=order, account=account,
                                          summary=data[1], amount=data[2],
                                          current_user=self.user)
            order = order + 1

    def add_income_transaction(self, date: Union[datetime.date, int],
                               credit: List[RecordData]) -> None:
        """Adds a cash income transaction.

        Args:
            date: The date, or the number of days from today.
            credit: Tuples of (account, summary, amount) of the credit records.
        """
        amount = sum([x[2] for x in credit])
        self.add_transfer_transaction(
            date, [(Account.CASH, None, amount)], credit)

    def add_expense_transaction(self, date: Union[datetime.date, int],
                                debit: List[RecordData]) -> None:
        """Adds a cash income transaction.

        Args:
            date: The date, or the number of days from today.
            debit: Tuples of (account, summary, amount) of the debit records.
        """
        amount = sum([x[2] for x in debit])
        self.add_transfer_transaction(
            date, debit, [(Account.CASH, None, amount)])


def get_cash_accounts() -> List[Account]:
    """Returns the cash accounts.

    Returns:
        The cash accounts.
    """
    accounts = list(
        Account.objects
        .filter(
            code__in=Record.objects
            .filter(
                Q(account__code__startswith="11")
                | Q(account__code__startswith="12")
                | Q(account__code__startswith="21")
                | Q(account__code__startswith="22"))
            .values("account__code"))
        .order_by("code"))
    accounts.insert(0, Account(
        code="0",
        title=_("current assets and liabilities"),
    ))
    return accounts


def get_default_cash_account() -> Account:
    """Returns the default cash account.

    Returns:
        The default cash account.
    """
    try:
        code = settings.ACCOUNTING["DEFAULT_CASH_ACCOUNT"]
    except AttributeError:
        code = DEFAULT_CASH_ACCOUNT
    except TypeError:
        code = DEFAULT_CASH_ACCOUNT
    except KeyError:
        code = DEFAULT_CASH_ACCOUNT
    if code == "0":
        return Account(code="0", title=_("current assets and liabilities"))
    try:
        return Account.objects.get(code=code)
    except Account.DoesNotExist:
        pass
    try:
        return Account.objects.get(code=DEFAULT_CASH_ACCOUNT)
    except Account.DoesNotExist:
        pass
    return Account(code="0", title=_("current assets and liabilities"))


def get_cash_shortcut_accounts() -> List[str]:
    """Returns the codes of the shortcut cash accounts.

    Returns:
        The codes of the shortcut cash accounts.
    """
    try:
        accounts = settings.ACCOUNTING["CASH_SHORTCUT_ACCOUNTS"]
    except AttributeError:
        return CASH_SHORTCUT_ACCOUNTS
    except TypeError:
        return CASH_SHORTCUT_ACCOUNTS
    except KeyError:
        return CASH_SHORTCUT_ACCOUNTS
    if not isinstance(accounts, list):
        return CASH_SHORTCUT_ACCOUNTS
    return accounts


def get_ledger_accounts() -> List[Account]:
    """Returns the accounts for the ledger.

    Returns:
        The accounts for the ledger.
    """
    """
    For SQL one-liner:
SELECT s.*
  FROM accounting_accounts AS s
  WHERE s.code IN (SELECT s.code
    FROM accounting_accounts AS s
      INNER JOIN (SELECT s.code
        FROM accounting_accounts AS s
         INNER JOIN accounting_records AS r ON r.account_id = s.id
        GROUP BY s.code) AS u
      ON u.code LIKE s.code || '%%'
    GROUP BY s.code)
  ORDER BY s.code
    """
    codes = {}
    for code in [x.code for x in Account.objects
                 .annotate(Count("record"))
                 .filter(record__count__gt=0)]:
        while len(code) > 0:
            codes[code] = True
            code = code[:-1]
    return Account.objects.filter(code__in=codes).order_by("code")


def get_default_ledger_account() -> Optional[Account]:
    """Returns the default ledger account.

    Returns:
        The default ledger account.
    """
    try:
        code = settings.ACCOUNTING["DEFAULT_CASH_ACCOUNT"]
    except AttributeError:
        code = DEFAULT_CASH_ACCOUNT
    except TypeError:
        code = DEFAULT_CASH_ACCOUNT
    except KeyError:
        code = DEFAULT_CASH_ACCOUNT
    try:
        return Account.objects.get(code=code)
    except Account.DoesNotExist:
        pass
    try:
        return Account.objects.get(code=DEFAULT_LEDGER_ACCOUNT)
    except Account.DoesNotExist:
        pass
    return None


def find_imbalanced(records: Iterable[Record]) -> None:
    """"Finds the records with imbalanced transactions, and sets their
    is_balanced attribute.

    Args:
        records: The accounting records.
    """
    imbalanced = [x.pk for x in Transaction.objects
                  .annotate(
                    balance=Sum(Case(
                        When(record__is_credit=True, then=-1),
                        default=1) * F("record__amount")))
                  .filter(~Q(balance=0))]
    for record in records:
        record.is_balanced = record.transaction.pk not in imbalanced


def find_order_holes(records: Iterable[Record]) -> None:
    """"Finds whether the order of the transactions on this day is not
        1, 2, 3, 4, 5..., and should be reordered, and sets their
        has_order_holes attributes.

    Args:
        records: The accounting records.
    """
    holes = [x["date"] for x in Transaction.objects
             .values("date")
             .annotate(count=Count("ord"),
                       max=Max("ord"),
                       min=Min("ord"))
             .filter(~(Q(max=F("count")) & Q(min=1)))] +\
            [x["date"] for x in Transaction.objects
             .values("date", "ord")
             .annotate(count=Count("pk"))
             .filter(~Q(count=1))]
    for record in records:
        record.has_order_hole = record.pk is not None\
                                and record.transaction.date in holes


def find_payable_records(account: Account, records: Iterable[Record]) -> None:
    """Finds and sets the whether the payable record is paid.

    Args:
        account: The current ledger account.
        records: The accounting records.
    """
    try:
        payable_accounts = settings.ACCOUNTING["PAYABLE_ACCOUNTS"]
    except AttributeError:
        return
    except TypeError:
        return
    except KeyError:
        return
    if not isinstance(payable_accounts, list):
        return
    if account.code not in payable_accounts:
        return
    rows = Record.objects\
        .filter(
            account__code__in=payable_accounts,
            summary__isnull=False)\
        .values("account__code", "summary")\
        .annotate(
            balance=Sum(Case(When(is_credit=True, then=1), default=-1)
                        * F("amount")))\
        .filter(~Q(balance=0))
    keys = ["%s-%s" % (x["account__code"], x["summary"]) for x in rows]
    for x in [x for x in records
              if x.pk is not None
              and F"{x.account.code}-{x.summary}" in keys]:
        x.is_payable = True


def find_existing_equipments(account: Account,
                             records: Iterable[Record]) -> None:
    """Finds and sets the equipments that still exist.

    Args:
        account: The current ledger account.
        records: The accounting records.
    """
    try:
        equipment_accounts = settings.ACCOUNTING["EQUIPMENT_ACCOUNTS"]
    except AttributeError:
        return
    except TypeError:
        return
    except KeyError:
        return
    if not isinstance(equipment_accounts, list):
        return
    if account.code not in equipment_accounts:
        return
    rows = Record.objects\
        .filter(
            account__code__in=equipment_accounts,
            summary__isnull=False)\
        .values("account__code", "summary")\
        .annotate(
            balance=Sum(Case(When(is_credit=True, then=1), default=-1)
                        * F("amount")))\
        .filter(~Q(balance=0))
    keys = ["%s-%s" % (x["account__code"], x["summary"]) for x in rows]
    for x in [x for x in records
              if x.pk is not None
              and F"{x.account.code}-{x.summary}" in keys]:
        x.is_existing_equipment = True
