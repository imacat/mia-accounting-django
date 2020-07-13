from django.conf import settings
from django.urls import reverse

from accounting.models import Subject
from mia_core.period import Period


class ReportUrl:
    """The URL of the accounting reports.

    Args:
        **kwargs: the keyword arguments:
            period (Period): The currently-specified period.
            cash (Subject): The currently-specified subject of the
                cash account or cash summary.
            ledger (Subject): The currently-specified subject of the
                ledger or leger summary.

    Attributes:
        cash (str): The URL of the cash account.
        cash_summary (str): The URL of the cash summary.
        ledger (str): The URL of the ledger.
        ledger_summary (str): The URL of the ledger summary.
        journal (str): The URL of the journal.
        trial_balance (str): The URL of the trial balance.
        income_statement (str): The URL of the income statement.
        balance_sheet (str): The URL of the balance sheet.
    """
    _period = None
    _cash_subject = None
    _ledger_subject = None

    def __init__(self, **kwargs):
        if "period" in kwargs:
            self._period = kwargs["period"]
        else:
            self._period = Period(None, None, None, None)
        if "cash" in kwargs:
            self._cash_subject = kwargs["cash"]
        else:
            self._cash_subject = Subject.objects.filter(
                code=settings.ACCOUNTING["DEFAULT_CASH_SUBJECT"]
            ).first()
        if "ledger" in kwargs:
            self._ledger_subject = kwargs["ledger"]
        else:
            self._ledger_subject = Subject.objects.filter(
                code=settings.ACCOUNTING["DEFAULT_LEDGER_SUBJECT"]
            ).first()

    @property
    def cash(self):
        return reverse(
            "accounting:cash",
            args=[self._cash_subject.code, self._period.spec])

    @property
    def cash_summary(self):
        return reverse(
            "accounting:cash-summary", args=[self._cash_subject.code])

    @property
    def ledger(self):
        return reverse(
            "accounting:ledger",
            args=[self._ledger_subject.code, self._period.spec])

    @property
    def ledger_summary(self):
        return reverse(
            "accounting:ledger-summary",
            args=[self._ledger_subject.code])

    @property
    def journal(self):
        return reverse("accounting:journal", args=[self._period.spec])

    @property
    def trial_balance(self):
        return reverse(
            "accounting:trial-balance", args=[self._period.spec])

    @property
    def income_statement(self):
        return reverse(
            "accounting:income-statement", args=[self._period.spec])

    @property
    def balance_sheet(self):
        return reverse(
            "accounting:balance-sheet", args=[self._period.spec])
