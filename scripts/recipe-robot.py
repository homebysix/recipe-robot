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
                       [--ignore-existing] [--config]
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
  --ignore-existing     Offer to generate recipes even if one already exists
                        on GitHub.
  --config              Adjust Recipe Robot preferences prior to generating
                        recipes.
"""


import argparse
import os.path
import plistlib
from pprint import pprint
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

# TODO(Elliot): Send bcolors.ENDC upon exception or keyboard interrupt.
# Otherwise people's terminal windows might get stuck in purple mode!


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
        "--ignore-existing",
        action="store_true",
        help="Offer to generate recipes even if one already exists on GitHub.")
    parser.add_argument(
        "--config",
        action="store_true",
        help="Adjust Recipe Robot preferences prior to generating recipes.")
    parser.print_help()
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

    print welcome_text


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
            "description": "Imports into your SCCM server."
        },
        {  # index 7
            "name": "ds",
            "description": "Imports into your DeployStudio Packages folder."
        }
    )

    # Set default values for all recipe types.
    for i in range(0, len(recipes)):
        recipes[i]["preferred"] = True
        recipes[i]["existing"] = False
        recipes[i]["buildable"] = False
        recipes[i]["selected"] = True
        recipes[i]["icon_path"] = ""
        recipes[i]["keys"] = {
            "Identifier": "",
            "MinimumVersion": "0.5.0",
            "Input": {},
            "Process": [],
            "Comment": "Generated by Recipe Robot v%s (https://github.com/homebysix/recipe-robot)" % version
        }

    return recipes


def init_prefs(prefs, recipes):
    """Read from preferences plist, if it exists."""

    prefs = {}

    # If prefs file exists, try to read from it.
    if os.path.isfile(prefs_file):

        # Open the file.
        try:
            prefs = plistlib.readPlist(prefs_file)
            for i in range(0, len(recipes)):
                # Load preferred recipe types.
                if recipes[i]["name"] in prefs["RecipeTypes"]:
                    recipes[i]["preferred"] = True
                else:
                    recipes[i]["preferred"] = False

        except Exception:
            print("There was a problem opening the prefs file. "
                  "Building new preferences.")
            prefs = build_prefs(prefs, recipes)

    else:
        print "No prefs file found. Building new preferences..."
        prefs = build_prefs(prefs, recipes)

    # Record last version number.
    prefs["LastRecipeRobotVersion"] = version

    # Write preferences to plist.
    plistlib.writePlist(prefs, prefs_file)

    return prefs


def build_prefs(prefs, recipes):
    """Prompt user for preferences, then save them back to the plist."""

    # TODO(Elliot): Make this something users can come back to and modify,
    # rather than just a first-run thing.

    # Start recipe count at zero.
    prefs["RecipeCreateCount"] = 0

    # Prompt for and save recipe identifier prefix.
    prefs["RecipeIdentifierPrefix"] = "com.github.homebysix"
    print "\nRecipe identifier prefix"
    print "This is your default identifier, in reverse-domain notation.\n"
    choice = raw_input(
        "[%s]: " % prefs["RecipeIdentifierPrefix"])
    if choice != "":
        prefs["RecipeIdentifierPrefix"] = str(choice).rstrip(". ")

    # Prompt for recipe creation location.
    prefs["RecipeCreateLocation"] = "~/Library/AutoPkg/RecipeOverrides"
    print "\nLocation to save new recipes"
    print "This is where on disk your newly created recipes will be saved.\n"
    choice = raw_input(
        "[%s]: " % prefs["RecipeCreateLocation"])
    if choice != "":
        prefs["RecipeCreateLocation"] = str(choice).rstrip("/ ")

    # Prompt to set recipe types on/off as desired.
    prefs["RecipeTypes"] = []
    print "\nPreferred recipe types"
    print "Choose which recipe types will be offered to you by default.\n"
    # TODO(Elliot): Make this interactive while retaining scrollback.
    # Maybe with curses module?
    while True:
        for i in range(0, len(recipes)):
            if recipes[i]["preferred"] is False:
                indicator = " "
            else:
                indicator = "*"
            print "  [%s] %s. %s - %s" % (indicator, i, recipes[i]["name"], recipes[i]["description"])
        choice = raw_input(
            "\nType a number to toggle the corresponding recipe "
            "type between ON [*] and OFF [ ]. When you're satisfied "
            "with your choices, type an \"S\" to save and proceed: ")
        if choice.upper() == "S":
            break
        else:
            try:
                if recipes[int(choice)]["preferred"] is False:
                    recipes[int(choice)]["preferred"] = True
                else:
                    recipes[int(choice)]["preferred"] = False
            except Exception:
                print "%s%s is not a valid option. Please try again.%s\n" % (bcolors.ERROR, choice, bcolors.ENDC)

    # Set "preferred" status of each recipe type according to preferences.
    for i in range(0, len(recipes)):
        if recipes[i]["preferred"] is True:
            prefs["RecipeTypes"].append(recipes[i]["name"])

    return prefs


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


def create_existing_recipe_list(app_name, recipes):
    """Use autopkg search results to build existing recipe list."""

    # TODO(Elliot): Suggest users create GitHub API token to prevent limiting.
    # TODO(Elliot): Do search again without spaces in app names.
    # TODO(Elliot): Match results for apps with "!" in names. (e.g. Paparazzi!)
    cmd = "autopkg search -p %s" % app_name
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if exitcode == 0:
        # TODO(Elliot): There's probably a more efficient way to do this.
        # For each recipe type, see if it exists in the search results.
        for i in range(0, len(recipes)):
            search_term = "%s.%s.recipe" % (app_name, recipes[i]["name"])
            for line in out.split("\n"):
                if search_term in line:
                    # Set to False by default. If found, set to True.
                    recipes[i]["existing"] = True
    else:
        print err
        sys.exit(exitcode)


def create_buildable_recipe_list(app_name, recipes):
    """Add any preferred recipe types that don't already exist to the buildable
    list.
    """

    for i in range(0, len(recipes)):
        # if recipes[i]["existing"] is False:
        if True:  # DEBUG
            if recipes[i]["preferred"] is True:
                recipes[i]["buildable"] = True


# TODO(Shea): Let's have a think about how we're handling input in the
# functions below. In addition to external input (the arguments passed
# when the script is run) we may want to handle internal input too (from
# one recipe type to another). I feel like a recursive function might be
# the way to do this, but it's going to be a complex one. But I think
# recusion will cut down on duplicate logic.

def handle_app_input(input_path, recipes):
    """Process an app, gathering required information to create a recipe."""

    app_name = ""
    sparkle_feed = ""
    min_sys_vers = ""
    icon_path = ""

    print "Validating app..."
    try:
        info_plist = plistlib.readPlist(input_path + "/Contents/Info.plist")
    except Exception:
        print "This doesn't look like a valid app to me."
        if debug_mode is True:
            raise
        else:
            sys.exit(1)

    if app_name == "":  # Will always be true at this point.
        print "Determining app's name from CFBundleName..."
        try:
            app_name = info_plist["CFBundleName"]
        except KeyError:
            print "    This app doesn't have a CFBundleName. That's OK, we'll keep trying."

    if app_name == "":
        print "Determining app's name from CFBundleExecutable..."
        try:
            app_name = info_plist["CFBundleExecutable"]
        except KeyError:
            print "    This app doesn't have a CFBundleExecutable. The plot thickens."

    if app_name == "":
        print "Determining app's name from input path..."
        app_name = os.path.basename(input_path)[:-4]

    print "    App name is: %s" % app_name

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes)

    print "Checking for a Sparkle feed in SUFeeduRL..."
    try:
        sparkle_feed = info_plist["SUFeedURL"]
        # TODO(Elliot): Find out what format the Sparkle feed downloads in.
    except Exception:
        print "    No SUFeedURL found in this app's Info.plist."

    if sparkle_feed == "":
        print "Checking for a Sparkle feed in SUOriginalFeedURL..."
        try:
            sparkle_feed = info_plist["SUOriginalFeedURL"]
            # TODO(Elliot): Find out what format the Sparkle feed downloads in.
        except Exception:
            print "    No SUOriginalFeedURL found in this app's Info.plist."

    if sparkle_feed == "":
        print "    No Sparkle feed."
    else:
        print "    Sparkle feed is: %s" % sparkle_feed

    # TODO(Elliot): search_sourceforge_and_github(app_name)
    # TODO(Elliot): Find out what format the GH/SF feed downloads in.

    print "Checking for minimum OS version requirements..."
    try:
        min_sys_vers = info_plist["LSMinimumSystemVersion"]
        print "    Minimum OS version: %s" % min_sys_vers
    except Exception:
        print "    No LSMinimumSystemVersion found."

    print "Looking for app icon..."
    try:
        icon_path = "%s/Contents/Resources/%s" % (input_path, info_plist["CFBundleIconFile"])
        print "    Icon found: %s" % icon_path
    except Exception:
        print "    No CFBundleIconFile found in this app's Info.plist."

    # TODO(Elliot): Collect other information as required to build recipes.

    # Send the information we discovered to the recipe keys.
    for i in range(0, len(recipes)):
        recipes[i]["keys"]["Input"]["NAME"] = app_name
        if recipes[i]["buildable"] is True:

            if recipes[i]["name"] == "download":
                if sparkle_feed != "":
                    # Example: Cyberduck.download
                    recipes[i]["keys"]["Input"][
                        "SPARKLE_FEED_URL"] = sparkle_feed
                    recipes[i]["keys"]["Process"].append({
                        "Processor": "SparkleUpdateInfoProvider",
                        "Arguments": {
                            "appcast_url": "%SPARKLE_FEED_URL%"
                        }
                    })
                    recipes[i]["keys"]["Process"].append({
                        "Processor": "URLDownloader"
                    })
                    recipes[i]["keys"]["Process"].append({
                        "Processor": "EndOfCheckPhase"
                    })

            if recipes[i]["name"] == "munki":
                recipes[i]["keys"]["Input"]["pkginfo"] = {}
                recipes[i]["keys"]["Input"]["pkginfo"]["minimum_os_version"] = min_sys_vers
                recipes[i]["icon_path"] = icon_path

            if recipes[i]["name"] == "pkg":
                pass

            if recipes[i]["name"] == "install":
                pass

            if recipes[i]["name"] == "jss":
                recipes[i]["icon_path"] = icon_path
                pass

            if recipes[i]["name"] == "absolute":
                # TODO(Elliot): What info do we need for this recipe type?
                pass

            if recipes[i]["name"] == "sccm":
                # TODO(Elliot): What info do we need for this recipe type?
                pass

            if recipes[i]["name"] == "ds":
                # TODO(Elliot): What info do we need for this recipe type?
                pass


def handle_download_recipe_input(input_path, recipes):
    """Process a download recipe, gathering information useful for building
    other types of recipes.
    """

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    print "Determining app's name from NAME input key..."
    app_name = input_recipe["Input"]["NAME"]
    print "    App name is: %s" % app_name

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes)

    # Get the download file format.
    # TODO(Elliot): Parse the recipe properly. Don't use grep.
    print "Determining download format..."
    parsed_download_format = ""
    for download_format in supported_download_formats:
        cmd = "grep '.%s</string>' '%s'" % (download_format, input_path)
        exitcode, out, err = get_exitcode_stdout_stderr(cmd)
        if exitcode == 0:
            print "    Download format: %s." % download_format
            parsed_download_format = download_format
            break

    # Send the information we discovered to the recipe keys.
    # This information is type-specific. Universal keys like Identifier are
    # set when the recipe is generated.
    for i in range(0, len(recipes)):
        recipes[i]["keys"]["Input"]["NAME"] = app_name
        recipes[i]["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipes[i]["buildable"] is True:

            if recipes[i]["name"] == "munki":
                pass

            if recipes[i]["name"] == "pkg":
                if parsed_download_format == "dmg":
                    # Example: GoogleChrome.pkg
                    recipes[i]["Process"].append({
                        "Processor": "AppDmgVersioner",
                        "Arguments": {
                            "dmg_path": "%pathname%"
                        }
                    })
                    recipes[i]["keys"]["Process"].append({
                        "Processor": "PkgRootCreator",
                        "Arguments": {
                            "pkgroot": "%RECIPE_CACHE_DIR%/%NAME%",
                            "pkgdirs": {
                                "Applications": "0775"
                            }
                        }
                    })
                    recipes[i]["keys"]["Process"].append({
                        "Processor": "Copier",
                        "Arguments": {
                            "source_path": "%pathname%/%app_name%",
                            "destination_path": "%pkgroot%/Applications/%app_name%"
                        }
                    })
                    recipes[i]["keys"]["Process"].append({
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
                    recipes[i]["Process"].append({
                        "Processor": "PkgRootCreator",
                        "Arguments": {
                            "pkgroot": "%RECIPE_CACHE_DIR%/%NAME%",
                            "pkgdirs": {
                                "Applications": "0775"
                            }
                        }
                    })
                    recipes[i]["keys"]["Process"].append({
                        "Processor": "Unarchiver",
                        "Arguments": {
                            "archive_path": "%pathname%",
                            "destination_path": "%pkgroot%/Applications",
                            "purge_destination": True
                        }
                    })
                    recipes[i]["keys"]["Process"].append({
                        "Processor": "Versioner",
                        "Arguments": {
                            "input_plist_path": "%pkgroot%/Applications/The Unarchiver.app/Contents/Info.plist",
                            "plist_version_key": "CFBundleShortVersionString"
                        }
                    })
                    recipes[i]["keys"]["Process"].append({
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

            if recipes[i]["name"] == "install":
                pass

            if recipes[i]["name"] == "jss":
                pass

            if recipes[i]["name"] == "absolute":
                pass

            if recipes[i]["name"] == "sccm":
                pass

            if recipes[i]["name"] == "ds":
                pass


def handle_munki_recipe_input(input_path, recipes):
    """Process a munki recipe, gathering information useful for building other
    types of recipes."""

    # Determine whether there's already a download Parent recipe.
    # If not, add it to the list of offered recipe formats.

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    print "Determining app's name from NAME input key..."
    app_name = input_recipe["Input"]["NAME"]
    print "    App name is: %s" % app_name

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes)

    # If this munki recipe both downloads and imports the app, we
    # should offer to build a discrete download recipe with only
    # the appropriate sections of the munki recipe.

    # Offer to build pkg, jss, etc.

    # TODO(Elliot): Think about whether we want to dig into OS requirements,
    # blocking applications, etc when building munki recipes. I vote
    # yes, but it's probably not going to be easy.

    # Send the information we discovered to the recipe keys.
    for i in range(0, len(recipes)):
        recipes[i]["keys"]["Input"]["NAME"] = app_name
        recipes[i]["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipes[i]["buildable"] is True:

            if recipes[i]["name"] == "download":
                pass

            if recipes[i]["name"] == "pkg":
                pass

            if recipes[i]["name"] == "install":
                pass

            if recipes[i]["name"] == "jss":
                pass

            if recipes[i]["name"] == "absolute":
                pass

            if recipes[i]["name"] == "sccm":
                pass

            if recipes[i]["name"] == "ds":
                pass


def handle_pkg_recipe_input(input_path, recipes):
    """Process a pkg recipe, gathering information useful for building other
    types of recipes."""

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    print "Determining app's name from NAME input key..."
    app_name = input_recipe["Input"]["NAME"]
    print "    App name is: %s" % app_name

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes)

    # Check to see whether the recipe has a download recipe as its parent. If
    # not, offer to build a discrete download recipe.

    # Send the information we discovered to the recipe keys.
    for i in range(0, len(recipes)):
        recipes[i]["keys"]["Input"]["NAME"] = app_name
        recipes[i]["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipes[i]["buildable"] is True:

            if recipes[i]["name"] == "download":
                pass

            if recipes[i]["name"] == "munki":
                pass

            if recipes[i]["name"] == "install":
                pass

            if recipes[i]["name"] == "jss":
                pass

            if recipes[i]["name"] == "absolute":
                pass

            if recipes[i]["name"] == "sccm":
                pass

            if recipes[i]["name"] == "ds":
                pass


def handle_install_recipe_input(input_path, recipes):
    """Process an install recipe, gathering information useful for building
    other types of recipes."""

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    print "Determining app's name from NAME input key..."
    app_name = input_recipe["Input"]["NAME"]
    print "    App name is: %s" % app_name

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes)

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Send the information we discovered to the recipe keys.
    for i in range(0, len(recipes)):
        recipes[i]["keys"]["Input"]["NAME"] = app_name
        recipes[i]["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipes[i]["buildable"] is True:

            if recipes[i]["name"] == "download":
                pass

            if recipes[i]["name"] == "munki":
                pass

            if recipes[i]["name"] == "pkg":
                pass

            if recipes[i]["name"] == "jss":
                pass

            if recipes[i]["name"] == "absolute":
                pass

            if recipes[i]["name"] == "sccm":
                pass

            if recipes[i]["name"] == "ds":
                pass


def handle_jss_recipe_input(input_path, recipes):
    """Process a jss recipe, gathering information useful for building other
    types of recipes."""

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    print "Determining app's name from NAME input key..."
    app_name = input_recipe["Input"]["NAME"]
    print "    App name is: %s" % app_name

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes)

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Send the information we discovered to the recipe keys.
    for i in range(0, len(recipes)):
        recipes[i]["keys"]["Input"]["NAME"] = app_name
        recipes[i]["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipes[i]["buildable"] is True:

            if recipes[i]["name"] == "download":
                pass

            if recipes[i]["name"] == "munki":
                pass

            if recipes[i]["name"] == "pkg":
                pass

            if recipes[i]["name"] == "install":
                pass

            if recipes[i]["name"] == "absolute":
                pass

            if recipes[i]["name"] == "sccm":
                pass

            if recipes[i]["name"] == "ds":
                pass


def handle_absolute_recipe_input(input_path, recipes):
    """Process an absolute recipe, gathering information useful for building
    other types of recipes.
    """

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    print "Determining app's name from NAME input key..."
    app_name = input_recipe["Input"]["NAME"]
    print "    App name is: %s" % app_name

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes)

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Send the information we discovered to the recipe keys.
    for i in range(0, len(recipes)):
        recipes[i]["keys"]["Input"]["NAME"] = app_name
        recipes[i]["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipes[i]["buildable"] is True:

            if recipes[i]["name"] == "download":
                pass

            if recipes[i]["name"] == "munki":
                pass

            if recipes[i]["name"] == "pkg":
                pass

            if recipes[i]["name"] == "install":
                pass

            if recipes[i]["name"] == "jss":
                pass

            if recipes[i]["name"] == "sccm":
                pass

            if recipes[i]["name"] == "ds":
                pass


def handle_sccm_recipe_input(input_path, recipes):
    """Process a sccm recipe, gathering information useful for building other
    types of recipes."""

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    print "Determining app's name from NAME input key..."
    app_name = input_recipe["Input"]["NAME"]
    print "    App name is: %s" % app_name

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes)

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Send the information we discovered to the recipe keys.
    for i in range(0, len(recipes)):
        recipes[i]["keys"]["Input"]["NAME"] = app_name
        recipes[i]["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipes[i]["buildable"] is True:

            if recipes[i]["name"] == "download":
                pass

            if recipes[i]["name"] == "munki":
                pass

            if recipes[i]["name"] == "pkg":
                pass

            if recipes[i]["name"] == "install":
                pass

            if recipes[i]["name"] == "jss":
                pass

            if recipes[i]["name"] == "absolute":
                pass

            if recipes[i]["name"] == "ds":
                pass


def handle_ds_recipe_input(input_path, recipes):
    """Process a ds recipe, gathering information useful for building other
    types of recipes."""

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    print "Determining app's name from NAME input key..."
    app_name = input_recipe["Input"]["NAME"]
    print "    App name is: %s" % app_name

    # Search for existing recipes that match the app's name.
    create_existing_recipe_list(app_name, recipes)

    # If supported recipe type doesn't already exist, mark as buildable.
    # The buildable list will be used to determine what is offered to the user.
    create_buildable_recipe_list(app_name, recipes)

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Send the information we discovered to the recipe keys.
    for i in range(0, len(recipes)):
        recipes[i]["keys"]["Input"]["NAME"] = app_name
        recipes[i]["keys"]["ParentRecipe"] = input_recipe["Identifier"]
        if recipes[i]["buildable"] is True:

            if recipes[i]["name"] == "download":
                pass

            if recipes[i]["name"] == "munki":
                pass

            if recipes[i]["name"] == "pkg":
                pass

            if recipes[i]["name"] == "install":
                pass

            if recipes[i]["name"] == "jss":
                pass

            if recipes[i]["name"] == "absolute":
                pass

            if recipes[i]["name"] == "sccm":
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

    print "\nPlease select which recipes you'd like to create:\n"

    # TODO(Elliot): Make this interactive while retaining scrollback.
    # Maybe with curses module?
    while True:
        for i in range(0, len(recipes)):
            indicator = " "
            if (recipes[i]["preferred"] is True and recipes[i]["buildable"] is True):
                if recipes[i]["selected"] is True:
                    indicator = "*"
                print "  [%s] %s. %s - %s" % (indicator, i, recipes[i]["name"], recipes[i]["description"])
        choice = raw_input(
            "\nType a number to toggle the corresponding recipe "
            "type between ON [*] and OFF [ ]. When you're satisfied "
            "with your choices, type an \"S\" to save and proceed: ")
        if choice.upper() == "S":
            break
        else:
            try:
                if recipes[int(choice)]["selected"] is False:
                    recipes[int(choice)]["selected"] = True
                else:
                    recipes[int(choice)]["selected"] = False
            except Exception:
                print "%s%s is not a valid option. Please try again.%s\n" % (bcolors.ERROR, choice, bcolors.ENDC)


def generate_selected_recipes(prefs, recipes):
    """Generate the selected types of recipes."""

    print "\nGenerating selected recipes..."
    # TODO(Elliot): Say "no recipes selected" if appropriate.

    for i in range(0, len(recipes)):
        if (recipes[i]["preferred"] is True and recipes[i]["buildable"] is True and recipes[i]["selected"] is True):

            # Set the identifier of the recipe.
            recipes[i]["keys"]["Identifier"] = "%s.%s.%s" % (
                prefs["RecipeIdentifierPrefix"], recipes[i]["name"], recipes[i]["keys"]["Input"]["NAME"])

            # Set type-specific keys.
            if recipes[i]["name"] == "download":

                recipes[i]["keys"]["Description"] = "Downloads the latest version of %s." % recipes[
                    i]["keys"]["Input"]["NAME"]

            elif recipes[i]["name"] == "munki":

                recipes[i]["keys"]["Description"] = "Imports the latest version of %s into Munki." % recipes[
                    i]["keys"]["Input"]["NAME"]

                # if recipes[i]["icon_path"] != "":
                #     png_path = "%s/%s.png" % (prefs["RecipeCreateLocation"], recipes[i]["keys"]["Input"]["NAME"])
                #     extract_app_icon(recipes[i]["icon_path"], png_path)

            elif recipes[i]["name"] == "pkg":

                recipes[i]["keys"]["Description"] = "Downloads the latest version of %s and creates an installer package." % recipes[
                    i]["keys"]["Input"]["NAME"]

            elif recipes[i]["name"] == "install":

                recipes[i]["keys"]["Description"] = "Installs the latest version of %s." % recipes[
                    i]["keys"]["Input"]["NAME"]

            elif recipes[i]["name"] == "jss":

                recipes[i]["keys"]["Description"] = "Imports the latest version of %s into your JSS." % recipes[
                    i]["keys"]["Input"]["NAME"]

                # if recipes[i]["icon_path"] != "":
                #     png_path = "%s/%s.png" % (prefs["RecipeCreateLocation"], recipes[i]["keys"]["Input"]["NAME"])
                #     extract_app_icon(recipes[i]["icon_path"], png_path)

            elif recipes[i]["name"] == "absolute":

                recipes[i]["keys"]["Description"] = "Imports the latest version of %s into Absolute Manage." % recipes[
                    i]["keys"]["Input"]["NAME"]

            elif recipes[i]["name"] == "sccm":

                recipes[i]["keys"]["Description"] = "Imports the latest version of %s into SCCM." % recipes[
                    i]["keys"]["Input"]["NAME"]

            elif recipes[i]["name"] == "ds":

                recipes[i]["keys"]["Description"] = "Imports the latest version of %s into DeployStudio." % recipes[
                    i]["keys"]["Input"]["NAME"]
            else:
                print "I don't know how to generate a recipe of type %s." % recipes[i]["name"]

            # Write the recipe to disk.
            filename = "%s.%s.recipe" % (
                recipes[i]["keys"]["Input"]["NAME"], recipes[i]["name"])
            write_recipe_file(filename, prefs, recipes[i]["keys"])
            print "    %s/%s" % (prefs["RecipeCreateLocation"], filename)


def create_dest_dirs(path):
    """Creates the path to the recipe export location, if it doesn't exist."""

    dest_dir = os.path.expanduser(path)
    if not os.path.exists(dest_dir):
        try:
            os.makedirs(dest_dir)
        except Exception:
            print "[ERROR] Unable to create directory at %s." % dest_dir
            if debug_mode:
                raise
            else:
                sys.exit(1)


