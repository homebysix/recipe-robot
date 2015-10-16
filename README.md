![Recipe Robot](images/header.jpg)

__Table of contents__

<!-- MarkdownTOC autolink=true depth=3 bracket=round -->

- [Overview](#overview)
- [Python Script Usage](#python-script-usage)
- [Tips](#tips)
  - [Compatibility](#compatibility)
  - [Apps with existing AutoPkg recipes](#apps-with-existing-autopkg-recipes)
  - [App Store Apps](#app-store-apps)
- [Troubleshooting](#troubleshooting)
- [Feedback](#feedback)

<!-- /MarkdownTOC -->


## Overview

Recipe Robot will soon become the easiest way to create basic AutoPkg recipes. It will consist of two components:

- A __Python script__ that takes various types of input and automatically outputs AutoPkg recipes in various formats.

- A __native Mac app__ that puts a friendly face on the Python script and makes it as simple as dragging and dropping.

This two-pronged approach will allow AutoPkg novices to easily create recipes that follow community-accepted guidelines, and will still provide a command-line tool for more advanced AutoPkg users. Also, ensuring that all program logic is written in Python should hopefully encourage community contribution to this project.


## Python Script Usage

The Python script is under heavy development right now, but you're welcome to try it out if you want a preview of what Recipe Robot will do. __Use at your own risk,__ and always manually review the recipes that are created before running them.

Just open Terminal, `cd` to the scripts folder, then type:

```
recipe-robot <input>
```

For `<input>`, you can use one of several types of information:

- The path to a Mac app.
- The path to a zip, dmg, or pkg installer for a Mac app.
- The path to an app's Sparkle feed.
- The direct download URL for an app (which usually ends with .zip or .dmg).
- The GitHub, BitBucket, or SourceForge project URL for an app.

The first time Recipe Robot runs, you'll be prompted for some information. On subsequent runs, you can use the `--config` argument to force this prompt to return.

Here's what Recipe Robot looks like when it's working properly. The command I used was: `recipe-robot http://delicious-monster.com/downloads/DeliciousLibrary3.zip`

```
                      -----------------------------------
                     |  Welcome to Recipe Robot v0.0.6.  |
                      -----------------------------------
                                \   _[]_
                                 \  [oo]
                                   d-||-b
                                     ||
                                   _/  \_

Processing http://delicious-monster.com/downloads/DeliciousLibrary3.zip ...
Generating download recipe...
    ~/Library/AutoPkg/Recipe Robot output/Delicious Monster Software, LLC/DeliciousLibrary3.download.recipe
Generating munki recipe...
    ~/Library/AutoPkg/Recipe Robot output/Delicious Monster Software, LLC/Delicious Library 3.png
    ~/Library/AutoPkg/Recipe Robot output/Delicious Monster Software, LLC/DeliciousLibrary3.munki.recipe
Generating pkg recipe...
    ~/Library/AutoPkg/Recipe Robot output/Delicious Monster Software, LLC/DeliciousLibrary3.pkg.recipe
Generating install recipe...
    ~/Library/AutoPkg/Recipe Robot output/Delicious Monster Software, LLC/DeliciousLibrary3.install.recipe

You've now created 4 recipes with Recipe Robot. Well done!
```

If you use the `--verbose` argument, you'll get a little more information about what's going on:

```
                      -----------------------------------
                     |  Welcome to Recipe Robot v0.0.6.  |
                      -----------------------------------
                                \   _[]_
                                 \  [oo]
                                   d-||-b
                                     ||
                                   _/  \_

Processing http://delicious-monster.com/downloads/DeliciousLibrary3.zip ...
Input path looks like a download URL.
    Download URL is: http://delicious-monster.com/downloads/DeliciousLibrary3.zip
Downloading file for further inspection...
    Downloaded to ~/Library/Caches/Recipe Robot/DeliciousLibrary3.zip
Determining download format...
    Download format is zip
Validating app...
    App seems valid
Getting app name...
    App name is: Delicious Library 3
Getting bundle identifier...
    Bundle idenfitier is: com.delicious-monster.library3
Checking for a Sparkle feed...
    No Sparkle feed
Looking for version key...
    Version key is: CFBundleShortVersionString (3.3.5)
Looking for app icon...
    App icon is: ~/Library/Caches/Recipe Robot/unpacked/Delicious Library 3.app/Contents/Resources/Delicious Library.icns
Getting app description from MacUpdate...
    Description: Import, browse and share your media.
Determining whether app is codesigned...
    Codesign status is: signed
    Codesign requirements are: anchor apple generic and identifier "com.delicious-monster.library3" and (certificate leaf[field.1.2.840.113635.100.6.1.9] /* exists */ or certificate 1[field.1.2.840.113635.100.6.2.6] /* exists */ and certificate leaf[field.1.2.840.113635.100.6.1.13] /* exists */ and certificate leaf[subject.OU] = RM6A3972U7)
Searching for existing AutoPkg recipes for "Delicious Library 3"...
    No results
Searching for existing AutoPkg recipes for "DeliciousLibrary3"...
    No results
Determining application developer and codesign version...
    Developer: Delicious Monster Software, LLC
    Codesign version: 2
    Download format is zip
Generating download recipe...
    ~/Library/AutoPkg/Recipe Robot output/Delicious Monster Software, LLC/DeliciousLibrary3.download.recipe
Generating munki recipe...
    ~/Library/AutoPkg/Recipe Robot output/Delicious Monster Software, LLC/Delicious Library 3.png
    ~/Library/AutoPkg/Recipe Robot output/Delicious Monster Software, LLC/DeliciousLibrary3.munki.recipe
Generating pkg recipe...
    ~/Library/AutoPkg/Recipe Robot output/Delicious Monster Software, LLC/DeliciousLibrary3.pkg.recipe
Generating install recipe...
    ~/Library/AutoPkg/Recipe Robot output/Delicious Monster Software, LLC/DeliciousLibrary3.install.recipe

You've now created 4 recipes with Recipe Robot. Round of applause for you!
```

It's fun to see the details, and very useful in case anything goes wrong.


<!-- ## Mac App Usage -->


## Tips

### Compatibility

My goal is _not_ to make Recipe Robot generate perfect recipes 100% of the time. There will certainly be apps that Recipe Robot chokes on, and some recipe types are more complex to build than others. I hope Recipe Robot will make the process of writing _standard_ recipes for _simple_ apps much faster and more consistent. The recipes created by Recipe Robot should serve as a platform that you can customize before using and sharing.

You may still need to make a recipe the old fashioned way, if the Robot comes up empty.

### Apps with existing AutoPkg recipes

By default, Recipe Robot does not generate recipes for an app if any AutoPkg recipes already exist for that app. This is a design choice we made after careful consideration, for two reasons:

1. It's difficult to parse a ParentRecipe and determine exactly which processors will be needed and which file paths we can rely on. Your brain is still the best tool for that, for now.

2. Many AutoPkg recipe authors put a lot of work into the recipes they write, and it's important that we respect that by refraining from uploading duplicate recipes to GitHub.

You can override this etiquette, but please only post a duplicate set of recipes to GitHub if they meet these guidelines:

- applicable to a wide audience
- better than the original in at least one significant way
- a note in the description clarifies how your recipe differs from the existing recipe (see [this example](https://github.com/autopkg/homebysix-recipes/blob/b3e30cf859e983ff1cf6ad6a053917d17434567f/ObjectiveDevelopment/LaunchBar.download.recipe#L10-L13))

Thank you!

__Things to tweak in Recipe Robot-produced recipes__

Each time Recipe Robot produces a batch of recipes for you, I suggest you check a few things before letting the recipes loose in the wild:

- The filename of the recipe and the `NAME` input variable are determined by the name of the app itself. Many apps are suffixed with a version number (e.g. "Delicious Library 3"), and that version number may not be desirable in all cases. You may need to remove the version number from the filename, recipe identifiers, and `ParentRecipe` keys.

- Recipe Robot doesn't currently know the difference between an app installer and a bona fide app. Therefore, certain apps may produce recipes that simply install the app's installer instead of the app itself. When this happens, it's usually pretty obvious because you'll end up with a set of recipes called, for example, `ChronoSync Installer.___.recipe` instead of `ChronoSync.___.recipe`. The download recipe is probably usable, but the others will need significant customization.

- Recipe Robot does its best at determining an app's description for use in Munki and JSS recipes. But it's far from perfect, and it will surprise you with false positives! Always double-check the description before running Munki and JSS recipes or uploading them to GitHub.

- It's fine to use a version-specific URL as input, but be careful that it doesn't result in download recipes that depend upon it. Such recipes will not serve the purpose of downloading the latest version using AutoPkg.

    You may need to try again with a different URL (preferably one like `http://foo-app.com/latest` or `http://downloads.pretendco.com/Foo.zip` which doesn't point to a specific version).

    Or you may want to explore using [URLTextSearcher](https://github.com/autopkg/autopkg/wiki/Processor-URLTextSearcher) to determine the latest URL by inspecting the source of the developer's download page.

### App Store Apps

If you provide Recipe Robot with the path to an app that came from the Mac App Store, it will create an override for use with Nick McSpadden's [AppStoreApp recipes](https://github.com/autopkg/nmcspadden-recipes#appstoreapp-recipe). Please see the details in his README for requirements necessary to use these overrides.


## Troubleshooting

- If at first you don't succeed, try try again! I usually enlist the following steps for creating recipes:

    1. Provide the app itself as input to Recipe Robot.
    2. If that doesn't work, go to the developer's website and see if they provide a static download link (usually ends with .zip or .dmg). Try using that.
    3. If that still doesn't work, maybe the app has a GitHub or SourceForge project page? Try providing that to Recipe Robot.
    4. Still no luck? Write a recipe from scratch like the good old days.

- Run again with `--verbose` when errors occur, and you'll usually see why. It's often because Recipe Robot couldn't determine how to download the app. As I said, the Robot won't work for all apps.

- If you get Python exceptions while using Recipe Robot, I invite you to [create an issue on GitHub](https://github.com/homebysix/recipe-robot/issues/new) so I can track the problem. Include full traceback plus whatever input (URL, path, etc) you provided when you ran Recipe Robot.

- Due to reasons I'm still learning about, Recipe Robot (and AutoPkg) don't work with certain kinds of SSL. If you see `SSLV3_ALERT_HANDSHAKE_FAILURE` in the traceback message, see the first troubleshooting point above. If none of those steps work, you might be out of luck.


## Feedback

Recipe Robot hasn't been formally released yet, so let's keep this between you and me for now. :-)

