#!/usr/bin/env python

# Recipe Robot
# Copyright 2015 Elliot Jordan
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


'''
recipe-robot.py

Easily and automatically create AutoPkg recipes.

usage: recipe-robot.py [-h] [-v] input_path

positional arguments:
    input_path            Path to a recipe or app you'd like to use as the basis
                          for creating AutoPkg recipes.

optional arguments:
    -h, --help            show this help message and exit
    -v, --verbose         generate additional output about the process
'''


from subprocess import Popen, PIPE
import argparse
import os.path
import plistlib
import shlex
import sys


# Global variables.
__version__ = '0.0.1'
__debug_mode__ = True  # enables additional output


def get_exitcode_stdout_stderr(cmd):
    '''Execute the external command and get its exitcode, stdout and stderr.'''
    args = shlex.split(cmd)

    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    exitcode = proc.returncode
    #
    return exitcode, out, err


def generate_recipe(app_name, recipe_type):
    '''Generates a recipe.'''
    print "Generating %s.%s.recipe..." % app_name, recipe_type

    # TODO: I'm guessing Shea is going to come in here and dump a load of
    # classes for plists and recipes. Until then, I'm using find/replace like
    # a n00b.

    pass


def main():
    '''This is where the magic happens.'''

    welcome_text = '''Welcome to Recipe Robot.

     -------------------------------
    | I'm just pseudo-code for now. |
     -------------------------------
            \   _\/_
             \  (oo)
               d-||-b
                 ||
               _/  \_'''

    print welcome_text

    # Get the total number of args passed to the script.
    input_args_count = len(sys.argv[1:])

    # Get the arguments list.
    input_args = sys.argv[1:]

    # Set the default recipe identifier prefix.
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

    # Debug mode enables additional output.
    if __debug_mode__:
        print "\n"
        print "Debug mode is on!"
        print ("Input argument count: %d " % input_args_count)
        print ("Input arguments: %s " % str(input_args))

    if input_args_count > 0:
        for input_arg in input_args:

            # Build the list of existing recipes.
            # Example: ['Firefox.download.recipe']
            existing_recipes = []

            # Build the dict of buildable recipes and their corresponding
            # templates. Example: {'Firefox.jss.recipe': 'pkg.jss.recipe'}
            buildable_recipes = {}

            print "\nProcessing %s..." % input_arg

# ----------------------------------- APPS ----------------------------------- #

            if input_arg[-4:] == ".app" or input_arg[-5:] == ".app/":
                print "%s is an app." % input_arg

                # Figure out the name of the app.
                try:
                    info_plist = plistlib.readPlist(
                        input_arg + "/Contents/Info.plist")
                    app_name = info_plist["CFBundleName"]
                except KeyError, e:
                    try:
                        app_name = info_plist["CFBundleExecutable"]
                    except KeyError, e:
                        print "Sorry, I can't figure out what this app is called."
                        raise

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
                    raise

                # Check for a Sparkle feed, but only if a download recipe
                # doesn't exist.
                if app_name + ".download.recipe" not in existing_recipes:
                    try:
                        print "We found a Sparkle feed: %s" % info_plist["SUFeedURL"]
                        buildable_recipes[
                            app_name + ".download.recipe"] = "sparkle.download.recipe"

                        # TODO: There was no existing download recipe, but
                        # thanks to the Sparkle feed, we now know we can build
                        # one. However, we don't know what format the resulting
                        # download will be. We need to find that out before we
                        # can create recipes that use the download as a parent.

                    except KeyError, e:
                        print "No Sparkle feed."

                        # TODO: Search GitHub for the app, to see if we can use
                        # the GitHubReleasesProvider processor to create a
                        # download recipe.

                        # TODO: Search SourceForge for the app, to see if we
                        # can use the SourceForgeReleasesProvider processor to
                        # create a download recipe.

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

                print "\nExisting recipes: %s" % existing_recipes
                print "\nAvailable recipe formats: %s" % avail_recipe_formats
                print "\nBuildable recipes: %s" % buildable_recipes

# ----------------------------- DOWNLOAD RECIPES ----------------------------- #

            elif input_arg[-16:] == ".download.recipe":
                print "%s is a download recipe." % input_arg

                # Read the recipe as a plist.
                input_recipe = plistlib.readPlist(input_arg)

                # Get the app's name from the recipe.
                app_name = input_recipe["Input"]["NAME"]

                # Get the download file format.
                # TODO: Parse the recipe properly. Don't use grep.
                parsed_download_format = ""
                for download_format in supported_download_formats:
                    cmd = "grep '." + download_format + "</string>' '" + input_arg + "'"
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
                    raise

                for recipe_format in avail_recipe_formats:
                    if app_name + "." + recipe_format + ".recipe" not in existing_recipes:
                        buildable_recipes[
                            # TODO: Determine proper template to use based on download_format.
                            app_name + "." + recipe_format + ".recipe"] = "template TBD"

                # Offer to build pkg, munki, jss, etc.

                print "\nExisting recipes: %s" % existing_recipes
                print "\nAvailable recipe formats: %s" % avail_recipe_formats
                print "\nBuildable recipes: %s" % buildable_recipes

# ------------------------------ MUNKI RECIPES ------------------------------- #

            elif input_arg[-13:] == ".munki.recipe":
                print "%s is a munki recipe." % input_arg
                # Determine whether there's already a download Parent recipe.
                # If not, add it to the list of offered recipe formats.

                # The following lines should probably be a definition.
                cmd = "autopkg info %s" % input_arg
                exitcode, out, err = get_exitcode_stdout_stderr(cmd)
                if exitcode == 0:
                    print out
                else:
                    print err

                # If this munki recipe both downloads and imports the app, we
                # should offer to build a discrete download recipe with only
                # the appropriate sections of the munki recipe.

                # Offer to build pkg, jss, etc.

                print "\nExisting recipes: %s" % existing_recipes
                print "\nAvailable recipe formats: %s" % avail_recipe_formats
                print "\nBuildable recipes: %s" % buildable_recipes

# ------------------------------- PKG RECIPES -------------------------------- #

            elif input_arg[-11:] == ".pkg.recipe":
                print "%s is a pkg recipe." % input_arg

                # The following lines should probably be a definition.
                cmd = "autopkg info %s" % input_arg
                exitcode, out, err = get_exitcode_stdout_stderr(cmd)
                if exitcode == 0:
                    print out
                else:
                    print err

                # Check to see whether the recipe has a download recipe as its
                # parent. If not, offer to build a discrete download recipe.

                # Offer to build munki, jss, etc.

                print "\nExisting recipes: %s" % existing_recipes
                print "\nAvailable recipe formats: %s" % avail_recipe_formats
                print "\nBuildable recipes: %s" % buildable_recipes

# ------------------------------- JSS RECIPES -------------------------------- #

            elif input_arg[-11:] == ".jss.recipe":
                print "%s is a jss recipe." % input_arg

                # The following lines should probably be a definition.
                cmd = "autopkg info %s" % input_arg
                exitcode, out, err = get_exitcode_stdout_stderr(cmd)
                if exitcode == 0:
                    print out
                else:
                    print err

                # Check to see whether the recipe has a download and/or pkg
                # recipe as its parent. If not, offer to build a discrete
                # download and/or pkg recipe.

                # Offer to build other recipes as able.

                print "\nExisting recipes: %s" % existing_recipes
                print "\nAvailable recipe formats: %s" % avail_recipe_formats
                print "\nBuildable recipes: %s" % buildable_recipes

            print "Finished processing %s" % app_name

if __name__ == '__main__':
    main()
