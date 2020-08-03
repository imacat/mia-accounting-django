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
import datetime
import re

from django.core.serializers.json import DjangoJSONEncoder
from django.template import defaultfilters
from django.utils import dateformat, timezone
from django.utils.translation import gettext

from mia_core.utils import Language


class Period:
    """The template helper for the period chooser.

    Args:
        spec (str): The current period specification
        data_start (datetime.date): The available first day of the data.
        data_end (datetime.date): The available last day of the data.

    Raises:
        ValueError: When the period specification is invalid.
    """
    def __init__(self, spec=None, data_start=None, data_end=None):
        # Raises ValueError
        self._period = self.Parser(spec)
        self._data_start = data_start
        self._data_end = data_end

    @property
    def spec(self):
        """Returns the period specification.

        Returns:
            str: The period specification.
        """
        return self._period.spec

    @property
    def start(self):
        """Returns the start day of the currently-specified period.

        Returns:
            datetime.date: The start day of the currently-specified period.
        """
        return self._period.start

    @property
    def end(self):
        """Returns the end day of the currently-specified period.

        Returns:
            datetime.date: The end day of the currently-specified period.
        """
        return self._period.end

    @property
    def description(self):
        """Returns the text description of the currently-specified period.

        Returns:
            str: The text description of the currently-specified period
        """
        return self._period.description

    @property
    def error(self):
        """Returns the error of the period specification format.

        Returns:
            str|None: The error of the period specification format, or None on
                success.
        """
        return self._period.error

    @staticmethod
    def _get_last_month_start():
        """Returns the first day of the last month.

        Returns:
            datetime.date: The first day of the last month.
        """
        today = timezone.localdate()
        month = today.month - 1
        year = today.year
        if month < 1:
            month = 12
            year = year - 1
        return datetime.date(year, month, 1)

    @staticmethod
    def _get_next_month_start():
        """Returns the first day of the next month.

        Returns:
            datetime.date: The first day of the next month.
        """
        today = timezone.localdate()
        month = today.month + 1
        year = today.year
        if month > 12:
            month = 1
            year = year + 1
        return datetime.date(year, month, 1)

    def this_month(self):
        """Returns the specification of this month.

        Returns:
            str|None: The specification of this month, or None if there is no
                data in or before this month.
        """
        if self._data_start is None:
            return None
        today = timezone.localdate()
        first_month_start = datetime.date(
            self._data_start.year, self._data_start.month, 1)
        if today < first_month_start:
            return None
        return dateformat.format(today, "Y-m")

    def last_month(self):
        """Returns the specification of last month.

        Returns:
            str|None: The specification of last month, or None if there is no
                data in or before last month.
        """
        if self._data_start is None:
            return None
        last_month_start = self._get_last_month_start()
        first_month_start = datetime.date(
            self._data_start.year, self._data_start.month, 1)
        if last_month_start < first_month_start:
            return None
        return dateformat.format(last_month_start, "Y-m")

    def since_last_month(self):
        """Returns the specification since last month.

        Returns:
            str|None: The specification since last month, or None if there is
                no data in or before last month.
        """
        last_month = self.last_month()
        if last_month is None:
            return None
        return last_month + "-"

    def has_months_to_choose(self):
        """Returns whether there are months to choose besides this month and
        last month.

        Returns:
            bool: True if there are months to choose besides this month and
                last month, or False otherwise.
        """
        if self._data_start is None:
            return False
        if self._data_start < self._get_last_month_start():
            return True
        if self._data_end >= self._get_next_month_start():
            return True
        return False

    def chosen_month(self):
        """Returns the specification of the chosen month, or None if the
        current period is not a month or is out of available data range.

        Returns:
            str|None: The specification of the chosen month, or None if the
                current period is not a month or is out of available data
                range.
        """
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

    def this_year(self):
        """Returns the specification of this year.

        Returns:
            str|None: The specification of this year, or None if there is no
                data in or before this year.
        """
        if self._data_start is None:
            return None
        this_year = timezone.localdate().year
        if this_year < self._data_start.year:
            return None
        return str(this_year)

    def last_year(self):
        """Returns the specification of last year.

        Returns:
            str|None: The specification of last year, or None if there is no
                data in or before last year.
        """
        if self._data_start is None:
            return None
        last_year = timezone.localdate().year - 1
        if last_year < self._data_start.year:
            return None
        return str(last_year)

    def has_years_to_choose(self):
        """Returns whether there are years to choose besides this year and
        last year.

        Returns:
            bool: True if there are years to choose besides this year and
                last year, or False otherwise.
        """
        if self._data_start is None:
            return False
        this_year = timezone.localdate().year
        if self._data_start.year < this_year - 1:
            return True
        if self._data_end.year > this_year:
            return True
        return False

    def years_to_choose(self):
        """Returns the years to choose besides this year and last year.

        Returns:
            list[str]: The years to choose besides this year and last year.
        """
        if self._data_start is None:
            return None
        this_year = timezone.localdate().year
        before = [str(x) for x in range(
            self._data_start.year, this_year - 1)]
        after = [str(x) for x in range(
            self._data_end.year, this_year, -1)]
        return after + before[::-1]

    def today(self):
        """Returns the specification of today.

        Returns:
            (str): The specification of today, or None if there is no data
                in or before today.
        """
        if self._data_start is None:
            return None
        today = timezone.localdate()
        if today < self._data_start or today > self._data_end:
            return None
        return dateformat.format(today, "Y-m-d")

    def yesterday(self):
        """Returns the specification of yesterday.

        Returns:
            (str): The specification of yesterday, or None if there is no data
                in or before yesterday.
        """
        if self._data_start is None:
            return None
        yesterday = timezone.localdate() - datetime.timedelta(days=1)
        if yesterday < self._data_start or yesterday > self._data_end:
            return None
        return dateformat.format(yesterday, "Y-m-d")

    def chosen_day(self):
        """Returns the specification of the chosen day.

        Returns:
            (str): The specification of the chosen day, or the start day
                of the period if the current period is not a day.
        """
        return dateformat.format(self._period.start, "Y-m-d")

    def has_days_to_choose(self):
        """Returns whether there are more than one day to choose from.

        Returns:
            bool: True if there are more than one day to choose from,
                or False otherwise.
        """
        if self._data_start is None:
            return False
        if self._data_start == self._data_end:
            return False
        return True

    def first_day(self):
        """Returns the specification of the available first day.

        Returns:
            str: The specification of the available first day.
        """
        if self._data_start is None:
            return None
        return dateformat.format(self._data_start, "Y-m-d")

    def last_day(self):
        """Returns the specification of the available last day.

        Returns:
            str: The specification of the available last day.
        """
        if self._data_end is None:
            return None
        return dateformat.format(self._data_end, "Y-m-d")

    def chosen_start(self):
        """Returns the specification of of the first day of the
        specified period.

        Returns:
            str: The specification of of the first day of the
                specified period.
        """
        if self._data_start is None:
            return None
        day = self._period.start \
            if self._period.start >= self._data_start \
            else self._data_start
        return dateformat.format(day, "Y-m-d")

    def chosen_end(self):
        """Returns the specification of of the last day of the
        specified period.

        Returns:
            str: The specification of of the last day of the
                specified period.
        """
        if self._data_end is None:
            return None
        day = self._period.end \
            if self._period.end <= self._data_end \
            else self._data_end
        return dateformat.format(day, "Y-m-d")

    def period_before(self):
        """Returns the specification of the period before the current period.

        Returns:
            str|None: The specification of the period before the current
                period, or None if there is no data before the current period.
        """
        if self._data_start is None:
            return None
        if self.start <= self._data_start:
            return None
        previous_day = self.start - datetime.timedelta(days=1)
        if re.match("^[0-9]{4}$", self.spec):
            return "-" + str(previous_day.year)
        if re.match("^[0-9]{4}-[0-9]{2}$", self.spec):
            return dateformat.format(previous_day, "-Y-m")
        return dateformat.format(previous_day, "-Y-m-d")

    def month_picker_params(self):
        """Returns the parameters for the month-picker, as a JSON text string.

        Returns:
            str: The parameters for the month-picker, as a JSON text string.
        """
        if self._data_start is None:
            return None
        start = datetime.date(self._data_start.year, self._data_start.month, 1)
        return DjangoJSONEncoder().encode({
            "locale": Language.current().locale,
            "minDate": start,
            "maxDate": self._data_end,
            "defaultDate": self.chosen_month(),
        })

    @staticmethod
    def default_spec():
        """Returns the specification for the default period.

        Returns:
            str: The specification for the default period
        """
        return dateformat.format(timezone.localdate(), "Y-m")

    class Parser:
        """The period parser.

        Args:
            spec (str|None): The period specification.

        Raises:
            ValueError: When the period specification is invalid.

        Attributes:
            spec (str): The currently-using period specification.
            start (datetime.date): The start of the period.
            end (datetime.date): The end of the period.
            description (str): The text description of the period.
            error (str): The period specification format error, or
                         None on success.
        """
        VERY_START = datetime.date(1990, 1, 1)

        def __init__(self, spec):
            self.spec = None
            self.start = None
            self.end = None
            self.description = None
            self.error = None

            if spec is None:
                self._set_this_month()
                return
            self.spec = spec
            # A specific month
            m = re.match("^([0-9]{4})-([0-9]{2})$", spec)
            if m is not None:
                year = int(m.group(1))
                month = int(m.group(2))
                # Raises ValueError
                self.start = datetime.date(year, month, 1)
                self.end = self._month_last_day(self.start)
                self.description = self._month_text(year, month)
                return
            # From a specific month
            m = re.match("^([0-9]{4})-([0-9]{2})-$", spec)
            if m is not None:
                year = int(m.group(1))
                month = int(m.group(2))
                # Raises ValueError
                self.start = datetime.date(year, month, 1)
                self.end = self._month_last_day(timezone.localdate())
                self.description = gettext("Since %s")\
                                   % self._month_text(year, month)
                return
            # Until a specific month
            m = re.match("^-([0-9]{4})-([0-9]{2})$", spec)
            if m is not None:
                year = int(m.group(1))
                month = int(m.group(2))
                # Raises ValueError
                until_month = datetime.date(year, month, 1)
                self.start = Period.Parser.VERY_START
                self.end = self._month_last_day(until_month)
                self.description = gettext("Until %s")\
                                   % self._month_text(year, month)
                return
            # A specific year
            m = re.match("^([0-9]{4})$", spec)
            if m is not None:
                year = int(m.group(1))
                # Raises ValueError
                self.start = datetime.date(year, 1, 1)
                self.end = datetime.date(year, 12, 31)
                self.description = self._year_text(year)
                return
            # Until a specific year
            m = re.match("^-([0-9]{4})$", spec)
            if m is not None:
                year = int(m.group(1))
                # Raises ValueError
                self.end = datetime.date(year, 12, 31)
                self.start = Period.Parser.VERY_START
                self.description = gettext("Until %s")\
                                   % self._year_text(year)
                return
            # All time
            if spec == "-":
                self.start = Period.Parser.VERY_START
                self.end = self._month_last_day(timezone.localdate())
                self.description = gettext("All")
                return
            # A specific date
            m = re.match("^([0-9]{4})-([0-9]{2})-([0-9]{2})$",
                         spec)
            if m is not None:
                # Raises ValueError
                self.start = datetime.date(
                    int(m.group(1)),
                    int(m.group(2)),
                    int(m.group(3)))
                self.end = self.start
                self.description = self._date_text(self.start)
                return
            # A specific date period
            m = re.match(("^([0-9]{4})-([0-9]{2})-([0-9]{2})"
                          "-([0-9]{4})-([0-9]{2})-([0-9]{2})$"),
                         spec)
            if m is not None:
                # Raises ValueError
                self.start = datetime.date(
                    int(m.group(1)),
                    int(m.group(2)),
                    int(m.group(3)))
                self.end = datetime.date(
                    int(m.group(4)),
                    int(m.group(5)),
                    int(m.group(6)))
                today = timezone.localdate()
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
                    self.description = self._date_text(self.start)
                return
            # Until a specific day
            m = re.match("^-([0-9]{4})-([0-9]{2})-([0-9]{2})$", spec)
            if m is not None:
                # Raises ValueError
                self.end = datetime.date(
                    int(m.group(1)),
                    int(m.group(2)),
                    int(m.group(3)))
                self.start = Period.Parser.VERY_START
                self.description = gettext("Until %s")\
                                   % self._date_text(self.end)
                return
            # Wrong period format
            raise ValueError

        def _set_this_month(self):
            """Sets the period to this month."""
            today = timezone.localdate()
            self.spec = dateformat.format(today, "Y-m")
            self.start = datetime.date(today.year, today.month, 1)
            self.end = self._month_last_day(self.start)
            self.description = gettext("This Month")

        @staticmethod
        def _month_last_day(day):
            """Calculates and returns the last day of a month.

            Args:
                day (datetime.date): A day in the month.

            Returns:
                date: The last day in the month
            """
            next_month = day.month + 1
            next_year = day.year
            if next_month > 12:
                next_month = 1
                next_year = next_year + 1
            return datetime.date(
                next_year, next_month, 1) - datetime.timedelta(days=1)

        @staticmethod
        def _month_text(year, month):
            """Returns the text description of a month.

            Args:
                year (int): The year.
                month (int): The month.

            Returns:
                str: The description of the month.
            """
            today = timezone.localdate()
            if year == today.year and month == today.month:
                return gettext("This Month")
            prev_month = today.month - 1
            prev_year = today.year
            if prev_month < 1:
                prev_month = 12
                prev_year = prev_year - 1
            prev = datetime.date(prev_year, prev_month, 1)
            if year == prev.year and month == prev.month:
                return gettext("Last Month")
            return "%d/%d" % (year, month)

        @staticmethod
        def _year_text(year):
            """Returns the text description of a year.

            Args:
                year (int): The year.

            Returns:
                str: The description of the year.
            """
            this_year = timezone.localdate().year
            if year == this_year:
                return gettext("This Year")
            if year == this_year - 1:
                return gettext("Last Year")
            return str(year)

        @staticmethod
        def _date_text(day):
            """Returns the text description of a day.

            Args:
                day (datetime.date): The date.

            Returns:
                str: The description of the day.
            """
            today = timezone.localdate()
            if day == today:
                return gettext("Today")
            elif day == today - datetime.timedelta(days=1):
                return gettext("Yesterday")
            elif day.year != today.year:
                return defaultfilters.date(day, "Y/n/j")
            else:
                return defaultfilters.date(day, "n/j")
