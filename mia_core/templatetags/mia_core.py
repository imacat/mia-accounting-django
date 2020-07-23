# The core application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/7/1

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

"""The template tags and filters of the Mia core application.

"""
from datetime import date

from django import template
from django.template import defaultfilters
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext

from mia_core.utils import UrlBuilder

register = template.Library()


@register.simple_tag(takes_context=True)
def setvar(context, key, value):
    """Sets a variable in the template.

    Args:
        context (Context): the context
        key (str): The variable name
        value (str): The variable value

    Returns:
        str: An empty string.
    """
    context.dicts[0][key] = value
    return ""


@register.simple_tag
def str_format(format_str, *args):
    """Sets a variable in the template.

    Args:
        format_str (str): The format.
        args (*str): The arguments.

    Returns:
        str: The formatted text string.
    """
    return format_str.format(*args)


@register.simple_tag
def url_query(url, **kwargs):
    """Returns the URL with the query parameters set.

    Args:
        url (str): The URL.
        kwargs (**dict): The query parameters.

    Returns:
        str: The URL with query parameters set.
    """
    print(url)
    builder = UrlBuilder(url)
    for key in kwargs.keys():
        if kwargs[key] is not None:
            builder.set_param(key, kwargs[key])
    return str(builder)


@register.simple_tag(takes_context=True)
def url_period(context, period_spec):
    request = context["request"]
    view_name = "%s:%s" % (
        request.resolver_match.app_name,
        request.resolver_match.url_name)
    kwargs = request.resolver_match.kwargs
    kwargs["period"] = period_spec
    return reverse(view_name, kwargs=kwargs)


@register.filter
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


@register.filter
def smart_month(value):
    """Formats the month for human friendliness.

    Args:
        value (datetime.date): The month.

    Returns:
        str: The human-friendly format of the month.
    """
    today = timezone.localdate()
    if value.year == today.year and value.month == today.month:
        return gettext("This Month")
    month = today.month - 1
    year = today.year
    if month < 1:
        month = 12
        year = year - 1
    if value.year == year and value.month == month:
        return gettext("Last Month")
    return defaultfilters.date(value, "Y/n")
