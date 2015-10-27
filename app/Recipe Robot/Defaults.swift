//
//  Defaults.swift
//  Recipe Robot
//
//  Created by Eldon on 10/27/15.
//  Copyright © 2015 Linde Group. All rights reserved.
//

import Foundation


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
}