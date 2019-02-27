//
//  FeedMeDropImageView.swift
//
//  Recipe Robot
//  Copyright 2015-2019 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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

// MARK: -- Dragging  --
class FeedMeDropImageView: NSImageView {

    override func performDragOperation(_ sender: NSDraggingInfo) -> Bool {
        guard let controller = sender.draggingDestinationWindow?.contentViewController as? FeedMeViewController else {
            print ("failed coercing contentViewController to FeedMeViewController")
            return true
        }
        guard let files = sender.draggingPasteboard.propertyList(forType: NSPasteboard.PasteboardType(rawValue: "NSFilenamesPboardType")) as? NSArray else {
            print ("failed coercing NSFilenamesPboardType to NSArray")
            return true
        }
        guard let file = files.firstObject as? String else {
            print ("failed coercing files.firstObject to String")
            return true
        }

        controller.task.appOrRecipe = file
        controller.performSegue(withIdentifier:"FeedMeSegue", sender: self)

        return true
    }

    override func prepareForDragOperation(_ sender: NSDraggingInfo) -> Bool {
        return true
    }

    override func concludeDragOperation(_ sender: NSDraggingInfo?) {
        // All done.
    }

    override func draggingEntered(_ sender: NSDraggingInfo) -> NSDragOperation  {
        return NSDragOperation.copy
    }

    override func draggingExited(_ sender: NSDraggingInfo?) {
    }
}

//// MARK: -- Pasting  --
//extension FeedMeDropImageView {
//    @IBAction func paste(sender: AnyObject){
//        let pasteboard = NSPasteboard.generalPasteboard()
//        let classes = [NSURL.classForCoder()]
//        let options = [String: AnyObject]()
//        if pasteboard.canReadObjectForClasses(classes, options: options){
//            let objs = pasteboard.readObjectsForClasses(classes, options: options)
//            Swift.print(objs)
//            Swift.print(sender)
//        }
//    }
//}
