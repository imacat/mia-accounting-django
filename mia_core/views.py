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
from typing import Dict, Type, Optional, Any

from dirtyfields import DirtyFieldsMixin
from django import forms
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import Model
from django.http import HttpResponse, HttpRequest, \
    HttpResponseRedirect, Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import DeleteView as CoreDeleteView, \
    RedirectView as CoreRedirectView
from django.views.generic.base import View

from . import stored_post, utils
from .models import StampedModel
from .utils import UrlBuilder


class RedirectView(CoreRedirectView):
    """The redirect view, with current_app at the current namespace."""

    def get_redirect_url(self, *args, **kwargs):
        url = reverse(self.pattern_name, kwargs=kwargs,
                      current_app=self.request.resolver_match.namespace)
        if self.query_string and self.request.META["QUERY_STRING"] != "":
            url = url + "?" + self.request.META["QUERY_STRING"]
        return url


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
        self.object: Optional[Model] = None

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """The view to store an accounting transaction."""
        self.object = self.get_object()
        if self.request.method == "POST":
            return self.post(request, *args, **kwargs)
        else:
            return self.get(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handles the GET requests."""
        return render(self.request, self.get_template_name(),
                      self.get_context_data(**kwargs))

    def post(self, request: HttpRequest, *args,
             **kwargs) -> HttpResponseRedirect:
        """Handles the POST requests."""
        form = self.get_form(**kwargs)
        if not form.is_valid():
            return self.form_invalid(form)
        return self.form_valid(form)

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

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Returns the context data for the template."""
        return {self.context_object_name: self.get_form()}

    def get_form(self, **kwargs) -> forms.Form:
        """Returns the form for the template."""
        if self.request.method == "POST":
            post = self.request.POST.dict()
            utils.strip_post(post)
            return self.make_form_from_post(post)
        else:
            previous_post = stored_post.get_previous_post(self.request)
            if previous_post is not None:
                return self.make_form_from_post(previous_post)
            if self.object is not None:
                return self.make_form_from_model(self.object)
            return self.get_form_class()()

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
        if isinstance(obj, StampedModel):
            obj.current_user = self.request.user

    def form_invalid(self, form: forms.Form) -> HttpResponseRedirect:
        """Handles the action when the POST form is invalid."""
        return stored_post.error_redirect(
            self.request, self.get_error_url(), form.data)

    def form_valid(self, form: forms.Form) -> HttpResponseRedirect:
        """Handles the action when the POST form is valid."""
        if self.object is None:
            self.object = self._model()
        self.fill_model_from_form(self.object, form)
        if isinstance(self.object, DirtyFieldsMixin)\
                and not self.object.is_dirty(check_relationship=True):
            message = self.get_not_modified_message(form.cleaned_data)
        else:
            with transaction.atomic():
                self.object.save()
            message = self.get_success_message(form.cleaned_data)
        messages.success(self.request, message)
        return redirect(str(UrlBuilder(self.get_success_url())
                            .query(r=self.request.GET.get("r"))))

    def get_success_url(self) -> str:
        """Returns the URL on success."""
        if self.success_url is not None:
            return self.success_url
        get_absolute_url = getattr(self.object, "get_absolute_url", None)
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

    def get_not_modified_message(self, cleaned_data: Dict[str, str]) -> str:
        """Returns the message when the data was not modified.

        Args:
            cleaned_data: The cleaned data of the form.

        Returns:
            The message when the data was not modified.
        """
        return self.not_modified_message % cleaned_data

    def get_success_message(self, cleaned_data: Dict[str, str]) -> str:
        """Returns the success message.

        Args:
            cleaned_data: The cleaned data of the form.

        Returns:
            The message when the data was not modified.
        """
        return self.success_message % cleaned_data

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
