//
//  Taskable.swift
//
//  Recipe Robot
//  Copyright 2015-2020 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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
    func stdin(message: @escaping (String) -> String?) -> Self
    func isInteractive(string: String) -> Bool
}

typealias CancellationHandler = () -> (Void)
protocol CancelableTask {
    func cancelled(handler: @escaping CancellationHandler) -> Self
    func cancel()
}

protocol ChainableTask : CancelableTask {
    func stdout(message: @escaping (String) -> (Void)) -> ChainableTask
    func stderr(message: @escaping (String) -> (Void)) -> ChainableTask
    func completed(complete: @escaping (Error?) -> (Void)) -> ChainableTask
    func run() -> Self
}



extension Taskable where Self: InteractableTaskable {
    var expectedPrompts: [String] {
        return [ "y/n: ", "Y/N: ", "Password: " ]
    }
}

struct ProcessAssociatedData {
    static var cancellationHandlerTable:[Int32:CancellationHandler] = [:]
    static func removeCancellationHandler(for process:Process) {
          cancellationHandlerTable[process.processIdentifier] = nil
    }
    static func registerCancellationHandler(for process:Process, cancellationHandler: @escaping CancellationHandler) {
          cancellationHandlerTable[process.processIdentifier] = cancellationHandler
   }
    static func cancellationHandler(for process:Process) -> CancellationHandler? {
         return cancellationHandlerTable[process.processIdentifier]
    }
}

extension Process: ChainableTask, CancelableTask {

    // its not allowed to just add a var on a Process, because we don't own the class,
    // so either we have to subclass Process, or we fake a var parameter by building a static table, or
    // we stuff data in using the objc runtime using objc_getAssociatedObject.  I'm going with the static table approach
    // ProcessAssociatedData encapsulates a dictionary of [processIdentifier : cancellationHandler]

    func cancelled(handler: @escaping CancellationHandler) -> Self {
        ProcessAssociatedData.registerCancellationHandler(for:self, cancellationHandler:handler)
        if (terminationHandler == nil) {
            // terminationHandler may also be set in the func completed() below, so we don't want to overwrite that.
            terminationHandler = ({
                _ in
                ProcessAssociatedData.removeCancellationHandler(for:self)
            })

        }
        return self
    }

    func cancel() {
        if self.isRunning {
            if let handler = ProcessAssociatedData.cancellationHandler(for:self) {
                ProcessAssociatedData.removeCancellationHandler(for:self)
                handler()
            }
            self.terminate()
        }
    }

    func stderr(message: @escaping (String) -> (Void)) -> ChainableTask {
        let standardErrPipe = Pipe()
        standardErrPipe.fileHandleForReading.readabilityHandler = ({
            fh in
            let data = fh.availableData
            guard let decoded = String(data: data, encoding: String.Encoding.utf8) else {
                return
            }
            message(decoded)
        })
        standardError = standardErrPipe
        return self
    }

    func stdout(message: @escaping (String) -> (Void)) -> ChainableTask {
        let standardOutPipe = Pipe()
        standardOutPipe.fileHandleForReading.readabilityHandler = ({
            fh in
            let data = fh.availableData
            guard let decoded = String(data: data, encoding: String.Encoding.utf8) else {
                return
            }
            message(decoded)
        })
        standardOutput = standardOutPipe
        return self
    }

    func completed(complete: @escaping (Error?) -> (Void)) -> ChainableTask {
        terminationHandler = ({
            aTask in
            if ( aTask.terminationStatus != 0 ){
                complete(nil)
            } else {
                complete(Task.ErrorEnum.NonZeroExit)
            }
            ProcessAssociatedData.removeCancellationHandler(for:self)
        })
        return self
    }

    func run() -> Self {
        launch()
        return self
    }
}

class Task: Taskable, CancelableTask {
    enum ErrorEnum: Error {
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
                return "Error running the command."
            }
        }
    }

    let process = Process()
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

    func stderr(message: @escaping (String) -> (Void)) -> ChainableTask {
        let stdErrorPipe = Pipe()
        stdErrorPipe.fileHandleForReading.readabilityHandler = ({
            fh in
            let data = fh.availableData
            guard let decoded = String(data: data, encoding: String.Encoding.utf8) else {
                print("Unable to decode stderr.")
                return
            }
            DispatchQueue.main.async {
                message(decoded)
            }
        })
        self.process.standardError = stdErrorPipe
        return self
    }

    func stdout(message: @escaping (String) -> (Void)) -> ChainableTask {
        let stdOutPipe = Pipe()
        stdOutPipe.fileHandleForReading.readabilityHandler = ({
            fh in
            let data = fh.availableData
            guard let decoded = String(data: data, encoding: String.Encoding.utf8) else {
                print("Unable to decode stdout.")
                return
            }
            DispatchQueue.main.async {
                message(decoded)
            }
        })
        self.process.standardOutput = stdOutPipe
        return self
    }

    func completed(complete: @escaping (Error?) -> (Void)) -> ChainableTask {
        process.terminationHandler = ({
            aTask in

            let error: Error? = ( aTask.terminationStatus == 0 ) ? nil : Task.ErrorEnum.NonZeroExit
            DispatchQueue.main.async {
                complete(error)
            }
            if let stdErrorPipe = aTask.standardError as? Pipe {
                stdErrorPipe.fileHandleForReading.readabilityHandler = nil
            }
            if let stdOutPipe = aTask.standardOutput as? Pipe {
                stdOutPipe.fileHandleForReading.readabilityHandler = nil
            }
        })
        return self
    }

    func run() -> Self {
        process.launchPath = executable

        if let args = args {
            process.arguments = args
        }

        var environment = ProcessInfo.processInfo.environment
        if let env = env {
            for (val, key) in env {
                environment[key] = val
            }
        }

        environment["NSUnbufferedIO"] = "YES"
        process.environment = environment

        if !process.isRunning && FileManager.default.isExecutableFile(atPath: executable){
            process.launch()
        }

        return self
    }

    internal var cancellationHandler: CancellationHandler?

    func cancelled(handler: @escaping CancellationHandler) -> Self {
        cancellationHandler = handler
        return self
    }

    func cancel() {
        if process.isRunning {
            if let handler = cancellationHandler {
                handler()
            }
            process.terminate()
        }
    }
}

class InteractiveTask: Task, InteractableTaskable {

    private var inHandler:((String) -> (String)?)?

    func isInteractive(string: String) -> Bool {
        return expectedPrompts.filter({
            val in
            return string.lowercased().hasSuffix(val.lowercased())
        }).count > 0
    }

    func stdin(message: @escaping (String) -> (String)?) -> Self {
        inHandler = message
        return self
    }

    func stdout(message: @escaping (String) -> (Void)) -> Self {
        let standardOutPipe = Pipe()
        standardOutPipe.fileHandleForReading.readabilityHandler = ({ [weak self]
            fh in
            guard let _self = self else {
                return
            }
            let data = fh.availableData
            guard let decoded = String(data: data, encoding: String.Encoding.utf8) else {
                return
            }

            if _self.isInteractive(string: decoded) {
                guard let inputHandler = _self.inHandler else {
                    return
                }
                guard let results = inputHandler(decoded) else {
                    return
                }
                if (results.isEmpty && _self.process.isRunning){
                    guard let data = results.data(using: String.Encoding.utf8) else {
                        return
                    }
                    guard let stdInputPipe = _self.process.standardInput as? Pipe else {
                        return
                    }

                    stdInputPipe.fileHandleForWriting.write(data)
                }
            } else {
                message(decoded)
            }
        })
        self.process.standardOutput = standardOutPipe
        return self
    }
}
