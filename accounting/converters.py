# The accounting application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/7/23

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

"""The URL converters.

"""
from accounting.models import Transaction
from mia_core.period import Period


class TransactionTypeConverter:
    """The path converter for the transaction types."""
    regex = "income|expense|transfer"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


class PeriodConverter:
    """The path converter for the period."""
    regex = ".+"

    def to_python(self, value):
        """Returns the period by the period specification.

        Args:
            value (str): The period specification.

        Returns:
            Period: The period.
        """
        first_txn = Transaction.objects.order_by("date").first()
        data_start = first_txn.date if first_txn is not None else None
        last_txn = Transaction.objects.order_by("-date").first()
        data_end = last_txn.date if last_txn is not None else None
        period = Period(value, data_start, data_end)
        if period.error is not None:
            raise ValueError
        return period

    def to_url(self, value):
        """Returns the specification of a period.

        Args:
            value (Period|str): The period.

        Returns:
            str: The period specification.
        """
        if isinstance(value, Period):
            return value.spec
        return value
