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
generate_sample_data.py

Script that can be used for generating a new sample_data.yaml file, which is
used by the Recipe Robot functional tests to recreate actual AutoPkg recipes.
"""

import os
import plistlib

import yaml


def get_proc_attr(process, processor_name, attribute_name):
    """Given an AutoPkg recipe processor array, extract the value of a specified
    processor's attribute.

    Args:
        process ([dict]): List of dictionaries representing an AutoPkg recipe
            process.
        processor_name (str): Name of the processor to get the attribute from.
        attribute_name (str): Name of the attribute.

    Returns:
        usually str: Value of the processor attribute.
    """
    proc = [x for x in process if x.get("Processor") == processor_name]
    if not proc:
        return

    # Assumption: we only care about the first instance of the processor.
    return proc[0].get(attribute_name)


def main():
    """Main process."""

    # Get list of local recipes.
    recipes = []
    recipe_repos = os.path.expanduser("~/Developer/_personal/sheepdog/repos")
    for dirpath, dirnames, filenames in os.walk(recipe_repos):
        for dirname in dirnames:
            if dirname.startswith("."):
                dirnames.remove(dirname)
        filenames = [x for x in filenames if x.endswith(".recipe")]
        for filename in filenames:
            recipes.append(os.path.join(dirpath, filename))

    sample_data = {}
    for recipe in recipes:
        with open(recipe, "rb") as openfile:
            recipe_dict = plistlib.load(openfile)

        # Skip recipes that don't have NAME or Input keys.
        if not recipe_dict.get("Input"):
            continue
        if not recipe_dict["Input"].get("NAME"):
            continue

        name = recipe_dict["Input"]["NAME"]
        if recipe.endswith(".download.recipe"):
            # Gather input paths from download recipe.
            input_path = None
            if recipe_dict["Input"].get("DOWNLOAD_URL"):
                input_path = recipe_dict["Input"]["DOWNLOAD_URL"]
            elif recipe_dict["Input"].get("SPARKLE_FEED_URL"):
                input_path = recipe_dict["Input"]["SPARKLE_FEED_URL"]
            elif recipe_dict["Input"].get("GITHUB_REPO"):
                input_path = "https://github.com/" + recipe_dict["Input"]["GITHUB_REPO"]
            elif recipe_dict.get("Process"):
                input_path = get_proc_attr(
                    recipe_dict["Process"], "URLDownloader", "url"
                )
                if not input_path:
                    input_path = get_proc_attr(
                        recipe_dict["Process"],
                        "SparkleUpdateInfoProvider",
                        "appcast_url",
                    )
                if not input_path:
                    gh_repo = get_proc_attr(
                        recipe_dict["Process"],
                        "GitHubReleasesInfoProvider",
                        "github_repo",
                    )
                    if gh_repo:
                        input_path = "https://github.com/" + gh_repo

            if input_path:
                if name not in sample_data:
                    sample_data[name] = {"input_path": input_path}
                else:
                    sample_data[name]["input_path"] = input_path

        if recipe.endswith(".pkg.recipe"):
            # Gather bundle IDs from pkg recipe.
            bundle_id = None
            if recipe_dict["Input"].get("BUNDLE_ID"):
                bundle_id = recipe_dict["Input"]["BUNDLE_ID"]
            elif recipe_dict.get("Process"):
                bundle_id = get_proc_attr(
                    recipe_dict["Process"],
                    "PkgCreator",
                    "id",
                )

            if bundle_id:
                if name not in sample_data:
                    sample_data[name] = {"bundle_id": bundle_id}
                else:
                    sample_data[name]["bundle_id"] = bundle_id

        if recipe.endswith(".munki.recipe"):
            # Gather developer from munki recipe.
            developer = None
            if recipe_dict["Input"].get("DEVELOPER"):
                developer = recipe_dict["Input"]["DEVELOPER"]
            elif recipe_dict["Input"].get("MUNKI_DEVELOPER"):
                developer = recipe_dict["Input"]["MUNKI_DEVELOPER"]
            elif recipe_dict["Input"].get("pkginfo"):
                developer = recipe_dict["Input"]["pkginfo"].get("developer")
            if developer:
                if name not in sample_data:
                    sample_data[name] = {"developer": developer}
                else:
                    sample_data[name]["developer"] = developer

    output = []
    for app_name, datum in sample_data.items():
        if all(
            (datum.get("bundle_id"), datum.get("developer"), datum.get("input_path"))
        ):
            output.append(
                {
                    "app_name": app_name,
                    "bundle_id": datum["bundle_id"],
                    "developer": datum["developer"],
                    "input_path": datum["input_path"],
                }
            )
    output.sort(key=lambda x: x["app_name"].lower())
    with open("generated_sample_data.yaml", "w") as openfile:
        openfile.write(yaml.dump(output, indent=2))


if __name__ == "__main__":
    main()
