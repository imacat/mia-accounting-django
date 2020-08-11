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
import json
import re

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Sum, Case, When, F, Count, Max, Min, Value, \
    CharField
from django.db.models.functions import StrIndex, Left
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from mia_core import stored_post
from mia_core.period import Period
from mia_core.templatetags.mia_core import smart_month
from mia_core.utils import new_pk
from .forms import TransactionForm, RecordForm
from .models import Account, Transaction, Record

DEFAULT_CASH_ACCOUNT = "1111"
CASH_SHORTCUT_ACCOUNTS = ["0", "1111"]
DEFAULT_LEDGER_ACCOUNT = "1111"
PAYABLE_ACCOUNTS = ["2141", "21413"]
EQUIPMENT_ACCOUNTS = ["1441"],


class MonthlySummary:
    """A summary record.

    Args:
        month (datetime.date): The month.
        label (str): The text label.
        credit (int): The credit amount.
        debit (int): The debit amount.
        balance (int): The balance.
        cumulative_balance (int): The cumulative balance.

    Attributes:
        month (datetime.date): The month.
        label (str): The text label.
        credit (int): The credit amount.
        debit (int): The debit amount.
        balance (int): The balance.
        cumulative_balance (int): The cumulative balance.
    """

    def __init__(self, month=None, label=None, credit=None, debit=None,
                 balance=None, cumulative_balance=None):
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
        cash (Account): The currently-specified account of the
            cash account or cash summary.
        ledger (Account): The currently-specified account of the
            ledger or leger summary.
        period (Period): The currently-specified period.
    """

    def __init__(self, cash=None, ledger=None, period=None):
        self._period = Period() if period is None else period
        self._cash = get_default_cash_account() if cash is None else cash
        self._ledger = get_default_ledger_account()\
            if ledger is None else ledger

    def cash(self):
        return reverse(
            "accounting:cash", args=(self._cash, self._period))

    def cash_summary(self):
        return reverse("accounting:cash-summary", args=(self._cash,))

    def ledger(self):
        return reverse(
            "accounting:ledger", args=(self._ledger, self._period))

    def ledger_summary(self):
        return reverse("accounting:ledger-summary", args=(self._ledger,))

    def journal(self):
        return reverse("accounting:journal", args=(self._period,))

    def trial_balance(self):
        return reverse("accounting:trial-balance", args=(self._period,))

    def income_statement(self):
        return reverse("accounting:income-statement", args=(self._period,))

    def balance_sheet(self):
        return reverse("accounting:balance-sheet", args=(self._period,))


class Populator:
    """The helper to populate the accounting data.

    Args:
        user (User): The user in action.

    Attributes:
        user (User): The user in action.
    """

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
        self.add_transfer_transaction(
            date, ((Account.CASH, None, amount),), credit)

    def add_expense_transaction(self, date, debit):
        """Adds a cash income transaction.

        Args:
            date (datetime.date|int): The date, or the number of days from
                today.
            debit (tuple[tuple[any]]): Tuples of (account, summary, amount) of
                the debit records.
        """
        amount = sum([x[2] for x in debit])
        self.add_transfer_transaction(
            date, debit, ((Account.CASH, None, amount),))


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
        title=_("current assets and liabilities"),
    ))
    return accounts


def get_default_cash_account():
    """Returns the default cash account.

    Returns:
        Account: The default cash account.
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


def get_cash_shortcut_accounts():
    """Returns the codes of the shortcut cash accounts.

    Returns:
        list[str]: The codes of the shortcut cash accounts.
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
         INNER JOIN accounting_records AS r ON r.account_id = s.id
        GROUP BY s.code) AS u
      ON u.code LIKE s.code || '%%'
    GROUP BY s.code)
  ORDER BY s.code"""))


def get_default_ledger_account():
    """Returns the default ledger account.

    Returns:
        Account: The default ledger account.
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
             .annotate(count=Count("pk"))
             .filter(~Q(count=1))]
    for record in records:
        record.has_order_hole = record.pk is not None\
                                and record.transaction.date in holes


def find_payable_records(account, records):
    """Finds and sets the whether the payable record is paid.

    Args:
        account (Account): The current ledger account.
        records (list[Record]): The accounting records.
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


