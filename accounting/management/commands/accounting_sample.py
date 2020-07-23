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
import random

from django.core.management import BaseCommand, CommandParser
from django.utils import timezone

from accounting.utils import Populator
from mia_core.models import User


class Command(BaseCommand):
    """Populates the database with sample accounting data."""
    help = "Populates the database with sample accounting data."

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
        print("This may mess up your data.  Continue? [Y/N] ", end="")
        if input().lower() not in ("y", "yes"):
            return

        user = User(sn=923153018, login_id="imacat",
                    password="5486b64881adaf7bc1485cc26e57e51e", name="依瑪貓",
                    is_disabled=False, is_deleted=False)
        user.created_by = user
        user.updated_by = user
        user.save()

        p = Populator(user)
        p.add_accounts((
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
            (9, "非經常營業損益", "nonrecurring gain or loss", "非经常营业损益"),

            (11, "流動資產", "current assets", "流动资产"),
            (111, "現金及約當現金", "cash and cash equivalents", "现金及约当现金"),
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

            (21, "流動負債", "current liabilities", "流动负债"),
            (214, "應付帳款", "accounts payable", "应付帐款"),
            (2141, "應付帳款", "accounts payable", "应付帐款"),

            (33, "保留盈餘(或累積虧損)",
             "retained earnings (accumulated deficit)", "保留盈余(或累积亏损)"),
            (335, "未分配盈餘(或累積虧損)",
             "retained earnings-unappropriated (or accumulated deficit)",
             "未分配盈余(或累积亏损)"),
            (3351, "累積盈虧", "accumulated profit or loss", "累积盈亏"),
            (3353, "本期損益", "net income or loss for current period", "本期损益"),

            (46, "勞務收入", "service revenue", "劳务收入"),
            (461, "勞務收入", "service revenue", "劳务收入"),
            (4611, "勞務收入", "service revenue", "劳务收入"),

            (62, "管理及總務費用", "general & administrative expenses", "管理及总务费用"),
            (625, "管理及總務費用", "general & administrative expenses", "管理及总务费用"),
            (6254, "旅費", "travelling expense, travel", "旅费"),
            (626, "管理及總務費用", "general & administrative expenses", "管理及总务费用"),
            (6262, "保險費", "insurance (expense)", "保险费"),
            (627, "管理及總務費用", "general & administrative expenses", "管理及总务费用"),
            (6272, "伙食費", "meal (expenses)", "伙食费"),
            (6273, "職工福利", "employee benefits/welfare", "职工福利"),
        ))

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
        date = timezone.localdate() - timezone.timedelta(days=15)
        month = (date.replace(day=1) - timezone.timedelta(days=1)).month
        p.add_transfer_transaction(
            date,
            (("1113", "薪資轉帳", savings),
             ("1314", F"勞保{month}月", pension),
             ("6262", F"健保{month}月", insurance),
             ("1255", "代扣所得稅", tax)),
            (("4611", F"{month}月份薪水", income),))

        p.add_income_transaction(
            -15,
            (("1113", "ATM提款", 2000),))
        p.add_transfer_transaction(
            -14,
            (("6254", "高鐵—台北→左營", 1490),),
            (("2141", "高鐵—台北→左營", 1490),))
        p.add_transfer_transaction(
            -14,
            (("6273", "電影—復仇者聯盟", 80),),
            (("2141", "電影—復仇者聯盟", 80),))
        p.add_transfer_transaction(
            -11,
            (("2141", "電影—復仇者聯盟", 80),),
            (("1113", "電影—復仇者聯盟", 80),))

        p.add_expense_transaction(
            -2,
            (("6272", "午餐—排骨飯", random.randint(40, 200)),
             ("6272", "飲料—紅茶", random.randint(40, 200))))
        p.add_expense_transaction(
            -1,
            (("6272", "午餐—牛肉麵", random.randint(40, 200)),
             ("6272", "飲料—紅茶", random.randint(40, 200))))
        p.add_expense_transaction(
            -1,
            (("6272", "午餐—排骨飯", random.randint(40, 200)),
             ("6272", "飲料—冬瓜茶", random.randint(40, 200))))
        p.add_expense_transaction(
            0,
            (("6272", "午餐—雞腿飯", random.randint(40, 200)),
             ("6272", "飲料—咖啡", random.randint(40, 200))))
