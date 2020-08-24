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
from typing import Any, Dict, List

from dirtyfields import DirtyFieldsMixin
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from mia_core.utils import new_pk, Language


class RandomPkModel(models.Model):
    """The abstract data model that uses 9-digit random primary keys."""
    id = models.PositiveIntegerField(primary_key=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.pk is None:
            self.pk = new_pk(self.__class__)
        super().save(force_insert=force_insert, force_update=force_update,
                     using=using, update_fields=update_fields)

    class Meta:
        abstract = True


class StampedModel(models.Model):
    """The abstract base model that has created_at, created_by, updated_at, and
    updated_by."""
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="created_%(app_label)s_%(class)s")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="updated_%(app_label)s_%(class)s")

    def __init__(self, *args, **kwargs):
        self.current_user = None
        if "current_user" in kwargs:
            self.current_user = kwargs["current_user"]
            del kwargs["current_user"]
        super().__init__(*args, **kwargs)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.current_user is None:
            raise AttributeError(
                F"Missing current_user in {self.__class__.__name__}")
        try:
            self.created_by
        except ObjectDoesNotExist as e:
            self.created_by = self.current_user
        self.updated_by = self.current_user
        super().save(force_insert=force_insert, force_update=force_update,
                     using=using, update_fields=update_fields)

    class Meta:
        abstract = True


class LocalizedModel(models.Model):
    """An abstract localized model."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if getattr(self, "_l10n", None) is None:
            self._l10n: Dict[str, Dict[str, Any]] = {}
        # Amends the is_dirty() method in DirtyFieldsMixin
        if isinstance(self, DirtyFieldsMixin):
            old_is_dirty = getattr(self, "is_dirty", None)

            def new_is_dirty(check_relationship=False, check_m2m=None) -> bool:
                """Returns whether the current data model is changed."""
                if old_is_dirty(check_relationship=check_relationship,
                                check_m2m=check_m2m):
                    return True
                default_language = self._get_default_language()
                for name in self._l10n:
                    for language in self._l10n[name]:
                        new_value = self._l10n[name][language]
                        if language == default_language:
                            if getattr(self, name + "_l10n") != new_value:
                                return True
                        else:
                            l10n_rec = self._get_l10n_set() \
                                .filter(name=name, language=language) \
                                .first()
                            if l10n_rec is None or l10n_rec.value != new_value:
                                return True
                return False
            self.is_dirty = new_is_dirty

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """Saves the data model, along with the localized contents."""
        default_language = self._get_default_language()
        l10n_to_save: List[models.Model] = []
        if getattr(self, "_l10n", None) is not None:
            for name in self._l10n:
                for language in self._l10n[name]:
                    new_value = self._l10n[name][language]
                    if language == default_language:
                        setattr(self, name + "_l10n", new_value)
                    else:
                        current_value = getattr(self, name + "_l10n")
                        if current_value is None or current_value == "":
                            setattr(self, name + "_l10n", new_value)
                        l10n_rec = self._get_l10n_set()\
                            .filter(name=name, language=language)\
                            .first()
                        if l10n_rec is None:
                            l10n_to_save.append(self._get_l10n_set().model(
                                master=self, name=name,
                                language=language,
                                value=self._l10n[name][language]))
                        elif l10n_rec.value != new_value:
                            if getattr(self, name + "_l10n") == l10n_rec.value:
                                setattr(self, name + "_l10n", new_value)
                            l10n_rec.value = new_value
                            l10n_to_save.append(l10n_rec)
        super().save(force_insert=force_insert, force_update=force_update,
                     using=using, update_fields=update_fields)
        for l10n_rec in l10n_to_save:
            if isinstance(self, StampedModel)\
                    and isinstance(l10n_rec, StampedModel):
                l10n_rec.current_user = self.current_user
            l10n_rec.save(force_insert=force_insert, force_update=force_update,
                          using=using, update_fields=update_fields)

    def _get_l10n_set(self):
        """Returns the related localization data model."""
        l10n_set = getattr(self, "l10n_set", None)
        if l10n_set is None:
            raise AttributeError("Please define the localization data model.")
        return l10n_set

    def _get_default_language(self) -> str:
        """Returns the default language."""
        default = getattr(self.__class__, "DEFAULT_LANGUAGE", None)
        return Language.default().id if default is None else default

    def get_l10n(self, name: str) -> Any:
        """Returns the value of a localized field in the current language.

        Args:
            name: The field name.

        Returns:
            The value of this field in the current language.
        """
        return self.get_l10n_in(name, Language.current().id)

    def get_l10n_in(self, name: str, language: str) -> Any:
        """Returns the value of a localized field in a specific language.

        Args:
            name: The field name.
            language: The language ID.

        Returns:
            The value of this field in this language.
        """
        if getattr(self, "_l10n", None) is None:
            self._l10n: Dict[str, Dict[str, Any]] = {}
        if name not in self._l10n:
            self._l10n[name]: Dict[str, Any] = {}
        if language not in self._l10n[name]:
            if language != self._get_default_language():
                l10n_rec = self._get_l10n_set() \
                    .filter(name=name, language=language) \
                    .first()
                self._l10n[name][language] = getattr(self, name + "_l10n") \
                    if l10n_rec is None else l10n_rec.value
            else:
                self._l10n[name][language] = getattr(self, name + "_l10n")
        return self._l10n[name][language]

    def set_l10n(self, name: str, value: Any) -> None:
        """Sets the value of a localized field in the current language.

        Args:
            name: The field name.
            value: The value.
        """
        self.set_l10n_in(name, Language.current().id, value)

    def set_l10n_in(self, name: str, language: str, value: Any) -> None:
        """Sets the value of a localized field in a specific language.

        Args:
            name: The field name.
            language: The language ID.
            value: The value.
        """
        if getattr(self, "_l10n", None) is None:
            self._l10n: Dict[str, Dict[str, Any]] = {}
        if name not in self._l10n:
            self._l10n[name]: Dict[str, Any] = {}
        self._l10n[name][language] = value

    class Meta:
        abstract = True


class L10nModel(models.Model):
    """The abstract base localization model."""
    name = models.CharField(max_length=128)
    language = models.CharField(max_length=7)
    value = models.CharField(max_length=65535)

    class Meta:
        abstract = True
