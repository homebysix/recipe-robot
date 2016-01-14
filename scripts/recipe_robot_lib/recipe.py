#!/usr/bin/python
# This Python file uses the following encoding: utf-8

# Recipe Robot
# Copyright 2015 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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


from recipe_robot_lib import processor
from recipe_robot_lib.roboabc import RoboDict, RoboList
from recipe_robot_lib.tools import (robo_print, LogLevel, __version__)
try:
    from recipe_robot_lib import FoundationPlist
except ImportError:
    robo_print("Importing plistlib as FoundationPlist", LogLevel.WARNING)
    import plistlib as FoundationPlist


# TODO(Elliot): Create a way to specify the display order of this list. (#67)
RECIPE_TYPES = {
    "download": "Downloads an app in whatever format the developer provides.",
    "munki": "Imports into your Munki repository.",
    "pkg": "Creates a standard pkg installer file.",
    "install": "Installs the app on the computer running AutoPkg.",
    "jss": ("Imports into your Casper JSS and creates necessary groups, "
            "policies, etc."),
    "absolute": "Imports into your Absolute Manage server.",
    "sccm": "Creates a cmmac package for deploying via Microsoft SCCM.",
    "ds": "Imports into your DeployStudio Packages folder.",
    "filewave": "Imports a fileset into your FileWave server.",
    "bigfix": ("Builds a .bes deployment file and imports it into your "
               "BigFix console")
}


class Recipe(RoboDict):
    """An AutoPkg Recipe."""

    def __init__(self, recipe_type, description):
        """Build a recipe dictionary."""
        super(Recipe, self).__init__()
        self.update(
            {"type": recipe_type,
             "description": description,
             "preferred": True,
             "existing": False})
        self["keys"] = {
            "Identifier": "",
            "MinimumVersion": "0.5.2",
            "Input": {
                "NAME": ""},
            "Process": [],
            "Comment": "Created with Recipe Robot v%s "
                       "(https://github.com/homebysix/recipe-robot)"
                       % __version__}

    def write(self, path):
        """Write the recipe to disk."""
        FoundationPlist.writePlist(self["keys"], path)

    def set_description(self, description):
        """Save a description that explains what this recipe does."""
        self["keys"]["Description"] = description

    def set_parent(self, parent):
        """Set the parent recipe key to parent."""
        self["keys"]["ParentRecipe"] = parent.replace(" ", "")

    def set_parent_from(self, prefs, facts, recipe_type):
        """Set parent recipe based on prefs, facts, and a type."""
        elements = (prefs["RecipeIdentifierPrefix"], recipe_type,
                    facts["app_name"])
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
        self.extend([Recipe(recipe, desc) for recipe, desc in
                     RECIPE_TYPES.items() ])
