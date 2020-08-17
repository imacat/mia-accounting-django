# The accounting application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/6/29

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

"""The data models of the accounting application.

"""
import datetime
from typing import Dict, List, Optional

from dirtyfields import DirtyFieldsMixin
from django.conf import settings
from django.db import models, transaction
from django.db.models import Q, Max
from django.urls import reverse

from mia_core.utils import get_multi_lingual_attr, set_multi_lingual_attr, \
    new_pk


class Account(DirtyFieldsMixin, models.Model):
    """An account."""
    id = models.PositiveIntegerField(primary_key=True)
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True,
        related_name="child_set")
    code = models.CharField(max_length=5, unique=True)
    title_zh_hant = models.CharField(max_length=32)
    title_en = models.CharField(max_length=128, null=True)
    title_zh_hans = models.CharField(max_length=32, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="created_accounting_accounts")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="updated_accounting_accounts")
    CASH = "1111"
    ACCUMULATED_BALANCE = "3351"
    NET_CHANGE = "3353"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = None
        self.debit_amount = None
        self.credit_amount = None
        self.amount = None
        self.is_for_debit = None
        self.is_for_credit = None
        self._is_in_use = None
        self._is_parent_and_in_use = None
        self.current_user = None

    def __str__(self):
        """Returns the string representation of this account."""
        return self.code.__str__() + " " + self.title

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.parent = None if len(self.code) == 1\
            else Account.objects.get(code=self.code[:-1])
        if self.pk is None:
            self.pk = new_pk(Account)
            if self.current_user is not None:
                self.created_by = self.current_user
        if self.current_user is not None:
            self.updated_by = self.current_user
        with transaction.atomic():
            super().save(force_insert=force_insert, force_update=force_update,
                         using=using, update_fields=update_fields)

    def get_absolute_url(self):
        """REturns the """
        return reverse("accounting:accounts.detail", args=(self,))

    class Meta:
        db_table = "accounting_accounts"

    @property
    def title(self) -> str:
        """The title in the current language."""
        return get_multi_lingual_attr(self, "title")

    @title.setter
    def title(self, value: str) -> None:
        set_multi_lingual_attr(self, "title", value)

    @property
    def option_data(self) -> Dict[str, str]:
        """The data as an option."""
        return {
            "code": self.code,
            "title": self.title,
        }

    @property
    def is_parent_and_in_use(self) -> bool:
        """Whether this is a parent account and is in use."""
        if self._is_parent_and_in_use is None:
            self._is_parent_and_in_use = self.child_set.count() > 0\
                                         and self.record_set.count() > 0
        return self._is_parent_and_in_use

    @is_parent_and_in_use.setter
    def is_parent_and_in_use(self, value: bool) -> None:
        self._is_parent_and_in_use = value

    @property
    def is_in_use(self) -> bool:
        """Whether this account is in use."""
        if self._is_in_use is None:
            self._is_in_use = self.child_set.count() > 0\
                              or self.record_set.count() > 0
        return self._is_in_use

    @is_in_use.setter
    def is_in_use(self, value: bool) -> None:
        self._is_in_use = value


