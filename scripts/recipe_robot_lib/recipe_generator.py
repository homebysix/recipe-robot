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


"""recipe-generator"""


import os

# TODO(Elliot): Can we use the one at /Library/AutoPkg/FoundationPlist instead?
# Or not use it at all (i.e. use the preferences system correctly).
try:
    from recipe_robot_lib import FoundationPlist
    from .tools import create_dest_dirs, create_SourceForgeURLProvider, extract_app_icon
    from .tools import robo_print, LogLevel, __version__
except ImportError:
    print '[WARNING] importing plistlib as FoundationPlist'
    import plistlib as FoundationPlist


# Global variables.
prefs_file = os.path.expanduser(
    "~/Library/Preferences/com.elliotjordan.recipe-robot.plist")
cache_dir = os.path.expanduser("~/Library/Caches/Recipe Robot")

# Build the list of download formats we know about.
supported_image_formats = ("dmg", "iso")  # downloading iso unlikely
supported_archive_formats = ("zip", "tar.gz", "gzip", "tar.bz2", "tbz", "tgz")
supported_install_formats = ("pkg", "mpkg")  # downloading mpkg unlikely
all_supported_formats = (supported_image_formats + supported_archive_formats +
                         supported_install_formats)


def generate_recipes(facts, prefs, recipes):
    """Generate the selected types of recipes.

    Args:
        facts: A continually-updated dictionary containing all the information
            we know so far about the app associated with the input path.
        prefs: The dictionary containing a key/value pair for each preference.
        recipes: The list of known recipe types, created by init_recipes().
    """
    preferred = [recipe for recipe in recipes if recipe["preferred"]]

    # No recipe types are preferred.
    if not preferred:
        robo_print("Sorry, no recipes available to generate.", LogLevel.ERROR)

    # TODO(Shea) Move to some kind of fact-validator function. (#30)
    # We don't have enough information to create a recipe set.
    if (facts["is_from_app_store"] is False and
            "sparkle_feed" not in facts and
            "github_repo" not in facts and
            "sourceforge_id" not in facts and
            "download_url" not in facts):
        robo_print("Sorry, I don't know how to download this app. "
                   "Maybe try another angle? If you provided an app, try "
                   "providing the Sparkle feed for the app instead. Or maybe "
                   "the app's developers offer a direct download URL on their "
                   "website.", LogLevel.ERROR)
    if (facts["is_from_app_store"] is False and
            "download_format" not in facts):
        robo_print("Sorry, I can't tell what format to download this app in. "
                   "Maybe try another angle? If you provided an app, try "
                   "providing the Sparkle feed for the app instead. Or maybe "
                   "the app's developers offer a direct download URL on their "
                   "website.", LogLevel.ERROR)

    # We have enough information to create a recipe set, but with assumptions.
    if "codesign_status" not in facts:
        robo_print("I can't tell whether this app is codesigned or not, so "
                   "I'm going to assume it's not. You may want to verify that "
                   "yourself and add the CodeSignatureVerifier processor if "
                   "necessary.", LogLevel.REMINDER)
        facts["codesign_status"] = "unsigned"
    if "version_key" not in facts:
        robo_print("I can't tell whether to use CFBundleShortVersionString or "
                   "CFBundleVersion for the version key of this app. Most "
                   "apps use CFBundleShortVersionString, so that's what I'll "
                   "use. You may want to verify that and modify the recipes "
                   "if necessary.", LogLevel.REMINDER)
        facts["version_key"] = "CFBundleShortVersionString"

    # Prepare the destination directory.
    if "developer" in facts:
        recipe_dest_dir = os.path.join(os.path.expanduser(prefs["RecipeCreateLocation"]), facts["developer"])
    else:
        recipe_dest_dir = os.path.join(os.path.expanduser(prefs["RecipeCreateLocation"]), facts["app_name"])
    create_dest_dirs(recipe_dest_dir)

    # Create a recipe for each preferred type we know about.
    for recipe in preferred:

        # TODO (Shea): This could be a global constant. Well, maybe.
        # Construct the default keys common to all recipes.
        recipe["keys"] = {
            "Identifier": "",
            "MinimumVersion": "0.5.0",
            "Input": {
                "NAME": facts["app_name"]
            },
            "Process": [],
            "Comment": "Created with Recipe Robot v%s "
                       "(https://github.com/homebysix/recipe-robot)"
                       % __version__
        }
        keys = recipe["keys"]

        # Set the recipe filename (no spaces, except JSS recipes).
        recipe["filename"] = "%s.%s.recipe" % (
            facts["app_name"].replace(" ", ""), recipe["type"])

        # Set the recipe identifier.
        keys["Identifier"] = "%s.%s.%s" % (prefs["RecipeIdentifierPrefix"],
                                            recipe["type"],
                                            facts["app_name"].replace(" ", ""))

        # If the name of the app bundle differs from the name of the app
        # itself, we need another input variable for that.
        if "app_file" in facts:
            keys["Input"]["APP_FILENAME"] = facts["app_file"]
            facts["app_name_key"] = "%APP_FILENAME%"
        else:
            facts["app_name_key"] = "%NAME%"

        # Set keys specific to download recipes.
        if recipe["type"] == "download":
            generate_download_recipe(facts, prefs, recipe)
        # Set keys specific to App Store munki overrides.
        elif recipe["type"] == "munki" and facts["is_from_app_store"] is True:
            generate_app_store_munki_recipe(facts, prefs, recipe)
        # Set keys specific to non-App Store munki recipes.
        elif recipe["type"] == "munki" and facts["is_from_app_store"] is False:
            generate_munki_recipe(facts, prefs, recipe)
        # Set keys specific to App Store pkg overrides.
        elif recipe["type"] == "pkg" and facts["is_from_app_store"] is True:
            generate_app_store_pkg_recipe(facts, prefs, recipe)
        # Set keys specific to non-App Store pkg recipes.
        elif recipe["type"] == "pkg" and facts["is_from_app_store"] is False:
            generate_pkg_recipe(facts, prefs, recipe)
        # Set keys specific to install recipes.
        elif recipe["type"] == "install":
            generate_install_recipe(facts, prefs, recipe)
        # Set keys specific to jss recipes.
        elif recipe["type"] == "jss":
            generate_jss_recipe(facts, prefs, recipe)
        # Set keys specific to absolute recipes.
        elif recipe["type"] == "absolute":
            generate_absolute_recipe(facts, prefs, recipe)
        # Set keys specific to sccm recipes.
        elif recipe["type"] == "sccm":
            generate_sccm_recipe(facts, prefs, recipe)
        # Set keys specific to ds recipes.
        elif recipe["type"] == "ds":
            generate_ds_recipe(facts, prefs, recipe)
        # Set keys specific to filewave recipes.
        elif recipe["type"] == "filewave":
            generate_filewave_recipe(facts, prefs, recipe)
        else:
            # This shouldn't happen, if all the right recipe types are
            # specified in init_recipes() and also specified above.
            robo_print("Oops, I think my programmer messed up. I don't "
                        "yet know how to generate a %s recipe. Sorry about "
                        "that." % recipe["type"], LogLevel.WARNING)

        # Write the recipe to disk.
        if len(recipe["keys"]["Process"]) > 0:
            dest_path = os.path.join(recipe_dest_dir, recipe["filename"])
            if not os.path.exists(dest_path):
                # Keep track of the total number of unique recipes we've created.
                prefs["RecipeCreateCount"] += 1
            # TODO(Elliot): Warning if a file already exists here. (#32)
            # TODO(Elliot): Create subfolders automatically. (#31)
            FoundationPlist.writePlist(recipe["keys"], dest_path)
            robo_print("%s/%s" % (recipe_dest_dir,
                                  recipe["filename"]), LogLevel.LOG, 4)

    # Save preferences to disk for next time.
    FoundationPlist.writePlist(prefs, prefs_file)


