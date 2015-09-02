![Recipe Robot](images/header.jpg)

__Table of contents__

<!-- MarkdownTOC autolink=true depth=3 bracket=round -->

- [Overview](#overview)
- [Python Script Usage](#python-script-usage)
- [Mac App Usage](#mac-app-usage)
- [Tips](#tips)
- [Troubleshooting](#troubleshooting)
- [Feedback](#feedback)

<!-- /MarkdownTOC -->


## Overview

Recipe Robot will soon become the easiest way to create AutoPkg recipes. It will consist of two components:

- __Python script__ that takes various types of input and automatically outputs AutoPkg recipes in various formats.

- A __native Mac app__ that puts a friendly face on the Python script and makes it as simple as dragging and dropping.

This two-pronged approach will allow AutoPkg novices to easily create recipes that follow community-accepted guidelines with the minimum amount of effort, and will still provide a command-line tool for more advanced AutoPkg users. Also, ensuring that all program logic is done in Python should hopefully foster community contribution to this project.


## Python Script Usage

The Python script is under heavy development right now and is super rough, but you're welcome to try it out if you want a preview of what Recipe Robot will do. __Use at your own risk.__ I don't think Recipe Robot will delete all your files, but you are accepting that possibility.

Just open Terminal, `cd` to the scripts folder, then type:

```
python recipe-robot.py <input>
```

For `<input>`, you can use one of several types of information:

- The path to a Mac app.
- The path to an app's Sparkle feed.
- The direct download URL for an app (which usually ends with .zip or .dmg).
- The GitHub project URL for an app.
- The SourceForge project URL for an app.
- The path to an existing recipe associated with an app.

The first time Recipe Robot runs, you'll be prompted for some information. On subsequent runs, you can use the `--config` argument to force this prompt to return.

Here's what Recipe Robot looks like when it's working properly. The command I used was: `python recipe-robot.py http://delicious-monster.com/downloads/DeliciousLibrary3.zip`

```
                      -----------------------------------
                     |  Welcome to Recipe Robot v0.0.3.  |
                      -----------------------------------
                                \   _[]_
                                 \  [oo]
                                   d-||-b
                                     ||
                                   _/  \_

Processing http://delicious-monster.com/downloads/DeliciousLibrary3.zip ...
Generating download recipe...
    ~/Library/AutoPkg/RecipeOverrides/DeliciousLibrary3.download.recipe
Generating munki recipe...
    ~/Library/AutoPkg/RecipeOverrides/DeliciousLibrary3.munki.recipe
Generating pkg recipe...
    ~/Library/AutoPkg/RecipeOverrides/DeliciousLibrary3.pkg.recipe
Generating install recipe...
    ~/Library/AutoPkg/RecipeOverrides/DeliciousLibrary3.install.recipe

You've now created 4 recipes with Recipe Robot. Well done!
```

If you use the `--verbose` argument, you'll get a little more information about what's going on:

```
                      -----------------------------------
                     |  Welcome to Recipe Robot v0.0.3.  |
                      -----------------------------------
                                \   _[]_
                                 \  [oo]
                                   d-||-b
                                     ||
                                   _/  \_

Processing http://delicious-monster.com/downloads/DeliciousLibrary3.zip ...
Input path looks like a download URL.
    Download URL is: http://delicious-monster.com/downloads/DeliciousLibrary3.zip
Getting download filename...
    Download filename is: DeliciousLibrary3.zip
Determining download format...
    Download format is zip
Downloading file for further inspection...
    Downloaded to /Users/elliot/Library/Caches/Recipe Robot/DeliciousLibrary3.zip
Verifying downloaded file format...
    Download format is zip
Validating app...
    App seems valid
Getting app name...
    App name is: Delicious Library 3
Getting bundle identifier...
    Bundle idenfitier is: com.delicious-monster.library3
Checking for a Sparkle feed...
    No Sparkle feed
Determining whether app was downloaded from the Mac App Store...
    App did not come from the App Store
Looking for version key...
    Version key is: CFBundleShortVersionString (3.3.5)
Looking for app icon...
    App icon is: /Users/elliot/Library/Caches/Recipe Robot/unpacked/Delicious Library 3.app/Contents/Resources/Delicious Library.icns
Getting app description from MacUpdate...
    Description: Import, browse and share your media.
Determining whether app is codesigned...
    Codesign status is: signed
    Codesign requirements are: anchor apple generic and identifier "com.delicious-monster.library3" and (certificate leaf[field.1.2.840.113635.100.6.1.9] /* exists */ or certificate 1[field.1.2.840.113635.100.6.2.6] /* exists */ and certificate leaf[field.1.2.840.113635.100.6.1.13] /* exists */ and certificate leaf[subject.OU] = RM6A3972U7)
Searching for existing AutoPkg recipes for "Delicious Library 3"...
    No results
Searching for existing AutoPkg recipes for "DeliciousLibrary3"...
    No results
Generating download recipe...
    ~/Library/AutoPkg/RecipeOverrides/DeliciousLibrary3.download.recipe
Generating munki recipe...
    ~/Library/AutoPkg/RecipeOverrides/DeliciousLibrary3.munki.recipe
Generating pkg recipe...
    ~/Library/AutoPkg/RecipeOverrides/DeliciousLibrary3.pkg.recipe
Generating install recipe...
    ~/Library/AutoPkg/RecipeOverrides/DeliciousLibrary3.install.recipe

You've now created 8 recipes with Recipe Robot. Round of applause for you!
```

It's fun to see the details, and very useful if anything goes wrong.


## Mac App Usage

The Mac app is still being built. Stay tuned!


## Tips

__A note about compatibility__

My goal is not to make Recipe Robot generate perfect recipes 100% of the time. There will certainly be apps that Recipe Robot chokes on, and some recipe types are more complex to generate than others. I hope Recipe Robot will make the process of generating _standard_ recipes for _simple_ apps much faster and more consistent. The recipes generated by Recipe Robot should serve as a platform that you can customize before using and sharing.

You may still need to make a recipe the old fashioned way, if the Robot comes up empty.

__A note about existing recipes__

AutoPkg recipe authors put a lot of work into the recipes they write, and it's important that we respect that by refraining from uploading duplicate recipes to GitHub.

To that end, Recipe Robot will not generate recipes that already exist in the wild. You can override this etiquette, but please only post a duplicate recipe to GitHub if it's applicable to a wide audience and significantly better than the original. Thanks!

__Things to tweak in Recipe Robot-produced recipes__

Each time Recipe Robot produces a batch of recipes for you, I suggest you check a few things before letting the recipes loose in the wild:

- The filename of the recipe and the NAME input variable are determined by the name of the app itself. Many apps are suffixed with a version number (e.g. "Delicious Library 3"), and that version number may not be desirable in all cases. You may need to remove the version number from the filename, recipe identifier(s), and description.

- Recipe Robot does its best at determining an app's description for use in Munki and JSS recipes. But it's far from perfect, and it will surprise you with false positives! Always double-check the description before running Munki and JSS recipes.

- You'll want to check the code signature verification included in download recipes created by Recipe Robot. Although it works great 99% of the time, occasionally you'll find that apps use obsolete "version 1" signatures. In those cases, you may want to modify or remove the code signature verification.


## Troubleshooting

- If at first you don't succeed, try try again! I usually enlist the following steps for creating recipes:
    1. Provide the app itself as input to Recipe Robot.
    2. If that doesn't work, go to the developer's website and see if they provide a static download link (usually ends with .zip or .dmg). Try using that.
    3. If that still doesn't work, maybe the app has a GitHub or SourceForge project page? Try providing that to Recipe Robot.

- Run again with `--verbose` when errors occur, and you'll usually see why. It's often because Recipe Robot couldn't determine how to download the app. As I said, the Robot won't work for all apps.

- If you get Python exceptions while using Recipe Robot, I invite you to [create an issue on GitHub](https://github.com/homebysix/recipe-robot/issues/new) so I can track the problem. Include full traceback plus whatever input (URL, path, etc) you provided when you ran Recipe Robot.


## Feedback

If you have any questions about Recipe Robot, get in touch with me on [Twitter](https://twitter.com/homebysix).
