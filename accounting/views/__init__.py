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
from datetime import timedelta

from django.db import connection
from django.db.models import Sum
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils import dateformat, timezone
from django.utils.translation import pgettext
from django.views.decorators.http import require_GET

from accounting.models import Record, Transaction, Subject, \
    RecordSummary
from accounting.utils import ReportUrl
from mia import settings
from mia_core.digest_auth import digest_login_required
from mia_core.period import Period
from mia_core.utils import Pagination, SqlQuery


@require_GET
@digest_login_required
def home(request):
    """The accounting home page.

    Returns:
        HttpResponseRedirect: The redirection to the default
            accounting report.
    """
    return HttpResponseRedirect(reverse("accounting:cash.home"))


@require_GET
@digest_login_required
def cash_home(request):
    """The accounting cash report home page.

    Returns:
        HttpResponseRedirect: The redirection to the default subject
            and month.
    """
    subject_code = settings.ACCOUNTING["DEFAULT_CASH_SUBJECT"]
    period_spec = dateformat.format(timezone.localdate(), "Y-m")
    return HttpResponseRedirect(
        reverse("accounting:cash", args=(subject_code, period_spec)))


def _cash_subjects():
    """Returns the subjects for the cash account reports.

    Returns:
        list[Subject]: The subjects for the cash account reports.
    """
    subjects = list(Subject.objects.raw("""SELECT s.*
FROM accounting_subjects AS s
  WHERE s.code IN (SELECT s1.code
    FROM accounting_subjects AS s1
      INNER JOIN accounting_records AS r1 ON s1.sn=r1.subject_sn
    WHERE s1.code LIKE '11%'
      OR s1.code LIKE '12%'
      OR s1.code LIKE '21%'
      OR s1.code LIKE '22%'
    GROUP BY s1.code)
  ORDER BY s.code"""))
    subjects.insert(0, Subject(
        code="0",
        title=pgettext(
            "Accounting|", "current assets and liabilities"),
    ))
    return subjects


def _find_imbalanced(records):
    """"Finds the records with imbalanced transactions, and sets their
    is_balanced attribute.

    Args:
        records (list[Record]): The accounting records.
    """
    with connection.cursor() as cursor:
        cursor.execute("""SELECT transaction_sn
  FROM accounting_records
  GROUP BY transaction_sn
  HAVING SUM(CASE WHEN is_credit THEN -1 ELSE 1 END * amount) != 0""")
        imbalanced = [x[0] for x in cursor.fetchall()]
    for record in records:
        record.is_balanced = record.transaction.sn not in imbalanced


def _find_order_holes(records):
    """"Finds whether the order of the transactions on this day is not
        1, 2, 3, 4, 5..., and should be reordered, and sets their
        has_order_holes attributes.

    Args:
        records (list[Record]): The accounting records.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
  SELECT date FROM accounting_transactions
  GROUP BY date HAVING COUNT(*)!=MAX(ord)
  UNION
  SELECT date FROM accounting_transactions
  GROUP BY date, ord HAVING COUNT(*) > 1""")
        holes = [x[0] for x in cursor.fetchall()]
    for record in records:
        record.has_order_hole = record.transaction.date in holes