def generate_download_recipe(facts, prefs, recipe):
    """Generate a download recipe on passed recipe dict.

    Args:
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        recipe: The recipe to operate on. This recipe will be mutated
            by this function!
    """
    keys = recipe["keys"]
    # Can't make this recipe if the app is from the App Store.
    if facts["is_from_app_store"] is True:
        robo_print("Skipping %s recipe, because this app "
                    "was downloaded from the "
                    "App Store." % recipe["type"], LogLevel.WARNING)
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    # Save a description that explains what this recipe does.
    keys["Description"] = ("Downloads the latest version "
                            "of %s." % facts["app_name"])

    if "sparkle_feed" in facts:
        keys["Input"]["SPARKLE_FEED_URL"] = facts["sparkle_feed"]
        if "user-agent" in facts:
            keys["Process"].append({
                "Processor": "SparkleUpdateInfoProvider",
                "Arguments": {
                    "appcast_request_headers": {
                        "user-agent": facts["user-agent"]
                    },
                    "appcast_url": "%SPARKLE_FEED_URL%"
                }
            })
            keys["Process"].append({
                "Processor": "URLDownloader",
                "Arguments": {
                    "filename": "%%NAME%%-%%version%%.%s" % facts["download_format"],
                    "request_headers": {
                        "user-agent": facts["user-agent"]
                    }
                }
            })
        else:
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
        if "developer" in facts:
            create_SourceForgeURLProvider(os.path.join(os.path.expanduser(prefs["RecipeCreateLocation"]), facts["developer"]))
        else:
            create_SourceForgeURLProvider(os.path.join(os.path.expanduser(prefs["RecipeCreateLocation"]), facts["app_name"]))
        recipe["keys"]["Process"].append({
            "Processor": "SourceForgeURLProvider",
            "Arguments": {
                "SOURCEFORGE_FILE_PATTERN": "\\.%s" % facts["download_format"],
                "SOURCEFORGE_PROJECT_ID": facts["sourceforge_id"]
            }
        })
        keys["Process"].append({
            "Processor": "URLDownloader",
            "Arguments": {
                "filename": "%%NAME%%.%s" % facts["download_format"]
            }
        })
    elif "download_url" in facts:
        if "user-agent" in facts:
            keys["Input"]["DOWNLOAD_URL"] = facts["download_url"]
            keys["Process"].append({
                "Processor": "URLDownloader",
                "Arguments": {
                    "url": "%DOWNLOAD_URL%",
                    # TODO(Elliot): Explicit filename may not be necessary. (#35)
                    # Example: http://www.sonnysoftware.com/Bookends.dmg
                    "filename": facts["download_filename"],
                    "request_headers": {
                        "user-agent": facts["user-agent"]
                    }
                }
            })
        else:
            keys["Input"]["DOWNLOAD_URL"] = facts["download_url"]
            keys["Process"].append({
                "Processor": "URLDownloader",
                "Arguments": {
                    "url": "%DOWNLOAD_URL%",
                    "filename": facts["download_filename"]
                }
            })
    keys["Process"].append({
        "Processor": "EndOfCheckPhase"
    })

    if facts["codesign_status"] == "signed":
        # We encountered a signed app, and will use CodeSignatureVerifier on
        # the app. We are assuming the app is at the base level of the dmg/zip.
        if facts["download_format"] in supported_image_formats:
            keys["Process"].append({
                "Processor": "CodeSignatureVerifier",
                "Arguments": {
                    "input_path": "%%pathname%%/%s.app" % facts["app_name_key"],
                    "requirement": facts.get("codesign_reqs", "")
                }
            })
            if facts.get("sparkle_provides_version", False) is False:
                # Either the Sparkle feed doesn't provide version, or there's no
                # Sparkle feed.
                if facts["version_key"] == "CFBundleShortVersionString":
                    keys["Process"].append({
                        "Processor": "AppDmgVersioner",
                        "Arguments": {
                            "dmg_path": "%pathname%"
                        }
                    })
                else:
                    keys["Process"].append({
                        "Processor": "Versioner",
                        "Arguments": {
                            "input_plist_path": "%%pathname%%/%s.app/Contents/Info.plist" % facts["app_name_key"],
                            "plist_version_key": facts["version_key"]
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
                    "input_path": "%%RECIPE_CACHE_DIR%%/%%NAME%%/Applications/%s.app" % facts["app_name_key"],
                    "requirement": facts.get("codesign_reqs", "")
                }
            })
            if facts.get("sparkle_provides_version", False) is False:
                # Either the Sparkle feed doesn't provide version, or there's no
                # Sparkle feed.
                keys["Process"].append({
                    "Processor": "Versioner",
                    "Arguments": {
                        "input_plist_path": "%%RECIPE_CACHE_DIR%%/%%NAME%%/Applications/%s.app/Contents/Info.plist" % facts["app_name_key"],
                        "plist_version_key": facts["version_key"]
                    }
                })
        elif facts["download_format"] in supported_install_formats:
            # TODO(Elliot): Check for signed .pkg files. (#36)
            robo_print("I'm not quite sure how I ended up here. Looks like I "
                       "found a signed pkg download, but also a signed app "
                       "somewhere along the way. My boss is going to need to "
                       "put his thinking cap on.", LogLevel.WARNING)
            return
    elif facts.get("codesign_authorities", "unsigned") == "signed":
        # We encountered a signed pkg, and will use CodeSignatureVerifier on
        # the pkg. We are assuming the pkg is at the base level of the dmg/zip.
        if facts["download_format"] in supported_image_formats:
            keys["Process"].append({
                "Processor": "CodeSignatureVerifier",
                "Arguments": {
                    "input_path": "%pathname%/*.pkg",
                    "expected_authority_names": facts["codesign_authorities"]
                }
            })
        elif facts["download_format"] in supported_archive_formats:
            keys["Process"].append({
                "Processor": "Unarchiver",
                "Arguments": {
                    "archive_path": "%pathname%",
                    "destination_path": "%RECIPE_CACHE_DIR%/%NAME%",
                    "purge_destination": True
                }
            })
            keys["Process"].append({
                "Processor": "CodeSignatureVerifier",
                "Arguments": {
                    "input_path": "%RECIPE_CACHE_DIR%/%NAME%/*.pkg",
                    "expected_authority_names": facts["codesign_authorities"]
                }
            })
        elif facts["download_format"] in supported_install_formats:
            keys["Process"].append({
                "Processor": "CodeSignatureVerifier",
                "Arguments": {
                    "input_path": "%pathname%",
                    "expected_authority_names": facts["codesign_authorities"]
                }
            })


