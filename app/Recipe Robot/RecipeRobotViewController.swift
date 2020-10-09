//
//  ViewController.swift
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
import AudioToolbox
import Quartz

//let sound = NSSound(named: "Glass")
var sound: NSSound?

// MARK: Base view Controller for Main Storyboard.
class RecipeRobotViewController: NSViewController {

    deinit {
        print("dealloc \(self.className)")
    }

    var task: RecipeRobotTask = RecipeRobotTask()

    override func viewDidLoad() {
        super.viewDidLoad()
    }

    override func awakeFromNib() {
        super.awakeFromNib()
        self.view.wantsLayer = true
    }

    override var representedObject: Any? {
        didSet {
        // Update the view, if already loaded.
        }
    }

    override func prepare(for segue: NSStoryboardSegue, sender: Any?) {
        if let source = segue.sourceController as? RecipeRobotViewController,
            let dest = segue.destinationController as? RecipeRobotViewController {
                // Here we pass off the task object during the seague transition.
                // So in the future make sure to call super.prepareForSegue() on any
                // additional viewControllers.

                if let dest = dest as? ProcessingViewController {
                    dest.task = source.task
                    dest.processRecipes()
                } else if let dest = dest as? FeedMeViewController {
                    dest.task = RecipeRobotTask()
                }
        }
    }
}

// MARK: - Feed Me View Controller
class FeedMeViewController: RecipeRobotViewController {

    @IBOutlet var ignoreButton: NSButton!
    @IBOutlet var urlTextField: NSTextField!

    var eventMonitor: Any?

    deinit {
        if let eventMonitor = eventMonitor {
            NSEvent.removeMonitor(eventMonitor)
        }
    }

    override func awakeFromNib() {
        super.awakeFromNib()
    }

    override func viewDidLoad() {
        ignoreButton.target = self
        ignoreButton.action = #selector(FeedMeViewController.changeIgnoreState(sender:))

        eventMonitor = NSEvent.addLocalMonitorForEvents(matching: NSEvent.EventTypeMask.flagsChanged) { [weak self](event) -> NSEvent? in
            if let _self = self {
                if _self.ignoreButton.state == NSControl.StateValue.on {
                    _self.ignoreButton.isHidden = false
                } else {
                    _self.ignoreButton.isHidden = (event.modifierFlags.rawValue & NSEvent.ModifierFlags.option.rawValue) == 0
                }
            }
            return event
            }
        super.viewDidLoad()
    }

    override func viewDidAppear() {
        super.viewDidAppear()
        if !Defaults.sharedInstance.initialized {
            self.presentAsSheet(MainStoryboard().preferenceViewController)
            Defaults.sharedInstance.initialized = true
        }
        self.task = RecipeRobotTask()
    }

    @IBAction func changeIgnoreState(sender: NSButton?) {
        if sender === ignoreButton {
            task.ignoreExisting = (sender?.state == NSControl.StateValue.on)
        }
    }

    @IBAction func processRecipe(sender: NSButton?) {
        if urlTextField.stringValue.isEmpty {
            return
        }

        guard let url = NSURL(string: urlTextField.stringValue) else {
            return
        }
        print("Received input: \(url.absoluteString!)")
        task.appOrRecipe = url.absoluteString!
        performSegue(withIdentifier: NSStoryboardSegue.Identifier("FeedMeSegue"), sender: self)
    }
}

// MARK: - Preference View Controller
class PreferenceViewController: RecipeRobotViewController {

    // MARK: IBOutlets
    @IBOutlet var tableView: NSTableView!
    @IBOutlet var scrollView: NSScrollView!

    @IBOutlet var dsFolderPathButton: NSButton!
    @IBOutlet weak var dsLabel: NSTextField!
    @IBOutlet weak var dsTextField: NSTextField!

    @IBOutlet var recipeFolderPathButton: NSButton!

    @IBOutlet weak var recipeLocation: NSTextField!

    @IBOutlet weak var jssCheckBox: NSButton!

    private var enabledRecipeTypes = Defaults.sharedInstance.recipeTypes ?? Set<String>()

