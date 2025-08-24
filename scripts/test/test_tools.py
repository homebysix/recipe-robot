#!/usr/local/autopkg/python

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
test_tools.py

Unit tests for tools-related functions.
"""


import unittest
import tempfile
import os
from unittest.mock import patch

from scripts.recipe_robot_lib import tools
from scripts.recipe_robot_lib.facts import Facts
from scripts.recipe_robot_lib.tools import strip_dev_suffix


class TestTools(unittest.TestCase):
    """Tests for tools.py."""

    def test_strip_dev_suffix_with_none(self):
        """Test that None input returns None."""
        result = strip_dev_suffix(None)
        self.assertIsNone(result)

    def test_strip_dev_suffix_with_empty_string(self):
        """Test that empty string input returns empty string."""
        result = strip_dev_suffix("")
        self.assertEqual(result, "")

    def test_strip_dev_suffix_with_whitespace_only(self):
        """Test that whitespace-only string returns empty string after cleaning."""
        result = strip_dev_suffix("   ")
        self.assertEqual(result, "")

    def test_strip_dev_suffix_no_suffix(self):
        """Test that developer names without suffixes are returned unchanged."""
        test_cases = [
            "Apple",
            "Microsoft",
            "Adobe Systems",
            "Google",
            "Mozilla Foundation",
        ]
        for dev_name in test_cases:
            with self.subTest(dev_name=dev_name):
                result = strip_dev_suffix(dev_name)
                self.assertEqual(result, dev_name)

    def test_strip_dev_suffix_with_inc(self):
        """Test stripping 'Inc' and 'Inc.' suffixes."""
        test_cases = [
            ("Apple Inc", "Apple"),
            ("Apple Inc.", "Apple"),
            ("Microsoft Inc", "Microsoft"),
            ("Adobe Systems Inc.", "Adobe Systems"),
            ("Apple, Inc.", "Apple"),
            ("Microsoft, Inc", "Microsoft"),
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = strip_dev_suffix(input_name)
                self.assertEqual(result, expected)

    def test_strip_dev_suffix_with_corp(self):
        """Test stripping 'Corp' and 'Corporation' suffixes."""
        test_cases = [
            ("Apple Corp", "Apple"),
            ("Microsoft Corp.", "Microsoft"),
            ("Adobe Corporation", "Adobe"),
            ("Google Corporation.", "Google"),
            ("Apple, Corp", "Apple"),
            ("Microsoft, Corporation", "Microsoft"),
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = strip_dev_suffix(input_name)
                self.assertEqual(result, expected)

    def test_strip_dev_suffix_with_llc(self):
        """Test stripping 'LLC' and 'L.L.C' suffixes."""
        test_cases = [
            ("Apple LLC", "Apple"),
            ("Microsoft LLC.", "Microsoft"),
            ("Adobe L.L.C", "Adobe"),
            ("Google L.L.C.", "Google"),
            ("Apple, LLC", "Apple"),
            ("Microsoft, L.L.C", "Microsoft"),
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = strip_dev_suffix(input_name)
                self.assertEqual(result, expected)

    def test_strip_dev_suffix_with_ltd(self):
        """Test stripping 'Ltd' and 'Limited' suffixes."""
        test_cases = [
            ("Apple Ltd", "Apple"),
            ("Microsoft Ltd.", "Microsoft"),
            ("Adobe Limited", "Adobe"),
            ("Google Limited.", "Google"),
            ("Apple, Ltd", "Apple"),
            ("Microsoft, Limited", "Microsoft"),
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = strip_dev_suffix(input_name)
                self.assertEqual(result, expected)

    def test_strip_dev_suffix_with_pvt_ltd(self):
        """Test stripping 'Pvt Ltd' and 'Pvt. Ltd' suffixes."""
        test_cases = [
            ("Apple Pvt Ltd", "Apple"),
            ("Microsoft Pvt. Ltd", "Microsoft"),
            ("Adobe Pvt Ltd.", "Adobe"),
            ("Google Pvt. Ltd.", "Google"),
            ("Apple, Pvt Ltd", "Apple"),
            ("Microsoft, Pvt. Ltd", "Microsoft"),
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = strip_dev_suffix(input_name)
                self.assertEqual(result, expected)

    def test_strip_dev_suffix_with_pty_ltd(self):
        """Test stripping 'Pty Ltd' and 'Pty. Ltd' suffixes."""
        test_cases = [
            ("Apple Pty Ltd", "Apple"),
            ("Microsoft Pty. Ltd", "Microsoft"),
            ("Adobe Pty Ltd.", "Adobe"),
            ("Google Pty. Ltd.", "Google"),
            ("Apple, Pty Ltd", "Apple"),
            ("Microsoft, Pty. Ltd", "Microsoft"),
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = strip_dev_suffix(input_name)
                self.assertEqual(result, expected)

    def test_strip_dev_suffix_with_gmbh(self):
        """Test stripping 'GmbH' suffix."""
        test_cases = [
            ("Apple GmbH", "Apple"),
            ("Microsoft GmbH.", "Microsoft"),
            ("Adobe, GmbH", "Adobe"),
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = strip_dev_suffix(input_name)
                self.assertEqual(result, expected)

    def test_strip_dev_suffix_with_european_suffixes(self):
        """Test stripping European corporate suffixes."""
        test_cases = [
            ("Apple SA", "Apple"),
            ("Microsoft S.A R.L", "Microsoft"),
            ("Adobe SA RL", "Adobe"),
            ("Google SARL", "Google"),
            ("Oracle SRL", "Oracle"),
            ("Apple, SA", "Apple"),
            ("Microsoft, S.A R.L", "Microsoft"),
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = strip_dev_suffix(input_name)
                self.assertEqual(result, expected)

    def test_strip_dev_suffix_with_nordic_suffixes(self):
        """Test stripping Nordic corporate suffixes."""
        test_cases = [
            ("Apple AB", "Apple"),
            ("Microsoft OY", "Microsoft"),
            ("Adobe OY/Ltd", "Adobe"),
            ("Apple, AB", "Apple"),
            ("Microsoft, OY", "Microsoft"),
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = strip_dev_suffix(input_name)
                self.assertEqual(result, expected)

    def test_strip_dev_suffix_case_insensitive(self):
        """Test that suffix matching is case insensitive."""
        test_cases = [
            ("Apple INC", "Apple"),
            ("Microsoft inc", "Microsoft"),
            ("Adobe CORPORATION", "Adobe"),
            ("Google llc", "Google"),
            ("Oracle LTD", "Oracle"),
            ("Apple GMBH", "Apple"),
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = strip_dev_suffix(input_name)
                self.assertEqual(result, expected)

    def test_strip_dev_suffix_with_extra_spaces(self):
        """Test that extra spaces are handled correctly."""
        test_cases = [
            ("Apple Inc  ", "Apple"),
            ("Microsoft Corp   .", "Microsoft"),
            ("Adobe   LLC", "Adobe"),
            ("Google  Ltd  ", "Google"),
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = strip_dev_suffix(input_name)
                self.assertEqual(result, expected)

    def test_strip_dev_suffix_suffix_as_part_of_name(self):
        """Test that suffixes that are part of the actual name are not stripped."""
        test_cases = [
            ("Incorporated Software", "Incorporated Software"),
            ("Limited Edition Games", "Limited Edition Games"),
            ("Corporation Street Studios", "Corporation Street Studios"),
            ("IncredibleSoft", "IncredibleSoft"),
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = strip_dev_suffix(input_name)
                self.assertEqual(result, expected)

    def test_strip_dev_suffix_only_first_match(self):
        """Test that only the first matching suffix is stripped."""
        test_cases = [
            ("Inc Corp Inc", "Inc Corp"),
            ("Limited Corp Ltd", "Limited Corp"),
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = strip_dev_suffix(input_name)
                self.assertEqual(result, expected)

    def test_strip_dev_suffix_real_world_examples(self):
        """Test with real-world company names."""
        test_cases = [
            ("Adobe Systems Incorporated", "Adobe Systems"),
            ("Microsoft Corporation", "Microsoft"),
            ("Apple Inc.", "Apple"),
            ("Google LLC", "Google"),
            ("Oracle Corporation", "Oracle"),
            ("SAP SE", "SAP SE"),  # SE is not in our suffix list
            ("Spotify AB", "Spotify"),
            ("Nokia Corporation", "Nokia"),
            ("Atlassian Pty Ltd", "Atlassian"),
            ("JetBrains s.r.o.", "JetBrains"),  # s.r.o. should match sro
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = strip_dev_suffix(input_name)
                self.assertEqual(result, expected)

    def test_normalize_keyword_basic(self):
        """Test normalize_keyword function."""
        test_cases = [
            ("Test Keyword", "testkeyword"),
            ("with-dashes", "withdashes"),
            ("Multiple   Spaces", "multiplespaces"),
            ("MixedCase", "mixedcase"),
            ("", ""),
        ]

        for input_keyword, expected in test_cases:
            with self.subTest(input_keyword=input_keyword):
                result = tools.normalize_keyword(input_keyword)
                self.assertEqual(result, expected)

    @patch("scripts.recipe_robot_lib.tools.get_exitcode_stdout_stderr")
    def test_get_user_defaults_failure(self, mock_exec):
        """Test get_user_defaults when defaults command fails."""
        # Mock failed defaults read
        mock_exec.return_value = (1, "", "Error message")

        result = tools.get_user_defaults()

        # Should return current state on failure (function doesn't return empty dict)
        self.assertIsInstance(result, dict)

    def test_get_bundle_name_info_no_bundles(self):
        """Test get_bundle_name_info when no recognized bundles exist."""
        # Create Facts object with empty inspections
        facts = Facts()
        facts["inspections"] = {}

        bundle_type, bundle_name_key = tools.get_bundle_name_info(facts)

        # Should return None values when no bundles found
        self.assertIsNone(bundle_type)
        self.assertIsNone(bundle_name_key)

    def test_get_table_row_empty_input(self):
        """Test get_table_row with empty inputs."""
        result = tools.get_table_row("", "")

        self.assertIsInstance(result, str)


class TestToolsFilesystemFunctions(unittest.TestCase):
    """Test filesystem-related functions in tools module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("scripts.recipe_robot_lib.tools.robo_print")
    def test_print_welcome_text(self, mock_print):
        """Test print_welcome_text function."""
        tools.print_welcome_text()

        # Should call robo_print
        self.assertTrue(mock_print.called)

    @patch("scripts.recipe_robot_lib.tools.robo_print")
    def test_print_death_text(self, mock_print):
        """Test print_death_text function."""
        tools.print_death_text()

        # Should call robo_print
        self.assertTrue(mock_print.called)

    def test_reset_term_colors(self):
        """Test reset_term_colors function."""
        # Function should not raise an exception
        try:
            tools.reset_term_colors()
        except Exception as e:
            self.fail(f"reset_term_colors raised an exception: {e}")


class TestToolsSearchFunctions(unittest.TestCase):
    """Test search-related functions in tools module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.temp_dir, "test_cache.json")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
