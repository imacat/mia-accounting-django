# The core application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/8/1

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

"""The validators of the Mia core application.

"""
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext as _

from .models import Account, Record


def validate_record_id(value: str) -> None:
    """Validates the record ID.

    Args:
        value: The record ID.

    Raises:
        ValidationError: When the validation fails.
    """
    try:
        Record.objects.get(pk=value)
    except Record.DoesNotExist:
        raise ValidationError(_("This accounting record does not exists."),
                              code="not_exist")


def validate_record_account_code(value: str) -> None:
    """Validates an account code.

    Args:
        value: The account code.

    Raises:
        ValidationError: When the validation fails.
    """
    try:
        Account.objects.get(code=value)
    except Account.DoesNotExist:
        raise ValidationError(_("This account does not exist."),
                              code="not_exist")
    child = Account.objects.filter(
        Q(code__startswith=value),
        ~Q(code=value),
    ).first()
    if child is not None:
        raise ValidationError(_("You cannot select a parent account."),
                              code="parent_account")
