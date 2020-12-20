//
//  NotificationListener.swift
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

import Cocoa

enum NoteType: Int {
    case Info, Error, Reminders, Warnings, Recipes, Icons, Complete

    static func fromName(name: NSNotification.Name) -> NoteType? {
        for t in self.cases {
            if t.name == name {
                return t
            }
        }
        return nil
    }

    var key: String {
        switch self {
        case .Complete: return "complete"
        case .Error: return "errors"
        case .Icons: return "icons"
        case .Info: return "information"
        case .Recipes: return "recipes"
        case .Reminders: return "reminders"
        case .Warnings: return "warnings"
        }
    }

    var name: NSNotification.Name {
        return NSNotification.Name("com.elliotjordan.recipe-robot.dnc." + self.key)
    }

    var prefix: String {
        switch self {
        case .Error, .Warnings, .Reminders:
            return "[\(String(describing: self.key.uppercased))]"
        default:
            return ""
        }
    }

    var color: Color {
        switch self {
        case .Error: return Color.Red
        case .Reminders: return Color.Green
        case .Warnings: return Color.Yellow
        default: return Color.Black
        }
    }

    static var cases: [NoteType] {
        var all = [NoteType]()
        var idx = 0
        while let noteType = NoteType(rawValue: idx) {
            all.append(noteType)
            idx += 1
        }
        return all
    }
}

class NotificationListener: NSObject {
    var notificationHandler: ((_ name: NoteType, _ info: [String: AnyObject]) -> Void)?
    private let center = DistributedNotificationCenter.default()

    override init() {
        super.init()

        for n in NoteType.cases {
            center.addObserver(
                self, selector: #selector(NotificationListener.noticed(_:)),
                name: n.name,
                object: nil)
        }
    }

    init(noteTypes: [NoteType]) {
        super.init()
        for n in noteTypes {
            center.addObserver(
                self, selector: #selector(NotificationListener.noticed(_:)),
                name: n.name,
                object: nil)
        }
    }

    deinit {
        DistributedNotificationCenter.default().removeObserver(self)
    }

    @objc func noticed(_ note: NSNotification) {
        if let handler = notificationHandler {
            if let noteType = NoteType.fromName(name: note.name),
                let dict = note.userInfo as? [String: AnyObject]
            {
                handler(noteType, dict)
            }
        }
    }
}
