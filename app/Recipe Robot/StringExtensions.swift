//
//  StringExtensions.swift
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

import Cocoa

// MARK: Space
extension String {
    public func splitByLine() -> [String] {
        return self.components(separatedBy: CharacterSet.newlines)
    }

    public func splitBySpace() -> [String] {
        return self.components(separatedBy: CharacterSet.whitespaces)
    }
}

// MARK: Trimmed
extension String {

    /// Trimmed whitespace and new line
    public var trimmedFull: String {
        return self.trimmingCharacters(in: CharacterSet.whitespacesAndNewlines)
    }

    /// Timmed whitespace
    public var trimmed: String {
        return self.trimmingCharacters(in: CharacterSet.whitespaces)
    }
}

// MARK: Brackets
private let BracketedColorDict = [
    "[ERROR]": Color.Red.ns,
    "[WARNING]": Color.Yellow.ns,
    "[REMINDER]": Color.Green.ns
]

extension String {
    var color: NSColor {
        for (k, v) in BracketedColorDict {
            if self.contains(k){
                return v
            }
        }
        return Color.Black.ns
    }

    var bracketedColor: NSAttributedString {
        return NSAttributedString(string: self,
                                  attributes: [NSAttributedString.Key.foregroundColor: color])
    }
}
