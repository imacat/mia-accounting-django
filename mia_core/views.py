# The core application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/7/4

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
from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import DeleteView as CoreDeleteView


class DeleteView(SuccessMessageMixin, CoreDeleteView):
    """The delete form view, with SuccessMessageMixin."""

    def delete(self, request, *args, **kwargs):
        response = super(DeleteView, self).delete(request, *args, **kwargs)
        messages.success(request, self.get_success_message({}))
        return response


@require_GET
def home(request):
    """The view of the home page.

    Args:
        request (HttpRequest): The request.

    Returns:
        HttpResponse: The response.
    """
    return render(request, "index.html")


@require_POST
def logout(request):
    """The view to log out a user.

    Args:
        request (HttpRequest): The request.

    Returns:
        HttpRedirectResponse: The redirect response.
    """
    logout_user(request)
    if "next" in request.POST:
        request.session["logout"] = True
        return redirect(request.POST["next"])
    return redirect("/")


# TODO: To be removed.
def todo(request, **kwargs):
    """A dummy placeholder view for the URL settings that are not
    implemented yet.

    Returns:
        HttpResponse: A dummy response.
    """
    return HttpResponse("TODO: To be done.")