    // MARK: Overrides
    override func viewDidLoad() {
        super.viewDidLoad()
        self.tableView.backgroundColor = NSColor.clear
        self.scrollView.backgroundColor = NSColor.clear
        self.scrollView.focusRingType = NSFocusRingType.none

        self.recipeFolderPathButton.action = #selector(PreferenceViewController.chooseFilePath(sender:))
        self.recipeFolderPathButton.target = self
        self.dsFolderPathButton.action = #selector(PreferenceViewController.chooseFilePath(sender:))
        self.dsFolderPathButton.target = self

        let jssHidden = !enabledRecipeTypes.contains(RecipeType.JSS.value)
        jssCheckBox.isHidden = jssHidden

        let dsHidden = !enabledRecipeTypes.contains(RecipeType.DS.value)
        dsLabel.isHidden = dsHidden
        dsTextField.isHidden = dsHidden
        dsFolderPathButton.isHidden = dsHidden

        if let dsPath = Defaults.sharedInstance.dsPackagePath {
            dsTextField.stringValue = dsPath
        }

        _ = dsTextField.stringChanged {
            chainable in
            if let chainableTextField = chainable as? NSTextField {
                if chainableTextField.markAsValidDirectory() {
                    Defaults.sharedInstance.dsPackagePath = chainableTextField.path
                }
            }
        }

        if let recipePath = Defaults.sharedInstance.recipeCreateLocation {
            recipeLocation.stringValue = recipePath
        }

        _ = recipeLocation.stringChanged {
            chainable in
            if let chainableTextField = chainable as? NSTextField {
                if chainableTextField.markAsValidDirectory() {
                    Defaults.sharedInstance.recipeCreateLocation = chainableTextField.path
                }
            }
        }
    }

    override func viewWillDisappear() {
        super.viewWillDisappear()
        Defaults.sharedInstance.recipeTypes = self.enabledRecipeTypes
    }

    @IBAction func close(sender: AnyObject) {
        if enabledRecipeTypes.contains(RecipeType.DS.value) &&
            !dsTextField.markAsValidDirectory() {
                // pass
        } else {
            self.dismiss(sender)
            self.view.window?.close()
        }
    }
}

extension PreferenceViewController {
    @IBAction func chooseFilePath(sender: NSButton) {
        let d = Defaults.sharedInstance
        var directoryURL = NSHomeDirectory()
        if sender === recipeFolderPathButton {
            if let p = d.recipeCreateLocation {
                directoryURL = p
            }
        } else if sender === dsFolderPathButton {
            if let p = d.dsPackagePath {
                directoryURL = p
            }
        }

        let panel = NSOpenPanel()

        let dir = (directoryURL as NSString).expandingTildeInPath
        var isDir: ObjCBool = ObjCBool(false)
        if FileManager.default.fileExists(atPath: dir, isDirectory: &isDir) && isDir.boolValue {
            panel.directoryURL = URL(fileURLWithPath: dir)
        }

        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.canCreateDirectories = true
        panel.allowsMultipleSelection = false
        panel.prompt = "Choose"

        panel.beginSheetModal(for: self.view.window!) {
            [weak self] result in
            if result.rawValue == NSApplication.ModalResponse.OK.rawValue {

                guard let strongSelf = self else {
                    return
                }
                guard let path = panel.url?.path else {
                    return
                }
                if sender === self!.recipeFolderPathButton {
                    d.recipeCreateLocation = path
                    strongSelf.recipeLocation.stringValue = path
                    _ = strongSelf.recipeLocation.markAsValidDirectory()
                } else if sender === self!.dsFolderPathButton {
                    d.dsPackagePath = path
                    strongSelf.dsTextField.stringValue = path
                    _ = strongSelf.dsTextField.markAsValidDirectory()
                }
            }
        }
    }
}

// MARK: Preference View Controller: Table View
extension PreferenceViewController: NSTableViewDataSource, NSTableViewDelegate {

    func numberOfRows(in tableView: NSTableView) -> Int {
        return RecipeType.values.count
    }

    func tableView(_ tableView: NSTableView, objectValueFor tableColumn: NSTableColumn?, row: Int) -> Any? {
        return (enabledRecipeTypes.contains(RecipeType.values[row])) ? NSControl.StateValue.on : NSControl.StateValue.off
    }

    func tableView(_ tableView: NSTableView, willDisplayCell cell: Any, for tableColumn: NSTableColumn?, row: Int) {
        if let cell = cell as? NSButtonCell {
            cell.title = RecipeType.values[row]
        }
    }

    func tableView(_ tableView: NSTableView, setObjectValue object: Any?, for tableColumn: NSTableColumn?, row: Int) {

        guard let value = object as? Int else {
            return
        }
        let enabled = (value == NSControl.StateValue.on.rawValue)

        let type = RecipeType.cases[row]
        switch type {
        case .JSS:
            jssCheckBox.isHidden = !enabled
        case .DS:
            dsLabel.isHidden = !enabled
            dsTextField.isHidden = !enabled
            dsFolderPathButton.isHidden = !enabled
        default:
            break
        }

        if value == NSControl.StateValue.on.rawValue {
            enabledRecipeTypes = enabledRecipeTypes.union(type.requiredTypeValues)
        } else if value == NSControl.StateValue.off.rawValue {
            if enabledRecipeTypes.count > 0 {
                guard  enabledRecipeTypes.contains(type.value) else {
                    return
                }
                enabledRecipeTypes.remove(type.value)
            }
        }
        tableView.reloadData()
    }
}

