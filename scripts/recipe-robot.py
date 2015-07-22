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

usage: recipe-robot.py [-h] [-v] input_path

positional arguments:
    input_path            Path to a recipe or app you'd like to use as the basis
                          for creating AutoPkg recipes.

optional arguments:
    -h, --help            Show this help message and exit.
    -v, --verbose         Generate additional output about the process.
"""


import argparse
from pprint import pprint
from subprocess import Popen, PIPE
import os.path
import plistlib
import shlex
import sys


# Global variables.
__version__ = '0.0.1'
__debug_mode__ = True  # set to True for additional output
__pref_file__ = os.path.expanduser(
    "~/Library/Preferences/com.elliotjordan.recipe-robot.plist")


class bcolors:
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
#     print bcolors.ERROR + "ERROR" + bcolors.ENDC + bcolors.ENDC + "ENDC" + bcolors.ENDC
#     print bcolors.BOLD + "BOLD" + bcolors.ENDC
#     print bcolors.UNDERLINE + "UNDERLINE" + bcolors.ENDC


class InputType(object):
    """Python pseudo-enum for describing types of input."""
    (app, download_recipe) = range(2)


def get_exitcode_stdout_stderr(cmd):
    """Execute the external command and get its exitcode, stdout and stderr."""
    args = shlex.split(cmd)
    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    exitcode = proc.returncode
    #
    return exitcode, out, err


def generate_recipe(app_name, recipe_type):
    """Generates a recipe."""
    print "Generating %s.%s.recipe..." % app_name, recipe_type

    # TODO: I'm guessing Shea is going to come in here and dump a load of
    # classes for plists and recipes. Until then, I'm using find/replace like
    # a n00b.

    # recipe_file = os.path.expanduser("~/Library/Caches/Recipe Robot/test.recipe")
    #
    # recipe_contents = dict(
    #     Identifier="com.elliotjordan.pkg.AutoPkgr",
    #     Description="Creates an installer for the latest version of AutoPkgr.",
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

    pass


def build_argument_parser():
    """Builds and returns the argument parser for Recipe Robot."""
    parser = argparse.ArgumentParser(description="Easily and automatically "
                                     "create AutoPkg recipes.")
    parser.add_argument("input_path", help="Path to a recipe or app you'd "
                        "like to use as the basis for creating AutoPkg "
                        "recipes.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Generate additional output about the process.")
    parser.add_argument("--plist", action="store_true",
                        help="Output all results as plists.")

    return parser


def get_input_type(input_path):
    """Determine the type of recipe generation needed based on path.

    Args:
        input_path: String path to an app, download recipe, etc.

    Returns:
        Int pseudo-enum value of InputType.
    """
    if input_path[-4:] == ".app" or input_path[-5:] == ".app/":
        return InputType.app


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
        print bcolors.ERROR + "[ERROR] Input path does not exist. Please try again with a valid input path." + bcolors.ENDC
        sys.exit(1)

    # Set the default recipe identifier prefix.
    # I imagine this needs to be a defaulted value.
    # TODO(Shea): Implement preferences.
    default_identifier_prefix = "com.github.homebysix"

    # Build the recipe format offerings.
    avail_recipe_formats = {
        "download": "Downloads an app in whatever format the developer provides.",
        "munki": "Imports into your Munki repository.",
        "pkg": "Creates a standard pkg installer file.",
        "install": "Installs the app on the computer running AutoPkg.",
        "jss": "Imports into your Casper JSS and creates necessary groups, policies, etc.",
        "absolute": "Imports into your Absolute Manage server.",
        "sccm": "Imports into your SCCM server.",
        "ds": "Imports into your DeployStudio Packages folder."
    }

    # Build the list of download formats we know about.
    supported_download_formats = (
        "dmg",
        "zip",
        "tar.gz",
        "gzip",
        "pkg"
    )

    if __debug_mode__:
        print bcolors.DEBUG + "\n"
        print "    DEBUG MODE:  ON"
        print "    INPUT PATH:  %s " % input_path + bcolors.ENDC

# ---------------------------------- CONFIG ---------------------------------- #

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

    # Build the list of existing recipes.
    # Example: ['Firefox.download.recipe']
    existing_recipes = []

    # Build the dict of buildable recipes and their corresponding
    # templates. Example: {'Firefox.jss.recipe': 'pkg.jss.recipe'}
    buildable_recipes = {}

    # Orchestrate helper functions to handle input_path's "type".
    input_type = get_input_type(input_path)
    if input_type is InputType.app:
        # Handle app input...
        pass
    elif input_type is InputType.download-recipe:
        # Handle download recipe input...
        pass


# ----------------------------------- APPS ----------------------------------- #

    if input_path[-4:] == ".app" or input_path[-5:] == ".app/":
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
                print "[ERROR] Sorry, I can't figure out what this app is called." + bcolors.ENDC
                sys.exit(1)

        # Search for existing recipes for this app.
        cmd = "autopkg search -p %s" % app_name
        exitcode, out, err = get_exitcode_stdout_stderr(cmd)
        if exitcode == 0:
            for line in out.split("\n"):
                if ".recipe" in line:
                    # Add the first "word" of each line of search
                    # results. Example: Firefox.pkg.recipe
                    existing_recipes.append(line.split(None, 1)[0])
        else:
            print err
            sys.exit(exitcode)

        # Check for a Sparkle feed, but only if a download recipe
        # doesn't exist.
        if app_name + ".download.recipe" not in existing_recipes:
            try:
                print "We found a Sparkle feed: %s" % info_plist["SUFeedURL"]
                buildable_recipes[
                    app_name + ".download.recipe"] = "download-from-sparkle.recipe"

            except KeyError, e:
                try:
                    print "We found a Sparkle feed: %s" % info_plist["SUOriginalFeedURL"]
                    buildable_recipes[
                        app_name + ".download.recipe"] = "download-from-sparkle.recipe"

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

        for recipe_format in avail_recipe_formats:
            if app_name + "." + recipe_format + ".recipe" not in existing_recipes:
                buildable_recipes[
                    # TODO: Determine proper template to use.
                    app_name + "." + recipe_format + ".recipe"] = "template TBD"

        # If munki recipe is buildable, the minimum OS version prove useful.
        if app_name + ".munki.recipe" in buildable_recipes:
            try:
                min_sys_vers = info_plist["LSMinimumSystemVersion"]
            except KeyError, e:
                if __debug_mode__:
                    print bcolors.DEBUG
                    print "[WARNING] Can't detect minimum system version." + bcolors.ENDC

# ----------------------------- DOWNLOAD RECIPES ----------------------------- #

    elif input_path[-16:] == ".download.recipe":
        if __debug_mode__:
            print bcolors.DEBUG + "\n    INPUT TYPE:  download recipe\n" + bcolors.ENDC

        # Read the recipe as a plist.
        input_recipe = plistlib.readPlist(input_path)

        # Get the app's name from the recipe.
        app_name = input_recipe["Input"]["NAME"]

        # Get the download file format.
        # TODO: Parse the recipe properly. Don't use grep.
        parsed_download_format = ""
        for download_format in supported_download_formats:
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
                    existing_recipes.append(line.split(None, 1)[0])
        else:
            print err
            sys.exit(exitcode)

        # Attempting to simultaneously determine which recipe types are
        # available to build and which templates we should use for each.
        # TODO: Make it better.
        for recipe_format in avail_recipe_formats:
            if app_name + "." + recipe_format + ".recipe" not in existing_recipes:
                if recipe_format in ("pkg", "install", "munki"):
                    buildable_recipes[
                        app_name + "." + recipe_format + ".recipe"] = recipe_format + "-from-download_" + download_format
                else:
                    buildable_recipes[
                        app_name + "." + recipe_format + ".recipe"] = recipe_format + "-from-pkg"

        # Offer to build pkg, munki, jss, etc.

# ------------------------------ MUNKI RECIPES ------------------------------- #

    elif input_path[-13:] == ".munki.recipe":
        if __debug_mode__:
            print bcolors.DEBUG + "\n    INPUT TYPE:  munki recipe\n" + bcolors.ENDC

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
                    existing_recipes.append(line.split(None, 1)[0])
        else:
            print err
            sys.exit(exitcode)

        for recipe_format in avail_recipe_formats:
            if app_name + "." + recipe_format + ".recipe" not in existing_recipes:
                buildable_recipes[
                    # TODO: Determine proper template to use.
                    app_name + "." + recipe_format + ".recipe"] = "template TBD"

        # If this munki recipe both downloads and imports the app, we
        # should offer to build a discrete download recipe with only
        # the appropriate sections of the munki recipe.

        # Offer to build pkg, jss, etc.

        # TODO: Think about whether we want to dig into OS requirements,
        # blocking applications, etc when building munki recipes. I vote
        # yes, but it's probably not going to be easy.

# ------------------------------- PKG RECIPES -------------------------------- #

    elif input_path[-11:] == ".pkg.recipe":
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
                    # Add the first "word" of each line of search
                    # results. Example: Firefox.pkg.recipe
                    existing_recipes.append(line.split(None, 1)[0])
        else:
            print err
            sys.exit(exitcode)

        for recipe_format in avail_recipe_formats:
            if app_name + "." + recipe_format + ".recipe" not in existing_recipes:
                buildable_recipes[
                    # TODO: Determine proper template to use.
                    app_name + "." + recipe_format + ".recipe"] = "template TBD"

        # Check to see whether the recipe has a download recipe as its
        # parent. If not, offer to build a discrete download recipe.

        # Offer to build munki, jss, etc.

# ------------------------------- JSS RECIPES -------------------------------- #

    elif input_path[-11:] == ".jss.recipe":
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
                    existing_recipes.append(line.split(None, 1)[0])
        else:
            print err
            sys.exit(exitcode)

        for recipe_format in avail_recipe_formats:
            if app_name + "." + recipe_format + ".recipe" not in existing_recipes:
                buildable_recipes[
                    # TODO: Determine proper template to use.
                    app_name + "." + recipe_format + ".recipe"] = "template TBD"

        # Check to see whether the recipe has a download and/or pkg
        # recipe as its parent. If not, offer to build a discrete
        # download and/or pkg recipe.

        # Offer to build other recipes as able.

    else:
        print "I haven't been trained on how to handle this input path:"
        print "    %s" % input_path
        sys.exit(1)

    if __debug_mode__:
        print bcolors.DEBUG + "\n    EXISTING RECIPES:\n"
        pprint(existing_recipes)
        print "\n    AVAILABLE RECIPE TYPES:\n"
        pprint(avail_recipe_formats)
        print "\n    BUILDABLE RECIPES:\n"
        pprint(buildable_recipes) + bcolors.ENDC

    # Prompt the user with the available recipes types and let them choose.
    print "\nHere are the recipe types available to build:"
    for key, value in buildable_recipes.iteritems():
        print "    %s" % key

    # Generate selected recipes.

    # We'll use this later when creating icons automatically!
    # cmd = 'sips -s format png "/Applications/iTunes.app/Contents/Resources/iTunes.icns" --out "/Users/elliot/Desktop/iTunes.png" --resampleHeightWidthMax 128'

if __name__ == '__main__':
    main()
