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
test_functional_pkg_download_url.py

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

# pylint: enable=unused-wildcard-import, wildcard-import


def test():
    # Robby wants a challenge: a pkg with multiple apps inside.
    app_name = "Kindle Previewer 3"
    developer = "AMZN Mobile"
    description = "Preview book layouts; ideal for publishers and authors."
    input_path = (
        "https://s3.amazonaws.com/kindlepreviewer3/KindlePreviewerInstaller.pkg"
    )

    if not input_path:
        return

    # Process the input and return the recipes.
    recipes = robot_runner(input_path, app_name, developer)

    # Perform checks on recipes.
    for recipe_type in ("download", "munki", "install", "jss"):
        assert_in("Input", recipes[recipe_type])
        assert_in("Process", recipes[recipe_type])

    assert_equals(
        "https://s3.amazonaws.com/kindlepreviewer3/KindlePreviewerInstaller.pkg",
        recipes["download"]["Input"]["DOWNLOAD_URL"],
    )

    expected_args = {"filename": "%NAME%.pkg", "url": "%DOWNLOAD_URL%"}
    verify_processor_args("URLDownloader", recipes["download"], expected_args)

    assert_in(
        "EndOfCheckPhase",
        [processor["Processor"] for processor in recipes["download"]["Process"]],
    )

    expected_args = {
        "input_path": "%pathname%",
        "expected_authority_names": [
            "Developer ID Installer: AMZN Mobile LLC (94KV3E626L)",
            "Developer ID Certification Authority",
            "Apple Root CA",
        ],
    }
    verify_processor_args("CodeSignatureVerifier", recipes["download"], expected_args)

    expected_pkginfo = {
        "blocking_applications": [
            "KindlePreviewerUpdater.app",
            "Kindle Previewer 3.app",
        ],
        "catalogs": ["testing"],
        "description": description,
        "developer": developer,
        "display_name": app_name,
        "name": "%NAME%",
        "unattended_install": True,
    }
    assert_equals(expected_pkginfo, recipes["munki"]["Input"]["pkginfo"])

    expected_args = {
        "pkg_path": "%pathname%",
        "repo_subdirectory": "%MUNKI_REPO_SUBDIR%",
    }
    verify_processor_args("MunkiImporter", recipes["munki"], expected_args)

    assert_equals("Productivity", recipes["jss"]["Input"]["CATEGORY"])
    assert_equals("%NAME%-update-smart", recipes["jss"]["Input"]["GROUP_NAME"])
    assert_equals("SmartGroupTemplate.xml", recipes["jss"]["Input"]["GROUP_TEMPLATE"])
    assert_equals(app_name, recipes["jss"]["Input"]["NAME"])
    assert_equals("Testing", recipes["jss"]["Input"]["POLICY_CATEGORY"])
    assert_equals("PolicyTemplate.xml", recipes["jss"]["Input"]["POLICY_TEMPLATE"])
    assert_equals(description, recipes["jss"]["Input"]["SELF_SERVICE_DESCRIPTION"])
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

    expected_args = {"pkg_path": "%pathname%"}
    verify_processor_args("Installer", recipes["install"], expected_args)
