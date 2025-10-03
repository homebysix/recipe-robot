#!/usr/local/autopkg/python

# Recipe Robot
# Copyright 2015-2025 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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
test_processor.py

Unit tests for processor class.
"""


import unittest
from scripts.recipe_robot_lib import processor


class TestProcessor(unittest.TestCase):
    """Tests for the AbstractProcessor subclasses."""

    def test_set_via_constructor_kwargs(self):
        """See if processor constructor correctly sets attr vals."""
        val = "/test"
        app_dmg_versioner = processor.AppDmgVersioner(dmg_path=val)
        self.assertEqual(app_dmg_versioner.dmg_path, val)

    def test_set_via_attribute(self):
        """Test that setting attribute values works."""
        val = "/test"
        app_dmg_versioner = processor.AppDmgVersioner()
        app_dmg_versioner.dmg_path = val
        self.assertEqual(app_dmg_versioner.dmg_path, val)

    def test_input_variables(self):
        """Ensure a processor gets input vars setup correctly."""
        munki_importer = processor.MunkiImporter()
        expected_variables = (
            "additional_makepkginfo_options",
            "extract_icon",
            "force_munki_repo_lib",
            "force_munkiimport",
            "metadata_additions",
            "MUNKI_PKGINFO_FILE_EXTENSION",
            "MUNKI_REPO_PLUGIN",
            "MUNKI_REPO",
            "munkiimport_appname",
            "munkiimport_pkgname",
            "MUNKILIB_DIR",
            "pkg_path",
            "pkginfo",
            "repo_subdirectory",
            "uninstaller_pkg_path",
            "version_comparison_key",
        )

        self.assertSequenceEqual(
            sorted(munki_importer._input_variables), sorted(expected_variables)
        )

    def test_empty_to_dict(self):
        """Ensure a processor's dict repr is correct with no values."""
        adv = processor.AppDmgVersioner()
        output_dict = adv.to_dict()
        test_dict = {"Processor": "AppDmgVersioner"}

        self.assertDictEqual(output_dict, test_dict)

    def test_loaded_to_dict(self):
        """Ensure a processor's dict repr is correct with values."""
        adv = processor.AppDmgVersioner(dmg_path="~/Downloads/Awesome.dmg")
        output_dict = adv.to_dict()
        test_dict = {
            "Processor": "AppDmgVersioner",
            "Arguments": {"dmg_path": "~/Downloads/Awesome.dmg"},
        }

        self.assertDictEqual(output_dict, test_dict)


if __name__ == "__main__":
    unittest.main()
