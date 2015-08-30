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

usage: recipe-robot.py [-h] [-v] [-o OUTPUT_DIR] [-t RECIPE_TYPES]
                       [--include-existing] [--config]
                       input_path

positional arguments:
  input_path            Path to a recipe or app from which to derive AutoPkg
                        recipes.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Generate additional output about the process.
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Path to a folder you'd like to save your generated
                        recipes in.
  -t RECIPE_TYPES, --recipe-types RECIPE_TYPES
                        The types of recipe you'd like to generate.
  --include-existing    Offer to generate recipes even if one already exists
                        on GitHub.
  --config              Adjust Recipe Robot preferences prior to generating
                        recipes.
"""


import argparse
import json
import os.path
import pprint
import random
import re
import shlex
from subprocess import Popen, PIPE
import sys
from urllib2 import urlopen
from xml.etree.ElementTree import parse

# TODO(Elliot): Can we use the one at /Library/AutoPkg/FoundationPlist instead?
try:
    import FoundationPlist
except:
    print '[WARNING] importing plistlib as FoundationPlist'
    import plistlib as FoundationPlist


# Global variables.
version = '0.0.3'
verbose_mode = False  # set to True for additional user-facing output
debug_mode = False  # set to True to output everything all the time
prefs_file = os.path.expanduser(
    "~/Library/Preferences/com.elliotjordan.recipe-robot.plist")

# Build the list of download formats we know about.
supported_image_formats = ("dmg", "iso")  # downloading iso unlikely
supported_archive_formats = ("zip", "tar.gz", "gzip", "tar.bz2", "tbz")
supported_install_formats = ("pkg", "mpkg")  # downloading mpkg unlikely
all_supported_formats = supported_image_formats + supported_archive_formats + supported_install_formats

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


def robo_print(output_type, message):
    """Print the specified message in an appropriate color, and only print
    debug output if debug_mode is True.

    Args:
        output_type: One of "error", "warning", "debug", or "verbose".
        message: String to be printed to output.
    """

    if output_type == "error":
        print >> sys.stderr, "%s[ERROR] %s%s" % (bcolors.ERROR, message, bcolors.ENDC)
        sys.exit(1)
    elif output_type == "warning":
        print >> sys.stderr, "%s[WARNING] %s%s" % (bcolors.WARNING, message, bcolors.ENDC)
    elif output_type == "reminder":
        print "%s[REMINDER] %s%s" % (bcolors.OKBLUE, message, bcolors.ENDC)
    elif output_type == "debug" and debug_mode is True:
        print "%s[DEBUG] %s%s" % (bcolors.DEBUG, message, bcolors.ENDC)
    elif output_type == "verbose":
        if verbose_mode is True or debug_mode is True:
            print message
        else:
            pass
    else:
        print message


def get_exitcode_stdout_stderr(cmd):
    """Execute the external command and get its exitcode, stdout and stderr.

    Args:
        cmd: The single shell command to be executed. No piping allowed.

    Returns:
        exitcode: Zero upon success. Non-zero upon error.
        out: String from standard output.
        err: String from standard error.
    """

    args = shlex.split(cmd)
    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    exitcode = proc.returncode
    return exitcode, out, err


def build_argument_parser():
    """Build and return the argument parser for Recipe Robot.

    Returns:
        Parser object.
    """

    parser = argparse.ArgumentParser(
        description="Easily and automatically create AutoPkg recipes.")
    parser.add_argument(
        "input_path",
        help="Path from which to derive AutoPkg recipes. This can be one of "
             "the following: existing app, existing AutoPkg recipe, Sparkle "
             "feed, GitHub or SourceForge URL, or direct download URL.")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Generate additional output about the process.")
    parser.add_argument(
        "-o", "--output-dir",
        action="store",
        help="Path to a folder you'd like to save your generated recipes in.")
    parser.add_argument(
        "-t", "--recipe-types",
        action="store",
        help="The types of recipe you'd like to generate.")
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


def init_recipes():
    """Store information related to each supported AutoPkg recipe type.

    Returns:
        A tuple of dicts that describe all the AutoPkg recipe types we know about.
    """

    recipes = ( {
            "type": "download",
            "description": "Downloads an app in whatever format the developer "
                           "provides."
        }, {
            "type": "munki",
            "description": "Imports into your Munki repository."
        }, {
            "type": "pkg",
            "description": "Creates a standard pkg installer file."
        }, {
            "type": "install",
            "description": "Installs the app on the computer running AutoPkg."
        }, {
            "type": "jss",
            "description": "Imports into your Casper JSS and creates "
                           "necessary groups, policies, etc."
        }, {
            "type": "absolute",
            "description": "Imports into your Absolute Manage server."
        }, {
            "type": "sccm",
            "description": "Creates a cmmac package for deploying via "
                           "Microsoft SCCM."
        }, {
            "type": "ds",
            "description": "Imports into your DeployStudio Packages folder."
        }
    )

    # Set default values for all recipe types.
    for recipe in recipes:
        recipe["preferred"] = True
        recipe["existing"] = False
        recipe["buildable"] = False

    return recipes


def init_prefs(prefs, recipes, args):
    """Read Recipe Robot preferences in the following priority order:
        0. If --config argument is specified, ignore prefs and rebuild.
        3. If preferences plist doesn't exist, rebuild.
        4. If preferences plist does exist, use it.

    Args:
        prefs: TODO
        recipes: TODO
        args: TODO

    Returns:
        prefs: TODO
    """

    prefs = {}
    global prefs_file

    # If prefs file exists, try to read from it.
    if os.path.isfile(prefs_file):

        # Open the file.
        try:
            prefs = FoundationPlist.readPlist(prefs_file)
        except Exception:
            robo_print("warning",
                       "There was a problem opening the prefs file. Building "
                       "new preferences.")
            prefs = build_prefs(prefs, recipes)

        for recipe in recipes:
            # Load preferred recipe types.
            if recipe["type"] in prefs["RecipeTypes"]:
                recipe["preferred"] = True
            else:
                recipe["preferred"] = False

        if args.config is True:
            robo_print("log", "Showing configuration options...")
            prefs = build_prefs(prefs, recipes)

        # This seems to be necessary in order to avoid an error when reading
        # the plist back during subsequent runs.
        prefs["RecipeCreateCount"] = int(prefs["RecipeCreateCount"])

    else:
        robo_print("warning", "No prefs file found. Building new preferences...")
        prefs = build_prefs(prefs, recipes)

    # Record last version number.
    prefs["LastRecipeRobotVersion"] = version

    # Save preferences to disk for next time.
    FoundationPlist.writePlist(prefs, prefs_file)

    return prefs


def build_prefs(prefs, recipes):
    """Prompt user for preferences, then save them back to the plist.

    Args:
        prefs: TODO
        recipes: TODO

    Returns:
        prefs: TODO
    """

    # Start recipe count at zero, if no value already exists.
    if "RecipeCreateCount" not in prefs:
        prefs["RecipeCreateCount"] = int(0)

    # Prompt for and save recipe identifier prefix.
    prefs["RecipeIdentifierPrefix"] = "com.github.homebysix"
    robo_print("log", "\nRecipe identifier prefix")
    robo_print("log", "This is your default identifier, in reverse-domain notation.\n")
    choice = raw_input(
        "[%s]: " % prefs["RecipeIdentifierPrefix"])
    if choice != "":
        prefs["RecipeIdentifierPrefix"] = str(choice).rstrip(". ")

    # Prompt for recipe creation location.
    prefs["RecipeCreateLocation"] = "~/Library/AutoPkg/RecipeOverrides"
    robo_print("log", "\nLocation to save new recipes")
    robo_print("log", "This is where on disk your newly created recipes will be saved.\n")
    choice = raw_input(
        "[%s]: " % prefs["RecipeCreateLocation"])
    if choice != "":
        prefs["RecipeCreateLocation"] = str(choice).rstrip("/ ")

    # Prompt to set recipe types on/off as desired.
    prefs["RecipeTypes"] = []
    robo_print("log", "\nPreferred recipe types")
    robo_print("log", "Choose which recipe types will be offered to you by default.\n")
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
                       (indicator, i, recipe["type"], recipe["description"]))
            i += 1
        robo_print("log", "      A. Enable all recipe types.")
        robo_print("log", "      D. Disable all recipe types.")
        robo_print("log", "      Q. Quit without saving changes.")
        robo_print("log", "      S. Save changes and proceed.")
        choice = raw_input(
            "\nType a number to toggle the corresponding recipe "
            "type between ON [*] and OFF [ ].\nWhen you're satisfied "
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
                robo_print("warning",
                           "%s is not a valid option. Please try "
                           "again.\n" % choice)

    # Set "preferred" status of each recipe type according to preferences.
    for recipe in recipes:
        if recipe["preferred"] is True:
            prefs["RecipeTypes"].append(recipe["type"])

            if recipe["type"] == "ds":
                prefs["DSPackagesPath"] = "/Shared/DeployStudio/Packages"
                robo_print("log", "\nLocation of your DeployStudio packages:")
                robo_print("log", "This where packages will be copied in order to "
                                  "appear in DeployStudio.\n")
                choice = raw_input(
                    "[%s]: " % prefs["DSPackagesPath"])
                if choice != "":
                    prefs["DSPackagesPath"] = str(choice).rstrip("/ ")

    return prefs

def process_input_path(input_path, args, facts):
    """Determine which functions to call based on the type of input path.

    Args:
        input_path: TODO
    """

    if input_path.startswith("http"):
        if input_path.endswith(".xml") or input_path.endswith(".php"):
            robo_print("verbose", "Input path looks like a Sparkle feed.")
            facts = inspect_sparkle_feed_url(input_path, args, facts)
        elif "github.com" in input_path or "githubusercontent.com" in input_path:
            robo_print("verbose", "Input path looks like a GitHub URL.")
            facts = inspect_github_url(input_path, args, facts)
        elif "sourceforge.net" in input_path:
            robo_print("verbose", "Input path looks like a SourceForge URL.")
            facts = inspect_sourceforge_url(input_path, args, facts)
        elif "bitbucket.org" in input_path:
            # TODO(Elliot): Also support BitBucket.
            robo_print("verbose", "Input path looks like a BitBucket URL.")
            robo_print("error", "Sorry, I don't yet speak BitBucket.")
        else:
            robo_print("verbose", "Input path looks like another kind of URL.")
            robo_print("error",
                       "Sorry, my programmer hasn't told me what to do with "
                       "that URL yet.")
            # TODO(Elliot): Some Sparkle feeds don't have .xml extensions.
            # Otherwise this is probably a direct download.
            pass
    elif input_path.startswith("ftp"):
        robo_print("verbose", "Input path looks like a download URL.")
        facts = inspect_download_url(input_path, args, facts)
    elif os.path.exists(input_path):
        if input_path.endswith(".app"):
            robo_print("verbose", "Input path looks like an app.")
            facts = inspect_app(input_path, args, facts)
        elif input_path.endswith(".recipe"):
            robo_print("verbose", "Input path looks like a recipe.")
            facts = inspect_recipe(input_path, args, facts)
        else:
            robo_print("error",
                       "I haven't been trained on how to handle this "
                       "input path:\n    %s" % input_path)
    else:
        robo_print("error",
                   "Input path does not exist. Please try again with a "
                   "valid input path.")


def get_app_description(app_name):
    """Use an app's name to generate a description from MacUpdate.com.

    Args:
        app_name: TODO

    Returns:
        description: A string containing a description of the app.
    """

    # Start with an empty string. (If it remains empty, the parent function
    # will know that no description was available.)
    description = ""

    # This is the HTML immediately preceding the description text on the
    # MacUpdate search results page.
    description_marker = "-shortdescrip\">"

    cmd = "curl -s \"http://www.macupdate.com/find/mac/%s\"" % app_name
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)

    # For each line in the resulting text, look for the description marker.
    html = out.split("\n")
    if exitcode == 0:
        for line in html:
            if description_marker in line:
                # Trim the HTML from the beginning of the line.
                start = line.find(description_marker) + len(description_marker)
                # Trim the HTML from the end of the line.
                description = line[start:].rstrip("</span>")
                # If we found a description, no need to process further lines.
                break
    else:
        robo_print("warning",
                   "Error occurred while getting description from "
                   "MacUpdate: %s" % err)

    return description


def inspect_github_url(input_path, args, facts):
    """Process a GitHub URL, gathering required information to create a
    recipe.

    Args:
        input_path: TODO
        args: TODO
        facts: TODO
    """

    # Grab the GitHub repo path.
    github_repo = ""
    robo_print("verbose", "Getting GitHub repo...")
    input_path = input_path.replace("raw.githubusercontent.com", "github.com")
    r_obj = re.search(r"(?<=https://github\.com/)[\w-]+/[\w-]+", input_path)
    if r_obj is not None:
        github_repo = r_obj.group(0)
    if github_repo != "":
        robo_print("verbose", "    GitHub repo is: %s" % github_repo)
        facts["github_repo"] = github_repo

        # TODO(Elliot): How can we use GitHub tokens to prevent rate limiting?

        # Use GitHub API to obtain project information.
        repo_api_url = "https://api.github.com/repos/" + github_repo
        try:
            raw_json = urlopen(repo_api_url).read()
            parsed_json = json.loads(raw_json)
        except Exception as err:
            robo_print("warning",
                       "Error occurred while talking to GitHub. If you've "
                       "been creating a lot of recipes quickly, you may have "
                       "hit the rate limit. Give it a few minutes, then try "
                       "again. (%s)" % err)
            return facts

        # Get app name.
        if "app_name" not in facts:
            app_name = ""
            robo_print("verbose", "Getting app name...")
            if "name" in parsed_json:
                if parsed_json["name"] != "":
                    app_name = parsed_json["name"]
            if app_name != "":
                robo_print("verbose", "    App name is: %s" % app_name)
                facts["app_name"] = app_name

        # Get app description.
        if "description" not in facts:
            description = ""
            robo_print("verbose", "Getting GitHub description...")
            if "description" in parsed_json:
                if parsed_json["description"] != "":
                    description = parsed_json["description"]
            if description != "":
                robo_print("verbose", "    GitHub description is: %s" % description)
                facts["description"] = description
            else:
                robo_print("warning", "Could not detect GitHub description.")

        # Warn user if the GitHub project is private.
        if "private" in parsed_json:
            if parsed_json["private"] is True:
                robo_print("warning",
                           "This GitHub project is marked \"private\" "
                           "and recipes you generate may not work for others.")

        # Warn user if the GitHub project is a fork.
        if "private" in parsed_json:
            if parsed_json["fork"] is True:
                robo_print("warning",
                           "This GitHub project is a fork. You may want to "
                           "try again with the original repo URL instead.")
    else:
        robo_print("warning", "Could not detect GitHub repo.")

    return facts


def inspect_sourceforge_url(input_path, args, facts):
    """Process a SourceForge URL, gathering required information to create a
    recipe.

    Args:
        input_path: TODO
        args: TODO
        facts: TODO
    """

    # Determine the name of the SourceForge project.
    proj_name = ""
    robo_print("verbose", "Determining name of SourceForge project...")
    # TODO(Elliot): Is it better to do this with re.search()?
    if  "/projects/" in input_path:
        # Example: http://sourceforge.net/projects/adium/?source=recommended
        # Example: http://sourceforge.net/projects/grandperspectiv
        # Example: http://sourceforge.net/projects/grandperspectiv/
        marker = "/projects/"
        proj_str = input_path[input_path.find(marker) + len(marker):]
        if proj_str.find("/") > 0:
            proj_name = proj_str[:proj_str.find("/")]
        else:
            proj_name = proj_str
    elif "/p/" in input_path:
        # Example: http://sourceforge.net/p/grandperspectiv/wiki/Home/
        marker = "/p/"
        proj_str = input_path[input_path.find(marker) + len(marker):]
        if proj_str.find("/") > 0:
            proj_name = proj_str[:proj_str.find("/")]
        else:
            proj_name = proj_str
    elif ".sourceforge.net" in input_path:
        # Example: http://grandperspectiv.sourceforge.net/
        # Example: http://grandperspectiv.sourceforge.net/screenshots.html
        marker = ".sourceforge.net"
        proj_str = input_path.lstrip("http://")
        proj_name = proj_str[:proj_str.find(marker)]
    else:
        robo_print("warning", "Unable to parse SourceForge URL.")
    if proj_name != "":

        # Use SourceForge API to obtain project information.
        project_api_url = "https://sourceforge.net/rest/p/" + proj_name
        raw_json = urlopen(project_api_url).read()
        parsed_json = json.loads(raw_json)

        # Get app name.
        if "app_name" not in facts:
            if "shortname" in parsed_json or "name" in parsed_json:
                # Record the shortname, if shortname isn't blank.
                if parsed_json["shortname"] != "":
                    app_name = parsed_json["shortname"]
                # Overwrite the shortname with name, if name isn't blank.
                if parsed_json["name"] != "":
                    app_name = parsed_json["name"]
            if app_name != "":
                robo_print("verbose", "    App name is: %s" % app_name)
                facts["app_name"] = app_name

        # Determine project ID.
        proj_id = ""
        robo_print("verbose", "Getting SourceForge project ID...")
        for this_dict in parsed_json["tools"]:
            if "sourceforge_group_id" in this_dict:
                proj_id = this_dict["sourceforge_group_id"]
        if proj_id != "":
            robo_print("verbose", "    SourceForge project ID is: %s" % proj_id)
            facts["sourceforge_proj_id"] = proj_id
        else:
            robo_print("warning", "Could not detect SourceForge project ID.")

        # Get project description.
        if "description" not in facts:
            description = ""
            robo_print("verbose", "Getting SourceForge description...")
            if "summary" in parsed_json:
                if parsed_json["summary"] != "":
                    description = parsed_json["summary"]
                elif parsed_json["short_description"] != "":
                    description = parsed_json["short_description"]
            if description != "":
                robo_print("verbose", "    SourceForge description is: %s" % description)
                facts["description"] = description
            else:
                robo_print("warning", "Could not detect SourceForge description.")

        # Warn user if the SourceForge project is private.
        if "private" in parsed_json:
            if parsed_json["private"] is True:
                robo_print("warning",
                           "This SourceForge project is marked \"private\" "
                           "and recipes you generate may not work for others.")

        # TODO(Elliot): Can we make use of parsed_json["icon"]?
        # Example: https://sourceforge.net/p/adium/icon

    else:
        robo_print("warning", "Could not detect SourceForge project name.")

    return facts


def inspect_sparkle_feed_url(input_path, args, facts):
    """Process a Sparkle feed URL, gathering required information to create a
    recipe.

    Args:
        input_path: TODO
        args: TODO
        facts: TODO
    """

    # Save the Sparkle feed URL to the dictionary of facts.
    robo_print("verbose", "    Sparkle feed is: %s" % input_path)
    facts["sparkle_feed"] = input_path

    # Download the Sparkle feed and parse it.
    html = urlopen(input_path)
    doc = parse(html)

    # Get the latest download URL.
    download_url = ""
    robo_print("verbose", "Determining download URL from Sparkle feed...")
    for item in doc.iterfind('channel/item/enclosure'):
        download_url = item.attrib["url"]
        break  # should stop after the most recent (first) enclosure item
    if download_url != "":
        facts = inspect_download_url(download_url, args, facts)

    # If Sparkle feed is hosted on GitHub, we can gather more information.
    if "github_repo" not in facts:
        if "github.com" in input_path or "githubusercontent.com" in input_path:
            facts = inspect_github_url(input_path, args, facts)

    return facts


def inspect_download_url(input_path, args, facts):
    """Process a direct download URL, gathering required information to
    create a recipe.

    Args:
        input_path: TODO
        args: TODO
        facts: TODO
    """

    # Save the download URL to the dictionary of facts.
    robo_print("verbose", "    Download URL is: %s" % input_path)
    facts["download_url"] = input_path

    # Try to determine the type of file downloaded. (Overwrites any previous
    # download_type, because the download URL is the most reliable source.)
    download_format = ""
    robo_print("verbose", "Determining download type from download URL...")
    filename = input_path.split("/")[-1]
    for this_format in all_supported_formats:
        if filename.endswith(this_format):
            download_format = this_format
            break  # should stop after the first format match
    if download_format != "":
        robo_print("verbose", "    Download format is: %s" % download_format)
        facts["download_format"] = download_format

    # If download URL is hosted on GitHub, we can gather more information.
    if "github_repo" not in facts:
        if "github.com" in input_path or "githubusercontent.com" in input_path:
            facts = inspect_github_url(input_path, args, facts)

    # Download the file for continued inspection.
    # TODO(Elliot): Maybe something like this is better for downloading big
    # files? https://gist.github.com/gourneau/1430932
    # robo_print("verbose", "Downloading file for further inspection...")
    # f = urlopen(input_path)
    # tmp_path = "/tmp/%s" % filename
    # with open(tmp_path, "wb") as code:
    #     code.write(f.read())
    #     robo_print("verbose", "    Downloaded to %s" % tmp_path)

    # TODO(Elliot): Further processing of downloaded files.
    if download_format in supported_image_formats:
        # Mount the dmg and look for an app.
        pass
    elif download_format in supported_archive_formats:
        # Unzip the zip and look for an app.
        pass
    elif download_format in supported_install_formats:
        # Use pkgutil to extract contents and look for an app.
        pass

    # TODO(Elliot): Delete file from /tmp.

    return facts


def inspect_app(input_path, args, facts):
    """Process an app, gathering required information to create a recipe.

    Args:
        input_path: TODO
        args: TODO
        facts: TODO
    """

    # Read the app's Info.plist.
    robo_print("verbose", "Validating app...")
    try:
        info_plist = FoundationPlist.readPlist(input_path + "/Contents/Info.plist")
        robo_print("verbose", "    App seems valid")
    except Exception:
        robo_print("error", "This doesn't look like a valid app to me.")

    # Get the filename of the app (which is usually the same as the app name.)
    app_file = os.path.basename(input_path)[:-4]

    # Determine the name of the app. (Overwrites any previous app_name, because
    # the app Info.plist itself is the most reliable source.)
    app_name = ""
    robo_print("verbose", "Getting name of software...")
    if "CFBundleName" in info_plist:
        app_name = info_plist["CFBundleName"]
    elif "CFBundleExecutable" in info_plist:
        app_name = info_plist["CFBundleExecutable"]
    else:
        app_name = app_file
    robo_print("verbose", "    Software name is: %s" % app_name)
    facts["app_name"] = app_name

    # If the app's filename is different than the app's name, we need to make
    # a note of that. Many recipes require another input variable for this.
    if app_name != app_file:
        robo_print("verbose", "Software name differs from the bundle filename.")
        robo_print("verbose", "    Bundle filename: %s.app" % app_file)
        facts["app_file"] = app_file

    # Determine the bundle identifier of the app.
    if "bundle_id" not in facts:
        bundle_id = ""
        robo_print("verbose", "Getting bundle identifier...")
        if "CFBundleIdentifier" in info_plist:
            bundle_id = info_plist["CFBundleIdentifier"]
        else:
            robo_print("warning", "This app doesn't have a bundle identifier.")
        if bundle_id != "":
            robo_print("verbose", "    Bundle idenfitier is: %s" % bundle_id)
            facts["bundle_id"] = bundle_id

    # Attempt to determine how to download this app.
    if "sparkle_feed" not in facts:
        sparkle_feed = ""
        download_format = ""
        robo_print("verbose", "Checking for a Sparkle feed in SUFeedURL...")
        if "SUFeedURL" in info_plist:
            sparkle_feed = info_plist["SUFeedURL"]
            facts = inspect_sparkle_feed_url(sparkle_feed, args, facts)
        elif "SUOriginalFeedURL" in info_plist:
            sparkle_feed = info_plist["SUOriginalFeedURL"]
            facts = inspect_sparkle_feed_url(sparkle_feed, args, facts)
        else:
            robo_print("warning", "This app doesn't have a Sparkle feed.")

    # TODO(Elliot): Are there ways to download other than Sparkle that are
    # exposed in the app's Info.plist?

    # Determine whether to use CFBundleShortVersionString or
    # CFBundleVersionString for versioning.
    if "version_key" not in facts:
        version_key = ""
        robo_print("verbose", "Looking for version key...")
        if "CFBundleShortVersionString" in info_plist:
            # TODO(Elliot): Validate whether this is a true version.
            version_key = "CFBundleShortVersionString"
        elif "CFBundleVersionString" in info_plist:
            # TODO(Elliot): Validate whether this is a true version.
            version_key = "CFBundleVersionString"
        else:
            robo_print("warning", "Can't determine which key to use for version.")
        if version_key != "":
            robo_print("verbose", "    Version key is: %s" % version_key)
            facts["version_key"] = version_key

    # Determine path to the app's icon.
    if "icon_path" not in facts:
        icon_path = ""
        robo_print("verbose", "Looking for app icon...")
        if "CFBundleIconFile" in info_plist:
            icon_path = "%s/Contents/Resources/%s" % (
                input_path, info_plist["CFBundleIconFile"])
        else:
            robo_print("warning", "Can't determine app icon.")
        if icon_path != "":
            robo_print("verbose", "    App icon is: %s" % icon_path)
            facts["icon_path"] = icon_path

    # Attempt to get a description of the app from MacUpdate.com.
    if "description" not in facts:
        robo_print("verbose", "Getting app description from MacUpdate...")
        description = get_app_description(app_name)
        if description != "":
            robo_print("verbose", "    Description: %s" % description)
            facts["description"] = description

    # Attempt to determine code signing verification/requirements.
    if "codesign_status" not in facts:
        codesign_status = ""
        codesign_reqs = ""
        robo_print("verbose", "Determining whether app is codesigned...")
        cmd = "codesign --display -r- \"%s\"" % (input_path)
        exitcode, out, err = get_exitcode_stdout_stderr(cmd)
        if exitcode == 0:
            codesign_status = "signed"
            # Determine code signing requirements.
            marker = "designated => "
            for line in out.split("\n"):
                if line.startswith(marker):
                    codesign_reqs = line[len(marker):]
        else:
            codesign_status = "unsigned"
        robo_print("verbose", "    Codesign status is: %s" % codesign_status)
        facts["codesign_status"] = codesign_status
        if codesign_reqs != "":
            robo_print("verbose", "    Codesign requirements are: %s" % codesign_reqs)
            facts["codesign_reqs"] = codesign_reqs

    # TODO(Elliot): Collect other information as required to build recipes.
    #    - Use bundle identifier to locate related helper apps on disk?
    #    - App category... maybe prompt for that if JSS recipe is selected.

    # Send the information we discovered to the recipe keys.
    return facts


def inspect_recipe(input_path, args, facts):
    """Process a recipe, gathering information useful for building other types
    of recipes.

    Args:
        input_path: TODO
        args: TODO
        facts: TODO
    """

    # Read the recipe as a plist.
    robo_print("verbose", "Validating recipe...")
    try:
        input_recipe = FoundationPlist.readPlist(input_path)
    except Exception:
        robo_print("warning", "Could not parse recipe as a plist.")

    # Run autopkg info on the recipe and save the output.
    cmd = "autopkg info %s" % input_path
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if exitcode == 0:
        out = out.split("\n")
    else:
        robo_print("warning", "Could not run \"autopkg info\" on recipe.")

    # Determine the name of the app.
    if "app_name" not in facts:
        app_name = ""
        robo_print("verbose", "Getting name of app...")
        if "Input" in input_recipe:
            if "NAME" in input_recipe["Input"]:
                app_name = input_recipe["Input"]["NAME"]
        robo_print("verbose", "    App name is: %s" % app_name)

    # Determine parent recipe, and get more facts from it.
    marker = "Parent recipe(s):"
    robo_print("verbose", "Looking for a parent recipe...")
    for line in out:
        if marker in line:
            parent_recipe_path = line[len(marker):].lstrip()
            robo_print("verbose", "    Parent recipe is: %s" % parent_recipe_path)
            facts = inspect_recipe(parent_recipe_path, args, facts)

    # Determine whether there's a Sparkle feed.
    if "sparkle_feed" not in facts:
        marker = "SPARKLE"
        robo_print("verbose", "Looking for a Sparkle feed...")
        for line in out:
            if marker in line:
                sparkle_feed = line[len(marker):].lstrip()
                robo_print("verbose", "    Sparkle feed is: %s" % sparkle_feed)
                facts = inspect_sparkle_feed_url(sparkle_feed, args, facts)

    # Determine whether there's a download URL.
    if "download_url" not in facts:
        marker = "DOWNLOAD_URL"
        robo_print("verbose", "Looking for a direct download URL...")
        for line in out:
            if marker in line:
                download_url = line[len(marker):].lstrip()
                facts = inspect_download_url(download_url, args, facts)

    # Get the download file format.
    if "download_format" not in facts:
        download_format = ""
        robo_print("verbose", "Trying to determine download format...")
        for test_format in all_supported_formats:
            cmd = "grep '.%s</string>' '%s'" % (test_format, input_path)
            exitcode, out, err = get_exitcode_stdout_stderr(cmd)
            if exitcode == 0:
                download_format = test_format
                break
        if download_format != "":
            robo_print("verbose", "    Download format (from recipe) is: %s" % download_format)
            facts["download_format"] = download_format

    # Run the recipe and inspect the resulting app.
    # robo_print("verbose", "Running recipe to see what we get...")
    # cmd = "autopkg run \"%s\"" % input_path
    # exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    # if exitcode == 0:
    #     pass

    return facts


def create_existing_recipe_list(app_name, recipes, args):
    """Use autopkg search results to build existing recipe list.

    Args:
        app_name: TODO
        recipes: TODO
    """

    # TODO(Elliot): Suggest users create GitHub API token to prevent limiting.

    # If --include-existing is specified, no need to search at all.
    if args.include_existing is True:
        return

    recipe_searches = []
    recipe_searches.append(app_name)

    app_name_no_space = "".join(app_name.split())
    if app_name_no_space != app_name:
        recipe_searches.append(app_name_no_space)

    app_name_no_symbol = re.sub(r'[^\w]', '', app_name)
    if app_name_no_symbol != app_name and app_name_no_symbol != app_name_no_space:
        recipe_searches.append(app_name_no_symbol)

    for this_search in recipe_searches:
        robo_print("verbose", "Searching for existing AutoPkg recipes for %s..." % this_search)
        cmd = "/usr/local/bin/autopkg search -p \"%s\"" % this_search
        exitcode, out, err = get_exitcode_stdout_stderr(cmd)
        out = out.split("\n")
        if exitcode == 0:
            # TODO(Elliot): There's probably a more efficient way to do this.
            # For each recipe type, see if it exists in the search results.
            for recipe in recipes:
                recipe_name = "%s.%s.recipe" % (this_search, recipe["type"])
                for line in out:
                    if recipe_name.lower() in line.lower():
                        # Set to False by default. If found, set to True.
                        recipe["existing"] = True
                        robo_print("verbose", "    Found existing %s." % recipe_name)
                        break
        else:
            robo_print("error", err)


def create_buildable_recipe_list(app_name, recipes, args, facts):
    """Add any preferred recipe types that don't already exist to the buildable
    list.

    Args:
        app_name: TODO
        recipes: TODO
        args: TODO
        facts: TODO
    """

    # Determine which recipes are buildable based on "preferred" preference
    # values and the --include-existing argument.
    for recipe in recipes:
        if args.include_existing is False:
            if recipe["preferred"] is True and recipe["existing"] is False:
                recipe["buildable"] = True
        else:
            if recipe["preferred"] is True:
                recipe["buildable"] = True

    # TODO(Elliot):  Do we also need to consider which facts we have collected
    # at this point? For example, if we didn't find a Sparkle URL or any other
    # way to download the app, it's unlikely that we can produce a download
    # recipe.


def generate_recipes(facts, prefs, recipes):
    """Generate the selected types of recipes.

    Args:
        prefs: TODO
        recipes: TODO
    """

    preferred_recipe_count = 0
    for recipe in recipes:
        if recipe["buildable"] is True:

            # Count the number of preferred recipes.
            preferred_recipe_count += 1

            # Construct the default keys common to all recipes.
            recipe["keys"] = {
                "Identifier": "",
                "MinimumVersion": "0.5.0",
                "Input": {
                    "NAME": facts["app_name"]
                },
                "Process": [],
                "Comment": "Generated by Recipe Robot v%s "
                           "(https://github.com/homebysix/recipe-robot)" % version
            }

    # All known recipe types already appear in "autopkg search" results.
    if preferred_recipe_count == 0:
        robo_print("log", "Sorry, no recipes available to generate.")

    # We don't have enough information to create a recipe set.
    if("download_format" not in facts
           or "app_name" not in facts
          or "bundle_id" not in facts):
        robo_print("error",
                   "Sorry, we're missing some crucial information and can't "
                   "build recipes for this app.")

    for recipe in recipes:
        if recipe["buildable"] is True:
            keys = recipe["keys"]

            # Set the recipe filename (no spaces, except JSS recipes).
            filename = "%s.%s.recipe" % (
                facts["app_name"].replace(" ", ""), recipe["type"])

            # Set the recipe identifier.
            keys["Identifier"] = "%s.%s.%s" % (prefs["RecipeIdentifierPrefix"],
                                               recipe["type"],
                                               facts["app_name"].replace(" ", ""))

            # If the name of the app bundle differs from the name of the app
            # itself, we need another input variable for that.
            if "app_file" in facts:
                keys["Input"]["APP_FILENAME"] = facts["app_file"]
                app_name_key = "%APP_FILENAME%"
            else:
                app_name_key = "%NAME%"

            # Set keys specific to download recipes.
            if recipe["type"] == "download":

                robo_print("log", "Generating %s recipe..." % recipe["type"])

                # Save a description that explains what this recipe does.
                keys["Description"] = ("Downloads the latest version "
                                       "of %s." % facts["app_name"])

                if "sparkle_feed" in facts:
                    keys["Input"]["SPARKLE_FEED_URL"] = facts["sparkle_feed"]
                    keys["Process"].append({
                        "Processor": "SparkleUpdateInfoProvider",
                        "Arguments": {
                            "appcast_url": "%SPARKLE_FEED_URL%"
                        }
                    })
                    keys["Process"].append({
                        "Processor": "URLDownloader",
                        "Arguments": {
                            "filename": "%%NAME%%-%%version%%.%s" % facts["download_format"]
                        }
                    })
                elif "github_repo" in facts:
                    keys["Input"]["GITHUB_REPO"] = facts["github_repo"]
                    recipe["keys"]["Process"].append({
                        "Processor": "GitHubReleasesInfoProvider",
                        "Arguments": {
                            "github_repo": "%GITHUB_REPO%"
                        }
                    })
                    keys["Process"].append({
                        "Processor": "URLDownloader",
                        "Arguments": {
                            "filename": "%%NAME%%-%%version%%.%s" % facts["download_format"]
                        }
                    })
                elif "sourceforge_id" in facts:
                    keys["Input"]["SOURCEFORGE_PROJECT_ID"] = facts["sourceforge_id"]
                    recipe["keys"]["Process"].append({
                        "Processor": "SourceForgeURLProvider"
                    })
                    keys["Process"].append({
                        "Processor": "URLDownloader",
                        "Arguments": {
                            "filename": "%%NAME%%-%%version%%.%s" % facts["download_format"]
                        }
                    })
                elif "download_url" in facts:
                    keys["Input"]["DOWNLOAD_URL"] = facts["download_url"]
                    keys["Process"].append({
                        "Processor": "URLDownloader",
                        "Arguments": {
                            "url": "%DOWNLOAD_URL%"
                        }
                    })
                keys["Process"].append({
                    "Processor": "EndOfCheckPhase"
                })

                if facts["codesign_status"] == "signed":
                    if facts["download_format"] in supported_image_formats:
                        keys["Process"].append({
                            "Processor": "CodeSignatureVerifier",
                            "Arguments": {
                                # TODO(Elliot): What if the app name isn't the same as %NAME%?
                                "input_path": "%%pathname%%/%s.app" % app_name_key,
                                "requirement": facts["codesign_reqs"]
                            }
                        })
                    elif facts["download_format"] in supported_archive_formats:
                        keys["Process"].append({
                            "Processor": "Unarchiver",
                            "Arguments": {
                                "archive_path": "%pathname%",
                                "destination_path": "%RECIPE_CACHE_DIR%/%NAME%/Applications",
                                "purge_destination": True
                            }
                        })
                        keys["Process"].append({
                            "Processor": "CodeSignatureVerifier",
                            "Arguments": {
                                "input_path": "%%RECIPE_CACHE_DIR%%/%%NAME%%/Applications/%s.app" % app_name_key,
                                "requirement": facts["codesign_reqs"]
                            }
                        })
                        keys["Process"].append({
                            "Processor": "Versioner",
                            "Arguments": {
                                "input_plist_path": "%%RECIPE_CACHE_DIR%%/%%NAME%%/Applications/%s.app/Contents/Info.plist" % app_name_key,
                                "plist_version_key": facts["version_key"]
                            }
                        })

                    elif facts["download_format"] in supported_install_formats:
                        # TODO(Elliot): Check for signed .pkg files.
                        robo_print("warning",
                                   "Sorry, I don't yet know how to use "
                                   "CodeSignatureVerifier with pkg downloads.")
                        continue

            # Set keys specific to munki recipes.
            elif recipe["type"] == "munki":

                robo_print("log", "Generating %s recipe..." % recipe["type"])

                # Save a description that explains what this recipe does.
                keys["Description"] = ("Downloads the latest version of %s "
                                      "and imports it into "
                                      "Munki" % facts["app_name"])

                # Specify the Munki repo subdirectory.
                keys["Input"]["MUNKI_REPO_SUBDIR"] = "apps/%NAME%"

                # Save Munki pkginfo.
                keys["Input"]["pkginfo"] = {
                    "catalogs": ["testing"],
                    "display_name": facts["app_name"],
                    "name": "%NAME%",
                    "unattended_install": True
                }

                if "description" in facts:
                    keys["Input"]["pkginfo"]["description"] = facts["description"]
                else:
                    robo_print("reminder",
                               "I couldn't find a description for this app, "
                               "so you'll need to manually add one to the "
                               "munki recipe.")
                    keys["Input"]["pkginfo"]["description"] = " "

                # Make the download recipe the parent of the Munki recipe.
                # TODO(Elliot): What if it's somebody else's download recipe?
                keys["ParentRecipe"] = "%s.download.%s" % (prefs["RecipeIdentifierPrefix"], facts["app_name"].replace(" ", ""))

                import_file_var = "%pathname%"

                if facts["download_format"] in supported_image_formats and "sparkle_feed" not in facts:
                    # It's a dmg download, but not from Sparkle, so we need to version it.
                    keys["Process"].append({
                        "Processor": "Versioner",
                        "Arguments": {
                            "input_plist_path": "%%pathname%%/%s.app/Contents/Info.plist" % app_name_key,
                            "plist_version_key": facts["version_key"]
                        }
                    })

                elif facts["download_format"] in supported_archive_formats:
                    if facts["codesign_status"] == "unsigned":
                        # If unsigned, that means the download recipe hasn't
                        # unarchived the zip yet.
                        keys["Process"].append({
                            "Processor": "Unarchiver",
                            "Arguments": {
                                "archive_path": "%pathname%",
                                "destination_path": "%RECIPE_CACHE_DIR%/%NAME%/Applications",
                                "purge_destination": True
                            }
                        })
                    keys["Process"].append({
                        "Processor": "DmgCreator",
                        "Arguments": {
                            "dmg_path": "%RECIPE_CACHE_DIR%/%NAME%.dmg",
                            "dmg_root": "%RECIPE_CACHE_DIR%/%NAME%/Applications"
                        }
                    })
                    import_file_var = "%dmg_path%"

                elif facts["download_format"] in supported_install_formats:
                    # TODO(Elliot): Put pkg in dmg?
                    keys["Input"]["pkginfo"]["blocking_applications"] = "%s.app" % app_name_key
                    robo_print("warning",
                               "Sorry, I don't yet know how to create "
                               "munki recipes from pkg downloads.")
                    continue

                keys["Process"].append({
                    "Processor": "MunkiImporter",
                    "Arguments": {
                        "pkg_path": import_file_var,
                        "repo_subdirectory": "%MUNKI_REPO_SUBDIR%",
                        "version_comparison_key": facts["version_key"]
                    }
                })

                # Extract the app's icon and save it to disk.
                extracted_icon = "%s/%s.png" % (prefs["RecipeCreateLocation"],
                                                facts["app_name"])
                extract_app_icon(facts["icon_path"], extracted_icon)

            # Set keys specific to pkg recipes.
            elif recipe["type"] == "pkg":

                robo_print("log", "Generating %s recipe..." % recipe["type"])

                # Save a description that explains what this recipe does.
                keys["Description"] = ("Downloads the latest version of %s and "
                                      "creates a package." % facts["app_name"])

                # Save bundle identifier.
                keys["Input"]["BUNDLE_ID"] = facts["bundle_id"]

                # Make the download recipe the parent of the Munki recipe.
                # TODO(Elliot): What if it's somebody else's download recipe?
                keys["ParentRecipe"] = "%s.download.%s" % (prefs["RecipeIdentifierPrefix"], facts["app_name"].replace(" ", ""))

                if facts["download_format"] in supported_image_formats:
                    keys["Process"].append({
                        "Processor": "PkgRootCreator",
                        "Arguments": {
                            "pkgroot": "%RECIPE_CACHE_DIR%/%NAME%",
                            "pkgdirs": {
                                "Applications": "0775"
                            }
                        }
                    })
                    if facts["codesign_status"] == "unsigned":
                        # If unsigned, that means the download recipe hasn't
                        # unarchived the zip yet. Need to do that and version.
                        keys["Process"].append({
                            "Processor": "Unarchiver",
                            "Arguments": {
                                "archive_path": "%pathname%",
                                "destination_path": "%RECIPE_CACHE_DIR%/%NAME%/Applications",
                                "purge_destination": True
                            }
                        })
                        keys["Process"].append({
                            "Processor": "Versioner",
                            "Arguments": {
                                "input_plist_path": "%%RECIPE_CACHE_DIR%%/%%NAME%%/Applications/%s.app/Contents/Info.plist" % app_name_key,
                                "plist_version_key": facts["version_key"]
                            }
                        })
                    keys["Process"].append({
                        "Processor": "Copier",
                        "Arguments": {
                            "source_path": "%%pathname%%/%s.app" % app_name_key,
                            "destination_path": "%%pkgroot%%/Applications/%s.app" % app_name_key
                        }
                    })

                elif facts["download_format"] in supported_archive_formats:
                    # Pkgroot is already in place from previous unarchiving.
                    pass

                elif facts["download_format"] in supported_install_formats:
                    robo_print("verbose",
                               "Skipping pkg recipe, since the download "
                               "format is already pkg.")
                    continue

                keys["Process"].append({
                    "Processor": "PkgCreator",
                    "Arguments": {
                        "pkg_request": {
                            "pkgroot": "%RECIPE_CACHE_DIR%/%NAME%",
                            "pkgname": "%NAME%-%version%",
                            "version": "%version%",
                            "id": "%BUNDLE_ID%",
                            "options": "purge_ds_store",
                            "chown": [{
                                "path": "Applications",
                                "user": "root",
                                "group": "admin"
                            }]
                        }
                    }
                })

            # Set keys specific to install recipes.
            elif recipe["type"] == "install":

                robo_print("log", "Generating %s recipe..." % recipe["type"])

                # Save a description that explains what this recipe does.
                keys["Description"] = ("Installs the latest version "
                                      "of %s." % facts["app_name"])

                # Make the download recipe the parent of the Munki recipe.
                # TODO(Elliot): What if it's somebody else's download recipe?
                keys["ParentRecipe"] = "%s.download.%s" % (prefs["RecipeIdentifierPrefix"], facts["app_name"].replace(" ", ""))

                if facts["download_format"] in supported_image_formats:
                    pass  # InstallFromDMG (added below) is the only
                          # processor required.

                elif facts["download_format"] in supported_archive_formats:
                    if facts["codesign_status"] == "unsigned":
                        keys["Process"].append({
                            "Processor": "Unarchiver",
                            "Arguments": {
                                "archive_path": "%pathname%",
                                "destination_path": "%RECIPE_CACHE_DIR%/%NAME%/Applications",
                                "purge_destination": True
                            }
                        })
                    keys["Process"].append({
                        "Processor": "DmgCreator",
                        "Arguments": {
                            "dmg_root": "%RECIPE_CACHE_DIR%/%NAME%",
                            "dmg_path": "%RECIPE_CACHE_DIR%/%NAME%.dmg"
                        }
                    })

                elif facts["download_format"] in supported_install_formats:
                    keys["Process"].append({
                        "Processor": "Installer",
                        "Arguments": {
                            "pkg_path": "%pathname%"
                        }
                    })
                    continue  # No more processors needed for pkg install.

                keys["Process"].append({
                    "Processor": "InstallFromDMG",
                    "Arguments": {
                        "dmg_path": "%dmg_path%",
                        "items_to_copy": {
                            "source_item": "%s.app" % app_name_key,
                            "destination_path": "/Applications"
                        }
                    }
                })

            # Set keys specific to jss recipes.
            elif recipe["type"] == "jss":

                robo_print("log", "Generating %s recipe..." % recipe["type"])

                # Authors of jss recipes are encouraged to use spaces.
                filename = "%s.%s.recipe" % (facts["app_name"], recipe["type"])

                # Save a description that explains what this recipe does.
                keys["Description"] = ("Downloads the latest version of %s and "
                                      "imports it into your "
                                      "JSS." % facts["app_name"])

                # Set the parent recipe to the pkg recipe.
                # Make the download recipe the parent of the Munki recipe.
                # TODO(Elliot): What if it's somebody else's pkg recipe?
                keys["ParentRecipe"] = "%s.pkg.%s" % (prefs["RecipeIdentifierPrefix"], facts["app_name"])

                # TODO(Elliot): How can we set the category automatically?
                keys["Input"]["CATEGORY"] = ""
                robo_print("reminder",
                           "Remember to manually set the category "
                           "in the jss recipe.")

                keys["Input"]["POLICY_CATEGORY"] = "Testing"
                keys["Input"]["POLICY_TEMPLATE"] = "PolicyTemplate.xml"
                robo_print("reminder",
                           "Please make sure PolicyTemplate.xml is in your "
                           "AutoPkg search path.")
                keys["Input"]["SELF_SERVICE_ICON"] = "%NAME%.png"
                robo_print("reminder",
                           "Please make sure %s.png is in your AutoPkg search "
                           "path." % facts["app_name"])
                keys["Input"]["SELF_SERVICE_DESCRIPTION"] = facts["description"]
                keys["Input"]["GROUP_NAME"] = "%NAME%-update-smart"

                if facts["version_key"] == "CFBundleVersion":
                    keys["Input"]["GROUP_TEMPLATE"] = "CFBundleVersionSmartGroupTemplate.xml"
                    robo_print("reminder",
                               "Please make sure "
                               "CFBundleVersionSmartGroupTemplate.xml is in "
                               "your AutoPkg search path.")
                    keys["Process"].append({
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
                            }],
                            "extension_attributes": [{
                                "ext_attribute_path": "CFBundleVersionExtensionAttribute.xml"
                            }]
                        }
                    })
                else:
                    keys["Input"]["GROUP_TEMPLATE"] = "SmartGroupTemplate.xml"
                    robo_print("reminder",
                               "Please make sure SmartGroupTemplate.xml is in "
                               "your AutoPkg search path.")
                    keys["Process"].append({
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

                # Extract the app's icon and save it to disk.
                extracted_icon = "%s/%s.png" % (prefs["RecipeCreateLocation"],
                                                facts["app_name"])
                extract_app_icon(facts["icon_path"], extracted_icon)

            # Set keys specific to absolute recipes.
            elif recipe["type"] == "absolute":

                robo_print("log", "Generating %s recipe..." % recipe["type"])

                # Save a description that explains what this recipe does.
                keys["Description"] = ("Downloads the latest version of %s and "
                                      "copies it into your Absolute Manage "
                                      "Server." % facts["app_name"])

                # Set the parent recipe to the pkg recipe.
                # Make the download recipe the parent of the Munki recipe.
                # TODO(Elliot): What if it's somebody else's pkg recipe?
                keys["ParentRecipe"] = "%s.pkg.%s" % (prefs["RecipeIdentifierPrefix"], facts["app_name"])

                keys["Process"].append({
                    "Processor": "com.github.tburgin.AbsoluteManageExport/AbsoluteManageExport",
                    "SharedProcessorRepoURL": "https://github.com/tburgin/AbsoluteManageExport",
                    "Arguments": {
                        "dest_payload_path": "%RECIPE_CACHE_DIR%/%NAME%-%version%.amsdpackages",
                        "sdpackages_ampkgprops_path": "%RECIPE_DIR%/%NAME%-Defaults.ampkgprops",
                        "source_payload_path": "%pkg_path%",
                        "import_abman_to_servercenter": True
                    }
                })

            # Set keys specific to sccm recipes.
            elif recipe["type"] == "sccm":

                robo_print("log", "Generating %s recipe..." % recipe["type"])

                # Save a description that explains what this recipe does.
                keys["Description"] = ("Downloads the latest version of %s and "
                                      "copies it into your SCCM "
                                      "Server." % facts["app_name"])

                # Set the parent recipe to the pkg recipe.
                # Make the download recipe the parent of the Munki recipe.
                # TODO(Elliot): What if it's somebody else's pkg recipe?
                keys["ParentRecipe"] = "%s.pkg.%s" % (prefs["RecipeIdentifierPrefix"], facts["app_name"])

                keys["Process"].append({
                    "Processor": "com.github.autopkg.cgerke-recipes.SharedProcessors/CmmacCreator",
                    "SharedProcessorRepoURL": "https://github.com/autopkg/cgerke-recipes",
                    "Arguments": {
                        "source_file": "%pkg_path%",
                        "destination_directory": "%RECIPE_CACHE_DIR%"
                    }
                })

            # Set keys specific to ds recipes.
            elif recipe["type"] == "ds":

                robo_print("log", "Generating %s recipe..." % recipe["type"])

                # Save a description that explains what this recipe does.
                keys["Description"] = ("Downloads the latest version of %s and "
                                      "copies it to your DeployStudio "
                                      "packages." % facts["app_name"])

                # Set the parent recipe to the pkg recipe.
                # Make the download recipe the parent of the Munki recipe.
                # TODO(Elliot): What if it's somebody else's pkg recipe?
                keys["ParentRecipe"] = "%s.pkg.%s" % (prefs["RecipeIdentifierPrefix"], facts["app_name"])
                keys["Input"]["DS_PKGS_PATH"] = prefs["DSPackagesPath"]
                keys["Input"]["DS_NAME"] = "%NAME%"
                keys["Process"].append({
                    "Processor": "StopProcessingIf",
                    "Arguments": {
                        "predicate": "new_package_request == FALSE"
                    }
                })
                keys["Process"].append({
                    "Processor": "Copier",
                    "Arguments": {
                        "source_path": "%pkg_path%",
                        "destination_path": "%DS_PKGS_PATH%/%DS_NAME%.pkg",
                        "overwrite": True
                    }
                })

            else:
                # This shouldn't happen, if all the right recipe types are
                # specified in init_recipes() and also specified above.
                robo_print("warning",
                           "Oops, I think my programmer messed up. I don't "
                           "yet know how to generate a %s recipe. Sorry about "
                           "that." % recipe["type"])

            # Write the recipe to disk.
            dest_dir = os.path.expanduser(prefs["RecipeCreateLocation"])
            create_dest_dirs(dest_dir)
            # TODO(Elliot): Warning if a file already exists here.
            dest_path = "%s/%s" % (dest_dir, filename)
            FoundationPlist.writePlist(recipe["keys"], dest_path)
            prefs["RecipeCreateCount"] += 1

            robo_print("verbose", "    %s/%s" %
                       (prefs["RecipeCreateLocation"], filename))

    # Save preferences to disk for next time.
    FoundationPlist.writePlist(prefs, prefs_file)


def create_dest_dirs(path):
    """Creates the path to the recipe export location, if it doesn't exist.

    Args:
        path: TODO
    """

    dest_dir = os.path.expanduser(path)
    if not os.path.exists(dest_dir):
        try:
            os.makedirs(dest_dir)
        except Exception:
            robo_print("error", "Unable to create directory at %s." % dest_dir)


def extract_app_icon(icon_path, png_path):
    """Convert the app's icns file to 300x300 png at the specified path.
    300x300 is Munki's preferred size, and 128x128 is Casper's preferred size,
    as of 2015-08-01.

    Args:
        icon_path: TODO
        png_path: TODO
    """

    png_path_absolute = os.path.expanduser(png_path)
    create_dest_dirs(os.path.dirname(png_path_absolute))

    # Add .icns if the icon path doesn't already end with .icns.
    if not icon_path.endswith(".icns"):
        icon_path = icon_path + ".icns"

    if not os.path.exists(png_path_absolute):
        cmd = ("sips -s format png \"%s\" --out \"%s\" "
               "--resampleHeightWidthMax 300" % (icon_path, png_path_absolute))
        exitcode, out, err = get_exitcode_stdout_stderr(cmd)
        if exitcode == 0:
            robo_print("verbose", "    %s" % png_path)
        else:
            robo_print("warning",
                       "An error occurred during icon extraction: %s" % err)


def debug_dump(items):
    """Dump all the variables we know about to output.

    Args:
        items: A dict of dicts of all the things to dump to output.
    """

    for key, value in items.iteritems():
        print "%s\n%s:\n\n%s\n%s" % (bcolors.DEBUG,
                                           key.upper(),
                                           pprint.pformat(value),
                                           bcolors.ENDC)


def congratulate(prefs):
    """Display a friendly congratulatory message upon creating recipes.

    Args:
        prefs: TODO
    """

    congrats_msg = (
        "Amazing.",
        "Easy peasy.",
        "Fantastic.",
        "Good on ya!",
        "Imagine all the typing you saved.",
        "Isn't meta-automation great?",
        "(Yep, it's pretty fun for me too.)",
        "Pretty cool, right?",
        "Round of applause for you!",
        "Terrific job!",
        "Thanks!",
        "That's awesome!",
        "Want to do another?",
        "Well done!",
        "You rock star, you."
    )
    if prefs["RecipeCreateCount"] == 1:
        robo_print("log", "\nYou've created your first recipe with Recipe Robot. Congratulations!\n")
    elif prefs["RecipeCreateCount"] > 1:
        robo_print("log", "\nYou've now created %s recipes with Recipe Robot. %s\n" % (
            prefs["RecipeCreateCount"], random.choice(congrats_msg)))


# TODO(Elliot): Make main() shorter. Just a flowchart for the logic.
def main():
    """Make the magic happen."""

    try:
        global verbose_mode

        print_welcome_text()

        argparser = build_argument_parser()
        args = argparser.parse_args()
        if args.include_existing is True:
            robo_print("warning",
                       "Will build recipes even if they already exist in "
                       "\"autopkg search\" results. Please don't upload "
                       "duplicate recipes.")
        if args.verbose is True or verbose_mode is True:
            robo_print("verbose", "Verbose mode is on.")
            verbose_mode = True

        # Create the master recipe information list.
        recipes = init_recipes()

        # Read or create the user preferences.
        prefs = {}
        prefs = init_prefs(prefs, recipes, args)

        input_path = args.input_path
        input_path = input_path.rstrip("/ ")
        robo_print("log", "\nProcessing %s ..." % input_path)

        # Collect facts from the input path, based on the type of path given.
        facts = {}
        process_input_path(input_path, args, facts)

        # Look up existing recipes.
        create_existing_recipe_list(facts["app_name"], recipes, args)

        # Determine which recipes we can build.
        create_buildable_recipe_list(facts["app_name"], recipes, args, facts)

        # Create recipes for the recipe types that were selected above.
        generate_recipes(facts, prefs, recipes)

        # If debug is on, print all the things.
        if debug_mode is True:
            debug_dump({
                "Command line arguments": args,
                "Supported file formats": all_supported_formats,
                "Preferences for this session": prefs,
                "Recipe information": recipes,
                "Facts we have collected": facts
            })

        # Pat on the back!
        congratulate(prefs)

    # If killed, make sure to reset the terminal color with our dying breath.
    except (KeyboardInterrupt, SystemExit):
        print bcolors.ENDC


if __name__ == '__main__':
    main()
