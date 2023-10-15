//
//  AppDelegate.swift
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

import AppKit
import Cocoa
import Sparkle

//import AppMover

@NSApplicationMain
class AppDelegate: NSObject, NSApplicationDelegate {

    // Outlet for "Check for Updates" menu item
    @IBOutlet var checkForUpdatesMenuItem: NSMenuItem!

    let updaterController: SPUStandardUpdaterController

    override init() {
        // Check for updates using Sparkle
        updaterController = SPUStandardUpdaterController(startingUpdater: true, updaterDelegate: nil, userDriverDelegate: nil)
    }

    func applicationDidFinishLaunching(_ aNotification: Notification) {
        // Disabled until AppMover is implemented
        // AppMover.moveIfNecessary()

        // Check for updates using Sparkle
        checkForUpdatesMenuItem.target = updaterController
        checkForUpdatesMenuItem.action = #selector(SPUStandardUpdaterController.checkForUpdates(_:))
    }

    func applicationWillTerminate(aNotification: NSNotification) {
        // Insert code here to tear down your application
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }

    @IBAction func openHelpURL(sender: AnyObject) {
        guard
            let url = URL(string: "https://github.com/homebysix/recipe-robot/blob/master/README.md")
        else {
            print("Failed to convert Help URL.")
            return
        }

        NSWorkspace.shared.open(url)
    }
}
