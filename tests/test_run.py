# The accounting application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2022/12/5

#  Copyright (c) 2022 imacat.
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

"""The tests to run the accounting application.

"""
import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from secrets import token_urlsafe

from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from django.test import Client


class RunTestCase(unittest.TestCase):
    """The test case to run the accounting application."""

    def setUp(self):
        """Sets up the test.

        Returns:
            None.
        """
        test_site_path: str = str(Path(__file__).parent / "test_site")
        if test_site_path not in sys.path:
            sys.path.append(test_site_path)
        self.username: str = "admin"
        self.password: str = token_urlsafe(16)
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_site.settings")
        get_wsgi_application()
        call_command("migrate")
        os.getlogin()
        call_command("createsuperuser", interactive=False,
                     username=self.username,  email="test@example.com")
        from django.contrib.auth.models import User
        user = User.objects.get(username=self.username)
        user.set_password(self.password)
        user.save()
        call_command("accounting_accounts")
        call_command("accounting_sample")
        self.client = Client()

    def test_run(self):
        """Tests the accounting application.

        Returns:
            None.
        """
        response = self.client.get("/accounting/", follow=True)
        self.assertEqual(response.status_code, 404)
        response = self.client.post("/admin/login/",
                                    {"username": self.username,
                                     "password": self.password,
                                     "next": "/ok"})
        # 200 for errors, 302 for success.
        self.assertEqual(response.status_code, 302)
        response = self.client.get("/accounting/", follow=True)
        self.assertEqual(response.status_code, 200)

        today: str = datetime.today().strftime("%Y-%m-%d")

        response = self.client.post(
            "/accounting/transactions/expense/create?r=/ok",
            {"date": today,
             "debit-2-ord": 6,
             "debit-2-summary": "lunch",
             "debit-2-amount": 80,
             "debit-2-account": "6272",
             "debit-8-ord": 4,
             "debit-8-summary": "movies",
             "debit-8-amount": 320,
             "debit-8-account": "6273",
             "notes": "yammy"})
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(response.headers["Location"],
                            "/accounting/transactions/expense/create?r=/ok")

        response = self.client.post(
            "/accounting/transactions/income/create?r=/ok",
            {"date": today,
             "credit-3-ord": 7,
             "credit-3-summary": "withdrawal",
             "credit-3-amount": 1000,
             "credit-3-account": "1113",
             "credit-6-ord": 3,
             "credit-6-summary": "payroll",
             "credit-6-amount": 10000,
             "credit-6-account": "4611",
             "notes": "wonderful"})
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(response.headers["Location"],
                            "/accounting/transactions/income/create?r=/ok")

        response = self.client.post(
            "/accounting/transactions/transfer/create?r=/ok",
            {"date": today,
             "debit-2-ord": 6,
             "debit-2-summary": "lunch",
             "debit-2-amount": 80,
             "debit-2-account": "6272",
             "debit-8-ord": 4,
             "debit-8-summary": "movies",
             "debit-8-amount": 320,
             "debit-8-account": "6273",
             "credit-3-ord": 7,
             "credit-3-summary": "withdrawal",
             "credit-3-amount": 100,
             "credit-3-account": "1113",
             "credit-6-ord": 3,
             "credit-6-summary": "",
             "credit-6-amount": 320,
             "credit-6-account": "1111",
             "notes": "nothing"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"],
                         "/accounting/transactions/transfer/create?r=/ok")

        response = self.client.post(
            "/accounting/transactions/transfer/create?r=/ok",
            {"date": today,
             "debit-2-ord": 6,
             "debit-2-summary": "lunch",
             "debit-2-amount": 80,
             "debit-2-account": "6272",
             "debit-8-ord": 4,
             "debit-8-summary": "movies",
             "debit-8-amount": 320,
             "debit-8-account": "6273",
             "credit-3-ord": 7,
             "credit-3-summary": "withdrawal",
             "credit-3-amount": 100,
             "credit-3-account": "1113",
             "credit-6-ord": 3,
             "credit-6-summary": "",
             "credit-6-amount": 300,
             "credit-6-account": "1111",
             "notes": "nothing"})
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(response.headers["Location"],
                            "/accounting/transactions/transfer/create?r=/ok")
