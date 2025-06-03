#!/usr/local/autopkg/python
# This Python file uses the following encoding: utf-8

# Recipe Robot
# Copyright 2015-2020 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
test_facts.py

Unit tests for facts-related functions.
"""

from __future__ import absolute_import

import unittest
from recipe_robot_lib.facts import *


class TestFacts(unittest.TestCase):
    """Tests for the Facts class."""

    def setUp(self):
        self.facts = Facts()

    def test_init(self):
        self.assertTrue(isinstance(self.facts, Facts))

    def test_init_contents(self):
        init_keys = (
            "complete",
            "errors",
            "icons",
            "information",
            "recipes",
            "reminders",
            "warnings",
        )
        for k in init_keys:
            self.assertIn(k, self.facts)

    def test_add_error(self):
        self.facts["errors"].append("This is a test error.")
        self.assertEqual(len(self.facts["errors"]), 1)

    def test_add_warning(self):
        self.facts["warnings"].append("This is a test warning.")
        self.assertEqual(len(self.facts["warnings"]), 1)

    def test_add_reminder(self):
        self.facts["reminders"].append("This is a test reminder.")
        self.assertEqual(len(self.facts["reminders"]), 1)

    def test_app_store(self):
        self.facts["is_from_app_store"] = False
        self.assertFalse(self.facts["is_from_app_store"])
        self.facts["is_from_app_store"] = True
        self.assertTrue(self.facts["is_from_app_store"])


class TestNotifyingList(unittest.TestCase):
    """Tests for the NotifyingList class."""

    def setUp(self):
        self.notifyinglist = NotifyingList("warning", ["bar", "baz"])

    def test_init(self):
        self.assertTrue(isinstance(self.notifyinglist, NotifyingList))

    def test_set(self):
        self.notifyinglist = NotifyingList("warning", ["bar", "baz"])
        self.notifyinglist[0] = "foo"
        self.assertEqual(self.notifyinglist[0], "foo")
        self.assertEqual(self.notifyinglist[1], "baz")

    def test_insert(self):
        self.notifyinglist = NotifyingList("warning", ["foo", "baz"])
        self.notifyinglist.insert(1, "bar")
        self.assertEqual(self.notifyinglist[0], "foo")
        self.assertEqual(self.notifyinglist[1], "bar")
        self.assertEqual(self.notifyinglist[2], "baz")


class TestNoisyNotifyingList(unittest.TestCase):
    """Tests for the NoisyNotifyingList class."""

    def setUp(self):
        self.noisynotifyinglist = NoisyNotifyingList("warning")

    def test_init(self):
        self.assertTrue(isinstance(self.noisynotifyinglist, NoisyNotifyingList))

    def test_append_warning(self):
        self.noisynotifyinglist = NoisyNotifyingList("warning")
        self.noisynotifyinglist.append("This is a test warning.")
        self.assertEqual(self.noisynotifyinglist[0], "This is a test warning.")
        self.noisynotifyinglist.append("This is a second warning.")
        self.assertEqual(self.noisynotifyinglist[1], "This is a second warning.")

    def test_append_error(self):
        self.noisynotifyinglist = NoisyNotifyingList("error")
        self.noisynotifyinglist.append("This is a test error.")
        self.assertEqual(self.noisynotifyinglist[0], "This is a test error.")
        self.noisynotifyinglist.append("This is a second error.")
        self.assertEqual(self.noisynotifyinglist[1], "This is a second error.")


class TestNotifyingString(unittest.TestCase):
    """Tests for the NotifyingString class."""

    def setUp(self):
        self.notifyingstring = NotifyingString("warning", "Test string.")

    def test_init(self):
        self.assertTrue(isinstance(self.notifyingstring, NotifyingString))


class TestNotifyingBool(unittest.TestCase):
    """Tests for the NotifyingBool class."""

    def setUp(self):
        self.notifyingbool = NotifyingBool("warning", True)

    def test_init(self):
        self.assertTrue(self.notifyingbool)
        self.assertTrue(isinstance(self.notifyingbool, bool))

    def test_false(self):
        self.notifyingbool = NotifyingBool("warning", False)
        self.assertFalse(self.notifyingbool)


if __name__ == "__main__":
    unittest.main()
