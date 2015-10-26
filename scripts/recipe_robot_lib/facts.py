from collections import MutableMapping, MutableSequence
from copy import deepcopy
import sys

from Foundation import (NSDistributedNotificationCenter,
                        NSNotificationDeliverImmediately)

from .tools import (LogLevel, robo_print)


# TODO (Shea): Write some docstrings!


class Facts(MutableMapping):
    """Dictionary-like object that writes to a plist every update."""

    def __init__(self):
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
            del(self._dict[key])

    def __iter__(self):
        for key in self._dict:
            yield key

    def __len__(self):
        return len(self._dict)


class NotifyingList(MutableSequence):
    """A list that robo_prints and sends NSNotifications on changes"""

    def __init__(self, message_type, iterable=None):
        self.notification_center = (
            NSDistributedNotificationCenter.defaultCenter())
        self.message_type = message_type
        if iterable:
            self._list = iterable
        else:
            self._list = []

    def __getitem__(self, index):
        return self._list(index)

    def __setitem__(self, index, val):
        self._list[index] = val
        self._respond_to_item_setting(item)

    def __delitem__(self, index):
        del self._list[index]

    def __len__(self):
        return len(self._list)

    def insert(self, index, item):
        self._list.insert(index, item)
        self._respond_to_item_setting(item)

    def _respond_to_item_setting(self, message):
        self._send_notification(self.message_type, message)

    def _send_notification(self, name, message):
        userInfo = {"message": str(message)}
        self.notification_center.postNotificationName_object_userInfo_options_(
            "com.elliotjordan.recipe-robot.dnc.%s" % name,
            None,
            userInfo,
            NSNotificationDeliverImmediately)


class NoisyNotifyingList(NotifyingList):
    """A NotifyingList that quits when updated."""

    def _respond_to_item_setting(self, message):
        self._send_notification(self.message_type, message)
        log_level = LogLevel.__getattribute__(
                LogLevel, self.message_type.rstrip("s").upper()))
        robo_print(message, log_level)
