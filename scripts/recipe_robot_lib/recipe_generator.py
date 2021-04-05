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


"""recipe_generator.py.

This module of Recipe Robot uses the facts collected by the main script
to create autopkg recipes for the specified app.
"""


# TODO: refactor code issuing warnings about missing processors/repos.
# pylint: disable=no-member

from __future__ import absolute_import

import os

from . import processor
from .exceptions import RoboError
from .tools import (
    SUPPORTED_ARCHIVE_FORMATS,
    SUPPORTED_BUNDLE_TYPES,
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_INSTALL_FORMATS,
    LogLevel,
    __version__,
    create_dest_dirs,
    create_existing_recipe_list,
    extract_app_icon,
    get_bundle_name_info,
    get_exitcode_stdout_stderr,
    recipe_dirpath,
    robo_join,
    robo_print,
    save_user_defaults,
    strip_dev_suffix,
    timed,
)


@timed
def generate_recipes(facts, prefs):
    """Generate the selected types of recipes.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.

    Raises:
        RoboError: Standard exception raised when Recipe Robot cannot proceed.
    """
    recipes = facts["recipes"]
    # A bundle name key like "app_name" or "prefpane_name" is required, because
    # it's strong evidence that we have enough facts to create a recipe set.
    bundle_type, bundle_name_key = get_bundle_name_info(facts)
    if bundle_name_key:
        if not facts["args"].ignore_existing:
            create_existing_recipe_list(facts)
    else:
        raise RoboError(
            "I wasn't able to gather enough information about "
            "this app to make recipes. If you saw any warnings "
            "above, they may contain more specific information."
        )

    preferred = [recipe for recipe in recipes if recipe["preferred"]]

    raise_if_recipes_cannot_be_generated(facts, preferred)

    # We have enough information to create a recipe set, but with assumptions.
    # TODO(Elliot): This code may not be necessary if inspections do their job.
    if "codesign_reqs" not in facts and "codesign_authorities" not in facts:
        facts["reminders"].append(
            "I can't tell whether this app is codesigned or not, so I'm "
            "going to assume it's not. You may want to verify that yourself "
            "and add the CodeSignatureVerifier processor if necessary."
        )
        facts["codesign_reqs"] = ""
        facts["codesign_authorities"] = []
    if "version_key" not in facts:
        facts["reminders"].append(
            "I can't tell whether to use CFBundleShortVersionString or "
            "CFBundleVersion for the version key of this app. Most apps use "
            "CFBundleShortVersionString, so that's what I'll use. You may "
            "want to verify that and modify the recipes if necessary."
        )
        facts["version_key"] = "CFBundleShortVersionString"

    # TODO(Elliot): Run `autopkg repo-list` once and store the resulting value
    # for future use when detecting missing required repos, rather than running
    # `autopkg repo-list` separately during each check. (For example, the
    # FileWaveImporter repo must be present to run created filewave recipes.)

    # Prepare the destination directory.
    recipe_dest_dir = recipe_dirpath(
        facts[bundle_name_key], facts.get("developer", None), prefs
    )
    facts["recipe_dest_dir"] = recipe_dest_dir
    create_dest_dirs(recipe_dest_dir)

    build_recipes(facts, preferred, prefs)

    # TODO (Shea): As far as I can tell, the only pref that changes is the
    # recipe created count. Move out from here!
    # Save preferences to disk for next time.
    save_user_defaults(prefs)


def raise_if_recipes_cannot_be_generated(facts, preferred):
    """Raise a RoboError if recipes cannot be generated.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        preferred ([str]): List of strings representing our preferred recipe
            types. If none are provided, we cannot produce recipes.

    Raises:
        RoboError: Standard exception raised when Recipe Robot cannot proceed.
    """
    # No recipe types are preferred.
    if not preferred:
        raise RoboError("Sorry, no recipes available to generate.")

    # We don't have enough information to create a recipe set.
    if not facts.is_from_app_store() and not any(
        [
            key in facts
            for key in ("sparkle_feed", "github_repo", "sourceforge_id", "download_url")
        ]
    ):
        raise RoboError(
            "Sorry, I don't know how to download this app. Maybe "
            "try another angle? The app's developer might have a direct "
            "download URL on their website, for example."
        )
    if not facts.is_from_app_store() and "download_format" not in facts:
        raise RoboError(
            "Sorry, I can't tell what format this app downloads in. It "
            "doesn't seem to be a dmg, zip, or pkg."
        )


def required_repo_reminder(repo_name, repo_url, facts):
    """Print a reminder if a required repo is not already added.

    Args:
        repo_name (str): Name of repo to issue reminder to add.
        repo_url (str): URL to the repo, to use with `autopkg repo-add`.
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
    """
    cmd = "/usr/local/bin/autopkg repo-list"
    exitcode, out, err = get_exitcode_stdout_stderr(cmd)
    if not any(
        (line.endswith("(%s)" % repo_url) or line.endswith("(%s.git)" % repo_url))
        for line in out.splitlines()
    ):
        facts["reminders"].append(
            "You'll need to add the %s repo in order to use "
            "this recipe:\n        autopkg repo-add "
            '"%s"' % (repo_name, repo_url)
        )


def build_recipes(facts, preferred, prefs):
    """Create a recipe for each preferred type we know about.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        preferred ([str]): List of strings representing our preferred recipe
            types. If none are provided, we cannot produce recipes.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
    """
    recipe_dest_dir = facts["recipe_dest_dir"]
    bundle_type, bundle_name_key = get_bundle_name_info(facts)
    for recipe in preferred:

        keys = recipe["keys"]

        keys["Input"]["NAME"] = facts[bundle_name_key]

        # Set the recipe filename (spaces are OK).
        recipe["filename"] = "%s.%s.recipe" % (facts[bundle_name_key], recipe["type"])

        # Set the recipe identifier.
        clean_name = facts[bundle_name_key].replace(" ", "").replace("+", "Plus")
        keys["Identifier"] = "%s.%s.%s" % (
            prefs["RecipeIdentifierPrefix"],
            recipe["type"],
            clean_name,
        )

        # If the name of the app bundle differs from the name of the app
        # itself, we need another input variable for that.
        if "app_file" in facts:
            keys["Input"]["APP_FILENAME"] = facts["app_file"]
            facts["app_name_key"] = "%APP_FILENAME%"
        else:
            facts["app_name_key"] = "%NAME%"

        # Set keys specific to download recipes.
        generation_func = get_generation_func(facts, prefs, recipe)
        if not generation_func:
            facts["warnings"].append(
                "Oops, I think my programmer messed up. I don't yet know how "
                "to generate a %s recipe. Sorry about that." % recipe["type"]
            )
        else:
            recipe = generation_func(facts, prefs, recipe)

        if recipe:
            if prefs.get("RecipeFormat") not in ("plist", None):
                dest_path = robo_join(
                    recipe_dest_dir, recipe["filename"] + "." + prefs["RecipeFormat"]
                )
            else:
                dest_path = robo_join(recipe_dest_dir, recipe["filename"])
            if not os.path.exists(dest_path):
                count = prefs.get("RecipeCreateCount", 0)
                prefs["RecipeCreateCount"] = count + 1

            recipe.write(dest_path, prefs.get("RecipeFormat"))
            robo_print(dest_path, LogLevel.LOG, 4)
            facts["recipes"].append(dest_path)


