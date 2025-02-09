#!/usr/local/autopkg/python
# This Python file uses the following encoding: utf-8

# Recipe Robot
# Copyright 2015-2020 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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


from __future__ import absolute_import, print_function

import json
import os
import shlex
import subprocess
import sys
import timeit
from datetime import datetime
from functools import wraps
from random import choice as random_choice

# pylint: disable=no-name-in-module
from Foundation import (
    CFPreferencesAppSynchronize,
    CFPreferencesCopyAppValue,
    CFPreferencesCopyKeyList,
    CFPreferencesSetAppValue,
    kCFPreferencesAnyHost,
    kCFPreferencesCurrentUser,
)

from .exceptions import RoboError

# pylint: enable=no-name-in-module


__version__ = "2.3.3"
ENDC = "\033[0m"
BUNDLE_ID = "com.elliotjordan.recipe-robot"
PREFS_FILE = os.path.expanduser("~/Library/Preferences/%s.plist" % BUNDLE_ID)

# Build the list of download formats we know about.
SUPPORTED_IMAGE_FORMATS = ("dmg", "iso")  # downloading iso unlikely
SUPPORTED_ARCHIVE_FORMATS = ("zip", "tar.gz", "gzip", "tar.bz2", "tbz", "tgz")
SUPPORTED_INSTALL_FORMATS = ("pkg",)
ALL_SUPPORTED_FORMATS = (
    SUPPORTED_IMAGE_FORMATS + SUPPORTED_ARCHIVE_FORMATS + SUPPORTED_INSTALL_FORMATS
)

# Build the list of bundle types we support, and their destinations. ("app" should be listed first.)
SUPPORTED_BUNDLE_TYPES = {
    "app": "/Applications",
    "plugin": "/Library/Internet Plug-Ins",
    "prefpane": "/Library/PreferencePanes",
    "qlgenerator": "/Library/QuickLook",
    "saver": "/Library/Screen Savers",
}

# Known Recipe Robot preference keys. All other keys will be removed from
# the com.elliotjordan.recipe-robot.plist preference file.
PREFERENCE_KEYS = (
    "DSPackagesPath",
    "IgnoreExisting",
    "Initialized",  # Used by the RR app to show/hide config sheet on first launch.
    "LastRecipeRobotVersion",
    "RecipeCreateCount",
    "RecipeCreateLocation",
    "RecipeFormat",
    "RecipeIdentifierPrefix",
    "RecipeTypes",
    "StripDeveloperSuffixes",
    "SUEnableAutomaticChecks",
    "SUHasLaunchedBefore",
    "SULastCheckTime",
    "SUSendProfileInfo",
)

# Global variables.

# Cache directory location.
CACHE_DIR = os.path.join(
    os.path.expanduser("~/Library/Caches/Recipe Robot"),
    datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f"),
)

# Whether to display Terminal colors or not.
# Variable name required to be lowercase in order to be overridden by script.
color_setting = False

# Domains associated with GitHub.
GITHUB_DOMAINS = ("github.com", "githubusercontent.com", "github.io")

# Domains that return HTTP 403 upon HEAD request.
KNOWN_403_ON_HEAD = (
    "bitbucket.org",
    "github.com",
    "hockeyapp.net",
    "updates.devmate.com",
)


class LogLevel(object):
    """Correlate logging level of a message with designated colors for more
    readable output in Terminal."""

    DEBUG = ("\033[95m", "DEBUG")
    ERROR = ("\033[1;38;5;196m", "ERROR")
    LOG = ("", "")
    REMINDER = ("\033[1;38;5;33m", "REMINDER")
    VERBOSE = ("\033[0m", "")
    WARNING = ("\033[1;38;5;208m", "WARNING")


