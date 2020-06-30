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

"""The utilities of the accounting application.

"""


class PeriodParser:
    """The period parser.

    Attributes:
        start: The start of the period.
        end: The end of the period.
    """
    start = None
    end = None

    def __init__(self, period_spec):
        """Constructs a new period parser.

        Args:
            period_spec (str): The period specification.
        """
        self.start = period_spec + "-01"
        self.end = period_spec + "-30"
