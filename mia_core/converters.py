# The core application of the Mia project.
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

"""The URL converters.

"""
from .models import User


class UserConverter:
    """The path converter for the user accounts."""
    regex = ".*"

    def to_python(self, value):
        try:
            return User.objects.get(login_id=value)
        except User.DoesNotExist:
            raise ValueError

    def to_url(self, value):
        return value.login_id
