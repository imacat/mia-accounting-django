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
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum, Case, When, F, Count, Max, Min
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import pgettext, gettext_noop

from accounting.models import Account, Transaction, Record
from mia_core.period import Period
from mia_core.status import retrieve_status
from mia_core.utils import new_pk


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
            Account(pk=new_pk(Account), parent=parent, code=code,
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
        transaction = Transaction(pk=new_pk(Transaction), date=date, ord=order,
                                  created_by=self.user, updated_by=self.user)
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
            transaction.record_set.create(pk=new_pk(Record), is_credit=True,
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


def fill_transaction_from_form(transaction, form):
    """Fills the transaction from the form.

    Args:
        transaction (Transaction): The transaction.
        form (dict): The form
    """
    if "date" in form:
        transaction.date = form["date"]
    if "notes" in form:
        transaction.notes = form["notes"]
    # The records
    max_no = {
        "debit": 0,
        "credit": 0,
    }
    for key in form.keys():
        m = re.match(
            "^(debit|credit)-([1-9][0-9]*)-(sn|ord|account|summary|amount)$",
            key)
        if m is not None:
            rec_type = m.group(1)
            no = int(m.group(2))
            if max_no[rec_type] < no:
                max_no[rec_type] = no
    records = []
    for rec_type in max_no.keys():
        for i in range(max_no[rec_type]):
            no = i + 1
            record = Record(
                ord=no,
                is_credit=(rec_type == "credit"),
                transaction=transaction)
            if F"{rec_type}-{no}-sn" in form:
                record.pk = form[F"{rec_type}-{no}-sn"]
            if F"{rec_type}-{no}-account" in form:
                record.account = Account(code=form[F"{rec_type}-{no}-account"])
            if F"{rec_type}-{no}-summary" in form:
                record.summary = form[F"{rec_type}-{no}-summary"]
            if F"{rec_type}-{no}-amount" in form:
                record.amount = form[F"{rec_type}-{no}-amount"]
            records.append(record)
    transaction.records = records


def fill_transaction_from_previous_form(request, transaction):
    """Fills the transaction from the previously-stored form.

    Args:
        request (HttpRequest): The request
        transaction (Transaction): The transaction.
    """
    status = retrieve_status(request)
    if status is None:
        return
    if "form" not in status:
        return
    form = status["form"]
    fill_transaction_from_form(transaction, form)


def sort_form_transaction_records(form):
    """Sorts the records in the form by their specified order, so that the
    form can be used to populate the data to return to the user.

    Args:
        form (dict): The POSTed form.
    """
    # Collects the available record numbers
    record_no = {
        "debit": [],
        "credit": [],
    }
    for key in form.keys():
        m = re.match(
            "^(debit|credit)-([1-9][0-9]*)-(sn|ord|account|summary|amount)",
            key)
        if m is None:
            continue
        record_type = m.group(1)
        no = int(m.group(2))
        if no not in record_no[record_type]:
            record_no[record_type].append(no)
    # Sorts these record numbers by their specified orders
    for record_type in record_no.keys():
        orders = {}
        for no in record_no[record_type]:
            try:
                orders[no] = int(form[F"{record_type}-{no}-ord"])
            except KeyError:
                orders[no] = 9999
            except ValueError:
                orders[no] = 9999
        record_no[record_type].sort(key=lambda x: orders[x])
    # Constructs the sorted new form
    new_form = {}
    for record_type in record_no.keys():
        for i in range(len(record_no[record_type])):
            old_no = record_no[record_type][i]
            no = i + 1
            new_form[F"{record_type}-{no}-ord"] = no
            for attr in ["sn", "account", "summary", "amount"]:
                if F"{record_type}-{old_no}-{attr}" in form:
                    new_form[F"{record_type}-{no}-{attr}"]\
                        = form[F"{record_type}-{old_no}-{attr}"]
    # Purges the old form and fills it with the new form
    for x in [x for x in form.keys() if re.match(
            "^(debit|credit)-([1-9][0-9]*)-(sn|ord|account|summary|amount)",
            x)]:
        del form[x]
    for key in new_form.keys():
        form[key] = new_form[key]


def validate_account_code(record):
    """Validates the account code.

    Args:
        record (Record): The accounting record.

    Exceptions:
        ValidationError: Thrown when validation fails.
    """
    if record.account.code is None:
        raise ValidationError(gettext_noop(
            "Please select the account."))
    if record.account.code == "":
        raise ValidationError(gettext_noop(
            "Please select the account."))
    try:
        record.account = Account.objects.get(code=record.account.code)
    except Account.DoesNotExist:
        raise ValidationError(gettext_noop(
            "This account does not exist."))
    child_account = Account.objects.filter(
        code__startswith=record.account.code).first()
    if child_account is not None:
        raise ValidationError(gettext_noop(
            "You cannot choose a parent account."))