def get_generation_func(facts, prefs, recipe):
    """Return the correct generation function based on type.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
        recipe (Recipe): Object representing the recipe being generated.

    Returns:
        str: String representing the function that is used to generate this
            recipe type.
    """
    if recipe["type"] not in prefs["RecipeTypes"]:
        return None

    func_name = ["generate", recipe["type"].replace("-", "_"), "recipe"]

    if recipe["type"] in ("munki", "pkg") and facts.is_from_app_store():
        func_name.insert(1, "app_store")

    # TODO (Shea): This is a hack until I can use AbstractFactory for this.
    generation_func = globals()["_".join(func_name)]

    return generation_func


def generate_download_recipe(facts, prefs, recipe):
    """Generate a download recipe based on passed recipe dict.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
        recipe (Recipe): The recipe to operate on. This recipe will be mutated
            by this function.

    Returns:
        Recipe: Newly updated Recipe object suitable for converting to plist.
    """
    # TODO(Elliot): Handle signed or unsigned pkgs wrapped in dmgs or zips.
    keys = recipe["keys"]
    bundle_type, bundle_name_key = get_bundle_name_info(facts)

    if facts.is_from_app_store():
        warn_about_app_store_generation(facts, recipe["type"])
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    recipe.set_description(
        "Downloads the latest version of %s." % facts[bundle_name_key]
    )

    # TODO (Shea): Extract method(s) to get_source_processor()
    if "sparkle_feed" in facts:
        sparkle_processor = processor.SparkleUpdateInfoProvider(
            appcast_url=facts["sparkle_feed"]
        )

        if "user-agent" in facts:
            sparkle_processor.appcast_request_headers = {
                "user-agent": facts["user-agent"]
            }

        recipe.append_processor(sparkle_processor)

    # TODO (Shea): Extract method(s) to get_source_processor()
    elif "github_repo" in facts:
        if facts.get("use_asset_regex", False):
            gh_release_info_provider = processor.GitHubReleasesInfoProvider(
                asset_regex=".*\\.%s$" % facts["download_format"],
                github_repo=facts["github_repo"],
            )
        else:
            gh_release_info_provider = processor.GitHubReleasesInfoProvider(
                github_repo=facts["github_repo"]
            )
        recipe.append_processor(gh_release_info_provider)

    # TODO (Shea): Extract method(s) to get_source_processor()
    elif "sourceforge_id" in facts:
        SourceForgeURLProvider = processor.ProcessorFactory(
            "com.github.jessepeterson.munki.GrandPerspective/SourceForgeURLProvider",
            ("SOURCEFORGE_FILE_PATTERN", "SOURCEFORGE_PROJECT_ID"),
        )
        sf_url_provider = SourceForgeURLProvider(
            SOURCEFORGE_FILE_PATTERN="\\.%s\\/download$" % facts["download_format"],
            SOURCEFORGE_PROJECT_ID=facts["sourceforge_id"],
        )
        recipe.append_processor(sf_url_provider)
        if not os.path.exists(
            os.path.expanduser(
                "~/Library/AutoPkg/RecipeRepos/com.github.autopkg."
                "jessepeterson-recipes/GrandPerspective/"
                "SourceForgeURLProvider.py"
            )
        ):
            facts["reminders"].append(
                "The download recipe I created uses the "
                "SourceForgeURLProvider processor, which is not in the "
                "AutoPkg core. You'll need to add the appropriate repository "
                "before running the recipe:\n"
                "        autopkg repo-add jessepeterson-recipes"
            )

    url_downloader = processor.URLDownloader()

    if "download_url" in facts:
        if facts.get("sparkle_provides_version") or "github_repo" in facts:
            # Sparkle and GitHub provide version information.
            url_downloader.filename = "%NAME%-%version%.{}".format(
                facts["download_format"]
            )
        elif "sourceforge_id" in facts:
            # SourceForge does not provide reliable version information, but signed apps
            # are generally handled with a Versioner or AppDmgVersioner processor.
            url_downloader.filename = "%NAME%.{}".format(facts["download_format"])
            if not facts.get("codesign_reqs") and not facts.get("codesign_authorities"):
                # If no signing, chances are low that we have version information.
                if facts["download_format"] in SUPPORTED_ARCHIVE_FORMATS:
                    facts["warnings"].append(
                        "I couldn't a reliable source of version information. You may need to "
                        "manually add Unarchiver and Versioner processors "
                        "to your download recipe."
                    )
                if facts["download_format"] in SUPPORTED_IMAGE_FORMATS:
                    facts["warnings"].append(
                        "I couldn't a reliable source of version information. You may need to "
                        "manually add a Versioner or AppDmgVersioner processor "
                        "to your download recipe."
                    )
                if facts["download_format"] in SUPPORTED_INSTALL_FORMATS:
                    facts["warnings"].append(
                        "I couldn't a reliable source of version information. You may need to "
                        "manually add FlatPkgUnpacker and Versioner processors "
                        "to your download recipe."
                    )
        else:
            url_downloader.url = facts["download_url"]
            url_downloader.filename = "%NAME%.{}".format(facts["download_format"])

    if "user-agent" in facts:
        url_downloader.request_headers = {"user-agent": facts["user-agent"]}

    recipe.append_processor(url_downloader)

    end_of_check_phase = processor.EndOfCheckPhase()
    recipe.append_processor(end_of_check_phase)

    # TODO (Shea): Refactor to get_codesigning and get_unarchiver funcs.
    if facts.get("codesign_reqs") or facts.get("codesign_authorities"):

        if facts["download_format"] in SUPPORTED_ARCHIVE_FORMATS:
            unarchiver = processor.Unarchiver()
            unarchiver.archive_path = "%pathname%"
            unarchiver.destination_path = "%RECIPE_CACHE_DIR%/%NAME%"
            unarchiver.purge_destination = True
            recipe.append_processor(unarchiver)

        if facts["download_format"] in SUPPORTED_IMAGE_FORMATS:
            # We're assuming that the app is at the root level of the dmg.
            input_path = "%pathname%/{}{}".format(
                facts.get("relative_path", ""), facts["codesign_input_filename"]
            )
        elif facts["download_format"] in SUPPORTED_ARCHIVE_FORMATS:
            input_path = "%RECIPE_CACHE_DIR%/%NAME%/{}{}".format(
                facts.get("relative_path", ""), facts["codesign_input_filename"]
            )
        elif facts["download_format"] in SUPPORTED_INSTALL_FORMATS:
            # The download is in pkg format, and the pkg is signed.
            # TODO(Elliot): Need a few test cases to prove this works.
            input_path = "%pathname%"
        else:
            facts["warnings"].append(
                "CodeSignatureVerifier cannot be created. "
                "The download format is not recognized."
            )
            input_path = None

        if input_path:
            codesigverifier = get_code_signature_verifier(input_path, facts)
            recipe.append_processor(codesigverifier)

        # TODO (Shea): Extract method -> get_versioner
        if needs_versioner(facts):
            versioner = processor.Versioner()
            if (
                facts.get("codesign_input_filename", "").endswith(".pkg")
                or "pkg" in facts["inspections"]
            ):
                facts["warnings"].append(
                    "To add a Versioner processor with a pkg as input requires quite "
                    "a bit of customization. I'm going to take my best shot, but I "
                    "might be wrong."
                )

                flatpkgunpacker = processor.FlatPkgUnpacker()
                flatpkgunpacker.destination_path = "%RECIPE_CACHE_DIR%/unpack"
                flatpkgunpacker.flat_pkg_path = input_path
                flatpkgunpacker.purge_destination = True
                recipe.append_processor(flatpkgunpacker)

                pkgpayloadunpacker = processor.PkgPayloadUnpacker()
                pkgpayloadunpacker.destination_path = "%RECIPE_CACHE_DIR%/payload"
                pkgpayloadunpacker.purge_destination = True

                if not "pkg_filename" in facts:
                    # Use FileFinder to search for the package if the name is unknown.
                    filefinder = processor.FileFinder()
                    filefinder.pattern = "%RECIPE_CACHE_DIR%/unpack/*.pkg/Payload"
                    filefinder.find_method = "glob"
                    recipe.append_processor(filefinder)
                    pkgpayloadunpacker.pkg_payload_path = "%found_filename%"
                else:
                    # Skip FileFinder and specify the filename of the package.
                    pkgpayloadunpacker.pkg_payload_path = "%RECIPE_CACHE_DIR%/unpack/{}/Payload".format(
                        facts["pkg_filename"]
                    )

                recipe.append_processor(pkgpayloadunpacker)

                versioner.input_plist_path = "%RECIPE_CACHE_DIR%/payload/{}/Contents/Info.plist".format(
                    facts["app_relpath_from_payload"]
                )
            else:
                if facts["download_format"] in SUPPORTED_IMAGE_FORMATS:
                    versioner.input_plist_path = "%pathname%/{}{}.{}/Contents/Info.plist".format(
                        facts.get("relative_path", ""),
                        facts.get("app_file", facts[bundle_name_key]),
                        bundle_type,
                    )
                else:
                    versioner.input_plist_path = (
                        "%RECIPE_CACHE_DIR%/%NAME%/"
                        "{}{}.{}/Contents/Info.plist".format(
                            facts.get("relative_path", ""),
                            facts.get("app_file", facts[bundle_name_key]),
                            bundle_type,
                        )
                    )
            versioner.plist_version_key = facts["version_key"]
            recipe.append_processor(versioner)

    return recipe


