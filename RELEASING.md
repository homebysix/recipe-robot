# Releasing new versions of Recipe Robot

## Requirements

- [DropDMG](https://c-command.com/dropdmg/), with a configuration called "Recipe Robot" that has the proper layout and settings
- Xcode and command line tools
- Carthage (install using `brew install carthage`)

## Steps

1. Update frameworks with Carthage:

        cd ./app
        carthage update --platform macOS

1. Ensure both the `MARKETING_VERSION` variables in __app/Recipe Robot.xcodeproj/project.pbxproj__ have been updated.

1. Ensure the version in __scripts/recipe_robot_lib/tools.py__ has been updated.

1. Ensure the change log has been updated and reflects actual release date.

1. Merge development branch to main/master branch.

1. Run Recipe Robot unit tests and fix any errors. (See __scripts/test/README.md__ for detailed steps.)

1. (TEMPORARY) Use Xcode to build an archive of the signed app, upload to Apple for notarization, and export the notarized app to __build/Release/Recipe Robot.app__.

1. Build a release disk image:

        rm -fv build/RecipeRobot*.dmg
        dropdmg --config-name "Recipe Robot" --destination build/ "build/Release/Recipe Robot.app"
        autoload zmv
        zmv -v 'build/Recipe Robot (*).dmg' 'build/RecipeRobot-$1.dmg'
        open build/

1. Create new release on GitHub. Add notes from change log. Attach built disk image.

1. Trigger a GitHub Pages build, which updates the Sparkle feed ([using @huangyq23's method detailed here](https://www.yiqiu.me/2015/11/19/sparkle-update-on-github/)):

        git checkout gh-pages
        git commit --allow-empty -m "Trigger gh-pages build"
        git push
        git checkout master

1. Announce to [autopkg](https://macadmins.slack.com/archives/C056155B4) and other relevant channels, if desired.
