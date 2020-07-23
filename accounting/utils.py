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

from django.conf import settings
from django.db.models import Q, Sum, Case, When, F, Count, Max, Min
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import pgettext

from accounting.models import Account, Transaction, Record
from mia_core.period import Period
from mia_core.utils import new_id


class ReportUrl:
    """The URL of the accounting reports.

    Args:
        **kwargs: the keyword arguments:
            period (Period): The currently-specified period.
            cash (Account): The currently-specified account of the
                cash account or cash summary.
            ledger (Account): The currently-specified account of the
                ledger or leger summary.

    Attributes:
        cash (str): The URL of the cash account.
        cash_summary (str): The URL of the cash summary.
        ledger (str): The URL of the ledger.
        ledger_summary (str): The URL of the ledger summary.
        journal (str): The URL of the journal.
        trial_balance (str): The URL of the trial balance.
        income_statement (str): The URL of the income statement.
        balance_sheet (str): The URL of the balance sheet.
    """
    _period = None
    _cash = None
    _ledger = None

    def __init__(self, **kwargs):
        if "period" in kwargs:
            self._period = kwargs["period"]
        else:
            self._period = Period()
        if "cash" in kwargs:
            self._cash = kwargs["cash"]
        else:
            self._cash = Account.objects.get(
                code=settings.ACCOUNTING["DEFAULT_CASH_ACCOUNT"])
        if "ledger" in kwargs:
            self._ledger = kwargs["ledger"]
        else:
            self._ledger = Account.objects.get(
                code=settings.ACCOUNTING["DEFAULT_LEDGER_ACCOUNT"])

    @property
    def cash(self):
        return reverse(
            "accounting:cash", args=(self._cash, self._period))

    @property
    def cash_summary(self):
        return reverse("accounting:cash-summary", args=(self._cash,))

    @property
    def ledger(self):
        return reverse(
            "accounting:ledger", args=(self._ledger, self._period))

    @property
    def ledger_summary(self):
        return reverse("accounting:ledger-summary", args=(self._ledger,))

    @property
    def journal(self):
        return reverse("accounting:journal", args=(self._period,))

    @property
    def trial_balance(self):
        return reverse("accounting:trial-balance", args=(self._period,))

    @property
    def income_statement(self):
        return reverse("accounting:income-statement", args=(self._period,))

    @property
    def balance_sheet(self):
        return reverse("accounting:balance-sheet", args=(self._period,))


class Populator:
    """The helper to populate the accounting data.

    Args:
        user (User): The user in action.

    Attributes:
        user (User): The user in action.
    """
    user = None

    def __init__(self, user):
        self.user = user

    def add_accounts(self, accounts):
        """Adds accounts.

        Args:
            accounts (tuple[tuple[any]]): Tuples of
                (code, Traditional Chinese, English, Simplified Chinese)
                of the accounts.
        """
        for data in accounts:
            code = data[0]
            if isinstance(code, int):
                code = str(code)
            parent = None if len(code) == 1\
                else Account.objects.get(code=code[:-1])
            Account(pk=new_id(Account), parent=parent, code=code,
                    title_zh_hant=data[1], title_en=data[2],
                    title_zh_hans=data[3],
                    created_by=self.user, updated_by=self.user).save()

    def add_transfer_transaction(self, date, debit, credit):
        """Adds a transfer transaction.

        Args:
            date (datetime.date|int): The date, or the number of days from
                today.
            debit (tuple[tuple[any]]): Tuples of (account, summary, amount)
                of the debit records.
            credit (tuple[tuple[any]]): Tuples of (account, summary, amount)
                of the credit records.
        """
        if isinstance(date, int):
            date = timezone.localdate() + timezone.timedelta(days=date)
        order = Transaction.objects.filter(date=date).count() + 1
        transaction = Transaction(pk=new_id(Transaction), date=date, ord=order,
                                  created_by=self.user, updated_by=self.user)
        transaction.save()
        order = 1
        for data in debit:
            account = data[0]
            if isinstance(account, str):
                account = Account.objects.get(code=account)
            elif isinstance(account, int):
                account = Account.objects.get(code=str(account))
            transaction.record_set.create(pk=new_id(Record), is_credit=False,
                                          ord=order, account=account,
                                          summary=data[1], amount=data[2],
                                          created_by=self.user,
                                          updated_by=self.user)
            order = order + 1
        order = 1
        for data in credit:
            account = data[0]
            if isinstance(account, str):
                account = Account.objects.get(code=account)
            elif isinstance(account, int):
                account = Account.objects.get(code=str(account))
            transaction.record_set.create(pk=new_id(Record), is_credit=True,
                                          ord=order, account=account,
                                          summary=data[1], amount=data[2],
                                          created_by=self.user,
                                          updated_by=self.user)
            order = order + 1

    def add_income_transaction(self, date, credit):
        """Adds a cash income transaction.

        Args:
            date (datetime.date|int): The date, or the number of days from
                today.
            credit (tuple[tuple[any]]): Tuples of (account, summary, amount) of
                the credit records.
        """
        amount = sum([x[2] for x in credit])
        self.add_transfer_transaction(date, (("1111", None, amount),), credit)

    def add_expense_transaction(self, date, debit):
        """Adds a cash income transaction.

        Args:
            date (datetime.date|int): The date, or the number of days from
                today.
            debit (tuple[tuple[any]]): Tuples of (account, summary, amount) of
                the debit records.
        """
        amount = sum([x[2] for x in debit])
        self.add_transfer_transaction(date, debit, (("1111", None, amount),))


def get_cash_accounts():
    """Returns the cash accounts.

    Returns:
        list[Account]: The cash accounts.
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
        title=pgettext(
            "Accounting|", "current assets and liabilities"),
    ))
    return accounts


def get_ledger_accounts():
    """Returns the accounts for the ledger.

    Returns:
        list[Account]: The accounts for the ledger.
    """
    # TODO: Te be replaced with the Django model queries
    return list(Account.objects.raw("""SELECT s.*
  FROM accounting_accounts AS s
  WHERE s.code IN (SELECT s.code
    FROM accounting_accounts AS s
      INNER JOIN (SELECT s.code
        FROM accounting_accounts AS s
         INNER JOIN accounting_records AS r ON r.account_sn = s.sn
        GROUP BY s.code) AS u
      ON u.code LIKE s.code || '%'
    GROUP BY s.code)
  ORDER BY s.code"""))


def find_imbalanced(records):
    """"Finds the records with imbalanced transactions, and sets their
    is_balanced attribute.

    Args:
        records (list[Record]): The accounting records.
    """
    imbalanced = [x.pk for x in Transaction.objects
                  .annotate(
                    balance=Sum(Case(
                        When(record__is_credit=True, then=-1),
                        default=1) * F("record__amount")))
                  .filter(~Q(balance=0))]
    for record in records:
        record.is_balanced = record.transaction.pk not in imbalanced


def find_order_holes(records):
    """"Finds whether the order of the transactions on this day is not
        1, 2, 3, 4, 5..., and should be reordered, and sets their
        has_order_holes attributes.

    Args:
        records (list[Record]): The accounting records.
    """
    holes = [x["date"] for x in Transaction.objects
             .values("date")
             .annotate(count=Count("ord"),
                       max=Max("ord"),
                       min=Min("ord"))
             .filter(~(Q(max=F("count")) & Q(min=1)))] +\
            [x["date"] for x in Transaction.objects
             .values("date", "ord")
             .annotate(count=Count("sn"))
             .filter(~Q(count=1))]
    for record in records:
        record.has_order_hole = record.transaction.date in holes
