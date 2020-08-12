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
from typing import Union, Optional

from django import template

from accounting.models import Account
from accounting.utils import ReportUrl
from mia_core.period import Period

register = template.Library()


@register.filter
def accounting_amount(value: Union[str, int]) -> str:
    if value is None:
        return ""
    if value == 0:
        return "-"
    s = str(abs(value))
    while True:
        m = re.match("^([1-9][0-9]*)([0-9]{3})", s)
        if m is None:
            break
        s = m.group(1) + "," + m.group(2)
    if value < 0:
        s = "(%s)" % (s)
    return s


@register.simple_tag
def report_url(cash_account: Optional[Account],
               ledger_account: Optional[Account],
               period: Optional[Period]) -> ReportUrl:
    """Returns accounting report URL helper.

    Args:
        cash_account: The current cash account.
        ledger_account: The current ledger account.
        period: The period.

    Returns:
        ReportUrl: The accounting report URL helper.
    """
    return ReportUrl(
        cash=cash_account or None,
        ledger=ledger_account or None,
        period=period or None)
