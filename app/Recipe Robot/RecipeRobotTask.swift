//
//  RecipeRobotTask.swift
//  Recipe Robot
//
//  Created by Eldon Ahrold on 7/23/15.
//  Copyright (c) 2015 Eldon Ahrold. All rights reserved.
//

import Cocoa

class RecipeRobotTask: NSObject {

    // MARK: Public
    var appOrRecipe: String = ""
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

    func createRecipes(progress: (progress: String) -> Void, completion: (error: NSError? ) -> Void) {

        task.launchPath = "/usr/bin/python"
        task.arguments = self.constructTaskArgs() as? [String]

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

    // MARK: Private
    private var task = NSTask()

    private func constructTaskEnvironment() -> Dictionary<String, AnyObject> {
        let dict = Dictionary<String, AnyObject>()
        return dict
    }

    private func constructTaskArgs() -> [AnyObject] {
        var args = [AnyObject]()

        if let recipeRobotPy = NSBundle.mainBundle().pathForResource("scripts/recipe-robot", ofType: nil){
            args.appendContentsOf([recipeRobotPy, "-v", self.appOrRecipe])
        }

        return args
    }

    private class func taskError(string: String, exitCode: Int32) -> NSError {
        print(string)
        let error = NSError(domain: "recipe-robot", code: Int(exitCode), userInfo: [NSLocalizedDescriptionKey: string])
        return error
    }

}
