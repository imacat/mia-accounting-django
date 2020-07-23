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

from django import template
from django.urls import reverse

from mia_core.utils import UrlBuilder

register = template.Library()


@register.filter
def accounting_amount(value):
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


@register.simple_tag(takes_context=True)
def url_with_return(context, view_name, *args):
    """Returns the transaction URL.

    Args:
        context (RequestContext): The request context.
        view_name (str): The view name.
        *args (tuple[any]): The URL arguments.

    Returns:
        str: The URL.
    """
    url = reverse(view_name, args=args)
    return_to = context.request.get_full_path()
    return str(UrlBuilder(url).set_param("return-to", return_to))