def generate_app_store_munki_recipe(facts, prefs, recipe):
    """Generate a munki recipe on passed recipe dict.

    This function is for app-store apps.

    Args:
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        recipe: The recipe to operate on. This recipe will be mutated
            by this function!
    """
    keys = recipe["keys"]
    robo_print("Generating %s recipe..." % recipe["type"])

    # Save a description that explains what this recipe does.
    keys["Description"] = ("Downloads the latest version of "
                            "%s from the Mac App Store and "
                            "imports it into "
                            "Munki." % facts["app_name"])
    keys["ParentRecipe"] = "com.github.nmcspadden.munki.appstore"
    keys["Input"]["PATH"] = facts["app_path"]
    recipe["filename"] = "MAS-" + recipe["filename"]

    keys["Input"]["MUNKI_REPO_SUBDIR"] = "apps/%NAME%"
    keys["Input"]["pkginfo"] = {
        "catalogs": ["testing"],
        "developer": facts.get("developer", ""),
        "display_name": facts["app_name"],
        "name": "%NAME%",
        "unattended_install": True
    }

    if "description" in facts:
        keys["Input"]["pkginfo"]["description"] = facts["description"]
    else:
        robo_print("I couldn't find a description for this app, "
                    "so you'll need to manually add one to the "
                    "munki recipe.", LogLevel.REMINDER)
        keys["Input"]["pkginfo"]["description"] = " "

    warn_about_appstoreapp_pyasn()


