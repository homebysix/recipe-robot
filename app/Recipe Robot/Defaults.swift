//
//  Defaults.swift
//  Recipe Robot
//
//  Created by Eldon on 10/27/15.
//  Copyright © 2015 Linde Group. All rights reserved.
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
}