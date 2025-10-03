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
test_roboabc.py

Unit tests for abstract base classes.
"""

import unittest
from collections.abc import MutableMapping, MutableSequence
from scripts.recipe_robot_lib.roboabc import RoboDict, RoboList


class TestRoboDict(unittest.TestCase):
    """Tests for the RoboDict class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.robo_dict = RoboDict()

    def test_robo_dict_inherits_from_mutable_mapping(self):
        """Test that RoboDict properly inherits from MutableMapping."""
        self.assertIsInstance(self.robo_dict, MutableMapping)
        self.assertIsInstance(self.robo_dict, RoboDict)

    def test_robo_dict_init(self):
        """Test RoboDict initialization creates empty internal dict."""
        self.assertEqual(len(self.robo_dict), 0)
        self.assertEqual(dict(self.robo_dict), {})

    def test_robo_dict_setitem_and_getitem(self):
        """Test setting and getting items from RoboDict."""
        self.robo_dict["key1"] = "value1"
        self.robo_dict["key2"] = 42

        self.assertEqual(self.robo_dict["key1"], "value1")
        self.assertEqual(self.robo_dict["key2"], 42)
        self.assertEqual(len(self.robo_dict), 2)

    def test_robo_dict_getitem_keyerror(self):
        """Test that accessing non-existent key raises KeyError."""
        with self.assertRaises(KeyError):
            _ = self.robo_dict["nonexistent_key"]

    def test_robo_dict_delitem(self):
        """Test deleting items from RoboDict."""
        self.robo_dict["key1"] = "value1"
        self.robo_dict["key2"] = "value2"

        del self.robo_dict["key1"]

        self.assertNotIn("key1", self.robo_dict)
        self.assertIn("key2", self.robo_dict)
        self.assertEqual(len(self.robo_dict), 1)

    def test_robo_dict_delitem_nonexistent_key(self):
        """Test that deleting non-existent key doesn't raise error."""
        # Should not raise any exception
        del self.robo_dict["nonexistent_key"]

    def test_robo_dict_iter(self):
        """Test iteration over RoboDict keys."""
        test_data = {"a": 1, "b": 2, "c": 3}
        for key, value in test_data.items():
            self.robo_dict[key] = value

        keys = list(self.robo_dict)
        self.assertEqual(set(keys), set(test_data.keys()))

    def test_robo_dict_len(self):
        """Test length calculation for RoboDict."""
        self.assertEqual(len(self.robo_dict), 0)

        self.robo_dict["key1"] = "value1"
        self.assertEqual(len(self.robo_dict), 1)

        self.robo_dict["key2"] = "value2"
        self.assertEqual(len(self.robo_dict), 2)

        del self.robo_dict["key1"]
        self.assertEqual(len(self.robo_dict), 1)

    def test_robo_dict_repr(self):
        """Test string representation of RoboDict."""
        self.assertEqual(repr(self.robo_dict), "{}")

        self.robo_dict["key"] = "value"
        self.assertEqual(repr(self.robo_dict), "{'key': 'value'}")

    def test_robo_dict_contains(self):
        """Test membership testing with 'in' operator."""
        self.robo_dict["existing_key"] = "value"

        self.assertIn("existing_key", self.robo_dict)
        self.assertNotIn("non_existing_key", self.robo_dict)

    def test_robo_dict_update(self):
        """Test updating RoboDict with another dictionary."""
        other_dict = {"a": 1, "b": 2}
        self.robo_dict.update(other_dict)

        self.assertEqual(self.robo_dict["a"], 1)
        self.assertEqual(self.robo_dict["b"], 2)
        self.assertEqual(len(self.robo_dict), 2)

    def test_robo_dict_get(self):
        """Test get method with default values."""
        self.robo_dict["existing"] = "value"

        self.assertEqual(self.robo_dict.get("existing"), "value")
        self.assertIsNone(self.robo_dict.get("nonexistent"))
        self.assertEqual(self.robo_dict.get("nonexistent", "default"), "default")

    def test_robo_dict_keys_values_items(self):
        """Test keys(), values(), and items() methods."""
        test_data = {"a": 1, "b": 2, "c": 3}
        self.robo_dict.update(test_data)

        self.assertEqual(set(self.robo_dict.keys()), set(test_data.keys()))
        self.assertEqual(set(self.robo_dict.values()), set(test_data.values()))
        self.assertEqual(set(self.robo_dict.items()), set(test_data.items()))