@require_GET
@digest_login_required
def cash(request, subject_code, period_spec):
    """The cash account report."""
    # The period
    first_txn = Transaction.objects.order_by("date").first()
    data_start = first_txn.date if first_txn is not None else None
    last_txn = Transaction.objects.order_by("-date").first()
    data_end = last_txn.date if last_txn is not None else None
    period = Period(period_spec, data_start, data_end)
    # The subject
    subjects = _cash_subjects()
    current_subject = None
    for subject in subjects:
        if subject.code == subject_code:
            current_subject = subject
    if current_subject is None:
        raise Http404()
    # The accounting records
    if current_subject.code == "0":
        select_records = """SELECT r.*
FROM accounting_records AS r
  INNER JOIN (SELECT
         t1.sn AS sn,
         t1.date AS date,
         t1.ord AS ord
      FROM accounting_records AS r1
        LEFT JOIN accounting_transactions AS t1
          ON r1.transaction_sn=t1.sn
        LEFT JOIN accounting_subjects AS s1
          ON r1.subject_sn = s1.sn
      WHERE (s1.code LIKE '11%%'
        OR s1.code LIKE '12%%'
        OR s1.code LIKE '21%%'
        OR s1.code LIKE '22%%')
        AND t1.date >= %s
        AND t1.date <= %s
      GROUP BY t1.sn) AS t
    ON r.transaction_sn=t.sn
  LEFT JOIN accounting_subjects AS s ON r.subject_sn = s.sn
WHERE s.code NOT LIKE '11%%'
  AND s.code NOT LIKE '12%%'
  AND s.code NOT LIKE '21%%'
  AND s.code NOT LIKE '22%%'
ORDER BY
  t.date,
  t.ord,
  CASE WHEN is_credit THEN 1 ELSE 2 END,
  r.ord"""
        sql_records = SqlQuery(
            select_records,
            [period.start, period.end])
        select_balance_before = """SELECT
    SUM(CASE WHEN is_credit THEN 1 ELSE -1 END * amount) AS amount
  FROM (%s) AS b""" % select_records
        sql_balance_before = SqlQuery(
            select_balance_before,
            [data_start, period.start - timedelta(days=1)])
    else:
        select_records = """SELECT r.*
FROM accounting_records AS r
  INNER JOIN (SELECT
         t1.sn AS sn,
         t1.date AS date,
         t1.ord AS ord
      FROM accounting_records AS r1
       LEFT JOIN accounting_transactions AS t1
         ON r1.transaction_sn=t1.sn
       LEFT JOIN accounting_subjects AS s1
         ON r1.subject_sn = s1.sn
      WHERE t1.date >= %s
        AND t1.date <= %s
        AND s1.code LIKE %s
      GROUP BY t1.sn) AS t
    ON r.transaction_sn=t.sn
  LEFT JOIN accounting_subjects AS s ON r.subject_sn = s.sn
WHERE s.code NOT LIKE %s
ORDER BY
  t.date,
  t.ord,
  CASE WHEN is_credit THEN 1 ELSE 2 END,
  r.ord"""
        sql_records = SqlQuery(
            select_records,
            [period.start,
             period.end,
             current_subject.code + "%",
             current_subject.code + "%"])
        select_balance_before = f"""SELECT
    SUM(CASE WHEN is_credit THEN 1 ELSE -1 END * amount) AS amount
  FROM ({select_records})"""
        sql_balance_before = SqlQuery(
            select_balance_before,
            [data_start,
             period.start - timedelta(days=1),
             current_subject.code + "%",
             current_subject.code + "%"])
    # The list data
    records = list(Record.objects.raw(
        sql_records.sql,
        sql_records.params))
    with connection.cursor() as cursor:
        cursor.execute(
            sql_balance_before.sql, sql_balance_before.params)
        row = cursor.fetchone()
    balance_before = row[0]
    if balance_before is None:
        balance_before = 0
    balance = balance_before
    for record in records:
        sign = 1 if record.is_credit else -1
        balance = balance + sign * record.amount
        record.balance = balance
    record_sum = Record(
        transaction=Transaction(date=records[-1].transaction.date),
        subject=current_subject,
        summary=pgettext("Accounting|", "Total"),
        balance=balance
    )
    record_sum.credit_amount = sum([
        x.amount for x in records if x.is_credit])
    record_sum.debit_amount = sum([
        x.amount for x in records if not x.is_credit])
    records.insert(0, Record(
        transaction=Transaction(date=period.start),
        subject=Subject.objects.filter(code="3351").first(),
        is_credit=balance_before >= 0,
        amount=abs(balance_before),
        balance=balance_before))
    records.append(record_sum)
    pagination = Pagination(request, records, True)
    records = pagination.records
    _find_imbalanced(records)
    _find_order_holes(records)
    shortcut_subjects = settings.ACCOUNTING["CASH_SHORTCUT_SUBJECTS"]
    return render(request, "accounting/cash.html", {
        "records": records,
        "pagination": pagination,
        "current_subject": current_subject,
        "period": period,
        "reports": ReportUrl(cash=current_subject, period=period),
        "shortcut_subjects": [x for x in subjects
                              if x.code in shortcut_subjects],
        "all_subjects": [x for x in subjects
                         if x.code not in shortcut_subjects],
    })


