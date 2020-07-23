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
from . import converters, views

register_converter(converters.PeriodConverter, "period")
register_converter(converters.CashAccountConverter, "cash-account")
register_converter(converters.LedgerAccountConverter, "ledger-account")
register_converter(converters.TransactionTypeConverter, "txn-type")
register_converter(converters.TransactionConverter, "txn")

app_name = "accounting"
urlpatterns = [
    path("", views.home, name="home"),
    path("cash", views.cash_default, name="cash.home"),
    path("cash/<cash-account:account>/<period:period>",
         views.cash, name="cash"),
    path("cash-summary",
         views.cash_summary_default, name="cash-summary.home"),
    path("cash-summary/<cash-account:account>",
         views.cash_summary, name="cash-summary"),
    path("ledger",
         views.ledger_default, name="ledger.home"),
    path("ledger/<ledger-account:account>/<period:period>",
         views.ledger, name="ledger"),
    path("ledger-summary",
         views.ledger_summary_default, name="ledger-summary.home"),
    path("ledger-summary/<ledger-account:account>",
         views.ledger_summary, name="ledger-summary"),
    path("journal",
         views.journal_default, name="journal.home"),
    path("journal/<period:period>",
         views.journal, name="journal"),
    path("trial-balance",
         views.trial_balance_default, name="trial-balance.home"),
    path("trial-balance/<period:period>",
         views.trial_balance, name="trial-balance"),
    path("income-statement",
         views.income_statement_default, name="income-statement.home"),
    path("income-statement/<period:period>",
         views.income_statement, name="income-statement"),
    path("balance-sheet",
         views.balance_sheet_default, name="balance-sheet.home"),
    path("balance-sheet/<period:period>",
         views.balance_sheet, name="balance-sheet"),
    path("search",
         views.search, name="search"),
    path("transactions/<txn-type:type>/create",
         mia_core_views.todo, name="transactions.create"),
    path("transactions/<txn-type:type>/store",
         mia_core_views.todo, name="transactions.store"),
    path("transactions/<txn-type:type>/<txn:transaction>",
         views.transaction_show, name="transactions.show"),
    path("transactions/<txn-type:type>/<txn:transaction>/edit",
         mia_core_views.todo, name="transactions.edit"),
    path("transactions/<txn-type:type>/<txn:transaction>/update",
         mia_core_views.todo, name="transactions.update"),
    path("transactions/<txn:transaction>/delete",
         mia_core_views.todo, name="transactions.delete"),
    path("accounts",
         mia_core_views.todo, name="accounts"),
    path("accounts/create",
         mia_core_views.todo, name="accounts.create"),
    path("accounts/store",
         mia_core_views.todo, name="accounts.store"),
    path("accounts/<str:account_code>",
         mia_core_views.todo, name="accounts.show"),
    path("accounts/<str:account_code>/edit",
         mia_core_views.todo, name="accounts.edit"),
    path("accounts/<str:account_code>/update",
         mia_core_views.todo, name="accounts.update"),
    path("accounts/<str:account_code>/delete",
         mia_core_views.todo, name="accounts.delete"),
]
