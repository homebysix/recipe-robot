#!/usr/bin/python
# This Python file uses the following encoding: utf-8

# Recipe Robot
# Copyright 2015-2019 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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
test_functional_pkg_zip_download_url.py

Functional tests for Recipe Robot.

Since it's apparently a thing, test scenarios are run by a fictional
character. We will use "Robby the Robot" for ours.
"""


import os
import shutil
import subprocess

from .test_functional import robot_runner, verify_processor_args, get_output_path

# pylint: disable=unused-wildcard-import, wildcard-import
from nose.tools import *
from recipe_robot_lib import FoundationPlist

# pylint: enable=unused-wildcard-import, wildcard-import


def test():
    # Robby wants to challenge Recipe Robot to process a zipped package in a Sparkle feed. Game on!
    app_name = "Karabiner"
    developer = "Fumihiko Takayama"
    input_path = "https://pqrs.org/osx/karabiner/files/Karabiner-10.9.0.dmg"

    # Process the input and return the recipes.
    recipes = robot_runner(input_path, app_name, developer)

    for recipe_type in ("download", "pkg", "munki", "install", "jss"):
        assert_in("Input", recipes[recipe_type])
        assert_in("Process", recipes[recipe_type])

    assert_equals(
        "https://pqrs.org/osx/karabiner/files/appcast.xml",
        recipes["download"]["Input"]["SPARKLE_FEED_URL"],
    )

    # Make sure SparkleUpdateInfoProvider is present and uses the correct repo.
    expected_args = {"appcast_url": "%SPARKLE_FEED_URL%"}
    verify_processor_args(
        "SparkleUpdateInfoProvider", recipes["download"], expected_args
    )

    expected_args = {"filename": "%NAME%-%version%.zip"}
    verify_processor_args("URLDownloader", recipes["download"], expected_args)

    assert_in(
        "EndOfCheckPhase",
        [processor["Processor"] for processor in recipes["download"]["Process"]],
    )

    expected_args = {
        "archive_path": "%pathname%",
        "destination_path": "%RECIPE_CACHE_DIR%/%NAME%",
        "purge_destination": True,
    }
    verify_processor_args("Unarchiver", recipes["download"], expected_args)

    expected_args = {
        "input_path": "%RECIPE_CACHE_DIR%/%NAME%/Karabiner.sparkle_guided.pkg",
        "expected_authority_names": [
            "Developer ID Installer: Fumihiko Takayama (G43BCU2T37)",
            "Developer ID Certification Authority",
            "Apple Root CA",
        ],
    }
    verify_processor_args("CodeSignatureVerifier", recipes["download"], expected_args)

    assert_equals("org.pqrs.Karabiner", recipes["pkg"]["Input"]["BUNDLE_ID"])

    expected_args = {"app_path": "%RECIPE_CACHE_DIR%/%NAME%/Karabiner.app"}
    verify_processor_args("AppPkgCreator", recipes["pkg"], expected_args)

    expected_pkginfo = {
        "blocking_applications": [
            "EventViewer.app",
            "Karabiner.app",
            "Karabiner_AXNotifier.app",
            "Profile3.app",
            "Profile1.app",
            "ReloadXML.app",
            "KarabinerUninstaller.app",
            "Profile2.app",
            "Profile0.app",
            "Karabiner_multitouchextension.app",
        ],
        "catalogs": ["testing"],
        "description": "MacBook keyboard remapper.",
        "developer": developer,
        "display_name": app_name,
        "name": "%NAME%",
        "unattended_install": True,
    }
    assert_equals(expected_pkginfo, recipes["munki"]["Input"]["pkginfo"])

    expected_args = {
        "dmg_path": "%RECIPE_CACHE_DIR%/%NAME%.dmg",
        "dmg_root": "%RECIPE_CACHE_DIR%/%NAME%",
    }
    verify_processor_args("DmgCreator", recipes["munki"], expected_args)

    expected_args = {
        "pkg_path": "%dmg_path%",
        "repo_subdirectory": "%MUNKI_REPO_SUBDIR%",
    }
    verify_processor_args("MunkiImporter", recipes["munki"], expected_args)

    # Make sure JSS recipe inputs are correct.
    assert_equals("Productivity", recipes["jss"]["Input"]["CATEGORY"])
    assert_equals("%NAME%-update-smart", recipes["jss"]["Input"]["GROUP_NAME"])
    assert_equals("SmartGroupTemplate.xml", recipes["jss"]["Input"]["GROUP_TEMPLATE"])
    assert_equals(app_name, recipes["jss"]["Input"]["NAME"])
    assert_equals("Testing", recipes["jss"]["Input"]["POLICY_CATEGORY"])
    assert_equals("PolicyTemplate.xml", recipes["jss"]["Input"]["POLICY_TEMPLATE"])
    assert_equals(
        "MacBook keyboard remapper.",
        recipes["jss"]["Input"]["SELF_SERVICE_DESCRIPTION"],
    )
    assert_equals("%NAME%.png", recipes["jss"]["Input"]["SELF_SERVICE_ICON"])

    expected_args = {
        "category": "%CATEGORY%",
        "groups": [
            {"name": "%GROUP_NAME%", "smart": True, "template_path": "%GROUP_TEMPLATE%"}
        ],
        "policy_category": "%POLICY_CATEGORY%",
        "policy_template": "%POLICY_TEMPLATE%",
        "prod_name": "%NAME%",
        "self_service_description": "%SELF_SERVICE_DESCRIPTION%",
        "self_service_icon": "%SELF_SERVICE_ICON%",
    }
    verify_processor_args("JSSImporter", recipes["jss"], expected_args)

    expected_args = {
        "dmg_path": "%RECIPE_CACHE_DIR%/%NAME%.dmg",
        "dmg_root": "%RECIPE_CACHE_DIR%/%NAME%",
    }
    verify_processor_args("DmgCreator", recipes["install"], expected_args)

    expected_args = {
        "dmg_path": "%dmg_path%",
        "items_to_copy": [
            {"destination_path": "/Applications", "source_item": "Karabiner.app"}
        ],
    }
    verify_processor_args("InstallFromDMG", recipes["install"], expected_args)
