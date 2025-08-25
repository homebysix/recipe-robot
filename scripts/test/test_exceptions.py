#!/usr/local/autopkg/python

# Recipe Robot
# Copyright 2015-2025 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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
test_exceptions.py

Unit tests for custom exceptions.
"""

import unittest

from scripts.recipe_robot_lib.exceptions import RoboException, RoboError


class TestRoboException(unittest.TestCase):
    """Tests for the RoboException class."""

    def test_robo_exception_basic_init(self):
        """Test basic initialization of RoboException."""
        message = "Test exception message"
        exception = RoboException(message)

        self.assertEqual(str(exception), message)
        # Access the private attribute directly for testing
        self.assertIsNone(getattr(exception, "_error", None))

    def test_robo_exception_with_error_object(self):
        """Test RoboException initialization with an error object."""
        message = "Test exception with error"

        # Create a test exception to pass as the error parameter
        try:
            raise ValueError("Original error")
        except ValueError as original_error:
            exception = RoboException(message, error=original_error)

        self.assertEqual(str(exception), message)
        self.assertIsNotNone(exception.error)
        self.assertIn("ValueError", exception.error)

    def test_robo_exception_error_property_setter(self):
        """Test the error property setter functionality."""
        exception = RoboException("Test message")

        # Test setting error to None should set it to None
        exception.error = None
        self.assertIsNone(exception.error)

        # Test setting error with an exception object that has traceback
        try:
            raise RuntimeError("Test runtime error")
        except RuntimeError as runtime_error:
            exception.error = runtime_error

        # The error property should contain the formatted traceback
        self.assertIsInstance(exception.error, str)
        self.assertIn("RuntimeError", exception.error)
        self.assertIn("Traceback", exception.error)

        # Test setting error with an exception object without traceback
        plain_error = ValueError("Plain error")
        exception.error = plain_error
        self.assertIsInstance(exception.error, str)
        self.assertEqual(exception.error, "Plain error")

    def test_robo_exception_inheritance(self):
        """Test that RoboException properly inherits from Exception."""
        exception = RoboException("Test message")
        self.assertIsInstance(exception, Exception)
        self.assertIsInstance(exception, RoboException)

    def test_robo_exception_str_representation(self):
        """Test string representation of RoboException."""
        message = "This is a test exception"
        exception = RoboException(message)
        self.assertEqual(str(exception), message)


class TestRoboError(unittest.TestCase):
    """Tests for the RoboError class."""

    def test_robo_error_basic_init(self):
        """Test basic initialization of RoboError."""
        message = "Test error message"
        error = RoboError(message)

        self.assertEqual(str(error), message)
        # Access the private attribute directly for testing
        self.assertIsNone(getattr(error, "_error", None))

    def test_robo_error_with_error_object(self):
        """Test RoboError initialization with an error object."""
        message = "Test error with nested exception"

        try:
            raise IOError("File not found")
        except IOError as io_error:
            error = RoboError(message, error=io_error)

        self.assertEqual(str(error), message)
        self.assertIsNotNone(error.error)
        self.assertIn("IOError", error.error)

    def test_robo_error_inheritance(self):
        """Test that RoboError properly inherits from RoboException."""
        error = RoboError("Test message")
        self.assertIsInstance(error, Exception)
        self.assertIsInstance(error, RoboException)
        self.assertIsInstance(error, RoboError)

    def test_robo_error_can_be_raised_and_caught(self):
        """Test that RoboError can be raised and caught properly."""
        message = "Test error for raising"

        with self.assertRaises(RoboError) as context:
            raise RoboError(message)

        self.assertEqual(str(context.exception), message)

    def test_robo_error_can_be_caught_as_robo_exception(self):
        """Test that RoboError can be caught as its parent class."""
        message = "Test error for parent catching"

        with self.assertRaises(RoboException) as context:
            raise RoboError(message)

        self.assertEqual(str(context.exception), message)
        self.assertIsInstance(context.exception, RoboError)

    def test_robo_error_with_complex_nested_exception(self):
        """Test RoboError with a complex nested exception chain."""
        error = None
        try:
            try:
                raise ValueError("Inner error")
            except ValueError as value_error:
                raise KeyError("Middle error") from value_error
        except KeyError as key_error:
            error = RoboError("Outer error", error=key_error)

        self.assertIsNotNone(error)
        self.assertIn("KeyError", error.error)
        # Should contain the full traceback
        self.assertIn("ValueError", error.error)


class TestExceptionIntegration(unittest.TestCase):
    """Integration tests for exception handling."""

    def test_exception_chaining_scenario(self):
        """Test a realistic scenario of exception chaining."""

        def problematic_function():
            """Simulate a function that causes an error."""
            raise FileNotFoundError("Recipe file not found")

        def wrapper_function():
            """Wrapper function that catches and re-raises."""
            try:
                problematic_function()
            except FileNotFoundError as e:
                raise RoboError("Failed to process recipe", error=e) from e

        with self.assertRaises(RoboError) as context:
            wrapper_function()

        error = context.exception
        self.assertEqual(str(error), "Failed to process recipe")
        self.assertIn("FileNotFoundError", error.error)

    def test_multiple_exception_creation(self):
        """Test creating multiple exceptions with different error sources."""
        errors = []

        # Create multiple errors with different source exceptions
        for i, exception_type in enumerate([ValueError, TypeError, KeyError]):
            try:
                raise exception_type(f"Test error {i}")
            except exception_type as e:
                errors.append(RoboError(f"Robo error {i}", error=e))

        self.assertEqual(len(errors), 3)
        for i, error in enumerate(errors):
            self.assertIn(f"Test error {i}", error.error)


if __name__ == "__main__":
    unittest.main()
