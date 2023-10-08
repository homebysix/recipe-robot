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


"""
test_functional.py

Functional test support functions for Recipe Robot.

Since it's apparently a thing, test scenarios are run by a fictional
character. We will use "Robby the Robot" for ours.
"""


from __future__ import absolute_import, print_function

import os
import plistlib
import shutil
import subprocess
from random import shuffle

import yaml
from nose.tools import *
from recipe_robot_lib.tools import strip_dev_suffix

# pylint: enable=unused-wildcard-import, wildcard-import

# TODO (Shea): Mock up an "app" for testing purposes.
# TODO (Shea): Add arguments to only produce certain RecipeTypes. This will
# allow us to narrow the tests down.

RECIPE_TYPES = ("download", "pkg", "munki", "install", "jss")


def robot_runner(input_path):
    """For given input, run Recipe Robot and return the output recipes as dicts."""

    proc = subprocess.run(
        ["./recipe-robot", "--ignore-existing", "--verbose", input_path], check=False
    )
    assert_equal(
        proc.returncode,
        0,
        "{}: Recipe Robot returned nonzero return code.".format(input_path),
    )


def autopkg_runner(recipe_path):
    """For given recipe path, run AutoPkg and make sure the return code is zero."""

    proc = subprocess.run(
        ["/usr/local/bin/autopkg", "run", recipe_path, "--quiet"], check=False
    )
    assert_equal(
        proc.returncode,
        0,
        "{}: AutoPkg returned nonzero return code.".format(recipe_path),
    )


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


def test():
    """Functional tests"""

    # Read preferences.
    prefs_path = "~/Library/Preferences/com.elliotjordan.recipe-robot.plist"
    with open(os.path.expanduser(prefs_path), "rb") as openfile:
        prefs = plistlib.load(openfile)

    # Read and randomize sample data.
    with open("test/sample_data.yaml", "rb") as openfile:
        sample_data = yaml.load(openfile, Loader=yaml.FullLoader)
    shuffle(sample_data)

    # Iterate through sample data, generating a recipe for each input.
    for app in sample_data:
        if prefs.get("StripDeveloperSuffixes") is True:
            app["developer"] = strip_dev_suffix(app["developer"])

        # Remove output folder, if it exists.
        destination = get_output_path(prefs, app["app_name"], app["developer"])
        clean_folder(destination)

        yield robot_runner, app["input_path"]

        for recipe_type in RECIPE_TYPES:
            recipe_path = get_output_path(
                prefs, app["app_name"], app["developer"], recipe_type=recipe_type
            )
            if recipe_type in ("download", "pkg"):
                # TODO: Remove AutoPkg cache folder, if it exists.
                if os.path.isfile(recipe_path):
                    yield autopkg_runner, recipe_path
