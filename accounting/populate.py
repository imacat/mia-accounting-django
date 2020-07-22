from django.utils import timezone

from accounting.models import Transaction, Record, Account
from mia_core.models import User
from mia_core.utils import new_sn


class Populator:
    """The helper to populate the accounting data.

    Args:
        user (User): The user in action.

    Attributes:
        user (User): The user in action.
    """
    user = None

    def __init__(self, user):
        self.user = user

    def add_accounts(self, accounts):
        """Adds accounts.

        Args:
            accounts (tuple[tuple[any]]): Tuples of
                (code, Traditional Chinese, English, Simplified Chinese)
                of the accounts.
        """
        for data in accounts:
            code = data[0]
            if isinstance(code, int):
                code = str(code)
            parent = None if len(code) == 1\
                else Account.objects.get(code=code[:-1])
            Account(sn=new_sn(Account), parent=parent, code=code,
                    title_zh_hant=data[1], title_en=data[2],
                    title_zh_hans=data[3],
                    created_by=self.user, updated_by=self.user).save()

    def add_transfer_transaction(self, date, debit, credit):
        """Adds a transfer transaction.

        Args:
            date (datetime.date|int): The date, or the number of days from
                today.
            debit (tuple[tuple[any]]): Tuples of (account, summary, amount)
                of the debit records.
            credit (tuple[tuple[any]]): Tuples of (account, summary, amount)
                of the credit records.
        """
        if isinstance(date, int):
            date = timezone.localdate() + timezone.timedelta(days=date)
        order = Transaction.objects.filter(date=date).count() + 1
        transaction = Transaction(sn=new_sn(Transaction), date=date, ord=order,
                                  created_by=self.user, updated_by=self.user)
        transaction.save()
        order = 1
        for data in debit:
            account = data[0]
            if isinstance(account, str):
                account = Account.objects.get(code=account)
            elif isinstance(account, int):
                account = Account.objects.get(code=str(account))
            transaction.record_set.create(sn=new_sn(Record), is_credit=False,
                                          ord=order, account=account,
                                          summary=data[1], amount=data[2],
                                          created_by=self.user,
                                          updated_by=self.user)
            order = order + 1
        order = 1
        for data in credit:
            account = data[0]
            if isinstance(account, str):
                account = Account.objects.get(code=account)
            elif isinstance(account, int):
                account = Account.objects.get(code=str(account))
            transaction.record_set.create(sn=new_sn(Record), is_credit=True,
                                          ord=order, account=account,
                                          summary=data[1], amount=data[2],
                                          created_by=self.user,
                                          updated_by=self.user)
            order = order + 1

    def add_income_transaction(self, date, credit):
        """Adds a cash income transaction.

        Args:
            date (datetime.date|int): The date, or the number of days from
                today.
            credit (tuple[tuple[any]]): Tuples of (account, summary, amount) of
                the credit records.
        """
        amount = sum([x[2] for x in credit])
        self.add_transfer_transaction(date, (("1111", None, amount),), credit)

    def add_expense_transaction(self, date, debit):
        """Adds a cash income transaction.

        Args:
            date (datetime.date|int): The date, or the number of days from
                today.
            debit (tuple[tuple[any]]): Tuples of (account, summary, amount) of
                the debit records.
        """
        amount = sum([x[2] for x in debit])
        self.add_transfer_transaction(date, debit, (("1111", None, amount),))