def warn_about_app_store_generation(facts, recipe_type):
    """Issue warning if we can't make this recipe due to it being from the Mac
    App Store.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        recipe_type (str): String representing the type of this recipe.
    """
    facts["warnings"].append(
        "Skipping %s recipe, because this app was downloaded from the "
        "App Store." % recipe_type
    )


def get_code_signature_verifier(input_path, facts):
    """Build a CodeSignatureVerifier processor.

    Args:
        input_path (str): Path to signed code.
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.

    Returns:
        CodeSignatureVerifier: An object representing the CodeSignatureVerifier
            processor.
    """
    """

    Args:
        input_path (str): Path to signed code.
        facts (Facts): Shared facts object.

    Returns:
        CodeSignatureVerifier
    """
    codesigverifier = processor.CodeSignatureVerifier()
    codesigverifier.input_path = input_path
    if facts.get("codesign_reqs"):
        codesigverifier.requirement = facts["codesign_reqs"]
    elif len(facts["codesign_authorities"]) > 0:
        codesigverifier.expected_authority_names = list(facts["codesign_authorities"])
    return codesigverifier


def needs_versioner(facts):
    """Determine whether we need to add a Versioner processor, based on available
    facts.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.

    Returns:
        bool: True if a Versioner processor is needed, False otherwise.
    """

    download_format = facts["download_format"]
    sparkle_version = facts.get("sparkle_provides_version", False)
    format_needs_versioner = any(
        download_format in formats
        for formats in (SUPPORTED_IMAGE_FORMATS, SUPPORTED_ARCHIVE_FORMATS)
    )
    return format_needs_versioner and not sparkle_version


def generate_app_store_munki_recipe(facts, prefs, recipe):
    """Generate an munki recipe for an App Store app on passed recipe dict.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
        recipe (Recipe): The recipe to operate on. This recipe will be mutated
            by this function.

    Returns:
        Recipe: Newly updated Recipe object suitable for converting to plist.
    """
    keys = recipe["keys"]
    robo_print("Generating %s recipe..." % recipe["type"])

    recipe.set_description(
        "Downloads the latest version of %s from the Mac "
        "App Store and imports it into Munki." % facts["app_name"]
    )

    recipe.set_parent("com.github.nmcspadden.munki.appstore")

    keys["Input"]["PATH"] = facts["app_path"]
    recipe["filename"] = "MAS-" + recipe["filename"]

    keys["Input"]["MUNKI_REPO_SUBDIR"] = "apps/%NAME%"
    keys["Input"]["pkginfo"] = {
        "catalogs": ["testing"],
        "developer": facts.get("developer", ""),
        "display_name": facts["app_name"],
        "name": "%NAME%",
        "unattended_install": True,
    }

    if "description" in facts:
        keys["Input"]["pkginfo"]["description"] = facts["description"]
    else:
        facts["reminders"].append(
            "I couldn't find a description for this app, so you'll need to "
            "manually add one to the munki recipe."
        )
        keys["Input"]["pkginfo"]["description"] = " "

    return recipe


