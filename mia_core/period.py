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

from django.core.serializers.json import DjangoJSONEncoder
from django.template import defaultfilters
from django.utils import dateformat
from django.utils.timezone import localdate
from django.utils.translation import gettext

from mia_core.utils import Language


class Period:
    """The template helper for the period chooser.

    Args:
        spec (str): The current period specification
        data_start (date): The available first day of the data.
        data_end (date): The available last day of the data.

    Attributes:
        spec (date): The currently-working period specification.
        start (date): The start day of the currently-specified period.
        end (date): The end day of the currently-specified period.
        description (str): The description of the currently-specified
                           period.
        this_month (str): The specification of this month.
        last_month (str): The specification of last month.
        since_last_month (str): The specification since last month.
        has_months_to_choose (bool): Whether there are months to
                                     choose besides this month and
                                     last month.
        chosen_month (bool): The specification of the chosen month,
                             or None if the current period is not a
                             month or is out of available data range.
        this_year (str): The specification of this year.
        last_year (str): The specification of last year.
        has_years_to_choose (bool): Whether there are years to
                                    choose besides this year and
                                    last year.
        years_to_choose (list[str]): This specification of the
                                     available years to choose,
                                     besides this year and last year.
        today (str): The specification of today.
        yesterday (str): The specification of yesterday.
        chosen_start (str): The specification of the first day of the
                            specified period, as the default date for
                            the single-day chooser.
        has_days_to_choose (bool): Whether there is a day range to
                                   choose.
        data_start (str): The specification of the available first day.
        data_end (str): The specification of the available last day.
        chosen_start (str): The specification of the first day of the
                            specified period
        chosen_end (str): The specification of the last day of the
                          specified period
        month_picker_params (str): The month-picker parameters, as a
                                   JSON text string
    """
    _data_start = None
    _data_end = None
    _period = None

    def __init__(
            self, spec = None, data_start = None, data_end = None):
        self._period = self.Parser(spec)
        self._data_start = data_start
        self._data_end = data_end

    @property
    def spec(self):
        return self._period.spec

    @property
    def start(self):
        return self._period.start

    @property
    def end(self):
        return self._period.end

    @property
    def description(self):
        return self._period.description

    @staticmethod
    def _get_last_month_start():
        """Returns the first day of the last month.

        Returns:
            date: The first day of the last month.
        """
        today = localdate()
        month = today.month - 1
        year = today.year
        if month < 1:
            month = 12
            year = year - 1
        return date(year, month, 1)

    @staticmethod
    def _get_next_month_start():
        """Returns the first day of the next month.

        Returns:
            date: The first day of the next month.
        """
        today = localdate()
        month = today.month + 1
        year = today.year
        if month > 12:
            month = 1
            year = year + 1
        return date(year, month, 1)

    @property
    def this_month(self):
        if self._data_start is None:
            return None
        today = localdate()
        first_month_start = date(
            self._data_start.year, self._data_start.month, 1)
        if today < first_month_start:
            return None
        return dateformat.format(today, "Y-m")

    @property
    def last_month(self):
        if self._data_start is None:
            return None
        last_month_start = self._get_last_month_start()
        first_month_start = date(
            self._data_start.year, self._data_start.month, 1)
        if last_month_start < first_month_start:
            return None
        return dateformat.format(last_month_start, "Y-m")

    @property
    def since_last_month(self):
        last_month = self.last_month
        if last_month is None:
            return None
        return self.last_month + "-"

    @property
    def has_months_to_choose(self):
        if self._data_start is None:
            return None
        if self._data_start < self._get_last_month_start():
            return True
        if self._data_end >= self._get_next_month_start():
            return True
        return False

    @property
    def chosen_month(self):
        if self._data_start is None:
            return None
        m = re.match("^[0-9]{4}-[0-2]{2}", self._period.spec)
        if m is None:
            return None
        if self._period.end < self._data_start:
            return None
        if self._period.start > self._data_end:
            return None
        return self._period.spec

    @property
    def this_year(self):
        if self._data_start is None:
            return None
        this_year = localdate().year
        if this_year < self._data_start.year:
            return None
        return str(this_year)

    @property
    def last_year(self):
        if self._data_start is None:
            return None
        last_year = localdate().year - 1
        if last_year < self._data_start.year:
            return None
        return str(last_year)

    @property
    def has_years_to_choose(self):
        if self._data_start is None:
            return None
        this_year = localdate().year
        if self._data_start.year < this_year - 1:
            return True
        if self._data_end.year > this_year:
            return True
        return False

    @property
    def years_to_choose(self):
        if self._data_start is None:
            return None
        this_year = localdate().year
        before = [str(x) for x in range(
            self._data_start.year, this_year - 1)]
        after = [str(x) for x in range(
            self._data_end.year, this_year, -1)]
        return after + before[::-1]

    def is_chosen_year(self, year):
        """Returne whether the specified year is the currently-chosen
        year.

        Args:
            year (str): the year.

        Returns:
            bool: True if the year is the currently-chosen year, or
            False otherwise
        """
        if self._period.spec == str(year):
            return True

    @property
    def today(self):
        if self._data_start is None:
            return None
        today = localdate()
        if today < self._data_start or today > self._data_end:
            return None
        return dateformat.format(today, "Y-m-d")

    @property
    def yesterday(self):
        if self._data_start is None:
            return None
        yesterday = localdate() - timedelta(days=1)
        if yesterday < self._data_start or yesterday > self._data_end:
            return None
        return dateformat.format(yesterday, "Y-m-d")

    @property
    def chosen_day(self):
        return dateformat.format(self._period.start, "Y-m-d")

    @property
    def has_days_to_choose(self):
        if self._data_start is None:
            return False
        if self._data_start == self._data_end:
            return False
        return True

    @property
    def first_day(self):
        if self._data_start is None:
            return None
        return dateformat.format(self._data_start, "Y-m-d")

    @property
    def last_day(self):
        if self._data_end is None:
            return None
        return dateformat.format(self._data_end, "Y-m-d")

    @property
    def chosen_start(self):
        if self._data_start is None:
            return None
        day = self._period.start \
            if self._period.start >= self._data_start \
            else self._data_start
        return dateformat.format(day, "Y-m-d")

    @property
    def chosen_end(self):
        if self._data_end is None:
            return None
        day = self._period.end \
            if self._period.end <= self._data_end \
            else self._data_end
        return dateformat.format(day, "Y-m-d")

    @property
    def month_picker_params(self):
        if self._data_start is None:
            return None
        start = date(self._data_start.year, self._data_start.month, 1)
        return DjangoJSONEncoder().encode({
            "locale": Language.current().locale,
            "minDate": start,
            "maxDate": self._data_end,
            "defaultDate": self.chosen_month,
        })

    class Parser:
        """The period parser.

        Args:
            spec (str|None): The period specification.

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

        def __init__(self, spec):
            if spec is None:
                self.set_this_month()
                return
            self.spec = spec
            # A specific month
            m = re.match("^([0-9]{4})-([0-9]{2})$", spec)
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
            m = re.match("^([0-9]{4})-([0-9]{2})-$", spec)
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
            m = re.match("^([0-9]{4})$", spec)
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
            if spec == "-":
                self.start = date(2000, 1, 1)
                self.end = self.get_month_last_day(localdate())
                self.description = gettext("All")
                return
            # A specific date
            m = re.match("^([0-9]{4})-([0-9]{2})-([0-9]{2})$",
                         spec)
            if m is not None:
                try:
                    self.start = date(
                        int(m.group(1)),
                        int(m.group(2)),
                        int(m.group(3)))
                except ValueError:
                    self.invalid_period()
                    return
                self.end = self.start
                self.description = self.get_date_text(self.start)
                return
            # A specific date period
            m = re.match(("^([0-9]{4})-([0-9]{2})-([0-9]{2})"
                          "-([0-9]{4})-([0-9]{2})-([0-9]{2})$"),
                         spec)
            if m is not None:
                try:
                    self.start = date(
                        int(m.group(1)),
                        int(m.group(2)),
                        int(m.group(3)))
                    self.end = date(
                        int(m.group(4)),
                        int(m.group(5)),
                        int(m.group(6)))
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

        def set_this_month(self):
            """Sets the period to this month."""
            today = localdate()
            self.spec = dateformat.format(today, "Y-m")
            self.start = date(today.year, today.month, 1)
            self.end = self.get_month_last_day(self.start)
            self.description = gettext("This Month")

        def invalid_period(self):
            """Sets the period when the period specification is
            invalid.
            """
            self.error = gettext("Invalid period.")
            self.set_this_month()

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
