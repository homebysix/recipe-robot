# Recipe Robot Change Log

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Added
- Sweet new icon!
- [Short video tutorials](https://www.youtube.com/playlist?list=PLK1ZziC_XFWoDnSYU3__WRQCRpXA2fhXq) for Recipe Robot are now available.
- We've started building unit tests for Recipe Robot, so we can minimize the number of bugs that find their way into future releaes.
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

[Unreleased]: https://github.com/homebysix/recipe-robot/compare/v0.2.2...HEAD
[0.2.2]: https://github.com/homebysix/recipe-robot/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/homebysix/recipe-robot/compare/v0.2.0...v0.2.1