def extract_app_icon(icon_path, png_path):
    """Convert the app's icns file to 128x128 png at the specified path."""

    # TODO(Elliot): User path expansion is not working right here.
    create_dest_dirs(os.path.dirname(os.path.expanduser(png_path)))

    # TODO(Elliot): Warning if a file already exists here.

    if debug_mode is True:
        print "Icon extraction command:"
        print "sips -s format png \"%s\" --out \"%s\" --resampleHeightWidthMax 128" % (icon_path, png_path)

    cmd = "sips -s format png \"%s\" --out \"%s\" --resampleHeightWidthMax 128" % (icon_path, png_path)
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if exitcode == 0:
        print "    %s" % png_path
    else:
        print err


def write_recipe_file(filename, prefs, keys):
    """Write a generated recipe to disk."""

    create_dest_dirs(prefs["RecipeCreateLocation"])

    # TODO(Elliot): Warning if a file already exists here.

    dest_dir = os.path.expanduser(prefs["RecipeCreateLocation"])
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
    print "\nYou've now created %s recipes with Recipe Robot. %s\n" % (prefs["RecipeCreateCount"], random.choice(congrats_msg))


def print_debug_info(prefs, recipes):
    """Print current debug information."""

    print bcolors.DEBUG
    print "\n    RECIPE IDENTIFIER PREFIX: \n"
    print prefs["RecipeIdentifierPrefix"]
    print "\n    PREFERRED RECIPE TYPES\n"
    pprint(prefs["RecipeTypes"])
    print "\n    SUPPORTED DOWNLOAD FORMATS\n"
    pprint(supported_download_formats)
    print "\n    CURRENT RECIPE INFORMATION\n"
    pprint(recipes)
    print bcolors.ENDC


