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

from django.db import models


class Subject(models.Model):
    """An accounting subject."""
    sn = models.IntegerField(primary_key=True)
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
    created_by_sn = models.IntegerField(
        default=923153018, db_column="createdby")
    updated_at = models.DateTimeField(
        auto_now_add=True, db_column="updated")
    updated_by_sn = models.IntegerField(
        default=923153018, db_column="updatedby")

    def __str__(self):
        """Returns the string representation of this accounting
        subject."""
        return self.code.__str__() + " " + self.title_zhtw.__str__()

    class Meta:
        db_table = "accounting_subjects"
        ordering = ["code"]


class Transaction(models.Model):
    """An accounting transaction."""
    sn = models.IntegerField(primary_key=True)
    date = models.DateField(auto_now_add=True)
    ord = models.PositiveSmallIntegerField(default=1)
    note = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(
        auto_now_add=True, db_column="created")
    created_by_sn = models.IntegerField(
        default=923153018, db_column="createdby")
    updated_at = models.DateTimeField(
        auto_now_add=True, db_column="updated")
    updated_by_sn = models.IntegerField(
        default=923153018, db_column="updatedby")

    def __str__(self):
        """Returns the string representation of this accounting
        transaction."""
        return self.date.__str__() + " #" + self.ord.__str__()

    class Meta:
        db_table = "accounting_transactions"
        ordering = ["date", "ord"]


class Record(models.Model):
    """An accounting record."""
    sn = models.IntegerField(primary_key=True)
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
    created_by_sn = models.IntegerField(
        default=923153018, db_column="createdby")
    updated_at = models.DateTimeField(
        auto_now_add=True, db_column="updated")
    updated_by_sn = models.IntegerField(
        default=923153018, db_column="updatedby")

    def __str__(self):
        """Returns the string representation of this accounting
        record."""
        return self.transaction.date.__str__() + " "\
               + self.subject.title_zhtw.__str__()\
               + " " + self.summary.__str__()\
               + " " + self.amount.__str__()

    class Meta:
        db_table = "accounting_records"
        ordering = ["is_credit", "ord"]