def find_existing_equipments(account, records):
    """Finds and sets the equipments that still exist.

    Args:
        account (Account): The current ledger account.
        records (list[Record]): The accounting records.
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


def get_summary_categories():
    """Finds and returns the summary categories and their corresponding account
    hints.

    Returns:
        dict[str,str]: The summary categories and their account hints, by
            their record types and category types.
    """
    rows = Record.objects\
        .filter(Q(summary__contains="—"),
                ~Q(account__code__startswith="114"),
                ~Q(account__code__startswith="214"),
                ~Q(account__code__startswith="128"),
                ~Q(account__code__startswith="228"))\
        .annotate(rec_type=Case(When(is_credit=True, then=Value("credit")),
                                default=Value("debit"),
                                output_field=CharField()),
                  cat_type=Case(
                      When(summary__regex=".+—.+—.+→.+", then=Value("bus")),
                      When(summary__regex=".+—.+[→↔].+", then=Value("travel")),
                      default=Value("general"),
                      output_field=CharField()),
                  category=Left("summary",
                                StrIndex("summary", Value("—")) - 1,
                                output_field=CharField()))\
        .values("rec_type", "cat_type", "category", "account__code")\
        .annotate(count=Count("category"))\
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
    # Converts the dictionary to a list, as the category may not be US-ASCII
    return json.dumps(categories)


def fill_txn_from_post(txn_type, txn, post):
    """Fills the transaction from the POSTed data.  The POSTed data must be
    validated and clean at this moment.

    Args:
        txn_type (str): The transaction type.
        txn (Transaction): The transaction.
        post (dict): The POSTed data.
    """
    m = re.match("^([0-9]{4})-([0-9]{2})-([0-9]{2})$", post["date"])
    txn.date = datetime.date(
        int(m.group(1)),
        int(m.group(2)),
        int(m.group(3)))
    if "notes" in post:
        txn.notes = post["notes"]
    else:
        txn.notes = None
    # The records
    max_no = _find_max_record_no(txn_type, post)
    records = []
    for record_type in max_no.keys():
        for i in range(max_no[record_type]):
            no = i + 1
            if F"{record_type}-{no}-id" in post:
                record = Record.objects.get(pk=post[F"{record_type}-{no}-id"])
            else:
                record = Record(
                    is_credit=(record_type == "credit"),
                    transaction=txn)
            record.ord = no
            record.account = Account.objects.get(
                code=post[F"{record_type}-{no}-account"])
            if F"{record_type}-{no}-summary" in post:
                record.summary = post[F"{record_type}-{no}-summary"]
            else:
                record.summary = None
            record.amount = int(post[F"{record_type}-{no}-amount"])
            records.append(record)
    if txn_type != "transfer":
        if txn_type == "expense":
            if len(txn.credit_records) > 0:
                record = txn.credit_records[0]
            else:
                record = Record(is_credit=True, transaction=txn)
        else:
            if len(txn.debit_records) > 0:
                record = txn.debit_records[0]
            else:
                record = Record(is_credit=False, transaction=txn)
        record.ord = 1
        record.account = Account.objects.get(code=Account.CASH)
        record.summary = None
        record.amount = sum([x.amount for x in records])
        records.append(record)
    txn.records = records


def sort_post_txn_records(post):
    """Sorts the records in the form by their specified order, so that the
    form can be used to populate the data to return to the user.

    Args:
        post (dict): The POSTed form.
    """
    # Collects the available record numbers
    record_no = {
        "debit": [],
        "credit": [],
    }
    for key in post.keys():
        m = re.match(
            "^(debit|credit)-([1-9][0-9]*)-(id|ord|account|summary|amount)",
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
                orders[no] = int(post[F"{record_type}-{no}-ord"])
            except KeyError:
                orders[no] = 9999
            except ValueError:
                orders[no] = 9999
        record_no[record_type].sort(key=lambda n: orders[n])
    # Constructs the sorted new form
    new_post = {}
    for record_type in record_no.keys():
        for i in range(len(record_no[record_type])):
            old_no = record_no[record_type][i]
            no = i + 1
            new_post[F"{record_type}-{no}-ord"] = str(no)
            for attr in ["id", "account", "summary", "amount"]:
                if F"{record_type}-{old_no}-{attr}" in post:
                    new_post[F"{record_type}-{no}-{attr}"]\
                        = post[F"{record_type}-{old_no}-{attr}"]
    # Purges the old form and fills it with the new form
    for x in [x for x in post.keys() if re.match(
            "^(debit|credit)-([1-9][0-9]*)-(id|ord|account|summary|amount)",
            x)]:
        del post[x]
    for key in new_post.keys():
        post[key] = new_post[key]


def make_txn_form_from_model(txn_type, txn):
    """Converts a transaction data model to a transaction form.

    Args:
        txn_type (str): The transaction type.
        txn (Transaction): The transaction data model.

    Returns:
        TransactionForm: The transaction form.
    """
    form = TransactionForm(
        {x: str(getattr(txn, x)) for x in ["date", "notes"]
         if getattr(txn, x) is not None})
    form.transaction = txn if txn.pk is not None else None
    form.txn_type = txn_type
    records = []
    if txn_type != "income":
        records = records + txn.debit_records
    if txn_type != "expense":
        records = records + txn.credit_records
    for record in records:
        data = {x: getattr(record, x)
                for x in ["summary", "amount"]
                if getattr(record, x) is not None}
        if record.pk is not None:
            data["id"] = record.pk
        try:
            data["account"] = record.account.code
        except ObjectDoesNotExist:
            pass
        record_form = RecordForm(data)
        record_form.transaction = form.transaction
        record_form.is_credit = record.is_credit
        if record.is_credit:
            form.credit_records.append(record_form)
        else:
            form.debit_records.append(record_form)
    return form


def make_txn_form_from_post(post, txn_type, txn):
    """Converts the POSTed data to a transaction form.

    Args:
        post (dict[str]): The POSTed data.
        txn_type (str): The transaction type.
        txn (Transaction|None): The current transaction, or None
            if there is no current transaction.

    Returns:
        TransactionForm: The transaction form.
    """
    form = TransactionForm(
        {x: post[x] for x in ("date", "notes") if x in post})
    form.transaction = txn
    form.txn_type = txn_type
    # The records
    max_no = _find_max_record_no(txn_type, post)
    for record_type in max_no.keys():
        records = []
        is_credit = (record_type == "credit")
        for i in range(max_no[record_type]):
            no = i + 1
            record_form = RecordForm(
                {x: post[F"{record_type}-{no}-{x}"]
                 for x in ["id", "account", "summary", "amount"]
                 if F"{record_type}-{no}-{x}" in post})
            record_form.transaction = form.transaction
            record_form.is_credit = is_credit
            records.append(record_form)
        if record_type == "debit":
            form.debit_records = records
        else:
            form.credit_records = records
    return form


def make_txn_form_from_status(request, txn_type, txn):
    """Converts the previously-stored status to a transaction form.

    Args:
        request (HttpRequest): The request.
        txn_type (str): The transaction type.
        txn (Transaction|None): The current transaction, or None
            if there is no current transaction.

    Returns:
        TransactionForm: The transaction form, or None if there is no
            previously-stored status.
    """
    form = stored_post.get_previous_post(request)
    if form is None:
        return None
    return make_txn_form_from_post(form, txn_type, txn)


def _find_max_record_no(txn_type, post):
    """Finds the max debit and record numbers from the POSTed form.

    Args:
        txn_type (str): The transaction type.
        post (dict[str,str]): The POSTed data.

    Returns:
        dict[str,int]: The max debit and record numbers from the POSTed form.

    """
    max_no = {}
    if txn_type != "credit":
        max_no["debit"] = 0
    if txn_type != "debit":
        max_no["credit"] = 0
    for key in post.keys():
        m = re.match(
            "^(debit|credit)-([1-9][0-9]*)-(id|ord|account|summary|amount)$",
            key)
        if m is None:
            continue
        record_type = m.group(1)
        if record_type not in max_no:
            continue
        no = int(m.group(2))
        if max_no[record_type] < no:
            max_no[record_type] = no
    return max_no
