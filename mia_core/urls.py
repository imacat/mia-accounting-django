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

from . import views, converters

register_converter(converters.UserConverter, "user")

app_name = "mia_core"
urlpatterns = [
    path("users", views.UserListView.as_view(), name="users"),
    path("users/create", views.user_form, name="users.create"),
    path("users/store", views.user_store, name="users.store"),
    path("users/<user:user>", views.UserView.as_view(), name="users.detail"),
    path("users/<user:user>/edit", views.user_form, name="users.edit"),
    path("users/<user:user>/update", views.user_store, name="users.update"),
    # TODO: To be done.
    path("users/<user:user>/delete", views.todo, name="users.delete"),
    path("api/users/<str:login_id>/exists", views.api_users_exists,
         name="api.users.exists"),
    # TODO: To be done.
    path("my-account", views.todo, name="my-account"),
    # TODO: To be done.
    path("my-account/edit", views.todo, name="my-account.edit"),
    # TODO: To be done.
    path("my-account/update", views.todo, name="my-account.update"),
]
