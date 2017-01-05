//
//  Colors.swift
//
//  Recipe Robot
//  Copyright 2015-2017 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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

enum Color: Int {
    case Blue, LtBlue, Grey, Green, Red, Yellow, Cream, Black, White

    // NSColor Representation
    var ns: NSColor {
        switch self {
        case Blue: return NSColor(SRGBRed: 88/255, green: 146/255, blue: 178/255, alpha: 1)
        case LtBlue: return NSColor(SRGBRed: 152/255, green: 185/255, blue: 204/255, alpha: 1)
        case Grey: return NSColor(SRGBRed: 192/255, green: 201/255, blue: 201/255, alpha: 1)
        case Green: return NSColor(SRGBRed: 135/255, green: 168/255, blue: 135/255, alpha: 1)
        case Red: return NSColor(SRGBRed: 181/255, green: 33/255, blue: 38/255, alpha: 1)
        case Yellow: return NSColor(SRGBRed: 221/255, green: 182/255, blue: 81/255, alpha: 1)
        case Cream: return NSColor(SRGBRed: 248/255, green: 235/255, blue: 189/255, alpha: 1)
        case Black: return NSColor.blackColor()
        case White: return NSColor.whiteColor()
        }
    }

    // CoreGraphics Representation
    var cg: CGColor {
        return self.ns.CGColor
    }

}
