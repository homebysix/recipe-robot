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
exceptions.py

Custom Exceptions for use in Recipe Robot.
"""


from __future__ import absolute_import

import traceback


class RoboException(Exception):
    """Base recipe-robot exception.

    Args:
        Exception (Exception): Python error superclass.

    Attributes:
        error (str): Reason for the exception.
    """

    def __init__(self, message, error=None):
        """Add message and kwargs to exception.

        Args:
            message: String message describing the exception.
            error:  An exception object. The traceback stack from
                'error' will be string formatted and added to the
                RoboException.error property.
        """
        # This is primarily set up to store tracebacks for later debug
        # printing.
        super(RoboException, self).__init__(message)
        self.error = error

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, exception_object):
        self._error = traceback.format_exc(exception_object)


class RoboError(RoboException):
    """Recipe Robot throws a RoboError exception when something happened that
    prevents us from continuing.

    Args:
        RoboException (Exception): Superclass - see above.
    """

    pass
