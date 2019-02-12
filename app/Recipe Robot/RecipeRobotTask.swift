//
//  RecipeRobotTask.swift
//
//  Recipe Robot
//  Copyright 2015-2019 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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



class RecipeRobotTask: Task {

    // Task Overrides
    override var executable: String {
        return "/usr/bin/python"
    }

    override var args: [String]? {
        get {
            var args = [String]()

            if let recipeRobotPy = Bundle.main.path(forResource: "scripts/recipe-robot", ofType: nil){

                args.append(contentsOf:[recipeRobotPy, "--verbose", "--app-mode"])

                // Honor the ignoreExisting of the instance first
                // If that's unset apply the setting from defaults.
                if let ignore = self.ignoreExisting {
                    if ignore {
                        args.append("--ignore-existing")
                    }
                } else if Defaults.sharedInstance.ignoreExisting {
                    args.append("--ignore-existing")
                }
                args.append(self.appOrRecipe)
            }
            return args
        }
        set {}
    }

    // MARK: Private
    private var appBundle: Bundle?

    // MARK: Public
    var ignoreExisting: Bool?

    var appOrRecipe: String = "" {
        didSet {
            appBundle = Bundle(path: appOrRecipe)
        }
    }

    var appIcon: NSImage? {
        if let dict = appBundle?.infoDictionary {
            var iconName: String? = nil

            if let name = dict["CFBundleIconFile"] as? String {
                iconName = name
            } else if let more = dict["CFBundleIcons"] as? [String: AnyObject],
                let evenMore = more["CFBundlePrimaryIcon"] as? [String: AnyObject],
                let array = evenMore["CFBundleIconFiles"] as? [String], let name = array.last {
                    iconName = name
            }

            if let iconName = iconName, let iconFile = appBundle?.pathForImageResource(iconName){
                if let image = NSImage(contentsOfFile: iconFile){
                    return image
                }
            }
        }
        return nil
    }

    var appOrRecipeName: String? {
        return (self.appOrRecipe as NSString).lastPathComponent
    }

    // var recipeTypes = []
    var output: String = "~/Library/AutoPkg/Recipe Robot Output/"
    var includeExisting : Bool = false

    private class func taskError(string: String, exitCode: Int32) -> NSError {
        print(string)
        let error = NSError(domain: "recipe-robot", code: Int(exitCode), userInfo: [NSLocalizedDescriptionKey: string])
        return error
    }

}
