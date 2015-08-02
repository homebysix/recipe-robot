#!/usr/bin/env python
# This Python file uses the following encoding: utf-8

# Recipe Robot
# Copyright 2015 Elliot Jordan, Shea G. Craig
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
recipe-robot.py

usage: recipe-robot.py [-h] [-v] [-o OUTPUT] [-t RECIPE_TYPE]
                       [--include-existing] [--config]
                       input_path

Easily and automatically create AutoPkg recipes.

positional arguments:
  input_path            Path to a recipe or app to use as the basis for
                        creating AutoPkg recipes.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Generate additional output about the process.
  -o OUTPUT, --output OUTPUT
                        Path to a folder you'd like to save your generated
                        recipes in.
  -t RECIPE_TYPE, --recipe-type RECIPE_TYPE
                        The type(s) of recipe you'd like to generate.
  --include-existing    Offer to generate recipes even if one already exists
                        on GitHub.
  --config              Adjust Recipe Robot preferences prior to generating
                        recipes.
"""


import argparse
import os.path
import plistlib
import pprint
import random
import shlex
from subprocess import Popen, PIPE
import sys


# Global variables.
version = '0.0.1'
debug_mode = True  # set to True for additional output
prefs_file = os.path.expanduser(
    "~/Library/Preferences/com.elliotjordan.recipe-robot.plist")

# Build the list of download formats we know about.
# TODO: It would be great if we didn't need this list, but I suspect we do need
# it in order to tell the recipes which Processors to use.
supported_download_formats = ("dmg", "zip", "tar.gz", "gzip", "pkg")


class bcolors:

    """Specify colors that are used in Terminal output."""

    BOLD = '\033[1m'
    DEBUG = '\033[95m'
    ENDC = '\033[0m'
    ERROR = '\033[91m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    UNDERLINE = '\033[4m'
    WARNING = '\033[93m'


class InputType(object):

    """Python pseudo-enum for describing types of input."""

    (app,
     download_recipe,
     munki_recipe,
     pkg_recipe,
     install_recipe,
     jss_recipe,
     absolute_recipe,
     sccm_recipe,
     ds_recipe) = range(9)


# Use this as a reference to build out the classes below:
# https://github.com/homebysix/recipe-robot/blob/master/DEVNOTES.md


class Recipe(object):

    """A generic AutoPkg recipe class."""

    def create(self):
        """Create a new recipe with required keys set to defaults."""
        self["Identifier"] = ""
        self["Input"] = {}
        self["Input"]["NAME"] = ""
        self["Process"] = []
        self["MinimumVersion"] = "0.5.0"

    def add_input(self, key, value=""):
        """Add or set a recipe input variable."""
        self["Input"][key] = value


class DownloadRecipe(Recipe):

    """A download recipe class. Extends Recipe."""

    def create(self):
        """Create a new recipe with required keys set to defaults."""
        self["Process"].append({
            "Processor": "URLDownloader"
        })


class MunkiRecipe(Recipe):

    """A munki recipe class. Extends Recipe."""

    def create(self):
        """Create a new recipe with required keys set to defaults."""
        self["ParentRecipe"] = ""
        self["Input"]["MUNKI_REPO_SUBDIR"] = ""
        self["Input"]["pkginfo"] = {
            "catalogs": [],
            "description": [],
            "display_name": [],
            "name": [],
            "unattended_install": True
        }
        self["Process"].append({
            "Processor": "MunkiImporter",
            "Arguments": {
                "pkg_path": "%pathname%",
                "repo_subdirectory": "%MUNKI_REPO_SUBDIR%"
            }
        })


class PkgRecipe(Recipe):

    """A pkg recipe class. Extends Recipe."""

    def create(self):
        """Create a new recipe with required keys set to defaults."""
        self["ParentRecipe"] = ""
        self["Input"]["PKG_ID"] = ""
        self["Process"].append({
            "Processor": "PkgRootCreator",
            "Arguments": {
                "pkgroot": "%RECIPE_CACHE_DIR%/%NAME%",
                "pkgdirs": {}
            }
        })
        self["Process"].append({
            "Processor": "Versioner",
            "Arguments": {
                "input_plist_path": "",
                "plist_version_key": ""
            }
        })
        self["Process"].append({
            "Processor": "PkgCreator",
            "Arguments": {
                "pkg_request": {
                    "pkgname": "%NAME%-%version%",
                    "version": "%version%",
                    "id": "",
                    "options": "purge_ds_store",
                    "chown": [{
                        "path": "Applications",
                        "user": "root",
                        "group": "admin"
                    }]
                }
            }
        })


class InstallRecipe(Recipe):

    """An install recipe class. Extends Recipe."""

    def create(self):
        """Create a new recipe with required keys set to defaults."""
        self["ParentRecipe"] = ""


class JSSRecipe(Recipe):

    """A jss recipe class. Extends Recipe."""

    def create(self):
        """Create a new recipe with required keys set to defaults."""
        self["ParentRecipe"] = ""
        self["Input"]["prod_name"] = ""
        self["Input"]["category"] = ""
        self["Input"]["policy_category"] = ""
        self["Input"]["policy_template"] = ""
        self["Input"]["self_service_icon"] = ""
        self["Input"]["self_service_description"] = ""
        self["Input"]["groups"] = []
        self["Input"]["GROUP_NAME"] = ""
        self["Input"]["GROUP_TEMPLATE"] = ""
        self["Process"].append({
            "Processor": "JSSImporter",
            "Arguments": {
                "prod_name": "%NAME%",
                "category": "%CATEGORY%",
                "policy_category": "%POLICY_CATEGORY%",
                "policy_template": "%POLICY_TEMPLATE%",
                "self_service_icon": "%SELF_SERVICE_ICON%",
                "self_service_description": "%SELF_SERVICE_DESCRIPTION%",
                "groups": [{
                    "name": "%GROUP_NAME%",
                    "smart": True,
                    "template_path": "%GROUP_TEMPLATE%"
                }]
            }
        })


class AbsoluteRecipe(Recipe):

    """An absolute recipe class. Extends Recipe."""

    def create(self):
        """Create a new recipe with required keys set to defaults."""
        self["ParentRecipe"] = ""
        self["Process"].append({
            "Processor": "com.github.tburgin.AbsoluteManageExport/AbsoluteManageExport",
            "SharedProcessorRepoURL": "https://github.com/tburgin/AbsoluteManageExport",
            "Arguments": {
                "dest_payload_path": "%RECIPE_CACHE_DIR%/%NAME%-%version%.amsdpackages",
                "sdpackages_ampkgprops_path": "%RECIPE_DIR%/%NAME%-Defaults.ampkgprops",
                "source_payload_path": "%pkg_path%",
                "import_abman_to_servercenter": True
            }
        })


class SCCMRecipe(Recipe):

    """An sccm recipe class. Extends Recipe."""

    def create(self):
        """Create a new recipe with required keys set to defaults."""
        self["ParentRecipe"] = ""
        self["Process"].append({
            "Processor": "com.github.autopkg.cgerke-recipes.SharedProcessors/CmmacCreator",
            "SharedProcessorRepoURL": "https://github.com/autopkg/cgerke-recipes",
            "Arguments": {
                "source_file": "%RECIPE_CACHE_DIR%/%NAME%-%version%.pkg",
                "destination_directory": "%RECIPE_CACHE_DIR%"
            }
        })


class DSRecipe(Recipe):

    """A ds recipe class. Extends Recipe."""

    def create(self):
        """Create a new recipe with required keys set to defaults."""
        self["ParentRecipe"] = ""
        self["Input"]["DS_PKGS_PATH"] = ""
        self["Input"]["DS_NAME"] = ""
        self["Process"].append({
            "Processor": "StopProcessingIf",
            "Arguments": {
                "predicate": "new_package_request == FALSE"
            }
        })
        self["Process"].append({
            "Processor": "Copier",
            "Arguments": {
                "source_path": "%pkg_path%",
                "destination_path": "%DS_PKGS_PATH%/%DS_NAME%.pkg",
                "overwrite": True
            }
        })


# TODO(Elliot): Once classes are added, rework these functions to use classes
# instead of existing hard-wired logic:
#    - init_recipes
#    - init_prefs
#    - build_prefs
#    - get_input_type
#    - create_existing_recipe_list
#    - create_buildable_recipe_list
#    - handle_app_input
#    - handle_download_recipe_input
#    - handle_munki_recipe_input
#    - handle_pkg_recipe_input
#    - handle_install_recipe_input
#    - handle_jss_recipe_input
#    - handle_absolute_recipe_input
#    - handle_sccm_recipe_input
#    - handle_ds_recipe_input
#    - search_sourceforge_and_github
#    - select_recipes_to_generate
#    - generate_selected_recipes
#    - write_recipe_file

def robo_print(output_type, message):
    """Print the specified message in an appropriate color, and only print
    debug output if debug_mode is True.
    """

    if output_type == "error":
        print >> sys.stderr, bcolors.ERROR, "[ERROR]", message, bcolors.ENDC
    elif output_type == "warning":
        print >> sys.stderr, bcolors.WARNING, "[WARNING]", message, bcolors.ENDC
    elif output_type == "debug" and debug_mode is True:
        print bcolors.DEBUG, "[DEBUG]", message, bcolors.ENDC
    else:
        print message


def get_exitcode_stdout_stderr(cmd):
    """Execute the external command and get its exitcode, stdout and stderr."""

    args = shlex.split(cmd)
    # TODO(Elliot): I've been told Popen is not a good practice. Better idea?
    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    exitcode = proc.returncode
    return exitcode, out, err


def build_argument_parser():
    """Build and return the argument parser for Recipe Robot."""

    parser = argparse.ArgumentParser(
        description="Easily and automatically create AutoPkg recipes.")
    parser.add_argument(
        "input_path",
        help="Path to a recipe or app to use as the basis for creating AutoPkg recipes.")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Generate additional output about the process.")
    parser.add_argument(
        "-o", "--output",
        action="store",
        help="Path to a folder you'd like to save your generated recipes in.")
    parser.add_argument(
        "-t", "--recipe-type",
        action="store",
        help="The type(s) of recipe you'd like to generate.")
    parser.add_argument(
        "--include-existing",
        action="store_true",
        help="Offer to generate recipes even if one already exists on GitHub.")
    parser.add_argument(
        "--config",
        action="store_true",
        help="Adjust Recipe Robot preferences prior to generating recipes.")
    return parser


def print_welcome_text():
    """Print the text that people see when they first start Recipe Robot."""

    welcome_text = """%s%s
                      -----------------------------------
                     |  Welcome to Recipe Robot v%s.  |
                      -----------------------------------
                                \   _[]_
                                 \  [oo]
                                   d-||-b
                                     ||
                                   _/  \_
    """ % (bcolors.DEBUG, bcolors.ENDC, version)

    robo_print("log", welcome_text)


def verify_input(input_path):
    """Before processing anything, verify that our input path exists."""

    if not os.path.exists(input_path):
        robo_print(
            "error", "Input path does not exist. Please try again with a valid input path.")
        sys.exit(1)


def init_recipes():
    """Store information related to each supported AutoPkg recipe type."""

    recipes = (
        {  # index 0
            "name": "download",
            "description": "Downloads an app in whatever format the developer provides."
        },
        {  # index 1
            "name": "munki",
            "description": "Imports into your Munki repository."
        },
        {  # index 2
            "name": "pkg",
            "description": "Creates a standard pkg installer file."
        },
        {  # index 3
            "name": "install",
            "description": "Installs the app on the computer running AutoPkg."
        },
        {  # index 4
            "name": "jss",
            "description": "Imports into your Casper JSS and creates necessary groups, policies, etc."
        },
        {  # index 5
            "name": "absolute",
            "description": "Imports into your Absolute Manage server."
        },
        {  # index 6
            "name": "sccm",
            "description": "Creates a cmmac package for deploying via Microsoft SCCM."
        },
        {  # index 7
            "name": "ds",
            "description": "Imports into your DeployStudio Packages folder."
        }
    )

    # Set default values for all recipe types.
    for recipe in recipes:
        recipe["preferred"] = True
        recipe["existing"] = False
        recipe["buildable"] = False
        recipe["selected"] = True
        recipe["icon_path"] = ""
        recipe["keys"] = {
            "Identifier": "",
            "MinimumVersion": "0.5.0",
            "Input": {},
            "Process": [],
            "Comment": "Generated by Recipe Robot v%s (https://github.com/homebysix/recipe-robot)" % version
        }

    return recipes


def init_prefs(prefs, recipes, args):
    """Read from preferences plist, if it exists."""

    prefs = {}

    # If prefs file exists, try to read from it.
    if os.path.isfile(prefs_file):

        # Open the file.
        try:
            prefs = plistlib.readPlist(prefs_file)

            for recipe in recipes:
                # Load preferred recipe types.
                if recipe["name"] in prefs["RecipeTypes"]:
                    recipe["preferred"] = True
                else:
                    recipe["preferred"] = False

            if args.include_existing is True:
                robo_print(
                    "warning", "Will offer to build recipes even if they already exist on GitHub. Please don't upload duplicate recipes.")

            if args.config is True:
                robo_print("log", "Showing configuration options...")
                prefs = build_prefs(prefs, recipes)

        except Exception:
            print("There was a problem opening the prefs file. "
                  "Building new preferences.")
            prefs = build_prefs(prefs, recipes)

    else:
        robo_print(
            "warning", "No prefs file found. Building new preferences...")
        prefs = build_prefs(prefs, recipes)

    # Record last version number.
    prefs["LastRecipeRobotVersion"] = version

    # Write preferences to plist.
    plistlib.writePlist(prefs, prefs_file)

    return prefs


def build_prefs(prefs, recipes):
    """Prompt user for preferences, then save them back to the plist."""

    # Start recipe count at zero.
    prefs["RecipeCreateCount"] = 0

    # Prompt for and save recipe identifier prefix.
    prefs["RecipeIdentifierPrefix"] = "com.github.homebysix"
    robo_print("log", "\nRecipe identifier prefix")
    robo_print(
        "log", "This is your default identifier, in reverse-domain notation.\n")
    choice = raw_input(
        "[%s]: " % prefs["RecipeIdentifierPrefix"])
    if choice != "":
        prefs["RecipeIdentifierPrefix"] = str(choice).rstrip(". ")

    # Prompt for recipe creation location.
    prefs["RecipeCreateLocation"] = "~/Library/AutoPkg/RecipeOverrides"
    robo_print("log", "\nLocation to save new recipes")
    robo_print(
        "log", "This is where on disk your newly created recipes will be saved.\n")
    choice = raw_input(
        "[%s]: " % prefs["RecipeCreateLocation"])
    if choice != "":
        prefs["RecipeCreateLocation"] = str(choice).rstrip("/ ")

    # Prompt to set recipe types on/off as desired.
    prefs["RecipeTypes"] = []
    robo_print("log", "\nPreferred recipe types")
    robo_print(
        "log", "Choose which recipe types will be offered to you by default.\n")
    # TODO(Elliot): Make this interactive while retaining scrollback.
    # Maybe with curses module?
    while True:
        i = 0
        for recipe in recipes:
            if recipe["preferred"] is False:
                indicator = " "
            else:
                indicator = "*"
            robo_print("log", "  [%s] %s. %s - %s" %
                       (indicator, i, recipe["name"], recipe["description"]))
            i += 1
        robo_print("log", "      A. Enable all recipe types.")
        robo_print("log", "      D. Disable all recipe types.")
        robo_print("log", "      Q. Quit without saving changes.")
        robo_print("log", "      S. Save changes and proceed.")
        choice = raw_input(
            "\nType a number to toggle the corresponding recipe "
            "type between ON [*] and OFF [ ]. When you're satisfied "
            "with your choices, type an \"S\" to save and proceed: ")
        if choice.upper() == "S":
            break
        elif choice.upper() == "A":
            for recipe in recipes:
                recipe["preferred"] = True
        elif choice.upper() == "D":
            for recipe in recipes:
                recipe["preferred"] = False
        elif choice.upper() == "Q":
            sys.exit(0)
        else:
            try:
                if recipes[int(choice)]["preferred"] is False:
                    recipes[int(choice)]["preferred"] = True
                else:
                    recipes[int(choice)]["preferred"] = False
            except Exception:
                robo_print(
                    "warning", "%s is not a valid option. Please try again.\n" % choice)

    # Set "preferred" status of each recipe type according to preferences.
    for recipe in recipes:
        if recipe["preferred"] is True:
            prefs["RecipeTypes"].append(recipe["name"])

    return prefs


def get_sparkle_download_format(sparkle_url):
    """Parse a Sparkle feed URL and return the type of download it produces."""

    # TODO(Elliot): There's got to be a better way than curl.
    cmd = "curl -s %s | awk -F 'url=\"|\"' '/enclosure url/{print $2}' | head -1" % sparkle_url
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if exitcode == 0:
        for format in supported_download_formats:
            if out.endswith(format):
                return format


def increment_recipe_count(prefs):
    """Add 1 to the cumulative count of recipes created by Recipe Robot."""

    prefs["RecipeCreateCount"] += 1
    plistlib.writePlist(prefs, prefs_file)


def get_input_type(input_path):
    """Determine the type of recipe generation needed based on path.

    Args:
        input_path: String path to an app, download recipe, etc.

    Returns:
        Int pseudo-enum value of InputType.
    """

    if input_path.endswith(".app"):
        return InputType.app
    elif input_path.endswith(".download.recipe"):
        return InputType.download_recipe
    elif input_path.endswith(".munki.recipe"):
        return InputType.munki_recipe
    elif input_path.endswith(".pkg.recipe"):
        return InputType.pkg_recipe
    elif input_path.endswith(".install.recipe"):
        return InputType.install_recipe
    elif input_path.endswith(".jss.recipe"):
        return InputType.jss_recipe
    elif input_path.endswith(".absolute.recipe"):
        return InputType.absolute_recipe
    elif input_path.endswith(".sccm.recipe"):
        return InputType.sccm_recipe
    elif input_path.endswith(".ds.recipe"):
        return InputType.ds_recipe


def get_app_description(app_name):
    """Use an app's name to generate a description from MacUpdate.com."""

    cmd = "curl -s http://www.macupdate.com/find/mac/" + app_name + " | awk -F '<|>' '/-shortdescrip/{print $3}' | head -1"
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if exitcode == 0:
        return out
    else:
        robo_print("warning", err)


