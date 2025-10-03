//
//  AppDelegate.swift
//
//  Recipe Robot
//  Copyright 2015-2025 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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

// import AppMover

@NSApplicationMain
class AppDelegate: NSObject, NSApplicationDelegate {

    // Outlet for "Check for Updates" menu item
    @IBOutlet var checkForUpdatesMenuItem: NSMenuItem!

    let updaterController: SPUStandardUpdaterController

    override init() {
        // Check for updates using Sparkle
        updaterController = SPUStandardUpdaterController(
            startingUpdater: true, updaterDelegate: nil, userDriverDelegate: nil)
    }

    func applicationDidFinishLaunching(_ aNotification: Notification) {
        // Disabled until AppMover is implemented
        // AppMover.moveIfNecessary()

        // Check for AutoPkg before proceeding
        if !checkAutoPkgInstallation() {
            showAutoPkgRequiredAlert()
            return
        }

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

    // MARK: - AutoPkg Dependency Checking

    private func checkAutoPkgInstallation() -> Bool {
        // First check if the autopkg executable exists
        let autopkgPath = "/usr/local/bin/autopkg"
        guard FileManager.default.fileExists(atPath: autopkgPath) else {
            return false
        }

        // Try to run autopkg version to verify it works
        let process = Process()
        process.launchPath = autopkgPath
        process.arguments = ["version"]

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        process.launch()
        process.waitUntilExit()

        // Check if autopkg ran successfully and produced output
        if process.terminationStatus == 0 {
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            let output = String(data: data, encoding: .utf8) ?? ""
            return !output.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        }

        return false
    }

    private func showAutoPkgRequiredAlert() {
        let alert = NSAlert()
        alert.messageText = "AutoPkg Required"
        alert.informativeText =
            "Recipe Robot requires AutoPkg to function. "
            + "Please install AutoPkg and then run Recipe Robot again."
        alert.alertStyle = .critical
        alert.addButton(withTitle: "Quit")
        alert.addButton(withTitle: "Get AutoPkg")

        let response = alert.runModal()
        if response == .alertSecondButtonReturn {
            if let url = URL(string: "https://github.com/autopkg/autopkg/releases/latest") {
                NSWorkspace.shared.open(url)
            }
        }

        NSApplication.shared.terminate(nil)
    }
}
