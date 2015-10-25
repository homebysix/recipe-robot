from collections import MutableMapping
from copy import deepcopy

from Foundation import (NSDistributedNotificationCenter,
                        NSNotificationDeliverImmediately)

from .tools import (LogLevel, robo_print)


class Facts(MutableMapping):
    """Dictionary-like object that writes to a plist every update."""

    def __init__(self):
        self.notification_center = (
            NSDistributedNotificationCenter.defaultCenter())
        # TODO (Shea): These could be @properties too, which would more clearly
        # state that they are treated differently than the dict items.
        self._dict = {"errors": [],
                      "reminders": [],
                      "warnings": [],
                      "recipes": [],
                      "icons": [],}

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, val):
        self._dict[key] = val
        if key in ("errors", "reminders", "warnings", "recipes", "icons"):
            userInfo = {"message": str(val)}
            self.notification_center.postNotificationName_object_userInfo_options_(
                "com.elliotjordan.recipe-robot.dnc.%s" % key,
                None,
                userInfo,
                NSNotificationDeliverImmediately)
        if key in ("errors", "reminders", "warnings"):
            log_level = LogLevel.__getattr__(key.rstrip("s").upper())
            robo_print(val, log_level)
            if key is "errors":
                sys.exit(1)


        # Old plist-writing version.
        # TODO (Shea): Eventually we need to make args a dict instead of a
        # Namespace.
        # if "args" in self._dict and not isinstance(output["args"], dict):
        #     output = deepcopy(self._dict)
        #     output["args"] = vars(output["args"])
        # else:
        #     output = self._dict
        # FoundationPlist.writePlist(output, self.path)

    def __delitem__(self, key):
        if key in self:
            del(self._dict[key])

    def __iter__(self):
        for key in self._dict:
            yield key

    def __len__(self):
        return len(self._dict)
