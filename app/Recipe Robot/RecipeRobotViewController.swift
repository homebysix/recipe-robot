//
//  ViewController.swift
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
import AudioToolbox
import Quartz

//let sound = NSSound(named: "Glass")
var sound: NSSound? = nil


// MARK: Base view Controller for Main Storyboard.
class RecipeRobotViewController: NSViewController {

    deinit {
        print("dealoc \(self.className)")
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

    var eventMonitor: AnyObject?

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
        ignoreButton.action = #selector(FeedMeViewController.changeIgnoreState(_:))

        eventMonitor = NSEvent.addLocalMonitorForEventsMatchingMask(NSEventMask.FlagsChanged) { [weak self](event) -> NSEvent? in
            if let _self = self {
                if (_self.ignoreButton.state == NSOnState){
                    _self.ignoreButton.hidden = false
                } else {
                    _self.ignoreButton.hidden = (event.modifierFlags.rawValue & NSEventModifierFlags.Option.rawValue) == 0
                }
            }
            return event
        }
        super.viewDidLoad()
    }

    override func viewDidAppear() {
        super.viewDidAppear()
        if !Defaults.sharedInstance.initialized {
            self.presentViewControllerAsSheet(MainStoryboard().preferenceViewController)
            Defaults.sharedInstance.initialized = true
        }
        self.task = RecipeRobotTask()
    }

    @IBAction func changeIgnoreState(sender: NSButton?){
        if sender === ignoreButton {
            task.ignoreExisting = (sender?.state == NSOnState)
        }
    }

    @IBAction func processRecipe(sender: NSButton?){
        if urlTextField.stringValue.isEmpty {
            return
        }
        
        guard let url = NSURL(string: urlTextField.stringValue) else {
            return
        }
        task.appOrRecipe = url.absoluteString!
        performSegueWithIdentifier("FeedMeSegue", sender: self)
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

        self.recipeFolderPathButton.action = #selector(PreferenceViewController.chooseFilePath(_:))
        self.recipeFolderPathButton.target = self
        self.dsFolderPathButton.action = #selector(PreferenceViewController.chooseFilePath(_:))
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

        dsTextField.stringChanged {
            textField in
            if textField.markAsValidDirectory() {
                Defaults.sharedInstance.dsPackagePath = textField.path
            }
        }


        if let recipePath = Defaults.sharedInstance.recipeCreateLocation {
            recipeLocation.stringValue = recipePath
        }

        recipeLocation.stringChanged {
            textField in
            if textField.markAsValidDirectory() {
                Defaults.sharedInstance.recipeCreateLocation = textField.path
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
    @IBAction func chooseFilePath(sender: NSButton){
        let d = Defaults.sharedInstance
        var directoryURL = NSHomeDirectory()
        if sender === recipeFolderPathButton {
            if let p = d.recipeCreateLocation {
                directoryURL = p
            }
        }
        else if sender === dsFolderPathButton {
            if let p = d.dsPackagePath {
                directoryURL = p
            }
        }

        let panel = NSOpenPanel()

        let dir = (directoryURL as NSString).expandingTildeInPath
        var isDir: ObjCBool = ObjCBool(false)
        if FileManager.default.fileExists(atPath:dir, isDirectory: &isDir) && isDir.boolValue {
            panel.directoryURL = URL(fileURLWithPath: dir)
        }

        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.canCreateDirectories = true
        panel.allowsMultipleSelection = false
        panel.prompt = "Choose";

        panel.beginSheetModalForWindow(self.view.window!) {
            [weak self] result in
            if (result == NSFileHandlingPanelOKButton) {
                guard let path = panel.url?.path else {
                    return
                }
                if sender === self!.recipeFolderPathButton {
                    d.recipeCreateLocation = path
                    self!.recipeLocation.stringValue = path
                    self!.recipeLocation.markAsValidDirectory()
                }
                else if sender === self!.dsFolderPathButton {
                    d.dsPackagePath = path
                    self!.dsTextField.stringValue = path
                    self!.dsTextField.markAsValidDirectory()
                }
            }
        }
    }
}

// MARK: Preference View Controller: Table View
extension PreferenceViewController: NSTableViewDataSource, NSTableViewDelegate {


    func numberOfRowsInTableView(tableView: NSTableView) -> Int {
        return RecipeType.values.count
    }

    func tableView(tableView: NSTableView, objectValueForTableColumn tableColumn: NSTableColumn?, row: Int) -> AnyObject? {
        return (enabledRecipeTypes.contains(RecipeType.values[row])) ? NSOnState: NSOffState
    }

    func tableView(tableView: NSTableView, willDisplayCell cell: AnyObject, forTableColumn tableColumn: NSTableColumn?, row: Int) {
        if let cell = cell as? NSButtonCell {
            cell.title = RecipeType.values[row]
        }
    }

    func tableView(tableView: NSTableView, setObjectValue object: AnyObject?, forTableColumn tableColumn: NSTableColumn?, row: Int) {

        guard let value = object as? Int else {
            return
        }
        let enabled = (value == NSControl.StateValue.on.rawValue)

        let type = RecipeType.cases[row]
        switch type {
        case .JSS:
            jssCheckBox.hidden = !enabled
        case .DS:
            dsLabel.hidden = !enabled
            dsTextField.hidden = !enabled
            dsFolderPathButton.hidden = !enabled
        default:
            break
        }

        if (value == NSControl.StateValue.on.rawValue) {
            enabledRecipeTypes = enabledRecipeTypes.union(type.requiredTypeValues)
        } else if (value == NSControl.StateValue.off.rawValue){
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
    private var completionInfo: Dictionary<String,AnyObject>?

    override func viewDidLoad() {
        super.viewDidLoad()

        infoLabel?.textColor = Color.White.ns
        infoLabel?.stringValue = "Preping..."

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
            b?.action = "showCompletionPopover:"
            b?.image = StatusImage.PartiallyAvailable.image
        }

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
        showInFinderButton.action = "openFolder:"
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

                self.appIcon?.action = "openFolder:"
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

        task.stdout {
            message in
                showProgress(message)
        }.stderr {
            message in
                showProgress(message)
        }.completed {
            error in
                completed(error)
        }.cancelled {
            print("Task cancelled")
        }.run()
    }

    // MARK: IBActions
    @IBAction private func openFolder(sender: AnyObject?){
        if let loc = Defaults.sharedInstance.recipeCreateLocation {
            let url = URL(fileURLWithPath: loc, isDirectory: true)
            NSWorkspace.shared.open(url)
        }
    }

    @IBAction private func cancelTask(sender: NSButton){
        if (cancelButton.identifier.rawValue != "Alldone") {
            self.task.cancel()
        }
        self.performSegueWithIdentifier("ProcessingSegue", sender: self)
    }
}

