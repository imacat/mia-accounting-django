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

"""The utilities of the accounting application.

"""


class PeriodParser:
    """The period parser.

    Args:
        period_spec (str): The period specification.

    Attributes:
        start (str): The start of the period.
        end (str): The end of the period.
    """
    start = None
    end = None

    def __init__(self, period_spec):
        self.start = period_spec + "-01"
        self.end = period_spec + "-30"


class Pagination:
    """The pagination.

    Args:
        count (int): The total number of records
        page_no (int): The specified page number
        page_size (int): The specified number of records per page
        is_reverse (bool): Whether we should display the last
                           page first

    Raises:
        PageNoOutOfRangeError: if the specified page number is out
            of range or is redundant.

    Attributes:
        page_no (int): The current page number
        page_size (int): The page size
    """
    page_no = None
    page_size = None

    DEFAULT_PAGE_SIZE = 10

    def __init__(self, count, page_no, page_size, is_reverse = False):
        self.page_size = page_size \
            if page_size is not None \
            else self.DEFAULT_PAGE_SIZE
        total_pages = int((count - 1) / self.page_size) + 1
        default_page = 1 if not is_reverse else total_pages
        if page_no == default_page:
            raise PageNoOutOfRangeError()
        self.page_no = page_no \
            if page_no is not None \
            else default_page
        if self.page_no > total_pages:
            raise PageNoOutOfRangeError()


class PageNoOutOfRangeError(Exception):
    pass
