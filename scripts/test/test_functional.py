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
test_functional.py

Functional tests for Recipe Robot.

Since it's apparently a thing, test scenarios are run by a fictional
character. We will use "Robby the Robot" for ours.
"""


import os
import shutil
import subprocess

# pylint: disable=unused-wildcard-import, wildcard-import
from nose.tools import *
from recipe_robot_lib import FoundationPlist

# pylint: enable=unused-wildcard-import, wildcard-import


def robot_runner(input_path, app, dev):
    """For given input, run Recipe Robot and return the output recipes as dicts."""
    # Read preferences.
    prefs = FoundationPlist.readPlist(
        os.path.expanduser("~/Library/Preferences/com.elliotjordan.recipe-robot.plist")
    )
    destination = get_output_path(prefs, app, dev)
    clean_folder(destination)
    subprocess.check_call(
        ["./recipe-robot", "--ignore-existing", "--verbose", input_path]
    )
    # Process the output recipes into dicts.
    recipes = {
        "download": FoundationPlist.readPlist(
            get_output_path(prefs, app, dev, recipe_type="download")
        ),
        "pkg": FoundationPlist.readPlist(
            get_output_path(prefs, app, dev, recipe_type="pkg")
        ),
        "munki": FoundationPlist.readPlist(
            get_output_path(prefs, app, dev, recipe_type="munki")
        ),
        "install": FoundationPlist.readPlist(
            get_output_path(prefs, app, dev, recipe_type="install")
        ),
        "jss": FoundationPlist.readPlist(
            get_output_path(prefs, app, dev, recipe_type="jss")
        ),
    }

    return recipes


def verify_processor_args(processor_name, recipe, expected_args):
    """Verify processor arguments against known dict."""
    assert_in(
        processor_name, [processor["Processor"] for processor in recipe["Process"]]
    )
    actual_args = dict(
        [
            processor
            for processor in recipe["Process"]
            if processor["Processor"] == processor_name
        ][0]["Arguments"]
    )
    assert_dict_equal(expected_args, actual_args)


def get_output_path(prefs, app_name, developer, recipe_type=None):
    """Build a path to the output dir or output recipe for app_name."""
    path = os.path.join(prefs.get("RecipeCreateLocation"), developer)
    if recipe_type:
        path = os.path.join(path, "{}.{}.recipe".format(app_name, recipe_type))
        if not os.path.exists(path):
            print("[ERROR] {} does not exist.".format(path))
    return os.path.expanduser(path)


def clean_folder(path):
    """Delete the RecipeCreateLocation subdir if it exists."""
    if os.path.exists(path):
        shutil.rmtree(path)


# TODO (Shea): Mock up an "app" for testing purposes.
# TODO (Shea): Add arguments to only produce certain RecipeTypes. This will
# allow us to narrow the tests down.
def zip_sparkle_app_test():
    # Robby needs a recipe for Evernote. He decides to try the Robot!
    app_name = "Evernote"
    developer = "Evernote"
    input_path = "/Applications/Evernote.app"  # requires app to be installed

    # Process the input and return the recipes.
    recipes = robot_runner(input_path, app_name, developer)

    # Check required recipe sections.
    for recipe_type in ("download", "pkg", "munki", "install", "jss"):
        assert_in("Input", recipes[recipe_type])
        assert_in("Process", recipes[recipe_type])

    # Make sure correct Sparkle feed is used.
    assert_equals(
        "https://update.evernote.com/public/ENMacSMD/EvernoteMacUpdate.xml",
        recipes["download"]["Input"]["SPARKLE_FEED_URL"],
    )

    # Make sure SparkleUpdateInfoProvider is present and uses the correct repo.
    expected_args = {"appcast_url": "%SPARKLE_FEED_URL%"}
    verify_processor_args(
        "SparkleUpdateInfoProvider", recipes["download"], expected_args
    )

    # Make sure URLDownloader is present and has the expected filename.
    expected_args = {"filename": "%NAME%-%version%.zip"}
    verify_processor_args("URLDownloader", recipes["download"], expected_args)

    # Make sure EndOfCheckPhase is present.
    assert_in(
        "EndOfCheckPhase",
        [processor["Processor"] for processor in recipes["download"]["Process"]],
    )

    # Make sure Unarchiver is present with expected arguments.
    expected_args = {
        "archive_path": "%pathname%",
        "destination_path": "%RECIPE_CACHE_DIR%/%NAME%",
        "purge_destination": True,
    }
    verify_processor_args("Unarchiver", recipes["download"], expected_args)

    # Make sure CodeSignatureVerifier is present with expected arguments.
    expected_args = {
        "input_path": "%RECIPE_CACHE_DIR%/%NAME%/Evernote.app",
        "requirement": (
            'identifier "com.evernote.Evernote" and anchor apple generic and '
            "certificate 1[field.1.2.840.113635.100.6.2.6] /* exists */ and "
            "certificate leaf[field.1.2.840.113635.100.6.1.13] /* exists */ and "
            "certificate leaf[subject.OU] = Q79WDW8YH9"
        ),
    }
    verify_processor_args("CodeSignatureVerifier", recipes["download"], expected_args)

    # Make sure correct bundle identifier is used.
    assert_equals("com.evernote.Evernote", recipes["pkg"]["Input"]["BUNDLE_ID"])

    # Make sure AppPkgCreator is present with expected arguments..
    expected_args = {"app_path": "%RECIPE_CACHE_DIR%/%NAME%/Evernote.app"}
    verify_processor_args("AppPkgCreator", recipes["pkg"], expected_args)

    # Make sure correct Munki pkginfo is used.
    expected_pkginfo = {
        "catalogs": ["testing"],
        "description": "Create searchable notes and access them anywhere.",
        "developer": developer,
        "display_name": app_name,
        "name": "%NAME%",
        "unattended_install": True,
    }
    assert_equals(expected_pkginfo, recipes["munki"]["Input"]["pkginfo"])

    # Make sure DmgCreator is present with expected arguments.
    expected_args = {
        "dmg_path": "%RECIPE_CACHE_DIR%/%NAME%.dmg",
        "dmg_root": "%RECIPE_CACHE_DIR%/%NAME%",
    }
    verify_processor_args("DmgCreator", recipes["munki"], expected_args)

    # Make sure MunkiImporter is present with expected arguments.
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
        "Create searchable notes and access them anywhere.",
        recipes["jss"]["Input"]["SELF_SERVICE_DESCRIPTION"],
    )
    assert_equals("%NAME%.png", recipes["jss"]["Input"]["SELF_SERVICE_ICON"])

    # Make sure JSSImporter is present with expected arguments.
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

    # Make sure DmgCreator is present with expected arguments.
    expected_args = {
        "dmg_path": "%RECIPE_CACHE_DIR%/%NAME%.dmg",
        "dmg_root": "%RECIPE_CACHE_DIR%/%NAME%",
    }
    verify_processor_args("DmgCreator", recipes["install"], expected_args)

    # Make sure InstallFromDMG is present with expected arguments.
    expected_args = {
        "dmg_path": "%dmg_path%",
        "items_to_copy": [
            {"destination_path": "/Applications", "source_item": "Evernote.app"}
        ],
    }
    verify_processor_args("InstallFromDMG", recipes["install"], expected_args)


def dmg_sparkle_app_test():
    # Robby wishes there was a one-click app to set up AutoPkg. Oh look, AutoPkgr!
    app_name = "AutoPkgr"
    developer = "The Linde Group Computer Support Inc"
    input_path = "/Applications/AutoPkgr.app"  # requires app to be installed

    # Process the input and return the recipes.
    recipes = robot_runner(input_path, app_name, developer)

    # Check required recipe sections.
    for recipe_type in ("download", "pkg", "munki", "install", "jss"):
        assert_in("Input", recipes[recipe_type])
        assert_in("Process", recipes[recipe_type])

    # Make sure correct Sparkle feed is used.
    assert_equals(
        "https://raw.githubusercontent.com/lindegroup/autopkgr/appcast/appcast.xml",
        recipes["download"]["Input"]["SPARKLE_FEED_URL"],
    )

    # Make sure SparkleUpdateInfoProvider is present and uses the correct repo.
    expected_args = {"appcast_url": "%SPARKLE_FEED_URL%"}
    verify_processor_args(
        "SparkleUpdateInfoProvider", recipes["download"], expected_args
    )

    # Make sure URLDownloader is present and has the expected filename.
    expected_args = {"filename": "%NAME%-%version%.dmg"}
    verify_processor_args("URLDownloader", recipes["download"], expected_args)

    # Make sure EndOfCheckPhase is present.
    assert_in(
        "EndOfCheckPhase",
        [processor["Processor"] for processor in recipes["download"]["Process"]],
    )

    # Make sure CodeSignatureVerifier is present with expected arguments.
    expected_args = {
        "input_path": "%pathname%/AutoPkgr.app",
        "requirement": (
            'anchor apple generic and identifier "com.lindegroup.AutoPkgr" and '
            "(certificate leaf[field.1.2.840.113635.100.6.1.9] /* exists */ or "
            "certificate 1[field.1.2.840.113635.100.6.2.6] /* exists */ and "
            "certificate leaf[field.1.2.840.113635.100.6.1.13] /* exists */ and "
            "certificate leaf[subject.OU] = JVY2ZR6SEF)"
        ),
    }
    verify_processor_args("CodeSignatureVerifier", recipes["download"], expected_args)

    # Make sure correct bundle identifier is used.
    assert_equals("com.lindegroup.AutoPkgr", recipes["pkg"]["Input"]["BUNDLE_ID"])

    # Make sure AppPkgCreator is present.
    assert_in(
        "AppPkgCreator",
        [processor["Processor"] for processor in recipes["pkg"]["Process"]],
    )

    # Make sure correct Munki pkginfo is used.
    expected_pkginfo = {
        "catalogs": ["testing"],
        "description": "AutoPkgr is a free Mac app that makes it easy to install and configure AutoPkg.",
        "developer": developer,
        "display_name": app_name,
        "name": "%NAME%",
        "unattended_install": True,
    }
    assert_equals(expected_pkginfo, recipes["munki"]["Input"]["pkginfo"])

    # Make sure MunkiImporter is present with expected arguments.
    expected_args = {
        "pkg_path": "%pathname%",
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
        "AutoPkgr is a free Mac app that makes it easy to install and configure AutoPkg.",
        recipes["jss"]["Input"]["SELF_SERVICE_DESCRIPTION"],
    )
    assert_equals("%NAME%.png", recipes["jss"]["Input"]["SELF_SERVICE_ICON"])

    # Make sure JSSImporter is present with expected arguments.
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

    # Make sure InstallFromDMG is present with expected arguments.
    expected_args = {
        "dmg_path": "%pathname%",
        "items_to_copy": [
            {"destination_path": "/Applications", "source_item": "AutoPkgr.app"}
        ],
    }
    verify_processor_args("InstallFromDMG", recipes["install"], expected_args)


def github_url_test():
    # Robby loves MunkiAdmin. Let's make some recipes.
    app_name = "MunkiAdmin"
    developer = "Hannes Juutilainen"
    input_path = "https://github.com/hjuutilainen/munkiadmin"

    # Process the input and return the recipes.
    recipes = robot_runner(input_path, app_name, developer)

    # Check required recipe sections.
    for recipe_type in ("download", "pkg", "munki", "install", "jss"):
        assert_in("Input", recipes[recipe_type])
        assert_in("Process", recipes[recipe_type])

    # Make sure correct GitHub repo is used.
    assert_equals(
        "hjuutilainen/munkiadmin", recipes["download"]["Input"]["GITHUB_REPO"]
    )

    # Make sure GitHubReleasesInfoProvider is present and uses the correct repo.
    expected_args = {"github_repo": "%GITHUB_REPO%"}
    verify_processor_args(
        "GitHubReleasesInfoProvider", recipes["download"], expected_args
    )

    # Make sure URLDownloader is present and has the expected filename.
    expected_args = {"filename": "%NAME%-%version%.dmg"}
    verify_processor_args("URLDownloader", recipes["download"], expected_args)

    # Make sure EndOfCheckPhase is present.
    assert_in(
        "EndOfCheckPhase",
        [processor["Processor"] for processor in recipes["download"]["Process"]],
    )

    # Make sure CodeSignatureVerifier is present with expected arguments.
    expected_args = {
        "input_path": "%pathname%/MunkiAdmin.app",
        "requirement": (
            'anchor apple generic and identifier "com.hjuutilainen.MunkiAdmin" and '
            "(certificate leaf[field.1.2.840.113635.100.6.1.9] /* exists */ or "
            "certificate 1[field.1.2.840.113635.100.6.2.6] /* exists */ and "
            "certificate leaf[field.1.2.840.113635.100.6.1.13] /* exists */ and "
            'certificate leaf[subject.OU] = "8XXWJ76X9Y")'
        ),
    }
    verify_processor_args("CodeSignatureVerifier", recipes["download"], expected_args)

    # Make sure Versioner is present with expected arguments.
    expected_args = {
        "input_plist_path": "%pathname%/MunkiAdmin.app/Contents/Info.plist",
        "plist_version_key": "CFBundleShortVersionString",
    }
    verify_processor_args("Versioner", recipes["download"], expected_args)

    # Make sure correct bundle identifier is used.
    assert_equals("com.hjuutilainen.MunkiAdmin", recipes["pkg"]["Input"]["BUNDLE_ID"])

    # Make sure AppPkgCreator is present.
    assert_in(
        "AppPkgCreator",
        [processor["Processor"] for processor in recipes["pkg"]["Process"]],
    )

    # Make sure correct Munki pkginfo is used.
    expected_pkginfo = {
        "catalogs": ["testing"],
        "description": "macOS app for managing Munki repositories",
        "developer": developer,
        "display_name": app_name,
        "name": "%NAME%",
        "unattended_install": True,
    }
    assert_equals(expected_pkginfo, recipes["munki"]["Input"]["pkginfo"])

    # Make sure MunkiImporter is present with expected arguments.
    expected_args = {
        "pkg_path": "%pathname%",
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
        "macOS app for managing Munki repositories",
        recipes["jss"]["Input"]["SELF_SERVICE_DESCRIPTION"],
    )
    assert_equals("%NAME%.png", recipes["jss"]["Input"]["SELF_SERVICE_ICON"])

    # Make sure JSSImporter is present with expected arguments.
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

    # Make sure InstallFromDMG is present with expected arguments.
    expected_args = {
        "dmg_path": "%pathname%",
        "items_to_copy": [
            {"destination_path": "/Applications", "source_item": "MunkiAdmin.app"}
        ],
    }
    verify_processor_args("InstallFromDMG", recipes["install"], expected_args)


def bitbucket_url_test():
    pass


def sourceforge_url_test():
    pass


def zip_sparkle_url_test():
    pass


def dmg_sparkle_url_test():
    pass


def devmate_url_test():
    pass


def zip_download_url_test():
    pass


def dmg_download_url_test():
    pass


def pkg_download_url_test():
    pass


def zip_with_wherefroms_test():
    pass


def dmg_with_wherefroms_test():
    pass


def pkg_with_wherefroms_test():
    pass