def generate_munki_recipe(facts, prefs, recipe):
    """Generate a munki recipe for a non-App Store app on passed recipe dict.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
        recipe (Recipe): The recipe to operate on. This recipe will be mutated
            by this function.

    Returns:
        Recipe: Newly updated Recipe object suitable for converting to plist.
    """
    keys = recipe["keys"]
    bundle_type, bundle_name_key = get_bundle_name_info(facts)
    robo_print("Generating %s recipe..." % recipe["type"])

    recipe.set_description(
        "Downloads the latest version of %s and imports it "
        "into Munki." % facts[bundle_name_key]
    )
    recipe.set_parent_from(prefs, facts, "download")

    keys["Input"]["MUNKI_REPO_SUBDIR"] = "apps/%NAME%"
    keys["Input"]["pkginfo"] = {
        "catalogs": ["testing"],
        "display_name": facts[bundle_name_key],
        "name": "%NAME%",
        "unattended_install": True,
    }

    if "description" in facts:
        keys["Input"]["pkginfo"]["description"] = facts["description"]
    else:
        facts["reminders"].append(
            "I couldn't find a description for this app, so you'll need to "
            "manually add one to the munki recipe."
        )
        keys["Input"]["pkginfo"]["description"] = " "

    if prefs.get("StripDeveloperSuffixes", False) is True:
        keys["Input"]["pkginfo"]["developer"] = strip_dev_suffix(
            facts.get("developer", "")
        )
    else:
        keys["Input"]["pkginfo"]["developer"] = facts.get("developer", "")

    # Set default variable to use for substitution.
    import_file_var = "%pathname%"

    # Create empty container for additional makepkginfo options.
    addl_makepkginfo_opts = []

    if facts["download_format"] in SUPPORTED_IMAGE_FORMATS:
        # If the app is not signed, we need a versioner processor here.
        if (
            facts.get("codesign_reqs", "") == ""
            and len(facts["codesign_authorities"]) == 0
        ):
            if (
                facts["version_key"] == "CFBundleShortVersionString"
                and bundle_type == "app"
            ):
                recipe.append_processor(
                    {
                        "Processor": "AppDmgVersioner",
                        "Arguments": {"dmg_path": "%pathname%"},
                    }
                )
            else:
                versioner = {
                    "Processor": "Versioner",
                    "Arguments": {
                        "input_plist_path": (
                            "%pathname%/{}{}.{}/Contents/Info.plist".format(
                                facts.get("relative_path", ""),
                                facts.get("app_file", facts[bundle_name_key]),
                                bundle_type,
                            )
                        )
                    },
                }
                if facts["version_key"] != "CFBundleShortVersionString":
                    versioner["Arguments"]["plist_version_key"] = facts["version_key"]
                recipe.append_processor(versioner)
        if bundle_type != "app":
            # Add --itemname option.
            itemname = "{}{}.{}".format(
                facts.get("relative_path", ""),
                facts.get("app_file", facts[bundle_name_key]),
                bundle_type,
            )
            addl_makepkginfo_opts.append("--itemname")
            addl_makepkginfo_opts.append(itemname)

            # Add --destinationpath option.
            destinationpath = SUPPORTED_BUNDLE_TYPES[bundle_type]
            addl_makepkginfo_opts.append("--destinationpath")
            addl_makepkginfo_opts.append(destinationpath)

    elif facts["download_format"] in SUPPORTED_ARCHIVE_FORMATS:
        if (
            facts.get("codesign_reqs", "") == ""
            and len(facts["codesign_authorities"]) == 0
        ):
            # If unsigned, that means the download recipe hasn't
            # unarchived the zip yet.
            recipe.append_processor(
                {
                    "Processor": "Unarchiver",
                    "Arguments": {
                        "archive_path": "%pathname%",
                        "destination_path": "%RECIPE_CACHE_DIR%/%NAME%",
                        "purge_destination": True,
                    },
                }
            )
        recipe.append_processor(
            {
                "Processor": "DmgCreator",
                "Arguments": {
                    "dmg_path": "%RECIPE_CACHE_DIR%/%NAME%.dmg",
                    "dmg_root": "%RECIPE_CACHE_DIR%/%NAME%",
                },
            }
        )
        import_file_var = "%dmg_path%"
        if bundle_type != "app":
            # Add --itemname option.
            itemname = "{}{}.{}".format(
                facts.get("relative_path", ""),
                facts.get("app_file", facts[bundle_name_key]),
                bundle_type,
            )
            addl_makepkginfo_opts.append("--itemname")
            addl_makepkginfo_opts.append(itemname)

            # Add --destinationpath option.
            destinationpath = SUPPORTED_BUNDLE_TYPES[bundle_type]
            addl_makepkginfo_opts.append("--destinationpath")
            addl_makepkginfo_opts.append(destinationpath)

    # Set blocking applications, if we found any.
    if len(facts["blocking_applications"]) > 0 and "pkg" in facts["inspections"]:
        keys["Input"]["pkginfo"]["blocking_applications"] = list(
            set(facts["blocking_applications"])
        )

    if bundle_type != "app":
        recipe.append_processor(
            {
                "Processor": "MunkiInstallsItemsCreator",
                "Arguments": {
                    "installs_item_paths": [
                        "{}/{}.{}".format(
                            SUPPORTED_BUNDLE_TYPES[bundle_type],
                            facts.get("app_file", facts[bundle_name_key]),
                            bundle_type,
                        )
                    ]
                },
            }
        )

    if facts["version_key"] != "CFBundleShortVersionString":
        recipe.append_processor(
            {
                "Processor": "MunkiPkginfoMerger",
                "Arguments": {"additional_pkginfo": {"version": "%version%"}},
            }
        )
        munki_importer = {
            "Processor": "MunkiImporter",
            "Arguments": {
                "pkg_path": import_file_var,
                "repo_subdirectory": "%MUNKI_REPO_SUBDIR%",
                "version_comparison_key": facts["version_key"],
            },
        }
    else:
        munki_importer = {
            "Processor": "MunkiImporter",
            "Arguments": {
                "pkg_path": import_file_var,
                "repo_subdirectory": "%MUNKI_REPO_SUBDIR%",
            },
        }

    if addl_makepkginfo_opts:
        munki_importer["Arguments"][
            "additional_makepkginfo_options"
        ] = addl_makepkginfo_opts

    recipe.append_processor(munki_importer)

    # Extract the app's icon and save it to disk.
    if "icon_path" in facts:
        extracted_icon = robo_join(
            recipe_dirpath(facts[bundle_name_key], facts.get("developer", None), prefs),
            facts[bundle_name_key] + ".png",
        )
        extract_app_icon(facts, extracted_icon)
    else:
        facts["warnings"].append(
            "I don't have enough information to create a PNG icon for this app."
        )

    return recipe


def get_pkgdirs(path):
    """Given a destination path, create the dictionary used for
    PkgRootCreator.

    Args:
        path (str): Path to the package installer destination.

    Returns:
        dict: Dictionary of subdirectory paths and file modes used by PkgRootCreator.
    """
    path_parts = os.path.split(path.lstrip("/"))
    pkgdirs = {}
    for index, dir in enumerate(path_parts):
        pkgdirs["/".join(path_parts[: index + 1])] = "0775"
    return pkgdirs


def generate_app_store_pkg_recipe(facts, prefs, recipe):
    """Generate a pkg recipe for an App Store app on passed recipe dict.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
        recipe (Recipe): The recipe to operate on. This recipe will be mutated
            by this function.

    Returns:
        Recipe: Newly updated Recipe object suitable for converting to plist.
    """
    keys = recipe["keys"]
    robo_print("Generating %s recipe..." % recipe["type"])

    recipe.set_description(
        "Downloads the latest version of %s from the Mac "
        "App Store and creates a package." % facts["app_name"]
    )

    recipe.set_parent("com.github.nmcspadden.pkg.appstore")

    keys["Input"]["PATH"] = facts["app_path"]
    recipe["filename"] = "MAS-" + recipe["filename"]

    warn_about_appstoreapp_pyasn(facts)
    return recipe


