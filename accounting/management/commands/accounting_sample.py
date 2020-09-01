# The accounting application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/7/22

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

"""The command to populate the database with sample accounting data.

"""
import datetime
import getpass
import random
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand, CommandParser, CommandError, \
    call_command
from django.db import transaction
from django.utils import timezone, formats
from django.utils.translation import gettext as _

from accounting.models import Account, Record
from accounting.utils import DataFiller


class Command(BaseCommand):
    """Populates the database with sample accounting data."""
    help = "Fills the database with sample accounting data."

    def __init__(self):
        super().__init__()
        self._filler: Optional[DataFiller] = None

    def add_arguments(self, parser):
        """Adds command line arguments to the parser.

        Args:
            parser (CommandParser): The command line argument parser.
        """
        parser.add_argument("--user", "-u", help="User")

    def handle(self, *args, **options):
        """Runs the command.

        Args:
            *args (list[str]): The command line arguments.
            **options (dict[str,str]): The command line switches.
        """
        if Record.objects.count() > 0:
            error = "Refuse to fill in sample data with existing data."
            raise CommandError(error, returncode=1)
        # Gets the user to use
        user = self.get_user(options["user"])
        if Account.objects.count() == 0:
            username = getattr(user, user.USERNAME_FIELD)
            call_command("accounting_accounts", F"-u={username}")
        self.stdout.write(F"Filling sample data as \"{user}\"")

        with transaction.atomic():
            self._filler = DataFiller(user)
            self.add_payrolls(5)

            self._filler.add_income_transaction(
                -15,
                [(1113, _("ATM withdrawal"), 2000)])
            self._filler.add_transfer_transaction(
                -14,
                [(6254, _("HSR—New Land→South Lake City"), 1490)],
                [(2141, _("HSR—New Land→South Lake City"), 1490)])
            self._filler.add_transfer_transaction(
                -14,
                [(6273, _("Movies—The Avengers"), 80)],
                [(2141, _("Movies—The Avengers"), 80)])
            self._filler.add_transfer_transaction(
                -13,
                [(6273, _("Movies—2001: A Space Odyssey"), 80)],
                [(2141, _("Movies—2001: A Space Odyssey"), 80)])
            self._filler.add_transfer_transaction(
                -11,
                [(2141, _("Movies—The Avengers"), 80)],
                [(1113, _("Movies—The Avengers"), 80)])

            self._filler.add_expense_transaction(
                -13,
                [(6273, _("Bus—2623—Uptown→City Park"), 477543627.4775)])

            self._filler.add_expense_transaction(
                -2,
                [(6272, _("Lunch—Spaghetti"), random.randint(40, 200)),
                 (6272, _("Drink—Tea"), random.randint(40, 200))])
            self._filler.add_expense_transaction(
                -1,
                ([(6272, _("Lunch—Pizza"), random.randint(40, 200)),
                 (6272, _("Drink—Tea"), random.randint(40, 200))]))
            self._filler.add_expense_transaction(
                -1,
                [(6272, _("Lunch—Spaghetti"), random.randint(40, 200)),
                 (6272, _("Drink—Soda"), random.randint(40, 200))])
            self._filler.add_expense_transaction(
                0,
                [(6272, _("Lunch—Salad"), random.randint(40, 200)),
                 (6272, _("Drink—Coffee"), random.randint(40, 200))])

    @staticmethod
    def get_user(username_option):
        """Returns the current user.

        Args:
            username_option: The username specified in the options.

        Returns:
            The current user.
        """
        user_model = get_user_model()
        if username_option is not None:
            try:
                return user_model.objects.get(**{
                    user_model.USERNAME_FIELD: username_option
                })
            except ObjectDoesNotExist:
                error = F"User \"{username_option}\" does not exist."
                raise CommandError(error, returncode=1)
        if user_model.objects.count() == 0:
            error = "Please run the \"createsuperuser\" command first."
            raise CommandError(error, returncode=1)
        if user_model.objects.count() == 1:
            return user_model.objects.first()
        try:
            return user_model.objects.get(**{
                user_model.USERNAME_FIELD: getpass.getuser()
            })
        except ObjectDoesNotExist:
            error = "Please specify the user with -u."
            raise CommandError(error, returncode=1)

    def add_payrolls(self, months: int):
        """Adds the payrolls for certain number of months.

        Args:
            months: The number of months to add.
        """
        today = timezone.localdate()
        payday = today.replace(day=5)
        if payday > today:
            payday = self.previous_month(payday)
        for i in range(months):
            self.add_payroll(payday)
            payday = self.previous_month(payday)

    @staticmethod
    def previous_month(date: datetime.date):
        """Obtain the same day in the previous month.

        Args:
            date: The date.

        Returns:
            The same day in the previous month.
        """
        month = date.month - 1
        if month < 1:
            year = date.year - 1
            return date.replace(year=year, month=12)
        return date.replace(month=month)

    def add_payroll(self, payday: datetime.date):
        """Adds the payroll for a payday.

        Args:
            payday: The payday.
        """
        income = random.randint(40000, 50000)
        pension = 882 if income <= 40100\
            else 924 if income <= 42000\
            else 966 if income <= 43900\
            else 1008
        insurance = 564 if income <= 40100\
            else 591 if income <= 42000\
            else 618 if income <= 43900\
            else 644 if income <= 45800\
            else 678 if income <= 48200\
            else 712
        tax = round(income * 0.05)
        savings = income - pension - insurance - tax
        previous_month = self.previous_month(payday)
        month = formats.date_format(previous_month, format="F")
        self._filler.add_transfer_transaction(
            payday,
            [(1113, _("Payroll Transfer"), savings),
             (1314, _("Pension for {month}").format(month=month), pension),
             (6262, _("Health insurance for {month}").format(month=month),
              insurance),
             (1255, _("Income Tax"), tax)],
            [(4611, _("Payroll for {month}").format(month=month), income)])
