# The template filters of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/7/2

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
import locale
from datetime import date

from django import template
from django.template import defaultfilters
from django.utils.translation import gettext

register = template.Library()


@register.filter(is_safe=True)
def smart_date(value):
    """Formats the date for human friendliness.

    Args:
        value (datetime.date): The date.

    Returns:
        str: The human-friendly format of the date.
    """
    if value == date.today():
        return gettext("Today")
    if (date.today() - value).days == 1:
        return gettext("Yesterday")
    if date.today().year == value.year:
        return defaultfilters.date(value, "n/j(D)").replace("星期", "")
    return defaultfilters.date(value, "Y/n/j(D)").replace("星期", "")
