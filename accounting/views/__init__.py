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
from datetime import timedelta

from django.db import connection
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import dateformat
from django.utils.timezone import localdate
from django.utils.translation import get_language, pgettext
from django.views.decorators.http import require_GET

from accounting.models import Record, Transaction, Subject
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
    period_spec = dateformat.format(localdate(), "Y-m")
    return HttpResponseRedirect(
        reverse("accounting:cash", args=(subject_code, period_spec)))


@require_GET
@digest_login_required
def cash(request, subject_code, period_spec):
    """The cash account report."""
    # The period
    first_txn = Transaction.objects.order_by("date").first()
    data_start = first_txn.date if first_txn is not None else None
    last_txn = Transaction.objects.order_by("-date").first()
    data_end = last_txn.date if last_txn is not None else None
    period = Period(
        get_language(), data_start, data_end,
        period_spec)
    # The SQL query
    if subject_code == "0":
        subject = Subject(code="0")
        subject.title_zhtw = pgettext(
            "Accounting|", "Current Assets And Liabilities")
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
        subject = Subject.objects.filter(
            code=subject_code).first()
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
             subject.code + "%",
             subject.code + "%"])
        select_balance_before = """SELECT
    SUM(CASE WHEN is_credit THEN 1 ELSE -1 END * amount) AS amount
  FROM (%s) AS b""" % select_records
        sql_balance_before = SqlQuery(
            select_balance_before,
            [data_start,
             period.start - timedelta(days=1),
             subject.code + "%",
             subject.code + "%"])
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
        subject=subject,
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
    return render(request, "accounting/cash.html", {
        "records": pagination.records,
        "pagination": pagination,
        "subject": subject,
        "period": period,
        "reports": ReportUrl(cash=subject, period=period)
    })
