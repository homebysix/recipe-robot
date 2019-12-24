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
recipe.py

Recipe: Class for describing AutoPkg recipes along with metadata.
Recipes: Container class for Recipe objects.
"""


from __future__ import absolute_import

from recipe_robot_lib import processor
from recipe_robot_lib.roboabc import RoboDict, RoboList
from recipe_robot_lib.tools import (
    LogLevel,
    __version__,
    get_bundle_name_info,
    robo_print,
)

try:
    from recipe_robot_lib import FoundationPlist as plistlib
except ImportError:
    robo_print("Importing plistlib", LogLevel.WARNING)
    import plistlib


# fmt: off
RECIPE_TYPES = (
    {
        "type": "download",
        "desc": "Downloads an app in whatever format the developer provides.",
    }, {
        "type": "pkg",
        "desc": "Creates a standard pkg installer file."
    }, {
        "type": "munki",
        "desc": "Imports into your Munki repository."
    }, {
        "type": "jss",
        "desc": "Imports into Jamf Pro and creates necessary groups, policies, "
                "etc.",
    }, {
        "type": "jss-upload",
        "desc": "Imports package only into Jamf Pro. Does not create policies "
                "or groups.",
    }, {
        "type": "ds",
        "desc": "Imports into your DeployStudio Packages folder."
    }, {
        "type": "filewave",
        "desc": "Imports a fileset into your FileWave server."
    }, {
        "type": "lanrev",
        "desc": "Imports into your LANrev server."
    }, {
        "type": "sccm",
        "desc": "Creates a cmmac package for deploying via Microsoft SCCM.",
    }, {
        "type": "bigfix",
        "desc": "Builds a .bes deployment file and imports it into your "
                "BigFix console",
    }, {
        "type": "install",
        "desc": "Installs the app on the computer running AutoPkg."
    },
)
# fmt: on


class Recipe(RoboDict):
    """An AutoPkg Recipe."""

    def __init__(self, recipe_type, description):
        """Build a recipe dictionary."""
        super(Recipe, self).__init__()
        default_enabled = ("download", "pkg")
        preferred = True if recipe_type in default_enabled else False
        self.update(
            {
                "type": recipe_type,
                "description": description,
                "preferred": preferred,
                "existing": False,
            }
        )
        self["keys"] = {
            "Identifier": "",
            "MinimumVersion": "1.0.0",
            "Input": {"NAME": ""},
            "Process": [],
            "Comment": "Created with Recipe Robot v%s "
            "(https://github.com/homebysix/recipe-robot)" % __version__,
        }

    def write(self, path):
        """Write the recipe to disk."""
        plistlib.writePlist(self["keys"], path)

    def set_description(self, description):
        """Save a description that explains what this recipe does."""
        self["keys"]["Description"] = description

    def set_parent(self, parent):
        """Set the parent recipe key to parent."""
        self["keys"]["ParentRecipe"] = parent.replace(" ", "")

    def set_parent_from(self, prefs, facts, recipe_type):
        """Set parent recipe based on prefs, facts, and a type."""
        _, bundle_name_key = get_bundle_name_info(facts)
        elements = (
            prefs["RecipeIdentifierPrefix"],
            recipe_type,
            facts[bundle_name_key],
        )
        self["keys"]["ParentRecipe"] = ".".join(elements).replace(" ", "")

    def append_processor(self, val):
        if isinstance(val, processor.AbstractProcessor):
            val = val.to_dict()
        self["keys"]["Process"].append(val)


class Recipes(RoboList):
    """A List-like object of Recipe objects."""

    def __init__(self):
        """Store information related to each supported recipe type."""
        super(Recipes, self).__init__()
        self.extend(
            [
                Recipe(recipe_type["type"], recipe_type["desc"])
                for recipe_type in RECIPE_TYPES
            ]
        )