def generate_pkg_recipe(facts, prefs, recipe):
    """Generate a pkg recipe for a non-App Store app based on passed recipe dict.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
        recipe (Recipe): The recipe to operate on. This recipe will be mutated
            by this function.

    Returns:
        Recipe: Newly updated Recipe object suitable for converting to plist.
    """
    keys = recipe["keys"]
    bundle_type, bundle_name_key = get_bundle_name_info(facts)
    # Can't make this recipe without a bundle identifier.
    # TODO(Elliot): Bundle id is also provided by AppDmgVersioner and some
    # Sparkle feeds. When those are present, can we proceed even though we
    # don't have bundle_id in facts? (#40)
    if "bundle_id" not in facts:
        facts["warnings"].append(
            "Skipping %s recipe, because I wasn't able to determine the "
            "bundle identifier of this app. You may want to actually download "
            "the app and try again, using the .app file itself as input."
            % recipe["type"]
        )
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    recipe.set_description(
        "Downloads the latest version of %s and creates a package."
        % facts[bundle_name_key]
    )

    recipe.set_parent_from(prefs, facts, "download")

    # TODO: Try to make AppPkgCreator work with exclamation points in app names. Example:
    # 'https://s3.amazonaws.com/shirtpocket/SuperDuper/SuperDuper!.dmg'
    if facts["download_format"] in SUPPORTED_IMAGE_FORMATS:
        # TODO: if "pkg" in facts["inspections"] then use PkgCopier.
        if bundle_type == "app":
            if "relative_path" in facts:
                recipe.append_processor(
                    {
                        "Processor": "AppPkgCreator",
                        "Arguments": {
                            "app_path": "%pathname%/{}{}.{}".format(
                                facts.get("relative_path", ""),
                                facts.get("app_file", facts[bundle_name_key]),
                                bundle_type,
                            )
                        },
                    }
                )
            else:
                recipe.append_processor({"Processor": "AppPkgCreator"})
        else:
            # TODO: Create postinstall script for running `qlmanage -r`
            # if bundle_type is qlgenerator.
            recipe.append_processor(
                {
                    "Processor": "PkgRootCreator",
                    "Arguments": {
                        "pkgdirs": get_pkgdirs(SUPPORTED_BUNDLE_TYPES[bundle_type]),
                        "pkgroot": "%RECIPE_CACHE_DIR%/pkgroot",
                    },
                }
            )
            recipe.append_processor(
                {
                    "Processor": "Copier",
                    "Arguments": {
                        "destination_path": "%pkgroot%/{}/{}.{}".format(
                            SUPPORTED_BUNDLE_TYPES[bundle_type].lstrip("/"),
                            facts.get("app_file", facts[bundle_name_key]),
                            bundle_type,
                        ),
                        "source_path": "%pathname%/{}{}.{}".format(
                            facts.get("relative_path", ""),
                            facts.get("app_file", facts[bundle_name_key]),
                            bundle_type,
                        ),
                    },
                }
            )
            recipe.append_processor(
                {
                    "Processor": "PkgCreator",
                    "Arguments": {
                        "pkg_request": {
                            "chown": [
                                {
                                    "group": "admin",
                                    "path": SUPPORTED_BUNDLE_TYPES[bundle_type].lstrip(
                                        "/"
                                    ),
                                    "user": "root",
                                }
                            ],
                            "id": facts["bundle_id"],
                            "options": "purge_ds_store",
                            "pkgname": "%NAME%-%version%",
                            "pkgroot": "%pkgroot%",
                            "version": "%version%",
                        }
                    },
                }
            )

    elif facts["download_format"] in SUPPORTED_ARCHIVE_FORMATS:
        if (
            facts.get("codesign_reqs", "") == ""
            and len(facts["codesign_authorities"]) == 0
        ):
            # If unsigned, that means the download recipe hasn't
            # unarchived the zip yet. Need to do that and version.
            recipe.append_processor(
                {
                    "Processor": "Unarchiver",
                    "Arguments": {
                        "archive_path": "%pathname%",
                        "destination_path": "%RECIPE_CACHE_DIR%/%NAME%",
                        "purge_destination": True,
                    },
                }
            )
        # TODO: if "pkg" in facts["inspections"] then use PkgCopier.
        if bundle_type == "app":
            recipe.append_processor(
                {
                    "Processor": "AppPkgCreator",
                    "Arguments": {
                        "app_path": "%RECIPE_CACHE_DIR%/%NAME%/{}{}.{}".format(
                            facts.get("relative_path", ""),
                            facts.get("app_file", facts[bundle_name_key]),
                            bundle_type,
                        )
                    },
                }
            )
        else:
            # TODO: Create postinstall script for running `qlmanage -r`
            # if bundle_type is qlgenerator.
            recipe.append_processor(
                {
                    "Processor": "PkgRootCreator",
                    "Arguments": {
                        "pkgdirs": get_pkgdirs(SUPPORTED_BUNDLE_TYPES[bundle_type]),
                        "pkgroot": "%RECIPE_CACHE_DIR%/pkgroot",
                    },
                }
            )
            recipe.append_processor(
                {
                    "Processor": "Copier",
                    "Arguments": {
                        "destination_path": "%pkgroot%/{}/{}.{}".format(
                            SUPPORTED_BUNDLE_TYPES[bundle_type].lstrip("/"),
                            facts.get("app_file", facts[bundle_name_key]),
                            bundle_type,
                        ),
                        "source_path": "%RECIPE_CACHE_DIR%/%NAME%/{}{}.{}".format(
                            facts.get("relative_path", ""),
                            facts.get("app_file", facts[bundle_name_key]),
                            bundle_type,
                        ),
                    },
                }
            )
            recipe.append_processor(
                {
                    "Processor": "PkgCreator",
                    "Arguments": {
                        "pkg_request": {
                            "chown": [
                                {
                                    "group": "admin",
                                    "path": SUPPORTED_BUNDLE_TYPES[bundle_type].lstrip(
                                        "/"
                                    ),
                                    "user": "root",
                                }
                            ],
                            "id": facts["bundle_id"],
                            "options": "purge_ds_store",
                            "pkgname": "%NAME%-%version%",
                            "pkgroot": "%pkgroot%",
                            "version": "%version%",
                        }
                    },
                }
            )

    elif facts["download_format"] in SUPPORTED_INSTALL_FORMATS:
        facts["warnings"].append(
            "Skipping pkg recipe, since the download format is already pkg."
        )
        return

    return recipe


