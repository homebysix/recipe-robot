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

Easily and automatically create AutoPkg recipes.

usage: recipe-robot.py [-h] [-v] input_path [-o output_path] [-t recipe_type]

positional arguments:
    input_path            Path to a recipe or app you'd like to use as the
                          basis for creating AutoPkg recipes.

optional arguments:
    -h, --help            Show this help message and exit.
    -v, --verbose         Generate additional output about the process.
                          Verbose mode is off by default.
    -o, --output          Specify the folder in which to create output recipes.
                          This folder is ~/Library/Caches/Recipe Robot by
                          default.
    -t, --recipe-type     Specify the type(s) of recipe to create.
                          (e.g. download, pkg, munki, jss)
"""


import argparse
import os.path
import plistlib
from pprint import pprint
import shlex
from subprocess import Popen, PIPE
import sys


# Global variables.
__version__ = '0.0.1'
__debug_mode__ = True  # set to True for additional output
__pref_file__ = os.path.expanduser(
    "~/Library/Preferences/com.elliotjordan.recipe-robot.plist")

# Build the recipe format offerings.
# TODO(Elliot): This should probably not be a global variable.
__avail_recipe_types__ = {
    "download": "Downloads an app in whatever format the developer "
                "provides.",
    "munki": "Imports into your Munki repository.",
    "pkg": "Creates a standard pkg installer file.",
    "install": "Installs the app on the computer running AutoPkg.",
    "jss": "Imports into your Casper JSS and creates necessary groups, "
           "policies, etc.",
    "absolute": "Imports into your Absolute Manage server.",
    "sccm": "Imports into your SCCM server.",
    "ds": "Imports into your DeployStudio Packages folder."
}

# Build the list of download formats we know about. TODO: It would be great
# if we didn't need this list, but I suspect we do need it in order to tell
# the recipes which Processors to use.
# TODO(Elliot): This should probably not be a global variable.
__supported_download_formats__ = ("dmg", "zip", "tar.gz", "gzip", "pkg")

# Build the list of existing recipes.
# Example: ['Firefox.download.recipe']
# TODO(Elliot): This should probably not be a global variable.
__existing_recipes__ = []

# Build the dict of buildable recipes and their corresponding
# templates. Example: {'Firefox.jss.recipe': 'pkg.jss.recipe'}
# TODO(Elliot): This should probably not be a global variable.
__buildable_recipes__ = {}

# The name of the app for which a recipe is being built.
# TODO(Elliot): This should probably not be a global variable.
__app_name__ = ""


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
    # TODO(Elliot): Add --plist argument to header info up top.
    parser.add_argument(
        "--plist",
        action="store_true",
        help="Output all results as plists.")
    parser.add_argument(
        "-o", "--output",
        action="store",
        help="Path to a folder you'd like to save your generated recipes in.")
    parser.add_argument(
        "-t", "--recipe-type",
        action="store",
        help="The type(s) of recipe you'd like to generate.")
    return parser


def get_input_type(input_path):
    """Determine the type of recipe generation needed based on path.

    Args:
        input_path: String path to an app, download recipe, etc.

    Returns:
        Int pseudo-enum value of InputType.
    """
    if input_path.rstrip("/").endswith(".app"):
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


def create_existing_recipe_list(__app_name__):
    """Use autopkg search results to build existing recipe list."""

    cmd = "autopkg search -p %s" % __app_name__
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if exitcode == 0:
        for line in out.split("\n"):
            if ".recipe" in line:
                # Add the first "word" of each line of search results. Example:
                # Firefox.pkg.recipe
                __existing_recipes__.append(line.split(None, 1)[0])
    else:
        print err
        sys.exit(exitcode)


def create_buildable_recipe_list(__app_name__):
    """Add any recipe types that don't already exist to the buildable list."""

    for recipe_format in __avail_recipe_types__:
        if "%s.%s.recipe" % (__app_name__, recipe_format) not in __existing_recipes__:
            __buildable_recipes__[
                # TODO(Elliot): Determine proper template to use.
                __app_name__ + "." + recipe_format + ".recipe"
            ] = "template TBD"