class TestRoboList(unittest.TestCase):
    """Tests for the RoboList class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.robo_list = RoboList()

    def test_robo_list_inherits_from_mutable_sequence(self):
        """Test that RoboList properly inherits from MutableSequence."""
        self.assertIsInstance(self.robo_list, MutableSequence)
        self.assertIsInstance(self.robo_list, RoboList)

    def test_robo_list_init_empty(self):
        """Test RoboList initialization without arguments."""
        self.assertEqual(len(self.robo_list), 0)
        self.assertEqual(list(self.robo_list), [])

    def test_robo_list_init_with_iterable(self):
        """Test RoboList initialization with an iterable."""
        initial_data = [1, 2, 3, "test"]
        robo_list = RoboList(initial_data)

        self.assertEqual(len(robo_list), 4)
        self.assertEqual(list(robo_list), initial_data)

    def test_robo_list_setitem_and_getitem(self):
        """Test setting and getting items by index."""
        self.robo_list.append("item1")
        self.robo_list.append("item2")

        self.assertEqual(self.robo_list[0], "item1")
        self.assertEqual(self.robo_list[1], "item2")

        self.robo_list[0] = "modified_item1"
        self.assertEqual(self.robo_list[0], "modified_item1")

    def test_robo_list_getitem_indexerror(self):
        """Test that accessing invalid index raises IndexError."""
        with self.assertRaises(IndexError):
            _ = self.robo_list[0]

        self.robo_list.append("item")
        with self.assertRaises(IndexError):
            _ = self.robo_list[5]

    def test_robo_list_delitem(self):
        """Test deleting items by index."""
        self.robo_list.extend([1, 2, 3, 4])

        del self.robo_list[1]  # Remove item at index 1 (value 2)

        self.assertEqual(list(self.robo_list), [1, 3, 4])
        self.assertEqual(len(self.robo_list), 3)

    def test_robo_list_len(self):
        """Test length calculation for RoboList."""
        self.assertEqual(len(self.robo_list), 0)

        self.robo_list.append("item")
        self.assertEqual(len(self.robo_list), 1)

        self.robo_list.extend([2, 3, 4])
        self.assertEqual(len(self.robo_list), 4)

    def test_robo_list_insert(self):
        """Test inserting items at specific positions."""
        self.robo_list.extend([1, 3, 4])

        self.robo_list.insert(1, 2)  # Insert 2 at index 1

        self.assertEqual(list(self.robo_list), [1, 2, 3, 4])

    def test_robo_list_append(self):
        """Test appending items to the list."""
        self.robo_list.append("first")
        self.robo_list.append("second")

        self.assertEqual(len(self.robo_list), 2)
        self.assertEqual(self.robo_list[0], "first")
        self.assertEqual(self.robo_list[1], "second")

    def test_robo_list_extend(self):
        """Test extending the list with another iterable."""
        self.robo_list.extend([1, 2, 3])

        self.assertEqual(len(self.robo_list), 3)
        self.assertEqual(list(self.robo_list), [1, 2, 3])

        self.robo_list.extend([4, 5])
        self.assertEqual(list(self.robo_list), [1, 2, 3, 4, 5])

    def test_robo_list_repr(self):
        """Test string representation of RoboList."""
        self.assertEqual(repr(self.robo_list), "[]")

        self.robo_list.append("item")
        self.assertEqual(repr(self.robo_list), "['item']")

    def test_robo_list_slicing(self):
        """Test list slicing operations."""
        self.robo_list.extend([1, 2, 3, 4, 5])

        self.assertEqual(self.robo_list[1:3], [2, 3])
        self.assertEqual(self.robo_list[:2], [1, 2])
        self.assertEqual(self.robo_list[2:], [3, 4, 5])
        self.assertEqual(self.robo_list[:], [1, 2, 3, 4, 5])

    def test_robo_list_contains(self):
        """Test membership testing with 'in' operator."""
        self.robo_list.extend(["a", "b", "c"])

        self.assertIn("a", self.robo_list)
        self.assertIn("b", self.robo_list)
        self.assertNotIn("d", self.robo_list)

    def test_robo_list_count_and_index(self):
        """Test count() and index() methods."""
        self.robo_list.extend([1, 2, 2, 3, 2])

        self.assertEqual(self.robo_list.count(2), 3)
        self.assertEqual(self.robo_list.count(1), 1)
        self.assertEqual(self.robo_list.count(5), 0)

        self.assertEqual(self.robo_list.index(2), 1)  # First occurrence
        self.assertEqual(self.robo_list.index(3), 3)

    def test_robo_list_remove(self):
        """Test removing items by value."""
        self.robo_list.extend([1, 2, 3, 2, 4])

        self.robo_list.remove(2)  # Removes first occurrence

        self.assertEqual(list(self.robo_list), [1, 3, 2, 4])

        with self.assertRaises(ValueError):
            self.robo_list.remove(10)  # Item not in list

    def test_robo_list_pop(self):
        """Test popping items from the list."""
        self.robo_list.extend([1, 2, 3, 4])

        # Pop from end
        popped = self.robo_list.pop()
        self.assertEqual(popped, 4)
        self.assertEqual(list(self.robo_list), [1, 2, 3])

        # Pop from specific index
        popped = self.robo_list.pop(1)
        self.assertEqual(popped, 2)
        self.assertEqual(list(self.robo_list), [1, 3])

    def test_robo_list_reverse(self):
        """Test reversing the list in place."""
        self.robo_list.extend([1, 2, 3, 4])

        self.robo_list.reverse()

        self.assertEqual(list(self.robo_list), [4, 3, 2, 1])

    def test_robo_list_clear(self):
        """Test clearing all items from the list."""
        self.robo_list.extend([1, 2, 3, 4])

        self.robo_list.clear()

        self.assertEqual(len(self.robo_list), 0)
        self.assertEqual(list(self.robo_list), [])


class TestRoboAbcIntegration(unittest.TestCase):
    """Integration tests for RoboDict and RoboList working together."""

    def test_robo_dict_with_robo_list_values(self):
        """Test using RoboList as values in RoboDict."""
        robo_dict = RoboDict()
        robo_list = RoboList([1, 2, 3])

        robo_dict["list_key"] = robo_list

        self.assertIsInstance(robo_dict["list_key"], RoboList)
        self.assertEqual(list(robo_dict["list_key"]), [1, 2, 3])

    def test_robo_list_with_robo_dict_items(self):
        """Test using RoboDict as items in RoboList."""
        robo_list = RoboList()
        robo_dict = RoboDict()
        robo_dict["key"] = "value"

        robo_list.append(robo_dict)

        self.assertIsInstance(robo_list[0], RoboDict)
        self.assertEqual(robo_list[0]["key"], "value")

    def test_nested_structures(self):
        """Test deeply nested RoboDict and RoboList structures."""
        # Create nested structure: dict -> list -> dict
        outer_dict = RoboDict()
        middle_list = RoboList()
        inner_dict = RoboDict()

        inner_dict["inner_key"] = "inner_value"
        middle_list.append(inner_dict)
        outer_dict["middle_list"] = middle_list

        # Test access
        self.assertEqual(outer_dict["middle_list"][0]["inner_key"], "inner_value")

        # Test modification
        outer_dict["middle_list"][0]["new_key"] = "new_value"
        self.assertEqual(outer_dict["middle_list"][0]["new_key"], "new_value")


if __name__ == "__main__":
    unittest.main()
