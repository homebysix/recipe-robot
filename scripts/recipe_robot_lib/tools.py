#!/usr/bin/python
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
tools.py

This module of Recipe Robot contains various helper and tool functions that
support the main `recipe-robot` script and the `recipe_generator.py` module.
"""


from datetime import datetime
import os
import shlex
from subprocess import Popen, PIPE
import sys
from urllib2 import urlopen

# TODO(Elliot): Can we use the one at /Library/AutoPkg/FoundationPlist instead?
# Or not use it at all (i.e. use the preferences system correctly). (#16)
try:
    from recipe_robot_lib import FoundationPlist
except ImportError:
    print "[WARNING] importing plistlib as FoundationPlist"
    import plistlib as FoundationPlist


__version__ = '0.1.0'
ENDC = "\033[0m"

# Report dict that will be output to a plist when Recipe Robot is done.
report = {
    "errors": [],
    "reminders": [],
    "warnings": [],
    "recipes": [],
    "icons": [],
    "start_time": 0,
    "stop_time": 0
}


class LogLevel(object):
    """Specify colors that are used in Terminal output."""
    DEBUG = ("\033[95m", "DEBUG")
    ERROR = ("\033[91m", "ERROR")
    LOG = ("", "")
    REMINDER = ("\033[94m", "REMINDER")
    VERBOSE = ("\033[0m", "")
    WARNING = ("\033[93m", "WARNING")


class OutputMode(object):
    """Manage global output mode state with a singleton."""
    verbose_mode = False  # set to True for additional user-facing output
    debug_mode = False  # set to True to output everything all the time

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


def timer(action):
    if action == "start":
        report["start_time"] = int(datetime.now().strftime("%s"))
    if action == "stop":
        report["stop_time"] = int(datetime.now().strftime("%s"))


def robo_print(message, log_level=LogLevel.LOG, indent=0):
    """Print the specified message in an appropriate color, and only print
    debug output if debug_mode is True.

    Args:
        log_level: LogLevel property for desired loglevel.
        message: String to be printed to output.
    """
    color = log_level[0]
    indents = indent * " "
    if log_level[1]:
        prefix = "[%s] " % log_level[1]
    else:
        prefix = ""
    suffix = ENDC

    line = color + indents + prefix + message + suffix

    if log_level in (LogLevel.ERROR, LogLevel.WARNING):
        print_func = _print_stderr
    else:
        print_func = _print_stdout

    if log_level is LogLevel.ERROR:
        print_func(line)
        report["errors"].append(message)
        timer("stop")
        write_report(report, os.path.join("/tmp", "report.plist"))
        sys.exit(1)
    elif log_level is LogLevel.REMINDER:
        print_func(line)
        report["reminders"].append(message)
    elif log_level is LogLevel.WARNING:
        print_func(line)
        report["warnings"].append(message)
    elif log_level is LogLevel.LOG:
        print_func(line)
    elif log_level is LogLevel.DEBUG and OutputMode.debug_mode:
        print_func(line)
    elif log_level is LogLevel.VERBOSE and (OutputMode.verbose_mode or OutputMode.debug_mode):
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
        except OSError:
            robo_print("Unable to create directory at %s." % dest_dir, LogLevel.ERROR)


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
        with open(os.path.join(dest_dir_absolute, "SourceForgeURLProvider.py"), "wb") as download_file:
            download_file.write(raw_download.read())
            robo_print(os.path.join(dest_dir, "SourceForgeURLProvider.py"), LogLevel.VERBOSE, 4)
    except:
        robo_print("Unable to download SourceForgeURLProvider from GitHub.", LogLevel.WARNING)
        # TODO(Elliot):  Copy SourceForgeURLProvider from local file. (#46)


def extract_app_icon(icon_path, png_path):
    """Convert the app's icns file to 300x300 png at the specified path.
    300x300 is Munki's preferred size, and 128x128 is Casper's preferred size,
    as of 2015-08-01.

    Args:
        icon_path: The path to the .icns file we're converting to .png.
        png_path: The path to the .png file we're creating.
    """
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
            report["icons"].append(png_path)
        else:
            robo_print("An error occurred during icon extraction: %s" % err, LogLevel.WARNING)


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
            p[i]=Popen(shlex.split(cmd_part), stdin=PIPE, stdout=PIPE, stderr=PIPE)
        else:
            p[i]=Popen(shlex.split(cmd_part), stdin=p[i-1].stdout, stdout=PIPE, stderr=PIPE)
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

    #TODO(Shea): Get the version back in here.
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


def reset_term_colors():
    """Ensure terminal colors are normal."""
    sys.stdout.write(ENDC)


def write_report(report, report_file):
    FoundationPlist.writePlist(report, report_file)
