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

"""The period chooser utilities of the Mia core application.

"""

import re
from datetime import date, timedelta

from django.template import defaultfilters
from django.utils import dateformat
from django.utils.timezone import localdate
from django.utils.translation import gettext, pgettext


class PeriodParser:
    """The period parser.

    Args:
        period_spec (str): The period specification.

    Attributes:
        spec (str): The currently-using period specification.
        start (date): The start of the period.
        end (date): The end of the period.
        description (str): The text description of the period.
        error (str): The period specification format error, or
                     None on success.
    """
    spec = None
    start = None
    end = None
    description = None
    error = None

    def __init__(self, period_spec):
        self.spec = period_spec
        # A specific month
        m = re.match("^([0-9]{4})-([0-9]{2})$", period_spec)
        if m is not None:
            year = int(m.group(1))
            month = int(m.group(2))
            try:
                self.start = date(year, month, 1)
            except ValueError:
                self.invalid_period()
                return
            self.end = self.get_month_last_day(self.start)
            self.description = self.get_month_text(year, month)
            return
        # From a specific month
        m = re.match("^([0-9]{4})-([0-9]{2})-$", period_spec)
        if m is not None:
            year = int(m.group(1))
            month = int(m.group(2))
            try:
                self.start = date(year, month, 1)
            except ValueError:
                self.invalid_period()
                return
            self.end = self.get_month_last_day(localdate())
            self.description = gettext(
                "Since %s") % self.get_month_text(year, month)
            return
        # A specific year
        m = re.match("^([0-9]{4})$", period_spec)
        if m is not None:
            year = int(m.group(1))
            try:
                self.start = date(year, 1, 1)
            except ValueError:
                self.invalid_period()
                return
            self.end = date(year, 12, 31)
            today = localdate()
            if year == today.year:
                self.description = gettext("This Year")
            elif year == today.year - 1:
                self.description = gettext("Last Year")
            else:
                self.description = str(year)
            return
        # All time
        if period_spec == "-":
            self.start = date(2000, 1, 1)
            self.end = self.get_month_last_day(localdate())
            self.description = gettext("All")
            return
        # A specific date
        m = re.match("^([0-9]{4})-([0-9]{2})-([0-9]{2})$",
                     period_spec)
        if m is not None:
            try:
                self.start = date(
                    int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                self.invalid_period()
                return
            self.end = self.start
            self.description = self.get_date_text(self.start)
            return
        # A specific date period
        m = re.match(("^([0-9]{4})-([0-9]{2})-([0-9]{2})"
                      "-([0-9]{4})-([0-9]{2})-([0-9]{2})$"),
                     period_spec)
        if m is not None:
            try:
                self.start = date(
                    int(m.group(1)), int(m.group(2)), int(m.group(3)))
                self.end = date(
                    int(m.group(4)), int(m.group(5)), int(m.group(6)))
            except ValueError:
                self.invalid_period()
                return
            today = localdate()
            # Spans several years
            if self.start.year != self.end.year:
                self.description = "%s-%s" % (
                    defaultfilters.date(self.start, "Y/n/j"),
                    defaultfilters.date(self.end, "Y/n/j"))
            # Spans several months
            elif self.start.month != self.end.month:
                if self.start.year != today.year:
                    self.description = "%s-%s" % (
                        defaultfilters.date(self.start, "Y/n/j"),
                        defaultfilters.date(self.end, "n/j"))
                else:
                    self.description = "%s-%s" % (
                        defaultfilters.date(self.start, "n/j"),
                        defaultfilters.date(self.end, "n/j"))
            # Spans several days
            elif self.start.day != self.end.day:
                if self.start.year != today.year:
                    self.description = "%s-%s" % (
                        defaultfilters.date(self.start, "Y/n/j"),
                        defaultfilters.date(self.end, "j"))
                else:
                    self.description = "%s-%s" % (
                        defaultfilters.date(self.start, "n/j"),
                        defaultfilters.date(self.end, "j"))
            # At the same day
            else:
                self.spec = dateformat.format(self.start, "Y-m-d")
                self.description = self.get_date_text(self.start)
            return
        # Wrong period format
        self.invalid_period()

    def invalid_period(self):
        """Sets the period when the period specification is invalid.
        """
        self.error = pgettext("Accounting|", "Invalid period.")
        today = localdate()
        self.spec = dateformat.format(localdate(), "Y-m")
        self.start = date(today.year, today.month, 1)
        self.end = self.get_month_last_day(self.start)
        self.description = gettext("This Month")

    def set_month_range(self, year, month):
        """Calculates and returns the date range of a month.

        Args:
            year (int): The year.
            month (int): The month.

        Returns:
            tuple(date): The date range of the month.

        Throws:
            ValueError: When the year and month are invalid
        """
        self.start = date(year, month, 1)
        self.end = self.get_month_last_day(self.start)

    @staticmethod
    def get_month_last_day(day):
        """Calculates and returns the last day of a month.

        Args:
            day (date): A day in the month.

        Returns:
            date: The last day in the month
        """
        next_month = day.month + 1
        next_year = day.year
        if next_month > 12:
            next_month = 1
            next_year = next_year + 1
        return date(next_year, next_month, 1) - timedelta(days=1)

    @staticmethod
    def get_month_text(year, month):
        """Returns the text description of a month.

        Args:
            year (int): The year.
            month (int): The month.

        Returns:
            str: The description of the month.
        """
        today = localdate()
        if year == today.year and month == today.month:
            return gettext("This Month")
        prev_month = today.month - 1
        prev_year = today.year
        if prev_month < 1:
            prev_month = 12
            prev_year = prev_year - 1
        prev = date(prev_year, prev_month, 1)
        if year == prev.year and month == prev.month:
            return gettext("Last Month")
        return "%d/%d" % (year, month)

    @staticmethod
    def get_date_text(day):
        """Returns the text description of a day.

        Args:
            day (date): The date.

        Returns:
            str: The description of the day.
        """
        today = localdate()
        if day == today:
            return gettext("Today")
        elif day == today - timedelta(days=1):
            return gettext("Yesterday")
        elif day.year != today.year:
            return defaultfilters.date(day, "Y/n/j")
        else:
            return defaultfilters.date(day, "n/j")
