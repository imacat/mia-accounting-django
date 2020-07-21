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

"""The view controllers of the accounting application.

"""

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_GET

from mia_core.digest_auth import digest_login_required


# noinspection PyUnusedLocal
@require_GET
@digest_login_required
def home(request):
    """The accounting home page.

    Args:
        request (HttpRequest) The request.

    Returns:
        HttpResponseRedirect: The redirection to the default
            accounting report.
    """
    return HttpResponseRedirect(reverse("accounting:cash.home"))
