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
    -h, --help            Show this help message and exit.
    -v, --verbose         Generate additional output about the process.
'''


from pprint import pprint
from subprocess import Popen, PIPE
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
             \  [oo]
               d-||-b
                 ||
               _/  \_'''

    print welcome_text

    # Get the input path.
    try:
        input_path = str(sys.argv[1]).strip()
    except IndexError:
        print "[ERROR] Please try again, and specify a valid input path."
        raise

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
        print "    DEBUG MODE:  ON"
        print "    INPUT PATH:  %s " % input_path

    if not input_path:
        print "Please try again with a valid input path."

    else:

        # Build the list of existing recipes.
        # Example: ['Firefox.download.recipe']
        existing_recipes = []

        # Build the dict of buildable recipes and their corresponding
        # templates. Example: {'Firefox.jss.recipe': 'pkg.jss.recipe'}
        buildable_recipes = {}

        print "\nProcessing %s ..." % input_path

# ----------------------------------- APPS ----------------------------------- #

        if input_path[-4:] == ".app" or input_path[-5:] == ".app/":
            if __debug_mode__:
                print "\n    INPUT TYPE:  app\n"

            # Figure out the name of the app.
            try:
                info_plist = plistlib.readPlist(
                    input_path + "/Contents/Info.plist")
                app_name = info_plist["CFBundleName"]
            except KeyError, e:
                try:
                    app_name = info_plist["CFBundleExecutable"]
                except KeyError, e:
                    print "[ERROR] Sorry, I can't figure out what this app is called."
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
                        app_name + ".download.recipe"] = "download-from-sparkle.recipe"

                    # TODO: There was no existing download recipe, but
                    # thanks to the Sparkle feed, we now know we can build
                    # one. However, we don't know what format the resulting
                    # download will be. We need to find that out before we
                    # can create recipes that use the download as a parent.

                except KeyError, e:
                    print "[ERROR] No Sparkle feed."

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

            if __debug_mode__:
                print "\n    EXISTING RECIPES:\n"
                pprint(existing_recipes)
                print "\n    AVAILABLE RECIPE TYPES:\n"
                pprint(avail_recipe_formats)
                print "\n    BUILDABLE RECIPES:\n"
                pprint(buildable_recipes)

# ----------------------------- DOWNLOAD RECIPES ----------------------------- #

        elif input_path[-16:] == ".download.recipe":
            if __debug_mode__:
                print "\n    INPUT TYPE:  download recipe\n"

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
                raise

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

            if __debug_mode__:
                print "\n    EXISTING RECIPES:\n"
                pprint(existing_recipes)
                print "\n    AVAILABLE RECIPE TYPES:\n"
                pprint(avail_recipe_formats)
                print "\n    BUILDABLE RECIPES:\n"
                pprint(buildable_recipes)

# ------------------------------ MUNKI RECIPES ------------------------------- #

        elif input_path[-13:] == ".munki.recipe":
            if __debug_mode__:
                print "\n    INPUT TYPE:  munki recipe\n"

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
                raise

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

            if __debug_mode__:
                print "\n    EXISTING RECIPES:\n"
                pprint(existing_recipes)
                print "\n    AVAILABLE RECIPE TYPES:\n"
                pprint(avail_recipe_formats)
                print "\n    BUILDABLE RECIPES:\n"
                pprint(buildable_recipes)

# ------------------------------- PKG RECIPES -------------------------------- #

        elif input_path[-11:] == ".pkg.recipe":
            if __debug_mode__:
                print "\n    INPUT TYPE:  pkg recipe\n"

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
                raise

            for recipe_format in avail_recipe_formats:
                if app_name + "." + recipe_format + ".recipe" not in existing_recipes:
                    buildable_recipes[
                        # TODO: Determine proper template to use.
                        app_name + "." + recipe_format + ".recipe"] = "template TBD"

            # Check to see whether the recipe has a download recipe as its
            # parent. If not, offer to build a discrete download recipe.

            # Offer to build munki, jss, etc.

            if __debug_mode__:
                print "\n    EXISTING RECIPES:\n"
                pprint(existing_recipes)
                print "\n    AVAILABLE RECIPE TYPES:\n"
                pprint(avail_recipe_formats)
                print "\n    BUILDABLE RECIPES:\n"
                pprint(buildable_recipes)

# ------------------------------- JSS RECIPES -------------------------------- #

        elif input_path[-11:] == ".jss.recipe":
            if __debug_mode__:
                print "\n    INPUT TYPE:  jss recipe\n"

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
                raise

            for recipe_format in avail_recipe_formats:
                if app_name + "." + recipe_format + ".recipe" not in existing_recipes:
                    buildable_recipes[
                        # TODO: Determine proper template to use.
                        app_name + "." + recipe_format + ".recipe"] = "template TBD"

            # Check to see whether the recipe has a download and/or pkg
            # recipe as its parent. If not, offer to build a discrete
            # download and/or pkg recipe.

            # Offer to build other recipes as able.

            if __debug_mode__:
                print "\n    EXISTING RECIPES:\n"
                pprint(existing_recipes)
                print "\n    AVAILABLE RECIPE TYPES:\n"
                pprint(avail_recipe_formats)
                print "\n    BUILDABLE RECIPES:\n"
                pprint(buildable_recipes)

        else:
            print "I haven't been trained on how to handle this input path:"
            print "    %s" % input_path

        # Prompt the user with the available recipes types and let them choose.
        print "\nHere are the recipe types available to build:"
        for key, value in buildable_recipes.iteritems():
            print "    %s" % key

        # Generate selected recipes.

        # We'll use this later when creating icons automatically!
        # cmd = 'sips -s format png "/Applications/iTunes.app/Contents/Resources/iTunes.icns" --out "/Users/elliot/Desktop/iTunes.png" --resampleHeightWidthMax 128'

if __name__ == '__main__':
    main()