class OutputMode(object):
    """Manage global output mode state with a singleton."""

    # Use --verbose command-line argument, or hard-code
    # to "True" here for additional user-facing output.
    verbose_mode = False

    # Use --debug command-line argument, or hard-code
    # to "True" here for additional development output.
    debug_mode = False

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

    Args:
        func (func): Function to be timed.

    Returns:
        float: Number of seconds taken by function execution.
        type varies: Original return value of the function.
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
        message (str): Message to be printed to output.
        log_level (LogLevel, optional): Object representing logging level,
            which is used to colorize output in Terminal.
        indent (int, optional): Indentation level, in number of spaces.
            Defaults to 0.
    """
    color = log_level[0] if color_setting else ""
    indents = indent * " "
    if log_level[1]:
        prefix = "[%s] " % log_level[1]
    else:
        prefix = ""
    suffix = ENDC if color_setting else ""

    line = color + indents + prefix + message + suffix

    if (
        log_level in (LogLevel.ERROR, LogLevel.REMINDER, LogLevel.WARNING, LogLevel.LOG)
        or (log_level is LogLevel.DEBUG and OutputMode.debug_mode)
        or (
            log_level is LogLevel.VERBOSE
            and (OutputMode.verbose_mode or OutputMode.debug_mode)
        )
    ):
        if os.environ.get("NSUnbufferedIO") == "YES":
            # Shell out to enable realtime output in Recipe Robot app.
            subprocess.run(["echo", line], check=False)
        elif log_level in (LogLevel.ERROR, LogLevel.WARNING):
            print(line, file=sys.stderr)
        else:
            print(line)


def get_github_token():
    """Return AutoPkg GitHub token, if file exists.

    Returns:
        str or None: AutoPkg token contents, or None if no token file exists.
    """
    # TODO: Also check for GITHUB_TOKEN preference.
    github_token_file = os.path.expanduser("~/.autopkg_gh_token")
    if os.path.isfile(github_token_file):
        try:
            with open(github_token_file, "r") as tokenfile:
                return tokenfile.read().strip()
        except IOError:
            print("WARNING: Couldn't read GitHub token file at %s." % github_token_file)
    return None


def strip_dev_suffix(dev):
    """Removes corporation suffix from developer names, if present.

    Args:
        dev (str): Name of app developer.

    Returns:
        str: Name of app developer with suffixes stripped.
    """
    corp_suffixes = (
        "incorporated",
        "corporation",
        "limited",
        "oy/ltd",
        "pty ltd",
        "pty. ltd",
        "pvt ltd",
        "pvt. ltd",
        "s.a r.l",
        "sa rl",
        "sarl",
        "srl",
        "corp",
        "gmbh",
        "l.l.c",
        "inc",
        "llc",
        "ltd",
        "pvt",
        "oy",
        "sa",
        "ab",
    )
    if dev not in (None, ""):
        for suffix in corp_suffixes:
            if dev.lower().rstrip(" .").endswith(suffix):
                dev = dev.rstrip(" .")[: len(dev) - len(suffix) - 1].rstrip(",. ")
                break
    return dev


def get_bundle_name_info(facts):
    """Returns the key used to store the bundle name. This is usually "app_name"
    but could be "prefpane_name". If both exist in facts, "app_name" wins.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.

    Returns:
        string or None: Bundle type (e.g. "app" or "prefpane").
        string or None: Bundle name key (e.g. "app_name" or "prefpane_name")
    """
    if "app" in facts["inspections"]:
        bundle_type = "app"
        bundle_name_key = "app_name"
    else:
        bundle_types = [x for x in SUPPORTED_BUNDLE_TYPES if x in facts["inspections"]]
        bundle_type = bundle_types[0] if bundle_types else None
        bundle_name_key = bundle_type + "_name" if bundle_types else None
    return bundle_type, bundle_name_key


def recipe_dirpath(app_name, dev, prefs):
    """Returns a macOS-friendly path to use for recipes.

    Args:
        app_name (str): Name of the app.
        dev (str): Name of the app developer.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.

    Returns:
        str: Path at which Recipe Robot will output recipes for this app.
    """
    # Special characters that shouldn't be in macOS file/folder names.
    char_replacements = (("/", "-"), ("\\", "-"), (":", "-"), ("*", "-"), ("?", ""))
    for char in char_replacements:
        app_name = app_name.replace(char[0], char[1])
    path_components = [prefs["RecipeCreateLocation"]]
    if dev is not None:
        # TODO: Put this in the preferences.
        if prefs.get("StripDeveloperSuffixes", False) is True:
            dev = strip_dev_suffix(dev)
        for char in char_replacements:
            dev = dev.replace(char[0], char[1])
        path_components.append(dev)
    else:
        path_components.append(app_name)

    return robo_join(*path_components)


def create_dest_dirs(path):
    """Creates the path to the recipe export location, if it doesn't exist. If
    intermediate folders are necessary in order to create the path, they will
    be created too.

    Args:
        path (str): Path to which recipes will be exported.

    Raises:
        RoboError: Standard exception raised when Recipe Robot cannot proceed.
    """
    dest_dir = os.path.expanduser(path)
    if not os.path.exists(dest_dir):
        try:
            os.makedirs(dest_dir)
        except OSError as error:
            raise RoboError("Unable to create directory at %s." % dest_dir, error)


def extract_app_icon(facts, png_path):
    """Convert the app's icns file to 300x300 png at the specified path.
    300x300 is Munki's preferred size, and 128x128 is Jamf Pro's preferred size,
    as of 2015-08-01.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path. The "icon_path" key is required for this function.
        png_path (str): The path to the .png file we're creating.
    """
    icon_path = facts["icon_path"]
    png_path_absolute = os.path.expanduser(png_path)
    create_dest_dirs(os.path.dirname(png_path_absolute))

    # Add .icns if the icon path doesn't already end with .icns.
    if not icon_path.endswith(".icns"):
        icon_path = icon_path + ".icns"

    if not os.path.exists(png_path_absolute):
        cmd = (
            '/usr/bin/sips -s format png "%s" --out "%s" '
            "--resampleHeightWidthMax 300" % (icon_path, png_path_absolute)
        )
        exitcode, _, err = get_exitcode_stdout_stderr(cmd)
        if exitcode == 0:
            robo_print("%s" % png_path, LogLevel.VERBOSE, 4)
            facts["icons"].append(png_path)
        else:
            facts["warnings"].append(
                "An error occurred during icon extraction: %s" % err
            )


def get_exitcode_stdout_stderr(cmd, stdin="", text=True):
    """Execute the external command and get its exitcode, stdout and stderr.

    Args:
        cmd (str): Shell command to execute, to be split with shlex.split().
        stdin (str, optional): Standard input. Defaults to "".
        text (bool, optional): Return text string instead of bytes.
            Defaults to True.

    Returns:
        int: Exit code of command.
        str: Standard output produced by the command.
        str: Standard error produced by the command.
    """
    robo_print("Shell command: %s" % cmd, LogLevel.DEBUG, 4)
    try:
        # First try to return text output.
        proc = subprocess.Popen(
            shlex.split(cmd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=text,
        )
        out, err = proc.communicate(stdin)
    except UnicodeDecodeError:
        # If that fails, force bytes output.
        proc = subprocess.Popen(
            shlex.split(cmd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
        )
        out, err = proc.communicate(stdin)
    exitcode = proc.returncode

    return exitcode, out, err


def print_welcome_text():
    """Print the text that appears when you run Recipe Robot."""
    welcome_text = (
        """
                      -----------------------------------
                     |  Welcome to Recipe Robot v%s.  |
                      -----------------------------------
                                \\   _[]_
                                 \\  [oo]
                                   d-||-b
                                     ||
                                   _/  \\_
    """
        % __version__
    )

    robo_print(welcome_text)


def print_death_text():
    """Print the text that appears when a RoboError is raised."""
    death_text = """
                                    _[]_
                                    [xx]
                                   q-||-p
                                     ||
                                   _/  \\_
    """
    robo_print(death_text)


def reset_term_colors():
    """Reset terminal colors back to normal."""
    if color_setting:
        sys.stdout.write(ENDC)


def get_user_defaults():
    """Get the user preferences for Recipe Robot.

    Returns:
        dict: The dictionary containing a key/value pair for Recipe Robot
            preferences.
    """
    prefs_dict = {
        key: CFPreferencesCopyAppValue(key, BUNDLE_ID) for key in PREFERENCE_KEYS
    }
    return prefs_dict


def save_user_defaults(prefs):
    """Write the user preferences for Recipe Robot back to disk.

    Args:
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
    """
    # Clean up non Recipe Robot related keys that were accidentally collected from the
    # global preferences by prior versions of Recipe Robot.
    cfprefs_keylist = CFPreferencesCopyKeyList(
        BUNDLE_ID, kCFPreferencesCurrentUser, kCFPreferencesAnyHost
    )
    if cfprefs_keylist:
        external_keys = [x for x in cfprefs_keylist if x not in PREFERENCE_KEYS]
        for ext_key in external_keys:
            CFPreferencesSetAppValue(ext_key, None, BUNDLE_ID)

    # Save latest values for all Recipe Robot keys.
    for key in PREFERENCE_KEYS:
        if prefs.get(key):
            CFPreferencesSetAppValue(key, prefs[key], BUNDLE_ID)
    CFPreferencesAppSynchronize(BUNDLE_ID)


def any_item_in_string(items, test_string):
    """Return true if any item in items is in test_string

    Args:
        items ([str]): List of strings to compare against test_string.
        test_string (str): String to search for the items.

    Returns:
        bool: True if any item exists in test_string, False otherwise.
    """
    return any([True for item in items if item in test_string])


def check_search_cache(facts, search_index_path):
    """Update local search index, if it's missing or out of date."""
    robo_print("Checking local search index cache...", LogLevel.VERBOSE)

    # Retrieve metadata about search index file from GitHub API
    cache_meta_url = (
        "https://api.github.com/repos/autopkg/index/contents/index.json?ref=main"
    )
    cmd = 'curl -sL "%s" -H "Accept: application/vnd.github.v3+json"' % cache_meta_url
    exitcode, stdout, _ = get_exitcode_stdout_stderr(cmd)
    if exitcode != 0:
        facts["warnings"].append(
            "Unable to retrieve search index metadata from GitHub API."
        )
        return
    cache_meta = json.loads(stdout)

    # If cache exists locally, check whether it's current
    if os.path.isfile(search_index_path) and os.path.isfile(
        search_index_path + ".etag"
    ):
        with open(search_index_path + ".etag", "r", encoding="utf-8") as openfile:
            local_etag = openfile.read().strip('"')
        if local_etag == cache_meta["sha"]:
            robo_print("Local search index cache is up to date.", LogLevel.VERBOSE, 4)
            return

    # Write etag file
    with open(search_index_path + ".etag", "w", encoding="utf-8") as openfile:
        openfile.write(cache_meta["sha"])

    # Write cache file
    cmd = 'curl -sLo "%s" "%s" -H "Accept: application/vnd.github.v3.raw"' % (
        search_index_path,
        cache_meta_url,
    )
    exitcode, _, _ = get_exitcode_stdout_stderr(cmd)
    if exitcode != 0:
        facts["warnings"].append(
            "Unable to retrieve search index contents from GitHub API."
        )
        return
    robo_print("Updated local search index cache.", LogLevel.VERBOSE, 4)


