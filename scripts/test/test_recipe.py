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
test_recipe.py

Unit tests for recipe-related classes and functions.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import plistlib
import yaml

from scripts.recipe_robot_lib.recipe import Recipe, Recipes, RECIPE_TYPES
from scripts.recipe_robot_lib.processor import AbstractProcessor
from scripts.recipe_robot_lib.facts import NotifyingBool, NotifyingList, NotifyingString
from Foundation import NSArray, NSDictionary, NSNumber


class TestRecipeTypes(unittest.TestCase):
    """Tests for the RECIPE_TYPES constant."""

    def test_recipe_types_structure(self):
        """Test that RECIPE_TYPES has the expected structure."""
        self.assertIsInstance(RECIPE_TYPES, tuple)
        self.assertGreater(len(RECIPE_TYPES), 0)

        for recipe_type in RECIPE_TYPES:
            self.assertIsInstance(recipe_type, dict)
            self.assertIn("type", recipe_type)
            self.assertIn("desc", recipe_type)
            self.assertIsInstance(recipe_type["type"], str)
            self.assertIsInstance(recipe_type["desc"], str)

    def test_recipe_types_contains_expected_types(self):
        """Test that RECIPE_TYPES contains expected recipe types."""
        expected_types = {
            "download",
            "pkg",
            "munki",
            "jamf",
            "ds",
            "filewave",
            "lanrev",
            "sccm",
            "bigfix",
            "install",
        }

        actual_types = {rt["type"] for rt in RECIPE_TYPES}
        self.assertEqual(actual_types, expected_types)

    def test_recipe_types_unique(self):
        """Test that all recipe types are unique."""
        types = [rt["type"] for rt in RECIPE_TYPES]
        self.assertEqual(len(types), len(set(types)))