def handle_app_input(input_path):
    """Process an app, gathering required information to create a recipe."""

    if __debug_mode__:
        print "\n%s    INPUT TYPE:  app%s\n" % (bcolors.DEBUG, bcolors.ENDC)

    # Figure out the name of the app.
    try:
        info_plist = plistlib.readPlist(input_path + "/Contents/Info.plist")
        __app_name__ = info_plist["CFBundleName"]
    except KeyError:
        try:
            __app_name__ = info_plist["CFBundleExecutable"]
        except KeyError:
            print "%s[ERROR] Sorry, I can't figure out what this app is called.%s" % (
                bcolors.ERROR, bcolors.ENDC
            )
            sys.exit(1)

    # Use the autopkg search results to build a list of existing recipes.
    create_existing_recipe_list(__app_name__)

    # Check for a Sparkle feed, but only if a download recipe doesn't exist.
    if __app_name__ + "%s.download.recipe" not in __existing_recipes__:
        try:
            print "We found a Sparkle feed: %s" % info_plist["SUFeedURL"]
            __buildable_recipes__[
                __app_name__ + ".download.recipe"
            ] = "download-from-sparkle.recipe"

        except KeyError:
            try:
                print("We found a Sparkle feed: %s" %
                      info_plist["SUOriginalFeedURL"])
                __buildable_recipes__[__app_name__ + ".download.recipe"] = (
                    "download-from-sparkle.recipe"
                )

        # TODO(Elliot): There was no existing download recipe, but if we have a
        # Sparkle feed, we now know we can build one. However, we don't
        # know what format the resulting download will be. We need to find
        # that out before we can create recipes that use the download as a
        # parent.

        # TODO(Elliot): Search GitHub for the app, to see if we can use the
        # GitHubReleasesProvider processor to create a download recipe.

        # TODO(Elliot): Search SourceForge for the app, to see if we can use the
        # SourceForgeReleasesProvider processor to create a download
        # recipe.

            except KeyError:
                print "%s[WARNING] No Sparkle feed.%s" % (bcolors.WARNING,
                                                          bcolors.ENDC)

    else:

        # TODO(Elliot): We know that there's an existing download recipe
        # available, but we don't know what format the resulting
        # download is. We need to find that out before we can
        # create recipes that use the download as a parent.
        pass

    # If an available recipe type doesn't already exist, add to the buildable
    # recipes list.
    create_buildable_recipe_list(__app_name__)

    # If munki recipe is buildable, the minimum OS version prove useful.
    # TODO(Elliot): Find a way to pass variables like this to the generator.
    if __app_name__ + ".munki.recipe" in __buildable_recipes__:
        try:
            min_sys_vers = info_plist["LSMinimumSystemVersion"]
        except KeyError:
            if __debug_mode__:
                print bcolors.DEBUG
                print("[WARNING] can't detect minimum system version." +
                      bcolors.ENDC)


