# Recipe Robot Change Log

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](http://semver.org/).


## [Unreleased]

### Changed
- Only download and pkg recipe types are enabled by default on first run.


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

[Unreleased]: https://github.com/homebysix/recipe-robot/compare/v1.1.2...HEAD
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