class TestRecipe(unittest.TestCase):
    """Tests for the Recipe class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.recipe = Recipe("download", "Downloads the app")

    def test_recipe_initialization(self):
        """Test Recipe initialization with basic parameters."""
        recipe = Recipe("munki", "Imports into Munki")

        self.assertEqual(recipe["type"], "munki")
        self.assertEqual(recipe["description"], "Imports into Munki")
        self.assertFalse(recipe["preferred"])  # munki not in default_enabled
        self.assertFalse(recipe["existing"])

        # Test default enabled types
        download_recipe = Recipe("download", "Downloads app")
        self.assertTrue(download_recipe["preferred"])

        pkg_recipe = Recipe("pkg", "Creates pkg")
        self.assertTrue(pkg_recipe["preferred"])

    def test_recipe_keys_structure(self):
        """Test that recipe keys have the expected structure."""
        keys = self.recipe["keys"]

        self.assertIn("Identifier", keys)
        self.assertIn("MinimumVersion", keys)
        self.assertIn("Input", keys)
        self.assertIn("Process", keys)
        self.assertIn("Comment", keys)

        self.assertEqual(keys["MinimumVersion"], "1.0.0")
        self.assertIsInstance(keys["Input"], dict)
        self.assertIn("NAME", keys["Input"])
        self.assertIsInstance(keys["Process"], list)
        self.assertIn("Recipe Robot", keys["Comment"])

    def test_recipe_inherits_from_robo_dict(self):
        """Test that Recipe properly inherits from RoboDict."""
        # Test that Recipe instances behave like RoboDict
        self.assertTrue(hasattr(self.recipe, "_dict"))
        self.assertTrue(callable(getattr(self.recipe, "__getitem__", None)))
        self.assertTrue(callable(getattr(self.recipe, "__setitem__", None)))
        self.assertTrue(callable(getattr(self.recipe, "__delitem__", None)))

        # Test basic dict-like behavior
        test_recipe = Recipe("test", "test")
        test_recipe["test_key"] = "test_value"
        self.assertEqual(test_recipe["test_key"], "test_value")

    def test_set_description(self):
        """Test setting recipe description."""
        description = "This recipe downloads and processes TestApp"
        self.recipe.set_description(description)

        self.assertEqual(self.recipe["keys"]["Description"], description)

    def test_set_parent(self):
        """Test setting parent recipe."""
        parent = "com.github.homebysix.download.TestApp"
        self.recipe.set_parent(parent)

        self.assertEqual(self.recipe["keys"]["ParentRecipe"], parent)

    def test_set_parent_removes_spaces(self):
        """Test that set_parent removes spaces from parent identifier."""
        parent_with_spaces = "com.github.homebysix.download.Test App"
        self.recipe.set_parent(parent_with_spaces)

        expected = "com.github.homebysix.download.TestApp"
        self.assertEqual(self.recipe["keys"]["ParentRecipe"], expected)

    def test_set_parent_from(self):
        """Test setting parent from preferences and facts."""
        prefs = {"RecipeIdentifierPrefix": "com.github.homebysix"}
        facts = {"app_name": "TestApp"}

        # Mock get_bundle_name_info to return app_name
        with patch(
            "scripts.recipe_robot_lib.recipe.get_bundle_name_info"
        ) as mock_get_bundle:
            mock_get_bundle.return_value = (None, "app_name")

            self.recipe.set_parent_from(prefs, facts, "download")

            expected = "com.github.homebysix.download.TestApp"
            self.assertEqual(self.recipe["keys"]["ParentRecipe"], expected)

    def test_set_parent_from_removes_spaces(self):
        """Test that set_parent_from removes spaces from generated identifier."""
        prefs = {"RecipeIdentifierPrefix": "com.github.homebysix"}
        facts = {"app_name": "Test App With Spaces"}

        with patch(
            "scripts.recipe_robot_lib.recipe.get_bundle_name_info"
        ) as mock_get_bundle:
            mock_get_bundle.return_value = (None, "app_name")

            self.recipe.set_parent_from(prefs, facts, "munki")

            expected = "com.github.homebysix.munki.TestAppWithSpaces"
            self.assertEqual(self.recipe["keys"]["ParentRecipe"], expected)

    def test_append_processor_with_dict(self):
        """Test appending a processor as a dictionary."""
        processor_dict = {
            "Processor": "URLDownloader",
            "Arguments": {"url": "https://example.com/app.dmg"},
        }

        self.recipe.append_processor(processor_dict)

        self.assertEqual(len(self.recipe["keys"]["Process"]), 1)
        self.assertEqual(self.recipe["keys"]["Process"][0], processor_dict)

    def test_append_processor_with_abstract_processor(self):
        """Test appending an AbstractProcessor object."""
        # Create a mock that properly inherits from AbstractProcessor
        mock_processor = MagicMock(spec=AbstractProcessor)
        mock_processor_dict = {
            "Processor": "MockProcessor",
            "Arguments": {"test": "value"},
        }
        mock_processor.to_dict.return_value = mock_processor_dict

        # Make isinstance() return True for our mock
        with patch("scripts.recipe_robot_lib.recipe.isinstance") as mock_isinstance:
            mock_isinstance.side_effect = lambda obj, cls: (
                obj is mock_processor and cls.__name__ == "AbstractProcessor"
            ) or isinstance(obj, cls)

            self.recipe.append_processor(mock_processor)

        self.assertEqual(len(self.recipe["keys"]["Process"]), 1)
        self.assertEqual(self.recipe["keys"]["Process"][0], mock_processor_dict)
        mock_processor.to_dict.assert_called_once()

    def test_deepconvert_notifying_types(self):
        """Test deep conversion of notifying types to Python primitives."""
        # Create a recipe with notifying types
        recipe = Recipe("test", "Test recipe")

        # Add notifying types to the recipe
        recipe["keys"]["TestBool"] = NotifyingBool("test", True)
        recipe["keys"]["TestString"] = NotifyingString("test", "test string")
        recipe["keys"]["TestList"] = NotifyingList("test", [1, 2, 3])

        # Access the private method for testing
        converted = recipe._Recipe__deepconvert(recipe["keys"])

        self.assertIsInstance(converted["TestBool"], bool)
        self.assertIsInstance(converted["TestString"], str)
        # NotifyingList converts to regular list, but the check needs to be looser
        self.assertEqual(list(converted["TestList"]), [1, 2, 3])
        self.assertEqual(converted["TestBool"], True)
        self.assertEqual(converted["TestString"], "test string")

    def test_deepconvert_foundation_types(self):
        """Test deep conversion of Foundation types to Python primitives."""
        recipe = Recipe("test", "Test recipe")

        # Create Foundation objects
        ns_number = NSNumber.numberWithInt_(42)
        ns_array = NSArray.arrayWithArray_([1, 2, 3])
        ns_dict = NSDictionary.dictionaryWithDictionary_({"key": "value"})

        # Test conversion
        self.assertEqual(recipe._Recipe__deepconvert(ns_number), 42)
        self.assertEqual(recipe._Recipe__deepconvert(ns_array), [1, 2, 3])
        self.assertEqual(recipe._Recipe__deepconvert(ns_dict), {"key": "value"})

    def test_deepconvert_nested_structures(self):
        """Test deep conversion of nested data structures."""
        recipe = Recipe("test", "Test recipe")

        # Create nested structure with various types
        nested_data = {
            "string": NotifyingString("test", "test"),
            "bool": NotifyingBool("test", False),
            "list": NotifyingList(
                "test",
                [
                    NotifyingString("test", "item1"),
                    {"nested_dict": NotifyingBool("test", True)},
                ],
            ),
            "dict": {
                "nested_string": NotifyingString("test", "nested"),
                "nested_list": NotifyingList("test", [1, 2]),
            },
        }

        converted = recipe._Recipe__deepconvert(nested_data)

        self.assertEqual(converted["string"], "test")
        self.assertEqual(converted["bool"], False)
        self.assertEqual(list(converted["list"])[0], "item1")
        self.assertEqual(list(converted["list"])[1]["nested_dict"], True)
        self.assertEqual(converted["dict"]["nested_string"], "nested")
        self.assertEqual(list(converted["dict"]["nested_list"]), [1, 2])


class TestRecipeWriting(unittest.TestCase):
    """Tests for Recipe file writing functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.recipe = Recipe("download", "Downloads the app")
        self.recipe["keys"]["Identifier"] = "com.test.download.TestApp"
        self.recipe["keys"]["Input"]["NAME"] = "TestApp"
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up after each test method."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_write_plist_format(self):
        """Test writing recipe in plist format."""
        file_path = str(Path(self.temp_dir) / "test.recipe")

        self.recipe.write(file_path, fmt="plist")

        self.assertTrue(Path(file_path).exists())

        # Verify content
        with open(file_path, "rb") as f:
            content = plistlib.load(f)

        self.assertEqual(content["Identifier"], "com.test.download.TestApp")
        self.assertEqual(content["MinimumVersion"], "2.3")  # Should be updated
        self.assertEqual(content["Input"]["NAME"], "TestApp")

    def test_write_yaml_format(self):
        """Test writing recipe in YAML format."""
        file_path = str(Path(self.temp_dir) / "test.recipe.yaml")

        self.recipe.write(file_path, fmt="yaml")

        self.assertTrue(Path(file_path).exists())

        # Verify content
        with open(file_path, "rb") as f:
            content = yaml.safe_load(f)

        self.assertEqual(content["Identifier"], "com.test.download.TestApp")
        self.assertEqual(content["MinimumVersion"], "2.3")
        self.assertEqual(content["Input"]["NAME"], "TestApp")

    def test_write_minimum_version_update(self):
        """Test that MinimumVersion is updated to at least 2.3."""
        self.recipe["keys"]["MinimumVersion"] = "1.0.0"
        file_path = str(Path(self.temp_dir) / "test.recipe")

        self.recipe.write(file_path)

        with open(file_path, "rb") as f:
            content = plistlib.load(f)

        self.assertEqual(content["MinimumVersion"], "2.3")

    def test_write_minimum_version_preserve_higher(self):
        """Test that higher MinimumVersion is preserved."""
        self.recipe["keys"]["MinimumVersion"] = "3.0"
        file_path = str(Path(self.temp_dir) / "test.recipe")

        self.recipe.write(file_path)

        with open(file_path, "rb") as f:
            content = plistlib.load(f)

        self.assertEqual(content["MinimumVersion"], "3.0")

    def test_write_with_notifying_types(self):
        """Test writing recipe with notifying types gets converted properly."""
        from scripts.recipe_robot_lib.facts import NotifyingString, NotifyingBool

        # Add notifying types to recipe
        self.recipe["keys"]["TestString"] = NotifyingString("test", "test value")
        self.recipe["keys"]["TestBool"] = NotifyingBool("test", True)

        file_path = str(Path(self.temp_dir) / "test.recipe")
        self.recipe.write(file_path)

        # Verify the notifying types were converted to primitives
        with open(file_path, "rb") as f:
            content = plistlib.load(f)

        self.assertEqual(content["TestString"], "test value")
        self.assertEqual(content["TestBool"], True)