def create_existing_recipe_list(app_name, recipes):
    """Use autopkg search results to build existing recipe list."""

    robo_print(
        "log", "Searching for existing AutoPkg recipes for %s..." % app_name)
    # TODO(Elliot): Suggest users create GitHub API token to prevent limiting.
    # TODO(Elliot): Do search again without spaces in app names.
    # TODO(Elliot): Match results for apps with "!" in names. (e.g. Paparazzi!)
    cmd = "autopkg search -p %s" % app_name
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if exitcode == 0:
        # TODO(Elliot): There's probably a more efficient way to do this.
        # For each recipe type, see if it exists in the search results.
        for recipe in recipes:
            search_term = "%s.%s.recipe" % (app_name, recipe["name"])
            for line in out.split("\n"):
                if search_term in line:
                    # Set to False by default. If found, set to True.
                    recipe["existing"] = True
    else:
        robo_print("error", err)
        sys.exit(exitcode)


def create_buildable_recipe_list(app_name, recipes, args):
    """Add any preferred recipe types that don't already exist to the buildable
    list.
    """

    for recipe in recipes:
        if args.include_existing is False:
            if recipe["preferred"] is True and recipe["existing"] is False:
                recipe["buildable"] = True
        else:
            if recipe["preferred"] is True:
                recipe["buildable"] = True


