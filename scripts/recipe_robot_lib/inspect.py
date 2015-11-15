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
inspect.py

Look at a path or URL for an app and generate facts about it.
"""


from distutils.version import StrictVersion, LooseVersion
import json
import os
import re
import shutil
import sys
from urllib2 import urlopen, HTTPError, URLError, build_opener
from urlparse import urlparse
from xml.etree.ElementTree import parse, ParseError

from recipe_robot_lib import FoundationPlist as FoundationPlist
from recipe_robot_lib.exceptions import RoboError
from recipe_robot_lib.tools import (
    robo_print, LogLevel, any_item_in_string, SUPPORTED_INSTALL_FORMATS,
    SUPPORTED_IMAGE_FORMATS, SUPPORTED_ARCHIVE_FORMATS,
    get_exitcode_stdout_stderr, ALL_SUPPORTED_FORMATS, CACHE_DIR)


def process_input_path(facts):
    """Determine which functions to call based on type of input path.

    Args:
        args: The command line arguments.
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
    """
    args = facts["args"]
    # If --config was specified without an input path, stop here.
    if not args.input_path:
        sys.exit(0)
    # Otherwise, retrieve the input path.
    input_path = args.input_path
    robo_print("Processing %s ..." % input_path)

    # Strip trailing slash, but only if input_path is not a URL.
    if "http" not in input_path:
        input_path = input_path.rstrip("/ ")

    # Put input_path into our facts for reporting purposes
    facts["input_path"] = input_path

    # Initialize facts that are lists.
    facts["inspections"] = []
    facts["blocking_applications"] = []
    facts["codesign_authorities"] = []

    github_domains = ("github.com", "githubusercontent.com", "github.io")

    # Determine what kind of input path we are working with, then
    # inspect it.
    inspect_func = None
    if input_path.startswith("http"):
        if (input_path.endswith((".xml", ".rss", ".php")) or
            "appcast" in input_path):
            robo_print("Input path looks like a Sparkle feed.",
                       LogLevel.VERBOSE)
            inspect_func = inspect_sparkle_feed_url
        elif any_item_in_string(github_domains, input_path):
            robo_print("Input path looks like a GitHub URL.", LogLevel.VERBOSE)
            inspect_func = inspect_github_url
        elif "sourceforge.net" in input_path:
            robo_print("Input path looks like a SourceForge URL.",
                       LogLevel.VERBOSE)
            inspect_func = inspect_sourceforge_url
        elif "bitbucket.org" in input_path:
            robo_print("Input path looks like a BitBucket URL.",
                       LogLevel.VERBOSE)
            inspect_func = inspect_bitbucket_url
        else:
            robo_print("Input path looks like a download URL.",
                       LogLevel.VERBOSE)
            inspect_func = inspect_download_url
    elif input_path.startswith("ftp"):
        robo_print("Input path looks like a download URL.", LogLevel.VERBOSE)
        inspect_func = inspect_download_url
    elif os.path.exists(input_path):
        if input_path.endswith(".app"):
            robo_print("Input path looks like an app.", LogLevel.VERBOSE)
            inspect_func = inspect_app
        elif input_path.endswith(".recipe"):
            raise RoboError("Sorry, I can't use existing AutoPkg recipes as "
                            "input.")
        elif input_path.endswith(SUPPORTED_INSTALL_FORMATS):
            robo_print("Input path looks like an installer.", LogLevel.VERBOSE)
            inspect_func = inspect_pkg
        elif input_path.endswith(SUPPORTED_IMAGE_FORMATS):
            robo_print("Input path looks like a disk image.", LogLevel.VERBOSE)
            inspect_func = inspect_disk_image
        elif input_path.endswith(SUPPORTED_ARCHIVE_FORMATS):
            robo_print("Input path looks like an archive.", LogLevel.VERBOSE)
            inspect_func = inspect_archive
        else:
            raise RoboError("I haven't been trained on how to handle this "
                            "input path:\n\t%s" % input_path)
    else:
        raise RoboError("Input path does not exist. Please try again with a "
                        "valid input path.")

    if inspect_func:
        facts = inspect_func(input_path, args, facts)


def inspect_app(input_path, args, facts):
    """Process an app

    Gather information required to create a recipe.

    Args:
        input_path: The path or URL that Recipe Robot was asked to use
            to create recipes.
        args: The command line arguments.
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.

    Returns:
        facts dictionary.
    """
    # Only proceed if we haven't inspected this app yet.
    if "app" in facts["inspections"]:
        return facts
    else:
        facts["inspections"].append("app")

    # Save the path of the app. (Used when overriding AppStoreApp
    # recipes.)
    facts["app_path"] = input_path

    # Record this app as a blocking application (for munki recipe based
    # on pkg).
    facts["blocking_applications"].append(os.path.basename(input_path))

    # Read the app's Info.plist.
    robo_print("Validating app...", LogLevel.VERBOSE)
    try:
        info_plist = FoundationPlist.readPlist(
            input_path + "/Contents/Info.plist")
        robo_print("App seems valid", LogLevel.VERBOSE, 4)
    except (ValueError, FoundationPlist.NSPropertyListSerializationException) as error:
        raise RoboError("%s doesn't look like a valid app to me." % input_path,
                        error)

    # Get the filename of the app (which is usually the same as the app
    # name.)
    app_file = os.path.basename(input_path)[:-4]

    # Determine the name of the app. (Overwrites any previous app_name,
    # because the app Info.plist itself is the most reliable source.)
    app_name = ""
    robo_print("Getting app name...", LogLevel.VERBOSE)
    if "CFBundleName" in info_plist:
        app_name = info_plist["CFBundleName"]
    elif "CFBundleExecutable" in info_plist:
        app_name = info_plist["CFBundleExecutable"]
    else:
        app_name = app_file
    robo_print("App name is: %s" % app_name, LogLevel.VERBOSE, 4)
    facts["app_name"] = app_name

    # If the app's filename is different than the app's name, we need to
    # make a note of that. Many recipes require another input variable
    # for this.
    if app_name != app_file:
        robo_print("App name differs from the actual app filename.", LogLevel.VERBOSE)
        robo_print("Actual app filename: %s.app" % app_file, LogLevel.VERBOSE, 4)
        facts["app_file"] = app_file

    # Determine the bundle identifier of the app. (Overwrites any
    # previous bundle_id, because the app itself is the most reliable
    # source.)
    bundle_id = ""
    robo_print("Getting bundle identifier...", LogLevel.VERBOSE)
    if "CFBundleIdentifier" in info_plist:
        bundle_id = info_plist["CFBundleIdentifier"]
    else:
        raise RoboError("Strange, this app doesn't have a bundle identifier.")
    robo_print("Bundle identifier is: %s" % bundle_id, LogLevel.VERBOSE, 4)
    facts["bundle_id"] = bundle_id

    # Attempt to determine how to download this app.
    if "sparkle_feed" not in facts:
        sparkle_feed = ""
        download_format = ""
        robo_print("Checking for a Sparkle feed...", LogLevel.VERBOSE)
        if "SUFeedURL" in info_plist:
            sparkle_feed = info_plist["SUFeedURL"]
        elif "SUOriginalFeedURL" in info_plist:
            sparkle_feed = info_plist["SUOriginalFeedURL"]
        if sparkle_feed != "" and sparkle_feed != "NULL":
            facts = inspect_sparkle_feed_url(sparkle_feed, args, facts)
        else:
            robo_print("No Sparkle feed", LogLevel.VERBOSE, 4)

    if "is_from_app_store" not in facts:
        robo_print("Determining whether app was downloaded from the Mac App "
                   "Store...", LogLevel.VERBOSE)
        if os.path.exists("%s/Contents/_MASReceipt/receipt" % input_path):
            robo_print("App came from the App Store", LogLevel.VERBOSE, 4)
            facts["is_from_app_store"] = True
        else:
            robo_print("App did not come from the App Store", LogLevel.VERBOSE, 4)
            facts["is_from_app_store"] = False

    # Determine whether to use CFBundleShortVersionString or
    # CFBundleVersion for versioning.
    if "version_key" not in facts:
        version_key = ""
        robo_print("Looking for version key...", LogLevel.VERBOSE)
        if "CFBundleShortVersionString" in info_plist:
            if "CFBundleVersion" in info_plist:
                # Both keys exist, so we must decide with a cage match!
                try:
                    if StrictVersion(info_plist["CFBundleShortVersionString"]):
                        # CFBundleShortVersionString is strict. Use it.
                        version_key = "CFBundleShortVersionString"
                except ValueError:
                    # CFBundleShortVersionString is not strict.
                    try:
                        if StrictVersion(info_plist["CFBundleVersion"]):
                            # CFBundleVersion is strict. Use it.
                            version_key = "CFBundleVersion"
                    except ValueError:
                        # Neither are strict versions. Are they
                        # integers?
                        if info_plist["CFBundleShortVersionString"].isdigit():
                            version_key = "CFBundleShortVersionString"
                        elif info_plist["CFBundleVersion"].isdigit():
                            version_key = "CFBundleVersion"
                        else:
                            # CFBundleShortVersionString wins by
                            # default.
                            version_key = "CFBundleShortVersionString"
            else:
                version_key = "CFBundleShortVersionString"
        else:
            if "CFBundleVersion" in info_plist:
                version_key = "CFBundleVersion"
        if version_key != "":
            robo_print("Version key is: %s (%s)" %
                       (version_key, info_plist[version_key]), LogLevel.VERBOSE, 4)
            facts["version_key"] = version_key
        else:
            raise RoboError("Sorry, I can't determine which version key to "
                            "use for this app.")

    # Determine path to the app's icon.
    if "icon_path" not in facts:
        icon_path = ""
        robo_print("Looking for app icon...", LogLevel.VERBOSE)
        if "CFBundleIconFile" in info_plist:
            icon_path = os.path.join(input_path, "Contents", "Resources", info_plist["CFBundleIconFile"])
        else:
            facts["warnings"].append("Can't determine app icon.")
        if icon_path != "":
            robo_print("App icon is: %s" % icon_path, LogLevel.VERBOSE, 4)
            facts["icon_path"] = icon_path

    # Attempt to get a description of the app from MacUpdate.com.
    if "description" not in facts:
        robo_print("Getting app description from MacUpdate...", LogLevel.VERBOSE)
        description, warning = get_app_description(app_name)
        if description:
            robo_print("Description: %s" % description, LogLevel.VERBOSE, 4)
            facts["description"] = description
        if warning:
            facts["warnings"].append(warning)

    # Gather info from code signing attributes, including:
    #    - Code signature verification requirements
    #    - Expected authority names
    #    - Name of developer (according to signing certificate)
    #    - Code signature version (version 1 is obsolete, treated as unsigned)
    if facts.get("codesign_reqs", "") == "" and len(facts["codesign_authorities"]) == 0:
        codesign_reqs = ""
        codesign_authorities = []
        developer = ""
        codesign_version = ""
        robo_print("Gathering code signature information...", LogLevel.VERBOSE)
        cmd = "codesign --display --verbose=2 -r- \"%s\"" % (input_path)
        exitcode, out, err = get_exitcode_stdout_stderr(cmd)
        if exitcode == 0:
            # From stdout:
            reqs_marker = "designated => "
            for line in out.split("\n"):
                if line.startswith(reqs_marker):
                    codesign_reqs = line[len(reqs_marker):]
            # From stderr:
            authority_marker = "Authority="
            dev_marker = "Authority=Developer ID Application: "
            vers_marker = "Sealed Resources version="
            for line in err.split("\n"):  # The info we need is in stderr.
                if line.startswith(authority_marker):
                    codesign_authorities.append(line[len(authority_marker):])
                if line.startswith(dev_marker):
                    if " (" in line:
                        line = line.split(" (")[0]
                    developer = line[len(dev_marker):]
                if line.startswith(vers_marker):
                    codesign_version = line[len(vers_marker):len(vers_marker) + 1]
                    if codesign_version == "1":
                        facts["warnings"].append(
                            "This app uses an obsolete code signature.")
                        # Clear code signature markers, treat app as
                        # unsigned.
                        codesign_reqs = ""
                        codesign_authorities = []
                        break
        if codesign_reqs == "" and len(codesign_authorities) == 0:
            robo_print("App is not signed", LogLevel.VERBOSE, 4)
        else:
            robo_print("Code signature verification requirements recorded", LogLevel.VERBOSE, 4)
            facts["codesign_reqs"] = codesign_reqs
            robo_print("%s authority names recorded" % len(codesign_authorities), LogLevel.VERBOSE, 4)
            facts["codesign_authorities"] = codesign_authorities
        if developer != "":
            robo_print("Developer: %s" % developer, LogLevel.VERBOSE, 4)
            facts["developer"] = developer

    return facts


def get_app_description(app_name):
    """Use an app's name to generate a description from MacUpdate.com.

    Args:
        app_name: The name of the app that we need to describe.

    Returns:
        description: A string containing a description of the app.
    """
    # Start with an empty string. (If it remains empty, the parent
    # function will know that no description was available.)
    description = ""
    warning = None

    # This is the HTML immediately preceding the description text on the
    # MacUpdate search results page.
    description_marker = "-shortdescrip\">"

    cmd = "curl --silent \"http://www.macupdate.com/find/mac/%s\"" % app_name
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)

    # For each line in the resulting text, look for the description
    # marker.
    html = out.split("\n")
    if exitcode == 0:
        for line in html:
            if description_marker in line:
                # Trim the HTML from the beginning of the line.
                start = line.find(description_marker) + len(description_marker)
                # Trim the HTML from the end of the line.
                description = line[start:].rstrip("</span>")
                # If we found a description, no need to process further
                # lines.
                break
    else:
        warning = ("Error occurred while getting description from "
                   "MacUpdate: %s" % err)

    return (description, warning)


def inspect_archive(input_path, args, facts):
    """Process an archive

    Gather information required to create a recipe.

    Args:
        input_path: The path or URL that Recipe Robot was asked to use
            to create recipes.
        args: The command line arguments.
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.

    Returns:
        facts dictionary.
    """
    # Only proceed if we haven't inspected this pkg yet.
    if "archive" in facts["inspections"]:
        return facts
    else:
        facts["inspections"].append("archive")

    # Unzip the zip and look for an app. (If this fails, we try tgz
    # next.)
    archive_cmds = ({
        "format": "zip",
        "cmd": "/usr/bin/unzip \"%s\" -d \"%s\"" % (input_path, os.path.join(CACHE_DIR, "unpacked"))
    },{
        "format": "tgz",
        "cmd": "/usr/bin/tar -zxvf \"%s\" -C \"%s\"" % (input_path, os.path.join(CACHE_DIR, "unpacked"))
    })
    for this_format in archive_cmds:
        exitcode, out, err = get_exitcode_stdout_stderr(this_format["cmd"])
        if exitcode == 0:

            # Confirmed; the download was a disk image. Make a note of
            # that.
            robo_print("Successfully unarchived %s" % this_format["format"], LogLevel.VERBOSE, 4)
            facts["download_format"] = this_format["format"]

            # If the download filename was ambiguous, change it.
            if not facts.get("download_filename", input_path).endswith(SUPPORTED_ARCHIVE_FORMATS):
                facts["download_filename"] = "%s.%s" % (facts.get("download_filename", os.path.basename(input_path)), this_format["format"])

            # Locate and inspect any enclosed apps or pkgs.
            for this_file in os.listdir(os.path.join(CACHE_DIR, "unpacked")):
                if this_file.endswith(".app"):
                    # TODO(Elliot): What if .app isn't on root of zip? (#26)
                    # Example: https://github.com/jbtule/cdto/releases/download/2_6_0/cdto_2_6.zip
                    facts = inspect_app(os.path.join(CACHE_DIR, "unpacked", this_file), args, facts)
                    break
                if this_file.endswith(SUPPORTED_INSTALL_FORMATS):
                    facts = inspect_pkg(os.path.join(CACHE_DIR, "unpacked", this_file), args, facts)
                    break

            return facts

    robo_print("Unable to unpack this archive: %s\n(You can ignore this message if the previous attempt to mount the downloaded file as a disk image succeeded.)" % input_path, LogLevel.DEBUG)
    return facts


def inspect_bitbucket_url(input_path, args, facts):
    """Process a BitBucket URL

    Gather information required to create a recipe.

    Args:
        input_path: The path or URL that Recipe Robot was asked to use
            to create recipes.
        args: The command line arguments.
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.

    Returns:
        facts dictionary.
    """
    # Only proceed if we haven't inspected this BitBucket URL yet.
    if "bitbucket_url" in facts["inspections"]:
        return facts
    else:
        facts["inspections"].append("bitbucket_url")

    # Grab the BitBucket repo path.
    bitbucket_repo = ""
    robo_print("Getting BitBucket repo...", LogLevel.VERBOSE)
    r_obj = re.search(r"(?<=https://bitbucket\.org/)[\w-]+/[\w-]+", input_path)
    if r_obj is not None:
        bitbucket_repo = r_obj.group(0)
    if bitbucket_repo != "":
        robo_print("BitBucket repo is: %s" % bitbucket_repo, LogLevel.VERBOSE, 4)
        facts["bitbucket_repo"] = bitbucket_repo

        # Use GitHub API to obtain information about the repo and
        # releases.
        repo_api_url = "https://api.bitbucket.org/2.0/repositories/%s" % bitbucket_repo
        releases_api_url = "https://api.bitbucket.org/2.0/repositories/%s/downloads" % bitbucket_repo
        try:
            raw_json_repo = urlopen(repo_api_url).read()
            parsed_repo = json.loads(raw_json_repo)
            raw_json_release = urlopen(releases_api_url).read()
            parsed_release = json.loads(raw_json_release)
        except HTTPError as err:
            if err.code == 403:
                facts["warnings"].append(
                    "Error occurred while getting information from the "
                    "BitBucket API. If you've been creating a lot of recipes "
                    "quickly, you may have hit the rate limit. Give it a few "
                    "minutes, then try again. (%s)" % err)
                return facts
            if err.code == 404:
                facts["warnings"].append(
                    "BitBucket API URL not found. " "(%s)" % err)
                return facts
            else:
                facts["warnings"].append(
                    "Error occurred while getting information from the "
                    "BitBucket API. (%s)" % err)
                return facts
        except URLError as err:
            if str(err.reason).startswith("[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE]"):
                # TODO(Elliot): Try again using curl? (#19)
                facts["warnings"].append(
                    "I got an SSLv3 handshake error while getting "
                    "information from the BitBucket API, and I don't yet "
                    "know what to do with that. (%s)" % err)
                return facts
            else:
                facts["warnings"].append(
                    "Error encountered while getting information from the "
                    "BitBucket API. (%s)" % err)
                return facts

        # Get app name.
        if "app_name" not in facts:
            app_name = ""
            robo_print("Getting app name...", LogLevel.VERBOSE)
            if parsed_repo.get("name", "") != "":
                app_name = parsed_repo["name"]
            if app_name != "":
                robo_print("App name is: %s" % app_name, LogLevel.VERBOSE, 4)
                facts["app_name"] = app_name

        # Get full name of owner.
        developer = ""
        if "developer" not in facts:
            developer = parsed_repo["owner"]["display_name"]
        if developer != "":
            robo_print("BitBucket owner full name "
                       "is: %s" % developer, LogLevel.VERBOSE, 4)
            facts["developer"] = developer

        # Get app description.
        if "description" not in facts:
            description = ""
            robo_print("Getting BitBucket description...", LogLevel.VERBOSE)
            if parsed_repo.get("description", "") != "":
                description = parsed_repo["description"]
            if description != "":
                robo_print("BitBucket description is: %s" % description, LogLevel.VERBOSE, 4)
                facts["description"] = description
            else:
                facts["warnings"].append(
                    "Could not detect BitBucket description.")

        # Get download format of latest release.
        if "download_format" not in facts or "download_url" not in facts:
            download_format = ""
            download_url = ""
            robo_print("Getting information from latest BitBucket release...", LogLevel.VERBOSE)
            if "values" in parsed_release:
                for asset in parsed_release["values"]:
                    for this_format in ALL_SUPPORTED_FORMATS:
                        if asset["links"]["self"]["href"].endswith(this_format):
                            download_format = this_format
                            download_url = asset["links"]["self"]["href"]
                            break
            if download_format != "":
                robo_print("BitBucket release download format "
                           "is: %s" % download_format, LogLevel.VERBOSE, 4)
                facts["download_format"] = download_format
            else:
                facts["warnings"].append(
                    "Could not detect BitBucket release download format.")
            if download_url != "":
                robo_print("BitBucket release download URL "
                           "is: %s" % download_url, LogLevel.VERBOSE, 4)
                facts["download_url"] = download_url
                facts = inspect_download_url(download_url, args, facts)
            else:
                facts["warnings"].append(
                    "Could not detect BitBucket release download URL.")

        # Warn user if the BitBucket project is private.
        if parsed_repo.get("is_private", False) is not False:
            facts["warnings"].append(
                "This BitBucket project is marked \"private\" and recipes "
                "you generate may not work for others.")

    else:
        facts["warnings"].append("Could not detect BitBucket repo.")

    return facts


def inspect_disk_image(input_path, args, facts):
    """Process an image

    Gather information required to create a recipe.

    Args:
        input_path: The path or URL that Recipe Robot was asked to use
            to create recipes.
        args: The command line arguments.
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.

    Returns:
        facts dictionary.
    """
    # Only proceed if we haven't inspected this pkg yet.
    if "disk_image" in facts["inspections"]:
        return facts
    else:
        facts["inspections"].append("disk_image")

    # Determine whether the dmg has a software license agreement.
    # Inspired by: https://github.com/autopkg/autopkg/blob/master/Code/autopkglib/DmgMounter.py#L74-L98
    dmg_has_sla = False
    cmd = "/usr/bin/hdiutil imageinfo -plist \"%s\"" % input_path
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if exitcode == 0:
        with open(os.path.join(CACHE_DIR, "dmg_info.plist"), "wb") as dmg_plist:
            dmg_plist.write(out)
        try:
            dmg_info = FoundationPlist.readPlist(os.path.join(CACHE_DIR, "dmg_info.plist"))
            if dmg_info.get("Properties").get("Software License Agreement") == True:
                dmg_has_sla = True
        except FoundationPlist.NSPropertyListSerializationException:
            pass

    # Mount the dmg and look for an app.
    cmd = "/usr/bin/hdiutil attach -nobrowse -plist \"%s\"" % input_path
    if dmg_has_sla is True:
        exitcode, out, err = get_exitcode_stdout_stderr(cmd, "Y\n")
    else:
        exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if exitcode == 0:

        # Confirmed; the download was a disk image. Make a note of that.
        robo_print("Successfully mounted disk image", LogLevel.VERBOSE, 4)
        facts["download_format"] = "dmg"  # most common disk image format

        # If the download filename was ambiguous, change it.
        if not facts.get("download_filename", input_path).endswith(SUPPORTED_IMAGE_FORMATS):
            facts["download_filename"] = facts.get("download_filename", input_path) + ".dmg"

        # Clean the output for cases where the dmg has a license
        # agreement.
        out_clean = out[out.find("<?xml"):]

        # Locate and inspect the app.
        with open(os.path.join(CACHE_DIR, "dmg_attach.plist"), "wb") as dmg_plist:
            dmg_plist.write(out_clean)
        try:
            dmg_dict = FoundationPlist.readPlist(os.path.join(CACHE_DIR, "dmg_attach.plist"))
        except Exception as error:
            raise RoboError(
                "Shoot, I had trouble parsing the output of hdiutil while "
                "mounting the downloaded dmg. Sorry about that.", error)
        for entity in dmg_dict["system-entities"]:
            if "mount-point" in entity:
                dmg_mount = entity["mount-point"]
                break
        for this_file in os.listdir(dmg_mount):
            if this_file.endswith(".app"):
                # Copy app to cache folder.
                # TODO(Elliot): What if .app isn't on root of dmg mount? (#26)
                attached_app_path = os.path.join(dmg_mount, this_file)
                cached_app_path = os.path.join(CACHE_DIR, "unpacked", this_file)
                if not os.path.exists(cached_app_path):
                    try:
                        shutil.copytree(attached_app_path, cached_app_path)
                    except shutil.Error:
                        pass
                # Unmount attached volume when done.
                cmd = "/usr/bin/hdiutil detach \"%s\"" % dmg_mount
                exitcode, out, err = get_exitcode_stdout_stderr(cmd)
                facts = inspect_app(cached_app_path, args, facts)
                break
            if this_file.endswith(SUPPORTED_INSTALL_FORMATS):
                facts = inspect_pkg(os.path.join(dmg_mount, this_file), args, facts)
                break
    else:
        robo_print("Unable to mount %s. (%s)\n(You can ignore this message if the upcoming attempt to unzip the downloaded file as an archive succeeds.)" % (input_path, err), LogLevel.DEBUG)

    return facts


def inspect_download_url(input_path, args, facts):
    """Process a direct download URL

    Gather information required to create a recipe.

    Args:
        input_path: The path or URL that Recipe Robot was asked to use
            to create recipes.
        args: The command line arguments.
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.

    Returns:
        facts dictionary.
    """
    # We never skip download URL inspection, even if we've already
    # inspected a download URL during this run. This handles rare
    # situations in which the download URL is in a different format than
    # the Sparkle download.
    # Example:
    # http://rdio0-a.akamaihd.net/media/static/desktop/mac/Rdio.dmg

    input_path = input_path.strip().replace(" ", "%20")

    # Save the download URL to the dictionary of facts.
    robo_print("Download URL is: %s" % input_path, LogLevel.VERBOSE, 4)
    facts["download_url"] = input_path
    facts["is_from_app_store"] = False

    # If download URL is hosted on GitHub or SourceForge, we can gather
    # more information.
    if "github.com" in input_path or "githubusercontent.com" in input_path:
        if "github_repo" not in facts:
            facts = inspect_github_url(input_path, args, facts)
    if "sourceforge.net" in input_path:
        if "sourceforge_id" not in facts:
            facts = inspect_sourceforge_url(input_path, args, facts)

    # Warn if it looks like we're using a version-specific download
    # path, but only if the path was not obtained from a feed of some
    # sort.
    version_match = re.search(r"[\d]+\.[\w]+$", input_path)
    if version_match is not None and ("sparkle_feed_url" not in facts["inspections"] and
                                      "github_url" not in facts["inspections"] and
                                      "sourceforge_url" not in facts["inspections"] and
                                      "bitbucket_url" not in facts["inspections"]):
        facts["warnings"].append(
            "Careful, this might be a version-specific URL. Better to give me "
            "a \"-latest\" URL or a Sparkle feed.")

    # Determine filename from input URL (will be overridden later if a
    # better candidate is found.)
    parsed_url = urlparse(input_path)
    filename = parsed_url.path.split("/")[-1]

    # If the download URL doesn't already end with the parsed filename,
    # it's very likely that URLDownloader needs the filename argument
    # specified.
    if not input_path.endswith(filename):
        facts["specify_filename"] = True
    else:
        facts["specify_filename"] = False

    # Download the file for continued inspection.
    # TODO(Elliot): Maybe something like this is better for downloading
    # big files? https://gist.github.com/gourneau/1430932 (#24)
    robo_print("Downloading file for further inspection...", LogLevel.VERBOSE)

    # Actually download the file.
    try:
        raw_download = urlopen(input_path)
    except HTTPError as err:
        if err.code == 403:
            # Try again, this time with a user-agent.
            try:
                opener = build_opener()
                opener.addheaders = [("User-agent", "Mozilla/5.0")]
                raw_download = opener.open(input_path)
                facts["warnings"].append(
                    "I had to use a different user-agent in order to "
                    "download this file. If you run the recipes and get a "
                    "\"Can't open URL\" error, it means AutoPkg encountered "
                    "the same problem.")
                facts["user-agent"] = "Mozilla/5.0"
            except Exception as err:
                facts["warnings"].append(
                    "Error encountered during file download. (%s)" % err)
                return facts
        if err.code == 404:
            facts["warnings"].append("Download URL not found. (%s)" % err)
            return facts
        else:
            facts["warnings"].append(
                "Error encountered during file download. (%s)" % err)
            return facts
    except URLError as err:
        if str(err.reason).startswith("[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE]"):
            # TODO(Elliot): Try again using curl? (#19)
            facts["warnings"].append(
                "I got an SSLv3 handshake error, and I don't yet know what to "
                "do with that. (%s)" % err)
            return facts
        else:
            facts["warnings"].append("Error encountered during file download. "
                                     "(%s)" % err.reason)
            return facts

    # Get the actual filename from the server, if it exists.
    if "Content-Disposition" in raw_download.info():
        content_disp = raw_download.info()["Content-Disposition"]
        r_obj = re.search(r"filename=\"(.+)\"\;", content_disp)
        if r_obj is not None:
            filename = r_obj.group(1)

    # If filename was not detected from either the URL or the headers,
    # use a safe default name.
    if filename == "":
        filename = "download"
    facts["download_filename"] = filename

    # Write the downloaded file to the cache folder.
    with open(os.path.join(CACHE_DIR, filename), "wb") as download_file:
        download_file.write(raw_download.read())
        robo_print("Downloaded to %s" % os.path.join(CACHE_DIR, filename), LogLevel.VERBOSE, 4)

    # Just in case the "download" was actually a Sparkle feed.
    hidden_sparkle = False
    with open(os.path.join(CACHE_DIR, filename), "r") as download_file:
        if download_file.read()[:6] == "<?xml ":
            robo_print("This download is actually a Sparkle "
                       "feed", LogLevel.VERBOSE, 4)
            hidden_sparkle = True
    if hidden_sparkle is True:
        os.remove(os.path.join(CACHE_DIR, filename))
        facts = inspect_sparkle_feed_url(input_path, args, facts)
        return facts

    # Try to determine the type of file downloaded. (Overwrites any
    # previous download_type, because the download URL is the most
    # reliable source.)
    download_format = ""
    robo_print("Determining download format...", LogLevel.VERBOSE)
    for this_format in ALL_SUPPORTED_FORMATS:
        if filename.lower().endswith(this_format) or this_format in parsed_url.query:
            download_format = this_format
            facts["download_format"] = this_format
            robo_print("File extension is %s" % this_format, LogLevel.VERBOSE, 4)
            break  # should stop after the first format match

    # If we've already seen the app and the download format, there's no
    # need to unpack the downloaded file.
    if "download_format" in facts and "app" in facts["inspections"]:
        return facts

    robo_print("Opening downloaded file...", LogLevel.VERBOSE)
    robo_print("Download format is unknown, so we're going to try mounting it "
               "as a disk image first, then unarchiving it. This may produce "
               "errors, but will hopefully result in a "
               "success.", LogLevel.DEBUG)

    # Open the disk image (or test to see whether the download is one).
    if (facts.get("download_format", "") == "" or download_format == "") or download_format in SUPPORTED_IMAGE_FORMATS:
        facts = inspect_disk_image(os.path.join(CACHE_DIR, filename), args, facts)

    # Open the zip archive (or test to see whether the download is one).
    if (facts.get("download_format", "") == "" or download_format == "") or download_format in SUPPORTED_ARCHIVE_FORMATS:
        facts = inspect_archive(os.path.join(CACHE_DIR, filename), args, facts)

    # Inspect the installer (or test to see whether the download is
    # one).
    if download_format in SUPPORTED_INSTALL_FORMATS:

        robo_print("Download format is %s" % download_format, LogLevel.VERBOSE, 4)
        facts["download_format"] = download_format

        # Inspect the package.
        facts = inspect_pkg(os.path.join(CACHE_DIR, filename), args, facts)

    if facts.get("download_format", "") == "":
        facts["warnings"].append(
            "I've investigated pretty thoroughly, and I'm still not sure "
            "what the download format is. This could cause problems later.")

    return facts


def inspect_github_url(input_path, args, facts):
    """Process a GitHub URL

    Gather information required to create a recipe.

    Args:
        input_path: The path or URL that Recipe Robot was asked to use
            to create recipes.
        args: The command line arguments.
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.

    Returns:
        facts dictionary.
    """
    # Only proceed if we haven't inspected this GitHub URL yet.
    if "github_url" in facts["inspections"]:
        return facts
    else:
        facts["inspections"].append("github_url")

    # Grab the GitHub repo path.
    github_repo = ""
    robo_print("Getting GitHub repo...", LogLevel.VERBOSE)
    # Matches all these examples:
    # [x] https://github.com/jbtule/cdto/releases/download/2_6_0/cdto_2_6.zip
    # [x] https://github.com/lindegroup/autopkgr
    # [x] https://raw.githubusercontent.com/macmule/AutoCasperNBI/master/README.md
    # [X] https://api.github.com/repos/macmule/AutoCasperNBI
    # [X] https://hjuutilainen.github.io/munkiadmin/
    github_repo = ""
    parsed_url = urlparse(input_path)
    path = parsed_url.path.split("/")
    path.remove("")
    if "api.github.com" in input_path:
        if "/repos/" not in input_path:
            message = "GitHub API URL specified is not a repository."
            facts["warnings"].append(message)
        else:
            github_repo = path[1] + "/" + path[2]
    elif ".github.io" in input_path:
        github_repo = parsed_url.netloc.split(".")[0] + "/" + path[0]
    else:
        github_repo = path[0] + "/" + path[1]
    if github_repo != "":
        robo_print("GitHub repo is: %s" % github_repo, LogLevel.VERBOSE, 4)
        facts["github_repo"] = github_repo

        # TODO(Elliot): How can we use GitHub tokens to prevent rate
        # limiting? (#18)

        # Use GitHub API to obtain information about the repo and
        # releases.
        repo_api_url = "https://api.github.com/repos/%s" % github_repo
        releases_api_url = "https://api.github.com/repos/%s/releases/latest" % github_repo
        user_api_url = "https://api.github.com/users/%s" % github_repo.split("/")[0]

        # Download the information from the GitHub API.
        try:
            raw_json_repo = urlopen(repo_api_url).read()
            raw_json_release = urlopen(releases_api_url).read()
            raw_json_user = urlopen(user_api_url).read()
        except HTTPError as err:
            if err.code == 403:
                facts["warnings"].append(
                    "Error occurred while getting information from the GitHub "
                    "API. If you've been creating a lot of recipes quickly, "
                    "you may have hit the rate limit. Give it a few minutes, "
                    "then try again. (%s)" % err)
                return facts
            if err.code == 404:
                facts["warnings"].append("GitHub API URL not found. (%s)" %
                                         err)
                return facts
            else:
                facts["warnings"].append(
                    "Error occurred while getting information from the GitHub "
                    "API. (%s)" % err)
                # TODO: All of these return facts can just be return, since
                # dicts are passed by reference.
                return facts
        except URLError as err:
            if str(err.reason).startswith(
                    "[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE]"):
                # TODO(Elliot): Try again using curl? (#19)
                facts["warnings"].append(
                    "I got an SSLv3 handshake error while getting information "
                    "from the GitHub API, and I don't yet know what to do "
                    "with that. (%s)" % err)
                return facts
            else:
                facts["warnings"].append(
                    "Error encountered while getting information from the "
                    "GitHub API. (%s)" % err)
                return facts

        # Parse the downloaded JSON.
        parsed_repo = json.loads(raw_json_repo)
        parsed_release = json.loads(raw_json_release)
        parsed_user = json.loads(raw_json_user)

        # Get app name.
        if "app_name" not in facts:
            app_name = ""
            robo_print("Getting app name...", LogLevel.VERBOSE)
            if parsed_repo.get("name", None) is not None:
                app_name = parsed_repo["name"]
            if app_name != "":
                robo_print("App name is: %s" % app_name, LogLevel.VERBOSE, 4)
                facts["app_name"] = app_name

        # Get app description.
        if "description" not in facts:
            description = ""
            robo_print("Getting GitHub description...", LogLevel.VERBOSE)
            if parsed_repo.get("description", None) is not None:
                description = parsed_repo["description"]
            if description != "":
                robo_print("GitHub description is: %s" % description,
                           LogLevel.VERBOSE, 4)
                facts["description"] = description
            else:
                facts["warnings"].append("No GitHub description provided.")

        # Get download format of latest release.
        if "download_format" not in facts or "download_url" not in facts:
            download_format = ""
            download_url = ""
            robo_print("Getting information from latest GitHub release...",
                       LogLevel.VERBOSE)
            if "assets" in parsed_release:
                for asset in parsed_release["assets"]:
                    for this_format in ALL_SUPPORTED_FORMATS:
                        if asset["browser_download_url"].endswith(this_format):
                            download_format = this_format
                            download_url = asset["browser_download_url"]
                            break
            if download_format != "":
                robo_print("GitHub release download format "
                           "is: %s" % download_format,
                           LogLevel.VERBOSE, 4)
                facts["download_format"] = download_format
            else:
                facts["warnings"].append(
                    "Could not detect GitHub release download format.")
            if download_url != "":
                robo_print("GitHub release download URL "
                           "is: %s" % download_url, LogLevel.VERBOSE, 4)
                facts["download_url"] = download_url
                facts = inspect_download_url(download_url, args, facts)
            else:
                facts["warnings"].append(
                    "Could not detect GitHub release download URL.")

        # Get the developer's name from GitHub.
        if "developer" not in facts:
            developer = ""
            robo_print("Getting developer name from GitHub...",
                       LogLevel.VERBOSE)
            if "name" in parsed_user:
                developer = parsed_user["name"]
            if developer != "":
                robo_print("GitHub developer "
                           "is: %s" % developer, LogLevel.VERBOSE, 4)
                facts["developer"] = developer
            else:
                facts["warnings"].append("Could not detect GitHub developer.")

        # Warn user if the GitHub project is private.
        if parsed_repo.get("private", False) is not False:
            facts["warnings"].append(
                "This GitHub project is marked \"private\" and recipes you "
                "generate may not work for others.")

        # Warn user if the GitHub project is a fork.
        if parsed_repo.get("fork", False) is not False:
            facts["warnings"].append(
                "This GitHub project is a fork. You may want to try again "
                "with the original repo URL instead.")
    else:
        facts["warnings"].append("Could not detect GitHub repo.")

    return facts


def inspect_pkg(input_path, args, facts):
    """Process a package

    Gather information required to create a recipe.

    Args:
        input_path: The path or URL that Recipe Robot was asked to use
            to create recipes.
        args: The command line arguments.
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.

    Returns:
        facts dictionary.
    """
    # Only proceed if we haven't inspected this pkg yet.
    if "pkg" in facts["inspections"]:
        return facts
    else:
        facts["inspections"].append("pkg")

    # Check whether package is signed.
    robo_print("Checking whether package is signed...", LogLevel.VERBOSE)
    cmd = "/usr/sbin/pkgutil --check-signature \"%s\"" % input_path
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if exitcode == 1:
        robo_print("Package is not signed", LogLevel.VERBOSE, 4)
    elif exitcode == 0:
        robo_print("Package is signed", LogLevel.VERBOSE, 4)

        # Get developer name from pkg signature.
        if "developer" not in facts:
            developer = ""
            robo_print("Getting developer from pkg signature...", LogLevel.VERBOSE)
            marker = "    1. Developer ID Installer: "
            for line in out.split("\n"):
                if line.startswith(marker):
                    if " (" in line:
                        line = line.split(" (")[0]
                    developer = line[len(marker):]
            if developer != "":
                robo_print("Developer is: %s" % developer, LogLevel.VERBOSE, 4)
                facts["developer"] = developer
            else:
                robo_print("Developer is unknown", LogLevel.VERBOSE, 4)

        # Get code signature verification authority names from pkg
        # signature.
        if len(facts["codesign_authorities"]) == 0:
            codesign_authorities = []
            robo_print("Getting package signature authority names...", LogLevel.VERBOSE)
            for line in out.split("\n"):
                if re.match("^    [\d]\. ", line):
                    codesign_authorities.append(line[7:])
            if codesign_authorities != []:
                robo_print("%s authority names recorded" % len(codesign_authorities), LogLevel.VERBOSE, 4)
                facts["codesign_authorities"] = codesign_authorities
            else:
                robo_print("Authority names unknown, treating as unsigned", LogLevel.VERBOSE, 4)

    else:
        robo_print("I don't know whether the package is signed - probably not "
                   "(pkgutil returned exit code %s)" % exitcode, LogLevel.VERBOSE, 4)

    # Expand the flat package and look for more facts.
    robo_print("Expanding package to look for clues...", LogLevel.VERBOSE)
    expand_path = os.path.join(CACHE_DIR, "expanded")
    if os.path.exists(expand_path):
        shutil.rmtree(expand_path)
    cmd = "/usr/sbin/pkgutil --expand \"%s\" \"%s\"" % (input_path, expand_path)
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if exitcode == 0:
        # Locate and inspect the app.
        robo_print("Package expanded to: %s" % os.path.join(CACHE_DIR, "expanded"), LogLevel.VERBOSE, 4)
        install_filename = ""
        for dirpath, dirnames, filenames in os.walk("%s" % os.path.join(CACHE_DIR, "expanded")):
            for dirname in dirnames:
                if dirname.startswith("."):
                    dirnames.remove(dirname)
            for filename in filenames:

                if filename == "PackageInfo":
                    robo_print("Getting information from PackageInfo file...", LogLevel.VERBOSE)
                    pkginfo_file = open(os.path.join(CACHE_DIR, "expanded", dirpath, filename), "r")
                    pkginfo_parsed = parse(pkginfo_file)

                    bundle_id = ""
                    if "bundle_id" not in facts:
                        bundle_id = pkginfo_parsed.getroot().attrib["identifier"]
                    if bundle_id != "":
                        robo_print("Bundle identifier: %s" % bundle_id, LogLevel.VERBOSE, 4)
                        facts["bundle_id"] = bundle_id

                    install_loc = pkginfo_parsed.getroot().attrib.get("install-location", "")
                    if install_loc != "":
                        robo_print("Install location: %s" % install_loc, LogLevel.VERBOSE, 4)
                    else:
                        robo_print("No install location specified", LogLevel.VERBOSE, 4)

                    install_filename = os.path.basename(install_loc)
                    robo_print("Install filename: %s" % install_filename, LogLevel.VERBOSE, 4)
                    continue  # TODO(Elliot): Or should we stop after the first? (#27)

                if filename == "Payload":
                    # We found a payload. Let's peek inside and see if
                    # there's an app.
                    robo_print("Extracting the package payload to see if we "
                               "can find an app...", LogLevel.VERBOSE)
                    app_found = False
                    payload_path = os.path.join(CACHE_DIR, "expanded", dirpath, filename)
                    if install_filename.endswith(".app"):
                        extracted_app_path = os.path.join(CACHE_DIR, "extracted_apps", install_filename)
                        if os.path.exists(extracted_app_path):
                            shutil.rmtree(extracted_app_path)
                        cmd = "/usr/bin/gunzip -c \"%s\" | pax -r -s \",./,%s/,\"" % (payload_path, extracted_app_path)
                        # TODO(Elliot): This doesn't work because it's outside the working directory. (#27)
                        exitcode, out, err = get_exitcode_stdout_stderr(cmd)
                        if exitcode == 0:
                            app_found = True
                            robo_print("Found app: %s" % extracted_app_path, LogLevel.VERBOSE, 4)
                            facts = inspect_app(extracted_app_path, args, facts)
                            break  # Struck pay dirt, so stop iterating
                                   # through apps in the payload
                        else:
                            robo_print("Error extracting the payload. (%s)" % err, LogLevel.VERBOSE, 4)

                    elif install_filename == "":

                        cmd = "/usr/bin/gunzip -c \"%s\" | pax" % payload_path
                        exitcode, out, err = get_exitcode_stdout_stderr(cmd)
                        if exitcode == 0:
                            out = out.split("\n")
                            for line in out:
                                if line.endswith(".app"):
                                    facts["blocking_applications"].append(os.path.basename(line))
                                    if ".app/Contents/" not in line:
                                        app_found = True
                                        robo_print("Found app: %s" % line, LogLevel.VERBOSE, 4)
                                        extracted_app_path = os.path.join(CACHE_DIR, "extracted_apps", os.path.split(line)[1])
                                        cmd = "/usr/bin/gunzip -c \"%s\" | pax -r -s \",%s,%s,\"" % (os.path.join(CACHE_DIR, "expanded", filename), line, extracted_app_path)
                                        exitcode, out, err = get_exitcode_stdout_stderr(cmd)
                                        if exitcode == 0:
                                            facts = inspect_app(extracted_app_path, args, facts)
                                            break  # Struck pay dirt, so stop iterating
                                                   # through apps in the payload
                                            # TODO(Elliot): Should we stop at the first app? (#27)
                                            # Find multiple, but use the one with the shortest path?
                                            # Find multiple, but use the largest file size?
                                            # Inspect all of them, use only the one with a Sparkle feed?
                                        else:
                                            robo_print("Error while extracting the package payload. "
                                                       "(%s)" % err, LogLevel.VERBOSE, 4)
                        else:
                            robo_print("Error while examining the package payload. "
                                       "(%s)" % err, LogLevel.VERBOSE, 4)

                    if app_found is False:
                        robo_print("Did not find an app in the package "
                                   "payload", LogLevel.VERBOSE, 4)
                    break  # Once we're done examining the Payload, there's not
                           # much else we can examine.

                if filename.endswith(".app"):
                    facts = inspect_app(filename, args, facts)
                    break  # Struck pay dirt, so stop iterating through files
                           # in the package

    else:
        robo_print("Unable to expand package", LogLevel.DEBUG, 4)

    # TODO(Elliot): What info do we need to gather to produce recipes here? (#27)

    return facts


def inspect_sourceforge_url(input_path, args, facts):
    """Process a SourceForge URL

    Gather information required to create a recipe.

    Args:
        input_path: The path or URL that Recipe Robot was asked to use
            to create recipes.
        args: The command line arguments.
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.

    Returns:
        facts dictionary.
    """
    # Only proceed if we haven't inspected this SourceForge URL yet.
    if "sourceforge_url" in facts["inspections"]:
        return facts
    else:
        facts["inspections"].append("sourceforge_url")

    # Determine the name of the SourceForge project.
    proj_name = ""
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
        facts["warnings"].append("Unable to parse SourceForge URL.")
    if proj_name != "":

        # Use SourceForge API to obtain project information.
        project_api_url = "https://sourceforge.net/rest/p/" + proj_name
        try:
            raw_json = urlopen(project_api_url).read()
        except HTTPError as err:
            if err.code == 403:
                facts["warnings"].append(
                    "Error occurred while getting information from the "
                    "SourceForge API. If you've been creating a lot of "
                    "recipes quickly, you may have hit the rate limit. Give "
                    "it a few minutes, then try again. (%s)" % err)
                return facts
            if err.code == 404:
                facts["warnings"].append("SourceForge API URL not found. "
                                         "(%s)" % err)
                return facts
            else:
                facts["warnings"].append(
                    "Error occurred while getting information from the "
                    "SourceForge API. (%s)" % err)
                return facts
        except URLError as err:
            if str(err.reason).startswith("[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE]"):
                # TODO(Elliot): Try again using curl? (#19)
                facts["warnings"].append(
                    "I got an SSLv3 handshake error while getting information "
                    "from the SourceForge API, and I don't yet know what to "
                    "do with that. (%s)" % err)
                return facts
            else:
                facts["warnings"].append(
                    "Error encountered while getting information from the "
                    "SourceForge API. (%s)" % err)
                return facts
        parsed_json = json.loads(raw_json)

        # Get app name.
        if "app_name" not in facts:
            if "shortname" in parsed_json or "name" in parsed_json:
                # Record the shortname, if shortname isn't blank.
                if parsed_json["shortname"] != "":
                    app_name = parsed_json["shortname"]
                # Overwrite shortname with name, if name isn't blank.
                if parsed_json["name"] != "":
                    app_name = parsed_json["name"]
            if app_name != "":
                robo_print("App name is: %s" % app_name, LogLevel.VERBOSE, 4)
                facts["app_name"] = app_name

        # Determine project ID.
        proj_id = ""
        robo_print("Getting SourceForge project ID...", LogLevel.VERBOSE)
        for this_dict in parsed_json["tools"]:
            if "sourceforge_group_id" in this_dict:
                proj_id = this_dict["sourceforge_group_id"]
        if proj_id != "":
            robo_print("SourceForge project ID is: %s" % proj_id, LogLevel.VERBOSE, 4)
            facts["sourceforge_id"] = proj_id
        else:
            facts["warnings"].append(
                "Could not detect SourceForge project ID.")

        # Get project description.
        if "description" not in facts:
            description = ""
            robo_print("Getting SourceForge description...", LogLevel.VERBOSE)
            if "summary" in parsed_json:
                if parsed_json["summary"] != "":
                    description = parsed_json["summary"]
                elif parsed_json["short_description"] != "":
                    description = parsed_json["short_description"]
            if description != "":
                robo_print("SourceForge description is: %s" % description, LogLevel.VERBOSE, 4)
                facts["description"] = description
            else:
                facts["warnings"].append(
                    "Could not detect SourceForge description.")

        # Get download format of latest release.
        if "download_url" not in facts:

            # Download the RSS feed and parse it.
            # Example: http://sourceforge.net/projects/grandperspectiv/rss
            # Example: http://sourceforge.net/projects/cord/rss
            files_rss = "http://sourceforge.net/projects/%s/rss" % proj_name
            try:
                raw_xml = urlopen(files_rss)
            except Exception as err:
                facts["warnings"].append(
                    "Error occurred while inspecting SourceForge RSS feed: "
                    "%s" % err)
            doc = parse(raw_xml)

            # Get the latest download URL.
            download_url = ""
            robo_print("Determining download URL from SourceForge RSS feed...", LogLevel.VERBOSE)
            for item in doc.iterfind("channel/item"):
                # TODO(Elliot): The extra-info tag is not a reliable
                # indicator of which item should actually be downloaded.
                # (#21) Example:
                # http://sourceforge.net/projects/grandperspectiv/rss
                search = "{https://sourceforge.net/api/files.rdf#}extra-info"
                if item.find(search).text.startswith("data"):
                    download_url = item.find("link").text.rstrip("/download")
                    break
            if download_url != "":
                facts = inspect_download_url(download_url, args, facts)
            else:
                facts["warnings"].append(
                    "Could not detect SourceForge latest release "
                    "download_url.")

        # Warn user if the SourceForge project is private.
        if "private" in parsed_json:
            if parsed_json["private"] is True:
                facts["warnings"].append(
                    "This SourceForge project is marked \"private\" and "
                    "recipes you generate may not work for others.")

    else:
        facts["warnings"].append("Could not detect SourceForge project name.")

    return facts


def inspect_sparkle_feed_url(input_path, args, facts):
    """Process a Sparkle feed URL

    Gather information required to create a recipe.

    Args:
        input_path: The path or URL that Recipe Robot was asked to use
            to create recipes.
        args: The command line arguments.
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.

    Returns:
        facts dictionary.
    """
    # Only proceed if we haven't inspected this Sparkle feed yet.
    if "sparkle_feed_url" in facts["inspections"]:
        return facts
    else:
        facts["inspections"].append("sparkle_feed_url")

    # Save the Sparkle feed URL to the dictionary of facts.
    robo_print("Sparkle feed is: %s" % input_path, LogLevel.VERBOSE, 4)
    facts["sparkle_feed"] = input_path

    # Download the Sparkle feed.
    try:
        raw_xml = urlopen(input_path)
    except HTTPError as err:
        if err.code == 403:
            # Try again, this time with a user-agent.
            try:
                opener = build_opener()
                opener.addheaders = [("User-agent", "Mozilla/5.0")]
                raw_xml = opener.open(input_path)
                facts["warnings"].append(
                    "I had to use a different user-agent in order to read "
                    "this Sparkle feed. If you run the recipes and get a "
                    "\"Can't open URL\" error, it means AutoPkg encountered "
                    "the same problem.")
                facts["user-agent"] = "Mozilla/5.0"
            except Exception as err:
                facts["warnings"].append(
                    "Error occurred while downloading Sparkle feed (%s)" % err)
                # Remove Sparkle feed if it's not usable.
                facts.pop("sparkle_feed", None)
                return facts
        if err.code == 404:
            facts["warnings"].append("Sparkle feed not found. (%s)" % err)
            facts.pop("sparkle_feed", None)
            return facts
        else:
            facts["warnings"].append(
                "Error occurred while getting information from the Sparkle "
                "feed. (%s)" % err)
            facts.pop("sparkle_feed", None)
            return facts
    except URLError as err:
        if str(err.reason).startswith("[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE]"):
            # TODO(Elliot): Try again using curl? (#19)
            facts["warnings"].append(
                "I got an SSLv3 handshake error while getting information "
                "from the Sparkle feed, and I don't yet know what to do with "
                "that.  (%s)" % err)
            facts.pop("sparkle_feed", None)
            return facts
        else:
            facts["warnings"].append(
                "Error encountered while getting information from the "
                "Sparkle feed. (%s)" % err)
            facts.pop("sparkle_feed", None)
            return facts

    # Parse the Sparkle feed.
    xmlns = "http://www.andymatuschak.org/xml-namespaces/sparkle"
    try:
        doc = parse(raw_xml)
    except ParseError as err:
        facts["warnings"].append(
            "Error occurred while parsing Sparkle feed (%s)" % err)
        facts.pop("sparkle_feed", None)
        return facts


    # Determine whether the Sparkle feed provides a version number.
    sparkle_provides_version = False
    latest_version = "0"
    latest_url = ""
    robo_print("Getting information from Sparkle feed...", LogLevel.VERBOSE)
    for item in doc.iterfind("channel/item/enclosure"):
        if item.get("{%s}shortVersionString" % xmlns) is not None:
            sparkle_provides_version = True
            if LooseVersion(item.get("{%s}shortVersionString" % xmlns)) > LooseVersion(latest_version):
                latest_version = item.get("{%s}shortVersionString" % xmlns)
                latest_url = item.attrib["url"]
        if item.get("{%s}version" % xmlns) is not None:
            sparkle_provides_version = True
            if LooseVersion(item.get("{%s}version" % xmlns)) > LooseVersion(latest_version):
                latest_version = item.get("{%s}version" % xmlns)
                latest_url = item.attrib["url"]
    if sparkle_provides_version is True:
        robo_print("The Sparkle feed provides a version "
                   "number", LogLevel.VERBOSE, 4)
    else:
        robo_print("The Sparkle feed does not provide a version "
                   "number", LogLevel.VERBOSE, 4)
    facts["sparkle_provides_version"] = sparkle_provides_version
    if latest_version != "":
        robo_print("The latest version is %s" % latest_version, LogLevel.VERBOSE, 4)
    if latest_url != "":
        facts = inspect_download_url(latest_url, args, facts)

    # If Sparkle feed is hosted on GitHub or SourceForge, we can gather
    # more information.
    if "github.com" in input_path or "githubusercontent.com" in input_path:
        if "github_repo" not in facts:
            facts = inspect_github_url(input_path, args, facts)
    if "sourceforge.net" in input_path:
        if "sourceforge_id" not in facts:
            facts = inspect_sourceforge_url(input_path, args, facts)

    return facts
