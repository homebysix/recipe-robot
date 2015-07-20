#!/usr/bin/env python

# Recipe Robot
# Copyright 2015 Elliot Jordan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.

'''
SCRIPT LOGIC
Also see: https://www.afp548.com/2015/04/06/autopkg-download-recipe-decision-making-process/

if input is valid .app (validate_input)
    search for existing recipes (autopkg_search)
        if NSURLFeed exists in Info.plist
            if NSURLFeed is a valid Sparkle feed
                add .download to the list of available recipes
            if bundle identifier exists on a GitHub project
                add .download (with GitHubReleasesProvider) to the list of available recipes
            if bundle identifier exists on a SourceForge project
                add .download (with SourceForgeReleasesProvider) to the list of available recipes

if input is valid recipe (validate_input)
    if recipe is .download
        if result of recipe is .zip or .tar or .tgz etc
            add .pkg (with Unarchiver processor) to the list of available recipes
        if result of recipe is .dmg
            add .pkg (with AppDmgVersioner process) to the list of available recipes
        if result of recipe is .pkg
            add .jss to the list of available recipes
    if recipe is .pkg
        add .jss to the list of available recipes
    else
        "sorry, we don't understand this recipe yet. but we're learning fast." and quit
    else
        "sorry, that's not valid input. try dragging on an app or a recipe." and quit

present user with list of recipe options, minus the existing autopkg search results
after user selects, then generate recipes
'''


def validate_input():
    '''
    Checks to ensure the input .app or .recipe is valid and usable.
    '''
    print "Validating input..."
    # do stuff
    return True


def autopkg_search():
    '''
    Searches for existing AutoPkg recipes that match the input.
    '''
    print "Searching for existing AutoPkg recipes..."
    # do stuff
    # return list of existing recipes


def main():
    print "I'm just pseudo-code for now."

    if validate_input() == True:
        print "Valid input."
    else:
        print "Invalid input."

    autopkg_search()


if __name__ == '__main__':
    main()
