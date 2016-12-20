//
//  Images.swift
//
//  Recipe Robot
//  Copyright 2015-2016 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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
