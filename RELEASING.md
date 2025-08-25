# Releasing new versions of Recipe Robot

## Requirements

- [DropDMG](https://c-command.com/dropdmg/), with a configuration called "Recipe Robot" that has the proper layout and settings
- Xcode and command line tools
- Carthage (install using `brew install carthage`)
- Apple Developer account must be active, and latest Apple Developer Program License Agreement accepted

## Steps

1. Update frameworks with Carthage:

        cd ./app
        carthage update --platform macOS

2. Ensure both the `MARKETING_VERSION` variables in __app/Recipe Robot.xcodeproj/project.pbxproj__ have been updated.

3. Ensure the version in __scripts/recipe_robot_lib/tools.py__ has been updated.

4. Ensure the change log has been updated and reflects actual release date.

5. Ensure copyright headers are updated, if desired.

6. Merge development branch to main/master branch.

7. Run Recipe Robot unit tests and fix any errors. (See __scripts/test/README.md__ for detailed steps. Optionally use `RUN_FUNCTIONAL_TESTS=true` to run lengthy functional tests.)

8. Open Xcode and choose __Product > Archive__.

9. Click __Distribute App > Direct Distribution > Distribute__. Wait for notarization to complete.

    > [!NOTE]
    > If upload fails, check that the Apple Developer agreements have been accepted.

10. Once ready, click __Export Notarized App__ and save to __build/Release/Recipe Robot.app__.

11. Build a release disk image:

        rm -fv build/RecipeRobot*.dmg
        dropdmg --config-name "Recipe Robot" --destination build/ "build/Release/Recipe Robot.app"
        autoload zmv
        zmv -v 'build/Recipe Robot (*).dmg' 'build/RecipeRobot-$1.dmg'
        open build/

12. Create new release on GitHub with title format `Recipe Robot X.X.X`. Set label format to `vX.X.X`. Add notes from change log. Attach built disk image.

13. Manually update `appcast.xml` on the `gh-pages` branch.

14. Announce to [autopkg](https://macadmins.slack.com/archives/C056155B4) and other relevant channels, if desired.

15. Create new `dev` branch.

16. Bump versions for development:

    - `MARKETING_VERSION` variables in __app/Recipe Robot.xcodeproj/project.pbxproj__

    - Version in __scripts/recipe_robot_lib/tools.py__
