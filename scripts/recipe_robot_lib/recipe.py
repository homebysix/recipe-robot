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
recipe.py

Recipe: Class for describing AutoPkg recipes along with metadata.
Recipes: Container class for Recipe objects.
"""


import plistlib

import yaml
from Foundation import NSArray, NSDictionary, NSNumber
from recipe_robot_lib import processor
from recipe_robot_lib.exceptions import RoboError
from recipe_robot_lib.facts import NotifyingBool, NotifyingList, NotifyingString
from recipe_robot_lib.roboabc import RoboDict, RoboList
from recipe_robot_lib.tools import __version__, get_bundle_name_info

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
        "type": "jamf",
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
    """A dictionary-like representation of an AutoPkg Recipe."""

    def __init__(self, recipe_type, description):
        """Build a recipe dictionary.

        Args:
            recipe_type (str): Type of recipe (e.g. download, pkg, munki).
            description (str): Description of what the recipe does.
        """
        super().__init__()
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

    def __deepconvert(self, object):
        """Convert all contents of an ObjC object to Python primitives, which
        is required in order to convert a recipe for yaml representation.

        Adapted from AutoPkg: https://github.com/autopkg/autopkg/blob/1aff762d8ea658b3fca8ac693f3bf13e8baf8778/Code/autopkglib/__init__.py#L141
        """
        # TODO: Should this be handled by class __repr__ instead?
        value = object
        if isinstance(object, NotifyingBool):
            value = bool(object)
        elif isinstance(object, (NSNumber, float)):
            value = int(object)
        elif isinstance(object, NotifyingString):
            value = str(object)
        elif isinstance(object, (NotifyingList, NSArray, list)):
            value = [self.__deepconvert(x) for x in object]
        elif isinstance(object, (NSDictionary, dict)):
            value = {k: self.__deepconvert(v) for k, v in object.items()}
        else:
            return object
        return value

    def write(self, path, fmt="plist"):
        """Write the recipe to disk.

        Args:
            path (str): Path to which the AutoPkg recipe will be written.

        Raises:
            RoboError: Standard exception raised when Recipe Robot cannot proceed.
        """
        # Ensure MinimumVersion is at least 2.3 to support yaml recipes.
        self["keys"]["MinimumVersion"] = max("2.3", self["keys"]["MinimumVersion"])

        # Ensure all objects in the recipe are Python primitives.
        recipe = self.__deepconvert(self["keys"])
        if fmt == "yaml":
            try:
                with open(path, "wb") as openfile:
                    yaml.dump(recipe, openfile, encoding="utf-8")
            except Exception as err:
                raise RoboError(
                    "Unable to write yaml recipe due to unexpected data type.\n"
                    "yaml error: %s\n"
                    "Recipe contents: %s\n" % (err, recipe)
                )
        # In case AutoPkg ever supports json recipes.
        # elif fmt == "json":
        #     try:
        #         with open(path, "wb") as openfile:
        #             openfile.write(json.dumps(recipe, indent=4))
        #     except Exception as err:
        #         raise RoboError(
        #             "Unable to write json recipe due to unexpected data type.\n"
        #             "json error: %s\n"
        #             "Recipe contents: %s\n" % (err, recipe)
        #         )
        else:
            try:
                with open(path, "wb") as openfile:
                    plistlib.dump(recipe, openfile)
            except Exception as err:
                raise RoboError(
                    "Unable to write plist recipe due to unexpected data type.\n"
                    "plistlib error: %s\n"
                    "Recipe contents: %s\n" % (err, recipe)
                )

    def set_description(self, description):
        """Save a description that explains what this recipe does.

        Args:
            description (str): Description of what the recipe does.
        """
        self["keys"]["Description"] = description

    def set_parent(self, parent):
        """Set the parent recipe key to parent.

        Args:
            parent (str): Reverse-domain identifier of the parent recipe. (The
                parent recipe must have also been produced by Recipe Robot in
                the same run as this recipe.)
        """
        self["keys"]["ParentRecipe"] = parent.replace(" ", "")

    def set_parent_from(self, prefs, facts, recipe_type):
        """Set parent recipe based on prefs, facts, and a type.

        Args:
            prefs (dict): The dictionary containing a key/value pair for Recipe Robot
                preferences.
            facts (RoboDict): A continually-updated dictionary containing all the
                information we know so far about the app associated with the
                input path.
            recipe_type (str): Type of recipe (e.g. download, pkg, munki).
        """
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
    """A list-like object of Recipe objects."""

    def __init__(self):
        """Store information related to each supported recipe type."""
        super().__init__()
        self.extend(
            [
                Recipe(recipe_type["type"], recipe_type["desc"])
                for recipe_type in RECIPE_TYPES
            ]
        )