def cash_summary(request, subject_code):
    """The cash account summary report."""
    # The subject
    subjects = _cash_subjects()
    current_subject = None
    for subject in subjects:
        if subject.code == subject_code:
            current_subject = subject
    if current_subject is None:
        raise Http404()
    # The accounting records
    if connection.vendor == "postgresql":
        month_definition = "CAST(DATE_TRUNC('month', t.date) AS date)"
    elif connection.vendor == "sqlite":
        month_definition = "DATE(t.date, 'start of month')"
    else:
        month_definition = None
    if current_subject.code == "0":
        records = list(RecordSummary.objects.raw(
            f"""SELECT
  {month_definition} AS month,
  SUM(CASE WHEN r.is_credit THEN r.amount ELSE 0 END) AS credit_amount,
  SUM(CASE WHEN r.is_credit THEN 0 ELSE r.amount END) AS debit_amount,
  SUM(CASE WHEN r.is_credit THEN 1 ELSE -1 END * r.amount) AS balance
FROM accounting_records AS r
  INNER JOIN (SELECT
      t1.sn AS sn,
      t1.date AS date,
      t1.ord AS ord
    FROM accounting_records AS r1
      LEFT JOIN accounting_transactions AS t1 ON r1.transaction_sn=t1.sn
      LEFT JOIN accounting_subjects AS s1 ON r1.subject_sn = s1.sn
    WHERE s1.code LIKE '11%%'
      OR s1.code LIKE '12%%'
      OR s1.code LIKE '21%%'
      OR s1.code LIKE '22%%'
    GROUP BY t1.sn) AS t
  ON r.transaction_sn=t.sn
  LEFT JOIN accounting_subjects AS s ON r.subject_sn = s.sn
WHERE s.code NOT LIKE '11%%'
  AND s.code NOT LIKE '12%%'
  AND s.code NOT LIKE '21%%'
  AND s.code NOT LIKE '22%%'
GROUP BY month
ORDER BY month"""))
    else:
        records = list(RecordSummary.objects.raw(
            f"""SELECT
  {month_definition} AS month,
  SUM(CASE WHEN r.is_credit THEN r.amount ELSE 0 END) AS credit_amount,
  SUM(CASE WHEN r.is_credit THEN 0 ELSE r.amount END) AS debit_amount,
  SUM(CASE WHEN r.is_credit THEN 1 ELSE -1 END * r.amount) AS balance
FROM accounting_records AS r
  INNER JOIN (SELECT
      t1.sn AS sn,
      t1.date AS date,
      t1.ord AS ord
    FROM accounting_records AS r1
      LEFT JOIN accounting_transactions AS t1 ON r1.transaction_sn=t1.sn
      LEFT JOIN accounting_subjects AS s1 ON r1.subject_sn = s1.sn
    WHERE s1.code LIKE %s
    GROUP BY t1.sn) AS t
  ON r.transaction_sn=t.sn
  LEFT JOIN accounting_subjects AS s ON r.subject_sn = s.sn
WHERE s.code NOT LIKE %s
GROUP BY month
ORDER BY month""",
            [current_subject.code + "%", current_subject.code + "%"]))
    cumulative_balance = 0
    for record in records:
        cumulative_balance = cumulative_balance + record.balance
        record.cumulative_balance = cumulative_balance
    records.append(RecordSummary(
        label=pgettext("Accounting|", "Total"),
        credit_amount=sum([x.credit_amount for x in records]),
        debit_amount=sum([x.debit_amount for x in records]),
        balance=sum([x.balance for x in records]),
        cumulative_balance=cumulative_balance,
    ))
    pagination = Pagination(request, records, True)
    shortcut_subjects = settings.ACCOUNTING["CASH_SHORTCUT_SUBJECTS"]
    return render(request, "accounting/cash_summary.html", {
        "records": pagination.records,
        "pagination": pagination,
        "current_subject": current_subject,
        "reports": ReportUrl(cash=current_subject),
        "shortcut_subjects": [x for x in subjects if
                              x.code in shortcut_subjects],
        "all_subjects": [x for x in subjects if
                         x.code not in shortcut_subjects],
    })


def _ledger_subjects():
    """Returns the subjects for the ledger reports.

    Returns:
        list[Subject]: The subjects for the ledger reports.
    """
    return list(Subject.objects.raw("""SELECT s.*
  FROM accounting_subjects AS s
  WHERE s.code IN (SELECT s.code
    FROM accounting_subjects AS s
      INNER JOIN (SELECT s.code
        FROM accounting_subjects AS s
         INNER JOIN accounting_records AS r ON r.subject_sn = s.sn
        GROUP BY s.code) AS u
      ON u.code LIKE s.code || '%'
    GROUP BY s.code)
  ORDER BY s.code"""))


