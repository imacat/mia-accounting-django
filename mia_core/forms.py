# The core application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/8/9

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

"""The forms of the Mia core application.

"""
from django import forms
from django.core.validators import RegexValidator
from django.db.models import Q
from django.utils.translation import gettext as _

from mia_core.models import User


class UserForm(forms.Form):
    """A user account form."""
    login_id = forms.CharField(
        max_length=32,
        error_messages={
            "required": _("Please fill in the log in ID."),
            "max_length": _("This log in ID is too long (max 32 characters)."),
        },
        validators=[
            RegexValidator(
                regex="^[^/]+$",
                message=_("You cannot use slash (/) in the log in ID.")),
        ])
    password = forms.CharField(required=False)
    password2 = forms.CharField(required=False)
    name = forms.CharField(
        max_length=32,
        error_messages={
            "required": _("Please fill in the name."),
            "max_length": _("This name is too long (max 32 characters)."),
        })
    is_disabled = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.current_user = None

    def clean(self):
        """Validates the form globally.

        Raises:
            ValidationError: When the validation fails.
        """
        errors = []
        validators = [self._validate_login_id_unique,
                      self._validate_password_new_required,
                      self._validate_password_login_id_changed_required,
                      self._validate_password2_required,
                      self._validate_passwords_equal,
                      self._validate_is_disabled_not_oneself]
        for validator in validators:
            try:
                validator()
            except forms.ValidationError as e:
                errors.append(e)
        if errors:
            raise forms.ValidationError(errors)

    def _validate_login_id_unique(self) -> None:
        """Validates whether the log in ID is unique.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if "login_id" not in self.data:
            return
        condition = Q(login_id=self.data["login_id"])
        if self.user is not None:
            condition = condition & ~Q(pk=self.user.pk)
        if User.objects.filter(condition).first() is None:
            return
        error = forms.ValidationError(_("This log in ID is already in use."),
                                      code="login_id_unique")
        self.add_error("login_id", error)
        raise error

    def _validate_password_new_required(self) -> None:
        """Validates whether the password is entered for newly-created users.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if self.user is not None:
            return
        if "password" in self.data:
            return
        error = forms.ValidationError(_("Please fill in the password."),
                                      code="password_required")
        self.add_error("password", error)
        raise error

    def _validate_password_login_id_changed_required(self) -> None:
        """Validates whether the password is entered for users whose login ID
        changed.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if self.user is None:
            return
        if "login_id" not in self.data:
            return
        if self.data["login_id"] == self.user.login_id:
            return
        if "password" in self.data:
            return
        error = forms.ValidationError(
            _("Please fill in the password to change the log in ID."),
            code="password_required")
        self.add_error("password", error)
        raise error

    def _validate_password2_required(self) -> None:
        """Validates whether the second password is entered.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if "password" not in self.data:
            return
        if "password2" in self.data:
            return
        error = forms.ValidationError(
            _("Please enter the password again to verify it."),
            code="password2_required")
        self.add_error("password2", error)
        raise error

    def _validate_passwords_equal(self) -> None:
        """Validates whether the two passwords are equal.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if "password" not in self.data:
            return
        if "password2" not in self.data:
            return
        if self.data["password"] == self.data["password2"]:
            return
        error = forms.ValidationError(_("The two passwords do not match."),
                                      code="passwords_equal")
        self.add_error("password2", error)
        raise error

    def _validate_is_disabled_not_oneself(self) -> None:
        """Validates whether the user tries to disable herself

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if "is_disabled" not in self.data:
            return
        if self.user is None:
            return
        if self.current_user is None:
            return
        if self.user.pk != self.current_user.pk:
            return
        error = forms.ValidationError(
            _("You cannot disable your own account."),
            code="not_oneself")
        self.add_error("is_disabled", error)
        raise error
