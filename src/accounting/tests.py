# The accounting application of the Mia project.
#   by imacat <imacat@mail.imacat.idv.tw>, 2020/8/2

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

"""The test cases of the accounting application.

"""
from django.test import TestCase

from .forms import TransactionForm


class SortTransactionPostTestCase(TestCase):
    """Tests the sort_post_txn_records() utility."""

    def test_sort(self):
        """Tests the sort_post_txn_records() utility."""
        post = {
            "date": "2020-07-15",
            "notes": "",
            "debit-2-account": "4144",
            "debit-2-ord": "4",
            "debit-2-summary": "",
            "debit-2-amount": "262",
            "debit-3-id": "714703431",
            "debit-3-account": "2715",
            "debit-3-ord": "4",
            "debit-3-summary": "lunch",
            "debit-3-amount": "477",
            "debit-16-id": "541574719",
            "debit-16-account": "6634",
            "debit-16-ord": "2",
            "debit-16-summary": "dinner",
            "debit-16-amount": "525",
            "credit-7-id": "747725334",
            "credit-7-account": "1211",
            "credit-7-ord": "3",
            "credit-7-summary": "",
            "credit-7-amount": "667",
        }
        TransactionForm._sort_post_txn_records(post)
        self.assertEqual(post.get("date"), "2020-07-15")
        self.assertEqual(post.get("notes"), "")
        self.assertEqual(post.get("debit-1-ord"), "1")
        self.assertEqual(post.get("debit-1-id"), "541574719")
        self.assertEqual(post.get("debit-1-account"), "6634")
        self.assertEqual(post.get("debit-1-summary"), "dinner")
        self.assertEqual(post.get("debit-1-amount"), "525")
        self.assertEqual(post.get("debit-2-ord"), "2")
        self.assertEqual(post.get("debit-2-account"), "4144")
        self.assertEqual(post.get("debit-2-summary"), "")
        self.assertEqual(post.get("debit-2-amount"), "262")
        self.assertEqual(post.get("debit-3-ord"), "3")
        self.assertEqual(post.get("debit-3-id"), "714703431")
        self.assertEqual(post.get("debit-3-account"), "2715")
        self.assertEqual(post.get("debit-3-summary"), "lunch")
        self.assertEqual(post.get("debit-3-amount"), "477")
        self.assertEqual(post.get("credit-1-ord"), "1")
        self.assertEqual(post.get("credit-1-id"), "747725334")
        self.assertEqual(post.get("credit-1-account"), "1211")
        self.assertEqual(post.get("credit-1-summary"), "")
        self.assertEqual(post.get("credit-1-amount"), "667")
