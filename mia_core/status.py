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

"""The session-based status management of the Mia core application.

"""
import random

from django.http import HttpResponseRedirect

from .utils import UrlBuilder


def error_redirect(request, url, form):
    """Redirects to a specific URL on error, with the status ID appended
    as the query parameter "s".  The status will be loaded with the
    retrieve_status template tag.

    Args:
        request (HttpRequest): The request.
        url (str): The destination URL.
        form (dict[str]): The received POSTed form.

    Returns:
        HttpResponseRedirect: The redirect response.
    """
    status_id = _store(request, {"form": form})
    return HttpResponseRedirect(str(UrlBuilder(url).query(s=status_id)))


def get_previous_post(request):
    """Retrieves the previously-stored status.

    Args:
        request (HttpRequest): The request.

    Returns:
        dict: The previously-stored status.
    """
    if "s" not in request.GET:
        return None
    status = _retrieve(request, request.GET["s"])
    if "form" not in status:
        return None
    return status["form"]


def _store(request, status):
    """Stores the status into the session, and returns the status ID that can
    be used to retrieve the status later with retrieve().

    Args:
        request (HttpRequest): The request.
        status (dict): The dict of the status.

    Returns:
        str: The status ID
    """
    if "stored_status" not in request.session:
        request.session["stored_status"] = {}
    id = _new_status_id(request.session["stored_status"])
    request.session["stored_status"][id] = status
    return id


def _retrieve(request, id):
    """Stores the status into the session, and returns the status ID that can
    be used to retrieve the status later with retrieve().

    Args:
        request (HttpRequest): The request.
        id (str): The status ID.

    Returns:
        dict: The status, or None if the status does not exist.
    """
    if "stored_status" not in request.session:
        return None
    if id not in request.session["stored_status"]:
        return None
    return request.session["stored_status"][id]


def _new_status_id(status_store):
    """Generates and returns a new status ID that does not exist yet.

    Args:
        status_store (dict): The status storage.

    Returns:
        str: The newly-generated status ID.
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
        if id not in status_store:
            return id
