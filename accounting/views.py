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

from django.http import HttpResponseRedirect

from django.urls import reverse
from django.utils import dateformat, timezone
from django.views import generic
from django.views.decorators.http import require_http_methods

from accounting.models import Record
from accounting.utils import PeriodParser, Pagination
from mia import settings


@require_http_methods(["GET"])
def home(request):
    """The accounting home page.

    Returns:
        The redirection to the default accounting report.
    """
    return HttpResponseRedirect(reverse("accounting:cash.home"))


@require_http_methods(["GET"])
def cash_home(request):
    """The accounting cash report home page.

    Returns:
        The redirection to the default subject and month.
    """
    subject_code = settings.ACCOUNTING["DEFAULT_CASH_SUBJECT"]
    period_spec = dateformat.format(timezone.now(), "Y-m")
    return HttpResponseRedirect(
        reverse("accounting:cash", args=(subject_code, period_spec)))


class CashReportView(generic.ListView):
    """The accounting cash report."""
    http_method_names = ["get"]
    template_name = "accounting/cash.html"
    context_object_name = "records"

    def get_queryset(self):
        """Return the accounting records for the cash report.

        Returns:
            The accounting records for the cash report
        """
        period = PeriodParser(self.kwargs["period_spec"])
        if self.kwargs["subject_code"] == "0":
            records = Record.objects.raw(
                """SELECT r.*
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
  r.ord""",
                [period.start, period.end])
        else:
            records = Record.objects.raw(
                """SELECT r.*
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
  r.ord""",
                [period.start,
                 period.end,
                 self.kwargs["subject_code"] + "%",
                 self.kwargs["subject_code"] + "%"])
        pagination = Pagination(
            len(records),
            get_query_number(self.request, "page"),
            get_query_number(self.request, "page-size"),
            True)
        start_no = pagination.page_size * (pagination.page_no - 1)
        return records[start_no:start_no + pagination.page_size]


def get_query_number(request, name):
    """Returns a positive number query parameter.

    Args:
        request (HttpRequest): The HTTP request
        name (str): The name of the query parameter

    Returns:
        int: The parameter value, or None if this parameter does not
        exist or is not a positive number
    """
    if name not in request.GET:
        return None
    elif not re.match("^[1-9][0-9]*$", request.GET[name]):
        return None
    else:
        return int(request.GET)
