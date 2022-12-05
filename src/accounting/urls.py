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
from django.views.decorators.http import require_GET

from mia_core.views import RedirectView
from . import converters, views

register_converter(converters.PeriodConverter, "period")
register_converter(converters.AccountConverter, "account")
register_converter(converters.CashAccountConverter, "cash-account")
register_converter(converters.LedgerAccountConverter, "ledger-account")
register_converter(converters.TransactionTypeConverter, "txn-type")
register_converter(converters.TransactionConverter, "txn")
register_converter(converters.DateConverter, "date")

app_name = "accounting"
urlpatterns = [
    path("", require_GET(RedirectView.as_view(
        query_string=True,
        pattern_name="accounting:cash.home",
    )), name="home"),
    path("cash",
         views.CashDefaultView.as_view(), name="cash.home"),
    path("cash/<cash-account:account>/<period:period>",
         views.cash, name="cash"),
    path("cash-summary",
         views.CashSummaryDefaultView.as_view(), name="cash-summary.home"),
    path("cash-summary/<cash-account:account>",
         views.cash_summary, name="cash-summary"),
    path("ledger",
         views.LedgerDefaultView.as_view(), name="ledger.home"),
    path("ledger/<ledger-account:account>/<period:period>",
         views.ledger, name="ledger"),
    path("ledger-summary",
         views.LedgerSummaryDefaultView.as_view(), name="ledger-summary.home"),
    path("ledger-summary/<ledger-account:account>",
         views.ledger_summary, name="ledger-summary"),
    path("journal",
         views.JournalDefaultView.as_view(), name="journal.home"),
    path("journal/<period:period>",
         views.journal, name="journal"),
    path("trial-balance",
         views.TrialBalanceDefaultView.as_view(), name="trial-balance.home"),
    path("trial-balance/<period:period>",
         views.trial_balance, name="trial-balance"),
    path("income-statement",
         views.IncomeStatementDefaultView.as_view(),
         name="income-statement.home"),
    path("income-statement/<period:period>",
         views.income_statement, name="income-statement"),
    path("balance-sheet",
         views.BalanceSheetDefaultView.as_view(), name="balance-sheet.home"),
    path("balance-sheet/<period:period>",
         views.balance_sheet, name="balance-sheet"),
    path("search",
         views.SearchListView.as_view(), name="search"),
    path("transactions/<txn-type:txn_type>/create",
         views.TransactionFormView.as_view(), name="transactions.create"),
    path("transactions/<txn-type:txn_type>/<txn:txn>",
         views.TransactionView.as_view(), name="transactions.detail"),
    path("transactions/<txn-type:txn_type>/<txn:txn>/update",
         views.TransactionFormView.as_view(), name="transactions.update"),
    path("transactions/<txn:txn>/delete",
         views.TransactionDeleteView.as_view(), name="transactions.delete"),
    path("transactions/sort/<date:date>",
         views.TransactionSortFormView.as_view(), name="transactions.sort"),
    path("accounts",
         views.AccountListView.as_view(), name="accounts"),
    path("accounts/create",
         views.AccountFormView.as_view(), name="accounts.create"),
    path("accounts/<account:account>",
         views.AccountView.as_view(), name="accounts.detail"),
    path("accounts/<account:account>/update",
         views.AccountFormView.as_view(), name="accounts.update"),
    path("accounts/<account:account>/delete",
         views.account_delete, name="accounts.delete"),
    path("api/accounts",
         views.api_account_list, name="api.accounts"),
    path("api/accounts/options",
         views.api_account_options, name="api.accounts.options"),
]