def generate_munki_recipe(facts, prefs, recipe):
    """Generate a munki recipe on passed recipe dict.

    Args:
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs: The dictionary containing a key/value pair for each
            preference.
        recipe: The recipe to operate on. This recipe will be mutated
            by this function!
    """
    keys = recipe["keys"]
    robo_print("Generating %s recipe..." % recipe["type"])

    # Save a description that explains what this recipe does.
    keys["Description"] = ("Downloads the latest version of %s "
                            "and imports it into "
                            "Munki." % facts["app_name"])
    # TODO(Elliot): What if it's somebody else's download recipe? (#37)
    keys["ParentRecipe"] = "%s.download.%s" % (prefs["RecipeIdentifierPrefix"], facts["app_name"].replace(" ", ""))

    keys["Input"]["MUNKI_REPO_SUBDIR"] = "apps/%NAME%"
    keys["Input"]["pkginfo"] = {
        "catalogs": ["testing"],
        "developer": facts.get("developer", ""),
        "display_name": facts["app_name"],
        "name": "%NAME%",
        "unattended_install": True
    }

    if "description" in facts:
        keys["Input"]["pkginfo"]["description"] = facts["description"]
    else:
        robo_print("I couldn't find a description for this app, "
                    "so you'll need to manually add one to the "
                    "munki recipe.", LogLevel.REMINDER)
        keys["Input"]["pkginfo"]["description"] = " "

    # Set default variable to use for substitution.
    import_file_var = "%pathname%"

    if facts["download_format"] in supported_image_formats:
        if facts["codesign_status"] != "signed":
            if facts["version_key"] == "CFBundleShortVersionString":
                keys["Process"].append({
                    "Processor": "AppDmgVersioner",
                    "Arguments": {
                        "dmg_path": "%pathname%"
                    }
                })
            else:
                keys["Process"].append({
                    "Processor": "Versioner",
                    "Arguments": {
                        "input_plist_path": "%%pathname%%/%s.app/Contents/Info.plist" % facts["app_name_key"],
                        "plist_version_key": facts["version_key"]
                    }
                })

    elif facts["download_format"] in supported_archive_formats:
        if facts["codesign_status"] != "signed":
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
        # Blocking applications are determined automatically by Munki except
        # when the software is distributed inside a pkg. In this case, the
        # blocking applications must be set manually in the recipe.
        if len(facts["blocking_applications"]) > 0:
            keys["Input"]["pkginfo"]["blocking_applications"] = facts["blocking_applications"]

    if facts["version_key"] != "CFBundleShortVersionString":
        keys["Process"].append({
            "Processor": "MunkiPkginfoMerger",
            "Arguments": {
                "additional_pkginfo": {
                    "version": "%version%"
                }
            }
        })
        keys["Process"].append({
            "Processor": "MunkiImporter",
            "Arguments": {
                "pkg_path": import_file_var,
                "repo_subdirectory": "%MUNKI_REPO_SUBDIR%",
                "version_comparison_key": facts["version_key"]
            }
        })
    else:
        keys["Process"].append({
            "Processor": "MunkiImporter",
            "Arguments": {
                "pkg_path": import_file_var,
                "repo_subdirectory": "%MUNKI_REPO_SUBDIR%"
            }
        })

    # Extract the app's icon and save it to disk.
    if "icon_path" in facts:
        if "developer" in facts:
            extracted_icon = os.path.join(os.path.expanduser(prefs["RecipeCreateLocation"]), facts["developer"], facts["app_name"] + ".png")
        else:
            extracted_icon = os.path.join(os.path.expanduser(prefs["RecipeCreateLocation"]), facts["app_name"], facts["app_name"] + ".png")
        extract_app_icon(facts["icon_path"], extracted_icon)
    else:
        robo_print("I don't have enough information to create a "
                    "PNG icon for this app.", LogLevel.WARNING)


