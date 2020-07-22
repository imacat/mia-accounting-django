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

from accounting.models import Record, Account, Transaction
from mia_core.models import User
from mia_core.utils import new_sn


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
        user = User(sn=923153018, login_id="imacat",
                    password="5486b64881adaf7bc1485cc26e57e51e", name="依瑪貓",
                    is_disabled=False, is_deleted=False)
        user.created_by = user
        user.updated_by = user
        user.save()

        Account(sn=new_sn(Account), code="1", title_zh_hant="資產",
                title_en="assets", title_zh_hans="资产", created_by=user,
                updated_by=user).save()
        Account(sn=new_sn(Account), code="2", title_zh_hant="負債",
                title_en="liabilities", title_zh_hans="负债", created_by=user,
                updated_by=user).save()
        Account(sn=new_sn(Account), code="3", title_zh_hant="業主權益",
                title_en="owners’ equity", title_zh_hans="业主权益",
                created_by=user, updated_by=user).save()
        Account(sn=new_sn(Account), code="4", title_zh_hant="營業收入",
                title_en="operating revenue", title_zh_hans="营业收入",
                created_by=user, updated_by=user).save()
        Account(sn=new_sn(Account), code="5", title_zh_hant="營業成本",
                title_en="operating costs", title_zh_hans="营业成本",
                created_by=user, updated_by=user).save()
        Account(sn=new_sn(Account), code="6", title_zh_hant="營業費用",
                title_en="operating expenses", title_zh_hans="营业费用",
                created_by=user, updated_by=user).save()
        Account(sn=new_sn(Account), code="7", title_zh_hant="營業外收入及費用",
                title_en=("non-operating revenue and expenses, "
                          "other income (expense)"),
                title_zh_hans="营业外收入及费用", created_by=user,
                updated_by=user).save()
        Account(sn=new_sn(Account), code="8", title_zh_hant="所得稅費用(或利益)",
                title_en="income tax expense (or benefit)",
                title_zh_hans="所得税费用(或利益)", created_by=user,
                updated_by=user).save()
        Account(sn=new_sn(Account), code="9", title_zh_hant="非經常營業損益",
                title_en="nonrecurring gain or loss", title_zh_hans="非经常营业损益",
                created_by=user, updated_by=user).save()

        Account(sn=new_sn(Account), parent=Account.objects.get(code="1"),
                code="11", title_zh_hant="流動資產", title_en="current assets",
                title_zh_hans="流动资产", created_by=user, updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="11"),
                code="111", title_zh_hant="現金及約當現金",
                title_en="cash and cash equivalents", title_zh_hans="现金及约当现金",
                created_by=user, updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="111"),
                code="1111", title_zh_hant="庫存現金",
                title_en="petty cash/revolving funds", title_zh_hans="库存现金",
                created_by=user, updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="111"),
                code="1112", title_zh_hant="零用金/週轉金", title_en="cash on hand",
                title_zh_hans="零用金/周转金", created_by=user,
                updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="111"),
                code="1113", title_zh_hant="銀行存款", title_en="cash in banks",
                title_zh_hans="银行存款", created_by=user,
                updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="1"),
                code="12", title_zh_hant="流動資產", title_en="current assets",
                title_zh_hans="流动资产", created_by=user, updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="12"),
                code="125", title_zh_hant="預付費用", title_en="prepaid expenses",
                title_zh_hans="预付费用", created_by=user, updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="125"),
                code="1255", title_zh_hant="預付所得稅", title_en="prepaid income tax",
                title_zh_hans="预付所得税", created_by=user, updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="1"),
                code="13", title_zh_hant="基金及長期投資",
                title_en="funds and long-term investments",
                title_zh_hans="基金及长期投资",
                created_by=user, updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="13"),
                code="131", title_zh_hant="基金", title_en="funds",
                title_zh_hans="基金", created_by=user, updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="131"),
                code="1314", title_zh_hant="退休基金", title_en="pension fund",
                title_zh_hans="退休基金", created_by=user, updated_by=user).save()

        Account(sn=new_sn(Account), parent=Account.objects.get(code="2"),
                code="21", title_zh_hant="流動負債", title_en="current liabilities",
                title_zh_hans="流动负债", created_by=user,updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="21"),
                code="214", title_zh_hant="應付帳款", title_en="accounts payable",
                title_zh_hans="应付帐款", created_by=user,updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="214"),
                code="2141", title_zh_hant="應付帳款", title_en="accounts payable",
                title_zh_hans="应付帐款", created_by=user,updated_by=user).save()

        Account(sn=new_sn(Account), parent=Account.objects.get(code="4"),
                code="46", title_zh_hant="勞務收入", title_en="service revenue",
                title_zh_hans="劳务收入", created_by=user,updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="46"),
                code="461", title_zh_hant="勞務收入", title_en="service revenue",
                title_zh_hans="劳务收入", created_by=user,updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="461"),
                code="4611", title_zh_hant="勞務收入", title_en="service revenue",
                title_zh_hans="劳务收入", created_by=user,updated_by=user).save()

        Account(sn=new_sn(Account), parent=Account.objects.get(code="3"),
                code="33", title_zh_hant="保留盈餘(或累積虧損)",
                title_en="retained earnings (accumulated deficit)",
                title_zh_hans="保留盈余(或累积亏损)", created_by=user,
                updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="33"),
                code="335", title_zh_hant="未分配盈餘(或累積虧損)",
                title_en=("retaid earnings-unappropriated "
                          "(or accumulated deficit)"),
                title_zh_hans="未分配盈余(或累积亏损)", created_by=user,
                updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="335"),
                code="3351", title_zh_hant="累積盈虧",
                title_en="accumulated profit or loss", title_zh_hans="累积盈亏",
                created_by=user, updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="335"),
                code="3353", title_zh_hant="本期損益",
                title_en="net income or loss for current period",
                title_zh_hans="本期损益", created_by=user, updated_by=user).save()

        Account(sn=new_sn(Account), parent=Account.objects.get(code="6"),
                code="62", title_zh_hant="管理及總務費用",
                title_en="general & administrative expenses",
                title_zh_hans="管理及总务费用", created_by=user,
                updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="62"),
                code="625", title_zh_hant="管理及總務費用",
                title_en="general & administrative expenses",
                title_zh_hans="管理及总务费用", created_by=user,
                updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="625"),
                code="6254", title_zh_hant="旅費",
                title_en="travelling expense, travel",
                title_zh_hans="旅费", created_by=user,
                updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="62"),
                code="626", title_zh_hant="管理及總務費用",
                title_en="general & administrative expenses",
                title_zh_hans="管理及总务费用", created_by=user,
                updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="626"),
                code="6262", title_zh_hant="保險費",
                title_en="insurance (expense)",
                title_zh_hans="保险费", created_by=user,
                updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="62"),
                code="627", title_zh_hant="管理及總務費用",
                title_en="general & administrative expenses",
                title_zh_hans="管理及总务费用", created_by=user,
                updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="627"),
                code="6272", title_zh_hant="伙食費", title_en="meal (enses)",
                title_zh_hans="伙食费", created_by=user, updated_by=user).save()
        Account(sn=new_sn(Account), parent=Account.objects.get(code="627"),
                code="6273", title_zh_hant="職工福利", title_en="employee benefits/welfare",
                title_zh_hans="职工福利", created_by=user, updated_by=user).save()

        today = timezone.localdate()
        cash_account = Account.objects.get(code="1111")
        bank_account = Account.objects.get(code="1113")
        tax_account = Account.objects.get(code="1255")
        pension_account = Account.objects.get(code="1314")
        salary_account = Account.objects.get(code="4611")
        payable_account = Account.objects.get(code="2141")
        travel_account = Account.objects.get(code="6254")
        insurance_account = Account.objects.get(code="6262")
        meal_account = Account.objects.get(code="6272")
        welfare_account = Account.objects.get(code="6273")

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
        date = today - timezone.timedelta(days=15)
        month = (date.replace(day=1) - timezone.timedelta(days=1)).month

        transaction = Transaction(sn=new_sn(Transaction),
                                  date=today - timezone.timedelta(days=15),
                                  ord=1, created_by=user, updated_by=user)
        transaction.save()
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=1,
                                      account=bank_account,
                                      summary="薪資轉帳", amount=savings,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=2,
                                      account=pension_account,
                                      summary=F"勞保{month}月",
                                      amount=pension,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=3,
                                      account=insurance_account,
                                      summary=F"健保{month}月",
                                      amount=insurance,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=4,
                                      account=tax_account,
                                      summary="代扣所得稅",
                                      amount=tax,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=True,
                                      ord=1,
                                      account=salary_account,
                                      summary=F"{month}月份薪水",
                                      amount=income,
                                      created_by=user, updated_by=user)

        transaction = Transaction(sn=new_sn(Transaction),
                                  date=today - timezone.timedelta(days=15),
                                  ord=2, created_by=user, updated_by=user)
        transaction.save()
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=1,
                                      account=cash_account,
                                      amount=2000,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=True,
                                      ord=1,
                                      account=bank_account,
                                      summary="ATM提款",
                                      amount=2000,
                                      created_by=user, updated_by=user)

        transaction = Transaction(sn=new_sn(Transaction),
                                  date=today - timezone.timedelta(days=14),
                                  ord=1, created_by=user, updated_by=user)
        transaction.save()
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=1,
                                      account=travel_account,
                                      summary="高鐵—台北→左營",
                                      amount=1490,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=True,
                                      ord=1,
                                      account=payable_account,
                                      summary="高鐵—台北→左營",
                                      amount=1490,
                                      created_by=user, updated_by=user)

        transaction = Transaction(sn=new_sn(Transaction),
                                  date=today - timezone.timedelta(days=14),
                                  ord=2, created_by=user, updated_by=user)
        transaction.save()
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=1,
                                      account=welfare_account,
                                      summary="電影—復仇者聯盟",
                                      amount=80,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=True,
                                      ord=1,
                                      account=payable_account,
                                      summary="電影—復仇者聯盟",
                                      amount=80,
                                      created_by=user, updated_by=user)

        transaction = Transaction(sn=new_sn(Transaction),
                                  date=today - timezone.timedelta(days=11),
                                  ord=1, created_by=user, updated_by=user)
        transaction.save()
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=1,
                                      account=payable_account,
                                      summary="電影—復仇者聯盟",
                                      amount=80,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=True,
                                      ord=1,
                                      account=bank_account,
                                      summary="電影—復仇者聯盟",
                                      amount=80,
                                      created_by=user, updated_by=user)

        amount1 = random.randint(40, 200)
        amount2 = random.randint(40, 200)
        transaction = Transaction(sn=new_sn(Transaction),
                                  date=today - timezone.timedelta(days=2),
                                  ord=1, created_by=user, updated_by=user)
        transaction.save()
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=1,
                                      account=meal_account,
                                      summary="午餐—排骨飯", amount=amount1,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=2,
                                      account=meal_account,
                                      summary="飲料—咖啡", amount=amount2,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=True, ord=1,
                                      account=cash_account,
                                      amount=amount1 + amount2,
                                      created_by=user, updated_by=user)

        amount1 = random.randint(40, 200)
        amount2 = random.randint(40, 200)
        transaction = Transaction(sn=new_sn(Transaction),
                                  date=today - timezone.timedelta(days=1),
                                  ord=1, created_by=user, updated_by=user)
        transaction.save()
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=1,
                                      account=meal_account,
                                      summary="午餐—牛肉麵", amount=amount1,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=2,
                                      account=meal_account,
                                      summary="飲料—紅茶", amount=amount2,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=True, ord=1,
                                      account=cash_account,
                                      amount=amount1 + amount2,
                                      created_by=user, updated_by=user)

        amount1 = random.randint(40, 200)
        amount2 = random.randint(40, 200)
        transaction = Transaction(sn=new_sn(Transaction),
                                  date=today - timezone.timedelta(days=1),
                                  ord=2, created_by=user, updated_by=user)
        transaction.save()
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=1,
                                      account=meal_account,
                                      summary="午餐—排骨飯", amount=amount1,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=2,
                                      account=meal_account,
                                      summary="飲料—冬瓜茶", amount=amount2,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=True, ord=1,
                                      account=cash_account,
                                      amount=amount1 + amount2,
                                      created_by=user, updated_by=user)

        amount1 = random.randint(40, 200)
        amount2 = random.randint(40, 200)
        transaction = Transaction(sn=new_sn(Transaction), date=today,
                                  ord=1, created_by=user, updated_by=user)
        transaction.save()
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=1,
                                      account=meal_account,
                                      summary="午餐—雞腿飯", amount=amount1,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                      ord=2,
                                      account=meal_account,
                                      summary="飲料—咖啡", amount=amount2,
                                      created_by=user, updated_by=user)
        transaction.record_set.create(sn=new_sn(Record), is_credit=True, ord=1,
                                      account=cash_account,
                                      amount=amount1 + amount2,
                                      created_by=user, updated_by=user)
