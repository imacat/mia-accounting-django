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


class Subject(models.Model):
    """An accounting subject."""
    sn = models.PositiveIntegerField(primary_key=True)
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True,
        db_column="parent_sn")
    code = models.CharField(max_length=5)
    title_zhtw = models.CharField(max_length=32)
    title_en = models.CharField(max_length=128, null=True, blank=True)
    title_zhcn = models.CharField(
        max_length=32, null=True, blank=True)
    created_at = models.DateTimeField(
        auto_now_add=True, db_column="created")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        db_column="createdby",
        related_name="created_accounting_subjects")
    updated_at = models.DateTimeField(
        auto_now_add=True, db_column="updated")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        db_column="updatedby",
        related_name="updated_accounting_subjects")

    def __str__(self):
        """Returns the string representation of this accounting
        subject."""
        return self.code.__str__() + " " + self.title_zhtw.__str__()

    class Meta:
        db_table = "accounting_subjects"
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

    @property
    def has_order_hole(self):
        """Whether the order of the transactions on this day is not
        1, 2, 3, 4, 5..., and should be reordered. """
        if self._has_order_hole is None:
            orders = [x.ord for x in Transaction.objects.filter(
                date=self.date).order_by("-ord")]
            if orders[0] != len(orders):
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
                and debit_records[0].subject.code == "1111"
                and debit_records[0].summary is None)

    @property
    def is_cash_expense(self):
        """Whether this transaction is a cash expense transaction."""
        credit_records = self.credit_records
        return (len(credit_records) == 1
                and credit_records[0].subject.code == "1111"
                and credit_records[0].summary is None)

    def get_absolute_url(self):
        """Returns the URL to view this transaction."""
        if self.is_cash_expense:
            return reverse(
                "accounting:transaction", args=("expense", self.sn))
        elif self.is_cash_income:
            return reverse(
                "accounting:transaction", args=("income", self.sn))
        else:
            return reverse(
                "accounting:transaction", args=("transfer", self.sn))

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
    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, db_column="subject_sn")
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

    @property
    def debit_amount(self):
        """The debit amount of this accounting record"""
        return self.amount if not self.is_credit else None

    @property
    def credit_amount(self):
        """The credit amount of this accounting record"""
        return self.amount if self.is_credit else None

    @property
    def accumulative_balance(self):
        return self._accumulative_balance

    @accumulative_balance.setter
    def accumulative_balance(self, value):
        self._accumulative_balance = value

    def __str__(self):
        """Returns the string representation of this accounting
        record."""
        return "%s %s %s %s" % (
            self.transaction.date,
            self.subject.title_zhtw,
            self.summary,
            self.amount)

    class Meta:
        db_table = "accounting_records"
        ordering = ["is_credit", "ord"]
