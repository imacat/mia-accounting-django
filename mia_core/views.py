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
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_noop
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import DeleteView as CoreDeleteView, ListView, \
    DetailView

from . import stored_post
from .digest_auth import login_required
from .forms import UserForm
from .models import User
from .utils import strip_post


class DeleteView(SuccessMessageMixin, CoreDeleteView):
    """The delete form view, with SuccessMessageMixin."""

    def delete(self, request, *args, **kwargs):
        response = super(DeleteView, self).delete(request, *args, **kwargs)
        messages.success(request, self.get_success_message({}))
        return response


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
    return redirect("home")


@method_decorator(require_GET, name="dispatch")
@method_decorator(login_required, name="dispatch")
class UserListView(ListView):
    """The view to list the users."""
    queryset = User.objects.order_by("login_id")


@method_decorator(require_GET, name="dispatch")
@method_decorator(login_required, name="dispatch")
class UserView(DetailView):
    """The view of a user."""
    def get_object(self, queryset=None):
        return self.request.resolver_match.kwargs["user"]


@require_GET
@login_required
def user_form(request, user=None):
    """The view to edit an accounting transaction.

    Args:
        request (HttpRequest): The request.
        user (User): The account.

    Returns:
        HttpResponse: The response.
    """
    previous_post = stored_post.get_previous_post(request)
    if previous_post is not None:
        form = UserForm(previous_post)
    elif user is not None:
        form = UserForm({
            "login_id": user.login_id,
            "name": user.name,
            "is_disabled": user.is_disabled,
        })
    else:
        form = UserForm()
    form.user = user
    form.current_user = request.user
    return render(request, "mia_core/user_form.html", {
        "form": form,
    })


def user_store(request, user=None):
    """The view to store a user.

    Args:
        request (HttpRequest): The request.
        user (Account): The user.

    Returns:
        HttpResponseRedirect: The response.
    """
    post = request.POST.dict()
    strip_post(post)
    form = UserForm(post)
    form.user = user
    form.current_user = request.user
    if not form.is_valid():
        if user is None:
            url = reverse("mia_core:users.create")
        else:
            url = reverse("mia_core:users.edit", args=(user,))
        return stored_post.error_redirect(request, url, post)
    if user is None:
        user = User()
    user.login_id = form["login_id"].value()
    if form["password"].value() is not None:
        user.set_digest_password(
            form["login_id"].value(), form["password"].value())
    user.name = form["name"].value()
    user.is_disabled = form["is_disabled"].value()
    if not user.is_dirty():
        message = gettext_noop("This user account was not changed.")
    else:
        user.save(current_user=request.user)
        message = gettext_noop("This user account was saved successfully.")
    messages.success(request, message)
    return redirect("mia_core:users.detail", user)


@require_POST
@login_required
def user_delete(request, user):
    """The view to delete an user.

    Args:
        request (HttpRequest): The request.
        user (User): The user.

    Returns:
        HttpResponseRedirect: The response.
    """
    message = None
    if user.pk == request.user.pk:
        message = gettext_noop("You cannot delete your own account.")
    elif user.is_in_use():
        message = gettext_noop(
            "You cannot delete this account because it is in use.")
    elif user.is_deleted:
        message = gettext_noop("This account is already deleted.")
    if message is not None:
        messages.error(request, message)
        return redirect("mia_core:users.detail", user)
    user.delete()
    message = gettext_noop("This user account was deleted successfully.")
    messages.success(request, message)
    return redirect("mia_core:users")



def api_users_exists(request, login_id):
    """The view to check whether a user with a log in ID exists.

    Args:
        request (HttpRequest): The request.
        login_id (str): The log in ID.

    Returns:
        JsonResponse: The response.
    """
    try:
        User.objects.get(login_id=login_id)
    except User.DoesNotExist:
        return JsonResponse(False, safe=False)
    return JsonResponse(True, safe=False)


# TODO: To be removed.
def todo(request, **kwargs):
    """A dummy placeholder view for the URL settings that are not
    implemented yet.

    Returns:
        HttpResponse: A dummy response.
    """
    return HttpResponse("TODO: To be done.")
