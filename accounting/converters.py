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
import datetime
import re

from django.utils.translation import gettext as _

from .models import Transaction, Record, Account
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
    regex = ("([0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?)|"
             "([0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?)?-"
             "([0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?)?")

    def to_python(self, value):
        """Returns the period by the period specification.

        Args:
            value (str): The period specification.

        Returns:
            Period: The period.

        Raises:
            ValueError: When the period specification is invalid.
        """
        first_txn = Transaction.objects.order_by("date").first()
        data_start = first_txn.date if first_txn is not None else None
        last_txn = Transaction.objects.order_by("-date").first()
        data_end = last_txn.date if last_txn is not None else None
        # Raises ValueError
        return Period(value, data_start, data_end)

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


class DateConverter:
    """The path converter for the date."""
    regex = "([0-9]{4})-([0-9]{2})-([0-9]{2})"

    def to_python(self, value):
        """Returns the date by the date specification.

        Args:
            value (str): The date specification.

        Returns:
            datetime.date: The date.
        """
        m = re.match("^([0-9]{4})-([0-9]{2})-([0-9]{2})$", value)
        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        return datetime.date(year, month, day)

    def to_url(self, value):
        """Returns the specification of a date.

        Args:
            value (datetime.date): The date.

        Returns:
            str: The date specification.
        """
        return value.strftime("%Y-%m-%d")


class AccountConverter:
    """The path converter for the account."""
    regex = "[1-9]{1,5}"

    def to_python(self, value):
        """Returns the account by the account code.

        Args:
            value (str): The account code.

        Returns:
            Account: The account.
        """
        try:
            return Account.objects.get(code=value)
        except Account.DoesNotExist:
            raise ValueError

    def to_url(self, value):
        """Returns the code of an account.

        Args:
            value (Account): The account.

        Returns:
            str: The account code.
        """
        return value.code


class CashAccountConverter:
    """The path converter for the cash account."""
    regex = "0|(11|12|21|22)[1-9]{1,3}"

    def to_python(self, value: str) -> Account:
        """Returns the cash account by the account code.

        Args:
            value: The account code.

        Returns:
            The account.

        Raises:
            ValueError: When the value is invalid
        """
        if value == "0":
            return Account(
                code="0",
                title=_("current assets and liabilities"),
            )
        try:
            account = Account.objects.get(code=value)
        except Account.DoesNotExist:
            raise ValueError
        if Record.objects.filter(account=account).count() == 0:
            raise ValueError
        return account

    def to_url(self, value: Account) -> str:
        """Returns the code of an account.

        Args:
            value: The account.

        Returns:
            The account code.
        """
        return value.code


class LedgerAccountConverter:
    """The path converter for the ledger account."""
    regex = "[1-9]{1,5}"

    def to_python(self, value: str) -> Account:
        """Returns the ledger account by the account code.

        Args:
            value: The account code.

        Returns:
            The account.

        Raises:
            ValueError: When the value is invalid
        """
        try:
            account = Account.objects.get(code=value)
        except Account.DoesNotExist:
            raise ValueError
        if Record.objects.filter(account__code__startswith=value).count() == 0:
            raise ValueError
        return account

    def to_url(self, value: Account) -> str:
        """Returns the code of an account.

        Args:
            value: The account.

        Returns:
            The account code.
        """
        return value.code


class TransactionConverter:
    """The path converter for the accounting transactions."""
    regex = "[1-9][0-9]{8}"

    def to_python(self, value: str) -> Transaction:
        """Returns the transaction by the transaction ID.

        Args:
            value: The transaction ID.

        Returns:
            The account.

        Raises:
            ValueError: When the value is invalid
        """
        try:
            return Transaction.objects.get(pk=value)
        except Transaction.DoesNotExist:
            raise ValueError

    def to_url(self, value: Transaction) -> str:
        """Returns the ID of a transaction.

        Args:
            value: The transaction.

        Returns:
            The transaction ID.
        """
        return value.pk
