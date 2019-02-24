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


class TestAppStoreAppInput(object):
    pass


# TODO (Shea): Mock up an "app" for testing purposes.
# TODO (Shea): Add arguments to only produce certain RecipeTypes. This will
# allow us to narrow the tests down.
class TestSparkleAppInput(object):
    """Given specific input, make sure Recipe Robot's output checks out."""

    def test(self):
        prefs = FoundationPlist.readPlist(
            os.path.expanduser(
                "~/Library/Preferences/com.elliotjordan.recipe-robot.plist"
            )
        )

        # Robby needs a recipe for Evernote. He decides to try the Robot!
        app = "Evernote"
        developer = "Evernote"
        destination = get_output_path(prefs, app, developer)
        clean_folder(destination)

        subprocess.check_call(
            [
                "./recipe-robot",
                "--ignore-existing",
                "--verbose",
                "/Applications/%s.app" % app,
            ]
        )

        # Ensure the download recipe uses the known-good Sparkle feed URL.
        download_recipe_path = get_output_path(
            prefs, app, developer, recipe_type="download"
        )
        download_recipe = FoundationPlist.readPlist(download_recipe_path)
        assert_in("Process", download_recipe)
        assert_equals(
            "https://update.evernote.com/public/ENMacSMD/EvernoteMacUpdate.xml",
            download_recipe["Input"]["SPARKLE_FEED_URL"],
        )

        # Make sure URLDownloader is present and uses the expected filename.
        assert_in(
            "URLDownloader",
            [processor["Processor"] for processor in download_recipe["Process"]],
        )
        urldownloader_args = [
            processor
            for processor in download_recipe["Process"]
            if processor["Processor"] == "URLDownloader"
        ][0]["Arguments"]
        expected_args = {"filename": "%NAME%-%version%.zip"}
        assert_dict_equal(expected_args, dict(urldownloader_args))

        # Make sure EndOfCheckPhase is present.
        assert_in(
            "EndOfCheckPhase",
            [processor["Processor"] for processor in download_recipe["Process"]],
        )

        # Make sure Unarchiver is present with expected arguments.
        assert_in(
            "Unarchiver",
            [processor["Processor"] for processor in download_recipe["Process"]],
        )
        unarchiver_args = [
            processor
            for processor in download_recipe["Process"]
            if processor["Processor"] == "Unarchiver"
        ][0]["Arguments"]
        expected_args = {
            "destination_path": "%RECIPE_CACHE_DIR%/%NAME%",
            "archive_path": "%pathname%",
            "purge_destination": True,
        }
        assert_dict_equal(expected_args, dict(unarchiver_args))

        # Make sure CodeSignatureVerifier is present with expected arguments.
        assert_in(
            "CodeSignatureVerifier",
            [processor["Processor"] for processor in download_recipe["Process"]],
        )
        codesigverifier_args = [
            processor
            for processor in download_recipe["Process"]
            if processor["Processor"] == "CodeSignatureVerifier"
        ][0]["Arguments"]
        expected_args = {
            "input_path": "%RECIPE_CACHE_DIR%/%NAME%/Evernote.app",
            "requirement": (
                'identifier "com.evernote.Evernote" and '
                "anchor apple generic and "
                "certificate 1[field.1.2.840.113635.100.6.2.6] /* exists */ and "
                "certificate leaf[field.1.2.840.113635.100.6.1.13] /* exists */ and "
                "certificate leaf[subject.OU] = Q79WDW8YH9"
            ),
        }
        assert_dict_equal(expected_args, dict(codesigverifier_args))


class TestGitHubURLInput(object):
    """Given specific input, make sure Recipe Robot's output checks out."""

    def test(self):
        prefs = FoundationPlist.readPlist(
            os.path.expanduser(
                "~/Library/Preferences/com.elliotjordan.recipe-robot.plist"
            )
        )

        # Robby loves MunkiAdmin. Let's make some recipes.
        app = "MunkiAdmin"
        developer = "Hannes Juutilainen"
        url = "https://github.com/hjuutilainen/munkiadmin"
        destination = get_output_path(prefs, app, developer)
        clean_folder(destination)

        subprocess.check_call(["./recipe-robot", "--ignore-existing", "--verbose", url])

        # Ensure the download recipe uses the correct GitHub project.
        download_recipe_path = get_output_path(
            prefs, app, developer, recipe_type="download"
        )
        download_recipe = FoundationPlist.readPlist(download_recipe_path)
        assert_in("Process", download_recipe)
        assert_equals(
            "hjuutilainen/munkiadmin", download_recipe["Input"]["GITHUB_REPO"]
        )

        # Make sure GitHubReleasesInfoProvider is present and uses the correct repo.
        assert_in(
            "GitHubReleasesInfoProvider",
            [processor["Processor"] for processor in download_recipe["Process"]],
        )
        githubreleasesinfoprovider_args = [
            processor
            for processor in download_recipe["Process"]
            if processor["Processor"] == "GitHubReleasesInfoProvider"
        ][0]["Arguments"]
        expected_args = {"github_repo": "%GITHUB_REPO%"}
        assert_dict_equal(expected_args, dict(githubreleasesinfoprovider_args))

        # Make sure URLDownloader is present and has the expected filename.
        assert_in(
            "URLDownloader",
            [processor["Processor"] for processor in download_recipe["Process"]],
        )
        urldownloader_args = [
            processor
            for processor in download_recipe["Process"]
            if processor["Processor"] == "URLDownloader"
        ][0]["Arguments"]
        expected_args = {"filename": "%NAME%-%version%.dmg"}
        assert_dict_equal(expected_args, dict(urldownloader_args))

        # Make sure EndOfCheckPhase is present.
        assert_in(
            "EndOfCheckPhase",
            [processor["Processor"] for processor in download_recipe["Process"]],
        )

        # Make sure CodeSignatureVerifier is present with expected arguments.
        assert_in(
            "CodeSignatureVerifier",
            [processor["Processor"] for processor in download_recipe["Process"]],
        )
        codesigverifier_args = [
            processor
            for processor in download_recipe["Process"]
            if processor["Processor"] == "CodeSignatureVerifier"
        ][0]["Arguments"]
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
        assert_dict_equal(expected_args, dict(codesigverifier_args))

        # Make sure Versioner is present with expected arguments.
        assert_in(
            "Versioner",
            [processor["Processor"] for processor in download_recipe["Process"]],
        )
        versioner_args = [
            processor
            for processor in download_recipe["Process"]
            if processor["Processor"] == "Versioner"
        ][0]["Arguments"]
        expected_args = {
            "input_plist_path": "%pathname%/MunkiAdmin.app/Contents/Info.plist",
            "plist_version_key": "CFBundleShortVersionString",
        }
        assert_dict_equal(expected_args, dict(versioner_args))


def get_output_path(prefs, app_name, developer, recipe_type=None):
    """Build a path to the output dir or output recipe for app_name."""
    path = os.path.join(prefs.get("RecipeCreateLocation"), developer)
    if recipe_type:
        path = os.path.join(path, "%s.%s.recipe" % (app_name, recipe_type))
    return os.path.expanduser(path)


def clean_folder(path):
    """Delete the RecipeCreateLocation subdir if it exists."""
    if os.path.exists(path):
        shutil.rmtree(path)