def generate_app_store_pkg_recipe(facts, prefs, recipe):
    """Generate a pkg recipe on passed recipe dict.

    This function is for app-store apps.

    Args:
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        recipe: The recipe to operate on. This recipe will be mutated
            by this function!
    """
    keys = recipe["keys"]
    robo_print("Generating %s recipe..." % recipe["type"])

    # Save a description that explains what this recipe does.
    keys["Description"] = ("Downloads the latest version of "
                            "%s from the Mac App Store and "
                            "creates a package." % facts["app_name"])
    keys["ParentRecipe"] = "com.github.nmcspadden.pkg.appstore"
    keys["Input"]["PATH"] = facts["app_path"]
    recipe["filename"] = "MAS-" + recipe["filename"]

    warn_about_appstoreapp_pyasn()


def generate_pkg_recipe(facts, prefs, recipe):
    """Generate a munki recipe on passed recipe dict.

    Args:
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs: The dictionary containing a key/value pair for each
            preference.
        recipe: The recipe to operate on. This recipe will be mutated
            by this function!
    """
    keys = recipe["keys"]
    # Can't make this recipe without a bundle identifier.
    # TODO(Elliot): Bundle id is also provided by AppDmgVersioner and some
    # Sparkle feeds. When those are present, can we proceed even though we
    # don't have bundle_id in facts? (#40)
    if "bundle_id" not in facts:
        robo_print("Skipping %s recipe, because I wasn't able to "
                    "determine the bundle identifier of this app. "
                    "You may want to actually download the app and "
                    "try again, using the .app file itself as "
                    "input." % recipe["type"], LogLevel.WARNING)
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    # Save a description that explains what this recipe does.
    keys["Description"] = ("Downloads the latest version of %s and "
                            "creates a package." % facts["app_name"])
    # TODO(Elliot): What if it's somebody else's download recipe? (#37)
    keys["ParentRecipe"] = "%s.download.%s" % (prefs["RecipeIdentifierPrefix"], facts["app_name"].replace(" ", ""))

    # Save bundle identifier.
    keys["Input"]["BUNDLE_ID"] = facts["bundle_id"]

    if facts["download_format"] in supported_image_formats:
        if facts["codesign_status"] != "signed":
            if facts["version_key"] == "CFBundleShortVersionString":
                keys["Process"].append({
                    "Processor": "AppDmgVersioner",
                    "Arguments": {
                        "dmg_path": "%pathname%"
                    }
                })
            else:
                keys["Process"].append({
                    "Processor": "Versioner",
                    "Arguments": {
                        "input_plist_path": "%%pathname%%/%s.app/Contents/Info.plist" % facts["app_name_key"],
                        "plist_version_key": facts["version_key"]
                    }
                })
        keys["Process"].append({
            "Processor": "PkgRootCreator",
            "Arguments": {
                "pkgroot": "%RECIPE_CACHE_DIR%/%NAME%",
                "pkgdirs": {
                    "Applications": "0775"
                }
            }
        })
        keys["Process"].append({
            "Processor": "Copier",
            "Arguments": {
                "source_path": "%%pathname%%/%s.app" % facts["app_name_key"],
                "destination_path": "%%pkgroot%%/Applications/%s.app" % facts["app_name_key"]
            }
        })

    elif facts["download_format"] in supported_archive_formats:
        if facts["codesign_status"] != "signed":
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
            if facts.get("sparkle_provides_version", False) is False:
                # Either the Sparkle feed doesn't provide version, or there's
                # no Sparkle feed.
                keys["Process"].append({
                    "Processor": "Versioner",
                    "Arguments": {
                        "input_plist_path": "%%RECIPE_CACHE_DIR%%/%%NAME%%/Applications/%s.app/Contents/Info.plist" % facts["app_name_key"],
                        "plist_version_key": facts["version_key"]
                    }
                })

    elif facts["download_format"] in supported_install_formats:
        robo_print("Skipping pkg recipe, since the download format is "
                   "already pkg.", LogLevel.WARNING)
        return

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


