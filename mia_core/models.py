# The core application of the Mia project.
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

"""The data models of the mia core application.

"""

from django.db import models


class Country(models.Model):
    """A country."""
    sn = models.PositiveIntegerField(primary_key=True)
    code = models.CharField(max_length=2, unique=True)
    name_en = models.CharField(max_length=64)
    name_zhtw = models.CharField(max_length=32, null=True)
    name_zhcn = models.CharField(max_length=32, null=True)
    is_special = models.BooleanField(
        default=False, db_column="special")
    created_at = models.DateTimeField(
        auto_now_add=True, db_column="created")
    created_by = models.ForeignKey(
        "User", on_delete=models.PROTECT,
        db_column="createdby", related_name="created_countries")
    updated_at = models.DateTimeField(
        auto_now_add=True, db_column="updated")
    updated_by = models.ForeignKey(
        "User", on_delete=models.PROTECT,
        db_column="updatedby", related_name="updated_countries")

    def __str__(self):
        """Returns the string representation of this country."""
        return self.code.__str__() + " " + self.name_zhtw.__str__()

    class Meta:
        db_table = "countries"
        ordering = ["code"]


class User(models.Model):
    """A user."""
    sn = models.PositiveIntegerField(primary_key=True)
    login_id = models.CharField(max_length=32, unique=True, db_column="id")
    password = models.CharField(max_length=32, db_column="passwd")
    name = models.CharField(max_length=32)
    is_disabled = models.BooleanField(
        default=False, db_column="disabled")
    is_deleted = models.BooleanField(
        default=False, db_column="deleted")
    language = models.CharField(max_length=6, null=True, db_column="lang")
    visits = models.PositiveSmallIntegerField(null=True)
    visited_at = models.DateTimeField(null=True, db_column="visited")
    visited_ip = models.GenericIPAddressField(null=True, db_column="ip")
    visited_host = models.CharField(max_length=128, null=True, db_column="host")
    visited_country = models.ForeignKey(
        Country, on_delete=models.PROTECT, null=True,
        db_column="ct", to_field="code", related_name="users")
    created_at = models.DateTimeField(
        auto_now_add=True, db_column="created")
    created_by = models.ForeignKey(
        "self", on_delete=models.PROTECT,
        db_column="createdby", related_name="created_users")
    updated_at = models.DateTimeField(
        auto_now_add=True, db_column="updated")
    updated_by = models.ForeignKey(
        "self", on_delete=models.PROTECT,
        db_column="updatedby", related_name="updated_users")
    REQUIRED_FIELDS = ["sn", "name"]
    USERNAME_FIELD = "login_id"

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    def set_password(self):
        pass

    def check_password(self):
        pass

    def __str__(self):
        """Returns the string representation of this user."""
        return "%s(%s)" % (
            self.name.__str__(), self.login_id.__str__())

    class Meta:
        db_table = "users"
        app_label = "mia_core"
        ordering = ["login_id"]
