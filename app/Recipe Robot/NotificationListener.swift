//
//  Notifications.swift
//  Recipe Robot
//
//  Created by Eldon on 10/24/15.
//  Copyright © 2015 Linde Group. All rights reserved.
//

import Cocoa


enum NoteType: Int {
    case Error, Reminders, Warnings, Recipes, Icons

    static func fromName(name: String) -> NoteType? {
        for t in self.cases {
            if t.name == name {
                return t
            }
        }
        return nil
    }

    var name: String {
        switch self {
        case Error: return "com.elliotjordan.recipe-robot.dnc.error"
        case Reminders: return "com.elliotjordan.recipe-robot.dnc.reminders"
        case Warnings: return "com.elliotjordan.recipe-robot.dnc.warnings"
        case Recipes: return "com.elliotjordan.recipe-robot.dnc.recipes"
        case Icons: return "com.elliotjordan.recipe-robot.dnc.icons"
        }
    }

    static var cases: [NoteType]{
        var all = [NoteType]()

        var idx = 0
        while let noteType = NoteType(rawValue: idx){
            all.append(noteType)
            idx++
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
            center.addObserver(self, selector: "noticed:",
                name: n.name,
                object: nil)
        }
    }

    init(noteTypes: [NoteType]) {
        super.init()
        for n in noteTypes {
            center.addObserver(self, selector: "noticed:",
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