def generate_install_recipe(facts, prefs, recipe):
    """Generate an install recipe on passed recipe dict.

    Args:
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs: The dictionary containing a key/value pair for each
            preference.
        recipe: The recipe to operate on. This recipe will be mutated
            by this function!
    """
    keys = recipe["keys"]
    # Can't make this recipe if the app is from the App Store.
    if facts["is_from_app_store"] is True:
        robo_print("Skipping %s recipe, because this app "
                    "was downloaded from the "
                    "App Store." % recipe["type"], LogLevel.WARNING)
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    # Save a description that explains what this recipe does.
    keys["Description"] = ("Installs the latest version "
                            "of %s." % facts["app_name"])

    # TODO(Elliot): What if it's somebody else's download recipe? (#37)
    keys["ParentRecipe"] = "%s.download.%s" % (prefs["RecipeIdentifierPrefix"], facts["app_name"].replace(" ", ""))

    if facts["download_format"] in supported_image_formats:
        keys["Process"].append({
            "Processor": "InstallFromDMG",
            "Arguments": {
                "dmg_path": "%pathname%",
                "items_to_copy": [{
                    "source_item": "%s.app" % facts["app_name_key"],
                    "destination_path": "/Applications"
                }]
            }
        })

    elif facts["download_format"] in supported_archive_formats:
        if facts["codesign_status"] != "signed":
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
                "dmg_root": "%RECIPE_CACHE_DIR%/%NAME%/Applications",
                "dmg_path": "%RECIPE_CACHE_DIR%/%NAME%.dmg"
            }
        })
        keys["Process"].append({
            "Processor": "InstallFromDMG",
            "Arguments": {
                "dmg_path": "%dmg_path%",
                "items_to_copy": [{
                    "source_item": "%s.app" % facts["app_name_key"],
                    "destination_path": "/Applications"
                }]
            }
        })

    elif facts["download_format"] in supported_install_formats:
        keys["Process"].append({
            "Processor": "Installer",
            "Arguments": {
                "pkg_path": "%pathname%"
            }
        })


