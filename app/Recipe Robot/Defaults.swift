//
//  Defaults.swift
//
//  Recipe Robot
//  Copyright 2015 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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

//enum Defs: Int {
//    case RecipeTypes, IgnoreExisting, RecipeCreateLocation, DSPackagePath
//
//    var key: String {
//        switch self {
//        case .RecipeTypes: return "RecipeTypes"
//        case .IgnoreExisting: return "IgnoreExisting"
//        case .RecipeCreateLocation: return "RecipeCreateLocation"
//        case .DSPackagePath: return "DSPackagePath"
//        }
//    }
//
//    func set()
//}

class Defaults: NSObject {
    static let sharedInstance = Defaults()

    override init() {
        super.init()
        defaults.registerDefaults(["RecipeCreateCount": 0,
                                    "RecipeCreateLocation": "\(NSHomeDirectory())/Library/AutoPkg/RecipeRobot"])
    }

    private let defaults = NSUserDefaults.standardUserDefaults()
    var recipeTypes: [String]? {
        get {
            return defaults.stringArrayForKey("RecipeTypes")
        }
        set {
            defaults.setValue(newValue, forKey: "RecipeTypes")
        }
    }

    var ignoreExisting: Bool {
        get {
            return defaults.boolForKey("IgnoreExisting")
        }
        set {
            defaults.setBool(newValue, forKey: "IgnoreExisting")
        }
    }

    var recipeCreateLocation: String? {
        get {
            return defaults.stringForKey("RecipeCreateLocation")
        }
        set {
            defaults.setValue(newValue, forKey: "RecipeCreateLocation")
        }
    }

    var dsPackagePath: String? {
        get {
            return defaults.stringForKey("DSPackagesPath")
        }
        set {
            defaults.setValue(newValue, forKey: "DSPackagesPath")
        }
    }

    var recipeCreateCount: Int {
        get {
            return defaults.integerForKey("RecipeCreateCount")
        }
        set {
            defaults.setInteger(newValue, forKey: "RecipeCreateCount")
        }
    }

    var initialized: Bool {
        get {
            return defaults.boolForKey("Initialized")
        }
        set {
            defaults.setBool(newValue, forKey: "Initialized")
        }
    }
}
