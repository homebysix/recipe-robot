# Recipe Robot Change Log

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Added
- If a dmg is supplied as input, Recipe Robot inspects the file metadata in order to detect possible download URLs (#81, thanks to @gregneagle).
- The script now displays a simple progress percentage during file downloads. (#24, #72)
- Added more [video tutorials](https://www.youtube.com/playlist?list=PLK1ZziC_XFWoDnSYU3__WRQCRpXA2fhXq)!

### Fixed
- Adjusted colors so that they'll be more readable on both bright and dark backgrounds. (#79)


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

[Unreleased]: https://github.com/homebysix/recipe-robot/compare/v1.0...HEAD
[1.0]: https://github.com/homebysix/recipe-robot/compare/v0.2.5...v1.0
[0.2.5]: https://github.com/homebysix/recipe-robot/compare/0.2.4...v0.2.5
[0.2.4]: https://github.com/homebysix/recipe-robot/compare/0.2.2...0.2.4
[0.2.2]: https://github.com/homebysix/recipe-robot/compare/v0.2.1...0.2.2
[0.2.1]: https://github.com/homebysix/recipe-robot/compare/v0.2.0...v0.2.1
