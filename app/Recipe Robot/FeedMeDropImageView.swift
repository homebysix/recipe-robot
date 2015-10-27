//
//  FeedMeDropImageView.swift
//  Recipe Robot
//
//  Created by Eldon on 10/27/15.
//  Copyright © 2015 Linde Group. All rights reserved.
//

import Cocoa

// MARK: -- Views --
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