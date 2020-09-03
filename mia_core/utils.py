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
import datetime
import random
import urllib.parse
from typing import Dict, List, Any, Type

from django.conf import settings
from django.db.models import Model
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import pgettext, get_language


def new_pk(cls: Type[Model]) -> int:
    """Finds a random ID that does not conflict with the existing data records.

    Args:
        cls: The Django model class.

    Returns:
         The new random ID.
    """
    while True:
        pk = random.randint(100000000, 999999999)
        try:
            cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            return pk


def strip_post(post: Dict[str, str]) -> None:
    """Strips the values of the POSTed data.  Empty strings are removed.

    Args:
        post (dict[str]): The POSTed data.
    """
    for key in list(post.keys()):
        post[key] = post[key].strip()
        if post[key] == "":
            del post[key]


def parse_date(s: str):
    """Parses a string for a date.  The date can be either YYYY-MM-DD,
    Y/M/D, or M/D/Y.

    Args:
        s: The string.

    Returns:
        The date.

    Raises:
        ValueError: When the string is not in a valid format.
    """
    for f in ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"]:
        try:
            return datetime.datetime.strptime(s, f)
        except ValueError:
            pass
    raise ValueError(F"not a recognized date {s}")


class Language:
    """A language.

    Args:
        language: The Django language code.

    Attributes:
        id (str): The language ID
        db (str): The database column suffix of this language.
        locale (str); The locale name of this language.
        is_default (bool): Whether this is the default language.
    """
    def __init__(self, language: str):
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


class UrlBuilder:
    """The URL builder.

    Attributes:
        path (str): the base path
        params (list[Param]): The query parameters
    """
    def __init__(self, start_url: str):
        """Constructs a new URL builder.

        Args:
            start_url (str): The URL to start with
        """
        pos = start_url.find("?")
        if pos == -1:
            self.path = start_url
            self.params = []
            return
        self.path = start_url[:pos]
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

    def query(self, **kwargs):
        """A keyword-styled query parameter setter.  The existing values are
        always replaced.  Multiple-values are added when the value is a list or
        tuple.  The existing values are dropped when the value is None.
        """
        for key in kwargs:
            self.remove(key)
            if isinstance(kwargs[key], list) or isinstance(kwargs[key], tuple):
                for value in kwargs[key]:
                    self.add(key, value)
            elif kwargs[key] is None:
                pass
            else:
                self.add(key, kwargs[key])
        return self

    def clone(self):
        """Returns a copy of this URL builder.

        Returns:
            UrlBuilder: A copy of this URL builder.
        """
        another = UrlBuilder(self.path)
        another.params = [
            self.Param(x.name, x.value) for x in self.params]
        return another

    def __str__(self) -> str:
        if len(self.params) == 0:
            return self.path
        return self.path + "?" + "&".join([
            str(x) for x in self.params])

    class Param:
        """A query parameter.

        Attributes:
            name: The parameter name
            value: The parameter value
        """
        def __init__(self, name: str, value: str):
            """Constructs a new query parameter

            Args:
                name (str): The parameter name
                value (str): The parameter value
            """
            self.name = name
            self.value = value

        def __str__(self) -> str:
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
        request: The request.
        items: All the items.
        is_reversed: Whether we should display the last page first.

    Raises:
        PaginationException: With invalid pagination parameters

    Attributes:
        current_url (UrlBuilder): The current request URL.
        is_reversed (bool): Whether we should display the last page first.
        page_size (int): The page size.
        total_pages (int): The total number of pages available.
        is_paged (bool): Whether there are more than one page.
        page_no (int): The current page number.
        items (list[Model]): The items in the current page.
    """
    DEFAULT_PAGE_SIZE = 10

    def __init__(self, request: HttpRequest, items: List[Any],
                 is_reversed: bool = False):
        self.current_url = UrlBuilder(request.get_full_path())
        self.is_reversed = is_reversed
        self.page_size = self.DEFAULT_PAGE_SIZE
        self.total_pages = None
        self.is_paged = None
        self.page_no = 1
        self.items = []

        # The page size
        try:
            self.page_size = int(request.GET["page-size"])
            if self.page_size == self.DEFAULT_PAGE_SIZE:
                raise PaginationException(self.current_url.remove("page-size"))
            if self.page_size < 1:
                raise PaginationException(self.current_url.remove("page-size"))
        except KeyError:
            self.page_size = self.DEFAULT_PAGE_SIZE
        except ValueError:
            raise PaginationException(self.current_url.remove("page-size"))
        self.total_pages = int(
            (len(items) - 1) / self.page_size) + 1
        default_page_no = 1 if not is_reversed else self.total_pages
        self.is_paged = self.total_pages > 1

        # The page number
        try:
            self.page_no = int(request.GET["page"])
            if not self.is_paged:
                raise PaginationException(self.current_url.remove("page"))
            if self.page_no == default_page_no:
                raise PaginationException(self.current_url.remove("page"))
            if self.page_no < 1:
                raise PaginationException(self.current_url.remove("page"))
            if self.page_no > self.total_pages:
                raise PaginationException(self.current_url.remove("page"))
        except KeyError:
            self.page_no = default_page_no
        except ValueError:
            raise PaginationException(self.current_url.remove("page"))

        if not self.is_paged:
            self.page_no = 1
            self.items = items
            return
        start_no = self.page_size * (self.page_no - 1)
        self.items = items[start_no:start_no + self.page_size]

    def links(self):
        """Returns the navigation links of the pagination bar.

        Returns:
            List[Link]: The navigation links of the pagination bar.
        """
        base_url = self.current_url.clone().remove("page").remove("s")
        links = []
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
        links.append(link)
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
        links.append(link)
        # The previous ellipsis
        if self.page_no > 4:
            link = self.Link()
            if self.page_no > 5:
                link.title = pgettext("Pagination|", "...")
            else:
                link.title = "2"
                link.url = str(base_url.clone().add(
                    "page", "2"))
            links.append(link)
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
            links.append(link)
        # The next ellipsis
        if self.page_no + 3 < self.total_pages:
            link = self.Link()
            if self.page_no + 4 < self.total_pages:
                link.title = pgettext("Pagination|", "...")
            else:
                link.title = str(self.total_pages - 1)
                link.url = str(base_url.clone().add(
                    "page", str(self.total_pages - 1)))
            links.append(link)
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
        links.append(link)
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
        links.append(link)
        return links

    class Link:
        """A navigation link in the pagination bar.

        Attributes:
            url (str): The link URL, or for a non-link slot.
            title (str): The title of the link.
            is_active (bool): Whether this link is currently active.
            is_small_screen (bool): Whether this link is for small
                                    screens
        """
        def __int__(self):
            self.url = None
            self.title = None
            self.is_active = False
            self.is_small_screen = False

    def page_size_options(self):
        """Returns the page size options.

        Returns:
            List[PageSizeOption]: The page size options.
        """
        base_url = self.current_url.remove("page").remove("page-size")
        return [self.PageSizeOption(x, self._page_size_url(base_url, x))
                for x in [10, 100, 200]]

    @staticmethod
    def _page_size_url(base_url: UrlBuilder, size: int) -> str:
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
            size: The page size.
            url: The URL of this page size.

        Attributes:
            size (int): The page size.
            url (str): The URL for this page size.
        """
        def __init__(self, size: int, url: str):
            self.size = size
            self.url = url


