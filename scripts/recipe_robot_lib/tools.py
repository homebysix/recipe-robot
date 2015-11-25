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
tools.py

This module of Recipe Robot contains various helper and tool functions that
support the main `recipe-robot` script and the `recipe_generator.py` module.
"""


from datetime import datetime
from functools import wraps
import os
from random import choice as random_choice
import re
import shlex
from subprocess import Popen, PIPE
import sys
import timeit
from urllib2 import urlopen

from .exceptions import RoboError
# TODO(Elliot): Can we use the one at /Library/AutoPkg/FoundationPlist instead?
# Or not use it at all (i.e. use the preferences system correctly). (#16)
try:
    from recipe_robot_lib import FoundationPlist
except ImportError:
    robo_print("Importing plistlib as FoundationPlist", LogLevel.WARNING)
    import plistlib as FoundationPlist


__version__ = '1.0.1'
ENDC = "\033[0m"
PREFS_FILE = os.path.expanduser(
    "~/Library/Preferences/com.elliotjordan.recipe-robot.plist")

# Build the list of download formats we know about.
SUPPORTED_IMAGE_FORMATS = ("dmg", "iso")  # downloading iso unlikely
SUPPORTED_ARCHIVE_FORMATS = ("zip", "tar.gz", "gzip", "tar.bz2", "tbz", "tgz")
SUPPORTED_INSTALL_FORMATS = ("pkg",)
ALL_SUPPORTED_FORMATS = (SUPPORTED_IMAGE_FORMATS + SUPPORTED_ARCHIVE_FORMATS +
                         SUPPORTED_INSTALL_FORMATS)

# Global variables.
CACHE_DIR = os.path.join(os.path.expanduser("~/Library/Caches/Recipe Robot"),
                         datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f"))
color_setting = False


class LogLevel(object):
    """Specify colors that are used in Terminal output."""
    DEBUG = ("\033[95m", "DEBUG")
    ERROR = ("\033[1;38;5;196m", "ERROR")
    LOG = ("", "")
    REMINDER = ("\033[1;38;5;33m", "REMINDER")
    VERBOSE = ("\033[0m", "")
    WARNING = ("\033[1;38;5;208m", "WARNING")


class OutputMode(object):
    """Manage global output mode state with a singleton."""
    verbose_mode = False  # Use --verbose command-line argument, or hard-code
                          # to "True" here for additional user-facing output.
    debug_mode = False  # Use --debug command-line argument, or hard-code
                        # to "True" here for additional development output.

    @classmethod
    def set_verbose_mode(cls, value):
        """Set the class variable for verbose_mode."""
        if isinstance(value, bool):
            cls.verbose_mode = value
        else:
            raise ValueError

    @classmethod
    def set_debug_mode(cls, value):
        """Set the class variable for debug_mode."""
        if isinstance(value, bool):
            cls.debug_mode = value
        else:
            raise ValueError


def timed(func):
    """Decorator for timing a function.

    Modifies func to return a tuple of:
        (execution time, original func's return value)
    """
    @wraps(func)
    def run_func(*args, **kwargs):
        """Time a function."""
        start = timeit.default_timer()
        result = func(*args, **kwargs)
        end = timeit.default_timer()
        return (end - start, result)
    return run_func


def robo_print(message, log_level=LogLevel.LOG, indent=0):
    """Print the specified message in an appropriate color, and only print
    debug output if debug_mode is True.

    Args:
        log_level: LogLevel property for desired loglevel.
        message: String to be printed to output.
    """
    color = log_level[0] if color_setting else ""
    indents = indent * " "
    if log_level[1]:
        prefix = "[%s] " % log_level[1]
    else:
        prefix = ""
    suffix = ENDC if color_setting else ""

    line = color + indents + prefix + message + suffix

    if log_level in (LogLevel.ERROR, LogLevel.WARNING):
        print_func = _print_stderr
    else:
        print_func = _print_stdout

    if ((log_level in (LogLevel.ERROR, LogLevel.REMINDER, LogLevel.WARNING,
                       LogLevel.LOG)) or
        (log_level is LogLevel.DEBUG and OutputMode.debug_mode) or
        (log_level is LogLevel.VERBOSE and (OutputMode.verbose_mode or
                                            OutputMode.debug_mode))):
        print_func(line)


def create_dest_dirs(path):
    """Creates the path to the recipe export location, if it doesn't exist. If
    intermediate folders are necessary in order to create the path, they will
    be created too.

    Args:
        path: The path to the directory that needs to be created.
    """
    dest_dir = os.path.expanduser(path)
    if not os.path.exists(dest_dir):
        try:
            os.makedirs(dest_dir)
        except OSError as error:
            raise RoboError("Unable to create directory at %s." % dest_dir,
                            error)


def create_SourceForgeURLProvider(dest_dir):
    """Copies the latest version of Jesse Peterson's SourceForgeURLProvider to
    the recipe output directory, because it's referenced by one of the recipes
    being created.
    """
    base_url = ("https://raw.githubusercontent.com/autopkg/"
                "jessepeterson-recipes/master/GrandPerspective/"
                "SourceForgeURLProvider.py")
    dest_dir_absolute = os.path.expanduser(dest_dir)
    try:
        raw_download = urlopen(base_url)
        with open(os.path.join(dest_dir_absolute, "SourceForgeURLProvider.py"),
                  "wb") as download_file:
            download_file.write(raw_download.read())
            robo_print(os.path.join(dest_dir, "SourceForgeURLProvider.py"),
                       LogLevel.VERBOSE, 4)
    except:
        # TODO(Elliot):  Copy SourceForgeURLProvider from local file. (#46)
        # TODO: This doesn't notify or update the facts object.
        robo_print("Unable to download SourceForgeURLProvider from GitHub.",
                   LogLevel.WARNING)


def extract_app_icon(facts, png_path):
    """Convert the app's icns file to 300x300 png at the specified path.
    300x300 is Munki's preferred size, and 128x128 is Casper's preferred size,
    as of 2015-08-01.

    Args:
        facts: Dictionary with key "icon_path", value: string path to
            icon.
        png_path: The path to the .png file we're creating.
    """
    icon_path = facts["icon_path"]
    png_path_absolute = os.path.expanduser(png_path)
    create_dest_dirs(os.path.dirname(png_path_absolute))

    # Add .icns if the icon path doesn't already end with .icns.
    if not icon_path.endswith(".icns"):
        icon_path = icon_path + ".icns"

    if not os.path.exists(png_path_absolute):
        cmd = ("sips -s format png \"%s\" --out \"%s\" "
               "--resampleHeightWidthMax 300" % (icon_path, png_path_absolute))
        exitcode, _, err = get_exitcode_stdout_stderr(cmd)
        if exitcode == 0:
            robo_print("%s" % png_path, LogLevel.VERBOSE, 4)
            facts["icons"].append(png_path)
        else:
            facts["warnings"].append(
                "An error occurred during icon extraction: %s" % err)


def get_exitcode_stdout_stderr(cmd, stdin=""):
    """Execute the external command and get its exitcode, stdout and stderr.

    Args:
        cmd: The shell command to be executed.

    Returns:
        exitcode: Zero upon success. Non-zero upon error.
        out: String from standard output.
        err: String from standard error.
    """
    if "|" in cmd:
        cmd_parts = cmd.split("|")
    else:
        cmd_parts = [cmd]

    i = 0
    p = {}
    for cmd_part in cmd_parts:
        cmd_part = cmd_part.strip()
        if i == 0:
            p[i]=Popen(shlex.split(cmd_part), stdin=PIPE, stdout=PIPE,
                       stderr=PIPE)
        else:
            p[i]=Popen(shlex.split(cmd_part), stdin=p[i-1].stdout, stdout=PIPE,
                       stderr=PIPE)
        i = i + 1

    out, err = p[i-1].communicate(stdin)
    exitcode = p[i-1].returncode

    return exitcode, out, err


def _print_stderr(p):
    print >> sys.stderr, p


def _print_stdout(p):
    print p


def print_welcome_text():
    """Print the text that appears when you run Recipe Robot."""
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

    robo_print(welcome_text)


def print_death_text():
    """Print the text that appears when you RoboError out."""
    death_text = """
                                    _[]_
                                    [xx]
                                   q-||-p
                                     ||
                                   _/  \_
    """
    robo_print(death_text, LogLevel.ERROR)


def reset_term_colors():
    """Ensure terminal colors are normal."""
    sys.stdout.write(ENDC)


def write_report(report, report_file):
    FoundationPlist.writePlist(report, report_file)


def any_item_in_string(items, test_string):
    """Return true if any item in items is in test_string"""
    return any([True for item in items if item in test_string])


def create_existing_recipe_list(facts):
    """Use autopkg search results to build existing recipe list.

    Args:
        facts: The Facts instance containing all of our information.
            Required keys:
                app_name: The app's name.
                recipes: The recipes to build.
                args: ArgParser args with github_token bool.
    """
    app_name = facts["app_name"]
    recipes = facts["recipes"]
    use_github_token = facts["args"].github_token
    # TODO(Elliot): Suggest users create GitHub API token to prevent limiting. (#29)
    recipe_searches = []
    recipe_searches.append(app_name)

    app_name_no_space = "".join(app_name.split())
    if app_name_no_space != app_name:
        recipe_searches.append(app_name_no_space)

    app_name_no_symbol = re.sub(r'[^\w]', '', app_name)
    if app_name_no_symbol not in (app_name, app_name_no_space):
        recipe_searches.append(app_name_no_symbol)

    for this_search in recipe_searches:
        robo_print("Searching for existing AutoPkg recipes for \"%s\"..." %
                   this_search, LogLevel.VERBOSE)
        if use_github_token:
            if not os.path.exists(os.path.expanduser("~/.autopkg_gh_token")):
                facts["warnings"].append(
                    "I couldn't find a GitHub token to use.")
                cmd = ("/usr/local/bin/autopkg search --path-only \"%s\"" %
                       this_search)
            else:
                # TODO(Elliot): Learn how to use the GitHub token. (#18) https://github.com/autopkg/autopkg/blob/680c75855f00b588e6dd50fb431bed5d5fd41d9c/Code/autopkglib/github/__init__.py#L31
                facts["warnings"].append(
                    "I found a GitHub token, but I'm still learning how to "
                    "use it.")
                cmd = ("/usr/local/bin/autopkg search --path-only --use-token "
                       "\"%s\"" % this_search)
        else:
            cmd = ("/usr/local/bin/autopkg search --path-only \"%s\"" %
                   this_search)
        exitcode, out, err = get_exitcode_stdout_stderr(cmd)
        out = out.split("\n")
        if exitcode == 0:
            # TODO(Elliot): There's probably a more efficient way to do this.
            # For each recipe type, see if it exists in the search
            # results.
            is_existing = False
            for recipe in recipes:
                recipe_name = "%s.%s.recipe" % (this_search, recipe["type"])
                for line in out:
                    if line.lower().startswith(recipe_name.lower()):
                        # Set to False by default. If found, set True.
                        recipe["existing"] = True
                        robo_print("Found existing %s" % recipe_name,
                                   LogLevel.LOG, 4)
                        is_existing = True
                        break
            if is_existing is True:
                raise RoboError(
                    "Sorry, AutoPkg recipes already exist for this app, and "
                    "I can't blend new recipes with existing recipes.\n\nHere "
                    "are my suggestions:\n\t- See if one of the above recipes "
                    "meets your needs, either as-is or using an override."
                    "\n\t- Write your own recipe using one of the above as "
                    "the ParentRecipe.\n\t- Or if you must, write your own "
                    "recipe from scratch.")
            if not is_existing:
                robo_print("No results", LogLevel.VERBOSE, 4)
        else:
            raise RoboError(err.message)


def congratulate(prefs):
    """Display a friendly congratulatory message upon creating recipes.

    Args:
        prefs: A dictionary containing a key/value pair for each
            preference.
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
        robo_print("\nYou've created your first recipe with Recipe "
                   "Robot. Congratulations!\n")
    elif prefs["RecipeCreateCount"] > 1:
        robo_print("\nYou've now created %s recipes with Recipe Robot. "
                   "%s\n" % (prefs["RecipeCreateCount"],
                             random_choice(congrats_msg)))


def robo_join(*args):
    return os.path.expanduser(os.path.join(*args))
