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

"""The template tags and filters of the accounting application.

"""
import re
from decimal import Decimal
from typing import Union, Optional

from django import template
from django.template import RequestContext

from accounting.models import Account
from accounting.utils import ReportUrl
from mia_core.period import Period

register = template.Library()


def _format_positive_amount(value: Union[str, Decimal]) -> str:
    """Formats a positive amount, groups every 3 digits by commas.

    Args:
        value: The amount.

    Returns:
        ReportUrl: The formatted amount.
    """
    s = str(value)
    while True:
        m = re.match("^([1-9][0-9]*)([0-9]{3}.*)", s)
        if m is None:
            break
        s = m.group(1) + "," + m.group(2)
    s = re.sub(r"^(.*\.[0-9]*?)0+$", r"\1", s)
    s = re.sub(r"^(.*)\.$", r"\1", s)
    return s


@register.filter
def accounting_amount(value: Union[Decimal]) -> str:
    """Formats an amount with the accounting notation, grouping every 3 digits
    by commas, and marking negative numbers with brackets instead of signs.

    Args:
        value: The amount.

    Returns:
        ReportUrl: The formatted amount.
    """
    if value is None:
        return ""
    if value == 0:
        return "-"
    s = _format_positive_amount(abs(value))
    if value < 0:
        s = F"({s})"
    return s


@register.filter
def short_amount(value: Union[Decimal]) -> str:
    """Formats an amount, groups every 3 digits by commas.

    Args:
        value: The amount.

    Returns:
        ReportUrl: The formatted amount.
    """
    if value is None:
        return ""
    if value == 0:
        return "-"
    s = _format_positive_amount(abs(value))
    if value < 0:
        s = "-" + s
    return s


@register.simple_tag(takes_context=True)
def report_url(context: RequestContext,
               cash_account: Optional[Account],
               ledger_account: Optional[Account],
               period: Optional[Period]) -> ReportUrl:
    """Returns accounting report URL helper.

    Args:
        context: The request context.
        cash_account: The current cash account.
        ledger_account: The current ledger account.
        period: The period.

    Returns:
        ReportUrl: The accounting report URL helper.
    """
    return ReportUrl(
        namespace=context.request.resolver_match.namespace,
        cash=cash_account or None,
        ledger=ledger_account or None,
        period=period or None)
