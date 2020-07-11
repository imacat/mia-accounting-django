# The accounting application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/6/30

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

"""The route settings of the accounting application.

"""

from django.urls import path, register_converter

from . import views
from mia_core import views as mia_core_views


class TransactionTypeConverter:
    """The path converter for the transaction types."""
    regex = "income|expense|transfer"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(TransactionTypeConverter, "txn-type")

app_name = "accounting"
urlpatterns = [
    path("", views.home, name="home"),
    path("cash", views.cash_home, name="cash.home"),
    path("cash/<str:subject_code>/<str:period_spec>",
         views.cash, name="cash"),
    path("cash-summary",
         mia_core_views.todo, name="cash-summary.home"),
    path("cash-summary/<str:subject_code>",
         mia_core_views.todo, name="cash-summary"),
    path("ledger",
         mia_core_views.todo, name="ledger.home"),
    path("ledger/<str:subject_code>/<str:period_spec>",
         mia_core_views.todo, name="ledger"),
    path("ledger-summary",
         mia_core_views.todo, name="ledger-summary.home"),
    path("ledger-summary/<str:subject_code>",
         mia_core_views.todo, name="ledger-summary"),
    path("journal",
         mia_core_views.todo, name="journal.home"),
    path("journal/<str:period_spec>",
         mia_core_views.todo, name="journal"),
    path("trial-balance",
         mia_core_views.todo, name="trial-balance.home"),
    path("trial-balance/<str:period_spec>",
         mia_core_views.todo, name="trial-balance"),
    path("income-statement",
         mia_core_views.todo, name="income-statement.home"),
    path("income-statement/<str:period_spec>",
         mia_core_views.todo, name="income-statement"),
    path("balance-sheet",
         mia_core_views.todo, name="balance-sheet.home"),
    path("balance-sheet/<str:period_spec>",
         mia_core_views.todo, name="balance-sheet"),
    path("search",
         mia_core_views.todo, name="search"),
    path("transactions/<txn-type:type>/create",
         mia_core_views.todo, name="transactions.create"),
    path("transactions/<txn-type:type>/store",
         mia_core_views.todo, name="transactions.store"),
    path("transactions/<txn-type:type>/<int:pk>",
         mia_core_views.todo, name="transactions.view"),
    path("transactions/<txn-type:type>/<int:pk>/edit",
         mia_core_views.todo, name="transactions.edit"),
    path("transactions/<txn-type:type>/<int:pk>/update",
         mia_core_views.todo, name="transactions.update"),
    path("transactions/<int:pk>/delete",
         mia_core_views.todo, name="transactions.delete"),
    path("subjects",
         mia_core_views.todo, name="subjects"),
    path("subjects/create",
         mia_core_views.todo, name="subjects.create"),
    path("subjects/store",
         mia_core_views.todo, name="subjects.store"),
    path("subjects/<str:subject_code>",
         mia_core_views.todo, name="subjects.view"),
    path("subjects/<str:subject_code>/edit",
         mia_core_views.todo, name="subjects.edit"),
    path("subjects/<str:subject_code>/update",
         mia_core_views.todo, name="subjects.update"),
    path("subjects/<str:subject_code>/delete",
         mia_core_views.todo, name="subjects.delete"),
]