def generate_jss_recipe(facts, prefs, recipe):
    """Generate a JSS recipe on passed recipe dict.

    Args:
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs: The dictionary containing a key/value pair for each
            preference.
        recipe: The recipe to operate on. This recipe will be mutated
            by this function!
    """
    keys = recipe["keys"]
    # Can't make this recipe without a bundle identifier.
    if "bundle_id" not in facts:
        robo_print("Skipping %s recipe, because I wasn't able to "
                    "determine the bundle identifier of this app. "
                    "You may want to actually download the app and "
                    "try again, using the .app file itself as "
                    "input." % recipe["type"], LogLevel.WARNING)
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    # Authors of jss recipes are encouraged to use spaces.
    filename = "%s.%s.recipe" % (facts["app_name"], recipe["type"])

    # Save a description that explains what this recipe does.
    keys["Description"] = ("Downloads the latest version of %s "
                            "and imports it into your JSS." %
                            facts["app_name"])
    # TODO(Elliot): What if it's somebody else's pkg recipe? (#37)
    keys["ParentRecipe"] = "%s.pkg.%s" % (
        prefs["RecipeIdentifierPrefix"], facts["app_name"].replace(" ", ""))

    keys["Input"]["CATEGORY"] = "Productivity"
    robo_print("Remember to manually set the category in the jss "
               "recipe. I've set it to \"Productivity\" by "
               "default.", LogLevel.REMINDER)

    keys["Input"]["POLICY_CATEGORY"] = "Testing"
    keys["Input"]["POLICY_TEMPLATE"] = "PolicyTemplate.xml"
    if not os.path.exists(os.path.join(os.path.expanduser(prefs["RecipeCreateLocation"]), "PolicyTemplate.xml")):
        robo_print("Please make sure PolicyTemplate.xml is in your "
                    "AutoPkg search path.", LogLevel.REMINDER)
    keys["Input"]["SELF_SERVICE_ICON"] = "%NAME%.png"
    if not os.path.exists(os.path.join(os.path.expanduser(prefs["RecipeCreateLocation"]), "%s.png" % facts["app_name"])):
        robo_print("Please make sure %s.png is in your AutoPkg search "
                    "path." % facts["app_name"], LogLevel.REMINDER)
    keys["Input"]["SELF_SERVICE_DESCRIPTION"] = facts.get("description", "")
    keys["Input"]["GROUP_NAME"] = "%NAME%-update-smart"

    if facts["version_key"] == "CFBundleVersion":
        keys["Input"]["GROUP_TEMPLATE"] = "CFBundleVersionSmartGroupTemplate.xml"
        if not os.path.exists(os.path.join(os.path.expanduser(prefs["RecipeCreateLocation"]), "CFBundleVersionSmartGroupTemplate.xml")):
            robo_print("Please make sure "
                        "CFBundleVersionSmartGroupTemplate.xml is in "
                        "your AutoPkg search path.", LogLevel.REMINDER)
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
        if not os.path.exists(os.path.join(os.path.expanduser(prefs["RecipeCreateLocation"]), "SmartGroupTemplate.xml")):
            robo_print("Please make sure SmartGroupTemplate.xml is in "
                        "your AutoPkg search path.", LogLevel.REMINDER)
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
    if "icon_path" in facts:
        extracted_icon = "%s/%s.png" % (prefs["RecipeCreateLocation"], facts["app_name"])
        extract_app_icon(facts["icon_path"], extracted_icon)
    else:
        robo_print("I don't have enough information to create a "
                    "PNG icon for this app.", LogLevel.WARNING)


def generate_absolute_recipe(facts, prefs, recipe):
    """Generate an Absolute Manage recipe on passed recipe dict.

    Args:
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs: The dictionary containing a key/value pair for each
            preference.
        recipe: The recipe to operate on. This recipe will be mutated
            by this function!
    """
    keys = recipe["keys"]
    # Can't make this recipe without a bundle identifier.
    if "bundle_id" not in facts:
        robo_print("Skipping %s recipe, because I wasn't able to "
                    "determine the bundle identifier of this app. "
                    "You may want to actually download the app and "
                    "try again, using the .app file itself as "
                    "input." % recipe["type"], LogLevel.WARNING)
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    # Save a description that explains what this recipe does.
    keys["Description"] = ("Downloads the latest version of %s and "
                            "copies it into your Absolute Manage "
                            "Server." % facts["app_name"])
    # TODO(Elliot): What if it's somebody else's pkg recipe? (#37)
    keys["ParentRecipe"] = "%s.pkg.%s" % (prefs["RecipeIdentifierPrefix"], facts["app_name"])

    # TODO(Elliot): Print a reminder if this processor isn't present on disk. (#42)
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


def generate_sccm_recipe(facts, prefs, recipe):
    """Generate an SCCM recipe on passed recipe dict.

    Args:
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs: The dictionary containing a key/value pair for each
            preference.
        recipe: The recipe to operate on. This recipe will be mutated
            by this function!
    """
    keys = recipe["keys"]
    # Can't make this recipe without a bundle identifier.
    if "bundle_id" not in facts:
        robo_print("Skipping %s recipe, because I wasn't able to "
                    "determine the bundle identifier of this app. "
                    "You may want to actually download the app and "
                    "try again, using the .app file itself as "
                    "input." % recipe["type"], LogLevel.WARNING)
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    # Save a description that explains what this recipe does.
    keys["Description"] = ("Downloads the latest version of %s and "
                            "copies it into your SCCM "
                            "Server." % facts["app_name"])
    # TODO(Elliot): What if it's somebody else's pkg recipe? (#37)
    keys["ParentRecipe"] = "%s.pkg.%s" % (prefs["RecipeIdentifierPrefix"], facts["app_name"])

    # TODO(Elliot): Print a reminder if this processor isn't present on disk. (#42)
    keys["Process"].append({
        "Processor": "com.github.autopkg.cgerke-recipes.SharedProcessors/CmmacCreator",
        "SharedProcessorRepoURL": "https://github.com/autopkg/cgerke-recipes",
        "Arguments": {
            "source_file": "%pkg_path%",
            "destination_directory": "%RECIPE_CACHE_DIR%"
        }
    })