def generate_install_recipe(facts, prefs, recipe):
    """Generate an install recipe based on passed recipe dict.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
        recipe (Recipe): The recipe to operate on. This recipe will be mutated
            by this function.

    Returns:
        Recipe: Newly updated Recipe object suitable for converting to plist.
    """
    keys = recipe["keys"]
    bundle_type, bundle_name_key = get_bundle_name_info(facts)
    if facts.is_from_app_store():
        warn_about_app_store_generation(facts, recipe["type"])
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    recipe.set_description(
        "Installs the latest version of %s." % facts[bundle_name_key]
    )

    recipe.set_parent_from(prefs, facts, "download")

    if facts["download_format"] in SUPPORTED_IMAGE_FORMATS:
        recipe.append_processor(
            {
                "Processor": "InstallFromDMG",
                "Arguments": {
                    "dmg_path": "%pathname%",
                    "items_to_copy": [
                        {
                            "source_item": "{}{}.{}".format(
                                facts.get("relative_path", ""),
                                facts.get("app_file", facts[bundle_name_key]),
                                bundle_type,
                            ),
                            "destination_path": SUPPORTED_BUNDLE_TYPES[bundle_type],
                        }
                    ],
                },
            }
        )

    elif facts["download_format"] in SUPPORTED_ARCHIVE_FORMATS:
        if (
            facts.get("codesign_reqs", "") == ""
            and len(facts["codesign_authorities"]) == 0
        ):
            recipe.append_processor(
                {
                    "Processor": "Unarchiver",
                    "Arguments": {
                        "archive_path": "%pathname%",
                        "destination_path": "%RECIPE_CACHE_DIR%/%NAME%",
                        "purge_destination": True,
                    },
                }
            )
        recipe.append_processor(
            {
                "Processor": "DmgCreator",
                "Arguments": {
                    "dmg_root": "%RECIPE_CACHE_DIR%/%NAME%",
                    "dmg_path": "%RECIPE_CACHE_DIR%/%NAME%.dmg",
                },
            }
        )
        recipe.append_processor(
            {
                "Processor": "InstallFromDMG",
                "Arguments": {
                    "dmg_path": "%dmg_path%",
                    "items_to_copy": [
                        {
                            "source_item": "{}{}.{}".format(
                                facts.get("relative_path", ""),
                                facts.get("app_file", facts[bundle_name_key]),
                                bundle_type,
                            ),
                            "destination_path": SUPPORTED_BUNDLE_TYPES[bundle_type],
                        }
                    ],
                },
            }
        )

    elif facts["download_format"] in SUPPORTED_INSTALL_FORMATS:
        recipe.append_processor(
            {"Processor": "Installer", "Arguments": {"pkg_path": "%pathname%"}}
        )

    return recipe


def generate_jss_recipe(facts, prefs, recipe):
    """Generate a jss recipe based on passed recipe dict.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
        recipe (Recipe): The recipe to operate on. This recipe will be mutated
            by this function.

    Returns:
        Recipe: Newly updated Recipe object suitable for converting to plist.
    """
    keys = recipe["keys"]
    bundle_type, bundle_name_key = get_bundle_name_info(facts)
    # Can't make this recipe without a bundle identifier.
    if "bundle_id" not in facts:
        facts["warnings"].append(
            "Skipping %s recipe, because I wasn't able to determine the "
            "bundle identifier of this app. You may want to actually download "
            "the app and try again, using the .app file itself as input."
            % recipe["type"]
        )
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    if prefs.get("FollowOfficialJSSRecipesFormat", False) is True:
        clean_name = facts[bundle_name_key].replace(" ", "").replace("+", "Plus")
        keys["Identifier"] = "com.github.jss-recipes.jss.%s" % clean_name

    recipe.set_description(
        "Downloads the latest version of %s and imports it "
        "into your JSS." % facts[bundle_name_key]
    )

    recipe.set_parent_from(prefs, facts, "pkg")

    keys["Input"]["CATEGORY"] = "Productivity"
    facts["reminders"].append(
        "Remember to manually set the category in the jss recipe. I've set "
        'it to "Productivity" by default.'
    )

    keys["Input"]["POLICY_CATEGORY"] = "Testing"
    keys["Input"]["POLICY_TEMPLATE"] = "PolicyTemplate.xml"
    keys["Input"]["SELF_SERVICE_ICON"] = "%NAME%.png"
    if not os.path.exists(
        robo_join(prefs["RecipeCreateLocation"], "%s.png" % facts[bundle_name_key])
    ):
        facts["reminders"].append(
            "Make sure to keep %s.png with the jss recipe so JSSImporter can "
            "use it." % facts[bundle_name_key]
        )
    keys["Input"]["SELF_SERVICE_DESCRIPTION"] = facts.get("description", "")
    keys["Input"]["GROUP_NAME"] = "%NAME%-update-smart"

    jssimporter_arguments = {
        "prod_name": "%NAME%",
        "category": "%CATEGORY%",
        "policy_category": "%POLICY_CATEGORY%",
        "policy_template": "%POLICY_TEMPLATE%",
        "self_service_icon": "%SELF_SERVICE_ICON%",
        "self_service_description": "%SELF_SERVICE_DESCRIPTION%",
        "groups": [
            {"name": "%GROUP_NAME%", "smart": True, "template_path": "%GROUP_TEMPLATE%"}
        ],
    }

    # Set variables and arguments as necessary depending on version key.
    if facts["version_key"] == "CFBundleVersion":
        keys["Input"]["GROUP_TEMPLATE"] = "CFBundleVersionSmartGroupTemplate.xml"
        jssimporter_arguments["extension_attributes"] = [
            {"ext_attribute_path": "CFBundleVersionExtensionAttribute.xml"}
        ]
    else:
        keys["Input"]["GROUP_TEMPLATE"] = "SmartGroupTemplate.xml"

    # If the app's name differs from its filename, set jss_inventory_name.
    if "app_file" in facts:
        jssimporter_arguments["jss_inventory_name"] = facts["app_file"]

    if bundle_type != "app":
        facts["reminders"].append(
            "Because this item is not an app, you'll need to manually create an "
            "extension attribute XML template to use with this JSS recipe."
        )

    # Extract the app's icon and save it to disk.
    if "icon_path" in facts:
        extracted_icon = robo_join(
            recipe_dirpath(facts[bundle_name_key], facts.get("developer", None), prefs),
            facts[bundle_name_key] + ".png",
        )
        extract_app_icon(facts, extracted_icon)
    else:
        facts["warnings"].append(
            "I don't have enough information to create a PNG icon for this app."
        )

    # Put fully constructed JSSImporter arguments into the process list.
    recipe.append_processor(
        {"Processor": "JSSImporter", "Arguments": jssimporter_arguments}
    )

    return recipe


def generate_jss_upload_recipe(facts, prefs, recipe):
    """Generate an upload-only jss recipe based on passed recipe dict.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
        recipe (Recipe): The recipe to operate on. This recipe will be mutated
            by this function.

    Returns:
        Recipe: Newly updated Recipe object suitable for converting to plist.
    """
    # TODO: Possibly combine with generate_jss_upload_recipe() to handle multiple
    # "varietals" of the same recipe type?
    keys = recipe["keys"]
    _, bundle_name_key = get_bundle_name_info(facts)
    # Can't make this recipe without a bundle identifier.
    if "bundle_id" not in facts:
        facts["warnings"].append(
            "Skipping %s recipe, because I wasn't able to determine the "
            "bundle identifier of this app. You may want to actually download "
            "the app and try again, using the .app file itself as input."
            % recipe["type"]
        )
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    if prefs.get("FollowOfficialJSSRecipesFormat", False) is True:
        clean_name = facts[bundle_name_key].replace(" ", "").replace("+", "Plus")
        keys["Identifier"] = "com.github.jss-recipes.jss-upload.%s" % clean_name

    recipe.set_description(
        "Downloads the latest version of %s and uploads the package "
        "to your JSS." % facts[bundle_name_key]
    )

    recipe.set_parent_from(prefs, facts, "pkg")

    keys["Input"]["CATEGORY"] = "Productivity"
    facts["reminders"].append(
        "Remember to manually set the category in the jss-upload recipe. I've set "
        'it to "Productivity" by default.'
    )

    jssimporter_arguments = {"prod_name": "%NAME%", "category": "%CATEGORY%"}

    # Put fully constructed JSSImporter arguments into the process list.
    recipe.append_processor(
        {"Processor": "JSSImporter", "Arguments": jssimporter_arguments}
    )

    return recipe


