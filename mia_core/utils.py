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

"""The utilities of the Mia core application.

"""
import random
import urllib.parse

from django.conf import settings
from django.db.models import Model, Q
from django.utils.translation import pgettext, get_language


def new_pk(cls):
    """Finds a random ID that does not conflict with the existing data records.

    Args:
        cls (class): The Django model class.

    Returns:
         int: The new random ID.
    """
    while True:
        id = random.randint(100000000, 999999999)
        try:
            cls.objects.get(pk=id)
        except cls.DoesNotExist:
            return id


def strip_form(form):
    """Strips the values of a form.  Empty strings are converted to None.

    Args:
        form (dict[str]): The form.
    """
    for key in form.keys():
        form[key] = form[key].strip()


class Language:
    """A language.

    Args:
        language (str): The Django language code.

    Attributes:
        id (str): The language ID
        db (str): The database column suffix of this language.
        locale (str); The locale name of this language.
        is_default (bool): Whether this is the default language.
    """
    id = None
    db = None
    locale = None
    is_default = False

    def __init__(self, language):
        self.id = language
        self.db = "_" + language.lower().replace("-", "_")
        if language == "zh-hant":
            self.locale = "zh-TW"
        elif language == "zh-hans":
            self.locale = "zh-CN"
        else:
            self.locale = language
        self.is_default = (language == settings.LANGUAGE_CODE)

    @staticmethod
    def default():
        return Language(settings.LANGUAGE_CODE)

    @staticmethod
    def current():
        return Language(get_language())


def get_multi_lingual_attr(model, name, default=None):
    """Returns a multi-lingual attribute of a data model.

    Args:
        model (object): The data model.
        name (str): The attribute name.
        default (str): The default language.

    Returns:
        (any): The attribute in this language, or in the default
            language if there is no content in the current language.
    """
    language = Language.current()
    title = getattr(model, name + language.db)
    if default is None:
        default = Language.default().id
    if language.id == default:
        return title
    if title is not None:
        return title
    return getattr(model, name + Language.default().db)


def set_multi_lingual_attr(model, name, value):
    """Sets a multi-lingual attribute of a data model.

    Args:
        model (object): The data model.
        name (str): The attribute name.
        value (any): The new value
    """
    language = Language.current()
    setattr(model, name + language.db, value)


