# Recipe Robot Change Log

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](http://semver.org/).

<!-- markdownlint-disable MD024 -->

## Unreleased

### Added

- Recipe Robot app now displays a warning on launch if AutoPkg isn't installed. (#184)
- Automated macOS 14 and 15 Xcode tests on GitHub actions.
- Some badges on readme, but only good ones.
- Unit tests for SourceForge and BareBones feed processing.

### Changed

- If multiple GitHub assets are available, prefer installers, then disk images, then archives. (#205)
- Prefer `SUFeedEntryDownloadURL` key from BareBones software update feeds, if available. (#194)
- Generally better download error handling when retrieving xml or json.
- Updated included version of Sparkle framework.
- Switched from `os.path` to `Pathlib.path` in codebase.

## [2.4.0] - 2025-08-24

### Fixed

- Fixed issue with app description parsing that was causing most descriptions to show "Popular multimedia player."
- Fixed redundant versioning caused by Recipe Robot's treatment of Sparkle feeds being out of date with SparkleUpdateInfoProvider. (#207)
- Restored icon extraction when Jamf recipes (but not Munki) are selected in user preferences. (#203)
- Fixed an EOFError that could happen if the `RecipeCreateLocation` doesn't exist. (#185)

### Changed

- Updated app to use latest version of Sparkle self-updater framework.
- Converted Python tests from nose to unittest and configured for code coverage.
- Made functional tests optional during unittest runs. Specify `RUN_FUNCTIONAL_TESTS=true` to include them.
- Built out Swift unit testing for the Mac app.
- Improved company suffix stripping (e.g. Inc, LLC, Ltd).
- Updated Python syntax to 3.10 using `pyupgrade`.
- Added `s.r.o.` to corporate suffixes able to be removed.
- Data structure adjustments to recipe generation functions.

### Removed

- Removed support for pulling app descriptions from now-inoperative Informer site

## [2.3.2] - 2025-02-08

### Fixed

- Resolved an issue with Sparkle feed parsing that could cause Recipe Robot to insert a static download URL in URLDownloader if the feed provided a version at the item level instead of the enclosure level. (#206)

## [2.3.1] - 2023-10-19

### Fixed

- Fixed an issue with Recipe Robot's Sparkle update feed that caused "you're up to date" to appear even when the app wasn't the newest version. Resolved by publishing new automation to the [gh-pages](https://github.com/homebysix/recipe-robot/tree/gh-pages) branch of the repo. (Although this is listed as a fix for 2.3.1, it should actually resolve the issue for all previous versions of Recipe Robot.)
- Jamf pkg upload recipes that use a parent download recipe that retrieves a package file won't fail (related to the behavior change below, #193).
- Fixed a very rare issue in which Recipe Robot is not able to remove its cache folder after a pkg is unpacked that contains files that aren't user-writeable.
- Adjusted SourceForge download URL search process and updated SF RSS parsing logic. Added support for detection of SourceForge `/project/` URLs, which apparently coexist with `/projects/` URLs.
- Made adjustments to functional tests for upcoming AutoPkg 3 recipe map compatibility.

### Changed

- Recipe Robot no longer skips creating 'pkg' type recipes if the download is already in pkg format. Instead, it creates a recipe with a `PkgCopier` process (and potentially other processes if necessary for versioning). (#193)

## [2.3.0] - 2023-10-16

### Added

- Recipe Robot is now able to create yaml recipes. To use this feature, run `--configure` and select `yaml` as the recipe format. (Or run `defaults write com.elliotjordan.recipe-robot RecipeFormat "yaml"`). The app does not yet have a method for selecting this preference.
- Now "jamf" recipes that leverage Graham Pugh's JamfPackageUploader processor can be created. This feature is currently limited to package-upload-only type recipes. (No creation of groups, policies, scripts, or other objects.) (#187)
- Redeveloped existing recipe detection using the automated AutoPkg [recipe index](https://github.com/autopkg/index). Recipe Robot will use this method until the `autopkg search` results become reliable again.
- Local `file://` URLs are now supported input paths (but be aware that these may not be desirable for providing ongoing updates via AutoPkg, unless you have automation updating the local file).
- New dedicated handler for Bare Bones update feeds, which are similar to Sparkle feeds but not the same. (#194)
- Added three more app description sources, increasing the chance that Recipe Robot will pre-fill your Munki or Jamf recipes with useful descriptions for you to customize.
- Added more post-recipe-creation affirmations, because why not.

### Fixed

- Better handling of disk images that contain packages. (#188)
- Recipe Robot better handles downloaded payloads that contain the contents of an app bundle, but lack the enclosing bundle itself. (Thanks to @andrewzierkel for #195)
- Prevented app window from expanding too much horizontally when processing extremely long filename or URL inputs.
- Fixed incorrect `[0m` that terminated script output in app.
- Fixed MacUpdate description pattern matching.
- Better handling of URLs with unquoted spaces. (#197)
- Improved detection of less obvious Sparkle feeds that might at first glance appear to be download URLs.
- More gracefully handle Sparkle and Bare Bones feeds with no usable items or enclosure URLs.

### Changed

- Recipe Robot app finally supports dark mode in script output box!
- Updated [Sparkle](https://github.com/sparkle-project/Sparkle/) framework to 2.5.1.
- If existing recipes are found, output a hint that using `--ignore-existing` can create new recipes anyway.
- Use zero-width space for script output contents placeholder, which ensures that "Processing" on the first line aligns with the left side.

### Removed

- Removed support for generation of "jss" style recipes, which leverage the deprecated [Python-JSS](https://github.com/jssimporter/python-jss) module. Please [switch to JamfUploader type recipes](https://grahamrpugh.com/2022/02/16/jssimporter-jamf-pro-api-token-auth.html) instead.
- Dropped AlternativeTo as a description source.

## [2.2.0] - 2020-12-13

### Added

- Recipe Robot now incorporates [Sparkle](https://sparkle-project.org) for keeping itself up to date. (#143)
- The app is now built as a universal binary (however no testing on Macs with Apple Silicon has been done yet).
- Verbose output now includes HTTP content-type and copying from disk images.

### Fixed

- Improved code signing authorities parsing, which should allow Recipe Robot to capture developer names and team identifiers in some situations where it would not previously.
- Fixed a bug that would prevent using Sparkle URLs hosted on updates.devmate.com as input.
- Gracefully handle missing file errors during installer payload inspection.
- Slightly more resilient processing of downloaded files when the file format is unknown.

### Removed

- Removed FoundationPlist since Recipe Robot no longer depends on it.

## [2.1.0] - 2020-11-14

### Added

- Recipe Robot is now codesigned with a shiny new developer certificate and notarized!
- Unit tests for `curl` related functions that will help detect and prevent release of bugs.

### Fixed

- Fixed a bug that would fail recipe generation if a `expected_authority_names` list is used for `CodeSignatureVerifier`.
- Resolved an uncaught exception resulting from the `RecipeIdentifierPrefix` or `RecipeCreateLocation` preferences being unset. (#179)
- Corrected minimum system version back to 10.13. (#180)

## [2.0.0] - 2020-11-03

### Added

- Full Python 3 support, which makes Recipe Robot compatible with (and require) AutoPkg 2. Big thanks to [@sheagcraig](https://github.com/sheagcraig) for fixing a particularly sticky bug involving string encoding. (#156, #160, #163)
- As part of Python 3 transition, rewrote significant portions of Recipe Robot to use `curl` instead of Python's urllib. This adds flexibility and mimics AutoPkg's behavior, but may result in changes in behavior from Recipe Robot 1.x.
- New disk image build tool and layout.
- The `recipe-robot` script now supports the creation of "jss-upload" type recipes, which imports a package into Jamf Pro but does not create any policies or groups. (#153)
- Now able to build recipes for macOS screen saver (.saver) bundles.
- Recipe Robot now does more thorough pre-checking of URLs: attempts to use HTTPS instead of HTTP when possible, and tries to add a widely used user-agent if a 403 error is encountered.
- Added CodeQL scanning to GitHub repo.
- Added Sparkle shortVersionString to verbose output. (#173)
- Added code signature team identifier verbose output. (#174)

### Changed

- Recipe Robot no longer assigns AutoPkg input variables for `DOWNLOAD_URL`, `SPARKLE_FEED_URL`, `GITHUB_REPO`, and `BUNDLE_ID`. Instead, it hard-codes these values into the appropriate processor arguments. [@jazzace](https://github.com/jazzace) nicely summarizes the benefit of this change [here](https://youtu.be/BI10WWrgG2A?t=2620).
- Added detail to the `--configure` option that clarifies that following the official "jss-recipes" style format is unnecessary unless you're contributing to [jss-recipes](https://www.github.com/autopkg/jss-recipes).
- Recipe Robot script `--configure` option now treats pressing Return the same as pressing "S" to save the list of preferred recipe types, to align with the behavior of other configuration options.
- Various minor adjustments to continue preparing for Python 3 compatibility.
- Cleaned up Swift codebase using `swiftlint`.
- More robust Sparkle feed processing. (#150, #173)

### Fixed

- Resolved an issue that resulted in preferences unrelated to Recipe Robot being saved into the Recipe Robot preference file.
- Updated regular expression used to grab app descriptions from MacUpdate.
- Fixed an issue that would cause certain GitHub URLs to be parsed incorrectly.
- Fixed a bug that occurred when checking for existing recipes using AutoPkg 2. (#171)
- Resolved a first-run issue with reading empty preference values.
- Fixed an issue that could cause a disk to fill up with recursive links. (#158)
- Caught an error that resulted from neglecting to cast certain lists before writing to recipe plist.
- Better handle download file inputs that are lacking `kMDItemWhereFroms` extended attributes.
- Worked around an issue preventing real-time script output from being displayed in the app by shelling out to `echo` while running in app mode. (#169, #170)

### Removed

- Removed internal support for piped subprocess commands, previously deprecated in v1.2.0.
- Temporarily removed 403 error detection (usually due to rate-limiting) for BitBucket, GitHub, and SourceForge API calls.
- Removed all calls to FoundationPlist in support of Python 3 transition. (Left FoundationPlist itself included in source, but will remove in a future release.)

### Known Issues

- On macOS 10.14 (and possibly earlier) an incorrect "certificate has expired" warning may appear in the output. (#165)
- The "jss-upload" type is not addressable yet in the Recipe Robot app, only in the script.
- Because Recipe Robot is now using plistlib instead of FoundationPlist, it's likely that some non-standard developer plist files may not successfully parse. This is because plistlib is stricter than FoundationPlist, and the same issue applies to AutoPkg itself (see [autopkg#618](https://github.com/autopkg/autopkg/issues/618) for an example).

## [1.2.1] - 2019-12-21

### Fixed

- Resolved Xcode signing issue that resulted in "damaged" warning upon launching Recipe Robot 1.2.0. (#154)

### Changed

- Various automatic syntax updates to align with Swift 5.

## [1.2.0] - 2019-12-15

### Known Issue

- Issue with Xcode signing may result in Gatekeeper showing "app is damaged" warning upon launch. Fixed in v1.2.1.

### Added

- Recipe Robot can now create recipes for basic non-app bundles (e.g. prefpane, plugin) contained in zip or dmg downloads.
- A warning will be displayed if the "content-type" header of downloaded files seems unusual.
- A warning will be displayed if a reliable version could not be determined (specifically from unsigned apps hosted by SourceForge). (#144)
- A warning will be displayed if an installer app is detected (e.g. "Install Hazel.app").
- Issue templates, Apache 2.0 license, and code of conduct added to GitHub project.
- Recipe Robot warns if a code signing requirements is unnecessarily loose (e.g. `anchor trusted`).

### Changed

- Only download and pkg recipe types are enabled by default on first run.
- Display recipe types in specified order when displaying configuration options. (#67)
- Made Recipe Robot less likely to give "user-agent" related warnings unnecessarily.

### Fixed

- Resolved a minor bug in which Recipe Robot would incorrectly treat a zip file as a tgz file.
- Resolved an issue with SourceForge file regex. (#144)
- Fixed rounding download progress to nearest 10% in app output.

### Removed

- Removed internal support for piped commands, in order to simplify shell-out process. Should have no effect on functionality.

## [1.1.2] - 2019-02-24

### Changed

- Recipe Robot will not add generically-named "Installer" or "Uninstaller" apps to the list of blocking applications in Munki recipes.
- Sparkle download URLs are now collected even if there is no version provided in the Sparkle feed. (#134)
- Recipe Robot now exits with an error if the /usr/local/bin/autopkg symlink is not present. (#134)
- A few Python formatting changes to prepare for eventual adoption of an autoformatter.

### Fixed

- Resolved a bug that would cause certain URL types not to be recognized properly. (#136)
- Fixed a bug that prevented expansion of tgz files. (#134)
- Squashed a meta-error caused by failed AutoPkg searches for existing recipes.
- Used better math to ensure first-time users will see their congratulations message.

### Removed

- The `--github-token` flag is now deprecated. Recipe Robot will automatically use the AutoPkg GitHub token file at ~/.autopkg_gh_token, if it exists.

## [1.1.1] - 2019-02-15

### Added

- Recipe Robot now uses the AutoPkg GitHub token file at ~/.autopkg_gh_token, if it exists. This can help you avoid rate limiting if you're creating many GitHub recipes in a short time. (#18)
- You can now use the `--configure` flag to access the Recipe Robot preferences setup in the Python script, in addition to the existing `-c` and `--config` flags.
- The Python script preferences setup now prompts you to set the new `StripDeveloperSuffixes` setting.

### Fixed

- Resolved a bug that would cause the `developer` key to be an array instead of a string in generated Munki recipes. (#141)

## [1.1.0] - 2019-02-12

### Added

- Recipe Robot now does a much better job at parsing package payloads! It can locate apps within packages, determine which of multiple apps is the "real" one, and even pass through code signing and payload unpacking information to the appropriate AutoPkg processors. Round of applause all around. (#27)
- Able to detect and use DevMate update feeds. (#129, thanks to [@macprince](https://github.com/macprince))
- More intelligent GitHub release searching. If multiple supported formats exist, Recipe Robot will generally prefer dmg first, then zip, and finally pkg. (#127)
- Automatically uses `asset_regex` in GitHubReleasesInfoProvider if it is needed.
- Uses AlternativeTo as a second source for app descriptions, if the description can't be found on MacUpdate.
- Optional `StripDeveloperSuffixes` preference, which automatically removes company name suffixes like "Inc" and "Ltd" from developer names.

### Changed

- The Recipe Robot app now requires macOS 10.13 or higher. (If you have an older version of macOS, you should be able to continue using the Python script.)
- App code base upgraded from Swift 2.3 to 4.2. (#139, HUGE thanks to [@olofhellman](https://github.com/olofhellman))
- A warning is printed if a GitHub or BitBucket link is provided as input, and the link points directly to a download file. Recipe Robot parses the link as a project repository (and looks for other release assets), but there may be some cases where this isn't the right thing to do (e.g. a project that contains releases for multiple apps) (#119).
- A warning is printed if a download produces HTML content instead of an actual file. This is common if a moved asset now produces a 404 error.
- Dropbox links that end in `?dl=0` are changed to `?dl=1` to force download of the file.
- Apps that lack bundle identifiers no longer result in a fatal error, just a warning.
- Read me image optimization. (#126, thanks to [@keeleysam](https://github.com/keeleysam))

### Fixed

- Fixed regex used to match MacUpdate descriptions.
- Blocking applications were not being added properly to Munki recipes for apps based on pkg file sources. That should be fixed now.

## [1.0.5] - 2017-01-27

### Added

- Uses new [AppPkgCreator](https://github.com/autopkg/autopkg/wiki/Processor-AppPkgCreator) processor, which greatly simplifies the process of creating a pkg from an app.

### Changed

- Updated app code to comply with Swift 2.3 syntax and Xcode 8.2 recommendations.
- `MinimumVersion` of AutoPkg on generated recipes is now 1.0.0, in order to support the new AppPkgCreator processor.
- Simplified the path that apps are unzipped to, since PkgCreator is no longer needed.
- Changed remaining `%NAME%` references to hard-coded app name where a path is required.

### Fixed

- Better handles apps where the filename of the app differs from the display name of the app.
- Improved performance and reliability of HTTPS URL validation.

## [1.0.4] - 2016-10-13

### Added

- Recipe Robot now automatically switches download URLs and Sparkle feeds from HTTP to HTTPS, if possible. (#92)
- Download progress indication is now displayed in the app. (#72)
- New `--skip-icon` command-line flag skips creation of PNG file for use as app icon in Munki/Casper.

### Changed

- Uses HTTPS for all SourceForge API calls.
- General readability and formatting improvements to Python code.
- Now references SourceForgeURLProvider as a shared processor rather than copying it to the output folder.
- Download progress percentage indicator updates in near-realtime.
- Streamlined the reminders you get when a required repo isn't present on disk.

### Fixed

- Handles unicode characters in MacUpdate app descriptions.
- Handles missing "where from" metadata in downloaded files more gracefully.
- Better compatibility with other terminal apps (e.g. PuTTY). (#108)

## [1.0.3] - 2016-08-25

### Added

- Now detects and warns when using URLs that contain `Expires` or `AWSAccessKeyId` parameters. In the case of Amazon Web Services, these URLs are not permanent and therefore not useful for creating AutoPkg recipes. (#97)
- Recipe Robot now complains if a Sparkle feed is not using HTTPS, although this does not prevent recipe creation. (#92)
- Outputs useful hints for people who want to test Recipe Robot by creating recipes for Recipe Robot.

### Fixed

- Corrected the FileWaveImporter processor identifier path used by FileWave recipes. (#104)
- Corrected the `fw_import_source` path referenced by FileWave recipes. (#104, thanks to [@cv-rao](https://github.com/cv-rao))
- Fixed a bug that prevented detection of existing recipes when the app name contained a space.

### Changed

- Clarified and improved a few error and warning messages.
- Recipe Robot will now use the actual app name for CodeSignatureVerifier, rather than using `%NAME%`. This should allow administrators to override the name without breaking code signature verification. (thanks to [@gregneagle](https://github.com/gregneagle) and [@chilcote](https://github.com/chilcote))
- Uses HTTPS to check MacUpdate for app description.

## [1.0.2] - 2016-03-23

### Added

- Added support for LANrev recipe type.
- Better support of disk images where the target app lives in an enclosed folder. (#90)

### Changed

- `MinimumVersion` of AutoPkg on generated recipes is now 0.6.1.
- Minor typo fixes, standardizations, and semi-obsessive tweaks.

### Removed

- Removed ability to create Absolute Manage recipe type. (Use LANrev instead.)

## [1.0.1] - 2015-12-28

### Added

- If a dmg is supplied as input, Recipe Robot inspects the file metadata in order to detect possible download URLs (#81, thanks to @gregneagle).
- The script now displays a simple progress percentage during file downloads. (#24, #72)
- Added more [video tutorials](https://www.youtube.com/playlist?list=PLK1ZziC_XFWoDnSYU3__WRQCRpXA2fhXq)!

### Fixed

- Adjusted colors so that they'll be more readable on both bright and dark backgrounds. (#79)

### Changed

- Now uses NSUserDefaults for preference handling. (#80)

## [1.0] - 2015-11-17

### Changed

- Put extra polish on things for MacBrained introduction demo.
- App now validates the path specified is a valid directory for recipe locations, and DS Packages.
- UI elements in preferences are hidden/shown only when required. (#69)
- Updated screenshots and demo animations in readme file.

## [0.2.5] - 2015-11-13

### Added

- Hooray! The Recipe Robot app can now accept URLs as input, just like the script.

### Changed

- Build number now tracks the Git commit count.
- Default preference value uses the existing value whenever possible. (#68)
- Updated URL of FileWave recipe repository.
- The Recipe Robot script now prints a debug message about `cfprefsd` after modifying the preference files directly. This is a stopgap measure until we switch to better handling of preferences. (#70)
- When you create AppStoreApp recipes, Recipe Robot only nags you once about adding Nick's repo and installing pyasn1.

### Fixed

- Fixed a bug that caused the app to display a "can't be found" error when clicking on the __Reveal Recipes__ button. (#60)
- Characters related to ANSI colors no longer appear in the app output.
- Resolved issue that prevented creation of AppStoreApp recipes.
- Recipe Robot handles curly quotes in app descriptions better now.
- Fixed an error that could occur when writing a jss recipe with a missing preference key.
- Spelling fixes, because we care!

### Removed

- Removed unused MacUpdate description scraper that was simpler but had dependencies.

## [0.2.4] - 2015-11-11

### Added

- Sweet new icon!
- [Short video tutorials](https://www.youtube.com/playlist?list=PLK1ZziC_XFWoDnSYU3__WRQCRpXA2fhXq) for Recipe Robot are now available.
- We've started building unit tests for Recipe Robot, so we can minimize the number of bugs that find their way into future releases.
- Added requirements to readme.

### Changed

- Default recipe identifier is now based on your local username. (#63)
- Significant simplification and refactoring of the recipe generation code.

### Fixed

- A few typo fixes.

## [0.2.2] - 2015-11-06

### Fixed

- Fixed an issue where the script output doesn't flush when run via the app.

## [0.2.1] - 2015-11-06

### Added

- Prefs sheet now appears by default on first launch.
- Help menu now opens README.md in default web browser. (#57)
- Added license header to each source file.

### Changed

- The app now displays the raw script output, including all warnings, reminders, and errors.
- Selecting a given recipe type in the preferences window (or `--config` prompts) now automatically selects its required parent recipe types.
- Changed readme to point to the version of `recipe-robot` Python script embedded in the Recipe Robot app.
- Code simplification and refactoring.

### Fixed

- Adjusted layout of Mac app.

## 0.2.0 - 2015-10-30

- Initial public release of Recipe Robot (beta).

[Unreleased]: https://github.com/homebysix/recipe-robot/compare/v2.4.0...HEAD
[2.4.0]: https://github.com/homebysix/recipe-robot/compare/v2.3.2...v2.4.0
[2.3.2]: https://github.com/homebysix/recipe-robot/compare/v2.3.1...v2.3.2
[2.3.1]: https://github.com/homebysix/recipe-robot/compare/v2.3.0...v2.3.1
[2.3.0]: https://github.com/homebysix/recipe-robot/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/homebysix/recipe-robot/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/homebysix/recipe-robot/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/homebysix/recipe-robot/compare/v1.2.1...v2.0.0
[1.2.1]: https://github.com/homebysix/recipe-robot/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/homebysix/recipe-robot/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/homebysix/recipe-robot/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/homebysix/recipe-robot/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/homebysix/recipe-robot/compare/v1.0.5...v1.1.0
[1.0.5]: https://github.com/homebysix/recipe-robot/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/homebysix/recipe-robot/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/homebysix/recipe-robot/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/homebysix/recipe-robot/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/homebysix/recipe-robot/compare/v1.0...v1.0.1
[1.0]: https://github.com/homebysix/recipe-robot/compare/v0.2.5...v1.0
[0.2.5]: https://github.com/homebysix/recipe-robot/compare/0.2.4...v0.2.5
[0.2.4]: https://github.com/homebysix/recipe-robot/compare/0.2.2...0.2.4
[0.2.2]: https://github.com/homebysix/recipe-robot/compare/v0.2.1...0.2.2
[0.2.1]: https://github.com/homebysix/recipe-robot/compare/v0.2.0...v0.2.1