class PaginationException(Exception):
    """The exception thrown with invalid pagination parameters.

    Args:
        url_builder: The canonical URL to redirect to.

    Attributes:
        url (str): The canonical URL to redirect to.
    """
    def __init__(self, url_builder: UrlBuilder):
        self.url = str(url_builder)


CDN_LIBRARIES = {
    "jquery": {"css": [],
               "js": ["https://code.jquery.com/jquery-3.5.1.min.js"]},
    "bootstrap4": {
        "css": [("https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/"
                 "bootstrap.min.css")],
        "js": [("https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/"
                "popper.min.js"),
               ("https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/"
                "bootstrap.min.js")]},
    "font-awesome-5": {
        "css": ["https://use.fontawesome.com/releases/v5.14.0/css/all.css"],
        "js": []},
    "bootstrap4-datatables": {
        "css": [("https://cdn.datatables.net/1.10.21/css/"
                 "jquery.dataTables.min.css"),
                ("https://cdn.datatables.net/1.10.21/css/"
                 "dataTables.bootstrap4.min.css")],
        "js": [("https://cdn.datatables.net/1.10.21/js/"
                "jquery.dataTables.min.js"),
               ("https://cdn.datatables.net/1.10.21/js/"
                "dataTables.bootstrap4.min.js")]},
    "jquery-ui": {"css": [("https://cdnjs.cloudflare.com/ajax/libs/jqueryui/"
                           "1.12.1/jquery-ui.min.css")],
                  "js": [("https://cdnjs.cloudflare.com/ajax/libs/jqueryui/"
                          "1.12.1/jquery-ui.min.js")]},
    "bootstrap4-tempusdominus": {
        "css": [("https://cdnjs.cloudflare.com/ajax/libs/"
                 "tempusdominus-bootstrap-4/5.1.2/css/"
                 "tempusdominus-bootstrap-4.min.css")],
        "js": [("https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.27.0/"
                "moment-with-locales.min.js"),
               ("https://cdnjs.cloudflare.com/ajax/libs/"
                "tempusdominus-bootstrap-4/5.1.2/js/"
                "tempusdominus-bootstrap-4.js")]},
    "decimal-js": {"css": [],
                   "js": [("https://cdnjs.cloudflare.com/ajax/libs/decimal.js/"
                           "10.2.0/decimal.min.js")]},
    "period-chooser": {"css": ["mia_core/css/period-chooser.css"],
                       "js": ["mia_core/js/period-chooser.js"]}
}
DEFAULT_LIBS = []