def handle_download_recipe_input(input_path):
    """Process a download recipe, gathering information useful for building
    other types of recipes.
    """
    if __debug_mode__:
        print "%s\n    INPUT TYPE:  download recipe%s\n" % (bcolors.DEBUG,
                                                            bcolors.ENDC)

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    # Get the app's name from the recipe.
    __app_name__ = input_recipe["Input"]["NAME"]

    # Get the download file format.
    # TODO(Elliot): Parse the recipe properly. Don't use grep.
    parsed_download_format = ""
    for download_format in __supported_download_formats__:
        cmd = "grep '.%s</string>' '%s'" % (download_format, input_path)
        exitcode, out, err = get_exitcode_stdout_stderr(cmd)
        if exitcode == 0:
            print "Looks like this recipe downloads a %s." % download_format
            parsed_download_format = download_format
            break

    # Use the autopkg search results to build a list of existing recipes.
    create_existing_recipe_list(__app_name__)

    # Attempting to simultaneously determine which recipe types are
    # available to build and which templates we should use for each.
    # TODO(Elliot): Make it better. Integrate with existing
    # create_buildable_recipe_list function.
    for recipe_format in __avail_recipe_types__:
        if __app_name__ + "." + recipe_format + ".recipe" not in __existing_recipes__:
            this_recipe_type = "%s.%s.recipe" % __app_name__, recipe_format
            if recipe_format in ("pkg", "install", "munki"):
                this_recipe_template = "%s-from-download_%s" % recipe_format, download_format
                __buildable_recipes__[this_recipe_type] = this_recipe_template
            else:
                this_recipe_template = "%s-from-pkg" % recipe_format
                __buildable_recipes__[this_recipe_type] = this_recipe_template

    # Offer to build pkg, munki, jss, etc.


def handle_munki_recipe_input(input_path):
    """Process a munki recipe, gathering information useful for building other
    types of recipes."""

    if __debug_mode__:
        print "%s\n    INPUT TYPE:  munki recipe%s\n" % (bcolors.DEBUG,
                                                         bcolors.ENDC)

    # Determine whether there's already a download Parent recipe.
    # If not, add it to the list of offered recipe formats.

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    # Get the app's name from the recipe.
    __app_name__ = input_recipe["Input"]["NAME"]

    # Use the autopkg search results to build a list of existing recipes.
    create_existing_recipe_list(__app_name__)

    # If an available recipe type doesn't already exist, add to the buildable
    # recipes list.
    create_buildable_recipe_list(__app_name__)

    # If this munki recipe both downloads and imports the app, we
    # should offer to build a discrete download recipe with only
    # the appropriate sections of the munki recipe.

    # Offer to build pkg, jss, etc.

    # TODO(Elliot): Think about whether we want to dig into OS requirements,
    # blocking applications, etc when building munki recipes. I vote
    # yes, but it's probably not going to be easy.


def handle_pkg_recipe_input(input_path):
    """Process a pkg recipe, gathering information useful for building other
    types of recipes."""

    if __debug_mode__:
        print "%s\n    INPUT TYPE:  pkg recipe%s\n" % (bcolors.DEBUG,
                                                       bcolors.ENDC)

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    # Get the app's name from the recipe.
    __app_name__ = input_recipe["Input"]["NAME"]

    # Use the autopkg search results to build a list of existing recipes.
    create_existing_recipe_list(__app_name__)

    # If an available recipe type doesn't already exist, add to the buildable
    # recipes list.
    create_buildable_recipe_list(__app_name__)

    # Check to see whether the recipe has a download recipe as its parent. If
    # not, offer to build a discrete download recipe.

    # Offer to build munki, jss, etc.


def handle_install_recipe_input(input_path):
    """Process an install recipe, gathering information useful for building
    other types of recipes."""

    if __debug_mode__:
        print "%s\n    INPUT TYPE:  install recipe%s\n" % (bcolors.DEBUG,
                                                           bcolors.ENDC)

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    # Get the app's name from the recipe.
    __app_name__ = input_recipe["Input"]["NAME"]

    # Use the autopkg search results to build a list of existing recipes.
    create_existing_recipe_list(__app_name__)

    # If an available recipe type doesn't already exist, add to the buildable
    # recipes list.
    create_buildable_recipe_list(__app_name__)

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Offer to build other recipes as able.


def handle_jss_recipe_input(input_path):
    """Process a jss recipe, gathering information useful for building other
    types of recipes."""

    if __debug_mode__:
        print "%s\n    INPUT TYPE:  jss recipe%s\n" % (bcolors.DEBUG,
                                                       bcolors.ENDC)

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    # Get the app's name from the recipe.
    __app_name__ = input_recipe["Input"]["NAME"]

    # Use the autopkg search results to build a list of existing recipes.
    create_existing_recipe_list(__app_name__)

    # If an available recipe type doesn't already exist, add to the buildable
    # recipes list.
    create_buildable_recipe_list(__app_name__)

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Offer to build other recipes as able.


