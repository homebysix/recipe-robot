//
//  RecipeRobotTask.swift
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

import Cocoa

class RecipeRobotTask: NSObject {

    // MARK: Private
    private var task = NSTask()
    private var appBundle: NSBundle?

    // MARK: Public
    var ignoreExisting: Bool?

    var appOrRecipe: String = "" {
        didSet {
            appBundle = NSBundle(path: appOrRecipe)
        }
    }

    var appIcon: NSImage? {
        if let dict = appBundle?.infoDictionary {
            var iconName: String? = nil

            if let name = dict["CFBundleIconFile"] as? String {
                iconName = name
            } else if let more = dict["CFBundleIcons"] as? [String: AnyObject],
                evenMore = more["CFBundlePrimaryIcon"] as? [String: AnyObject],
                array = evenMore["CFBundleIconFiles"] as? [String], name = array.last {
                    iconName = name
            }

            if let iconName = iconName, iconFile = appBundle?.pathForImageResource(iconName){
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

    var recipeTypes = []
    var output: String = "~/Library/AutoPkg/Recipe Robot Output/"
    var includeExisting : Bool = false

    var isProcessing: Bool {
        return self.task.running
    }

    func cancel(){
        if self.task.running {
            self.task.terminate()
        }
    }

    func createRecipes(progress: (progress: String) -> Void,
                       completion: (error: NSError? ) -> Void) {

        task.launchPath = "/usr/bin/python"
        task.arguments = constructTaskArgs()
        task.environment = constructTaskEnvironment()

        let out = NSPipe()
        task.standardOutput = out

        let err = NSPipe()
        task.standardError = err

        out.fileHandleForReading.readabilityHandler = {
            handle in
                let data = handle.availableData
                if let str = NSString(data: data, encoding: NSUTF8StringEncoding) as? String {
                    NSOperationQueue.mainQueue().addOperationWithBlock({ () -> Void in
                        progress(progress: str)
                    })
                }
        }

        let errData = NSMutableData()
        err.fileHandleForReading.readabilityHandler = {
            handle in
                let data = handle.availableData
                errData.appendData(data)
                if let str = NSString(data: data, encoding: NSUTF8StringEncoding) as? String {
                    NSOperationQueue.mainQueue().addOperationWithBlock({ () -> Void in
                        progress(progress: str)
                    })
                }
        }


        task.terminationHandler = {
            aTask in
                // nil out the readabilityHandlers to prevent retension.
                out.fileHandleForReading.readabilityHandler = nil
                err.fileHandleForReading.readabilityHandler = nil

                var error: NSError?
                if let dataString = NSString(data: errData, encoding:NSUTF8StringEncoding) as? String {
                    error = RecipeRobotTask.taskError(dataString, exitCode: aTask.terminationStatus)
                }

                NSOperationQueue.mainQueue().addOperationWithBlock({ () -> Void in
                    completion(error: error)
                })
        }

        task.launch()
    }

    private func constructTaskEnvironment() -> Dictionary<String, String> {
        let dict = NSProcessInfo.processInfo().environment
        /// Possibly do more here some day.
        return dict
    }

    private func constructTaskArgs() -> [String] {
        var args = [String]()

        if let recipeRobotPy = NSBundle.mainBundle().pathForResource("scripts/recipe-robot", ofType: nil){

            args.appendContentsOf([recipeRobotPy, "-v", "--app-mode"])

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

    private class func taskError(string: String, exitCode: Int32) -> NSError {
        print(string)
        let error = NSError(domain: "recipe-robot", code: Int(exitCode), userInfo: [NSLocalizedDescriptionKey: string])
        return error
    }

}
