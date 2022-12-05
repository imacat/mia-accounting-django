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
import datetime
import re
from decimal import Decimal
from typing import Optional, List, Dict

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import RegexValidator
from django.db.models import Q, Max, Model
from django.db.models.functions import Length
from django.utils.translation import gettext as _

from .models import Account, Record, Transaction
from .validators import validate_record_account_code, validate_record_id


class RecordForm(forms.Form):
    """An accounting record form.

    Attributes:
        txn_form (TransactionForm): The parent transaction form.
        is_credit (bool): Whether this is a credit record.
    """
    id = forms.IntegerField(
        required=False,
        error_messages={
            "invalid": _("This accounting record is not valid."),
        },
        validators=[validate_record_id])
    account = forms.CharField(
        error_messages={
            "required": _("Please select the account."),
        },
        validators=[validate_record_account_code])
    summary = forms.CharField(
        required=False,
        max_length=128,
        error_messages={
            "max_length": _("This summary is too long (max. 128 characters)."),
        })
    amount = forms.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=0.01,
        error_messages={
            "required": _("Please fill in the amount."),
            "invalid": _("Please fill in a number."),
            "min_value": _("The amount must be more than 0."),
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.txn_form = None
        self.is_credit = None

    def account_title(self) -> Optional[str]:
        """Returns the title of the specified account, if any.

        Returns:
            The title of the specified account, or None if the specified
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
            forms.ValidationError: When the validation fails.
        """
        errors = []
        if "id" in self.errors:
            errors = errors + self.errors["id"].as_data()
        validators = [self._validate_transaction,
                      self._validate_account_type,
                      self._validate_is_credit]
        for validator in validators:
            try:
                validator()
            except forms.ValidationError as e:
                errors.append(e)
        if errors:
            raise forms.ValidationError(errors)

    def _validate_transaction(self) -> None:
        """Validates whether the transaction matches the transaction form.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if "id" in self.errors:
            return
        if self.txn_form.transaction is None:
            if "id" in self.data:
                raise forms.ValidationError(
                    _("This record is not for this transaction."),
                    code="not_belong")
        else:
            if "id" in self.data:
                record = Record.objects.get(pk=self.data["id"])
                if record.transaction.pk != self.txn_form.transaction.pk:
                    raise forms.ValidationError(
                        _("This record is not for this transaction."),
                        code="not_belong")

    def _validate_account_type(self) -> None:
        """Validates whether the account is a correct debit or credit account.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if "account" in self.errors:
            return
        if self.is_credit:
            if not re.match("^([123489]|7[1234])", self.data["account"]):
                error = forms.ValidationError(
                    _("This account is not for credit records."),
                    code="not_credit")
                self.add_error("account", error)
                raise error
        else:
            if not re.match("^([1235689]|7[5678])", self.data["account"]):
                error = forms.ValidationError(
                    _("This account is not for debit records."),
                    code="not_debit")
                self.add_error("account", error)
                raise error

    def _validate_is_credit(self) -> None:
        """Validates whether debit and credit records are submitted correctly
        as corresponding debit and credit records.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if "id" in self.errors:
            return
        if "id" not in self.data:
            return
        record = Record.objects.get(pk=self.data["id"])
        if record.is_credit != self.is_credit:
            if self.is_credit:
                raise forms.ValidationError(
                    _("This accounting record is not a credit record."),
                    code="not_credit")
            else:
                raise forms.ValidationError(
                    _("This accounting record is not a debit record."),
                    code="not_debit")


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
            "required": _("Please fill in the date."),
            "invalid": _("This date is not valid.")
        })
    notes = forms.CharField(
        required=False,
        max_length=128,
        error_messages={
            "max_length": _("These notes are too long (max. 128 characters).")
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populates the belonging record forms
        self.debit_records = []
        self.credit_records = []
        if len(args) > 0 and isinstance(args[0], dict):
            by_rec_id = {}
            for key in args[0].keys():
                m = re.match(
                    ("^((debit|credit)-([1-9][0-9]*))-"
                     "(id|ord|account|summary|amount)$"),
                    key)
                if m is None:
                    continue
                rec_id = m.group(1)
                column = m.group(4)
                if rec_id not in by_rec_id:
                    by_rec_id[rec_id] = {
                        "is_credit": m.group(2) == "credit",
                        "no": int(m.group(3)),
                        "data": {},
                    }
                by_rec_id[rec_id]["data"][column] = args[0][key]
            debit_data_list = [x for x in by_rec_id.values()
                               if not x["is_credit"]]
            debit_data_list.sort(key=lambda x: x["no"])
            for x in debit_data_list:
                record_form = RecordForm(x["data"])
                record_form.txn_form = self
                record_form.is_credit = False
                self.debit_records.append(record_form)
            credit_data_list = [x for x in by_rec_id.values()
                                if x["is_credit"]]
            credit_data_list.sort(key=lambda x: x["no"])
            for x in credit_data_list:
                record_form = RecordForm(x["data"])
                record_form.txn_form = self
                record_form.is_credit = True
                self.credit_records.append(record_form)
        self.txn_type = None
        self.transaction = None

    @staticmethod
    def from_post(post: Dict[str, str], txn_type: str, txn: Model):
        """Constructs a transaction form from the POST data.

        Args:
            post: The post data.
            txn_type: The transaction type.
            txn: The transaction data model.

        Returns:
            The transaction form.
        """
        TransactionForm._sort_post_txn_records(post)
        form = TransactionForm(post)
        form.txn_type = txn_type
        form.transaction = txn
        return form

    @staticmethod
    def _sort_post_txn_records(post: Dict[str, str]) -> None:
        """Sorts the records in the form by their specified order, so that the
        form can be used to populate the data to return to the user.

        Args:
            post: The POSTed form.
        """
        # Collects the available record numbers
        record_no = {
            "debit": [],
            "credit": [],
        }
        for key in post.keys():
            m = re.match(
                "^(debit|credit)-([1-9][0-9]*)-(id|ord|account|summary|amount)",
                key)
            if m is None:
                continue
            record_type = m.group(1)
            no = int(m.group(2))
            if no not in record_no[record_type]:
                record_no[record_type].append(no)
        # Sorts these record numbers by their specified orders
        for record_type in record_no.keys():
            orders = {}
            for no in record_no[record_type]:
                try:
                    orders[no] = int(post[F"{record_type}-{no}-ord"])
                except KeyError:
                    orders[no] = 9999
                except ValueError:
                    orders[no] = 9999
            record_no[record_type].sort(key=lambda n: orders[n])
        # Constructs the sorted new form
        new_post = {}
        for record_type in record_no.keys():
            for i in range(len(record_no[record_type])):
                old_no = record_no[record_type][i]
                no = i + 1
                new_post[F"{record_type}-{no}-ord"] = str(no)
                for attr in ["id", "account", "summary", "amount"]:
                    if F"{record_type}-{old_no}-{attr}" in post:
                        new_post[F"{record_type}-{no}-{attr}"] \
                            = post[F"{record_type}-{old_no}-{attr}"]
        # Purges the old form and fills it with the new form
        for x in [x for x in post.keys() if re.match(
                "^(debit|credit)-([1-9][0-9]*)-(id|ord|account|summary|amount)",
                x)]:
            del post[x]
        for key in new_post.keys():
            post[key] = new_post[key]

    @staticmethod
    def from_model(txn: Transaction, txn_type: str):
        """Constructs a transaction form from the transaction data model.

        Args:
            txn: The transaction data model.
            txn_type: The transaction type.

        Returns:
            The transaction form.
        """
        form = TransactionForm(
            {x: str(getattr(txn, x)) for x in ["date", "notes"]
             if getattr(txn, x) is not None})
        form.transaction = txn if txn.pk is not None else None
        form.txn_type = txn_type
        records = []
        if txn_type != "income":
            records = records + txn.debit_records
        if txn_type != "expense":
            records = records + txn.credit_records
        for record in records:
            data = {x: getattr(record, x)
                    for x in ["summary", "amount"]
                    if getattr(record, x) is not None}
            if record.pk is not None:
                data["id"] = record.pk
            try:
                data["account"] = record.account.code
            except ObjectDoesNotExist:
                pass
            record_form = RecordForm(data)
            record_form.txn_form = form
            record_form.is_credit = record.is_credit
            if record.is_credit:
                form.credit_records.append(record_form)
            else:
                form.debit_records.append(record_form)
        return form

    def clean(self):
        """Validates the form globally.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        errors = []
        validators = [self._validate_has_debit_records,
                      self._validate_has_credit_records,
                      self._validate_balance]
        for validator in validators:
            try:
                validator()
            except forms.ValidationError as e:
                errors.append(e)
        if errors:
            raise forms.ValidationError(errors)

    def _validate_has_debit_records(self) -> None:
        """Validates whether there is any debit record.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if self.txn_type == "income":
            return
        if len(self.debit_records) > 0:
            return
        if self.txn_type == "transfer":
            raise forms.ValidationError(
                _("Please fill in debit accounting records."),
                code="has_debit_records")
        raise forms.ValidationError(
            _("Please fill in accounting records."),
            code="has_debit_records")

    def _validate_has_credit_records(self) -> None:
        """Validates whether there is any credit record.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if self.txn_type == "expense":
            return
        if len(self.credit_records) > 0:
            return
        if self.txn_type == "transfer":
            raise forms.ValidationError(
                _("Please fill in credit accounting records."),
                code="has_debit_records")
        raise forms.ValidationError(
            _("Please fill in accounting records."),
            code="has_debit_records")

    def _validate_balance(self) -> None:
        """Validates whether the total amount of debit and credit records are
        consistent.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if self.txn_type != "transfer":
            return
        if self.debit_total() == self.credit_total():
            return
        raise forms.ValidationError(
            _("The total of the debit and credit amounts are inconsistent."),
            code="balance")

    def is_valid(self) -> bool:
        if not super().is_valid():
            return False
        for x in self.debit_records + self.credit_records:
            if not x.is_valid():
                return False
        return True

    def balance_error(self) -> Optional[str]:
        """Returns the error message when the transaction is imbalanced.

        Returns:
            The error message when the transaction is imbalanced, or None
            otherwise.
        """
        errors = [x for x in self.non_field_errors().data
                  if x.code == "balance"]
        if errors:
            return errors[0].message
        return None

    def debit_total(self) -> Decimal:
        """Returns the total amount of the debit records.

        Returns:
            The total amount of the credit records.
        """
        return sum([Decimal(x.data["amount"]) for x in self.debit_records
                    if "amount" in x.data and "amount" not in x.errors])

    def credit_total(self) -> Decimal:
        """Returns the total amount of the credit records.

        Returns:
            The total amount of the credit records.
        """
        return sum([Decimal(x.data["amount"]) for x in self.credit_records
                    if "amount" in x.data and "amount" not in x.errors])


class TransactionSortForm(forms.Form):
    """A form to sort the transactions in a same day."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date = None
        self.txn_list: Optional[List[Transaction]] = None
        self.txn_orders: List[TransactionSortForm.Order] = []

    @staticmethod
    def from_post(date: datetime.date, post: Dict[str, str]):
        form = TransactionSortForm({})
        form.date = date
        post_orders: List[TransactionSortForm.Order] = []
        for txn in Transaction.objects.filter(date=date).all():
            key = F"transaction-{txn.pk}-ord"
            if key not in post:
                post_orders.append(form.Order(txn, 9999))
            elif not re.match("^[0-9]+$", post[key]):
                post_orders.append(form.Order(txn, 9999))
            else:
                post_orders.append(form.Order(txn, int(post[key])))
        post_orders.sort(key=lambda x: (x.order, x.txn.ord))
        form.txn_orders = []
        for i in range(len(post_orders)):
            form.txn_orders.append(form.Order(post_orders[i].txn, i + 1))
        form.txn_list = [x.txn for x in form.txn_orders]
        return form

    class Order:
        """A transaction order"""
        def __init__(self, txn: Transaction, order: int):
            self.txn = txn
            self.order = order


class AccountForm(forms.Form):
    """An account form."""
    code = forms.CharField(
        error_messages={
            "required": _("Please fill in the code."),
            "invalid": _("Please fill in a number."),
            "max_length": _("This code is too long  (max. 5)."),
            "min_value": _("This code is too long  (max. 5)."),
        }, validators=[
            RegexValidator(
                regex="^[1-9]+$",
                message=_("You can only use numbers 1-9 in the code.")),
        ])
    title = forms.CharField(
        max_length=128,
        error_messages={
            "required": _("Please fill in the title."),
            "max_length": _("This title is too long  (max. 128)."),
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.account = None

    @property
    def parent(self) -> Optional[Account]:
        """The parent account, or None if this is the topmost account."""
        code = self["code"].value()
        if code is None or len(code) < 2:
            return None
        return Account.objects.get(code=code[:-1])

    def clean(self):
        """Validates the form globally.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        errors = []
        validators = [self._validate_code_not_under_myself,
                      self._validate_code_unique,
                      self._validate_code_parent_exists,
                      self._validate_code_descendant_code_size]
        for validator in validators:
            try:
                validator()
            except forms.ValidationError as e:
                errors.append(e)
        if errors:
            raise forms.ValidationError(errors)

    def _validate_code_not_under_myself(self) -> None:
        """Validates whether the code is under itself.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if self.account is None:
            return
        if "code" not in self.data:
            return
        if self.data["code"] == self.account.code:
            return
        if not self.data["code"].startswith(self.account.code):
            return
        error = forms.ValidationError(
            _("You cannot set the code under itself."),
            code="not_under_myself")
        self.add_error("code", error)
        raise error

    def _validate_code_unique(self) -> None:
        """Validates whether the code is unique.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if "code" not in self.data:
            return
        try:
            if self.account is None:
                Account.objects.get(code=self.data["code"])
            else:
                Account.objects.get(Q(code=self.data["code"]),
                                    ~Q(pk=self.account.pk))
        except Account.DoesNotExist:
            return
        error = forms.ValidationError(_("This code is already in use."),
                                      code="code_unique")
        self.add_error("code", error)
        raise error

    def _validate_code_parent_exists(self) -> None:
        """Validates whether the parent account exists.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if "code" not in self.data:
            return
        if len(self.data["code"]) < 2:
            return
        try:
            Account.objects.get(code=self.data["code"][:-1])
        except Account.DoesNotExist:
            error = forms.ValidationError(
                _("The parent account of this code does not exist."),
                code="code_unique")
            self.add_error("code", error)
            raise error
        return

    def _validate_code_descendant_code_size(self) -> None:
        """Validates whether the codes of the descendants will be too long.

        Raises:
            forms.ValidationError: When the validation fails.
        """
        if "code" not in self.data:
            return
        if self.account is None:
            return
        cur_max_len = Account.objects\
            .filter(Q(code__startswith=self.account.code),
                    ~Q(pk=self.account.pk))\
            .aggregate(max_len=Max(Length("code")))["max_len"]
        if cur_max_len is None:
            return
        new_max_len = cur_max_len - len(self.account.code)\
            + len(self.data["code"])
        if new_max_len <= 5:
            return
        error = forms.ValidationError(
            _("The descendant account codes will be too long  (max. 5)."),
            code="descendant_code_size")
        self.add_error("code", error)
        raise error