class Transaction(DirtyFieldsMixin, models.Model):
    """An accounting transaction."""
    id = models.PositiveIntegerField(primary_key=True)
    date = models.DateField()
    ord = models.PositiveSmallIntegerField(default=1)
    notes = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="created_accounting_transactions")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="updated_accounting_transactions")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._records = None
        self._is_balanced = None
        self._has_order_hole = None
        self.old_date = None
        self.current_user = None

    def __str__(self):
        """Returns the string representation of this accounting
        transaction."""
        return self.date.__str__() + " #" + self.ord.__str__()

    def get_absolute_url(self) -> str:
        """Returns the URL to view this transaction."""
        if self.is_cash_expense:
            return reverse(
                "accounting:transactions.detail", args=("expense", self))
        elif self.is_cash_income:
            return reverse(
                "accounting:transactions.detail", args=("income", self))
        else:
            return reverse(
                "accounting:transactions.detail", args=("transfer", self))

    def is_dirty(self, check_relationship=False, check_m2m=None) -> bool:
        """Returns whether the data of this transaction is changed and need
        to be saved into the database.

        Returns:
            True if the data of this transaction is changed and need to be
            saved into the database, or False otherwise.
        """
        if super().is_dirty(check_relationship=check_relationship,
                            check_m2m=check_m2m):
            return True
        if len([x for x in self.records
                if x.is_dirty(check_relationship=check_relationship,
                              check_m2m=check_m2m)]) > 0:
            return True
        kept = [x.pk for x in self.records]
        if len([x for x in self.record_set.all() if x.pk not in kept]) > 0:
            return True
        return False

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # When the date is changed, the orders of the transactions in the same
        # day need to be reordered
        txn_to_sort = []
        if self.date != self.old_date:
            if self.old_date is not None:
                txn_same_day = list(
                    Transaction.objects
                    .filter(Q(date=self.old_date), ~Q(pk=self.pk))
                    .order_by("ord"))
                for i in range(len(txn_same_day)):
                    if txn_same_day[i].ord != i + 1:
                        txn_to_sort.append([txn_same_day[i], i + 1])
            max_ord = Transaction.objects\
                .filter(date=self.date)\
                .aggregate(max=Max("ord"))["max"]
            self.ord = 1 if max_ord is None else max_ord + 1
        # Collects the records to be deleted
        to_keep = [x.pk for x in self.records if x.pk is not None]
        to_delete = [x for x in self.record_set.all() if x.pk not in to_keep]
        # Applies the created by and updated by
        if self.pk is None:
            self.pk = new_pk(Transaction)
            if self.current_user is not None:
                self.created_by = self.current_user
        if self.current_user is not None:
            self.updated_by = self.current_user
        to_save = [x for x in self.records
                   if x.is_dirty(check_relationship=True)]
        for record in to_save:
            if record.pk is None:
                record.pk = new_pk(Record)
                if self.current_user is not None:
                    record.created_by = self.current_user
            if self.current_user is not None:
                record.updated_by = self.current_user
        # Runs the update
        with transaction.atomic():
            super().save(force_insert=force_insert, force_update=force_update,
                         using=using, update_fields=update_fields)
            for record in to_delete:
                record.delete()
            for record in to_save:
                record.save(force_insert=force_insert,
                            force_update=force_update,
                            using=using, update_fields=update_fields)
            for x in txn_to_sort:
                Transaction.objects.filter(pk=x[0].pk).update(ord=x[1])

    def delete(self, using=None, keep_parents=False):
        txn_same_day = list(
            Transaction.objects
            .filter(Q(date=self.date), ~Q(pk=self.pk))
            .order_by("ord"))
        txn_to_sort = []
        for i in range(len(txn_same_day)):
            if txn_same_day[i].ord != i + 1:
                txn_to_sort.append([txn_same_day[i], i + 1])
        with transaction.atomic():
            for record in self.record_set.all():
                record.delete()
            super().delete(using=using, keep_parents=keep_parents)
            for x in txn_to_sort:
                Transaction.objects.filter(pk=x[0].pk).update(ord=x[1])

    class Meta:
        db_table = "accounting_transactions"

    @property
    def records(self):
        """The records of the transaction.

        Returns:
            List[Record]: The records.
        """
        if self._records is None:
            self._records = list(self.record_set.all())
            self._records.sort(key=lambda x: (x.is_credit, x.ord))
        return self._records

    @records.setter
    def records(self, value):
        self._records = value

    @property
    def debit_records(self):
        """The debit records of this transaction.

        Returns:
            List[Record]: The records.
        """
        return [x for x in self.records if not x.is_credit]

    def debit_total(self) -> int:
        """The total amount of the debit records."""
        return sum([x.amount for x in self.debit_records
                    if isinstance(x.amount, int)])

    @property
    def debit_summaries(self) -> List[str]:
        """The summaries of the debit records."""
        return [x.account.title if x.summary is None else x.summary
                for x in self.debit_records]

    @property
    def credit_records(self):
        """The credit records of this transaction.

        Returns:
            List[Record]: The records.
        """
        return [x for x in self.records if x.is_credit]

    def credit_total(self) -> int:
        """The total amount of the credit records."""
        return sum([x.amount for x in self.credit_records
                    if isinstance(x.amount, int)])

    @property
    def credit_summaries(self) -> List[str]:
        """The summaries of the credit records."""
        return [x.account.title if x.summary is None else x.summary
                for x in self.credit_records]

    @property
    def amount(self) -> int:
        """The amount of this transaction."""
        return self.debit_total()

    @property
    def is_balanced(self) -> bool:
        """Whether the sum of the amounts of the debit records is the
        same as the sum of the amounts of the credit records. """
        if self._is_balanced is None:
            debit_sum = sum([x.amount for x in self.debit_records])
            credit_sum = sum([x.amount for x in self.credit_records])
            self._is_balanced = debit_sum == credit_sum
        return self._is_balanced

    @is_balanced.setter
    def is_balanced(self, value: bool) -> None:
        self._is_balanced = value

    def has_many_same_day(self) -> bool:
        """whether there are more than one transactions at this day,
        so that the user can sort their orders. """
        return Transaction.objects.filter(date=self.date).count() > 1

    @property
    def has_order_hole(self) -> bool:
        """Whether the order of the transactions on this day is not
        1, 2, 3, 4, 5..., and should be reordered. """
        if self._has_order_hole is None:
            orders = [x.ord for x in Transaction.objects.filter(
                date=self.date)]
            if len(orders) == 0:
                self._has_order_hole = False
            if max(orders) != len(orders):
                self._has_order_hole = True
            elif min(orders) != 1:
                self._has_order_hole = True
            elif len(orders) != len(set(orders)):
                self._has_order_hole = True
            else:
                self._has_order_hole = False
        return self._has_order_hole

    @has_order_hole.setter
    def has_order_hole(self, value: bool) -> None:
        self._has_order_hole = value

    @property
    def is_cash_income(self) -> bool:
        """Whether this transaction is a cash income transaction."""
        debit_records = self.debit_records
        return (len(debit_records) == 1
                and debit_records[0].account.code == Account.CASH
                and debit_records[0].summary is None)

    @property
    def is_cash_expense(self) -> bool:
        """Whether this transaction is a cash expense transaction."""
        credit_records = self.credit_records
        return (len(credit_records) == 1
                and credit_records[0].account.code == Account.CASH
                and credit_records[0].summary is None)

    @property
    def type(self) -> str:
        """The transaction type."""
        if self.is_cash_expense:
            return "expense"
        elif self.is_cash_income:
            return "income"
        else:
            return "transfer"


