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

__version__ = '0.0.1'
__debug_mode__ = True

import sys
import shlex
import plistlib
from subprocess import Popen, PIPE

'''
SCRIPT LOGIC
Also see: https://www.afp548.com/2015/04/06/autopkg-download-recipe-decision-making-process/

if input is valid .app (validate_input)
    search for existing recipes (autopkg_search)
    if NSURLFeed exists in Info.plist
        if NSURLFeed is a valid Sparkle feed
            add .download to the list of available recipes
        if bundle identifier exists on a GitHub project
            add .download (with GitHubReleasesProvider) to the list of available recipes
        if bundle identifier exists on a SourceForge project
            add .download (with SourceForgeReleasesProvider) to the list of available recipes

if input is valid recipe (validate_input)
    search for existing recipes (autopkg_search)
    if recipe is .download
        if result of recipe is .zip or .tar or .tgz etc
            add .pkg (with Unarchiver processor) to the list of available recipes
        if result of recipe is .dmg
            add .pkg (with AppDmgVersioner process) to the list of available recipes
        if result of recipe is .pkg
            add .jss to the list of available recipes
    if recipe is .pkg
        add .jss to the list of available recipes
    else
        "sorry, we don't understand this recipe yet. but we're learning fast." and quit
    else
        "sorry, that's not valid input. try dragging on an app or a recipe." and quit

present user with list of recipe options, minus the existing autopkg search results
after user selects, then generate recipes

'''


def get_exitcode_stdout_stderr(cmd):
    '''Execute the external command and get its exitcode, stdout and stderr.'''
    args = shlex.split(cmd)

    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    exitcode = proc.returncode
    #
    return exitcode, out, err


def main():
    print "Welcome to Recipe Robot."
    print ""
    print "     -------------------------------"
    print "    | I'm just pseudo-code for now. |"
    print "     ------------------------------- "
    print "            \   _\/_"
    print "             \  (oo)"
    print "               d-||-b"
    print "                 ||"
    print "               _/  \_"

    # Get the total number of args passed to the script
    input_args_count = len(sys.argv[1:])

    # Get the arguments list
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

    if __debug_mode__:
        print "\n"
        print "Debug mode is on!"
        print ("Input argument count: %d " % input_args_count)
        print ("Input arguments: %s " % str(input_args))

    if input_args_count > 0:
        for input_arg in input_args:
            print "\nProcessing %s..." % input_arg

            if input_arg[-4:] == ".app":
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
                        print "Can't figure out what this app is called."
                        raise

                # Search for existing AutoPkg recipes for this app.
                # The following lines should probably be a definition.
                cmd = "autopkg search -p %s" % app_name
                exitcode, out, err = get_exitcode_stdout_stderr(cmd)
                if exitcode == 0:
                    print out
                    # Instead of printing the above, create an array of recipe
                    # names.
                else:
                    print err
                    # Can we proceed from here? Is this error recoverable?

                # Check for a Sparkle feed in the Info.plist.
                try:
                    print "We found a Sparkle feed: %s" % info_plist["SUFeedURL"]
                except KeyError, e:
                    print "No Sparkle feed."

            elif input_arg[-16:] == ".download.recipe":
                print "%s is a download recipe." % input_arg
                # Parse the recipe to determine whether it downloads a pkg or
                # zip.

                # The following lines should probably be a definition.
                cmd = "autopkg info %s" % input_arg
                exitcode, out, err = get_exitcode_stdout_stderr(cmd)
                if exitcode == 0:
                    print out
                else:
                    print err

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

            elif input_arg[-11:] == ".pkg.recipe":
                print "%s is a pkg recipe." % input_arg

                # The following lines should probably be a definition.
                cmd = "autopkg info %s" % input_arg
                exitcode, out, err = get_exitcode_stdout_stderr(cmd)
                if exitcode == 0:
                    print out
                else:
                    print err

            elif input_arg[-11:] == ".jss.recipe":
                print "%s is a jss recipe." % input_arg

                # The following lines should probably be a definition.
                cmd = "autopkg info %s" % input_arg
                exitcode, out, err = get_exitcode_stdout_stderr(cmd)
                if exitcode == 0:
                    print out
                else:
                    print err


if __name__ == '__main__':
    main()
