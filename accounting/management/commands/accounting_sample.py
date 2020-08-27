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
import random
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand, CommandParser, CommandError
from django.db import transaction
from django.utils import timezone

from accounting.models import Account
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
        if Account.objects.count() > 0:
            error = "Refuse to fill in sample data with existing data."
            raise CommandError(error, returncode=1)
        # Gets the user to use
        user_model = get_user_model()
        if options["user"] is not None:
            try:
                user = user_model.objects.get(**{
                    user_model.USERNAME_FIELD: options["user"]
                })
            except ObjectDoesNotExist:
                error = "User \"%s\" does not exist." % options["user"]
                raise CommandError(error, returncode=1)
        elif user_model.objects.count() == 0:
            error = "Please run the \"createsuperuser\" command first."
            raise CommandError(error, returncode=1)
        elif user_model.objects.count() == 1:
            user = user_model.objects.first()
        else:
            error = "Please specify the user with -u."
            raise CommandError(error, returncode=1)

        with transaction.atomic():
            self._filler = DataFiller(user)
            self._filler.add_accounts([
                (1, "assets", "資產", "资产"),
                (2, "liabilities", "負債", "负债"),
                (3, "owners’ equity", "業主權益", "业主权益"),
                (4, "operating revenue", "營業收入", "营业收入"),
                (5, "operating costs", "營業成本", "营业成本"),
                (6, "operating expenses", "營業費用", "营业费用"),
                (7,
                 "non-operating revenue and expenses, other income (expense)",
                 "營業外收入及費用", "营业外收入及费用"),
                (8, "income tax expense (or benefit)", "所得稅費用(或利益)",
                 "所得税费用(或利益)"),
                (9, "nonrecurring gain or loss", "非經常營業損益",
                 "非经常营业损益"),

                (11, "current assets", "流動資產", "流动资产"),
                (111, "cash and cash equivalents", "現金及約當現金",
                 "现金及约当现金"),
                (1111, "petty cash/revolving funds", "庫存現金", "库存现金"),
                (1112, "cash on hand", "零用金/週轉金", "零用金/周转金"),
                (1113, "cash in banks", "銀行存款", "银行存款"),
                (12, "current assets", "流動資產", "流动资产"),
                (125, "prepaid expenses", "預付費用", "预付费用"),
                (1255, "prepaid income tax", "預付所得稅", "预付所得税"),
                (13, "funds and long-term investments", "基金及長期投資",
                 "基金及长期投资"),
                (131, "funds", "基金", "基金"),
                (1314, "pension fund", "退休基金", "退休基金"),
                (14, "property , plant, and equipment", "固定資產", "固定资产"),
                (144, "machinery and equipment", "機(器)具及設備",
                 "机(器)具及设备"),
                (1441, "machinery", "機(器)具", "机(器)具"),

                (21, "current liabilities", "流動負債", "流动负债"),
                (214, "accounts payable", "應付帳款", "应付帐款"),
                (2141, "accounts payable", "應付帳款", "应付帐款"),

                (33, "retained earnings (accumulated deficit)",
                 "保留盈餘(或累積虧損)", "保留盈余(或累积亏损)"),
                (335,
                 "retained earnings-unappropriated (or accumulated deficit)",
                 "未分配盈餘(或累積虧損)", "未分配盈余(或累积亏损)"),
                (3351, "accumulated profit or loss", "累積盈虧", "累积盈亏"),
                (3353, "net income or loss for current period", "本期損益",
                 "本期损益"),

                (46, "service revenue", "勞務收入", "劳务收入"),
                (461, "service revenue", "勞務收入", "劳务收入"),
                (4611, "service revenue", "勞務收入", "劳务收入"),

                (62, "general & administrative expenses", "管理及總務費用",
                 "管理及总务费用"),
                (625, "general & administrative expenses", "管理及總務費用",
                 "管理及总务费用"),
                (6254, "travelling expense, travel", "旅費", "旅费"),
                (626, "general & administrative expenses", "管理及總務費用",
                 "管理及总务费用"),
                (6262, "insurance (expense)", "保險費", "保险费"),
                (627, "general & administrative expenses", "管理及總務費用",
                 "管理及总务费用"),
                (6272, "meal (expenses)", "伙食費", "伙食费"),
                (6273, "employee benefits/welfare", "職工福利", "职工福利"),
            ])

            self.add_payrolls(5)

            self._filler.add_income_transaction(
                -15,
                [(1113, "ATM withdrawal", 2000)])
            self._filler.add_transfer_transaction(
                -14,
                [(6254, "HSR—New Land→South Lake City", 1490)],
                [(2141, "HSR—New Land→South Lake City", 1490)])
            self._filler.add_transfer_transaction(
                -14,
                [(6273, "Movies—The Avengers", 80)],
                [(2141, "Movies—The Avengers", 80)])
            self._filler.add_transfer_transaction(
                -13,
                [(6273, "Movies—2001: A Space Odyssey", 80)],
                [(2141, "Movies—2001: A Space Odyssey", 80)])
            self._filler.add_transfer_transaction(
                -11,
                [(2141, "Movies—The Avengers", 80)],
                [(1113, "Movies—The Avengers", 80)])

            self._filler.add_expense_transaction(
                -13,
                [(6273, "Bus—2623—Uptown→City Park", 477543627.4775)])

            self._filler.add_expense_transaction(
                -2,
                [(6272, "Lunch—Spaghetti", random.randint(40, 200)),
                 (6272, "Drink—Tea", random.randint(40, 200))])
            self._filler.add_expense_transaction(
                -1,
                ([(6272, "Lunch—Pizza", random.randint(40, 200)),
                 (6272, "Drink—Tea", random.randint(40, 200))]))
            self._filler.add_expense_transaction(
                -1,
                [(6272, "Lunch—Spaghetti", random.randint(40, 200)),
                 (6272, "Drink—Soda", random.randint(40, 200))])
            self._filler.add_expense_transaction(
                0,
                [(6272, "Lunch—Salad", random.randint(40, 200)),
                 (6272, "Drink—Coffee", random.randint(40, 200))])

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
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November",
                  "December"]
        month = payday.month - 1
        if month < 1:
            month = 12
        month_text = months[month - 1]
        self._filler.add_transfer_transaction(
            payday,
            [(1113, "Payroll Transfer", savings),
             (1314, F"Pension for {month_text}", pension),
             (6262, F"Health insurance for {month_text}", insurance),
             (1255, "Income Tax", tax)],
            [(4611, F"Payroll for {month_text}", income)])
