//
//  TextStorageExtensions.swift
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

extension NSTextStorage {
    func appendString(string: String, color: NSColor){

        var attrs = [String: AnyObject]()
        let idx = self.string.characters.count
        if idx > 0 {
            attrs.update(self.attributesAtIndex(idx - 1, effectiveRange: nil))
        }

        attrs[NSForegroundColorAttributeName] = color

        let attrString = NSAttributedString(string: string, attributes: attrs)
        self.appendAttributedString(attrString)
    }
}