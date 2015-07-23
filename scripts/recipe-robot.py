#!/usr/bin/env python

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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
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


from pprint import pprint
from subprocess import Popen, PIPE
import argparse
import os.path
import plistlib
import shlex
import sys


# Global variables.
__version__ = '0.0.1'
__debug_mode__ = True  # set to True for additional output
__pref_file__ = os.path.expanduser(
    "~/Library/Preferences/com.elliotjordan.recipe-robot.plist")

# Build the recipe format offerings.
__avail_recipe_formats__ = {
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
__supported_download_formats__ = (
    "dmg",
    "zip",
    "tar.gz",
    "gzip",
    "pkg"
)

# Build the list of existing recipes.
# Example: ['Firefox.download.recipe']
__existing_recipes__ = []

# Build the dict of buildable recipes and their corresponding
# templates. Example: {'Firefox.jss.recipe': 'pkg.jss.recipe'}
__buildable_recipes__ = {}


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


# if __debug_mode__:
#     print "\n    COLOR OPTIONS: \n"
#     print bcolors.HEADER + "HEADER" + bcolors.ENDC
#     print bcolors.OKBLUE + "OKBLUE" + bcolors.ENDC
#     print bcolors.OKGREEN + "OKGREEN" + bcolors.ENDC
#     print bcolors.WARNING + "WARNING" + bcolors.ENDC
#     print (bcolors.ERROR + "ERROR" + bcolors.ENDC + bcolors.ENDC + "ENDC" +
#            bcolors.ENDC)
#     print bcolors.BOLD + "BOLD" + bcolors.ENDC
#     print bcolors.UNDERLINE + "UNDERLINE" + bcolors.ENDC


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
    # TODO: I've been told Popen is not a good practice. Better idea?
    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    exitcode = proc.returncode
    return exitcode, out, err


def generate_recipe(app_name, recipe_type):
    """Generate a basic AutoPkg recipe of the desired format."""
    print "Generating {}.{}.recipe...".format(app_name, recipe_type)

    # TODO: I'm guessing Shea is going to come in here and dump a load of
    # classes for plists and recipes. Until then, I'm using find/replace like
    # a n00b.

    # We'll use this later when creating icons for Munki and JSS recipes.
    # cmd = 'sips -s format png \
    # "/Applications/iTunes.app/Contents/Resources/iTunes.icns" \
    # --out "/Users/elliot/Desktop/iTunes.png" \
    # --resampleHeightWidthMax 128'

    # The below is just an example recipe to prove that plistlib works.

    # recipe_file = os.path.expanduser(
    #     "~/Library/Caches/Recipe Robot/test.recipe")
    #
    # recipe_contents = dict(
    #     Identifier="com.elliotjordan.pkg.AutoPkgr",
    #     Description="Creates an installer for the latest version of "
    #         "AutoPkgr.",
    #     ParentRecipe="com.github.homebysix.download.AutoPkgr",
    #     MinimumVersion="0.5.0",
    #     Input=dict(
    #         NAME="AutoPkgr"
    #     ),
    #     Process=[
    #         dict(
    #             Processor="AppDmgVersioner",
    #             Arguments=dict(
    #                 dmg_path="%pathname%"
    #             )
    #         ),
    #         dict(
    #             Processor="PkgRootCreator",
    #             Arguments=dict(
    #                 pkgroot="%RECIPE_CACHE_DIR%/%NAME%",
    #                 pkgdirs=dict(
    #                     Applications="0775"
    #                 )
    #             )
    #         ),
    #         dict(
    #             Processor="Copier",
    #             Arguments=dict(
    #                 source_path="%pathname%/%PROD%.app",
    #                 destination_path="%pkgroot%/Applications/%PROD%.app"
    #             )
    #         ),
    #         dict(
    #             Processor="PkgCreator",
    #             Arguments=dict(
    #                 pkg_request=dict(
    #                     pkgname="%NAME%-%version%",
    #                     pkgdir="%RECIPE_CACHE_DIR%",
    #                     id="%PKG_IDENTIFIER%",
    #                     options="purge_ds_store",
    #                     chown=[
    #                         dict(
    #                             path="Applications",
    #                             user="root",
    #                             group="admin"
    #                         )
    #                     ]
    #                 )
    #             )
    #         )
    #     ]
    # )
    # plistlib.writePlist(recipe_contents, recipe_file)


def build_argument_parser():
    """Build and return the argument parser for Recipe Robot."""
    parser = argparse.ArgumentParser(
        description="Easily and automatically create AutoPkg recipes."
    )
    parser.add_argument(
        "input_path",
        help="Path to a recipe or app to use as the basis for creating AutoPkg recipes."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Generate additional output about the process."
    )
    # TODO: Add --plist argument to header info up top.
    parser.add_argument(
        "--plist",
        action="store_true",
        help="Output all results as plists."
    )
    parser.add_argument(
        "-o", "--output",
        action="store",
        help="Path to a folder you'd like to save your generated recipes in.")
    parser.add_argument(
        "-t", "--recipe-type",
        action="store",
        help="The type(s) of recipe you'd like to generate."
    )
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
    elif input_path.endswith(".pkg.recipe"):
        return InputType.pkg_recipe
    elif input_path.endswith(".munki.recipe"):
        return InputType.munki_recipe
    elif input_path.endswith(".jss.recipe"):
        return InputType.jss_recipe


# ----------------------------------- APPS ---------------------------------- #
def handle_app_input(input_path):

    """Process an app, gathering information that may be needed in order to
    create a recipe."""

    if __debug_mode__:
        print bcolors.DEBUG + "\n    INPUT TYPE:  app\n" + bcolors.ENDC

    # Figure out the name of the app.
    try:
        info_plist = plistlib.readPlist(
            input_path + "/Contents/Info.plist")
        app_name = info_plist["CFBundleName"]
    except KeyError, e:
        try:
            app_name = info_plist["CFBundleExecutable"]
        except KeyError, e:
            print bcolors.ERROR
            print ("[ERROR] Sorry, I can't figure out what this app is called."
                   + bcolors.ENDC)
            sys.exit(1)

    # Search for existing recipes for this app.
    cmd = "autopkg search -p %s" % app_name
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if exitcode == 0:
        for line in out.split("\n"):
            if ".recipe" in line:
                # Add the first "word" of each line of search
                # results. Example: Firefox.pkg.recipe
                __existing_recipes__.append(line.split(None, 1)[0])
    else:
        print err
        sys.exit(exitcode)

    # Check for a Sparkle feed, but only if a download recipe
    # doesn't exist.
    if app_name + ".download.recipe" not in __existing_recipes__:
        try:
            print "We found a Sparkle feed: %s" % info_plist["SUFeedURL"]
            __buildable_recipes__[
                app_name + ".download.recipe"] = "download-from-sparkle.recipe"

        except KeyError, e:
            try:
                print ("We found a Sparkle feed: %s" %
                       info_plist["SUOriginalFeedURL"])
                __buildable_recipes__[app_name + ".download.recipe"] = (
                    "download-from-sparkle.recipe")

        # TODO: There was no existing download recipe, but if we have a
        # Sparkle feed, we now know we can build one. However, we don't
        # know what format the resulting download will be. We need to find
        # that out before we can create recipes that use the download as a
        # parent.

        # TODO: Search GitHub for the app, to see if we can use the
        # GitHubReleasesProvider processor to create a download recipe.

        # TODO: Search SourceForge for the app, to see if we can use the
        # SourceForgeReleasesProvider processor to create a download
        # recipe.

            except KeyError, e:
                print bcolors.WARNING
                print "[WARNING] No Sparkle feed." + bcolors.ENDC

    else:

        # TODO: We know that there's an existing download recipe
        # available, but we don't know what format the resulting
        # download is. We need to find that out before we can
        # create recipes that use the download as a parent.
        pass

    for recipe_format in __avail_recipe_formats__:
        this_recipe = "{}.{}.recipe".format(app_name, recipe_format)
        if this_recipe not in __existing_recipes__:
            __buildable_recipes__[
                # TODO: Determine proper template to use.
                app_name + "." + recipe_format + ".recipe"] = "template TBD"

    # If munki recipe is buildable, the minimum OS version prove useful.
    # TODO: Find a way to pass variables like this to the generator.
    if app_name + ".munki.recipe" in __buildable_recipes__:
        try:
            min_sys_vers = info_plist["LSMinimumSystemVersion"]
        except KeyError:
            if __debug_mode__:
                print bcolors.DEBUG
                print ("[warning] can't detect minimum system version." +
                       bcolors.ENDC)

# ----------------------------- DOWNLOAD RECIPES ---------------------------- #
def handle_download_recipe_input(input_path):
    """Process a download recipe, gathering information useful for building other types of recipes."""
    if __debug_mode__:
        print (bcolors.DEBUG + "\n    INPUT TYPE:  download recipe\n" +
               bcolors.ENDC)

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    # Get the app's name from the recipe.
    app_name = input_recipe["Input"]["NAME"]

    # Get the download file format.
    # TODO: Parse the recipe properly. Don't use grep.
    parsed_download_format = ""
    for download_format in __supported_download_formats__:
        cmd = "grep '." + download_format + \
            "</string>' '" + input_path + "'"
        exitcode, out, err = get_exitcode_stdout_stderr(cmd)
        if exitcode == 0:
            print "Looks like this recipe downloads a %s." % download_format
            parsed_download_format = download_format
            break

    # Search for existing recipes for this app.
    cmd = "autopkg search -p %s" % app_name
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if exitcode == 0:
        for line in out.split("\n"):
            if ".recipe" in line:
                # Add the first "word" of each line of search
                # results. Example: Firefox.pkg.recipe
                __existing_recipes__.append(line.split(None, 1)[0])
    else:
        print err
        sys.exit(exitcode)

    # Attempting to simultaneously determine which recipe types are
    # available to build and which templates we should use for each.
    # TODO: Make it better.
    for recipe_format in __avail_recipe_formats__:
        if app_name + "." + recipe_format + ".recipe" not in __existing_recipes__:
            this_recipe_type = "%s.%s.recipe" % app_name, recipe_format
            if recipe_format in ("pkg", "install", "munki"):
                this_recipe_template = "%s-from-download_%s" % recipe_format, download_format
                __buildable_recipes__[this_recipe_type] = this_recipe_template
            else:
                this_recipe_template = "%s-from-pkg" % recipe_format
                __buildable_recipes__[this_recipe_type] = this_recipe_template

    # Offer to build pkg, munki, jss, etc.


# ------------------------------ MUNKI RECIPES ------------------------------ #

def handle_munki_recipe_input(input_path):
    """Process a munki recipe, gathering information useful for building other
    types of recipes."""

    if __debug_mode__:
        print (bcolors.DEBUG + "\n    INPUT TYPE:  munki recipe\n" +
               bcolors.ENDC)

    # Determine whether there's already a download Parent recipe.
    # If not, add it to the list of offered recipe formats.

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    # Get the app's name from the recipe.
    app_name = input_recipe["Input"]["NAME"]

    # Search for existing recipes for this app.
    cmd = "autopkg search -p %s" % app_name
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if exitcode == 0:
        for line in out.split("\n"):
            if ".recipe" in line:
                # Add the first "word" of each line of search
                # results. Example: Firefox.pkg.recipe
                __existing_recipes__.append(line.split(None, 1)[0])
    else:
        print err
        sys.exit(exitcode)

    for recipe_format in __avail_recipe_formats__:
        if app_name + "." + recipe_format + ".recipe" not in __existing_recipes__:
            __buildable_recipes__[
                # TODO: Determine proper template to use.
                app_name + "." + recipe_format + ".recipe"] = "template TBD"

    # If this munki recipe both downloads and imports the app, we
    # should offer to build a discrete download recipe with only
    # the appropriate sections of the munki recipe.

    # Offer to build pkg, jss, etc.

    # TODO: Think about whether we want to dig into OS requirements,
    # blocking applications, etc when building munki recipes. I vote
    # yes, but it's probably not going to be easy.


# ------------------------------- PKG RECIPES ------------------------------- #

def handle_pkg_recipe_input(input_path):
    """Process a pkg recipe, gathering information useful for building other
    types of recipes."""

    if __debug_mode__:
        print bcolors.DEBUG + "\n    INPUT TYPE:  pkg recipe\n" + bcolors.ENDC

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    # Get the app's name from the recipe.
    app_name = input_recipe["Input"]["NAME"]

    # Search for existing recipes for this app.
    cmd = "autopkg search -p %s" % app_name
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

    for recipe_format in __avail_recipe_formats__:
        if app_name + "." + recipe_format + ".recipe" not in __existing_recipes__:
            __buildable_recipes__[
                # TODO: Determine proper template to use.
                app_name + "." + recipe_format + ".recipe"] = "template TBD"

    # Check to see whether the recipe has a download recipe as its parent. If
    # not, offer to build a discrete download recipe.

    # Offer to build munki, jss, etc.


# ------------------------------- JSS RECIPES ------------------------------- #

def handle_jss_recipe_input(input_path):
    """Process a jss recipe, gathering information useful for building other
    types of recipes."""

    if __debug_mode__:
        print bcolors.DEBUG + "\n    INPUT TYPE:  jss recipe\n" + bcolors.ENDC

    # Read the recipe as a plist.
    input_recipe = plistlib.readPlist(input_path)

    # Get the app's name from the recipe.
    app_name = input_recipe["Input"]["NAME"]

    # Search for existing recipes for this app.
    cmd = "autopkg search -p %s" % app_name
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if exitcode == 0:
        for line in out.split("\n"):
            if ".recipe" in line:
                # Add the first "word" of each line of search
                # results. Example: Firefox.pkg.recipe
                __existing_recipes__.append(line.split(None, 1)[0])
    else:
        print err
        sys.exit(exitcode)

    for recipe_format in __avail_recipe_formats__:
        if app_name + "." + recipe_format + ".recipe" not in __existing_recipes__:
            __buildable_recipes__[
                # TODO: Determine proper template to use.
                app_name + "." + recipe_format + ".recipe"] = "template TBD"

    # Check to see whether the recipe has a download and/or pkg
    # recipe as its parent. If not, offer to build a discrete
    # download and/or pkg recipe.

    # Offer to build other recipes as able.


def main():
    """This is where the magic happens."""

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

    # TODO: Verify that the input path actually exists.
    if not os.path.exists(input_path):
        print (bcolors.ERROR + "[ERROR] Input path does not exist. Please try "
               "again with a valid input path." + bcolors.ENDC)
        sys.exit(1)

    # Set the default recipe identifier prefix.
    # I imagine this needs to be a defaulted value.
    # TODO(Shea): Implement preferences.
    default_identifier_prefix = "com.github.homebysix"

    if __debug_mode__:
        print bcolors.DEBUG + "\n"
        print "    DEBUG MODE:  ON"
        print "    INPUT PATH:  %s " % input_path + bcolors.ENDC

    # ---------------------------------- CONFIG ------------------------------#

    # If the preferences file already exists, read it. Otherwise, create it.
    if os.path.isfile(__pref_file__):
        pref_plist = plistlib.readPlist(__pref_file__)
        default_identifier_prefix = pref_plist["DefaultRecipeIdentifierPrefix"]
        default_recipe_types = pref_plist["DefaultRecipeTypes"]
    else:
        default_identifier_prefix = raw_input(
            "Please enter your preferred recipe identifier prefix: ")

        # TODO: Find a way to toggle the recipe types off/on as needed.
        default_recipe_types = raw_input(
            "Please choose your default recipe types: ")

        prefs = dict(
            DefaultRecipeIdentifierPrefix=default_identifier_prefix,
            # TODO: Use the actual default_recipe_types value from above.
            DefaultRecipeTypes=[
                "download",
                "munki",
                "pkg",
                "install",
                "jss",
                "absolute",
                "sccm",
                "ds"
            ],
            LastRecipeRobotVersion=__version__
        )
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
        print bcolors.DEBUG + "\n    EXISTING RECIPES:\n"
        pprint(__existing_recipes__)
        print "\n    AVAILABLE RECIPE TYPES:\n"
        pprint(__avail_recipe_formats__)
        print "\n    BUILDABLE RECIPES:\n"
        pprint(__buildable_recipes__)
        print bcolors.ENDC

    # Prompt the user with the available recipes types and let them choose.
    print "\nHere are the recipe types available to build:"
    for key, value in __buildable_recipes__.iteritems():
        print "    %s" % key

    # Generate selected recipes.


if __name__ == '__main__':
    main()
