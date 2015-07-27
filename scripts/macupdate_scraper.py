#!/usr/bin/env python

"""
Put in an app name, and it generates a description. Might be useful for Munki
and JSS recipe generation, although I'd love to find a way to use built-in
Python libraries instead of requests/lxml.  -Elliot
"""

from lxml import html
import requests

app_name = raw_input("App name: ")

page = requests.get('http://www.macupdate.com/find/mac/' + app_name)
tree = html.fromstring(page.text)

selector = "//span[substring(@class, string-length(@class) - string-length('-shortdescrip') +1) = '-shortdescrip']/text()"
description = tree.xpath(selector)[0]

print "Description: ", description
