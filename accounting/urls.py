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

from mia_core import views as mia_core_views
from . import views, converters
from .views import reports

register_converter(converters.TransactionTypeConverter, "txn-type")

register_converter(converters.PeriodConverter, "period")

app_name = "accounting"
urlpatterns = [
    path("", views.home, name="home"),
    path("cash", reports.cash_default, name="cash.home"),
    path("cash/<str:account_code>/<period:period>",
         reports.cash, name="cash"),
    path("cash-summary",
         reports.cash_summary_default, name="cash-summary.home"),
    path("cash-summary/<str:account_code>",
         reports.cash_summary, name="cash-summary"),
    path("ledger",
         reports.ledger_default, name="ledger.home"),
    path("ledger/<str:account_code>/<period:period>",
         reports.ledger, name="ledger"),
    path("ledger-summary",
         reports.ledger_summary_default, name="ledger-summary.home"),
    path("ledger-summary/<str:account_code>",
         reports.ledger_summary, name="ledger-summary"),
    path("journal",
         reports.journal_default, name="journal.home"),
    path("journal/<period:period>",
         reports.journal, name="journal"),
    path("trial-balance",
         reports.trial_balance_default, name="trial-balance.home"),
    path("trial-balance/<period:period>",
         reports.trial_balance, name="trial-balance"),
    path("income-statement",
         reports.income_statement_default, name="income-statement.home"),
    path("income-statement/<period:period>",
         reports.income_statement, name="income-statement"),
    path("balance-sheet",
         reports.balance_sheet_default, name="balance-sheet.home"),
    path("balance-sheet/<period:period>",
         reports.balance_sheet, name="balance-sheet"),
    path("search",
         reports.search, name="search"),
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
    path("accounts",
         mia_core_views.todo, name="accounts"),
    path("accounts/create",
         mia_core_views.todo, name="accounts.create"),
    path("accounts/store",
         mia_core_views.todo, name="accounts.store"),
    path("accounts/<str:account_code>",
         mia_core_views.todo, name="accounts.view"),
    path("accounts/<str:account_code>/edit",
         mia_core_views.todo, name="accounts.edit"),
    path("accounts/<str:account_code>/update",
         mia_core_views.todo, name="accounts.update"),
    path("accounts/<str:account_code>/delete",
         mia_core_views.todo, name="accounts.delete"),
]