def get_table_row(row_items, col_widths, header=False):
    """This function takes table row content (list of strings) and column
    widths (list of integers) as input and outputs a string representing a
    table row in Markdown, with normalized "pretty" spacing that is readable
    when unrendered."""

    output = ""
    header_sep = "\n"
    column_space = 4
    for idx, cell in enumerate(row_items):
        padding = col_widths[idx] - len(cell) + column_space
        header_sep += "-" * len(cell) + " " * padding
        output += f"{cell}{' ' * padding}"

    if header:
        return output + header_sep

    return output


def normalize_keyword(keyword):
    """Normalizes capitalization, punctuation, and spacing of search keywords
    for better matching."""
    # TODO: Consider implementing fuzzywuzzy or some other fuzzy search method
    keyword = keyword.lower()
    replacements = {" ": "", ".": "", ",": "", "-": ""}
    for old, new in replacements.items():
        keyword = keyword.replace(old, new)

    return keyword


def create_existing_recipe_list(facts):
    """Use autopkg search results to build existing recipe list.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path. The "app_name" and "recipes" keys are required.

    Raises:
        RoboError: Standard exception raised when Recipe Robot cannot proceed.
    """
    app_name = facts["app_name"]
    # TODO: Suggest users create GitHub API token to prevent
    # limiting. (#29)

    # Update search index JSON cache
    search_index_path = os.path.expanduser(
        "~/Library/Caches/Recipe Robot/search_index.json"
    )
    check_search_cache(facts, search_index_path)
    with open(search_index_path, "rb") as openfile:
        search_index = json.load(openfile)

    # Search for existing recipes in index
    robo_print(
        "Searching for existing AutoPkg recipes for %s..." % app_name, LogLevel.VERBOSE
    )
    result_ids = []
    for candidate, identifiers in search_index["shortnames"].items():
        if normalize_keyword(app_name) in normalize_keyword(candidate):
            result_ids.extend(identifiers)
    result_ids = list(set(result_ids))
    if not result_ids:
        robo_print("No results", LogLevel.VERBOSE, 4)
        return

    # Collect result info into result list
    result_items = []
    for result_id in result_ids:
        repo = search_index["identifiers"][result_id]["repo"]
        if repo.startswith("autopkg/"):
            repo = repo.replace("autopkg/", "")
        result_item = {
            "Name": os.path.split(search_index["identifiers"][result_id]["path"])[-1],
            "Repo": repo,
            "Path": search_index["identifiers"][result_id]["path"],
        }
        result_items.append(result_item)
    col_widths = [
        max([len(x[k]) for x in result_items] + [len(k)])
        for k in result_items[0].keys()
    ]

    # Print result table, sorted by repo
    robo_print("Found existing recipe(s):", LogLevel.LOG, 4)
    robo_print("")
    robo_print(get_table_row(result_items[0].keys(), col_widths, header=True))
    for result_item in sorted(result_items, key=lambda x: x["Repo"].lower()):
        robo_print(get_table_row(result_item.values(), col_widths))
    robo_print("")

    raise RoboError(
        "Sorry, AutoPkg recipes already exist for this app, and "
        "I can't blend new recipes with existing recipes.\n\nHere "
        "are my suggestions:\n\t- See if one of the above recipes "
        "meets your needs, either as-is or using an override."
        "\n\t- Write your own recipe using one of the above as "
        "the ParentRecipe.\n\t- Use Recipe Robot to assist in "
        "the creation of a new child recipe, as seen here:\n\t  "
        "https://youtu.be/5VKDzY8bBxI?t=2829\n\t- To ignore this "
        "warning and create recipes anyway, run again using "
        "--ignore-existing."
    )


