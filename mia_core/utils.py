# The core application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/7/1

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

"""The views of the mia core application.

"""

import urllib.parse


class UrlBuilder:
    """The URL builder.

    Attributes:
        base_path (str): the base path
        params (list[Param]): The query parameters
    """
    base_path = None
    params = []

    def __init__(self, start_url):
        """Constructs a new URL builder.

        Args:
            start_url (str): The URL to start with
        """
        pos = start_url.find("?")
        if pos == -1:
            self.base_path = start_url
            return
        self.base_path = start_url[:pos]
        self.params = []
        for piece in start_url[pos+1:].split("&"):
            pos = piece.find("=")
            name = urllib.parse.unquote(piece[:pos])
            value = urllib.parse.unquote(piece[pos+1:])
            self.params.append(self.Param(name, value))

    def add_param(self, name, value):
        """Adds a query parameter.

        Args:
            name (str): The parameter name
            value (str): The parameter value

        Returns:
            UrlBuilder: The URL builder itself, with the parameter
                modified.
        """
        self.params.append(self.Param(name, value))
        return self

    def del_param(self, name):
        """Removes a query parameter.

        Args:
            name (str): The parameter name

        Returns:
            UrlBuilder: The URL builder itself, with the parameter
                modified.
        """
        self.params = [x for x in self.params if x.name != name]
        return self

    def set_param(self, name, value):
        """Sets a query parameter.  The current parameters with the
        same name will be replaced.

        Args:
            name (str): The parameter name
            value (str): The parameter value

        Returns:
            UrlBuilder: The URL builder itself, with the parameter
                modified.
        """
        return self.del_param(name).add_param(name, value)

    def __str__(self):
        if len(self.params) == 0:
            return self.base_path
        return self.base_path + "?" + "&".join([
            str(x) for x in self.params])

    class Param:
        """A query parameter.

        Attributes:
            name (str): The parameter name
            value (str): The parameter value
        """
        name = None
        value = None

        def __init__(self, name, value):
            """Constructs a new query parameter

            Args:
                name (str): The parameter name
                value (str): The parameter value
            """
            self.name = name
            self.value = value

        def __str__(self):
            """Returns the string representation of this query
            parameter.

            Returns:
                str: The string representation of this query
                    parameter
            """
            return "%s=%s" % (
                urllib.parse.quote(self.name),
                urllib.parse.quote(self.value))


class Pagination:
    """The pagination.

    Args:
        records (list[Model]): All the records
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
        records (list[Model]): The records in the current page
    """
    page_no = None
    page_size = None
    records = None

    DEFAULT_PAGE_SIZE = 10

    def __init__(self, records, page_no, page_size, is_reverse=False):
        self.page_size = page_size \
            if page_size is not None \
            else self.DEFAULT_PAGE_SIZE
        total_pages = int((len(records) - 1) / self.page_size) + 1
        default_page = 1 if not is_reverse else total_pages
        if page_no == default_page:
            raise PageNoOutOfRangeException()
        self.page_no = page_no \
            if page_no is not None \
            else default_page
        if self.page_no > total_pages:
            raise PageNoOutOfRangeException()
        start_no = self.page_size * (self.page_no - 1)
        self.records = records[start_no:start_no + self.page_size]


class PageNoOutOfRangeException(Exception):
    """The error thrown when the specified page number is out of
    range.
    """
    pass