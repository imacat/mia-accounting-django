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

"""The utilities for the HTTP digest authentication.

"""
from functools import wraps

from django.http import HttpResponse

from mia_core.models import User


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
        print("mia_core.digest_auth.AccountBackend.get_user(): " + str(User.objects.filter(
            login_id=username).first()))
        return User.objects.filter(login_id=username).first()


def digest_login_required(function=None):
    """The decorator to check if the user has logged in, and send
    HTTP 401 if the user has not logged in.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_anonymous:
                return HttpResponse(status=401)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    if function:
        return decorator(function)
    return decorator
