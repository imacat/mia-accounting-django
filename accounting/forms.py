# The core application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/7/31

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
import re

from django import forms
from django.utils.translation import pgettext

from .models import Account, Record
from .validators import validate_record_account_code, validate_record_id


class RecordForm(forms.Form):
    """An accounting record form.

    Attributes:
        transaction (Transaction|None): The current transaction or None.
        is_credit (bool): Whether this is a credit record.
    """
    id = forms.IntegerField(
        required=False,
        error_messages={
            "invalid": pgettext("Accounting|", "This record is not valid."),
        },
        validators=[validate_record_id])
    account = forms.CharField(
        error_messages={
            "required": pgettext("Accounting|", "Please select the account."),
        },
        validators=[validate_record_account_code])
    summary = forms.CharField(
        required=False,
        max_length=128,
        error_messages={
            "max_length": pgettext("Accounting|", "This summary is too long."),
        })
    amount = forms.IntegerField(
        min_value=1,
        error_messages={
            "required": pgettext("Accounting|", "Please fill in the amount."),
            "invalid": pgettext("Accounting|", "Please fill in a number."),
            "min_value": pgettext(
                "Accounting|", "The amount must be at least 1."),
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transaction = None
        self.is_credit = None

    def account_title(self):
        """Returns the title of the specified account, if any.

        Returns:
            str: The title of the specified account, or None if the specified
                account is not available.
        """
        try:
            return Account.objects.get(code=self["account"].value()).title
        except KeyError:
            return None
        except Account.DoesNotExist:
            return None

    def clean(self):
        """Validates the form globally.

        Raises:
            ValidationError: When the validation fails.
        """
        errors = []
        validators = [self._validate_transaction, self._validate_account_type]
        for validator in validators:
            try:
                validator()
            except forms.ValidationError as e:
                errors.append(e)
        if errors:
            print(errors)
            raise forms.ValidationError(errors)

    def _validate_transaction(self):
        """Validates whether the transaction matches the transaction form.

        Raises:
            ValidationError: When the validation fails.
        """
        if "id" in self.errors:
            return
        if self.transaction is None:
            if "id" in self.data:
                error = forms.ValidationError(
                    pgettext("Accounting|",
                             "This record is not for this transaction."),
                    code="not_belong")
                self.add_error("id", error)
                raise error
        else:
            if "id" in self.data:
                record = Record.objects.get(pk=self.data["id"])
                if record.transaction.pk != self.transaction.pk:
                    error = forms.ValidationError(
                        pgettext("Accounting|",
                                 "This record is not for this transaction."),
                        code="not_belong")
                    self.add_error("id", error)
                    raise error

    def _validate_account_type(self):
        """Validates whether the account is a correct debit or credit account.

        Raises:
            ValidationError: When the validation fails.
        """
        if "account" in self.errors:
            return
        if self.is_credit:
            print(self.data["account"])
            if not re.match("^([123489]|7[1234])", self.data["account"]):
                error = forms.ValidationError(
                    pgettext("Accounting|",
                             "This account is not for credit records."),
                    code="not_credit")
                self.add_error("account", error)
                raise error
        else:
            if not re.match("^([1235689]|7[5678])", self.data["account"]):
                error = forms.ValidationError(
                    pgettext("Accounting|",
                             "This account is not for debit records."),
                    code="not_debit")
                self.add_error("account", error)
                raise error


class TransactionForm(forms.Form):
    """A transaction form.

    Attributes:
        txn_type (str): The transaction type.
        transaction (Transaction|None): The current transaction or None
        debit_records (list[RecordForm]): The debit records.
        credit_records (list[RecordForm]): The credit records.
    """
    date = forms.DateField(
        required=True,
        error_messages={
            "invalid": pgettext("Accounting|", "This date is not valid.")
        })
    notes = forms.CharField(
        required=False,
        max_length=128,
        error_messages={
            "max_length": pgettext("Accounting|", "This notes is too long.")
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.txn_type = None
        self.transaction = None
        self.debit_records = []
        self.credit_records = []

    def clean(self):
        """Validates the form globally.

        Raises:
            ValidationError: When the validation fails.
        """
        self._validate_balance()

    def _validate_balance(self):
        """Validates whether the total amount of debit and credit records are
        consistent.

        Raises:
            ValidationError: When the validation fails.
        """
        if self.txn_type != "transfer":
            return
        if self.debit_total() == self.credit_total():
            return
        raise forms.ValidationError(pgettext(
            "Accounting|",
            "The total amount of debit and credit records are inconsistent."),
            code="balance")

    def is_valid(self):
        if not super(TransactionForm, self).is_valid():
            return False
        for x in self.debit_records + self.credit_records:
            if not x.is_valid():
                return False
        return True

    def balance_error(self):
        """Returns the error message when the transaction is imbalanced.

        Returns:
            str: The error message when the transaction is imbalanced, or
                None otherwise.
        """
        errors = [x for x in self.non_field_errors().data
                  if x.code == "balance"]
        if errors:
            return errors[0].message
        return None

    def debit_total(self):
        """Returns the total amount of the debit records.

        Returns:
            int: The total amount of the credit records.
        """
        return sum([int(x.data["amount"]) for x in self.debit_records
                    if "amount" not in x.errors])

    def credit_total(self):
        """Returns the total amount of the credit records.

        Returns:
            int: The total amount of the credit records.
        """
        return sum([int(x.data["amount"]) for x in self.credit_records
                    if "amount" not in x.errors])
