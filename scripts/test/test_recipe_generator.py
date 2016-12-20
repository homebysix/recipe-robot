#!/usr/bin/python
# This Python file uses the following encoding: utf-8

# Recipe Robot
# Copyright 2015-2016 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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
test_recipe_generator.py

Unit tests for recipe_generator.
"""


from nose.tools import *  # pylint: disable=unused-wildcard-import, wildcard-import

from recipe_robot_lib import recipe_generator, facts
from recipe_robot_lib.tools import (SUPPORTED_IMAGE_FORMATS,
                                    SUPPORTED_ARCHIVE_FORMATS,
                                    SUPPORTED_INSTALL_FORMATS)


class TestRecipeGenerator(object):
    """Tests for the recipe_generator functions."""

    def test_get_code_signature_verifier_reqs(self):
        """Ensure processor is properly configured."""
        test_facts = facts.Facts()
        req = "TEST"
        test_facts["codesign_reqs"] = req
        input_path = "/path"
        codesigverifier = recipe_generator.get_code_signature_verifier(
            input_path, test_facts)
        assert_equal(codesigverifier.input_path, input_path)
        assert_equal(codesigverifier.requirement, req)
        assert_is_none(codesigverifier.expected_authority_names)

    def test_get_code_signature_verifier_expect_auth(self):
        """Ensure processor is properly configured."""
        test_facts = facts.Facts()
        req = ["TEST1", "TEST2"]
        test_facts["codesign_authorities"] = req
        input_path = "/path"
        codesigverifier = recipe_generator.get_code_signature_verifier(
            input_path, test_facts)
        assert_equal(codesigverifier.input_path, input_path)
        assert_is_none(codesigverifier.requirement)
        assert_sequence_equal(codesigverifier.expected_authority_names, req)

    def test_needs_versioner(self):
        for format in SUPPORTED_IMAGE_FORMATS + SUPPORTED_ARCHIVE_FORMATS:
            true_facts = {"download_format": format,
                           "sparkle_provides_version": False}
            assert_true(recipe_generator.needs_versioner(true_facts))
        for format in SUPPORTED_INSTALL_FORMATS:
            install_facts = {"download_format": format,
                           "sparkle_provides_version": False}
            assert_false(recipe_generator.needs_versioner(install_facts))

    def test_is_dynamic_url_source(self):
        for source in ("sparkle_feed", "github_repo", "sourceforge_id"):
            true_facts = {source: None}
            assert_true(recipe_generator.is_dynamic_url_source(true_facts))
        for source in ("download_url", "Unexpected"):
            false_facts = {source: None}
            assert_false(recipe_generator.is_dynamic_url_source(false_facts))