class Record(DirtyFieldsMixin, models.Model):
    """An accounting record."""
    id = models.PositiveIntegerField(primary_key=True)
    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE)
    is_credit = models.BooleanField()
    ord = models.PositiveSmallIntegerField()
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT)
    summary = models.CharField(max_length=128, blank=True, null=True)
    amount = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="created_accounting_records")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="updated_accounting_records")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._debit_amount = None
        self._credit_amount = None
        self.balance = None
        self._is_balanced = None
        self._has_order_hole = None
        self._is_payable = None
        self._is_existing_equipment = None
        self.is_payable = False
        self.is_existing_equipment = False

    def __str__(self):
        """Returns the string representation of this accounting
        record."""
        return "%s %s %s %s" % (
            self.transaction.date,
            self.account.title,
            self.summary,
            self.amount)

    class Meta:
        db_table = "accounting_records"

    @property
    def debit_amount(self) -> Optional[int]:
        """The debit amount of this accounting record."""
        if self._debit_amount is None:
            self._debit_amount = self.amount if not self.is_credit else None
        return self._debit_amount

    @debit_amount.setter
    def debit_amount(self, value: Optional[int]) -> None:
        self._debit_amount = value

    @property
    def credit_amount(self) -> Optional[int]:
        """The credit amount of this accounting record."""
        if self._credit_amount is None:
            self._credit_amount = self.amount if self.is_credit else None
        return self._credit_amount

    @credit_amount.setter
    def credit_amount(self, value: Optional[int]):
        self._credit_amount = value

    @property
    def is_balanced(self) -> bool:
        """Whether the transaction of this record is balanced. """
        if self._is_balanced is None:
            self._is_balanced = self.transaction.is_balanced
        return self._is_balanced

    @is_balanced.setter
    def is_balanced(self, value: bool) -> None:
        self._is_balanced = value

    @property
    def has_order_hole(self) -> bool:
        """Whether the order of the transactions on this day is not
        1, 2, 3, 4, 5..., and should be reordered. """
        if self._has_order_hole is None:
            self._has_order_hole = self.transaction.has_order_hole
        return self._has_order_hole

    @has_order_hole.setter
    def has_order_hole(self, value: bool) -> None:
        self._has_order_hole = value
