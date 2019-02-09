//
//  Defaults.swift
//
//  Recipe Robot
//  Copyright 2015-2018 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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

import Foundation

class Defaults: NSObject {
    static let sharedInstance = Defaults()

    override init() {
        super.init()
    }

    private let defaults = UserDefaults.standard 
    var recipeTypes: Set<String>? {
        get {
            guard let recipeTypes = defaults.stringArray(forKey: "RecipeTypes") else {
                return nil
            }
            return Set(recipeTypes)
        }
        set {
            if newValue == nil {
                defaults.setValue(newValue, forKey: "RecipeTypes")
            } else {
                defaults.setValue(Array(newValue!), forKey: "RecipeTypes")
            }
        }
    }

    var ignoreExisting: Bool {
        get {
            return defaults.bool(forKey: "IgnoreExisting")
        }
        set {
            defaults.set(newValue, forKey: "IgnoreExisting")
        }
    }

    var recipeCreateLocation: String? {
        get {
            guard let recipeCreateLocation = defaults.string(forKey: "RecipeCreateLocation") else {
                self.recipeCreateLocation = "\(NSHomeDirectory())/Library/AutoPkg/Recipe Robot Output"
                return self.recipeCreateLocation
            }
            return recipeCreateLocation
        }
        set {
            defaults.setValue(newValue, forKey: "RecipeCreateLocation")
        }
    }

    var dsPackagePath: String? {
        get {
            return defaults.string(forKey: "DSPackagesPath")
        }
        set {
            defaults.setValue(newValue, forKey: "DSPackagesPath")
        }
    }

    var recipeCreateCount: Int {
        get {
            return defaults.integer(forKey: "RecipeCreateCount")
        }
        set {
            defaults.set(newValue, forKey: "RecipeCreateCount")
        }
    }

    var initialized: Bool {
        get {
            return defaults.bool(forKey: "Initialized")
        }
        set {
            defaults.set(newValue, forKey: "Initialized")
        }
    }
}
