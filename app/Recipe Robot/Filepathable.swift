//
//  Filepathable.swift
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

protocol Filepathable {
    var path: String { get }
    var isFile: Bool { get }
    var isDirectory: Bool { get }
    var isExecutable: Bool { get }
}

protocol FilepathValidator: Filepathable {
    func markAsValidDirectory() -> Bool
    func markAsValidFile() -> Bool
    func markAsValidExecutable() -> Bool

}

extension Filepathable {
    var isFile: Bool {
        return FileManager.default.fileExists(atPath: self.path)
    }

    var isDirectory: Bool {
        var isDir: ObjCBool = false
        let fileExists = FileManager.default.fileExists(atPath:self.path, isDirectory:&isDir)
        return fileExists && isDir.boolValue
    }

    var isExecutable: Bool {
        return FileManager.default.isExecutableFile(atPath:self.path)
    }
}

extension String: Filepathable {
    var path: String { return self }
}

extension NSTextField: FilepathValidator {
    var path: String { return self.stringValue }

    private func valid(_ valid: Bool) -> Bool {
        textColor = valid ? NSColor.black : NSColor.red

        guard let cell = cell as? NSTextFieldCell else { return valid }
        guard let string = cell.placeholderAttributedString?.string ?? cell.placeholderString else { return valid }

        var attrs: [NSAttributedString.Key: Any]?
        let placeholderStringLength = cell.placeholderAttributedString?.string.count ?? 0
        if placeholderStringLength > 0
        {
            attrs = cell.placeholderAttributedString!.attributes(at: 0, effectiveRange: nil)
        } else if cell.attributedStringValue.string.count > 0 {
            attrs = cell.attributedStringValue.attributes(at: 0, effectiveRange: nil)
        }

        attrs?[NSAttributedString.Key.foregroundColor] = valid ? NSColor.lightGray : NSColor.red
        cell.placeholderAttributedString = NSAttributedString(string: string, attributes: attrs)
        placeholderAttributedString = cell.placeholderAttributedString
        
        return valid
    }

    func markAsValidDirectory() -> Bool {
        return valid(path.isDirectory)
    }

    func markAsValidFile() -> Bool {
        return valid(path.isFile)
    }

    func markAsValidExecutable() -> Bool {
        return valid(path.isExecutable)
    }
}
