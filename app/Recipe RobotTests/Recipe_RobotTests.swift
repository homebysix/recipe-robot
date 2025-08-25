//
//  Recipe_RobotTests.swift
//
//  Recipe Robot Tests
//  Copyright 2015-2025 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
//
//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.

import Cocoa
import XCTest
@testable import Recipe_Robot

class Recipe_RobotTests: XCTestCase {

    override func setUp() {
        super.setUp()
        // Reset defaults between tests
        UserDefaults.standard.removePersistentDomain(forName: Bundle.main.bundleIdentifier!)
    }

    override func tearDown() {
        super.tearDown()
    }

    // MARK: - RecipeType Tests

    func testRecipeTypeValues() {
        XCTAssertEqual(RecipeType.Download.value, "download")
        XCTAssertEqual(RecipeType.Munki.value, "munki")
        XCTAssertEqual(RecipeType.Pkg.value, "pkg")
        XCTAssertEqual(RecipeType.Install.value, "install")
        XCTAssertEqual(RecipeType.Jamf.value, "jamf")
        XCTAssertEqual(RecipeType.LANrev.value, "lanrev")
        XCTAssertEqual(RecipeType.SCCM.value, "sccm")
        XCTAssertEqual(RecipeType.DS.value, "ds")
        XCTAssertEqual(RecipeType.Filewave.value, "filewave")
        XCTAssertEqual(RecipeType.BigFix.value, "bigfix")
    }

    func testRecipeTypeDownloadRequiredTypes() {
        let downloadType = RecipeType.Download
        let requiredTypes = downloadType.requiredTypes

        XCTAssertEqual(requiredTypes.count, 1)
        XCTAssertTrue(requiredTypes.contains(.Download))
    }

    func testRecipeTypeMunkiRequiredTypes() {
        let munkiType = RecipeType.Munki
        let requiredTypes = munkiType.requiredTypes

        XCTAssertEqual(requiredTypes.count, 2)
        XCTAssertTrue(requiredTypes.contains(.Munki))
        XCTAssertTrue(requiredTypes.contains(.Download))
    }

    func testRecipeTypePkgRequiredTypes() {
        let pkgType = RecipeType.Pkg
        let requiredTypes = pkgType.requiredTypes

        XCTAssertEqual(requiredTypes.count, 2)
        XCTAssertTrue(requiredTypes.contains(.Pkg))
        XCTAssertTrue(requiredTypes.contains(.Download))
    }

    func testRecipeTypeJamfRequiredTypes() {
        let jamfType = RecipeType.Jamf
        let requiredTypes = jamfType.requiredTypes

        XCTAssertEqual(requiredTypes.count, 3)
        XCTAssertTrue(requiredTypes.contains(.Jamf))
        XCTAssertTrue(requiredTypes.contains(.Pkg))
        XCTAssertTrue(requiredTypes.contains(.Download))
    }

    func testRecipeTypeRequiredTypeValues() {
        let jamfType = RecipeType.Jamf
        let requiredValues = jamfType.requiredTypeValues

        XCTAssertTrue(requiredValues.contains("jamf"))
        XCTAssertTrue(requiredValues.contains("pkg"))
        XCTAssertTrue(requiredValues.contains("download"))
    }

    func testRecipeTypeStaticValues() {
        let values = RecipeType.values
        let expectedValues = ["download", "munki", "pkg", "install", "jamf", "lanrev", "sccm", "ds", "filewave", "bigfix"]

        XCTAssertEqual(values.count, expectedValues.count)
        for value in expectedValues {
            XCTAssertTrue(values.contains(value))
        }
    }

    func testRecipeTypeStaticCases() {
        let cases = RecipeType.cases

        XCTAssertEqual(cases.count, 10)
        XCTAssertTrue(cases.contains(.Download))
        XCTAssertTrue(cases.contains(.Munki))
        XCTAssertTrue(cases.contains(.Pkg))
        XCTAssertTrue(cases.contains(.Install))
        XCTAssertTrue(cases.contains(.Jamf))
        XCTAssertTrue(cases.contains(.LANrev))
        XCTAssertTrue(cases.contains(.SCCM))
        XCTAssertTrue(cases.contains(.DS))
        XCTAssertTrue(cases.contains(.Filewave))
        XCTAssertTrue(cases.contains(.BigFix))
    }

    // MARK: - Defaults Tests

    func testDefaultsSharedInstance() {
        let instance1 = Defaults.sharedInstance
        let instance2 = Defaults.sharedInstance

        XCTAssertTrue(instance1 === instance2, "Defaults should be a singleton")
    }

