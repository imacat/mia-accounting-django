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
from typing import Dict, Mapping, Any, Optional

from django.http import HttpResponseRedirect, HttpRequest
from django.shortcuts import redirect

from .utils import UrlBuilder

STORAGE_KEY: str = "stored_post"


def error_redirect(request: HttpRequest, url: str,
                   post: Dict[str, str]) -> HttpResponseRedirect:
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
    return redirect(str(UrlBuilder(url).query(s=post_id)))


def get_previous_post(request: HttpRequest) -> Optional[Dict[str, str]]:
    """Retrieves the previously-stored POST data.

    Args:
        request (HttpRequest): The request.

    Returns:
        dict: The previously-stored POST data.
    """
    if "s" not in request.GET:
        return None
    return _retrieve(request, request.GET["s"])


def _store(request: HttpRequest, post: Dict[str, str]) -> str:
    """Stores the POST data into the session, and returns the POST data ID that
    can be used to retrieve it later with _retrieve().

    Args:
        request: The request.
        post: The POST data.

    Returns:
        The POST data ID
    """
    if STORAGE_KEY not in request.session:
        request.session[STORAGE_KEY] = {}
    post_id = _new_post_id(request.session[STORAGE_KEY])
    request.session[STORAGE_KEY][post_id] = post
    return post_id


def _retrieve(request: HttpRequest, post_id: str) -> Optional[Dict[str, str]]:
    """Retrieves the POST data from the storage.

    Args:
        request: The request.
        post_id: The POST data ID.

    Returns:
        The POST data, or None if the corresponding data does not exist.
    """
    if STORAGE_KEY not in request.session:
        return None
    if post_id not in request.session[STORAGE_KEY]:
        return None
    return request.session[STORAGE_KEY][post_id]


def _new_post_id(post_store: Mapping[int, Any]) -> str:
    """Generates and returns a new POST ID that does not exist yet.

    Args:
        post_store (dict): The POST storage.

    Returns:
        str: The newly-generated POST ID.
    """
    while True:
        post_id = ""
        while len(post_id) < 16:
            n = random.randint(1, 64)
            if n < 26:
                post_id = post_id + chr(ord("a") + n)
            elif n < 52:
                post_id = post_id + chr(ord("a") + (n - 26))
            elif n < 62:
                post_id = post_id + chr(ord("0") + (n - 52))
            else:
                post_id = post_id + "-_."[n - 62]
        if post_id not in post_store:
            return post_id
