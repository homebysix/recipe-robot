//
//  StringExtensions.swift
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

// MARK: Space
extension String {
    public func splitByLine() -> [String] {
        return self.componentsSeparatedByCharactersInSet(NSCharacterSet.newlineCharacterSet())
    }

    public func splitBySpace() -> [String] {
        return self.componentsSeparatedByCharactersInSet(NSCharacterSet.whitespaceCharacterSet())
    }
}

// MARK: Trimmed
extension String {

    // Trimmed whitespace and new line
    public var trimmedFull: String {
        return self.stringByTrimmingCharactersInSet(NSCharacterSet.whitespaceAndNewlineCharacterSet())
    }

    // Timmed whitespace
    public var trimmed: String {
        return self.stringByTrimmingCharactersInSet(NSCharacterSet.whitespaceCharacterSet())
    }
}

// MARK: ANSI
extension String {
    public func parseANSI() -> NSAttributedString {
        var matchFound = false
        var color = NSColor.whiteColor()

        let string = NSMutableString(string: self)
        string.replaceCharactersInRange(NSMakeRange(0, 1), withString: "")

        let colorDict = ANSIColors()
        for (k, v) in colorDict {
            if string.hasPrefix(k){
                matchFound = true
                color = v
                string.replaceOccurrencesOfString(k,
                    withString: "",
                    options: NSStringCompareOptions.LiteralSearch,
                    range: NSMakeRange(0, string.length))
                break
            }
        }

        // Also replace the reset text
        string.replaceOccurrencesOfString("[0m", withString: "",
            options: NSStringCompareOptions.LiteralSearch,
            range: NSMakeRange(0, string.length)
        )

        let str = matchFound ? string as AnyObject as! String : self

        let attrString = NSAttributedString(string: str, attributes: [NSForegroundColorAttributeName: color])
        return attrString
    }

    public func ANSIColors() -> Dictionary<String, NSColor> {
        let val = [
            "[0m" : NSColor.whiteColor(),
            "[91m" : Color.Red.ns,
            "[93m" : Color.Yellow.ns,
            "[94m" : Color.Green.ns,
        ]
        return val
    }
}
