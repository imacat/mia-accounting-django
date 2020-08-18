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
from django.conf import settings
from django.db import models

from mia_core.utils import new_pk


class BaseModel(models.Model):
    """The common abstract base model that has id, created_at, created_by,
    updated_at, and updated_by."""
    id = models.PositiveIntegerField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="created_%(app_label)s_%(class)s")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="updated_%(app_label)s_%(class)s")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_user = None

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.pk is None:
            self.pk = new_pk(self.__class__)
            if self.current_user is not None:
                self.created_by = self.current_user
        if self.current_user is not None:
            self.updated_by = self.current_user
        super().save(force_insert=force_insert, force_update=force_update,
                     using=using, update_fields=update_fields)

    class Meta:
        abstract = True
