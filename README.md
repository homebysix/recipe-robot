![Recipe Robot](images/header.jpg)

__Table of contents__

<!-- MarkdownTOC autolink=true depth=3 bracket=round -->

- [Overview](#overview)
- [Project Status](#project-status)
- [Contributing Code](#contributing-code)

<!-- /MarkdownTOC -->

## Overview

I hope that Recipe Robot will become the easiest way to create AutoPkg recipes. It will consist of two components:

- __Python script(s)__ that takes an app or an existing AutoPkg recipe as input and generates AutoPkg recipes in various formats.

- A __native Mac app__ that puts a friendly face on the Python script and makes it as simple as dragging and dropping.

This two-pronged approach will allow AutoPkg novices to easily create recipes that follow community-accepted guidelines with the minimum amount of effort, and will still provide a command-line tool for more advanced AutoPkg users. Also, ensuring that all program logic is done in Python should hopefully foster community contribution to this project.

## Project Status

- [ ] __Python script__
    - [x] Detects app input
    - [ ] Validates app
    - [x] Detects Sparkle feed from Info.plist
    - [ ] Determines GitHub releases feed
    - [ ] Determines SourceForge releases feed
    - [x] Detects app name from Info.plist
    - [x] Detects recipe input
    - [ ] Validates usable recipe
    - [x] Detects type of recipe
    - [ ] Detects format of download
    - [ ] Detects app name from recipe
    - [x] Checks for existing AutoPkg recipes
    - [ ] Presents a list of available destination formats
    - [ ] References and modifies template recipe files
    - [ ] Creates a basic download recipe from Sparkle feed
    - [ ] Creates advanced download recipes ([see this article](https://www.afp548.com/2015/04/06/autopkg-download-recipe-decision-making-process/))
    - [ ] Creates a basic munki recipe from a download recipe
    - [ ] Creates a basic munki recipe from a pkg recipe
    - [ ] Creates a basic pkg recipe from a download recipe
    - [ ] Creates a basic jss recipe from a pkg recipe
    - [ ] Recipe format configuration options (identifier and recipe types)
- [ ] __Mac app__
    - [ ] Preferences window UI
    - [ ] File input UI (basic file picker)
    - [ ] File input UI (drag and drop)
    - [ ] Processing UI
    - [ ] Recipe format selection UI
    - [ ] Recipe output UI
    - [ ] Takes input from Python script
    - [ ] Writes output to file
    - [ ] Polish, bug fixes
    - [ ] Package, release, promote

## Contributing Code

I can't do this all myself, so I welcome contributions! Get in touch with me on [Twitter](https://twitter.com/homebysix), or just submit a PR if there's something you really want to tackle.

Rule of thumb: I'd like to get the features above working before spending too much time adding new features.
