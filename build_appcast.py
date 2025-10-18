#!/usr/bin/env python3

"""build_appcast.py

This script dynamically generates a Sparkle appcast feed for Recipe Robot by parsing recent
releases of the app on GitHub. The resulting xml file is published to the gh-pages branch, and
publicly accessible at this URL:

https://homebysix.github.io/recipe-robot/appcast.xml

"""

import os
import re
import subprocess
import sys

from github import Auth, Github
from markdown import markdown


# Minimum version of Recipe Robot to include in the appcast
MIN_VERS = "2.0.0"

# Link to desired Sparkle release used to generate appcast
SPARKLE_RELEASE = "https://github.com/sparkle-project/Sparkle/releases/download/2.7.1/Sparkle-2.7.1.tar.xz"


def create_cache(cache_path):
    """Create cache folder"""
    if not os.path.isdir(cache_path):
        os.makedirs(cache_path)
    return cache_path


def version_is_less_than(a, b):
    """Compare dot-separated version strings."""
    return tuple(map(int, a.split("."))) < tuple(map(int, b.split(".")))


def adjust_enclosure_urls(appcast_path):
    """Adjust enclosure URLs from GitHub Pages to GitHub Releases format."""
    with open(appcast_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Pattern to match enclosure URLs like:
    # https://homebysix.github.io/recipe-robot/RecipeRobot-2.4.0.dmg
    # And replace with:
    # https://github.com/homebysix/recipe-robot/releases/download/v2.4.0/RecipeRobot-2.4.0.dmg
    pattern = (
        r'<enclosure url="https://homebysix\.github\.io/recipe-robot/'
        r'RecipeRobot-([0-9]+\.[0-9]+\.[0-9]+)\.dmg"'
    )
    replacement = (
        r'<enclosure url="https://github.com/homebysix/recipe-robot/'
        r'releases/download/v\1/RecipeRobot-\1.dmg"'
    )

    content = re.sub(pattern, replacement, content)

    with open(appcast_path, "w", encoding="utf-8") as f:
        f.write(content)

    return content != re.sub(pattern, replacement, content)


def main():
    """Main process."""

    os.chdir(create_cache("cache"))

    # Read GitHub token
    # TODO: from Actions env var
    token_path = "~/.autopkg_gh_token"
    if not os.path.isfile(os.path.expanduser(token_path)):
        print(f"{token_path} is missing")
        sys.exit(1)
    with open(os.path.expanduser(token_path), "r", encoding="utf-8") as f:
        token = f.read().strip()

    # Use GitHub API to get Recipe Robot releases info
    g = Github(auth=Auth.Token(token))
    repo = g.get_repo("homebysix/recipe-robot")
    releases = repo.get_releases()
    for release in releases:
        if "candidate" in release.title.lower():
            # Skip release candidates
            continue
        elif version_is_less_than(release.tag_name.lstrip("v"), MIN_VERS):
            # Skip earlier than the minimum version
            continue
        assets = [
            x for x in release.get_assets() if x.browser_download_url.endswith(".dmg")
        ]
        if not assets:
            # Skip releases with no assets (this shouldn't happen)
            continue

        # Download first asset of each eligible release to cache
        filename = assets[0].browser_download_url.split("/")[-1]
        if not os.path.isfile(filename):
            print(f"Downloading {release.title}...")
            curl_cmd = [
                "curl",
                "-s",
                "-L",
                "-H",
                "Authentication: Bearer %s" % token,
                "-O",
                "--url",
                assets[0].browser_download_url,
            ]
            _ = subprocess.run(curl_cmd, check=False)

        # Download each release's description text to an HTML file
        if not os.path.isfile(os.path.splitext(filename)[0] + ".html"):
            html = markdown(release.body, tab_length=4)
            with open(os.path.splitext(filename)[0] + ".html", "w") as f:
                f.write(html)

    # Change back to parent directory to run generate_appcast
    os.chdir("..")

    # Generate/update the appcast.xml using Sparkle
    print("Generating appcast.xml...")
    sparkle_cmd = [
        os.path.expanduser("~/Developer/Sparkle-2.8.0/bin/generate_appcast"),
        "--maximum-deltas=0",
        "-o",
        "appcast.xml",
        "cache",
    ]
    result = subprocess.run(sparkle_cmd, check=False, capture_output=True, text=True)

    if result.returncode == 0:
        print("Appcast generated successfully")

        # Format the XML using xmllint to standardize formatting
        print("Formatting XML with xmllint...")
        xmllint_cmd = ["xmllint", "--format", "appcast.xml", "-o", "appcast.xml"]
        xmllint_result = subprocess.run(
            xmllint_cmd, check=False, capture_output=True, text=True
        )

        if xmllint_result.returncode == 0:
            print("XML formatted successfully")
        else:
            print(f"Warning: xmllint formatting failed: {xmllint_result.stderr}")

        # Adjust enclosure URLs to use GitHub releases format
        print("Adjusting enclosure URLs to GitHub releases format...")
        adjust_enclosure_urls("appcast.xml")
        print("URLs adjusted successfully")
    else:
        print(f"Error generating appcast: {result.stderr}")
        print(f"Command output: {result.stdout}")

    print("Done")


if __name__ == "__main__":
    main()
