# The accounting application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/9/1

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

"""The command to populate the database with the accounts.

"""
import os
import re
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, CommandParser, CommandError, \
    call_command
from django.utils import timezone
from opencc import OpenCC


class Command(BaseCommand):
    """Populates the database with sample accounting data."""
    help = "Fills the database with the accounting accounts."

    def __init__(self):
        super().__init__()
        self._cc: OpenCC = OpenCC("tw2sp")
        self._now: str = timezone.localtime().strftime("%Y-%m-%d %H:%M%z")

    def add_arguments(self, parser):
        """Adds command line arguments to the parser.

        Args:
            parser (CommandParser): The command line argument parser.
        """
        parser.add_argument("proj_dir", nargs="+",
                            help="The domain, either django or djangojs")
        parser.add_argument("--domain", "-d", action="append",
                            choices=["django", "djangojs"], required=True,
                            help="The domain, either django or djangojs")

    def handle(self, *args, **options):
        """Runs the command.

        Args:
            *args (list[str]): The command line arguments.
            **options (dict[str,str]): The command line switches.
        """
        locale_dirs = [os.path.join(settings.BASE_DIR, x, "locale")
                       for x in options["proj_dir"]]
        missing = [x for x in locale_dirs if not os.path.isdir(x)]
        if len(missing) > 0:
            error = "Directories not exist: " + ", ".join(missing)
            raise CommandError(error, returncode=1)
        domains = [x for x in ["django", "djangojs"] if x in options["domain"]]
        for locale_dir in locale_dirs:
            for domain in domains:
                self._handle_po(locale_dir, domain)
        call_command("compilemessages")

    def _handle_po(self, locale_dir: str, domain: str) -> None:
        """Updates a PO file in a specific directory

        Args:
            locale_dir: the locale directory that contains the PO file
            domain: The domain, either django or djangojs.
        """
        zh_hant = os.path.join(
            locale_dir, "zh_Hant", "LC_MESSAGES", F"{domain}.po")
        zh_hans = os.path.join(
            locale_dir, "zh_Hans", "LC_MESSAGES", F"{domain}.po")
        self._update_rev_date(zh_hant)
        self._convert_chinese(zh_hant, zh_hans)

    def _update_rev_date(self, file: str) -> None:
        """Updates the revision date of the PO file.

        Args:
            file: the PO file as its full path.
        """
        size = Path(file).stat().st_size
        with open(file, "r+") as f:
            content = f.read(size)
            content = re.sub("\n\"PO-Revision-Date: [^\n]*\"\n",
                             F"\n\"PO-Revision-Date: {self._now}\\\\n\"\n",
                             content)
            f.seek(0)
            f.write(content)

    def _convert_chinese(self, zh_hant: str, zh_hans: str) -> None:
        """Creates the Simplified Chinese PO file from the Traditional
        Chinese PO file.

        Args:
            zh_hant: the Traditional Chinese PO file as its full path.
            zh_hans: the Simplified Chinese PO file as its full path.
        """
        size = Path(zh_hant).stat().st_size
        with open(zh_hant, "r") as f:
            content = f.read(size)
        content = self._cc.convert(content)
        content = re.sub("^# Traditional Chinese PO file for the ",
                         "# Simplified Chinese PO file for the ", content)
        content = re.sub("\n\"PO-Revision-Date: [^\n]*\"\n",
                         F"\n\"PO-Revision-Date: {self._now}\\\\n\"\n",
                         content)
        content = re.sub("\n\"Language-Team: Traditional Chinese",
                         "\n\"Language-Team: Simplified Chinese", content)
        content = re.sub("\n\"Language: [^\n]*\"\n",
                         "\n\"Language: Simplified Chinese\\\\n\"\n",
                         content)
        with open(zh_hans, "w") as f:
            f.write(content)
