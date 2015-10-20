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
macupdate_scraper.py

Given the name of an app, this script retrieves a description from
MacUpdate.com. This file is not being used by Recipe Robot in its current form,
because of our preference to rely on built-in Python libraries instead of
external libraries like `requests`. However, we're keeping it here in storage
in case it proves useful in the future.
"""

from lxml import html
import requests

app_name = raw_input("App name: ")

page = requests.get('http://www.macupdate.com/find/mac/' + app_name)
tree = html.fromstring(page.text)

selector = "//span[substring(@class, string-length(@class) - string-length('-shortdescrip') +1) = '-shortdescrip']/text()"
description = tree.xpath(selector)[0]

print "Description: ", description
