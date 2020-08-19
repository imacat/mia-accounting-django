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
import sys
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, CommandParser
from django.db import transaction
from django.db.models import PositiveIntegerField
from django.utils import timezone

from accounting.utils import DataFiller
from mia_core.utils import new_pk


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
        pass

    def handle(self, *args, **options):
        """Runs the command.

        Args:
            *args (list[str]): The command line arguments.
            **options (dict[str,str]): The command line switches.
        """
        user_model = get_user_model()
        if user_model.objects.first() is not None:
            print("Refused to fill in sample data with existing data.",
                  file=sys.stderr)
            return

        with transaction.atomic():
            user = user_model()
            setattr(user, user_model.USERNAME_FIELD, "admin")
            for field in user_model.REQUIRED_FIELDS:
                setattr(user, field, "admin")
            if getattr(user_model, "EMAIL_FIELD", None) is not None:
                setattr(user, user_model.EMAIL_FIELD, "guest@example.com")
            if getattr(user_model, "created_by", None) is not None:
                user.created_by = user
            if getattr(user_model, "updated_by", None) is not None:
                user.updated_by = user
            if isinstance(user_model._meta.pk, PositiveIntegerField):
                user.pk = new_pk(user_model)
            if getattr(user_model, "set_digest_password", None) is not None:
                user.set_digest_password("admin", "12345")
            user.save()

            self._filler = DataFiller(user)
            self._filler.add_accounts([
                (1, "資產", "assets", "资产"),
                (2, "負債", "liabilities", "负债"),
                (3, "業主權益", "owners’ equity", "业主权益"),
                (4, "營業收入", "operating revenue", "营业收入"),
                (5, "營業成本", "operating costs", "营业成本"),
                (6, "營業費用", "operating expenses", "营业费用"),
                (7, "營業外收入及費用",
                 "non-operating revenue and expenses, other income (expense)",
                 "营业外收入及费用"),
                (8, "所得稅費用(或利益)", "income tax expense (or benefit)",
                 "所得税费用(或利益)"),
                (9, "非經常營業損益", "nonrecurring gain or loss",
                 "非经常营业损益"),

                (11, "流動資產", "current assets", "流动资产"),
                (111, "現金及約當現金", "cash and cash equivalents",
                 "现金及约当现金"),
                (1111, "庫存現金", "petty cash/revolving funds", "库存现金"),
                (1112, "零用金/週轉金", "cash on hand", "零用金/周转金"),
                (1113, "銀行存款", "cash in banks", "银行存款"),
                (12, "流動資產", "current assets", "流动资产"),
                (125, "預付費用", "prepaid expenses", "预付费用"),
                (1255, "預付所得稅", "prepaid income tax", "预付所得税"),
                (13, "基金及長期投資", "funds and long-term investments",
                 "基金及长期投资"),
                (131, "基金", "funds", "基金"),
                (1314, "退休基金", "pension fund", "退休基金"),
                (14, "固定資產", "property , plant, and equipment", "固定资产"),
                (144, "機(器)具及設備", "machinery and equipment", "机(器)具及设备"),
                (1441, "機(器)具", "machinery", "机(器)具"),

                (21, "流動負債", "current liabilities", "流动负债"),
                (214, "應付帳款", "accounts payable", "应付帐款"),
                (2141, "應付帳款", "accounts payable", "应付帐款"),

                (33, "保留盈餘(或累積虧損)",
                 "retained earnings (accumulated deficit)",
                 "保留盈余(或累积亏损)"),
                (335, "未分配盈餘(或累積虧損)",
                 "retained earnings-unappropriated (or accumulated deficit)",
                 "未分配盈余(或累积亏损)"),
                (3351, "累積盈虧", "accumulated profit or loss", "累积盈亏"),
                (3353, "本期損益", "net income or loss for current period",
                 "本期损益"),

                (46, "勞務收入", "service revenue", "劳务收入"),
                (461, "勞務收入", "service revenue", "劳务收入"),
                (4611, "勞務收入", "service revenue", "劳务收入"),

                (62, "管理及總務費用", "general & administrative expenses",
                 "管理及总务费用"),
                (625, "管理及總務費用", "general & administrative expenses",
                 "管理及总务费用"),
                (6254, "旅費", "travelling expense, travel", "旅费"),
                (626, "管理及總務費用", "general & administrative expenses",
                 "管理及总务费用"),
                (6262, "保險費", "insurance (expense)", "保险费"),
                (627, "管理及總務費用", "general & administrative expenses",
                 "管理及总务费用"),
                (6272, "伙食費", "meal (expenses)", "伙食费"),
                (6273, "職工福利", "employee benefits/welfare", "职工福利"),
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
                [(6273, "Bus—2623—Uptown→City Park", 30)])

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
