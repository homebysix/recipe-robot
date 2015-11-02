//
//  ViewController.swift
//
//  Recipe Robot
//  Copyright 2015 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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
//        if view.layer != nil {
//            view.layer = CAGradientLayer().baseGradient()
//            view.layer!.needsDisplay()
//        }
    }

    override var representedObject: AnyObject? {
        didSet {
        // Update the view, if already loaded.
        }
    }

    override func prepareForSegue(segue: NSStoryboardSegue, sender: AnyObject?) {
        if let source = segue.sourceController as? RecipeRobotViewController,
            dest = segue.destinationController as? RecipeRobotViewController {
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
        ignoreButton.action = "changeIgnoreState:"

        eventMonitor = NSEvent.addLocalMonitorForEventsMatchingMask(NSEventMask.FlagsChangedMask) { [weak self](event) -> NSEvent? in
            if let _self = self {
                if (_self.ignoreButton.state == NSOnState){
                    _self.ignoreButton.hidden = false
                } else {
                    _self.ignoreButton.hidden = (event.modifierFlags.rawValue & NSEventModifierFlags.AlternateKeyMask.rawValue) == 0
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
}

// MARK: - Preference View Controller

class PreferenceViewController: RecipeRobotViewController {

    // MARK: IBOutlets
    @IBOutlet var tableView: NSTableView!
    @IBOutlet var scrollView: NSScrollView!

    @IBOutlet var dsFolderPathButton: NSButton!
    @IBOutlet var recipeFolderPathButton: NSButton!

    let recipeTypes: [String] = [
        "download",
        "munki",
        "pkg",
        "install",
        "jss",
        "absolute",
        "sccm",
        "ds",
        "filewave"
    ]

    private var enabledRecipeTypes = Defaults.sharedInstance.recipeTypes ?? [String]()

    // MARK: Overrides
    override func viewDidLoad() {
        super.viewDidLoad()
        self.tableView.backgroundColor = NSColor.clearColor()
        self.scrollView.backgroundColor = NSColor.clearColor()
        self.scrollView.focusRingType = NSFocusRingType.None

        self.recipeFolderPathButton.action = "chooseFilePath:"
        self.recipeFolderPathButton.target = self
        self.dsFolderPathButton.action = "chooseFilePath:"
        self.dsFolderPathButton.target = self
        // Do view setup here.
    }

    override func viewWillDisappear() {
        super.viewWillDisappear()
        Defaults.sharedInstance.recipeTypes = self.enabledRecipeTypes
    }

    @IBAction func close(sender: AnyObject) {
        self.dismissController(sender)
        self.view.window?.close()
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

        let dir = (directoryURL as NSString).stringByExpandingTildeInPath
        var isDir: ObjCBool = ObjCBool(false)
        if NSFileManager.defaultManager().fileExistsAtPath(dir, isDirectory: &isDir) && isDir {
            panel.directoryURL = NSURL(fileURLWithPath: dir)
        }

        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.canCreateDirectories = true
        panel.allowsMultipleSelection = false
        panel.prompt = "Choose";

        panel.beginSheetModalForWindow(self.view.window!) {
            [weak self] result in
            if (result == NSFileHandlingPanelOKButton) {
                if let path = panel.URL?.path {
                    if sender === self!.recipeFolderPathButton {
                        d.recipeCreateLocation = path
                    }
                    else if sender === self!.dsFolderPathButton {
                        d.dsPackagePath = path
                    }
                }
            }
        }
    }
}

// MARK: Preference View Controller: Table View
extension PreferenceViewController: NSTableViewDataSource, NSTableViewDelegate {
    func numberOfRowsInTableView(tableView: NSTableView) -> Int {
        return recipeTypes.count
    }

    func tableView(tableView: NSTableView, objectValueForTableColumn tableColumn: NSTableColumn?, row: Int) -> AnyObject? {
        return (enabledRecipeTypes.contains(recipeTypes[row])) ? NSOnState: NSOffState
    }

    func tableView(tableView: NSTableView, willDisplayCell cell: AnyObject, forTableColumn tableColumn: NSTableColumn?, row: Int) {
        if let cell = cell as? NSButtonCell {
            cell.title = recipeTypes[row]
        }
    }

    func tableView(tableView: NSTableView, setObjectValue object: AnyObject?, forTableColumn tableColumn: NSTableColumn?, row: Int) {
        if let value = object as? Int {
            let type = recipeTypes[row]
            let idx = enabledRecipeTypes.indexOf(type)

            if (value == NSOnState) && (idx == nil) {
                enabledRecipeTypes.append(type)
            } else if (value == NSOffState){
                if enabledRecipeTypes.count > 0 {
                    if let idx = idx {
                        enabledRecipeTypes.removeAtIndex(idx)
                    }
                }
            }
        }
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

    @IBOutlet var gearContainerView: NSView!

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

        var traits =  NSFontSymbolicTraits(0)
        let green = StatusImage.Available.image
        let red = StatusImage.Unavailable.image

        infoLabel?.textColor = Color.White.ns
        infoLabel?.stringValue = "Preping..."

        listener.notificationHandler = {
            [weak self] noteType, info in

            var color = NSColor.blackColor()
            switch noteType {
            case .Info:
                break
            case .Recipes:
                self!.warningIndicator?.cell?.image = green
            case .Reminders:
                self!.reminderIndicator?.cell?.image = green
            case .Icons:
                self!.iconIndicator?.cell?.image = green
            case .Warnings:
                color = Color.Yellow.ns
                traits = (traits & NSFontSymbolicTraits(NSFontItalicTrait))
                self!.warningIndicator?.cell?.image = red
            case .Error:
                color = Color.Red.ns
                self!.errorIndicator?.cell?.image = red
            case .Complete:
                self!.completionInfo = info
            }

//            if let string = info["message"] as? String {
//                if let pView = self?.progressView {
//                    pView.textStorage?.appendString("\(noteType.prefix) \(string)\n\n", color: noteType.color.ns)
//                    pView.scrollToEndOfDocument(self)
//                }
//            }
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

        showInFinderButton.enabled = false
        showInFinderButton.target = self
        showInFinderButton.action = "openFolder:"
    }

    override func awakeFromNib() {
        super.awakeFromNib()
    }

    func gearsShouldRotate(start: Bool){
        for view in gearContainerView.subviews {
            if let view = view as? GearImageView {
                if start {
                    let delay = NSTimeInterval(arc4random_uniform(2000)) / 1000.0
                    NSTimer.scheduledTimerWithTimeInterval(delay, target: view, selector: "start", userInfo: nil, repeats: false)
                }  else {
                    view.stop()
                }
            }
        }
    }

    func processRecipes() {
        gearsShouldRotate(true)

        // Do view setup here.
        self.task.createRecipes({
            [weak self] progress in /* Do nothing */
                if let pView = self?.progressView {
                    let (string, color) = progress.decodedANSI();
                    pView.textStorage?.appendString(string, color: color)
                    pView.scrollToEndOfDocument(self)
                }
            }, completion: {[weak self]
                error in

                let success = (error == nil || error!.code == 0)
                self!.showInFinderButton.enabled = success
                
                if success {
                    self!.titleLabel.stringValue = "Ding! All done."
                    self!.appIcon?.image = NSImage(named: "NSFolder")

                    self!.appIcon?.action = "openFolder:"
                    self!.appIcon?.target = self
                } else {
                    self!.appIcon?.image = NSImage(named: "NSCaution")
                    self!.titleLabel.stringValue = "Oops, I couldn't make recipes for this app."
                }

                if let sound = sound{
                    sound.play()
                }

                self?.gearsShouldRotate(false)
                if let button = self?.cancelButton {
                    button.title = "Let's do another"
                }
        })
    }

    // MARK: IBActions
    @IBAction private func openFolder(sender: AnyObject?){
        if let loc = Defaults.sharedInstance.recipeCreateLocation {
            let url = NSURL(fileURLWithPath: loc, isDirectory: true)
            NSWorkspace.sharedWorkspace().openURL(url)
        }
    }

    @IBAction private func cancelTask(sender: NSButton){
        if self.task.isProcessing {
            cancelButton = sender
            self.task.cancel()
        }
        self.dismissController(sender)
    }

    @IBAction private func showCompletionPopover(sender: NSButton){
        var info: [String]? = nil
        
        if sender === recipeIndicator { /* Nothing here yet*/}
        else if sender === iconIndicator { /* Nothing here yet*/}
        else if sender === reminderIndicator {
            info = completionInfo?[NoteType.Reminders.key] as? [String]
        }
        else if sender === warningIndicator {
            info = completionInfo?[NoteType.Warnings.key] as? [String]
        }
        else if sender === errorIndicator {
            info = completionInfo?[NoteType.Error.key] as? [String]
        }

        info = ["first message", "second message", "third message"]
        if info != nil {
            let message = info!.reduce(""){"\($0)* \($1)\n"}.trimmedFull
            let popover = AHHelpPopover(sender: sender)
            popover.helpText = message
            popover.openPopover()
        }
    }
}

