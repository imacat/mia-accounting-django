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
from typing import Dict, Type, Optional

from dirtyfields import DirtyFieldsMixin
from django import forms
from django.contrib import messages
from django.contrib.auth import logout as logout_user
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Model
from django.http import HttpResponse, JsonResponse, HttpRequest, \
    HttpResponseRedirect, Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_noop
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import DeleteView as CoreDeleteView, ListView, \
    DetailView
from django.views.generic.base import View

from . import stored_post, utils
from .digest_auth import login_required
from .forms import UserForm
from .models import User
from .utils import UrlBuilder


class FormView(View):
    """The base form view."""
    model: Type[Model] = None
    form_class: Type[forms.Form] = None
    template_name: str = None
    context_object_name: str = "form"
    success_url: str = None
    error_url: str = None
    not_modified_message: str = None
    success_message: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._object = None
        self._is_object_requested = False

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """The view to store an accounting transaction."""
        if self.request.method != "POST":
            return self.get(request, *args, **kwargs)
        else:
            return self.post(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handles the GET requests."""
        obj = self.get_object()
        previous_post = stored_post.get_previous_post(self.request)
        if previous_post is not None:
            form = self.make_form_from_post(previous_post)
        elif obj is not None:
            form = self.make_form_from_model(obj)
        else:
            form = self.get_form_class()()
        return render(self.request, self.get_template_name(), {
            self.context_object_name: form
        })

    def post(self, request: HttpRequest, *args,
             **kwargs) -> HttpResponseRedirect:
        """Handles the POST requests."""
        obj = self.get_object()
        post = self.request.POST.dict()
        utils.strip_post(post)
        form = self.make_form_from_post(post)
        if not form.is_valid():
            return stored_post.error_redirect(
                self.request, self.get_error_url(), post)
        if obj is None:
            obj = self._model()
            self._set_object(obj)
        self.fill_model_from_form(obj, form)
        if isinstance(obj, DirtyFieldsMixin)\
                and not obj.is_dirty(check_relationship=True):
            message = self.get_not_modified_message()
        else:
            obj.save()
            message = self.get_success_message()
        messages.success(self.request, message)
        return redirect(str(UrlBuilder(self.get_success_url())
                            .query(r=self.request.GET.get("r"))))

    def get_form_class(self) -> Type[forms.Form]:
        """Returns the form class."""
        if self.form_class is None:
            raise AttributeError("Please defined the form_class property.")
        return self.form_class

    @property
    def _model(self):
        if self.model is None:
            raise AttributeError("Please defined the model property.")
        return self.model

    def _set_object(self, obj: Model) -> None:
        """Sets the current object that we are operating."""
        self._object = obj
        self._is_object_requested = True

    def _get_object(self) -> Optional[Model]:
        """Returns the current object that we are operating and cached."""
        if not self._is_object_requested:
            self._object = self.get_object()
            self._is_object_requested = True
        return self._object

    def get_template_name(self) -> str:
        """Returns the name of the template."""
        if self.template_name is not None:
            return self.template_name
        if self.model is not None:
            app_name = self.request.resolver_match.app_name
            model_name = self.model.__name__.lower()
            return F"{app_name}/{model_name}_form.html"
        raise AttributeError(
            "Please either define the template_name or the model property.")

    def make_form_from_post(self, post: Dict[str, str]) -> forms.Form:
        """Creates and returns the form from the POST data."""
        return self.get_form_class()(post)

    def make_form_from_model(self, obj: Model) -> forms.Form:
        """Creates and returns the form from a data model."""
        form_class = self.get_form_class()
        return form_class({x: getattr(obj, x, None)
                           for x in form_class.base_fields})

    def fill_model_from_form(self, obj: Model, form: forms.Form) -> None:
        """Fills in the data model from the form."""
        for name in form.fields:
            setattr(obj, name, form[name].value())

    def get_success_url(self) -> str:
        """Returns the URL on success."""
        if self.success_url is not None:
            return self.success_url
        obj = self._get_object()
        get_absolute_url = getattr(obj, "get_absolute_url", None)
        if get_absolute_url is not None:
            return get_absolute_url()
        raise AttributeError(
            "Please define either the success_url property,"
            " the get_absolute_url method on the data model,"
            " or the get_success_url method.")

    def get_error_url(self) -> str:
        """Returns the URL on error"""
        if self.error_url is not None:
            return self.error_url
        return self.request.get_full_path()

    def get_not_modified_message(self) -> str:
        """Returns the message when the data was not modified."""
        return self.not_modified_message

    def get_success_message(self) -> str:
        """Returns the success message."""
        return self.success_message

    def get_object(self) -> Optional[Model]:
        """Finds and returns the current object, or None on a create form."""
        if "pk" in self.kwargs:
            pk = self.kwargs["pk"]
            try:
                return self._model.objects.get(pk=pk)
            except self._model.DoesNotExist:
                raise Http404
        return None


class DeleteView(SuccessMessageMixin, CoreDeleteView):
    """The delete form view, with SuccessMessageMixin."""

    def delete(self, request, *args, **kwargs):
        response = super(DeleteView, self).delete(request, *args, **kwargs)
        messages.success(request, self.get_success_message({}))
        return response


@require_POST
def logout(request: HttpRequest) -> HttpResponseRedirect:
    """The view to log out a user.

    Args:
        request: The request.

    Returns:
        The redirect response.
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
        return self.kwargs["user"]


@method_decorator(login_required, name="dispatch")
class UserFormView(FormView):
    """The form to create or update a user."""
    model = User
    form_class = UserForm
    not_modified_message = gettext_noop("This user account was not changed.")
    success_message = gettext_noop("This user account was saved successfully.")

    def make_form_from_post(self, post: Dict[str, str]) -> UserForm:
        """Creates and returns the form from the POST data."""
        form = UserForm(post)
        form.user = self.get_object()
        form.current_user = self.request.user
        return form

    def make_form_from_model(self, obj: User) -> UserForm:
        """Creates and returns the form from a data model."""
        form = UserForm({
            "login_id": obj.login_id,
            "name": obj.name,
            "is_disabled": obj.is_disabled,
        })
        form.user = self.get_object()
        form.current_user = self.request.user
        return form

    def fill_model_from_form(self, obj: User, form: UserForm) -> None:
        """Fills in the data model from the form."""
        obj.login_id = form["login_id"].value()
        if form["password"].value() is not None:
            obj.set_digest_password(
                form["login_id"].value(), form["password"].value())
        obj.name = form["name"].value()
        obj.is_disabled = form["is_disabled"].value()
        obj.current_user = self.request.user

    def get_object(self) -> Optional[Model]:
        """Returns the current object, or None on a create form."""
        if "user" in self.kwargs:
            return self.kwargs["user"]
        return None


@require_POST
@login_required
def user_delete(request: HttpRequest, user: User) -> HttpResponseRedirect:
    """The view to delete an user.

    Args:
        request: The request.
        user: The user.

    Returns:
        The response.
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


@method_decorator(login_required, name="dispatch")
class MyAccountFormView(UserFormView):
    """The form to update the information of the currently logged-in user."""
    not_modified_message = gettext_noop("Your user account was not changed.")
    success_message = gettext_noop("Your user account was saved successfully.")

    def fill_model_from_form(self, obj: User, form: UserForm) -> None:
        """Fills in the data model from the form."""
        obj.login_id = form["login_id"].value()
        if form["password"].value() is not None:
            obj.set_digest_password(
                form["login_id"].value(), form["password"].value())
        obj.name = form["name"].value()
        obj.current_user = self.request.user

    def get_success_url(self) -> str:
        """Returns the URL on success."""
        return reverse("mia_core:my-account")

    def get_object(self) -> Optional[Model]:
        """Finds and returns the current object, or None on a create form."""
        return self.request.user


def api_users_exists(request: HttpRequest, login_id: str) -> JsonResponse:
    """The view to check whether a user with a log in ID exists.

    Args:
        request: The request.
        login_id: The log in ID.

    Returns:
        The response.
    """
    try:
        User.objects.get(login_id=login_id)
    except User.DoesNotExist:
        return JsonResponse(False, safe=False)
    return JsonResponse(True, safe=False)
