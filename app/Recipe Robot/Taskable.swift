//
//  Taskable.swift
//
//  Created by Eldon on 11/8/15.
//  Copyright © 2015 EEAapps.
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

protocol Taskable: ChainableTask {
    var executable: String { get }
    var args: [String]? { get set }
    var env: [String: String]? { get set }
}

protocol InteractableTaskable: Taskable {
    var expectedPrompts: [String] { get }
    func stdin(message:(String) -> String?) -> Self
    func isInteractive(string: String) -> Bool
}

protocol ChainableTask {
    func stdout(message: (String) -> (Void)) -> Self
    func stderr(message: (String) -> (Void)) -> Self
    func completed(complete: (ErrorType)? -> (Void)) -> Self
    func run() -> Self
}

protocol CancelableTask {
    var cancelledHandle:((Void) -> (Void))? { get set }
    func cancelled(cancelled:(Void) -> (Void)) -> Self
    func cancel()
}

extension CancelableTask {
    mutating func cancelled(cancelled:(Void) -> (Void)) -> Self {
        cancelledHandle = cancelled
        return self
    }
}
extension Taskable where Self: InteractableTaskable {
    var expectedPrompts: [String] {
        return [ "y/n: ", "Y/N: ", "Password: " ]
    }
}

extension NSTask: ChainableTask {
    func stderr(message: (String) -> (Void)) -> Self {
        standardError = NSPipe()
        standardError?.fileHandleForReading.readabilityHandler = {
            fh in
            let data = fh.availableData
            guard let decoded = NSString(data: data, encoding: NSUTF8StringEncoding) as? String else {
                return
            }
            message(decoded)
        }
        return self
    }

    func stdout(message: (String) -> (Void)) -> Self {
        standardOutput = NSPipe()
        standardOutput?.fileHandleForReading.readabilityHandler = {
            fh in
            let data = fh.availableData
            guard let decoded = NSString(data: data, encoding: NSUTF8StringEncoding) as? String else {
                return
            }
            message(decoded)
        }
        return self
    }

    func completed(complete: (ErrorType)? -> (Void)) -> Self {
        terminationHandler = {
            aTask in
            if ( aTask.terminationStatus != 0 ){
                complete(nil)
            } else {
                complete(Task.Error.NonZeroExit)
            }
        }
        return self
    }

    func run() -> Self {
        launch()
        return self
    }
}

class Task: Taskable, CancelableTask {
    enum Error: ErrorType {
        case NotExecutable, BadInput, BadOutput, NonZeroExit

        var localizedDescription: String {
            switch self {
            case .NotExecutable:
                return "The specified path is not executable."
            case .BadInput:
                return "The input data is bad."
            case .BadOutput:
                return "The received data was bad."
            case .NonZeroExit:
                return "Error running the command"
            }
        }
    }

    let task = NSTask()
    var args: [String]?
    var env: [String: String]?

    private var path: String?

    var executable: String {
        return path!
    }

    convenience init(executable: String){
        self.init()
        self.path = executable
    }

    convenience init(executable: String, args: [String]){
        self.init(executable: executable)
        self.args = args
    }

    func stderr(message:(String) -> (Void)) -> Self {
        self.task.standardError = NSPipe()
        task.standardError?.fileHandleForReading.readabilityHandler = {
            fh in
            let data = fh.availableData
            guard let decoded = NSString(data: data, encoding: NSUTF8StringEncoding) as? String else {
                return
            }
            dispatch_async(dispatch_get_main_queue(), {
                message(decoded)
            })
        }
        return self
    }

    func stdout(message: (String) -> (Void)) -> Self {
        self.task.standardOutput = NSPipe()

        task.standardOutput?.fileHandleForReading.readabilityHandler = {
            fh in

            let data = fh.availableData
            guard let decoded = NSString(data: data, encoding: NSUTF8StringEncoding) as? String else {
                return
            }
            dispatch_async(dispatch_get_main_queue(), {
                message(decoded)
            })
        }
        return self
    }

    func completed(complete: (ErrorType)? -> (Void)) -> Self {
        task.terminationHandler = {
            aTask in

            let error: ErrorType? = ( aTask.terminationStatus == 0 ) ? nil : Task.Error.NonZeroExit

            dispatch_async(dispatch_get_main_queue(), {
                complete(error)
            })

            aTask.standardError?.fileHandleForReading.readabilityHandler = nil
            aTask.standardOutput?.fileHandleForReading.readabilityHandler = nil
        }
        return self
    }

    func run() -> Self {
        task.launchPath = executable

        if let args = args {
            task.arguments = args
        }

        var environment = NSProcessInfo.processInfo().environment
        if let env = env {
            for (val, key) in env {
                environment[key] = val
            }
        }
        environment["NSUnbuffeedIO"] = "YES"
        if !task.running && NSFileManager.defaultManager().isExecutableFileAtPath(executable){
            task.launch()
        }

        return self
    }

    internal var cancelledHandle:((Void) -> (Void))?
    func cancelled(cancelled:(Void) -> (Void)) -> Self {
        cancelledHandle = cancelled
        return self
    }

    func cancel() {
        if task.running {
            if (cancelledHandle != nil) {
                cancelledHandle!()
            }
            task.terminate()
        }
    }
}

class InteractiveTask: Task, InteractableTaskable {
    private var inHandler:((String) -> (String)?)?

    func isInteractive(string: String) -> Bool {
        return expectedPrompts.filter({
            val in
            return string.lowercaseString.hasSuffix(val.lowercaseString)
        }).count > 0
    }

    func stdin(message: (String) -> (String)?) -> Self {
        inHandler = message
        return self
    }

    override func stdout(message: (String) -> (Void)) -> Self {
        self.task.standardOutput = NSPipe()

        task.standardOutput?.fileHandleForReading.readabilityHandler = { [weak self]
            fh in
            guard let _self = self else {
                return
            }
            let data = fh.availableData
            guard let decoded = NSString(data: data, encoding: NSUTF8StringEncoding) as? String else {
                return
            }

            if _self.isInteractive(decoded) {
                guard let results = _self.inHandler!(decoded) else {
                    return
                }
                if (results.isEmpty && _self.task.running){
                    guard let data = results.dataUsingEncoding(NSUTF8StringEncoding) else {
                        return
                    }
                    guard let inHandle = _self.task.standardInput?.fileHandleForWriting else {
                        return
                    }
                    inHandle.writeData(data)
                }
            } else {
                message(decoded)
            }
        }
        return self
    }
}
