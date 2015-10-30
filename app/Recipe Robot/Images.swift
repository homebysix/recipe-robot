//
//  Images.swift
//  Recipe Robot
//
//  Created by Eldon on 10/27/15.
//  Copyright (c) 2015 Eldon Ahrold. All rights reserved.
//

import Cocoa

enum StatusImage: Int {
    case None, Available, PartiallyAvailable, Unavailable

    var image: NSImage {
        switch self{
        case .None:
            return NSImage(named: "NSStatusNone")!
        case .Available:
            return NSImage(named: "NSStatusAvailable")!
        case .PartiallyAvailable:
            return NSImage(named: "NSStatusPartiallyAvailable")!
        case .Unavailable:
            return NSImage(named: "NSStatusUnavailable")!
        }
    }
}