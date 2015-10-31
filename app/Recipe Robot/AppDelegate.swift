//
//  AppDelegate.swift
//  Recipe Robot
//
//  Created by Elliot Jordan on 7/19/15.
//  Copyright (c) 2015 Elliot Jordan. All rights reserved.
//

import Cocoa

@NSApplicationMain
class AppDelegate: NSObject, NSApplicationDelegate {

    func applicationDidFinishLaunching(aNotification: NSNotification) {
        // Insert code here to initialize your application
    }

    func applicationWillTerminate(aNotification: NSNotification) {
        // Insert code here to tear down your application
    }

    func applicationShouldTerminateAfterLastWindowClosed(sender: NSApplication) -> Bool {
        return true
    }

    @IBAction func openHelpURL(sender: AnyObject) {
        let urlString = NSURL(string: "https://github.com/homebysix/recipe-robot/blob/master/README.md")
        NSWorkspace.sharedWorkspace().openURL(urlString!)
    }
}
