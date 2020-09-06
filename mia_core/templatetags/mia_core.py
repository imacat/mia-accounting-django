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
import datetime
import re
from datetime import date
from typing import Any

import titlecase
from django import template
from django.http import HttpRequest
from django.template import defaultfilters, RequestContext
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import SafeString
from django.utils.translation import gettext

from mia_core.utils import UrlBuilder, CssAndJavaScriptLibraries

register = template.Library()


@register.simple_tag(takes_context=True)
def setvar(context: RequestContext, key: str, value: Any) -> str:
    """Sets a variable in the template.

    Args:
        context: the context
        key: The variable name
        value: The variable value

    Returns:
        An empty string.
    """
    context.dicts[0][key] = value
    return ""


@register.simple_tag(takes_context=True)
def url_period(context: RequestContext, period_spec: str) -> str:
    """Returns the current URL with a new period.

    Args:
        context: The request context.
        period_spec: The period specification.

    Returns:
        The current URL with the new period.
    """
    view_name = "%s:%s" % (
        context.request.resolver_match.app_name,
        context.request.resolver_match.url_name)
    kwargs = context.request.resolver_match.kwargs.copy()
    kwargs["period"] = period_spec
    namespace = context.request.resolver_match.namespace
    return reverse(view_name, kwargs=kwargs, current_app=namespace)


@register.simple_tag(takes_context=True)
def url_with_return(context: RequestContext, url: str) -> str:
    """Returns the URL with the current page added as the "r" query parameter,
    so that returning to this page is possible.

    Args:
        context: The request context.
        url: The URL.

    Returns:
        The URL with the current page added as the "r" query parameter.
    """
    return str(UrlBuilder(url).query(
        r=str(UrlBuilder(context.request.get_full_path()).remove("s"))))


@register.simple_tag(takes_context=True)
def url_keep_return(context: RequestContext, url: str) -> str:
    """Returns the URL with the current "r" query parameter set, so that the
    next processor can still return to the same page.

    Args:
        context: The request context.
        url: The URL.

    Returns:
        The URL with the current "r" query parameter set.
    """
    return str(UrlBuilder(url).query(r=context.request.GET.get("r")))


@register.simple_tag(takes_context=True)
def init_libs(context: RequestContext) -> str:
    """Initializes the static libraries.

    Args:
        context: The request context.

    Returns:
        An empty string.
    """
    if "libs" not in context.dicts[0]:
        context.dicts[0]["libs"] = CssAndJavaScriptLibraries()
    return ""


@register.simple_tag(takes_context=True)
def add_lib(context: RequestContext, *args) -> str:
    """Adds CSS and JavaScript libraries.

    Args:
        context: The request context.
        args: The names of the CSS and JavaScript libraries.

    Returns:
        An empty string.
    """
    if "libs" not in context.dicts[0]:
        context.dicts[0]["libs"] = CssAndJavaScriptLibraries(args)
    else:
        context.dicts[0]["libs"].use(args)
    return ""


@register.simple_tag(takes_context=True)
def add_css(context: RequestContext, url: str) -> str:
    """Adds a local CSS file.  The file is added to the "css" template
    list variable.

    Args:
        context: The request context.
        url: The URL or path of the CSS file.

    Returns:
        An empty string.
    """
    if "libs" not in context.dicts[0]:
        context.dicts[0]["libs"] = CssAndJavaScriptLibraries()
    context.dicts[0]["libs"].add_css(url)
    return ""


@register.simple_tag(takes_context=True)
def add_js(context: RequestContext, url: str) -> str:
    """Adds a local JavaScript file.  The file is added to the "js" template
    list variable.

    Args:
        context: The request context.
        url: The URL or path of the JavaScript file.

    Returns:
        An empty string.
    """
    if "libs" not in context.dicts[0]:
        context.dicts[0]["libs"] = CssAndJavaScriptLibraries()
    context.dicts[0]["libs"].add_js(url)
    return ""


@register.filter
def smart_date(value: datetime.date) -> str:
    """Formats the date for human friendliness.

    Args:
        value: The date.

    Returns:
        The human-friendly format of the date.
    """
    if value == date.today():
        return gettext("Today")
    if (date.today() - value).days == 1:
        return gettext("Yesterday")
    if date.today().year == value.year:
        return defaultfilters.date(value, "n/j(D)").replace("星期", "")
    return defaultfilters.date(value, "Y/n/j(D)").replace("星期", "")


@register.filter
def smart_month(value: datetime.date) -> str:
    """Formats the month for human friendliness.

    Args:
        value: The month.

    Returns:
        The human-friendly format of the month.
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
def title_case(value: str) -> str:
    """Formats the title in a proper American-English case.

    Args:
        value: The title.

    Returns:
        The title in a proper American-English case.
    """
    value = str(value)
    if isinstance(value, SafeString):
        value = value + ""
    return titlecase.titlecase(value)


@register.filter
def is_in_section(request: HttpRequest, section_name: str) -> bool:
    """Returns whether the request is currently in a section.

    Args:
        request: The request.
        section_name: The view name of this section.

    Returns:
        True if the request is currently in this section, or False otherwise.
    """
    if request is None:
        return False
    if request.resolver_match is None:
        return False
    view_name = request.resolver_match.view_name
    return view_name == section_name\
        or view_name.startswith(section_name + ".")


@register.filter
def is_static_url(target: str) -> bool:
    """Returns whether the target URL is a static path

    Args:
        target: The target, either a static path that need to be passed to
            the static template tag, or an HTTP, HTTPS URL or absolute path
            that should be displayed directly.

    Returns:
        True if the target URL is a static path, or False otherwise.
    """
    return not (re.match("^https?://", target) or target.startswith("/"))