class TestRecipes(unittest.TestCase):
    """Tests for the Recipes class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.recipes = Recipes()

    def test_recipes_initialization(self):
        """Test Recipes initialization creates all recipe types."""
        self.assertEqual(len(self.recipes), len(RECIPE_TYPES))

        # Check that all recipe types are represented
        recipe_types = {recipe["type"] for recipe in self.recipes}
        expected_types = {rt["type"] for rt in RECIPE_TYPES}
        self.assertEqual(recipe_types, expected_types)

    def test_recipes_inherits_from_robo_list(self):
        """Test that Recipes properly inherits from RoboList."""
        # Test that Recipes instances behave like RoboList
        self.assertTrue(hasattr(self.recipes, "_list"))
        self.assertTrue(callable(getattr(self.recipes, "__getitem__", None)))
        self.assertTrue(callable(getattr(self.recipes, "__setitem__", None)))
        self.assertTrue(callable(getattr(self.recipes, "__delitem__", None)))
        self.assertTrue(callable(getattr(self.recipes, "append", None)))

        # Test basic list-like behavior
        initial_length = len(self.recipes)
        test_recipe = Recipe("test", "test")
        self.recipes.append(test_recipe)
        self.assertEqual(len(self.recipes), initial_length + 1)
        self.assertEqual(self.recipes[-1], test_recipe)

    def test_recipes_contains_recipe_objects(self):
        """Test that Recipes contains Recipe objects."""
        for recipe in self.recipes:
            self.assertIsInstance(recipe, Recipe)

    def test_recipes_preferred_settings(self):
        """Test that download and pkg recipes are preferred by default."""
        preferred_recipes = [r for r in self.recipes if r["preferred"]]
        preferred_types = {r["type"] for r in preferred_recipes}

        self.assertEqual(preferred_types, {"download", "pkg"})

    def test_recipes_access_by_type(self):
        """Test accessing recipes by type."""
        download_recipe = None
        munki_recipe = None

        for recipe in self.recipes:
            if recipe["type"] == "download":
                download_recipe = recipe
            elif recipe["type"] == "munki":
                munki_recipe = recipe

        self.assertIsNotNone(download_recipe)
        self.assertIsNotNone(munki_recipe)
        self.assertTrue(download_recipe["preferred"])
        self.assertFalse(munki_recipe["preferred"])

    def test_recipes_modification(self):
        """Test modifying recipes in the collection."""
        # Find the download recipe and modify it
        for recipe in self.recipes:
            if recipe["type"] == "download":
                recipe["keys"]["Identifier"] = "com.test.download.TestApp"
                break

        # Verify the modification persisted
        for recipe in self.recipes:
            if recipe["type"] == "download":
                self.assertEqual(
                    recipe["keys"]["Identifier"], "com.test.download.TestApp"
                )
                break

    def test_recipes_list_operations(self):
        """Test that standard list operations work on Recipes."""
        initial_count = len(self.recipes)

        # Test slicing
        first_three = self.recipes[:3]
        self.assertEqual(len(first_three), 3)

        # Test membership
        self.assertIn(self.recipes[0], self.recipes)

        # Test iteration
        count = 0
        for recipe in self.recipes:
            count += 1
        self.assertEqual(count, initial_count)


class TestRecipeIntegration(unittest.TestCase):
    """Integration tests for Recipe and Recipes working together."""

    def test_recipe_creation_and_modification_workflow(self):
        """Test a typical workflow of creating and modifying recipes."""
        recipes = Recipes()

        # Find and modify the download recipe
        download_recipe = None
        for recipe in recipes:
            if recipe["type"] == "download":
                download_recipe = recipe
                break

        self.assertIsNotNone(download_recipe)

        # Configure the download recipe
        download_recipe.set_description("Downloads TestApp from developer site")
        download_recipe["keys"]["Identifier"] = "com.test.download.TestApp"
        download_recipe["keys"]["Input"]["NAME"] = "TestApp"

        # Add a processor
        download_recipe.append_processor(
            {
                "Processor": "URLDownloader",
                "Arguments": {"url": "https://example.com/testapp.dmg"},
            }
        )

        # Verify the configuration
        self.assertEqual(
            download_recipe["keys"]["Description"],
            "Downloads TestApp from developer site",
        )
        self.assertEqual(len(download_recipe["keys"]["Process"]), 1)
        self.assertEqual(
            download_recipe["keys"]["Process"][0]["Processor"], "URLDownloader"
        )

    def test_recipe_parent_child_relationship(self):
        """Test setting up parent-child relationships between recipes."""
        recipes = Recipes()

        # Get download and pkg recipes
        download_recipe = None
        pkg_recipe = None

        for recipe in recipes:
            if recipe["type"] == "download":
                download_recipe = recipe
            elif recipe["type"] == "pkg":
                pkg_recipe = recipe

        # Set up download recipe
        download_recipe["keys"]["Identifier"] = "com.test.download.TestApp"

        # Set pkg recipe to use download as parent
        pkg_recipe.set_parent("com.test.download.TestApp")

        self.assertEqual(
            pkg_recipe["keys"]["ParentRecipe"], "com.test.download.TestApp"
        )


if __name__ == "__main__":
    unittest.main()
