#!/usr/bin/python
# This Python file uses the following encoding: utf-8

# Recipe Robot Tools
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
recipe-robot Tools
TODO: Module Docstring
"""


import os
import shlex
from subprocess import Popen, PIPE
import sys


class BColors(object):
    """Specify colors that are used in Terminal output."""
    BOLD = "\033[1m"
    DEBUG = "\033[95m"
    ENDC = "\033[0m"
    ERROR = "\033[91m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    UNDERLINE = "\033[4m"
    WARNING = "\033[93m"


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


def robo_print(output_type, message):
    """Print the specified message in an appropriate color, and only print
    debug output if debug_mode is True.

    Args:
        output_type: One of "error", "warning", "debug", or "verbose".
        message: String to be printed to output.
    """

    if output_type == "error":
        print >> sys.stderr, "%s[ERROR] %s%s" % (BColors.ERROR, message, BColors.ENDC)
        sys.exit(1)
    elif output_type == "warning":
        print >> sys.stderr, "%s[WARNING] %s%s" % (BColors.WARNING, message, BColors.ENDC)
    elif output_type == "reminder":
        print "%s[REMINDER] %s%s" % (BColors.OKBLUE, message, BColors.ENDC)
    elif output_type == "debug" and OutputMode.debug_mode is True:
        print "%s[DEBUG] %s%s" % (BColors.DEBUG, message, BColors.ENDC)
    elif output_type == "verbose":
        if OutputMode.verbose_mode is True or OutputMode.debug_mode is True:
            print message
        else:
            pass
    else:
        print message


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
            robo_print("error", "Unable to create directory at %s." % dest_dir)


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
            robo_print("verbose", "    %s" % png_path)
        else:
            robo_print("warning",
                       "An error occurred during icon extraction: %s" % err)


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
