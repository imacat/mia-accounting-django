# The core application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/7/5

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

"""The HTTP digest authentication utilities of the Mia core
application.

"""
import ipaddress
import socket
from functools import wraps

from django.conf import settings
from django.db.models import F
from django.db.models.functions import Now
from django.http import HttpResponse, HttpRequest
from geoip import geolite2

from .models import User, Country


class AccountBackend:
    """The account backend for the django-digest module."""

    def get_partial_digest(self, username):
        """Returns the HTTP digest authentication password digest hash
        of a user.

        Args:
            username (str): The log in user name.

        Return:
            str: The HTTP digest authentication password hash of
            the user, or None if the user does not exist.
        """
        user = User.objects.filter(login_id=username).first()
        if user is None:
            return None
        return user.password

    def get_user(self, username):
        """Returns the user by her log in user name.

        Args:
            username (str): The log in user name.

        Return:
            User: The user, or None if the user does not eixst.
        """
        return User.objects.filter(login_id=username).first()


def login_required(function=None):
    """The decorator to check if the user has logged in, and send
    HTTP 401 if the user has not logged in.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_anonymous:
                return HttpResponse(status=401)
            if "logout" in request.session:
                del request.session["logout"]
                if "visit_logged" in request.session:
                    del request.session["visit_logged"]
                return HttpResponse(status=401)
            if not settings.DEBUG:
                _log_visit(request)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    if function:
        return decorator(function)
    return decorator


def _log_visit(request):
    """Logs the visit information for the logged-in user.

    Args:
        request (HttpRequest): The request.
    """
    if "visit_logged" in request.session:
        return
    user = request.user
    ip = _get_remote_ip(request)
    User.objects.filter(pk=user.pk).update(
        visits=F("visits") + 1,
        visited_at=Now(),
        visited_ip=ip,
        visited_host=_get_host(ip),
        visited_country=_get_country(ip),
    )
    request.session["visit_logged"] = True


def _get_remote_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get('REMOTE_ADDR')


def _get_host(ip):
    """Look-up the host name by its IP.

    Args:
        ip (str): The IP

    Returns:
        str: The host name, or None if the look-up fails.
    """
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None


def _get_country(ip):
    """Look-up the country by its IP.

    Args:
        ip (str): The IP

    Returns:
        Country: The country.
    """
    code = _get_country_code(ip)
    try:
        return Country.objects.get(code=code)
    except Country.DoesNotExist:
        pass
    return None


def _get_country_code(ip):
    """Look-up the country code by its IP.

    Args:
        ip (str): The IP

    Returns:
        str: The country code, or None if the look-up fails.
    """
    try:
        return geolite2.lookup(ip).country
    except ValueError:
        pass
    except AttributeError:
        pass
    try:
        ipaddr = ipaddress.ip_address(ip)
        if ipaddr.is_private:
            return "AA"
    except ValueError:
        pass
    return None
