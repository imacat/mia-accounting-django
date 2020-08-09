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

import titlecase
from django import template
from django.template import defaultfilters
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import SafeString
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


@register.simple_tag(takes_context=True)
def url_period(context, period_spec):
    """Returns the current URL with a new period.

    Args:
        context (RequestContext): The request context.
        period_spec (str): The period specification.

    Returns:
        str: The current URL with the new period.
    """
    view_name = "%s:%s" % (
        context.request.resolver_match.app_name,
        context.request.resolver_match.url_name)
    kwargs = context.request.resolver_match.kwargs
    kwargs["period"] = period_spec
    return reverse(view_name, kwargs=kwargs)


@register.simple_tag(takes_context=True)
def url_with_return(context, url):
    """Returns the URL with the current page added as the "r" query parameter,
    so that returning to this page is possible.

    Args:
        context (RequestContext): The request context.
        url (str): The URL.

    Returns:
        str: The URL with the current page added as the "r" query parameter.
    """
    return str(UrlBuilder(url).query(
        r=str(UrlBuilder(context.request.get_full_path()).remove("s"))))


@register.simple_tag(takes_context=True)
def url_keep_return(context, url):
    """Returns the URL with the current "r" query parameter set, so that the
    next processor can still return to the same page.

    Args:
        context (RequestContext): The request context.
        url (str): The URL.

    Returns:
        str: The URL with the current "r" query parameter set.
    """
    return str(UrlBuilder(url).query(r=context.request.GET.get("r")))


@register.simple_tag(takes_context=True)
def add_css(context, url):
    """Adds a local CSS file.  The file is added to the "css" template
    list variable.

    Args:
        context (RequestContext): The request context.
        url (str): The URL or path of the CSS file.

    Returns:
        str: An empty string
    """
    if "css" not in context.dicts[0]:
        context.dicts[0]["css"] = []
    context.dicts[0]["css"].append(url)
    return ""


@register.simple_tag(takes_context=True)
def add_js(context, url):
    """Adds a local JavaScript file.  The file is added to the "js" template
    list variable.

    Args:
        context (RequestContext): The request context.
        url (str): The URL or path of the JavaScript file.

    Returns:
        str: An empty string
    """
    if "js" not in context.dicts[0]:
        context.dicts[0]["js"] = []
    context.dicts[0]["js"].append(url)
    return ""


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


@register.filter
def title_case(value):
    """Formats the title in a proper American-English case.

    Args:
        value (str): The title.

    Returns:
        str: The title in a proper American-English case.
    """
    value = str(value)
    if isinstance(value, SafeString):
        value = value + ""
    return titlecase.titlecase(value)
