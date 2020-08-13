# The Mia core application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/8/9

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

"""The route settings of the Mia core application.

"""
from django.urls import path, register_converter
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView

from . import views, converters
from .digest_auth import login_required

register_converter(converters.UserConverter, "user")

app_name = "mia_core"
urlpatterns = [
    path("logout", views.logout, name="logout"),
    path("users", views.UserListView.as_view(), name="users"),
    path("users/create", views.UserFormView.as_view(), name="users.create"),
    path("users/<user:user>", views.UserView.as_view(), name="users.detail"),
    path("users/<user:user>/update", views.UserFormView.as_view(), name="users.update"),
    path("users/<user:user>/delete", views.user_delete, name="users.delete"),
    path("api/users/<str:login_id>/exists", views.api_users_exists,
         name="api.users.exists"),
    path("my-account", require_GET(login_required(TemplateView.as_view(
        template_name="mia_core/user_detail.html"))), name="my-account"),
    path("my-account/edit", views.my_account_form, name="my-account.edit"),
    path("my-account/update", views.my_account_store,
         name="my-account.update"),
]