def get_multi_lingual_search(attr, query):
    """Returns the query condition on a multi-lingual attribute.

    Args:
        attr (str): The base name of the multi-lingual attribute.
        query (str): The query.

    Returns:
        Q: The query condition
    """
    language = Language.current()
    if language.is_default:
        return Q(**{attr + language.db + "__icontains": query})
    default = Language.default()
    q = (Q(**{attr + language.db + "__isnull": False})
            & Q(**{attr + language.db + "__icontains": query}))\
           | (Q(**{attr + language.db + "__isnull": True})
              & Q(**{attr + default.db + "__icontains": query}))
    return q


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
        for piece in start_url[pos + 1:].split("&"):
            pos = piece.find("=")
            name = urllib.parse.unquote(piece[:pos])
            value = urllib.parse.unquote(piece[pos + 1:])
            self.params.append(self.Param(name, value))

    def add(self, name, value):
        """Adds a query parameter.

        Args:
            name (str): The parameter name
            value (str): The parameter value

        Returns:
            UrlBuilder: The URL builder itself, with the parameter
                modified.
        """
        if value is not None:
            self.params.append(self.Param(name, value))
        return self

    def remove(self, name):
        """Removes a query parameter.

        Args:
            name (str): The parameter name

        Returns:
            UrlBuilder: The URL builder itself, with the parameter
                modified.
        """
        self.params = [x for x in self.params if x.name != name]
        return self

    def set(self, name, value):
        """Sets a query parameter.  The current parameters with the
        same name will be replaced.

        Args:
            name (str): The parameter name
            value (str): The parameter value

        Returns:
            UrlBuilder: The URL builder itself, with the parameter
                modified.
        """
        return self.remove(name).add(name, value)

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
        items (list): All the items
        page_no (int): The specified page number
        page_size (int): The specified number of items per page
        is_reversed (bool): Whether we should display the last
                            page first

    Raises:
        PaginationException: With invalid pagination parameters

    Attributes:
        is_reversed (bool): Whether we should display the last
                            page first
        page_size (int): The page size.
        total_pages (int): The total number of pages available.
        is_paged (bool): Whether there are more than one page.
        page_no (int): The current page number.
        items (list[Model]): The items in the current page.
        links (list[Link]): The navigation links in the pagination
                            bar.
        page_size_options(list[PageSizeOptions]): The page size
                                                  options
    """
    _current_url = None
    is_reversed = False
    page_size = None
    total_pages = None
    is_paged = None
    page_no = None
    items = None

    DEFAULT_PAGE_SIZE = 10

    def __init__(self, request, items, is_reversed=False):
        current_url = request.get_full_path()
        self._current_url = current_url
        self.is_reversed = is_reversed

        # The page size
        try:
            self.page_size = int(request.GET["page-size"])
            if self.page_size == self.DEFAULT_PAGE_SIZE:
                raise PaginationException(str(
                    UrlBuilder(current_url).remove("page-size")))
            if self.page_size < 1:
                raise PaginationException(str(
                    UrlBuilder(current_url).remove("page-size")))
        except KeyError:
            self.page_size = self.DEFAULT_PAGE_SIZE
        except ValueError:
            raise PaginationException(str(
                UrlBuilder(current_url).remove("page-size")))
        self.total_pages = int(
            (len(items) - 1) / self.page_size) + 1
        default_page_no = 1 if not is_reversed else self.total_pages
        self.is_paged = self.total_pages > 1

        # The page number
        try:
            self.page_no = int(request.GET["page"])
            if not self.is_paged:
                raise PaginationException(str(
                    UrlBuilder(current_url).remove("page")))
            if self.page_no == default_page_no:
                raise PaginationException(str(
                    UrlBuilder(current_url).remove("page")))
            if self.page_no < 1:
                raise PaginationException(str(
                    UrlBuilder(current_url).remove("page")))
            if self.page_no > self.total_pages:
                raise PaginationException(str(
                    UrlBuilder(current_url).remove("page")))
        except KeyError:
            self.page_no = default_page_no
        except ValueError:
            raise PaginationException(str(
                UrlBuilder(current_url).remove("page")))

        if not self.is_paged:
            self.page_no = 1
            self.items = items
            return
        start_no = self.page_size * (self.page_no - 1)
        self.items = items[start_no:start_no + self.page_size]

    _links = None

    @property
    def links(self):
        """Returns the navigation links of the pagination bar."""
        if self._links is None:
            base_url = UrlBuilder(self._current_url).remove("page")
            self._links = []
            # The previous page
            link = self.Link()
            link.title = pgettext("Pagination|", "Previous")
            if self.page_no > 1:
                if self.page_no - 1 == 1:
                    if not self.is_reversed:
                        link.url = str(base_url)
                    else:
                        link.url = str(base_url.clone().add(
                            "page", "1"))
                else:
                    link.url = str(base_url.clone().add(
                        "page", str(self.page_no - 1)))
            link.is_small_screen = True
            self._links.append(link)
            # The first page
            link = self.Link()
            link.title = "1"
            if not self.is_reversed:
                link.url = str(base_url)
            else:
                link.url = str(base_url.clone().add(
                    "page", "1"))
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
                    link.url = str(base_url.clone().add(
                        "page", "2"))
                self._links.append(link)
            # The nearby pages
            for no in range(self.page_no - 2, self.page_no + 3):
                if no <= 1 or no >= self.total_pages:
                    continue
                link = self.Link()
                link.title = str(no)
                link.url = str(base_url.clone().add(
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
                    link.url = str(base_url.clone().add(
                        "page", str(self.total_pages - 1)))
                self._links.append(link)
            # The last page
            link = self.Link()
            link.title = str(self.total_pages)
            if self.is_reversed:
                link.url = str(base_url)
            else:
                link.url = str(base_url.clone().add(
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
                        link.url = str(base_url.clone().add(
                            "page", str(self.total_pages)))
                else:
                    link.url = str(base_url.clone().add(
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

    @property
    def page_size_options(self):
        base_url = UrlBuilder(self._current_url).remove(
            "page").remove("page-size")
        return [self.PageSizeOption(x, self._page_size_url(base_url, x))
                for x in [10, 100, 200]]

    @staticmethod
    def _page_size_url(base_url, size):
        """Returns the URL for a new page size.

        Args:
            base_url (UrlBuilder): The base URL builder.
            size (int): The new page size.

        Returns:
            str: The URL for the new page size.
        """
        if size == Pagination.DEFAULT_PAGE_SIZE:
            return str(base_url)
        return str(base_url.clone().add("page-size", str(size)))

    class PageSizeOption:
        """A page size option.

        Args:
            size (int): The page size.
            url (str): The URL of this page size.

        Attributes:
            size (int): The page size.
            url (str): The URL for this page size.
        """
        size = None
        url = None

        def __init__(self, size, url):
            self.size = size
            self.url = url


class PaginationException(Exception):
    """The exception thrown with invalid pagination parameters.

    Args:
        url (str): The canonical URL to redirect to.

    Attributes:
        url (str): The canonical URL to redirect to.
    """
    url = None

    def __init__(self, url):
        self.url = url
