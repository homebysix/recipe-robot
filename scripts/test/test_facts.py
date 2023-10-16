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

from nose.tools import *  # pylint: disable=unused-wildcard-import, wildcard-import
from recipe_robot_lib.facts import *


class TestFacts:
    """Tests for the Facts class."""

    def __init__(self):
        self.facts = Facts()

    def test_init(self):
        assert_true(isinstance(self.facts, Facts))

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
            assert_in(k, self.facts)

    def test_add_error(self):
        self.facts["errors"].append("This is a test error.")
        assert_equal(len(self.facts["errors"]), 1)

    def test_add_warning(self):
        self.facts["warnings"].append("This is a test warning.")
        assert_equal(len(self.facts["warnings"]), 1)

    def test_add_reminder(self):
        self.facts["reminders"].append("This is a test reminder.")
        assert_equal(len(self.facts["reminders"]), 1)

    def test_app_store(self):
        self.facts["is_from_app_store"] = False
        assert_false(self.facts["is_from_app_store"])
        self.facts["is_from_app_store"] = True
        assert_true(self.facts["is_from_app_store"])


class TestNotifyingList:
    """Tests for the NotifyingList class."""

    def __init__(self):
        self.notifyinglist = NotifyingList("warning", ["bar", "baz"])

    def test_init(self):
        assert_true(isinstance(self.notifyinglist, NotifyingList))

    def test_set(self):
        self.notifyinglist = NotifyingList("warning", ["bar", "baz"])
        self.notifyinglist[0] = "foo"
        assert_equal(self.notifyinglist[0], "foo")
        assert_equal(self.notifyinglist[1], "baz")

    def test_insert(self):
        self.notifyinglist = NotifyingList("warning", ["foo", "baz"])
        self.notifyinglist.insert(1, "bar")
        assert_equal(self.notifyinglist[0], "foo")
        assert_equal(self.notifyinglist[1], "bar")
        assert_equal(self.notifyinglist[2], "baz")


class TestNoisyNotifyingList:
    """Tests for the NoisyNotifyingList class."""

    def __init__(self):
        self.noisynotifyinglist = NoisyNotifyingList("warning")

    def test_init(self):
        assert_true(isinstance(self.noisynotifyinglist, NoisyNotifyingList))

    def test_append_warning(self):
        self.noisynotifyinglist = NoisyNotifyingList("warning")
        self.noisynotifyinglist.append("This is a test warning.")
        assert_equal(self.noisynotifyinglist[0], "This is a test warning.")
        self.noisynotifyinglist.append("This is a second warning.")
        assert_equal(self.noisynotifyinglist[1], "This is a second warning.")

    def test_append_error(self):
        self.noisynotifyinglist = NoisyNotifyingList("error")
        self.noisynotifyinglist.append("This is a test error.")
        assert_equal(self.noisynotifyinglist[0], "This is a test error.")
        self.noisynotifyinglist.append("This is a second error.")
        assert_equal(self.noisynotifyinglist[1], "This is a second error.")


class TestNotifyingString:
    """Tests for the NotifyingString class."""

    def __init__(self):
        self.notifyingstring = NotifyingString("warning", "Test string.")

    def test_init(self):
        assert_true(isinstance(self.notifyingstring, NotifyingString))


class TestNotifyingBool:
    """Tests for the NotifyingBool class."""

    def __init__(self):
        self.notifyingbool = NotifyingBool("warning", True)

    def test_init(self):
        assert_true(self.notifyingbool)
        assert_true(isinstance(self.notifyingbool, bool))

    def test_false(self):
        self.notifyingbool = NotifyingBool("warning", False)
        assert_false(self.notifyingbool)