def handle_absolute_recipe_input(input_path):
    """Process an absolute recipe, gathering information useful for building
    other types of recipes.
    """

    if __debug_mode__:
        print "%s\n    INPUT TYPE:  absolute recipe%s\n" % (bcolors.DEBUG,
                                                            bcolors.ENDC)

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    # Get the app's name from the recipe.
    __app_name__ = input_recipe["Input"]["NAME"]

    # Use the autopkg search results to build a list of existing recipes.
    create_existing_recipe_list(__app_name__)

    # If an available recipe type doesn't already exist, add to the buildable
    # recipes list.
    create_buildable_recipe_list(__app_name__)

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Offer to build other recipes as able.


def handle_sccm_recipe_input(input_path):
    """Process a sccm recipe, gathering information useful for building other
    types of recipes."""

    if __debug_mode__:
        print "%s\n    INPUT TYPE:  sccm recipe%s\n" % (bcolors.DEBUG,
                                                        bcolors.ENDC)

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    # Get the app's name from the recipe.
    __app_name__ = input_recipe["Input"]["NAME"]

    # Use the autopkg search results to build a list of existing recipes.
    create_existing_recipe_list(__app_name__)

    # If an available recipe type doesn't already exist, add to the buildable
    # recipes list.
    create_buildable_recipe_list(__app_name__)

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Offer to build other recipes as able.


def handle_ds_recipe_input(input_path):
    """Process a ds recipe, gathering information useful for building other
    types of recipes."""

    if __debug_mode__:
        print "%s\n    INPUT TYPE:  ds recipe%s\n" % (bcolors.DEBUG,
                                                      bcolors.ENDC)

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    # Get the app's name from the recipe.
    __app_name__ = input_recipe["Input"]["NAME"]

    # Use the autopkg search results to build a list of existing recipes.
    create_existing_recipe_list(__app_name__)

    # If an available recipe type doesn't already exist, add to the buildable
    # recipes list.
    create_buildable_recipe_list(__app_name__)

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Offer to build other recipes as able.


def generate_recipe(plist_path, plist_object):
    """Generate a basic AutoPkg recipe of the desired format."""
    print "Generating AutoPkgr.download.recipe (why? because we can!)..."

    # TODO(Elliot): I'm guessing Shea is going to come in here and dump a load of
    # classes for plists and recipes. Until then, I'm using find/replace like
    # a n00b.

    # We'll use this later when creating icons for Munki and JSS recipes.
    # cmd = 'sips -s format png \
    # "/Applications/iTunes.app/Contents/Resources/iTunes.icns" \
    # --out "/Users/elliot/Desktop/iTunes.png" \
    # --resampleHeightWidthMax 128'

    # The below is just an example recipe to prove that plistlib works.
    plist_path = "~/Desktop/AutoPkgr.download.recipe"
    plist_object = dict(
        Identifier="com.elliotjordan.download.AutoPkgr",
        Description="Downloads the latest version of AutoPkgr.",
        MinimumVersion="0.5.0",
        Input=dict(
            NAME="AutoPkgr",
            SPARKLE_FEED_URL="https://raw.githubusercontent.com/lindegroup/autopkgr/appcast/appcast.xml"),
        Process=[
            dict(
                Processor="SparkleUpdateInfoProvider",
                Arguments=dict(
                    appcast_url="%SPARKLE_FEED_URL%")),
            dict(
                Processor="URLDownloader",
                Arguments=dict(
                    filename=">%NAME%.dmg")),
            dict(
                Processor="EndOfCheckPhase"),
        ])
    recipe_file = os.path.expanduser(plist_path)
    plistlib.writePlist(plist_object, recipe_file)
    print "    " + plist_path

# TODO(Elliot): Make main() shorter. Just a flowchart for the logic.