def generate_lanrev_recipe(facts, prefs, recipe):
    """Generate a lanrev recipe based on passed recipe dict.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
        recipe (Recipe): The recipe to operate on. This recipe will be mutated
            by this function.

    Returns:
        Recipe: Newly updated Recipe object suitable for converting to plist.
    """
    keys = recipe["keys"]
    bundle_type, bundle_name_key = get_bundle_name_info(facts)
    # TODO: Until we get it working.
    if facts.is_from_app_store():
        warn_about_app_store_generation(facts, recipe["type"])
        return
    # Can't make this recipe without a bundle identifier.
    if "bundle_id" not in facts:
        facts["warnings"].append(
            "Skipping %s recipe, because I wasn't able to determine the "
            "bundle identifier of this app. You may want to actually download "
            "the app and try again, using the .app file itself as input."
            % recipe["type"]
        )
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    recipe.set_description(
        "Downloads the latest version of %s and copies it "
        "into your LANrev Server." % facts[bundle_name_key]
    )

    recipe.set_parent_from(prefs, facts, "pkg")

    # Print a reminder if the required repo isn't present on disk.
    required_repo_reminder(
        "LANrevImporter", "https://github.com/jbaker10/LANrevImporter", facts
    )

    recipe.append_processor(
        {
            "Processor": "com.github.jbaker10.LANrevImporter/LANrevImporter",
            "SharedProcessorRepoURL": lanrevimporter_url,
            "Arguments": {
                "dest_payload_path": "%RECIPE_CACHE_DIR%/%NAME%-%version%.amsdpackages",
                "sdpackages_ampkgprops_path": "%RECIPE_DIR%/%NAME%-Defaults.ampkgprops",
                "source_payload_path": "%pkg_path%",
                "import_pkg_to_servercenter": True,
            },
        }
    )

    return recipe


def generate_sccm_recipe(facts, prefs, recipe):
    """Generate a sccm (Microsoft Endpoint Configuration Manager) recipe
    based on passed recipe dict.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
        recipe (Recipe): The recipe to operate on. This recipe will be mutated
            by this function.

    Returns:
        Recipe: Newly updated Recipe object suitable for converting to plist.
    """
    keys = recipe["keys"]
    bundle_type, bundle_name_key = get_bundle_name_info(facts)
    # TODO: Until we get it working.
    if facts.is_from_app_store():
        warn_about_app_store_generation(facts, recipe["type"])
        return
    # Can't make this recipe without a bundle identifier.
    if "bundle_id" not in facts:
        facts["warnings"].append(
            "Skipping %s recipe, because I wasn't able to determine the "
            "bundle identifier of this app. You may want to actually download "
            "the app and try again, using the .app file itself as input."
            % recipe["type"]
        )
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    recipe.set_description(
        "Downloads the latest version of %s and copies it "
        "into your SCCM Server." % facts[bundle_name_key]
    )
    recipe.set_parent_from(prefs, facts, "pkg")

    # Print a reminder if the required repo isn't present on disk.
    required_repo_reminder(
        "cgerke-recipes", "https://github.com/autopkg/cgerke-recipes", facts
    )

    recipe.append_processor(
        {
            "Processor": "com.github.autopkg.cgerke-recipes.SharedProcessors/CmmacCreator",
            "SharedProcessorRepoURL": cgerke_url,
            "Arguments": {
                "source_file": "%pkg_path%",
                "destination_directory": "%RECIPE_CACHE_DIR%",
            },
        }
    )

    return recipe


def generate_filewave_recipe(facts, prefs, recipe):
    """Generate a filewave recipe based on passed recipe dict.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
        recipe (Recipe): The recipe to operate on. This recipe will be mutated
            by this function.

    Returns:
        Recipe: Newly updated Recipe object suitable for converting to plist.
    """
    keys = recipe["keys"]
    bundle_type, bundle_name_key = get_bundle_name_info(facts)
    # TODO: Until we get it working.
    if facts.is_from_app_store():
        warn_about_app_store_generation(facts, recipe["type"])
        return
    # Can't make this recipe without a bundle identifier.
    if "bundle_id" not in facts:
        facts["warnings"].append(
            "Skipping %s recipe, because I wasn't able to determine the "
            "bundle identifier of this app. You may want to actually download "
            "the app and try again, using the .app file itself as input."
            % recipe["type"]
        )
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    recipe.set_description(
        "Downloads the latest version of %s, creates a "
        "fileset, and copies it into your FileWave "
        "Server." % facts[bundle_name_key]
    )

    recipe.set_parent_from(prefs, facts, "download")

    if (
        facts.get("download_format") in SUPPORTED_IMAGE_FORMATS
        and "sparkle_feed" not in facts
    ):
        # It's a dmg download, but not from Sparkle, so we need to version it.
        recipe.append_processor(
            {
                "Processor": "Versioner",
                "Arguments": {
                    "input_plist_path": (
                        "%pathname%/{}{}.{}/Contents/Info.plist".format(
                            facts.get("relative_path", ""),
                            facts.get("app_file", facts[bundle_name_key]),
                            bundle_type,
                        )
                    ),
                    "plist_version_key": facts["version_key"],
                },
            }
        )
    elif facts.get("download_format") in SUPPORTED_ARCHIVE_FORMATS:
        if (
            facts.get("codesign_reqs", "") == ""
            and len(facts["codesign_authorities"]) == 0
        ):
            # If unsigned, that means the download recipe hasn't
            # unarchived the zip yet.
            recipe.append_processor(
                {
                    "Processor": "Unarchiver",
                    "Arguments": {
                        "archive_path": "%pathname%",
                        "destination_path": "%RECIPE_CACHE_DIR%/%NAME%",
                        "purge_destination": True,
                    },
                }
            )
    elif facts.get("download_format") in SUPPORTED_INSTALL_FORMATS:
        # TODO(Elliot): Fix this. (#41)
        facts["warnings"].append(
            "Sorry, I don't yet know how to create filewave recipes from pkg "
            "downloads."
        )

    # Print a reminder if the required repo isn't present on disk.
    required_repo_reminder("FileWave", "https://github.com/autopkg/filewave", facts)

    recipe.append_processor(
        {
            "Processor": "com.github.autopkg.filewave.FWTool/FileWaveImporter",
            "Arguments": {
                "fw_app_bundle_id": facts["bundle_id"],
                "fw_app_version": "%version%",
                "fw_import_source": "%RECIPE_CACHE_DIR%/%NAME%/{}{}.{}".format(
                    facts.get("relative_path", ""),
                    facts.get("app_file", facts[bundle_name_key]),
                    bundle_type,
                ),
                "fw_fileset_name": "%NAME% - %version%",
                "fw_fileset_group": "Testing",
                "fw_destination_root": "{}/{}.{}".format(
                    SUPPORTED_BUNDLE_TYPES[bundle_type],
                    facts.get("app_file", facts[bundle_name_key]),
                    bundle_type,
                ),
            },
        }
    )

    return recipe