# TODO(Shea): Let's have a think about how we're handling input in the
# functions below. In addition to external input (the arguments passed
# when the script is run) we may want to handle internal input too (from
# one recipe type to another). I feel like a recursive function might be
# the way to do this, but it's going to be a complex one. But I think
# recusion will cut down on duplicate logic.

def handle_app_input(input_path, recipes, args):
    """Process an app, gathering required information to create a recipe."""

    # Create variables for every piece of information we might need to create
    # any sort of AutoPkg recipe. Then populate those variables with the info.

    app_name = ""
    robo_print("log", "Validating app...")
    try:
        info_plist = plistlib.readPlist(input_path + "/Contents/Info.plist")
    except Exception:
        robo_print("error", "This doesn't look like a valid app to me.")
        if debug_mode is True:
            raise
        else:
            sys.exit(1)
    if app_name == "":  # Will always be true at this point.
        robo_print("log", "Determining app's name from CFBundleName...")
        try:
            app_name = info_plist["CFBundleName"]
        except KeyError:
            robo_print(
                "warning", "This app doesn't have a CFBundleName. That's OK, we'll keep trying.")
    if app_name == "":
        robo_print("log", "Determining app's name from CFBundleExecutable...")
        try:
            app_name = info_plist["CFBundleExecutable"]
        except KeyError:
            robo_print(
                "warning", "This app doesn't have a CFBundleExecutable. The plot thickens.")
    if app_name == "":
        robo_print("log", "Determining app's name from input path...")
        app_name = os.path.basename(input_path)[:-4]
    robo_print("log", "    App name is: %s" % app_name)

    # Search for existing recipes that match the app's name.
    if args.include_existing is not True:
        create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes, args)

    sparkle_feed = ""
    github_repo = ""
    sourceforge_id = ""
    download_format = ""
    robo_print("log", "Checking for a Sparkle feed in SUFeeduRL...")
    try:
        sparkle_feed = info_plist["SUFeedURL"]
        # TODO(Elliot): Find out what format the Sparkle feed downloads in.
    except Exception:
        robo_print("warning", "No SUFeedURL found in this app's Info.plist.")
    if sparkle_feed == "":
        robo_print(
            "log", "Checking for a Sparkle feed in SUOriginalFeedURL...")
        try:
            sparkle_feed = info_plist["SUOriginalFeedURL"]
            download_format = get_sparkle_download_format(sparkle_feed)
        except Exception:
            robo_print(
                "warning", "No SUOriginalFeedURL found in this app's Info.plist.")
    if sparkle_feed == "":
        robo_print("warning", "No Sparkle feed.")
    else:
        robo_print("log", "    Sparkle feed is: %s" % sparkle_feed)
    if sparkle_feed == "":
        # TODO(Elliot): search_sourceforge_and_github(app_name)
        # if github release
            # github_repo = ""
        # if sourceforge release
            # sourceforge_id = ""
        # TODO(Elliot): Find out what format the GH/SF feed downloads in.
        pass

    min_sys_vers = ""
    robo_print("log", "Checking for minimum OS version requirements...")
    try:
        min_sys_vers = info_plist["LSMinimumSystemVersion"]
        robo_print("log", "    Minimum OS version: %s" % min_sys_vers)
    except Exception:
        robo_print("warning", "No LSMinimumSystemVersion found.")

    icon_path = ""
    robo_print("log", "Looking for app icon...")
    try:
        icon_path = "%s/Contents/Resources/%s" % (
            input_path, info_plist["CFBundleIconFile"])
        robo_print("log", "    Icon found: %s" % icon_path)
    except Exception:
        robo_print(
            "warning", "No CFBundleIconFile found in this app's Info.plist.")

    bundle_id = ""
    robo_print("log", "Getting bundle identifier...")
    try:
        bundle_id = info_plist["CFBundleIdentifier"]
        robo_print("log", "    Bundle ID: %s" % bundle_id)
    except Exception:
        robo_print(
            "warning", "No CFBundleIdentifier found in this app's Info.plist.")

    description = ""
    robo_print("log", "Getting app description from MacUpdate...")
    try:
        description = get_app_description(app_name)
        robo_print("log", "    Description: %s" % description)
    except Exception:
        pass
    if description == "":
        robo_print("warning", "Could not get app description.")

    # TODO(Elliot): Collect other information as required to build recipes.
    #    - Use bundle identifier to locate related helper apps on disk?
    #    - App category... maybe prompt for that if JSS recipe is selected.
    #    - Does the CFBundleShortVersionString provide a usable version number,
    #      or do we need to use CFBundleVersionString instead? (Will be
    #      relevant when producing JSS recipes that might require ext attrib.)

    # Send the information we discovered to the recipe keys.
    for recipe in recipes:
        recipe["keys"]["Input"]["NAME"] = app_name
        if recipe["buildable"] is True:

            if recipe["name"] == "download":
                if sparkle_feed != "":
                    # Example: Cyberduck.download
                    recipe["keys"]["Input"][
                        "SPARKLE_FEED_URL"] = sparkle_feed
                    recipe["keys"]["Process"].append({
                        "Processor": "SparkleUpdateInfoProvider",
                        "Arguments": {
                            "appcast_url": "%SPARKLE_FEED_URL%"
                        }
                    })
                elif github_repo != "":
                    # Example: AutoCaperNBI.download
                    recipe["keys"]["Process"].append({
                        "Processor": "GitHubReleasesInfoProvider",
                        "Arguments": {
                            "github_repo": github_repo
                        }
                    })
                elif sourceforge_id != "":
                    # Example: GrandPerspective.download
                    recipe["keys"]["Input"][
                        "SOURCEFORGE_FILE_PATTERN"] = "%s-[0-9_\.]*\.%s" % (app_name, download_format),
                    recipe["keys"]["Input"][
                        "SOURCEFORGE_PROJECT_ID"] = sourceforge_id
                # end if
                recipe["keys"]["Process"].append({
                    "Processor": "URLDownloader"
                })
                recipe["keys"]["Process"].append({
                    "Processor": "EndOfCheckPhase"
                })

            if recipe["name"] == "munki":
                # Example: Transmit.munki
                # TODO(Elliot): Review inline comments below and adjust.
                recipe["keys"]["Input"]["MUNKI_REPO_SUBDIR"] = ""
                recipe["keys"]["Input"]["pkginfo"] = {
                    "catalogs": ["testing"],
                    # TODO(Elliot): Bug is setting description to None.
                    "description": str(description),
                    "display_name": app_name,
                    "icon_name": "%s.png" % app_name,
                    "minimum_os_version": min_sys_vers,
                    "name": app_name,
                    "unattended_install": True  # Always?
                }
                # Save the icon path for use later with sips command.
                recipe["icon_path"] = icon_path
                recipe["keys"]["Process"].append({
                    "Processor": "MunkiImporter",
                    "Arguments": {
                        "pkg_path": "%RECIPE_CACHE_DIR%/%NAME%." + download_format,
                        "repo_subdirectory": "%MUNKI_REPO_SUBDIR%"
                    }
                })

            if recipe["name"] == "pkg":
                if bundle_id != "":
                    recipe["keys"]["Input"]["PKG_ID"] = bundle_id
                recipe["keys"]["Process"].append({
                    "Processor": "PkgRootCreator",
                    "Arguments": {
                        "pkgroot": "%RECIPE_CACHE_DIR%/%NAME%",
                        "pkgdirs": {
                            "Applications": "0775"
                        }
                    }
                })
                if download_format == "dmg":
                    # Example: AutoPkgr.pkg
                    recipe["keys"]["Process"].append({
                        "Processor": "AppDmgVersioner",
                        "Arguments": {
                            "dmg_path": "%pathname%"
                        }
                    })
                    recipe["keys"]["Process"].append({
                        "Processor": "Copier",
                        "Arguments": {
                            "source_path": "%pathname%/%NAME%.app",
                            "destination_path": "%pkgroot%/Applications/%NAME%.app"
                        }
                    })
                else:  # probably a zip or archive file
                    # Example: AppZapper.pkg
                    recipe["keys"]["Process"].append({
                        "Processor": "Unarchiver",
                        "Arguments": {
                            "archive_path": "%pathname%",
                            "destination_path": "%RECIPE_CACHE_DIR%/%NAME%/Applications"
                        }
                    })
                    recipe["keys"]["Process"].append({
                        "Processor": "Versioner",
                        "Arguments": {
                            "input_plist_path": "%RECIPE_CACHE_DIR%/%NAME%/Applications/%NAME%.app/Contents/Info.plist",
                            "plist_version_key": "CFBundleShortVersionString"
                        }
                    })
                # end if
                recipe["keys"]["Process"].append({
                    "Processor": "PkgCreator",
                    "Arguments": {
                        "pkg_request": {
                            "pkgname": "%NAME%-%version%",
                            "version": "%version%",
                            "id": "%PKG_ID%",
                            "options": "purge_ds_store",
                            "chown": [{
                                "path": "Applications",
                                "user": "root",
                                "group": "admin"
                            }]
                        }
                    }
                })

            if recipe["name"] == "install":
                pass

            if recipe["name"] == "jss":
                recipe["icon_path"] = icon_path
                # description
                pass

            if recipe["name"] == "absolute":
                # TODO(Elliot): What info do we need for this recipe type?
                pass

            if recipe["name"] == "sccm":
                # TODO(Elliot): What info do we need for this recipe type?
                pass

            if recipe["name"] == "ds":
                # TODO(Elliot): What info do we need for this recipe type?
                pass


