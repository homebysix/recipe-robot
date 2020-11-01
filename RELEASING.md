# Releasing new versions of Recipe Robot

## Requirements

- [DropDMG](https://c-command.com/dropdmg/), with a configuration called "Recipe Robot" that has the proper layout and settings
- Xcode and command line tools

## Steps

1. Update frameworks with Carthage:

        cd ./app
        carthage update --platform macOS

1. Ensure both the `MARKETING_VERSION` variables in __app/Recipe Robot.xcodeproj/project.pbxproj__ have been updated.

1. Ensure the version in __scripts/recipe_robot_lib/tools.py__ has been updated.

1. Ensure the change log has been updated and reflects actual release date.

1. Merge development branch to main/master branch.

1. Run Recipe Robot unit tests and fix any errors. (See __scripts/test/README.md__ for detailed steps.)

1. Build a new version of the Recipe Robot app:

        /usr/bin/xcodebuild clean -workspace "Recipe Robot.xcworkspace" -scheme "Recipe Robot - Release"
        /usr/bin/xcodebuild build -workspace "Recipe Robot.xcworkspace" -scheme "Recipe Robot - Release" OBJROOT=$(pwd)/build SYMROOT=$(pwd)/build

1. Build a release disk image:

        dropdmg --config-name "Recipe Robot" --destination build/ "build/Release/Recipe Robot.app"
        open build/

1. Create new release on GitHub. Add notes from change log. Attach built disk image.

1. TODO: Update Sparkle appcast using `gh-pages` branch.

1. Announce to [autopkg](https://macadmins.slack.com/archives/C056155B4) and other relevant channels, if desired.
