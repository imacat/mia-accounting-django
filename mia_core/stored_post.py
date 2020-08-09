# The core application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/7/24

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

"""The session-based POST data storage management of the Mia core application.

"""
import random

from django.http import HttpResponseRedirect

from .utils import UrlBuilder

STORAGE_KEY = "stored_post"


def error_redirect(request, url, post):
    """Redirects to a specific URL on error, with the POST data ID appended
    as the query parameter "s".  The POST data can be loaded with the
    get_previous_post() utility.

    Args:
        request (HttpRequest): The request.
        url (str): The destination URL.
        post (dict[str]): The POST data.

    Returns:
        HttpResponseRedirect: The redirect response.
    """
    post_id = _store(request, post)
    return HttpResponseRedirect(str(UrlBuilder(url).query(s=post_id)))


def get_previous_post(request):
    """Retrieves the previously-stored POST data.

    Args:
        request (HttpRequest): The request.

    Returns:
        dict: The previously-stored POST data.
    """
    if "s" not in request.GET:
        return None
    return _retrieve(request, request.GET["s"])


def _store(request, post):
    """Stores the POST data into the session, and returns the POST data ID that
    can be used to retrieve it later with _retrieve().

    Args:
        request (HttpRequest): The request.
        post (dict): The POST data.

    Returns:
        str: The POST data ID
    """
    if STORAGE_KEY not in request.session:
        request.session[STORAGE_KEY] = {}
    id = _new_post_id(request.session[STORAGE_KEY])
    request.session[STORAGE_KEY][id] = post
    return id


def _retrieve(request, id):
    """Retrieves the POST data from the storage.

    Args:
        request (HttpRequest): The request.
        id (str): The POST data ID.

    Returns:
        dict: The POST data, or None if the corresponding data does not exist.
    """
    if STORAGE_KEY not in request.session:
        return None
    if id not in request.session[STORAGE_KEY]:
        return None
    return request.session[STORAGE_KEY][id]


def _new_post_id(post_store):
    """Generates and returns a new POST ID that does not exist yet.

    Args:
        post_store (dict): The POST storage.

    Returns:
        str: The newly-generated POST ID.
    """
    while True:
        id = ""
        while len(id) < 16:
            n = random.randint(1, 64)
            if n < 26:
                id = id + chr(ord("a") + n)
            elif n < 52:
                id = id + chr(ord("a") + (n - 26))
            elif n < 62:
                id = id + chr(ord("0") + (n - 52))
            else:
                id = id + "-_."[n - 62]
        if id not in post_store:
            return id
