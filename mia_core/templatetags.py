# The template tags of the Mia project.
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

"""The template tags of the Mia core application.

"""

from django import template
register = template.Library()


@register.simple_tag(takes_context=True)
def setvar(context, key, value):
    """Sets a variable in the template.

    Args:
        context (Context): the context
        key (str): The variable name
        value (str): The variable value
    """
    context.dicts[0][key] = value
    return ""


@register.simple_tag(takes_context=True)
def format(context, format, *args, **kwargs):
    """Sets a variable in the template.

    Args:
        context (Context): the context.
        format (str): The format.
        args (str): The parameters.
        kwargs (str): The keyword arguments.
    """
    if "as" in kwargs:
        context.dicts[0][kwargs["as"]] = format.format(*args)
        return ""
    return format.format(*args)
