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
facts.py

Facts is a dictionary-like object that defines recipe-robot specific
MutableSequences; NotifyingList and NoisyNotifyingList.

The NotifyingList is used to post a NSNotification whenever a value is
set or inserted.

The NoisyNotifyingList posts NSNotifications under the same conditions,
but also robo_prints the message as well.
"""


# pylint: disable=no-name-in-module
from __future__ import absolute_import

from Foundation import NSDistributedNotificationCenter, NSNotificationDeliverImmediately

from .roboabc import RoboDict, RoboList
from .tools import LogLevel, robo_print

# pylint: enable=no-name-in-module

# pylint: disable=too-few-public-methods
class NotificationMixin(object):
    """Adds a send_notification method to Notifying classes."""

    def send_notification(self, message):
        """Send an NSNotification to our stored center."""
        if isinstance(message, str):
            message = message.encode("utf-8")
        userInfo = {"message": message}  # pylint: disable=invalid-name
        self.notification_center.postNotificationName_object_userInfo_options_(
            "com.elliotjordan.recipe-robot.dnc.%s" % self.message_type,
            None,
            userInfo,
            NSNotificationDeliverImmediately,
        )


# pylint: enable=too-few-public-methods
class Facts(RoboDict):
    """Dictionary-like object for holding all of recipe-robot's data.

    To aid in intercommunication with the App, all dictionary values
    are cast to notification-sending subclassed-variants of that type.

    i.e. lists -> NotifyingList, str -> NotifyingString.
    """

    default_suffix = "information"

    def __init__(self):
        """Set up a Fact instance with required list-like objects."""
        super(Facts, self).__init__()
        self._dict.update(
            {
                "complete": NotifyingList("complete"),
                "errors": NoisyNotifyingList("errors"),
                "icons": NotifyingList("icons"),
                "information": NoisyNotifyingList("information"),
                "recipes": NotifyingList("recipes"),
                "reminders": NoisyNotifyingList("reminders"),
                "warnings": NoisyNotifyingList("warnings"),
            }
        )

    def __setitem__(self, key, val):
        if isinstance(val, str):
            val = NotifyingString(self.default_suffix, val)
        elif isinstance(val, list):
            val = NotifyingList(self.default_suffix, val)
        elif isinstance(val, bool):
            val = NotifyingBool(self.default_suffix, val)
        super(Facts, self).__setitem__(key, val)

    def is_from_app_store(self):
        """Can't make this recipe if the app is from the App Store."""
        return self.get("is_from_app_store")


# pylint: disable=too-few-public-methods, too-many-ancestors
class NotifyingList(NotificationMixin, RoboList):
    """A list that robo_prints and sends NSNotifications on changes"""

    def __init__(self, message_type, iterable=None):
        """Set up NotifyingList for use.

        Args:
            message_type: String name appended to message identifier.
            iterable: Optional iterable to use to fill the instance.
        """
        super(NotifyingList, self).__init__(iterable)
        # NSDistributedNotificationCenter is the NotificationCenter
        # that allows messages to be sent between applications.
        self.notification_center = NSDistributedNotificationCenter.defaultCenter()
        self.message_type = message_type

    def __setitem__(self, index, val):
        """Set val at index, and send a notification with that val."""
        super(NotifyingList, self).__setitem__(index, val)
        self.send_notification(str(val))

    def insert(self, index, val):
        """Insert val before index, and send a notification with val."""
        super(NotifyingList, self).insert(index, val)
        self.send_notification(str(val))


class NoisyNotifyingList(NotifyingList):
    """A NotifyingList that robo_prints when updated."""

    def send_notification(self, message):
        """Notify that an item has been set, and robo_print it."""
        super(NoisyNotifyingList, self).send_notification(message)
        log_level = LogLevel.__getattribute__(
            LogLevel, self.message_type.rstrip("s").upper()
        )
        robo_print(message, log_level)


class NotifyingString(NotificationMixin, str):
    """A string that sends notifications."""

    def __new__(cls, message_type, text=""):
        """Set up NotifyingString for use.

        Args:
            message_type: String name appended to message identifier.
            text: Optional string to use to fill the instance.
        """
        instance = super(NotifyingString, cls).__new__(cls, text)
        instance.message_type = message_type
        return instance

    # pylint: disable=unused-argument
    def __init__(self, message_type, text=""):
        """Set up NotifyingString for use.

        Args:
            message_type: String name appended to message identifier.
            text: Optional string to use to fill the instance.
        """
        # NSDistributedNotificationCenter is the NotificationCenter
        # that allows messages to be sent between applications.
        self.notification_center = NSDistributedNotificationCenter.defaultCenter()
        self.send_notification(text)
        super(NotifyingString, self).__init__()

    # pylint: enable=unused-argument


class NotifyingBool(NotificationMixin, object):
    """A bool that sends notifications."""

    def __new__(cls, message_type, val):
        """Set up NotifyingBool for use.

        Args:
            message_type: String name appended to message identifier.
            val: True or False
        """
        instance = super(NotifyingBool, cls).__new__(cls)
        instance.message_type = message_type
        # NSDistributedNotificationCenter is the NotificationCenter
        # that allows messages to be sent between applications.
        instance.notification_center = NSDistributedNotificationCenter.defaultCenter()
        instance.send_notification(val)
        return bool(val)


# pylint: enable=too-few-public-methods, too-many-ancestors
