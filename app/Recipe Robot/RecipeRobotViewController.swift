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

    override func awakeFromNib() {
        super.awakeFromNib()
    }

    override func viewDidLoad() {
        ignoreButton.target = self
        ignoreButton.action = "changeIgnoreState:"

        NSEvent.addLocalMonitorForEventsMatchingMask(NSEventMask.FlagsChangedMask) { [weak self](event) -> NSEvent? in

            if (self!.ignoreButton.state == NSOnState){
                self!.ignoreButton.hidden = false
            } else {
                self!.ignoreButton.hidden = (event.modifierFlags.rawValue & NSEventModifierFlags.AlternateKeyMask.rawValue) == 0
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
    @IBOutlet private var cancelButton: NSButton?
    @IBOutlet weak var titleLabel: NSTextField!
    @IBOutlet weak var appIcon: NSButton!
    @IBOutlet weak var infoLabel: NSTextField!

    @IBOutlet var gearContainerView: NSView!


    @IBOutlet weak var recipeIndicator: NSButton?
    @IBOutlet weak var reminderIndicator: NSButton?
    @IBOutlet weak var iconIndicator: NSButton?
    @IBOutlet weak var warningIndicator: NSButton?
    @IBOutlet weak var errorIndicator: NSButton?

    private let listener = NotificationListener()

    override func viewDidLoad() {
        super.viewDidLoad()
        progressView?.hidden = true

        var traits =  NSFontSymbolicTraits(0)
        let green = StatusImage.Available.image
        let red = StatusImage.Unavailable.image

        let defaultAttrs = self.infoLabel.attributedStringValue.attributesAtIndex(0, effectiveRange: nil)

        infoLabel.textColor = Color.White.ns
        infoLabel.stringValue = "Preping..."

        listener.notificationHandler = {
            [weak self] noteType, info in

            var color = NSColor.whiteColor()
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
            }

            if let _string = info["message"] as? String {
                // Trim the progress message down to the first two lines.
                let string = _string.splitByLine()
                                    .prefix(2)
                                    .reduce(""){"\($0) \($1)"}
                                    .trimmed

                var attrs = [String: AnyObject]()

                if let label = self?.infoLabel {
                    let descriptor = label.font!
                                          .fontDescriptor
                                          .fontDescriptorWithSymbolicTraits(traits)

                    if label.attributedStringValue.length > 0 {
                        attrs = label.attributedStringValue
                                     .attributesAtIndex(0, effectiveRange: nil)
                    } else {
                        attrs = defaultAttrs
                    }

                    // Setting size to 0 keeps it the same.
                    attrs[NSFontAttributeName] =  NSFont(descriptor: descriptor, size: 0)
                    attrs[NSForegroundColorAttributeName] = color

                    label.attributedStringValue = NSAttributedString(string: string,
                                                                     attributes: attrs)
                }
            }
        }

        self.progressView?.backgroundColor = NSColor.clearColor()
        self.progressView?.drawsBackground = false
        if let clipView = self.progressView?.superview as? NSClipView,
                scrollView = clipView.superview as? NSScrollView {
            scrollView.backgroundColor = NSColor.clearColor()
            scrollView.drawsBackground = false
        }
    }

    override func viewWillAppear() {
        recipeIndicator?.image = StatusImage.PartiallyAvailable.image
        reminderIndicator?.image = StatusImage.PartiallyAvailable.image
        iconIndicator?.image = StatusImage.PartiallyAvailable.image
        warningIndicator?.image = StatusImage.PartiallyAvailable.image
        errorIndicator?.image = StatusImage.PartiallyAvailable.image


        if let icon = task.appIcon {
            appIcon.image = icon
        }
        if let name = task.appOrRecipeName {
            titleLabel.stringValue = "Making \(name) recipes..."
        } else {
            titleLabel.stringValue = "Making recipes..."
        }
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
            [weak self] progress in

            if let pView = self?.progressView {
                pView.textStorage?.appendAttributedString(progress.parseANSI())
                pView.scrollToEndOfDocument(self)
            }

            }, completion: {[weak self]
                error in

                if error == nil || error!.code == 0 {
                    self!.titleLabel.stringValue = "All done! Click the folder below to reveal your recipes."
                    self!.appIcon.image = NSImage(named: "NSFolder")

                    self!.appIcon.action = "openFolder:"
                    self!.appIcon.target = self
                } else {
                    self!.appIcon.image = NSImage(named: "NSCaution")
                    self!.titleLabel.stringValue = "Finished with errors."

                }

                if let pView = self?.progressView, error = error {
                    let attrString = NSAttributedString(string: error.localizedDescription)
                    pView.textStorage?.appendAttributedString(attrString)
                    pView.scrollToEndOfDocument(self)
                }

                if let sound = sound{
                    sound.play()
                }

                self?.gearsShouldRotate(false)
                if let button = self?.cancelButton {
                    button.title = "Do another?"
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
}
