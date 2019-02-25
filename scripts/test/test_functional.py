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

# TODO (Shea): Mock up an "app" for testing purposes.
# TODO (Shea): Add arguments to only produce certain RecipeTypes. This will
# allow us to narrow the tests down.


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
