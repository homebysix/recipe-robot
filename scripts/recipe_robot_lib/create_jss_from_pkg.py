#!/usr/bin/python
# This Python file uses the following encoding: utf-8

# Recipe Robot
# Copyright 2015 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
create_jss_from_pkg.py

Given a valid pkg recipe as input, this script generates a jss recipe that
uses the pkg recipe as a parent.

The resulting jss recipe will conform to the jss-recipes repo guidelines:
https://github.com/autopkg/jss-recipes#jss-recipes
"""

# Read the pkg recipe using FoundationPlist.

# Make sure there are no existing jss recies using `autopkg search`.

# Create a dictionary representing the jss recipe.

# Write the jss recipe to disk.
