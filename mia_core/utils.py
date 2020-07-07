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

"""The views of the Mia core application.

"""

import urllib.parse

from django.utils.translation import pgettext


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

    def clone(self):
        """Returns a copy of this URL builder.

        Returns:
            UrlBuilder: A copy of this URL builder.
        """
        another = UrlBuilder(self.base_path)
        another.params = [
            self.Param(x.name, x.value) for x in self.params]
        return another

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
        request (HttpRequest): The request
        records (list[Model]): All the records
        page_no (int): The specified page number
        page_size (int): The specified number of records per page
        is_reversed (bool): Whether we should display the last
                            page first

    Raises:
        PageNoOutOfRangeError: if the specified page number is out
            of range or is redundant.

    Attributes:
        current_url (bool): The current request URL
        is_reversed (bool): Whether we should display the last
                            page first
        page_size (int): The page size.
        total_pages (int): The total number of pages available.
        is_paged (bool): Whether there are more than one page.
        page_no (int): The current page number.
        records (list[Model]): The records in the current page.
        links (list[Link]): The navigation links in the pagination
                            bar.
    """
    current_url = None
    is_reversed = False
    page_size = None
    total_pages = None
    is_paged = None
    page_no = None
    records = None

    DEFAULT_PAGE_SIZE = 10

    def __init__(self, current_url, records, page_no,
                 page_size, is_reversed=False):
        self.current_url = current_url
        self.is_reversed = is_reversed
        self.page_size = page_size \
            if page_size is not None \
            else self.DEFAULT_PAGE_SIZE
        self.total_pages = int(
            (len(records) - 1) / self.page_size) + 1
        self.is_paged = self.total_pages > 1
        if not self.is_paged:
            self.page_no = 1
            self.records = records
            self._links = []
            return
        default_page = 1 if not is_reversed else self.total_pages
        if page_no == default_page:
            raise PageNoOutOfRangeException()
        self.page_no = page_no \
            if page_no is not None \
            else default_page
        if self.page_no > self.total_pages:
            raise PageNoOutOfRangeException()
        start_no = self.page_size * (self.page_no - 1)
        self.records = records[start_no:start_no + self.page_size]

    _links = None

    @property
    def links(self):
        """Returns the navigation links of the pagination bar."""
        if self._links is None:
            base_url = UrlBuilder(self.current_url).del_param("page")
            self._links = []
            # The previous page
            link = self.Link()
            link.title = pgettext("Pagination|", "Previous")
            if self.page_no > 1:
                if self.page_no - 1 == 1:
                    if not self.is_reversed:
                        link.url = str(base_url)
                    else:
                        link.url = str(base_url.clone().add_param(
                            "page", "1"))
                else:
                    link.url = str(base_url.clone().add_param(
                        "page", str(self.page_no - 1)))
            link.is_small_screen = True
            self._links.append(link)
            # The first page
            link = self.Link()
            link.title = "1"
            if not self.is_reversed:
                link.url = str(base_url)
            else:
                link.url = str(base_url.clone().add_param("page", "1"))
            if self.page_no == 1:
                link.is_active = True
            self._links.append(link)
            # The previous ellipsis
            if self.page_no > 4:
                link = self.Link()
                if self.page_no > 5:
                    link.title = pgettext("Pagination|", "...")
                else:
                    link.title = "2"
                    link.url = str(base_url.clone().add_param(
                        "page", "2"))
                self._links.append(link)
            # The nearby pages
            for no in range(self.page_no - 2, self.page_no + 3):
                if no <= 1 or no >= self.total_pages:
                    continue
                link = self.Link()
                link.title = str(no)
                link.url = str(base_url.clone().add_param(
                    "page", str(no)))
                if no == self.page_no:
                    link.is_active = True
                self._links.append(link)
            # The next ellipsis
            if self.page_no + 3 < self.total_pages:
                link = self.Link()
                if self.page_no + 4 < self.total_pages:
                    link.title = pgettext("Pagination|", "...")
                else:
                    link.title = str(self.total_pages - 1)
                    link.url = str(base_url.clone().add_param(
                        "page", str(self.total_pages - 1)))
                self._links.append(link)
            # The last page
            link = self.Link()
            link.title = str(self.total_pages)
            if self.is_reversed:
                link.url = str(base_url)
            else:
                link.url = str(base_url.clone().add_param(
                    "page", str(self.total_pages)))
            if self.page_no == self.total_pages:
                link.is_active = True
            self._links.append(link)
            # The next page
            link = self.Link()
            link.title = pgettext("Pagination|", "Next")
            if self.page_no < self.total_pages:
                if self.page_no + 1 == self.total_pages:
                    if self.is_reversed:
                        link.url = str(base_url)
                    else:
                        link.url = str(base_url.clone().add_param(
                            "page", str(self.total_pages)))
                else:
                    link.url = str(base_url.clone().add_param(
                        "page", str(self.page_no + 1)))
            link.is_small_screen = True
            self._links.append(link)
        return self._links

    class Link:
        """A navigation link in the pagination bar.

        Attributes:
            url (str): The link URL, or for a non-link slot.
            title (str): The title of the link.
            is_active (bool): Whether this link is currently active.
            is_small_screen (bool): Whether this link is for small
                                    screens
        """
        url = None
        title = None
        is_active = False
        is_small_screen = False


class PageNoOutOfRangeException(Exception):
    """The error thrown when the specified page number is out of
    range.
    """
    pass
