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

"""The data models of the Mia core application.

"""
import hashlib

from dirtyfields import DirtyFieldsMixin
from django.conf import settings
from django.db import models, connection, OperationalError, transaction, \
    ProgrammingError
from django.db.models.functions import Now
from django.urls import reverse

from mia_core.utils import get_multi_lingual_attr, set_multi_lingual_attr, \
    new_pk


class Country(DirtyFieldsMixin, models.Model):
    """A country."""
    id = models.PositiveIntegerField(primary_key=True, db_column="sn")
    code = models.CharField(max_length=2, unique=True, db_column="id")
    name_en = models.CharField(max_length=64)
    name_zh_hant = models.CharField(
        max_length=32, null=True, db_column="name_zhtw")
    name_zh_hans = models.CharField(
        max_length=32, null=True, db_column="name_zhcn")
    is_special = models.BooleanField(
        default=False, db_column="special")
    created_at = models.DateTimeField(
        auto_now_add=True, db_column="created")
    created_by = models.ForeignKey(
        "User", on_delete=models.PROTECT,
        db_column="createdby", related_name="created_countries")
    updated_at = models.DateTimeField(
        auto_now=True, db_column="updated")
    updated_by = models.ForeignKey(
        "User", on_delete=models.PROTECT,
        db_column="updatedby", related_name="updated_countries")

    def __str__(self):
        """Returns the string representation of this country."""
        return self.code.__str__() + " " + self.name.__str__()

    @property
    def name(self) -> str:
        """The country name in the current language."""
        return get_multi_lingual_attr(self, "name", "en")

    @name.setter
    def name(self, value: str) -> None:
        set_multi_lingual_attr(self, "name", value)

    class Meta:
        db_table = "country"


class User(DirtyFieldsMixin, models.Model):
    """A user."""
    id = models.PositiveIntegerField(primary_key=True, db_column="sn")
    login_id = models.CharField(max_length=32, unique=True, db_column="id")
    password = models.CharField(max_length=32, db_column="passwd")
    name = models.CharField(max_length=32)
    is_disabled = models.BooleanField(
        default=False, db_column="disabled")
    is_deleted = models.BooleanField(
        default=False, db_column="deleted")
    language = models.CharField(max_length=6, null=True, db_column="lang")
    visits = models.PositiveSmallIntegerField(default=0)
    visited_at = models.DateTimeField(null=True, db_column="visited")
    visited_ip = models.GenericIPAddressField(null=True, db_column="ip")
    visited_host = models.CharField(
        max_length=128, null=True, db_column="host")
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
    REQUIRED_FIELDS = ["id", "name"]
    USERNAME_FIELD = "login_id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_user = None

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def is_authenticated(self) -> bool:
        return True

    def set_password(self):
        pass

    def check_password(self):
        pass

    def __str__(self):
        """Returns the string representation of this user."""
        return "%s (%s)" % (
            self.name.__str__(), self.login_id.__str__())

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.pk is None:
            self.pk = new_pk(User)
            if self.current_user is not None:
                self.created_by = self.current_user
        if self.current_user is not None:
            self.updated_by = self.current_user
        with transaction.atomic():
            super(User, self).save(
                force_insert=force_insert, force_update=force_update,
                using=using, update_fields=update_fields)
            User.objects.filter(pk=self.pk).update(updated_at=Now())

    class Meta:
        db_table = "users"
        app_label = "mia_core"

    def set_digest_password(self, login_id, password):
        self.password = self.md5(
            F"{login_id}:{settings.DIGEST_REALM}:{password}")

    @staticmethod
    def md5(value: str) -> str:
        m = hashlib.md5()
        m.update(value.encode("utf-8"))
        return m.hexdigest()

    def is_in_use(self) -> bool:
        """Returns whether this user is in use.

        Returns:
            True if this user is in use, or False otherwise.
        """
        for table in connection.introspection.table_names():
            if self._is_in_use_with(F"SELECT * FROM {table}"
                                    " WHERE createdby=%s OR updatedby=%s"):
                return True
            if self._is_in_use_with(
                    F"SELECT * FROM {table}"
                    " WHERE created_by_id=%s OR updated_by_id=%s"):
                return True
        return False

    def _is_in_use_with(self, sql: str) -> bool:
        """Returns whether this user is in use with a specific SQL statement.

        Args:
            sql: The SQL query statement

        Returns:
            True if this user is in use, or False otherwise.
        """
        with connection.cursor() as cursor:
            try:
                cursor.execute(sql, [self.pk, self.pk])
            except OperationalError:
                return False
            except ProgrammingError:
                return False
            if cursor.fetchone() is None:
                return False
            return True
