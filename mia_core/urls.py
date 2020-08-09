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
from django.urls import path

from . import views

app_name = "mia_core"
urlpatterns = [
    # TODO: To be done.
    path("users", views.todo, name="users"),
    # TODO: To be done.
    path("users/create", views.todo, name="users.create"),
    # TODO: To be done.
    path("users/store", views.todo, name="users.store"),
    # TODO: To be done.
    path("users/<str:login_id>", views.todo, name="users.detail"),
    # TODO: To be done.
    path("users/<str:login_id>/edit", views.todo, name="users.edit"),
    # TODO: To be done.
    path("users/<str:login_id>/update", views.todo, name="users.update"),
    # TODO: To be done.
    path("users/<str:login_id>/delete", views.todo, name="users.delete"),
    # TODO: To be done.
    path("api/users/<str:login_id>/exists", views.todo,
         name="api.users.exists"),
    # TODO: To be done.
    path("my-account", views.todo, name="my-account"),
    # TODO: To be done.
    path("my-account/edit", views.todo, name="my-account.edit"),
    # TODO: To be done.
    path("my-account/update", views.todo, name="my-account.update"),
]