// MARK: - Processing
class ProcessingViewController: RecipeRobotViewController {

    @IBOutlet private var progressView: NSTextView?
    @IBOutlet private var cancelButton: NSButton!
    @IBOutlet private var showInFinderButton: NSButton!

    @IBOutlet weak var titleLabel: NSTextField!
    @IBOutlet weak var infoLabel: NSTextField?

    @IBOutlet weak var appIcon: NSButton?

    // MARK: Indicators
    @IBOutlet weak var recipeIndicator: NSButton?
    @IBOutlet weak var reminderIndicator: NSButton?
    @IBOutlet weak var iconIndicator: NSButton?
    @IBOutlet weak var warningIndicator: NSButton?
    @IBOutlet weak var errorIndicator: NSButton?

    private let listener = NotificationListener()
    private var completionInfo: [String: AnyObject]?

    override func viewDidLoad() {
        super.viewDidLoad()

        infoLabel?.textColor = Color.White.ns
        infoLabel?.stringValue = "Prepping..."

        listener.notificationHandler = {
            [weak self] noteType, info in

            switch noteType {
            case .Info:
                break
            case .Recipes:
                break
            case .Reminders:
                break
            case .Icons:
                break
            case .Warnings:
                break
            case .Error:
                break
            case .Complete:
                self!.completionInfo = info
            }
        }
    }

    override func viewWillAppear() {
        let buttons = [recipeIndicator,
                       reminderIndicator,
                       iconIndicator,
                       warningIndicator,
                       errorIndicator]

        for b in buttons {
            b?.target = self
            b?.image = StatusImage.PartiallyAvailable.image
        }

        print("Executable path: \(task.executable)")
        print("Command arguments: \(task.args ?? [""])")
        if let icon = task.appIcon {
            appIcon?.image = icon
        }
        if let name = task.appOrRecipeName {
            titleLabel.stringValue = "Making \(name) recipes..."
        } else {
            titleLabel.stringValue = "Making recipes..."
        }

        showInFinderButton.isEnabled = false
        showInFinderButton.target = self
        showInFinderButton.action = #selector(ProcessingViewController.openFolder(sender:))
    }

    func processRecipes() {
        // Do view setup here.
        NSApplication.shared.activate(ignoringOtherApps: true)

        func showProgress(progress: String) {
            guard let progressView = progressView else {
                return
            }
            progressView.textStorage?.appendString(string: progress, color: progress.color)
            progressView.scrollToEndOfDocument(self)
        }

        func completed(error: Error?) {
            let success = (error == nil)
            self.showInFinderButton.isEnabled = success

            if success {
                self.titleLabel.stringValue = "Ding! All done."
                self.appIcon?.image = NSImage(named: "NSFolder")

                self.appIcon?.action = #selector(ProcessingViewController.openFolder(sender:))
                self.appIcon?.target = self
            } else {
                self.appIcon?.image = NSImage(named: "NSCaution")
                self.titleLabel.stringValue = "Oops, I couldn't make recipes for this app."
            }

            if let sound = sound {
                sound.play()
            }

            if let cancelButton = self.cancelButton {
                cancelButton.title = "Let's Do Another!"
                cancelButton.identifier = NSUserInterfaceItemIdentifier(rawValue: "Alldone")
            }
        }

        _ = task.stdout {
            message in
                showProgress(progress: message)
        }.stderr {
            message in
                showProgress(progress: message)
        }.completed {
            error in
                completed(error: error)
        }.cancelled {
            print("Task cancelled")
        }.run()
    }

    // MARK: IBActions
    @IBAction private func openFolder(sender: AnyObject?) {
        if let loc = Defaults.sharedInstance.recipeCreateLocation {
            let url = URL(fileURLWithPath: loc, isDirectory: true)
            NSWorkspace.shared.open(url)
        }
    }

    @IBAction private func cancelTask(sender: NSButton) {
        if cancelButton.identifier?.rawValue != "Alldone" {
            self.task.cancel()
        }
        self.performSegue(withIdentifier: "ProcessingSegue", sender: self)
    }
}
