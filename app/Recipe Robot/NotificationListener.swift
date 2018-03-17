//
//  Notifications.swift
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


enum NoteType: Int {
    case Info, Error, Reminders, Warnings, Recipes, Icons, Complete

    static func fromName(name: String) -> NoteType? {
        for t in self.cases {
            if t.name == name {
                return t
            }
        }
        return nil
    }

    var key: String {
        switch self {
        case Info: return "information"
        case Error: return "errors"
        case Reminders: return "reminders"
        case Warnings: return "warnings"
        case Recipes: return "recipes"
        case Icons: return "icons"
        case Complete: return "complete"
        }
    }

    var name: String {
        return "com.elliotjordan.recipe-robot.dnc." + self.key
    }

    var prefix: String {
        switch self {
        case .Error, .Warnings, .Reminders:
            return "[\(self.key.uppercaseString)]"
        default:
            return ""
        }
    }
    
    var color: Color {
        switch self {
        case Error: return Color.Red
        case Reminders: return Color.Green
        case Warnings: return Color.Yellow
        default: return Color.Black
        }
    }

    static var cases: [NoteType]{
        var all = [NoteType]()
        var idx = 0
        while let noteType = NoteType(rawValue: idx){
            all.append(noteType)
            idx += 1
        }
        return all
    }
}

class NotificationListener: NSObject {
    var notificationHandler: ((name: NoteType, info: [String:AnyObject]) -> (Void))?
    private let center = NSDistributedNotificationCenter.defaultCenter()

    override init(){
        super.init()

        for n in NoteType.cases {
            center.addObserver(self, selector: #selector(NotificationListener.noticed(_:)),
                name: n.name,
                object: nil)
        }
    }

    init(noteTypes: [NoteType]) {
        super.init()
        for n in noteTypes {
            center.addObserver(self, selector: #selector(NotificationListener.noticed(_:)),
                name: n.name,
                object: nil)
        }
    }

    deinit {
        NSDistributedNotificationCenter.defaultCenter().removeObserver(self)
    }

    func noticed(note: NSNotification){
        if notificationHandler != nil{
            if let noteType = NoteType.fromName(note.name), dict = note.userInfo as? [String: AnyObject] {
                notificationHandler!(name: noteType, info: dict)
            }
        }
    }
}
