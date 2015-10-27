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
facts.py

Facts is a dictionary-like object that defines recipe-robot specific
MutableSequnces; NotifyingList and NoisyNotifyingList.

The NotifyingList is used to post a NSNotification whenever a value is
set or inserted.

The NoisyNotifyingList posts NSNotifications under the same conditions,
but also robo_prints the message as well.
"""


from collections import MutableMapping, MutableSequence

# pylint: disable=no-name-in-module
from Foundation import (NSDistributedNotificationCenter,
                        NSNotificationDeliverImmediately)
# pylint: enable=no-name-in-module

from .tools import (LogLevel, robo_print)


class Facts(MutableMapping):
    """Dictionary-like object for holding all of recipe-robot's data."""

    def __init__(self):
        """Set up a Fact instance with required list-like objects."""
        self._dict = {"errors": NoisyNotifyingList("errors"),
                      "reminders": NoisyNotifyingList("reminders"),
                      "warnings": NoisyNotifyingList("warnings"),
                      "recipes": NotifyingList("recipes"),
                      "icons": NotifyingList("icons"),}

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

class NotifyingList(MutableSequence):
    """A list that robo_prints and sends NSNotifications on changes"""

    def __init__(self, message_type, iterable=None):
        """Set up NotifyingList for use.

        Args:
            message_type: String name appended to message identifier.
            iterable: Optional iterable to use to fill the instance.
        """
        # NSDistributedNotificationCenter is the NotificationCenter
        # that allows messages to be sent between applications.
        self.notification_center = (
            NSDistributedNotificationCenter.defaultCenter())
        self.message_type = message_type
        if iterable:
            self._list = iterable
        else:
            self._list = []

    def __getitem__(self, index):
        return self._list[index]

    def __setitem__(self, index, val):
        """Set val at index, and send a notification with that val."""
        self._list[index] = val
        self._respond_to_item_setting(val)

    def __delitem__(self, index):
        del self._list[index]

    def __len__(self):
        return len(self._list)

    def insert(self, index, item):
        """Insert val before index, and send a notification with val."""
        self._list.insert(index, item)
        self._respond_to_item_setting(item)

    def _respond_to_item_setting(self, message):
        """Send a notification that an item has been set."""
        self._send_notification(self.message_type, message)

    def _send_notification(self, name, message):
        """Send an NSNotification to our stored center."""
        userInfo = {"message": str(message)}  # pylint: disable=invalid-name
        self.notification_center.postNotificationName_object_userInfo_options_(
            "com.elliotjordan.recipe-robot.dnc.%s" % name,
            None,
            userInfo,
            NSNotificationDeliverImmediately)

    def __repr__(self):
        return self._list.__repr__()


class NoisyNotifyingList(NotifyingList):
    """A NotifyingList that robo_prints when updated."""

    def _respond_to_item_setting(self, message):
        """Notify that an item has been set, and robo_print it."""
        self._send_notification(self.message_type, message)
        log_level = LogLevel.__getattribute__(
            LogLevel, self.message_type.rstrip("s").upper())
        robo_print(message, log_level)
