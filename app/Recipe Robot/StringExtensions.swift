//
//  StringExtensions.swift
//  Recipe Robot
//
//  Created by Eldon on 10/11/15.
//  Copyright (c) 2015 Eldon Ahrold. All rights reserved.
//

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