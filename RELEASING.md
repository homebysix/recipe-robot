# Releasing new versions of Recipe Robot

## Requirements

- [DropDMG](https://c-command.com/dropdmg/), with a configuration called "Recipe Robot" that has the proper layout and settings
- Xcode and command line tools
- Carthage (install using `brew install carthage`)

## Steps

1. Update frameworks with Carthage:

        cd ./app
        carthage update --platform macOS

2. Ensure both the `MARKETING_VERSION` variables in __app/Recipe Robot.xcodeproj/project.pbxproj__ have been updated.

3. Ensure the version in __scripts/recipe_robot_lib/tools.py__ has been updated.

4. Ensure the change log has been updated and reflects actual release date.

5. Merge development branch to main/master branch.

6. Run Recipe Robot unit tests and fix any errors. (See __scripts/test/README.md__ for detailed steps.)

7. Open Xcode and choose __Product > Archive__.

8. Click __Distribute App > Developer ID > Next > Upload__. Wait for notarization to complete.

9. Once ready, click __Export Notarized App__ and save to __build/Release/Recipe Robot.app__.

10. Build a release disk image:

        rm -fv build/RecipeRobot*.dmg
        dropdmg --config-name "Recipe Robot" --destination build/ "build/Release/Recipe Robot.app"
        autoload zmv
        zmv -v 'build/Recipe Robot (*).dmg' 'build/RecipeRobot-$1.dmg'
        open build/

11. Create new release on GitHub. Add notes from change log. Attach built disk image.

12. Trigger a GitHub Pages build, which updates the Sparkle feed ([using @huangyq23's method detailed here](https://www.yiqiu.me/2015/11/19/sparkle-update-on-github/)):

        git checkout gh-pages
        git commit --allow-empty -m "Trigger gh-pages build"
        git push
        git checkout master

13. Announce to [autopkg](https://macadmins.slack.com/archives/C056155B4) and other relevant channels, if desired.

14. Create new `dev` branch.

15. Bump versions for development:

    - `MARKETING_VERSION` variables in __app/Recipe Robot.xcodeproj/project.pbxproj__

    - Version in __scripts/recipe_robot_lib/tools.py__
