# Recipe Robot Change Log

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](http://semver.org/).


## [Unreleased]

### Added
- Recipe Robot now automatically switches download URLs and Sparkle feeds from HTTP to HTTPS, if possible. (#92)

### Changed
- Uses HTTPS for all SourceForge API calls.
- General readability and formatting improvements to Python code.

### Fixed
- Handles unicode characters in MacUpdate app descriptions.
- Handles missing "where from" metadata in downloaded files more gracefully.


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

### Changes
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

[Unreleased]: https://github.com/homebysix/recipe-robot/compare/v1.0.3...HEAD
[1.0.3]: https://github.com/homebysix/recipe-robot/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/homebysix/recipe-robot/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/homebysix/recipe-robot/compare/v1.0...v1.0.1
[1.0]: https://github.com/homebysix/recipe-robot/compare/v0.2.5...v1.0
[0.2.5]: https://github.com/homebysix/recipe-robot/compare/0.2.4...v0.2.5
[0.2.4]: https://github.com/homebysix/recipe-robot/compare/0.2.2...0.2.4
[0.2.2]: https://github.com/homebysix/recipe-robot/compare/v0.2.1...0.2.2
[0.2.1]: https://github.com/homebysix/recipe-robot/compare/v0.2.0...v0.2.1