def main():
    """Make the magic happen."""

    welcome_text = """
     -----------------------------------
    |  Welcome to Recipe Robot v%s.  |
     -----------------------------------
               \   _[]_
                \  [oo]
                  d-||-b
                    ||
                  _/  \_
    """ % __version__

    print welcome_text

    argparser = build_argument_parser()
    args = argparser.parse_args()

    # Temporary argument handling
    input_path = args.input_path

    # TODO(Elliot): Verify that the input path actually exists.
    if not os.path.exists(input_path):
        print "%s[ERROR] Input path does not exist. Please try again with a valid input path.%s" % (
            bcolors.ERROR, bcolors.ENDC
        )
        sys.exit(1)

    # Set the default recipe identifier prefix.
    # I imagine this needs to be a defaulted value.
    # TODO(Shea): Implement preferences.
    preferred_identifier_prefix = "com.github.homebysix"

    if __debug_mode__:
        print "%s\n    DEBUG MODE:  ON" % bcolors.DEBUG
        print "    INPUT PATH:  %s%s" % (input_path, bcolors.ENDC)

    # If the preferences file already exists, read it. Otherwise, create it.
    if os.path.isfile(__pref_file__):
        pref_plist = plistlib.readPlist(__pref_file__)
        preferred_identifier_prefix = pref_plist[
            "PreferredRecipeIdentifierPrefix"]
        preferred_recipe_types = pref_plist["PreferredRecipeTypes"]
    else:
        preferred_identifier_prefix = raw_input(
            "Please enter your preferred recipe identifier prefix: ")

        # TODO(Elliot): Find a way to toggle the recipe types off/on as needed.

        i = 0
        for this_type, this_description in __avail_recipe_types__.iteritems():
            # TODO(Elliot): if recipe is included in the preferred types
            if True:
                print "  [•] %s. %s - %s" % (i, this_type, this_description)
            # TODO(Elliot): if recipe is not included in the preferred types
            else:
                print "  [ ] %s. %s - %s" % (i, this_type, this_description)
            i += 1

        preferred_recipe_types = raw_input(
            "Please choose your default recipe types: ")

        prefs = dict(
            # TODO(Elliot): Use the actual preferred_recipe_types value from
            # above.
            PreferredRecipeIdentifierPrefix=preferred_identifier_prefix,
            PreferredRecipeTypes=[
                "download", "munki", "pkg", "install", "jss", "absolute",
                "sccm", "ds"
            ],
            LastRecipeRobotVersion=__version__)
        plistlib.writePlist(prefs, __pref_file__)

    print "\nProcessing %s ..." % input_path

    # Orchestrate helper functions to handle input_path's "type".
    input_type = get_input_type(input_path)
    if input_type is InputType.app:
        handle_app_input(input_path)
    elif input_type is InputType.download_recipe:
        handle_download_recipe_input(input_path)
    elif input_type is InputType.munki_recipe:
        handle_munki_recipe_input(input_path)
    elif input_type is InputType.pkg_recipe:
        handle_pkg_recipe_input(input_path)
    elif input_type is InputType.jss_recipe:
        handle_jss_recipe_input(input_path)
    else:
        print "I haven't been trained on how to handle this input path:"
        print "    %s" % input_path
        sys.exit(1)

    if __debug_mode__:
        print "%s\n    EXISTING RECIPES:\n" % bcolors.DEBUG
        pprint(__existing_recipes__)
        print "\n    AVAILABLE RECIPE TYPES:\n"
        pprint(__avail_recipe_types__)
        print "\n    BUILDABLE RECIPES:\n"
        pprint(__buildable_recipes__)
        print bcolors.ENDC

    # Prompt the user with the available recipes types and let them choose.
    print "\nHere are the recipe types available to build:"
    for key, value in __buildable_recipes__.iteritems():
        print "    %s" % key

    # Generate selected recipes.
    generate_recipe("", dict())


if __name__ == '__main__':
    main()