def handle_download_recipe_input(input_path, recipes, args):
    """Process a download recipe, gathering information useful for building
    other types of recipes.
    """

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    robo_print("log", "Determining app's name from NAME input key...")
    app_name = input_recipe["Input"]["NAME"]
    robo_print("log", "    App name is: %s" % app_name)

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes, args)

    # Get the download file format.
    # TODO(Elliot): Parse the recipe properly. Don't use grep.
    robo_print("log", "Determining download format...")
    parsed_download_format = ""
    for download_format in supported_download_formats:
        cmd = "grep '.%s</string>' '%s'" % (download_format, input_path)
        exitcode, out, err = get_exitcode_stdout_stderr(cmd)
        if exitcode == 0:
            robo_print("log", "    Download format: %s." % download_format)
            parsed_download_format = download_format
            break

    # Send the information we discovered to the recipe keys.
    # This information is type-specific. Universal keys like Identifier are
    # set when the recipe is generated.
    for recipe in recipes:
        recipe["keys"]["Input"]["NAME"] = app_name
        recipe["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipe["buildable"] is True:

            if recipe["name"] == "munki":
                pass

            if recipe["name"] == "pkg":
                if parsed_download_format == "dmg":
                    # Example: GoogleChrome.pkg
                    recipe["Process"].append({
                        "Processor": "AppDmgVersioner",
                        "Arguments": {
                            "dmg_path": "%pathname%"
                        }
                    })
                    recipe["keys"]["Process"].append({
                        "Processor": "PkgRootCreator",
                        "Arguments": {
                            "pkgroot": "%RECIPE_CACHE_DIR%/%NAME%",
                            "pkgdirs": {
                                "Applications": "0775"
                            }
                        }
                    })
                    recipe["keys"]["Process"].append({
                        "Processor": "Copier",
                        "Arguments": {
                            "source_path": "%pathname%/%app_name%",
                            "destination_path": "%pkgroot%/Applications/%app_name%"
                        }
                    })
                    recipe["keys"]["Process"].append({
                        "Processor": "PkgCreator",
                        "Arguments": {
                            "pkg_request": {
                                "pkgname": "%NAME%-%version%",
                                "version": "%version%",
                                # TODO(Elliot): How to determine bundle ID
                                # from the .dmg?
                                "id": "%bundleid%",
                                "options": "purge_ds_store",
                                "chown": ({
                                    "path": "Applications",
                                    "user": "root",
                                    "group": "admin"
                                })
                            }
                        }
                    })
                elif parsed_download_format in ("zip", "tar.gz", "gzip"):
                    # Example: TheUnarchiver.pkg
                    recipe["Process"].append({
                        "Processor": "PkgRootCreator",
                        "Arguments": {
                            "pkgroot": "%RECIPE_CACHE_DIR%/%NAME%",
                            "pkgdirs": {
                                "Applications": "0775"
                            }
                        }
                    })
                    recipe["keys"]["Process"].append({
                        "Processor": "Unarchiver",
                        "Arguments": {
                            "archive_path": "%pathname%",
                            "destination_path": "%pkgroot%/Applications",
                            "purge_destination": True
                        }
                    })
                    recipe["keys"]["Process"].append({
                        "Processor": "Versioner",
                        "Arguments": {
                            "input_plist_path": "%pkgroot%/Applications/The Unarchiver.app/Contents/Info.plist",
                            "plist_version_key": "CFBundleShortVersionString"
                        }
                    })
                    recipe["keys"]["Process"].append({
                        "Processor": "PkgCreator",
                        "Arguments": {
                            "pkg_request": {
                                "pkgname": "%NAME%-%version%",
                                "version": "%version%",
                                # TODO(Elliot): How to determine bundle ID
                                # from the .zip? Get it from Info.plist
                                # above?
                                "id": "%bundleid%",
                                "options": "purge_ds_store",
                                "chown": ({
                                    "path": "Applications",
                                    "user": "root",
                                    "group": "admin"
                                })
                            }
                        }
                    })
                elif parsed_download_format == "pkg":
                    # TODO(Elliot): Do we want to create download recipes for
                    # .pkg downloads, or skip right to the pkg recipe? I vote
                    # for making a download recipe, since the download format
                    # may possibly change someday.
                    pass
                else:
                    # TODO(Elliot): Construct keys for remaining supported
                    # download formats.
                    pass

            if recipe["name"] == "install":
                pass

            if recipe["name"] == "jss":
                pass

            if recipe["name"] == "absolute":
                pass

            if recipe["name"] == "sccm":
                pass

            if recipe["name"] == "ds":
                pass


def handle_munki_recipe_input(input_path, recipes, args):
    """Process a munki recipe, gathering information useful for building other
    types of recipes.
    """

    # Determine whether there's already a download Parent recipe.
    # If not, add it to the list of offered recipe formats.

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    robo_print("log", "Determining app's name from NAME input key...")
    app_name = input_recipe["Input"]["NAME"]
    robo_print("log", "    App name is: %s" % app_name)

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes, args)

    # If this munki recipe both downloads and imports the app, we
    # should offer to build a discrete download recipe with only
    # the appropriate sections of the munki recipe.

    # Offer to build pkg, jss, etc.

    # TODO(Elliot): Think about whether we want to dig into OS requirements,
    # blocking applications, etc when building munki recipes. I vote
    # yes, but it's probably not going to be easy.

    # Send the information we discovered to the recipe keys.
    for recipe in recipes:
        recipe["keys"]["Input"]["NAME"] = app_name
        recipe["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipe["buildable"] is True:

            if recipe["name"] == "download":
                pass

            if recipe["name"] == "pkg":
                pass

            if recipe["name"] == "install":
                pass

            if recipe["name"] == "jss":
                pass

            if recipe["name"] == "absolute":
                pass

            if recipe["name"] == "sccm":
                pass

            if recipe["name"] == "ds":
                pass


def handle_pkg_recipe_input(input_path, recipes, args):
    """Process a pkg recipe, gathering information useful for building other
    types of recipes.
    """

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    robo_print("log", "Determining app's name from NAME input key...")
    app_name = input_recipe["Input"]["NAME"]
    robo_print("log", "    App name is: %s" % app_name)

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes, args)

    # Check to see whether the recipe has a download recipe as its parent. If
    # not, offer to build a discrete download recipe.

    # Send the information we discovered to the recipe keys.
    for recipe in recipes:
        recipe["keys"]["Input"]["NAME"] = app_name
        recipe["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipe["buildable"] is True:

            if recipe["name"] == "download":
                pass

            if recipe["name"] == "munki":
                pass

            if recipe["name"] == "install":
                pass

            if recipe["name"] == "jss":
                pass

            if recipe["name"] == "absolute":
                pass

            if recipe["name"] == "sccm":
                pass

            if recipe["name"] == "ds":
                pass


def handle_install_recipe_input(input_path, recipes, args):
    """Process an install recipe, gathering information useful for building
    other types of recipes.
    """

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    robo_print("log", "Determining app's name from NAME input key...")
    app_name = input_recipe["Input"]["NAME"]
    robo_print("log", "    App name is: %s" % app_name)

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes, args)

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Send the information we discovered to the recipe keys.
    for recipe in recipes:
        recipe["keys"]["Input"]["NAME"] = app_name
        recipe["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipe["buildable"] is True:

            if recipe["name"] == "download":
                pass

            if recipe["name"] == "munki":
                pass

            if recipe["name"] == "pkg":
                pass

            if recipe["name"] == "jss":
                pass

            if recipe["name"] == "absolute":
                pass

            if recipe["name"] == "sccm":
                pass

            if recipe["name"] == "ds":
                pass


def handle_jss_recipe_input(input_path, recipes, args):
    """Process a jss recipe, gathering information useful for building other
    types of recipes.
    """

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    robo_print("log", "Determining app's name from NAME input key...")
    app_name = input_recipe["Input"]["NAME"]
    robo_print("log", "    App name is: %s" % app_name)

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes, args)

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Send the information we discovered to the recipe keys.
    for recipe in recipes:
        recipe["keys"]["Input"]["NAME"] = app_name
        recipe["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipe["buildable"] is True:

            if recipe["name"] == "download":
                pass

            if recipe["name"] == "munki":
                pass

            if recipe["name"] == "pkg":
                pass

            if recipe["name"] == "install":
                pass

            if recipe["name"] == "absolute":
                pass

            if recipe["name"] == "sccm":
                pass

            if recipe["name"] == "ds":
                pass


def handle_absolute_recipe_input(input_path, recipes, args):
    """Process an absolute recipe, gathering information useful for building
    other types of recipes.
    """

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    robo_print("log", "Determining app's name from NAME input key...")
    app_name = input_recipe["Input"]["NAME"]
    robo_print("log", "    App name is: %s" % app_name)

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes, args)

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Send the information we discovered to the recipe keys.
    for recipe in recipes:
        recipe["keys"]["Input"]["NAME"] = app_name
        recipe["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipe["buildable"] is True:

            if recipe["name"] == "download":
                pass

            if recipe["name"] == "munki":
                pass

            if recipe["name"] == "pkg":
                pass

            if recipe["name"] == "install":
                pass

            if recipe["name"] == "jss":
                pass

            if recipe["name"] == "sccm":
                pass

            if recipe["name"] == "ds":
                pass


def handle_sccm_recipe_input(input_path, recipes, args):
    """Process a sccm recipe, gathering information useful for building other
    types of recipes.
    """

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    robo_print("log", "Determining app's name from NAME input key...")
    app_name = input_recipe["Input"]["NAME"]
    robo_print("log", "    App name is: %s" % app_name)

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes, args)

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Send the information we discovered to the recipe keys.
    for recipe in recipes:
        recipe["keys"]["Input"]["NAME"] = app_name
        recipe["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipe["buildable"] is True:

            if recipe["name"] == "download":
                pass

            if recipe["name"] == "munki":
                pass

            if recipe["name"] == "pkg":
                pass

            if recipe["name"] == "install":
                pass

            if recipe["name"] == "jss":
                pass

            if recipe["name"] == "absolute":
                pass

            if recipe["name"] == "ds":
                pass


def handle_ds_recipe_input(input_path, recipes, args):
    """Process a ds recipe, gathering information useful for building other
    types of recipes.
    """

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    robo_print("log", "Determining app's name from NAME input key...")
    app_name = input_recipe["Input"]["NAME"]
    robo_print("log", "    App name is: %s" % app_name)

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes, args)

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Send the information we discovered to the recipe keys.
    for recipe in recipes:
        recipe["keys"]["Input"]["NAME"] = app_name
        recipe["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipe["buildable"] is True:

            if recipe["name"] == "download":
                pass

            if recipe["name"] == "munki":
                pass

            if recipe["name"] == "pkg":
                pass

            if recipe["name"] == "install":
                pass

            if recipe["name"] == "jss":
                pass

            if recipe["name"] == "absolute":
                pass

            if recipe["name"] == "sccm":
                pass


def search_sourceforge_and_github(app_name):
    """For apps that do not have a Sparkle feed, try to locate their project
    information on either SourceForge or GitHub so that the corresponding
    URL provider processors can be used to generate a recipe.
    """

    # TODO(Shea): Search on SourceForge for the project.
    #     If found, pass the project ID back to the recipe generator.
    #     To get ID: https://gist.github.com/homebysix/9640c6a6eecff82d3b16
    # TODO(Shea): Search on GitHub for the project.
    #     If found, pass the username and repo back to the recipe generator.


def select_recipes_to_generate(recipes):
    """Display menu that allows user to select which recipes to create."""

    buildable_count = 0
    for recipe in recipes:
        if recipe["buildable"] is True:
            buildable_count += 1

    if buildable_count < 1:
        robo_print("error", "Sorry, there are no recipe types to generate.")
        sys.exit(0)

    robo_print("log", "\nPlease select which recipes you'd like to create:\n")

    # TODO(Elliot): Make this interactive while retaining scrollback.
    # Maybe with curses module?
    while True:
        i = 0
        for recipe in recipes:
            indicator = " "
            if (recipe["preferred"] is True and recipe["buildable"] is True):
                if recipe["selected"] is True:
                    indicator = "*"
                robo_print(
                    "log", "  [%s] %s. %s - %s" % (indicator, i, recipe["name"], recipe["description"]))
            i += 1
        robo_print("log", "      A. Enable all recipe types.")
        robo_print("log", "      D. Disable all recipe types.")
        robo_print("log", "      Q. Quit without saving changes.")
        robo_print("log", "      S. Save changes and proceed.")
        choice = raw_input(
            "\nType a number to toggle the corresponding recipe "
            "type between ON [*] and OFF [ ]. When you're satisfied "
            "with your choices, type an \"S\" to save and proceed: ")
        robo_print("log", "")
        if choice.upper() == "S":
            break
        elif choice.upper() == "A":
            for recipe in recipes:
                recipe["selected"] = True
        elif choice.upper() == "D":
            for recipe in recipes:
                recipe["selected"] = False
        elif choice.upper() == "Q":
            sys.exit(0)
        else:
            try:
                if recipes[int(choice)]["selected"] is False:
                    recipes[int(choice)]["selected"] = True
                else:
                    recipes[int(choice)]["selected"] = False
            except Exception:
                robo_print(
                    "error", "%s is not a valid option. Please try again.\n" % choice)


def generate_selected_recipes(prefs, recipes):
    """Generate the selected types of recipes."""

    robo_print("log", "\nGenerating selected recipes...")
    # TODO(Elliot): Say "no recipes selected" if appropriate.

    for recipe in recipes:
        if (recipe["preferred"] is True and recipe["buildable"] is True and recipe["selected"] is True):

            # Set the identifier of the recipe.
            recipe["keys"]["Identifier"] = "%s.%s.%s" % (
                prefs["RecipeIdentifierPrefix"], recipe["name"], recipe["keys"]["Input"]["NAME"])

            # Set type-specific keys.
            if recipe["name"] == "download":

                recipe["keys"]["Description"] = "Downloads the latest version of %s." % recipe[
                    "keys"]["Input"]["NAME"]

                # TODO(Elliot): Read flag for GH/SF releases. If the flag is
                # present, copy relevant processors to the recipe output
                # folder.

            elif recipe["name"] == "munki":

                recipe["keys"]["Description"] = "Imports the latest version of %s into Munki." % recipe[
                    "keys"]["Input"]["NAME"]

                if recipe["icon_path"] != "":
                    png_path = "%s/%s.png" % (
                        prefs["RecipeCreateLocation"], recipe["keys"]["Input"]["NAME"])
                    extract_app_icon(recipe["icon_path"], png_path)

            elif recipe["name"] == "pkg":

                recipe["keys"]["Description"] = "Downloads the latest version of %s and creates an installer package." % recipe[
                    "keys"]["Input"]["NAME"]
                recipe["keys"]["ParentRecipe"] = "%s.download.%s" % (prefs["RecipeIdentifierPrefix"], recipe[
                    "keys"]["Input"]["NAME"])

            elif recipe["name"] == "install":

                recipe["keys"]["Description"] = "Installs the latest version of %s." % recipe[
                    "keys"]["Input"]["NAME"]

            elif recipe["name"] == "jss":

                recipe["keys"]["Description"] = "Imports the latest version of %s into your JSS." % recipe[
                    "keys"]["Input"]["NAME"]

                if recipe["icon_path"] != "":
                    png_path = "%s/%s.png" % (
                        prefs["RecipeCreateLocation"], recipe["keys"]["Input"]["NAME"])
                    extract_app_icon(recipe["icon_path"], png_path)

            elif recipe["name"] == "absolute":

                recipe["keys"]["Description"] = "Imports the latest version of %s into Absolute Manage." % recipe[
                    "keys"]["Input"]["NAME"]

            elif recipe["name"] == "sccm":

                recipe["keys"]["Description"] = "Downloads the latest version of %s and creates a cmmac package for deploying via Microsoft SCCM." % recipe[
                    "keys"]["Input"]["NAME"]

            elif recipe["name"] == "ds":

                recipe["keys"]["Description"] = "Imports the latest version of %s into DeployStudio." % recipe[
                    "keys"]["Input"]["NAME"]
            else:
                robo_print(
                    "error", "I don't know how to generate a recipe of type %s." % recipe["name"])

            # Write the recipe to disk.
            filename = "%s.%s.recipe" % (
                recipe["keys"]["Input"]["NAME"], recipe["name"])
            write_recipe_file(filename, prefs, recipe["keys"])
            robo_print("log", "    %s/%s" %
                       (prefs["RecipeCreateLocation"], filename))


def create_dest_dirs(path):
    """Creates the path to the recipe export location, if it doesn't exist."""

    dest_dir = os.path.expanduser(path)
    if not os.path.exists(dest_dir):
        try:
            os.makedirs(dest_dir)
        except Exception:
            robo_print("error", "Unable to create directory at %s." % dest_dir)
            if debug_mode:
                raise
            else:
                sys.exit(1)


def extract_app_icon(icon_path, png_path):
    """Convert the app's icns file to 300x300 png at the specified path. 300x300 is Munki's preferred size, and 128x128 is Casper's preferred size, as of 2015-08-01.
    """

    png_path_absolute = os.path.expanduser(png_path)
    create_dest_dirs(os.path.dirname(png_path_absolute))

    if not os.path.exists(png_path_absolute):
        cmd = "sips -s format png \"%s.icns\" --out \"%s\" --resampleHeightWidthMax 300" % (
            icon_path, png_path_absolute)
        robo_print("debug", "Icon extraction command:")
        robo_print("debug", cmd)
        exitcode, out, err = get_exitcode_stdout_stderr(cmd)
        if exitcode == 0:
            robo_print("log", "    %s" % png_path)
        else:
            robo_print("error", err)


def write_recipe_file(filename, prefs, keys):
    """Write a generated recipe to disk."""

    dest_dir = os.path.expanduser(prefs["RecipeCreateLocation"])
    create_dest_dirs(dest_dir)

    # TODO(Elliot): Warning if a file already exists here.

    dest_path = "%s/%s" % (dest_dir, filename)
    plistlib.writePlist(keys, dest_path)
    increment_recipe_count(prefs)


def congratulate(prefs):
    """Display a friendly congratulatory message upon creating recipes."""

    congrats_msg = (
        "That's awesome!",
        "Amazing.",
        "Well done!",
        "Good on ya!",
        "Thanks!",
        "Pretty cool, right?",
        "You rock star, you.",
        "Fantastic."
    )
    if prefs["RecipeCreateCount"] == 1:
        robo_print(
            "log", "\nYou've now created your first recipe with Recipe Robot. Congratulations!\n")
    elif prefs["RecipeCreateCount"] > 1:
        robo_print("log", "\nYou've now created %s recipes with Recipe Robot. %s\n" % (
            prefs["RecipeCreateCount"], random.choice(congrats_msg)))


# TODO(Elliot): Make main() shorter. Just a flowchart for the logic.
def main():
    """Make the magic happen."""

    try:
        print_welcome_text()

        argparser = build_argument_parser()
        args = argparser.parse_args()

        # Temporary argument handling
        input_path = args.input_path
        input_path = input_path.rstrip("/ ")
        verify_input(input_path)

        # Create the master recipe information list.
        recipes = init_recipes()

        # Read or create the user preferences.
        prefs = {}
        prefs = init_prefs(prefs, recipes, args)

        input_type = get_input_type(input_path)
        robo_print("log", "\nProcessing %s ..." % input_path)

        # Orchestrate helper functions to handle input_path's "type".
        if input_type is InputType.app:
            handle_app_input(input_path, recipes, args)
        elif input_type is InputType.download_recipe:
            handle_download_recipe_input(input_path, recipes, args)
        elif input_type is InputType.munki_recipe:
            handle_munki_recipe_input(input_path, recipes, args)
        elif input_type is InputType.pkg_recipe:
            handle_pkg_recipe_input(input_path, recipes, args)
        elif input_type is InputType.install_recipe:
            handle_install_recipe_input(input_path, recipes, args)
        elif input_type is InputType.jss_recipe:
            handle_jss_recipe_input(input_path, recipes, args)
        elif input_type is InputType.absolute_recipe:
            handle_absolute_recipe_input(input_path, recipes, args)
        elif input_type is InputType.sccm_recipe:
            handle_sccm_recipe_input(input_path, recipes, args)
        elif input_type is InputType.ds_recipe:
            handle_ds_recipe_input(input_path, recipes, args)
        else:
            robo_print("error", "I haven't been trained on how to handle "
                       "this input path:\n    %s" % input_path)
            sys.exit(1)

        if debug_mode is True:
            robo_print(
                "debug", "ARGUMENT LIST:\n" + pprint.pformat(args) + "\n")
            robo_print("debug", "SUPPORTED DOWNLOAD FORMATS:\n" +
                       pprint.pformat(supported_download_formats) + "\n")
            robo_print(
                "debug", "PREFERENCES:\n" + pprint.pformat(prefs) + "\n")
            robo_print(
                "debug", "CURRENT RECIPE INFORMATION:\n" + pprint.pformat(recipes) + "\n")

        # Prompt the user with the available recipes types and let them choose.
        select_recipes_to_generate(recipes)

        # Create recipes for the recipe types that were selected above.
        generate_selected_recipes(prefs, recipes)

        # Pat on the back!
        congratulate(prefs)

    # Make sure to reset the terminal color with our dying breath.
    except (KeyboardInterrupt, SystemExit):
        print bcolors.ENDC
        print "Thanks for using Recipe Robot!"


if __name__ == '__main__':
    main()