    func testDefaultsRecipeTypes() {
        let defaults = Defaults.sharedInstance

        // Test initial state (should be nil)
        XCTAssertNil(defaults.recipeTypes)

        // Test setting and getting recipe types
        let testTypes: Set<String> = ["download", "munki", "pkg"]
        defaults.recipeTypes = testTypes

        XCTAssertEqual(defaults.recipeTypes, testTypes)

        // Test setting to nil
        defaults.recipeTypes = nil
        XCTAssertNil(defaults.recipeTypes)
    }

    func testDefaultsIgnoreExisting() {
        let defaults = Defaults.sharedInstance

        // Test default value (should be false)
        XCTAssertFalse(defaults.ignoreExisting)

        // Test setting to true
        defaults.ignoreExisting = true
        XCTAssertTrue(defaults.ignoreExisting)

        // Test setting back to false
        defaults.ignoreExisting = false
        XCTAssertFalse(defaults.ignoreExisting)
    }

    func testDefaultsRecipeCreateLocation() {
        let defaults = Defaults.sharedInstance

        // Test default value (should set automatically)
        let defaultLocation = defaults.recipeCreateLocation
        let expectedDefault = "\(NSHomeDirectory())/Library/AutoPkg/Recipe Robot Output"
        XCTAssertEqual(defaultLocation, expectedDefault)

        // Test setting custom location
        let customLocation = "/custom/path"
        defaults.recipeCreateLocation = customLocation
        XCTAssertEqual(defaults.recipeCreateLocation, customLocation)

        // Test setting to nil resets to default
        defaults.recipeCreateLocation = nil
        // After setting to nil, getter automatically sets it to default again
        XCTAssertEqual(defaults.recipeCreateLocation, expectedDefault)
    }

    func testDefaultsRecipeCreateCount() {
        let defaults = Defaults.sharedInstance

        // Test default value (should be 0)
        XCTAssertEqual(defaults.recipeCreateCount, 0)

        // Test setting count
        defaults.recipeCreateCount = 5
        XCTAssertEqual(defaults.recipeCreateCount, 5)

        // Test incrementing
        defaults.recipeCreateCount += 1
        XCTAssertEqual(defaults.recipeCreateCount, 6)
    }

    func testDefaultsInitialized() {
        let defaults = Defaults.sharedInstance

        // Test default value (should be false)
        XCTAssertFalse(defaults.initialized)

        // Test setting to true
        defaults.initialized = true
        XCTAssertTrue(defaults.initialized)
    }

    // MARK: - String Extensions Tests

    func testStringSplitByLine() {
        let testString = "Line 1\nLine 2\r\nLine 3"
        let lines = testString.splitByLine()

        // splitByLine uses components(separatedBy: CharacterSet.newlines)
        // This will split on both \n and \r\n, potentially creating empty strings
        XCTAssertTrue(lines.count >= 3, "Should have at least 3 lines")
        XCTAssertEqual(lines[0], "Line 1")
        XCTAssertEqual(lines[1], "Line 2")
        // The last element might be "Line 3" depending on how \r\n is handled
        XCTAssertTrue(lines.contains("Line 3"), "Should contain 'Line 3'")
    }

    func testStringSplitBySpace() {
        let testString = "word1 word2   word3"
        let words = testString.splitBySpace()

        XCTAssertTrue(words.contains("word1"))
        XCTAssertTrue(words.contains("word2"))
        XCTAssertTrue(words.contains("word3"))
    }

    func testStringTrimmedFull() {
        let testString = "  \n\t Hello World \t\n  "
        let trimmed = testString.trimmedFull

        XCTAssertEqual(trimmed, "Hello World")
    }

    func testStringTrimmed() {
        let testString = "  Hello World  "
        let trimmed = testString.trimmed

        XCTAssertEqual(trimmed, "Hello World")
    }

    func testStringColor() {
        let errorString = "This is an [ERROR] message"
        let warningString = "This is a [WARNING] message"
        let reminderString = "This is a [REMINDER] message"
        let normalString = "This is a normal message"

        XCTAssertEqual(errorString.color, NSColor.systemRed)
        XCTAssertEqual(warningString.color, NSColor.systemOrange)
        XCTAssertEqual(reminderString.color, NSColor.systemGreen)
        XCTAssertEqual(normalString.color, NSColor.textColor)
    }

