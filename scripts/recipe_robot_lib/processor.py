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
processor.py

Processor class to encapsulate information that Recipe Robot needs to
write recipes.

Makes Processor subclasses from importing and introspection on the
AutoPkg autopkglib.
"""


import sys

from .roboabc import RoboDict
from .tools import robo_print, LogLevel

sys.path.append("/Library/AutoPkg")
try:
    import autopkglib
except ImportError:
    robo_print("AutoPkg must be installed!")
    sys.exit(1)


class AbstractProcessor(object):
    """Represent an AutoPkg processor for recipe purposes."""

    def __init__(self, classtype):
        self._type = classtype


def ProcessorFactory(name, attributes, base_class=AbstractProcessor):
    """Build a new class from a name, and the desired attributes."""

    def __init__(self, **kwargs):
        """Dynamically init a Processor."""
        for attr in attributes:
            setattr(self, attr, None)
        for key, val in kwargs.items():
            setattr(self, key, val)
        base_class.__init__(self, name[:-len("Class")])

    newclass = type(name, (AbstractProcessor, ), {"__init__": __init__})

    return newclass

processor_classes = [
    ProcessorFactory(proc_type,
                     autopkglib.get_processor(proc_type).input_variables)
    for proc_type in autopkglib.processor_names() if
    hasattr(autopkglib.get_processor(proc_type), "input_variables")]

for processor in processor_classes:
    globals()[processor.__name__] = processor