@require_GET
@digest_login_required
def ledger(request, subject_code, period_spec):
    """The ledger report."""
    # The period
    first_txn = Transaction.objects.order_by("date").first()
    data_start = first_txn.date if first_txn is not None else None
    last_txn = Transaction.objects.order_by("-date").first()
    data_end = last_txn.date if last_txn is not None else None
    period = Period(period_spec, data_start, data_end)
    # The subject
    subjects = _ledger_subjects()
    current_subject = None
    for subject in subjects:
        if subject.code == subject_code:
            current_subject = subject
    if current_subject is None:
        raise Http404()
    # The accounting records
    records = list(Record.objects.filter(
        transaction__date__gte=period.start,
        transaction__date__lte=period.end,
        subject__code__startswith=current_subject.code))
    if re.match("^[1-3]", current_subject.code) is not None:
        debit = Record.objects.filter(
            transaction__date__lt=period.start,
            subject__code__startswith=current_subject.code,
            is_credit=False).aggregate(sum=Sum("amount"))
        credit = Record.objects.filter(
            transaction__date__lt=period.start,
            subject__code__startswith=current_subject.code,
            is_credit=True).aggregate(sum=Sum("amount"))
        balance = (0 if debit["sum"] is None else debit["sum"]) \
                  - (0 if credit["sum"] is None else credit["sum"])
        record_brought_forward = Record(
            transaction=Transaction(
                date=records[-1].transaction.date),
            subject=current_subject,
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
    records = pagination.records
    _find_imbalanced(records)
    _find_order_holes(records)
    return render(request, "accounting/ledger.html", {
        "records": records,
        "pagination": pagination,
        "current_subject": current_subject,
        "period": period,
        "reports": ReportUrl(ledger=current_subject, period=period),
        "subjects": subjects,
    })


def ledger_summary(request, subject_code):
    """The ledger summary report."""
    # The subject
    subjects = _ledger_subjects()
    current_subject = None
    for subject in subjects:
        if subject.code == subject_code:
            current_subject = subject
    if current_subject is None:
        raise Http404()
    # The accounting records
    if connection.vendor == "postgresql":
        month_definition = "CAST(DATE_TRUNC('month', t.date) AS date)"
    elif connection.vendor == "sqlite":
        month_definition = "DATE(t.date, 'start of month')"
    else:
        month_definition = None
    records = list(RecordSummary.objects.raw(
        f"""SELECT
  {month_definition} AS month,
  SUM(CASE WHEN r.is_credit THEN 0 ELSE r.amount END) AS debit_amount,
  SUM(CASE WHEN r.is_credit THEN r.amount ELSE 0 END) AS credit_amount,
  SUM(CASE WHEN r.is_credit THEN -1 ELSE 1 END * r.amount) AS balance
FROM accounting_records AS r
  INNER JOIN accounting_transactions AS t ON r.transaction_sn = t.sn
  INNER JOIN accounting_subjects AS s ON r.subject_sn = s.sn
WHERE s.code LIKE %s
GROUP BY month
ORDER BY month""",
        [current_subject.code + "%"]))
    cumulative_balance = 0
    for record in records:
        cumulative_balance = cumulative_balance + record.balance
        record.cumulative_balance = cumulative_balance
    records.append(RecordSummary(
        label=pgettext("Accounting|", "Total"),
        credit_amount=sum([x.credit_amount for x in records]),
        debit_amount=sum([x.debit_amount for x in records]),
        balance=sum([x.balance for x in records]),
        cumulative_balance=cumulative_balance,
    ))
    pagination = Pagination(request, records, True)
    return render(request, "accounting/ledger_summary.html", {
        "records": pagination.records,
        "pagination": pagination,
        "current_subject": current_subject,
        "reports": ReportUrl(cash=current_subject),
        "subjects": subjects,
    })


@require_GET
@digest_login_required
def journal(request, period_spec):
    """The ledger report."""
    # The period
    first_txn = Transaction.objects.order_by("date").first()
    data_start = first_txn.date if first_txn is not None else None
    last_txn = Transaction.objects.order_by("-date").first()
    data_end = last_txn.date if last_txn is not None else None
    period = Period(period_spec, data_start, data_end)
    # The accounting records
    records = Record.objects.filter(
        transaction__date__gte=period.start,
        transaction__date__lte=period.end).order_by(
        "transaction__date", "is_credit", "ord")
    # The brought-forward records
    # TODO: To be done.

    pagination = Pagination(request, records, True)
    return render(request, "accounting/journal.html", {
        "records": pagination.records,
        "pagination": pagination,
        "period": period,
    })
