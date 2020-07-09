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
         views.CashReportView.as_view(), name="cash"),
    path("transactions/<txn-type:type>/<int:pk>",
         views.CashReportView.as_view(), name="transactions.view"),
    path("transactions/<txn-type:type>/<int:pk>/edit",
         views.CashReportView.as_view(), name="transactions.edit"),
]
