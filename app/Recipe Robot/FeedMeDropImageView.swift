//
//  FeedMeDropImageView.swift
//  Recipe Robot
//
//  Created by Eldon on 10/27/15.
//  Copyright (c) 2015 Eldon Ahrold. All rights reserved.
//

import Cocoa

// MARK: -- Dragging  --
class FeedMeDropImageView: NSImageView {

    override func performDragOperation(sender: NSDraggingInfo) -> Bool {
        if let controller = sender.draggingDestinationWindow()!.contentViewController as? FeedMeViewController,
            files = sender.draggingPasteboard().propertyListForType(NSFilenamesPboardType) as? NSArray,
            file = files.firstObject as? String {

                controller.task = RecipeRobotTask()
                controller.task.appOrRecipe = file
                controller.performSegueWithIdentifier("FeedMeSegue", sender: self)
        }
        return true
    }

    override func prepareForDragOperation(sender: NSDraggingInfo) -> Bool {
        return true
    }

    override func concludeDragOperation(sender: NSDraggingInfo?) {
        // All done.
    }

    override func draggingEntered(sender: NSDraggingInfo) -> NSDragOperation  {
        return NSDragOperation.Copy
    }

    override func draggingExited(sender: NSDraggingInfo?) {
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