# TODO(Elliot): Make main() shorter. Just a flowchart for the logic.
def main():
    """Make the magic happen."""

    print_welcome_text()

    argparser = build_argument_parser()
    args = argparser.parse_args()

    # Temporary argument handling
    input_path = args.input_path
    input_path = input_path.rstrip("/ ")

    # TODO(Elliot): Verify that the input path actually exists.
    if not os.path.exists(input_path):
        print "%s[ERROR] Input path does not exist. Please try again with a valid input path.%s" % (
            bcolors.ERROR, bcolors.ENDC
        )
        sys.exit(1)

    # Create the master recipe information list.
    recipes = init_recipes()

    # Read or create the user preferences.
    prefs = {}
    prefs = init_prefs(prefs, recipes)

    input_type = get_input_type(input_path)
    print "\nProcessing %s ..." % input_path

    # Orchestrate helper functions to handle input_path's "type".
    if input_type is InputType.app:
        handle_app_input(input_path, recipes)
    elif input_type is InputType.download_recipe:
        handle_download_recipe_input(input_path, recipes)
    elif input_type is InputType.munki_recipe:
        handle_munki_recipe_input(input_path, recipes)
    elif input_type is InputType.pkg_recipe:
        handle_pkg_recipe_input(input_path, recipes)
    elif input_type is InputType.install_recipe:
        handle_install_recipe_input(input_path, recipes)
    elif input_type is InputType.jss_recipe:
        handle_jss_recipe_input(input_path, recipes)
    elif input_type is InputType.absolute_recipe:
        handle_absolute_recipe_input(input_path, recipes)
    elif input_type is InputType.sccm_recipe:
        handle_sccm_recipe_input(input_path, recipes)
    elif input_type is InputType.ds_recipe:
        handle_ds_recipe_input(input_path, recipes)
    else:
        print("%s[ERROR] I haven't been trained on how to handle this input "
              "path:\n    %s%s" % (bcolors.ERROR, input_path, bcolors.ENDC))
        sys.exit(1)

    print_debug_info(prefs, recipes)

    # Prompt the user with the available recipes types and let them choose.
    select_recipes_to_generate(recipes)

    # Create recipes for the recipe types that were selected above.
    generate_selected_recipes(prefs, recipes)

    # Pat on the back!
    congratulate(prefs)


if __name__ == '__main__':
    main()
