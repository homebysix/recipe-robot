from collections import MutableMapping
from copy import deepcopy

from . import FoundationPlist


class Facts(MutableMapping):
    """Dictionary-like object that writes to a plist every update."""

    def __init__(self, path):
        self.path = path
        self._dict = {"errors": [],
                      "reminders": [],
                      "warnings": [],
                      "recipes": [],
                      "icons": [],}

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, val):
        self._dict[key] = val
        output = deepcopy(self._dict)
        if "args" in output and not isinstance(output["args"], dict):
            output["args"] = vars(output["args"])
        FoundationPlist.writePlist(output, self.path)

    def __delitem__(self, key):
        if key in self:
            del(self._dict[key])

    def __iter__(self):
        for key in self._dict:
            yield key

    def __len__(self):
        return len(self._dict)
