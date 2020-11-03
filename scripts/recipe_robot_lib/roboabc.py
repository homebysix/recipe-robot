#!/usr/local/autopkg/python
# This Python file uses the following encoding: utf-8

# Recipe Robot
# Copyright 2015-2020 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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
roboabc.py

RoboDict:
    Abstract Base Class dictionary for defining special methods
    and inits.
RoboList:
    Abstract Base Class list for defining special methods and inits.
"""


from __future__ import absolute_import

from collections.abc import MutableMapping, MutableSequence


class RoboDict(MutableMapping):
    """Base dictionary class for defining special methods and inits.

    Doesn't do anything different from dict, other than allow easy
    overriding for subclasses.
    """

    def __init__(self):
        self._dict = {}

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, val):
        self._dict[key] = val

    def __delitem__(self, key):
        if key in self:
            del self._dict[key]

    def __iter__(self):
        for key in self._dict:
            yield key

    def __len__(self):
        return len(self._dict)

    def __repr__(self):
        return self._dict.__repr__()


class RoboList(MutableSequence):
    """Base list class for defining special methods and inits.

    Doesn't do anything different from list, other than allow easy
    overriding for subclasses.
    """

    def __init__(self, iterable=None):
        """Set up NotifyingList for use.

        Args:
            iterable: Optional iterable to use to fill the instance.
        """
        if iterable:
            self._list = list(iterable)
        else:
            self._list = []

    def __getitem__(self, index):
        return self._list[index]

    def __setitem__(self, index, val):
        self._list[index] = val

    def __delitem__(self, index):
        del self._list[index]

    def __len__(self):
        return len(self._list)

    def insert(self, index, item):
        self._list.insert(index, item)

    def __repr__(self):
        return self._list.__repr__()
