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

Describes a Recipe class, mostly by initializing keys.
"""


from collections import MutableMapping
import os

from recipe_robot_lib.tools import (robo_print, LogLevel)
try:
    from recipe_robot_lib import FoundationPlist
except ImportError:
    robo_print("Importing plistlib as FoundationPlist", LogLevel.WARNING)
    import plistlib as FoundationPlist


class Recipe(MutableMapping):

    def __init__(self, recipe_type, description):
        """Build a recipe dictionary."""
        self._dict = {"type": recipe_type,
                    "description": description,
                    "preferred": True,
                    "existing": False}

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, val):
        self._dict[key] = val

    def __delitem__(self, key):
        if key in self:
            del self._dict[key]

    def __iter__(self):
        for key in self._dict:
            yield key

    def __len__(self):
        return len(self._dict)

    def __repr__(self):
        return self._dict.__repr__()

    def write(self, path):
        """Write the recipe to disk."""
        if len(self["keys"]["Process"]) > 0:
            FoundationPlist.writePlist(self["keys"], path)


def init_recipes():
    """Store information related to each supported AutoPkg recipe type.

    Returns:
        A generator that builds a Recipe for each type of recipe we
        know about.
    """
    recipes_meta = (
        ("download", "Downloads an app in whatever format the developer "
                     "provides."),
        ("munki", "Imports into your Munki repository."),
        ("pkg", "Creates a standard pkg installer file."),
        ("install", "Installs the app on the computer running AutoPkg."),
        ("jss", "Imports into your Casper JSS and creates necessary groups, "
         "policies, etc."),
        ("absolute", "Imports into your Absolute Manage server."),
        ("sccm", "Creates a cmmac package for deploying via Microsoft SCCM."),
        ("ds", "Imports into your DeployStudio Packages folder."),
        ("filewave", "Imports a fileset into your FileWave server."))

    recipes = ([Recipe(*recipe) for recipe in recipes_meta])

    return recipes