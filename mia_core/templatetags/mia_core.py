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

from mia_core.status import _retrieve
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
    return str(UrlBuilder(url).set_param("r", return_to))


@register.simple_tag(takes_context=True)
def url_keep_return(context, view_name, *args):
    """Returns the transaction URL.

    Args:
        context (RequestContext): The request context.
        view_name (str): The view name.
        *args (tuple[any]): The URL arguments.

    Returns:
        str: The URL.
    """
    url = reverse(view_name, args=args)
    return str(UrlBuilder(url).set_param("r", context.request.GET.get("r")))


@register.simple_tag(takes_context=True)
def retrieve_status(context):
    """Returns the success message from the previously-stored status.  The
    success message is saved as "success", and the error messages are saved as
    "errors" in the template variables.

    Args:
        context (RequestContext): The request context.

    Returns:
        str: An empty string.
    """
    if "s" not in context.request.GET:
        return ""
    status = _retrieve(context.request, context.request.GET["s"])
    if status is None:
        return ""
    if "success" in status:
        context.dicts[0]["success"] = status["success"]
    if "errors_by_field" in status:
        if "" in status["errors_by_field"]:
            if "page_errors" not in context.dicts[0]:
                context.dicts[0]["page_errors"] = []
            context.dicts[0]["page_errors"].append(
                status["errors_by_field"][""])
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


@register.filter()
def index(value, arg):
    """Returns the arg-th element of the value list or tuple.

    Args:
        value (list|tuple): The list or tuple.
        arg (int): The index.

    Returns:
        any: The arg-th element of the value
    """
    if not (isinstance(value, list) or isinstance(value, tuple)):
        return None
    if not isinstance(arg, int):
        return None
    if arg >= len(value):
        return None
    return value[arg]