def generate_filewave_recipe(facts, prefs, recipe):
    """Generate a FileWave recipe on passed recipe dict.

    Args:
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs: The dictionary containing a key/value pair for each
            preference.
        recipe: The recipe to operate on. This recipe will be mutated
            by this function!
    """
    keys = recipe["keys"]
    # Can't make this recipe without a bundle identifier.
    if "bundle_id" not in facts:
        robo_print("Skipping %s recipe, because I wasn't able to "
                    "determine the bundle identifier of this app. "
                    "You may want to actually download the app and "
                    "try again, using the .app file itself as "
                    "input." % recipe["type"], LogLevel.WARNING)
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    # Save a description that explains what this recipe does.
    keys["Description"] = ("Downloads the latest version of %s, creates a "
                           "fileset, and copies it into your FileWave "
                           "Server." % facts["app_name"])
    keys["ParentRecipe"] = "%s.download.%s" % (prefs["RecipeIdentifierPrefix"], facts["app_name"])

    if facts["download_format"] in supported_image_formats and "sparkle_feed" not in facts:
        # It's a dmg download, but not from Sparkle, so we need to version it.
        keys["Process"].append({
            "Processor": "Versioner",
            "Arguments": {
                "input_plist_path": "%%pathname%%/%s.app/Contents/Info.plist" % facts["app_name_key"],
                "plist_version_key": facts["version_key"]
            }
        })
    elif facts["download_format"] in supported_archive_formats:
        if facts["codesign_status"] != "signed":
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
    elif facts["download_format"] in supported_install_formats:
        # TODO(Elliot): Fix this. (#41)
        robo_print("Sorry, I don't yet know how to create "
                    "filewave recipes from pkg downloads.", LogLevel.WARNING)

    # TODO(Elliot): Print a reminder if this processor isn't present on disk. (#42)
    keys["Process"].append({
        "Processor": "com.github.johncclayton.filewave.FWTool/FileWaveImporter",
        "Arguments": {
            "fw_app_bundle_id": facts["bundle_id"],
            "fw_app_version": "%version%",
            "fw_import_source": "%RECIPE_CACHE_DIR%/%NAME%/%NAME%.app",
            "fw_fileset_name": "%NAME% - %version%",
            "fw_fileset_group": "Testing",
            "fw_destination_root": "/Applications/%NAME%.app"
        }
    })


def generate_ds_recipe(facts, prefs, recipe):
    """Generate a DeployStudio recipe on passed recipe dict.

    Args:
        facts: A continually-updated dictionary containing all the
            information we know so far about the app associated with the
            input path.
        prefs: The dictionary containing a key/value pair for each
            preference.
        recipe: The recipe to operate on. This recipe will be mutated
            by this function!
    """
    keys = recipe["keys"]
    # Can't make this recipe without a bundle identifier.
    if "bundle_id" not in facts:
        robo_print("Skipping %s recipe, because I wasn't able to "
                    "determine the bundle identifier of this app. "
                    "You may want to actually download the app and "
                    "try again, using the .app file itself as "
                    "input." % recipe["type"], LogLevel.WARNING)
        return

    robo_print("Generating %s recipe..." % recipe["type"])

    # Save a description that explains what this recipe does.
    keys["Description"] = ("Downloads the latest version of %s and "
                            "copies it to your DeployStudio "
                            "packages." % facts["app_name"])
    # TODO(Elliot): What if it's somebody else's pkg recipe? (#37)
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


def warn_about_appstoreapp_pyasn():
    """Print warning reminding user of dependencies for AppStoreApps."""
    robo_print("I've created at least one AppStoreApp override for you. "
                "Be sure to add the nmcspadden-recipes repo and install "
                "pyasn1, if you haven't already. (More information: "
                "https://github.com/autopkg/nmcspadden-recipes"
                "#appstoreapp-recipe)", LogLevel.REMINDER)


def main():
    """Do nothing"""
    pass


if __name__ == '__main__':
    main()
