//
//  Defaults.swift
//  Recipe Robot
//
//  Created by Eldon on 10/27/15.
//  Copyright (c) 2015 Eldon Ahrold. All rights reserved.
//

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