    func testStringBracketedColor() {
        let errorString = "This is an [ERROR] message"
        let attributedString = errorString.bracketedColor

        XCTAssertEqual(attributedString.string, errorString)

        let attributes = attributedString.attributes(at: 0, effectiveRange: nil)
        let color = attributes[NSAttributedString.Key.foregroundColor] as? NSColor
        XCTAssertEqual(color, NSColor.systemRed)
    }

    // MARK: - Dictionary Extensions Tests

    func testDictionaryUpdate() {
        var dict1 = ["key1": "value1", "key2": "value2"]
        let dict2 = ["key2": "newValue2", "key3": "value3"]

        dict1.update(other: dict2)

        XCTAssertEqual(dict1["key1"], "value1")
        XCTAssertEqual(dict1["key2"], "newValue2") // Should be updated
        XCTAssertEqual(dict1["key3"], "value3")   // Should be added
        XCTAssertEqual(dict1.count, 3)
    }

    // MARK: - RecipeRobotTask Tests

    func testRecipeRobotTaskExecutable() {
        let task = RecipeRobotTask()
        let expectedPath = Bundle.main.path(forResource: "scripts/recipe-robot", ofType: nil)!

        XCTAssertEqual(task.executable, expectedPath)
    }

    func testRecipeRobotTaskArgsDefault() {
        let task = RecipeRobotTask()
        task.appOrRecipe = "/path/to/app.app"

        let args = task.args

        XCTAssertNotNil(args)
        XCTAssertTrue(args!.contains("--verbose"))
        XCTAssertTrue(args!.contains("--app-mode"))
        XCTAssertTrue(args!.contains("--"))
        XCTAssertTrue(args!.contains("/path/to/app.app"))
    }

    func testRecipeRobotTaskArgsWithIgnoreExisting() {
        let task = RecipeRobotTask()
        task.appOrRecipe = "/path/to/app.app"
        task.ignoreExisting = true

        let args = task.args

        XCTAssertNotNil(args)
        XCTAssertTrue(args!.contains("--ignore-existing"))
    }

    func testRecipeRobotTaskArgsWithoutIgnoreExisting() {
        let task = RecipeRobotTask()
        task.appOrRecipe = "/path/to/app.app"
        task.ignoreExisting = false

        let args = task.args

        XCTAssertNotNil(args)
        XCTAssertFalse(args!.contains("--ignore-existing"))
    }

    func testRecipeRobotTaskArgsWithDefaultsIgnoreExisting() {
        // Set the default to true
        Defaults.sharedInstance.ignoreExisting = true

        let task = RecipeRobotTask()
        task.appOrRecipe = "/path/to/app.app"
        // Don't set task.ignoreExisting, should use default

        let args = task.args

        XCTAssertNotNil(args)
        XCTAssertTrue(args!.contains("--ignore-existing"))
    }

    func testRecipeRobotTaskAppOrRecipeName() {
        let task = RecipeRobotTask()
        task.appOrRecipe = "/path/to/TestApp.app"

        XCTAssertEqual(task.appOrRecipeName, "TestApp.app")
    }

    func testRecipeRobotTaskOutputDefault() {
        let task = RecipeRobotTask()

        XCTAssertEqual(task.output, "~/Library/AutoPkg/Recipe Robot Output/")
    }

    // MARK: - Task Tests

    func testTaskInitialization() {
        let executable = "/usr/bin/ls"
        let args = ["-la", "/tmp"]

        let task = Task(executable: executable, args: args)

        XCTAssertEqual(task.executable, executable)
        XCTAssertEqual(task.args, args)
    }

    func testTaskErrorEnum() {
        XCTAssertEqual(Task.ErrorEnum.NotExecutable.localizedDescription, "The specified path is not executable.")
        XCTAssertEqual(Task.ErrorEnum.BadInput.localizedDescription, "The input data is bad.")
        XCTAssertEqual(Task.ErrorEnum.BadOutput.localizedDescription, "The received data was bad.")
        XCTAssertEqual(Task.ErrorEnum.NonZeroExit.localizedDescription, "Error running the command.")
    }

    // MARK: - Performance Tests

    func testRecipeTypePerformance() {
        self.measure {
            for _ in 0..<1000 {
                let _ = RecipeType.cases
                let _ = RecipeType.values
            }
        }
    }

    func testStringExtensionsPerformance() {
        let testString = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"

        self.measure {
            for _ in 0..<1000 {
                let _ = testString.splitByLine()
                let _ = testString.trimmedFull
            }
        }
    }

}
