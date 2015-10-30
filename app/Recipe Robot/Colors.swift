//
//  Colors.swift
//  Recipe Robot
//
//  Created by Eldon on 10/11/15.
//  Copyright (c) 2015 Eldon Ahrold. All rights reserved.
//

import Cocoa

enum Color: Int {
    case Blue, LtBlue, Grey, Green, Red, Yellow, Cream, White

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
        case White: return NSColor.whiteColor()
        }
    }

    // CoreGraphics Representation
    var cg: CGColor {
        return self.ns.CGColor
    }

}
