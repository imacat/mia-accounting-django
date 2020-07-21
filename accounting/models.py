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
from django.conf import settings
from django.db import models
from django.urls import reverse

from mia_core.templatetags.mia_core import smart_month
from mia_core.utils import get_multi_lingual_attr


class Account(models.Model):
    """An account."""
    sn = models.PositiveIntegerField(primary_key=True)
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True,
        db_column="parent_sn")
    code = models.CharField(max_length=5, unique=True)
    title_zh_hant = models.CharField(
        max_length=32, db_column="title_zhtw")
    title_en = models.CharField(max_length=128, null=True, blank=True)
    title_zh_hans = models.CharField(
        max_length=32, null=True, blank=True, db_column="title_zhcn")
    created_at = models.DateTimeField(
        auto_now_add=True, db_column="created")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        db_column="createdby",
        related_name="created_accounting_accounts")
    updated_at = models.DateTimeField(
        auto_now_add=True, db_column="updated")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        db_column="updatedby",
        related_name="updated_accounting_accounts")

    def __str__(self):
        """Returns the string representation of this account."""
        return self.code.__str__() + " " + self.title

    _title = None

    @property
    def title(self):
        if self._title is None:
            self._title = get_multi_lingual_attr(self, "title")
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    _url = None

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    class Meta:
        db_table = "accounting_accounts"
        ordering = ["code"]


class Transaction(models.Model):
    """An accounting transaction."""
    sn = models.PositiveIntegerField(primary_key=True)
    date = models.DateField()
    ord = models.PositiveSmallIntegerField(default=1)
    note = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(
        auto_now_add=True, db_column="created")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        db_column="createdby",
        related_name="created_accounting_transactions")
    updated_at = models.DateTimeField(
        auto_now_add=True, db_column="updated")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        db_column="updatedby",
        related_name="updated_accounting_transactions")

    @property
    def debit_records(self):
        """The debit records of this transaction."""
        return [x for x in self.record_set.all() if not x.is_credit]

    @property
    def credit_records(self):
        """The credit records of this transaction."""
        return [x for x in self.record_set.all() if x.is_credit]

    _is_balanced = None

    @property
    def is_balanced(self):
        """Whether the sum of the amounts of the debit records is the
        same as the sum of the amounts of the credit records. """
        if self._is_balanced is None:
            debit_sum = sum([x.amount for x in self.debit_records])
            credit_sum = sum([x.amount for x in self.credit_records])
            self._is_balanced = debit_sum == credit_sum
        return self._is_balanced

    @is_balanced.setter
    def is_balanced(self, value):
        self._is_balanced = value

    @property
    def has_many_same_day(self):
        """whether there are more than one transactions at this day,
        so that the user can sort their orders. """
        return Transaction.objects.filter(
            date=self.date).count() > 1

    _has_order_hole = None

    @property
    def has_order_hole(self):
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
    def has_order_hole(self, value):
        self._has_order_hole = value

    @property
    def is_cash_income(self):
        """Whether this transaction is a cash income transaction."""
        debit_records = self.debit_records
        return (len(debit_records) == 1
                and debit_records[0].account.code == "1111"
                and debit_records[0].summary is None)

    @property
    def is_cash_expense(self):
        """Whether this transaction is a cash expense transaction."""
        credit_records = self.credit_records
        return (len(credit_records) == 1
                and credit_records[0].account.code == "1111"
                and credit_records[0].summary is None)

    def get_absolute_url(self):
        """Returns the URL to view this transaction."""
        if self.is_cash_expense:
            return reverse(
                "accounting:transactions.view",
                args=("expense", self.sn))
        elif self.is_cash_income:
            return reverse(
                "accounting:transactions.view",
                args=("income", self.sn))
        else:
            return reverse(
                "accounting:transactions.view",
                args=("transfer", self.sn))

    def __str__(self):
        """Returns the string representation of this accounting
        transaction."""
        return self.date.__str__() + " #" + self.ord.__str__()

    class Meta:
        db_table = "accounting_transactions"
        ordering = ["date", "ord"]


class Record(models.Model):
    """An accounting record."""
    sn = models.PositiveIntegerField(primary_key=True)
    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE,
        db_column="transaction_sn")
    is_credit = models.BooleanField()
    ord = models.PositiveSmallIntegerField(default=1)
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, db_column="account_sn")
    summary = models.CharField(max_length=128, blank=True, null=True)
    amount = models.PositiveIntegerField()
    created_at = models.DateTimeField(
        auto_now_add=True, db_column="created")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        db_column="createdby",
        related_name="created_accounting_records")
    updated_at = models.DateTimeField(
        auto_now_add=True, db_column="updated")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        db_column="updatedby",
        related_name="updated_accounting_records")

    _debit_amount = None

    @property
    def debit_amount(self):
        """The debit amount of this accounting record"""
        if self._debit_amount is not None:
            return self._debit_amount
        return self.amount if not self.is_credit else None

    @debit_amount.setter
    def debit_amount(self, value):
        self._debit_amount = value

    _credit_amount = None

    @property
    def credit_amount(self):
        """The credit amount of this accounting record"""
        if self._credit_amount is not None:
            return self._credit_amount
        return self.amount if self.is_credit else None

    @credit_amount.setter
    def credit_amount(self, value):
        self._credit_amount = value

    _balance = None

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        self._balance = value

    _is_balanced = None

    @property
    def is_balanced(self):
        """Whether the transaction of this record is balanced. """
        if self._is_balanced is None:
            self._is_balanced = self.transaction.is_balanced
        return self._is_balanced

    @is_balanced.setter
    def is_balanced(self, value):
        self._is_balanced = value

    _has_order_hole = None

    @property
    def has_order_hole(self):
        """Whether the order of the transactions on this day is not
        1, 2, 3, 4, 5..., and should be reordered. """
        if self._has_order_hole is None:
            self._has_order_hole = self.transaction.has_order_hole
        return self._has_order_hole

    @has_order_hole.setter
    def has_order_hole(self, value):
        self._has_order_hole = value

    _is_credit_card_paid = None

    @property
    def is_credit_card_paid(self):
        # TODO: To be done
        if self._is_credit_card_paid is None:
            self._is_credit_card_paid = True
        return self._is_credit_card_paid

    @is_credit_card_paid.setter
    def is_credit_card_paid(self, value):
        self._is_credit_card_paid = value

    _is_existing_equipment = None

    @property
    def is_existing_equipment(self):
        # TODO: To be done
        if self._is_existing_equipment is None:
            self._is_existing_equipment = False
        return self._is_existing_equipment

    @is_existing_equipment.setter
    def is_existing_equipment(self, value):
        self._is_existing_equipment = value

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
        ordering = ["is_credit", "ord"]


class RecordSummary(models.Model):
    """A summary record."""
    month = models.DateField(primary_key=True)
    credit = models.PositiveIntegerField()
    debit = models.PositiveIntegerField()
    balance = models.IntegerField()

    _label = None

    @property
    def label(self):
        if self._label is None:
            self._label = smart_month(self.month)
        return self._label

    @label.setter
    def label(self, value):
        self._label = value

    _cumulative_balance = None

    @property
    def cumulative_balance(self):
        return self._cumulative_balance

    @cumulative_balance.setter
    def cumulative_balance(self, value):
        self._cumulative_balance = value

    class Meta:
        db_table = None
        managed = False