def congratulate(prefs, first_timer):
    """Display a friendly congratulatory message upon creating recipes.

    Args:
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
        first_timer (bool): True if this is the first time the user has run
            Recipe Robot.
    """
    congrats_msg = (
        "(Yep, it's pretty fun for me too.)",
        "Amazing.",
        "Easy peasy.",
        "Fantastic.",
        "Good on ya!",
        "Imagine all the typing you saved.",
        "Isn't meta-automation great?",
        "Let's do some more!",
        "Pretty cool, right?",
        "Round of applause for you!",
        "Terrific job!",
        "That's awesome!",
        "Very impressive.",
        "Want to do another?",
        "Way to go!",
        "Well done!",
        "You came here to build recipes and chew bubblegum. And you're all out of bubblegum.",
        "You rock star, you.",
        "You're doing a great job.",
    )
    if prefs["RecipeCreateCount"] > 0:
        if first_timer:
            if prefs["RecipeCreateCount"] == 1:
                recipe_count = "your first recipe"
            else:
                recipe_count = "your first {} recipes".format(
                    prefs["RecipeCreateCount"]
                )
            congrats = "Congratulations!"
        else:
            if prefs["RecipeCreateCount"] == 1:
                recipe_count = "1 recipe"
            else:
                recipe_count = "{} recipes".format(prefs["RecipeCreateCount"])
            congrats = random_choice(congrats_msg)
        robo_print(
            "\nYou've created {} with Recipe Robot. {}\n".format(recipe_count, congrats)
        )


def robo_join(*args):
    """Wrapper function that creates a path from string components, and then
    converts the path to user-relative.

    Returns:
        str: Joined and user-relative file path.
    """
    return os.path.expanduser(os.path.join(*args))
