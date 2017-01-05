#!/usr/bin/python
# This Python file uses the following encoding: utf-8

# Recipe Robot
# Copyright 2015-2017 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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

from nose.tools import *  # pylint: disable=unused-wildcard-import, wildcard-import

from recipe_robot_lib import FoundationPlist


class TestAppStoreAppInput(object):
    pass


class TestAppInput(object):

    def test_sparkle_feed_app(self):
        # TODO (Shea): Mock up an "app" for testing purposes.
        # TODO (Shea): Add arguments to only produce certain RecipeTypes.
        # This will allow us to narrow the tests down.
        prefs = FoundationPlist.readPlist(os.path.expanduser(
            "~/Library/Preferences/com.elliotjordan.recipe-robot.plist"))

        # Robby needs a recipe for Skitch. He decides to try the Robot!
        app = "Evernote"
        destination = get_output_path(prefs, app)
        clean_folder(destination)

        subprocess.check_call(
            ["./recipe-robot", "--ignore-existing",
             "/Applications/%s.app" % app])

        # First, test the download recipe.
        # We know that (Shea's non-mocked "real" copy) Evernote has a
        # Sparkle Feed. Test to ensure download recipe uses it.
        download_recipe_path = get_output_path(prefs, app,
                                               recipe_type="download")
        download_recipe = FoundationPlist.readPlist(download_recipe_path)
        assert_in("Process", download_recipe)
        assert_equals("https://update.evernote.com/public/ENMacSMD/EvernoteMacUpdate.xml",
                    download_recipe["Input"]["SPARKLE_FEED_URL"])
        assert_in("URLDownloader", [processor["Processor"] for processor
                                    in download_recipe["Process"]])
        url_downloader = [processor for processor in
                          download_recipe["Process"] if
                          processor["Processor"] == "URLDownloader"][0]

        args = url_downloader["Arguments"]
        assert_dict_equal({"filename": "%NAME%-%version%.zip"}, dict(args))


def get_output_path(prefs, app_name, recipe_type=None):
    """Build a path to the output dir or output recipe for app_name."""
    path = os.path.join(prefs.get("RecipeCreateLocation"), app_name)
    if recipe_type:
        path = os.path.join(path, "%s.%s.recipe" % (app_name, recipe_type))
    return os.path.expanduser(path)


def clean_folder(path):
    """Delete the RecipeCreateLocation subdir if it exists."""
    if os.path.exists(path):
        shutil.rmtree(path)
