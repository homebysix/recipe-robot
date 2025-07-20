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


"""test_recipe_generator.py.

Unit tests for recipe_generator.
"""


# pylint: disable=unused-wildcard-import, wildcard-import
from __future__ import absolute_import

import unittest
from scripts.recipe_robot_lib import facts, recipe_generator
from scripts.recipe_robot_lib.tools import (
    SUPPORTED_ARCHIVE_FORMATS,
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_INSTALL_FORMATS,
)


class TestRecipeGenerator(unittest.TestCase):
    """Tests for the recipe_generator functions."""

    def test_get_code_signature_verifier_reqs(self):
        """Ensure CodeSignatureVerifier processor codesign_reqs arg is properly
        configured."""
        test_facts = facts.Facts()
        req = "TEST"
        test_facts["codesign_reqs"] = req
        input_path = "/path"
        codesigverifier = recipe_generator.get_code_signature_verifier(
            input_path, test_facts
        )
        self.assertEqual(codesigverifier.input_path, input_path)
        self.assertEqual(codesigverifier.requirement, req)
        self.assertIsNone(codesigverifier.expected_authority_names)

    def test_get_code_signature_verifier_expect_auth(self):
        """Ensure CodeSignatureVerifier processor codesign_authorities arg is
        properly configured."""
        test_facts = facts.Facts()
        req = ["TEST1", "TEST2"]
        test_facts["codesign_authorities"] = req
        input_path = "/path"
        codesigverifier = recipe_generator.get_code_signature_verifier(
            input_path, test_facts
        )
        self.assertEqual(codesigverifier.input_path, input_path)
        self.assertIsNone(codesigverifier.requirement)
        self.assertSequenceEqual(codesigverifier.expected_authority_names, req)

    def test_needs_versioner(self):
        """Test result of needs_versioner() function."""
        for format in SUPPORTED_IMAGE_FORMATS + SUPPORTED_ARCHIVE_FORMATS:
            true_facts = {"download_format": format, "sparkle_provides_version": False}
            self.assertTrue(recipe_generator.needs_versioner(true_facts))
        for format in SUPPORTED_INSTALL_FORMATS:
            install_facts = {
                "download_format": format,
                "sparkle_provides_version": False,
            }
            self.assertFalse(recipe_generator.needs_versioner(install_facts))

    def test_needs_versioner_with_sparkle(self):
        """Test needs_versioner() when Sparkle provides version."""
        sparkle_facts = {
            "download_format": "zip",
            "sparkle_provides_version": True,
        }
        self.assertFalse(recipe_generator.needs_versioner(sparkle_facts))

    def test_get_pkgdirs_simple_path(self):
        """Test get_pkgdirs() with a simple path."""
        path = "/Applications"
        result = recipe_generator.get_pkgdirs(path)
        expected = {"": "0775", "/Applications": "0775"}
        self.assertEqual(result, expected)

    def test_get_pkgdirs_nested_path(self):
        """Test get_pkgdirs() with a nested path."""
        path = "/Applications/Utilities"
        result = recipe_generator.get_pkgdirs(path)
        expected = {"Applications": "0775", "Applications/Utilities": "0775"}
        self.assertEqual(result, expected)

    def test_get_pkgdirs_with_leading_slash(self):
        """Test get_pkgdirs() behavior with multiple slashes."""
        path = "//Applications//Utilities/"
        result = recipe_generator.get_pkgdirs(path)
        expected = {
            "Applications//Utilities": "0775",
            "Applications//Utilities/": "0775",
        }
        self.assertEqual(result, expected)

    def test_get_code_signature_verifier_no_codesign_info(self):
        """Test CodeSignatureVerifier with no codesign information."""
        test_facts = facts.Facts()
        test_facts["codesign_authorities"] = []
        input_path = "/path/to/app"
        codesigverifier = recipe_generator.get_code_signature_verifier(
            input_path, test_facts
        )
        self.assertEqual(codesigverifier.input_path, input_path)
        self.assertIsNone(codesigverifier.requirement)
        self.assertIsNone(codesigverifier.expected_authority_names)

    def test_get_code_signature_verifier_both_reqs_and_authorities(self):
        """Test CodeSignatureVerifier when both requirements and authorities exist."""
        test_facts = facts.Facts()
        test_facts["codesign_reqs"] = "TEST_REQ"
        test_facts["codesign_authorities"] = ["AUTH1", "AUTH2"]
        input_path = "/path/to/app"
        codesigverifier = recipe_generator.get_code_signature_verifier(
            input_path, test_facts
        )
        self.assertEqual(codesigverifier.input_path, input_path)
        # Requirements should take precedence over authorities
        self.assertEqual(codesigverifier.requirement, "TEST_REQ")
        self.assertIsNone(codesigverifier.expected_authority_names)

    def test_warn_about_app_store_generation(self):
        """Test warn_about_app_store_generation() function."""
        test_facts = facts.Facts()
        initial_warning_count = len(test_facts["warnings"])
        recipe_type = "munki"

        recipe_generator.warn_about_app_store_generation(test_facts, recipe_type)

        self.assertEqual(len(test_facts["warnings"]), initial_warning_count + 1)
        warning_message = test_facts["warnings"][-1]
        self.assertIn("App Store", warning_message)
        self.assertIn(recipe_type, warning_message)


if __name__ == "__main__":
    unittest.main()