class CssAndJavaScriptLibraries:
    """The CSS and JavaScript library resolver."""
    AVAILABLE_LIBS: List[str] = ["jquery", "bootstrap4", "font-awesome-5",
                                 "bootstrap4-datatables", "jquery-ui",
                                 "bootstrap4-tempusdominus", "decimal-js",
                                 "i18n", "period-chooser"]

    def __init__(self, *args):
        self._use: Dict[str, bool] = {x: False for x in self.AVAILABLE_LIBS}
        self._add_default_libs()
        # The specified libraries
        if len(args) > 0:
            libs = args[0]
            invalid = [x for x in libs if x not in self.AVAILABLE_LIBS]
            if len(invalid) > 0:
                raise NameError("library %s invalid" % ", ".join(invalid))
            for lib in libs:
                self._use[lib] = True
        self._css = []
        try:
            self._css = self._css + settings.DEFAULT_CSS
        except AttributeError:
            pass
        self._js = []
        try:
            self._css = self._css + settings.DEFAULT_JS
        except AttributeError:
            pass

    def _add_default_libs(self):
        """Adds the default libraries."""
        invalid = [x for x in DEFAULT_LIBS if x not in self.AVAILABLE_LIBS]
        if len(invalid) > 0:
            raise NameError("library %s invalid" % ", ".join(invalid))
        for lib in DEFAULT_LIBS:
            self._use[lib] = True

    def use(self, *args) -> None:
        """Use the specific libraries.

        Args:
            args: The libraries.
        """
        if len(args) == 0:
            return
        libs = args[0]
        invalid = [x for x in libs if x not in self.AVAILABLE_LIBS]
        if len(invalid) > 0:
            raise NameError("library %s invalid" % ", ".join(invalid))
        for lib in libs:
            self._use[lib] = True

    def add_css(self, css) -> None:
        """Adds a custom CSS file."""
        self._css.append(css)

    def add_js(self, js) -> None:
        """Adds a custom JavaScript file."""
        self._js.append(js)

    def css(self) -> List[str]:
        """Returns the stylesheet files to use."""
        use: Dict[str, bool] = self._solve_use_dependencies()
        css = []
        for lib in [x for x in self.AVAILABLE_LIBS if use[x]]:
            if lib == "i18n":
                continue
            try:
                css = css + settings.STATIC_LIBS[lib]["css"]
            except AttributeError:
                css = css + CDN_LIBRARIES[lib]["css"]
            except TypeError:
                css = css + CDN_LIBRARIES[lib]["css"]
            except KeyError:
                css = css + CDN_LIBRARIES[lib]["css"]
        return css + self._css

    def js(self) -> List[str]:
        """Returns the JavaScript files to use."""
        use: Dict[str, bool] = self._solve_use_dependencies()
        js = []
        for lib in [x for x in self.AVAILABLE_LIBS if use[x]]:
            if lib == "i18n":
                js.append(reverse("javascript-catalog"))
                continue
            try:
                js = js + settings.STATIC_LIBS[lib]["js"]
            except AttributeError:
                js = js + CDN_LIBRARIES[lib]["js"]
            except TypeError:
                js = js + CDN_LIBRARIES[lib]["js"]
            except KeyError:
                js = js + CDN_LIBRARIES[lib]["js"]
        return js + self._js

    def _solve_use_dependencies(self) -> Dict[str, bool]:
        """Solves and returns the library dependencies."""
        use: Dict[str, bool] = {x: self._use[x] for x in self._use}
        if use["period-chooser"]:
            use["bootstrap4-tempusdominus"] = True
        if use["bootstrap4-tempusdominus"]:
            use["bootstrap4"] = True
        if use["bootstrap4-datatables"]:
            use["bootstrap4"] = True
        if use["jquery-ui"]:
            use["jquery"] = True
        if use["bootstrap4"]:
            use["jquery"] = True
        return use


def add_default_libs(*args) -> None:
    """Adds the specified libraries to the default CSS and JavaScript
    libraries.

    Args:
        args: The libraries to be added to the default libraries
    """
    libs = args
    invalid = [x for x in libs
               if x not in CssAndJavaScriptLibraries.AVAILABLE_LIBS]
    if len(invalid) > 0:
        raise NameError("library %s invalid" % ", ".join(invalid))
    for lib in libs:
        if lib not in DEFAULT_LIBS:
            DEFAULT_LIBS.append(lib)