def generate_ds_recipe(facts, prefs, recipe):
    """Generate a ds (DeployStudio) recipe based on passed recipe dict.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
        recipe (Recipe): The recipe to operate on. This recipe will be mutated
            by this function.

    Returns:
        Recipe: Newly updated Recipe object suitable for converting to plist.
    """
    keys = recipe["keys"]
    bundle_type, bundle_name_key = get_bundle_name_info(facts)
    # TODO: Until we get it working.
    if facts.is_from_app_store():
        warn_about_app_store_generation(facts, recipe["type"])
        return
    # Can't make this recipe without a bundle identifier.
    if "bundle_id" not in facts:
        facts["warnings"].append(
            "Skipping %s recipe, because I wasn't able to determine the "
            "bundle identifier of this app. You may want to actually download "
            "the app and try again, using the .app file itself as input."
            % recipe["type"]
        )
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    recipe.set_description(
        "Downloads the latest version of %s and copies it "
        "to your DeployStudio packages." % facts[bundle_name_key]
    )

    recipe.set_parent_from(prefs, facts, "pkg")

    keys["Input"]["DS_PKGS_PATH"] = prefs["DSPackagesPath"]
    keys["Input"]["DS_NAME"] = "%NAME%"
    recipe.append_processor(
        {
            "Processor": "StopProcessingIf",
            "Arguments": {"predicate": "new_package_request == FALSE"},
        }
    )
    recipe.append_processor(
        {
            "Processor": "Copier",
            "Arguments": {
                "source_path": "%pkg_path%",
                "destination_path": "%DS_PKGS_PATH%/%DS_NAME%.pkg",
                "overwrite": True,
            },
        }
    )

    return recipe


# TODO: Not completed, does not function yet
def generate_bigfix_recipe(facts, prefs, recipe):
    """Generate a bigfix (IBM BigFix) recipe based on passed recipe dict.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs (dict): The dictionary containing a key/value pair for Recipe Robot
            preferences.
        recipe (Recipe): The recipe to operate on. This recipe will be mutated
            by this function.

    Returns:
        Recipe: Newly updated Recipe object suitable for converting to plist.
    """

    robo_print(
        "Sorry, I don't know how to make a BigFix recipe yet. If you do, "
        "tell me how with a pull request!",
        LogLevel.WARNING,
    )
    # print(facts)
    return

    # TODO: Windows download examples to work from for future functionality:
    # - https://github.com/autopkg/hansen-m-recipes/tree/master/Box
    # - https://github.com/autopkg/hansen-m-recipes/tree/master/Google
    # - https://github.com/autopkg/hansen-m-recipes/search?utf8=%E2%9C%93&q=win.download
    # And a BigFix recipe example:
    # - https://github.com/CLCMacTeam/AutoPkgBESEngine/blob/dd1603c3fc39c1b9530b49e2a08d3eb0bbeb19a1/Examples/TextWrangler.bigfix.recipe
    keys = recipe["keys"]
    bundle_type, bundle_name_key = get_bundle_name_info(facts)
    # TODO: Until we get it working.
    if facts.is_from_app_store():
        warn_about_app_store_generation(facts, recipe["type"])
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    recipe.set_description(
        "Downloads the latest version of %s and imports it "
        "into your BigFix server." % facts[bundle_name_key]
    )

    recipe.set_parent_from(prefs, facts, "download")

    recipe.append_processor(
        {
            "Processor": "AutoPkgBESEngine",
            # TODO: Which arguments do we need to specify here?
            # - https://github.com/homebysix/recipe-robot/issues/74
            "Arguments": {
                "bes_filename": "%NAME%." + facts["download_format"],
                "bes_version": "%version%",
                "bes_title": "Install/Upgrade: "
                + facts["developer"]
                + " %NAME% %version% - macOS",
                # TODO: Might be a problem with <![CDATA[ being escaped incorrectly in resulting recipe
                "bes_description": "<p>This task will install/upgrade: %NAME% %version%</p>",
                "bes_category": "Software Installers",
                "bes_relevance": [
                    "mac of operating system",
                    'system version >= "10.6.8"',
                    'not exists folder "{}/{}.{}" whose '
                    '(version of it >= "%%version%%" '
                    "as version)".format(
                        SUPPORTED_BUNDLE_TYPES[bundle_type],
                        facts.get("app_file", facts[bundle_name_key]),
                        bundle_type,
                    ),
                ],
                "bes_actions": {
                    "1": {
                        "ActionName": "DefaultAction",
                        "ActionNumber": "Action1",
                        # TODO: The following ActionScript needs to be made universal
                        # 		- facts["download_format"]
                        # 		- facts["download_filename"]
                        # 		- facts["app_name_key"]
                        # 		- facts[bundle_name_key]
                        # 		- facts["description"]
                        # 		- facts["bundle_id"]
                        #
                        # http://www.pythonforbeginners.com/concatenation/string-concatenation-and-formatting-in-python
                        "ActionScript": """
parameter "download_format" = "{}"
parameter "download_filename" = "{}"
parameter "app_name_key" = "{}"
parameter "app_name" = "{}"
parameter "bundle_id" = "{}"
                    """.format(
                            facts["download_format"],
                            facts["download_filename"],
                            facts["app_name_key"],
                            facts[bundle_name_key],
                            facts["bundle_id"],
                        )
                        + """
parameter "NAME" = "%NAME%"
parameter "FILENAME" = "%NAME%.{parameter "download_format"}"
delete "/tmp/{parameter "FILENAME"}"
move "__Download/{parameter "FILENAME"}" "/tmp/{parameter "FILENAME"}"

wait /usr/bin/hdiutil attach -quiet -nobrowse -private -mountpoint "/tmp/%NAME%" "/tmp/{parameter "FILENAME"}"

continue if {exists folder "/tmp/%NAME%/TextWrangler.app"}

wait /bin/rm -rf "/Applications/TextWrangler.app"
wait /bin/cp -Rfp "/tmp/%NAME%/TextWrangler.app" "/Applications"

wait /usr/bin/hdiutil detach -force "/tmp/%NAME%"
delete "/tmp/{parameter "FILENAME"}"
                    """,
                    }
                },
            },
        }
    )

    # TODO: Once everything is working, only give this reminder if missing.
    bigfix_repo = "https://github.com/autopkg/hansen-m-recipes.git"
    facts["reminders"].append(
        "You'll need to have the AutoPkgBESEngine installed and configured:\n"
        "        autopkg repo-add %s\n"
        "        autopkg install BESEngine\n"
        "        autopkg install QnA\n" % bigfix_repo
    )

    return recipe


def warn_about_appstoreapp_pyasn(facts):
    """Print warning reminding user of dependencies for AppStoreApp overrides.

    Args:
        facts (RoboDict): A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path. The "reminders" key is required for this function.
    """
    facts["reminders"].append(
        "I've created at least one AppStoreApp override for you. Be sure to "
        "add the nmcspadden-recipes repo and install pyasn1, if you haven't "
        "already. More information:\n"
        "https://github.com/autopkg/nmcspadden-recipes#appstoreapp-recipe"
    )
