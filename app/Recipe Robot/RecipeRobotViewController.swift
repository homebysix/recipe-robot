//
//  ViewController.swift
//  RecipeRobot
//
//  Created by Eldon Ahrold on 8/14/15.
//  Copyright (c) 2015 Eldon Ahrold. All rights reserved.
//

import Cocoa
import AudioToolbox
import Quartz


//let sound = NSSound(named: "Glass")
var sound: NSSound? = nil


// MARK: -- Views --
class feedMeDropImageView: NSImageView {

    override func performDragOperation(sender: NSDraggingInfo) -> Bool {
        if let controller = sender.draggingDestinationWindow()!.contentViewController as? FeedMeViewController,
            files = sender.draggingPasteboard().propertyListForType(NSFilenamesPboardType) as? NSArray,
            file = files.firstObject as? String {

                controller.task = RecipeRobotTask()
                controller.task.appOrRecipe = file
                controller.performSegueWithIdentifier("feedMeSegue", sender: self)
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

// MARK: -- TableCellView --
class recipeTypeCellView: NSTableCellView {
    @IBOutlet var checkBox: NSButton?
}

// MARK: - View Controllers
// MARK: -
// MARK: Base view Controller for Recipe-Robot story board.
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
                dest.task = source.task
                if let dest = dest as? ProcessingViewController {
                    dest.processRecipes()
                } else if let dest = dest as? FeedMeViewController {
                    dest.task = RecipeRobotTask()
                }
        }
    }
}

// MARK: - FeedMe
class FeedMeViewController: RecipeRobotViewController {
    @IBOutlet var Gear1: NSImageView!

    override func awakeFromNib() {
        super.awakeFromNib()
    }
    override func viewDidLoad() {
        super.viewDidLoad()
    }

    override func viewDidAppear() {
        super.viewDidAppear()
        self.task = RecipeRobotTask()
    }
}

// MARK: - Recipe Choice
class PreferenceViewController: RecipeRobotViewController, NSTableViewDataSource, NSTableViewDelegate {

    @IBOutlet var tableView: NSTableView!
    @IBOutlet var scrollView: NSScrollView!

    // MARK: IBOutlets
    @IBOutlet var appIconImageView: NSImageView?

    let recipeTypes: [String] = [
        "download",
        "munki",
        "pkg",
        "install",
        "jss",
        "absolute",
        "sccm",
        "ds"
    ]
    
    private var enabledRecipeTypes = NSUserDefaults.standardUserDefaults().objectForKey("RecipeTypes") as? [String] ?? [String]()


    // MARK: Overrides
    override func viewDidLoad() {
        super.viewDidLoad()
        self.tableView.backgroundColor = NSColor.clearColor()
        self.scrollView.backgroundColor = NSColor.clearColor()
        self.scrollView.focusRingType = NSFocusRingType.None
        
        // Do view setup here.
    }

    override func viewWillDisappear() {
        super.viewWillDisappear()
        NSUserDefaults.standardUserDefaults().setObject(self.enabledRecipeTypes, forKey:"RecipeTypes")
    }

    func numberOfRowsInTableView(tableView: NSTableView) -> Int {
        return recipeTypes.count
    }

    func tableView(tableView: NSTableView, objectValueForTableColumn tableColumn: NSTableColumn?, row: Int) -> AnyObject? {
        return (enabledRecipeTypes.contains(recipeTypes[row])) ? NSOnState: NSOffState
    }

    func tableView(tableView: NSTableView, willDisplayCell cell: AnyObject, forTableColumn tableColumn: NSTableColumn?, row: Int) {
        if let cell = cell as? NSButtonCell {
            let title = recipeTypes[row]
            cell.title = title
        }
    }

    func tableView(tableView: NSTableView, setObjectValue object: AnyObject?, forTableColumn tableColumn: NSTableColumn?, row: Int) {
        if let value = object as? Int {
            let t = recipeTypes[row]
            let idx = enabledRecipeTypes.indexOf(t)

            if (value == NSOnState) && ( idx == nil) {
                enabledRecipeTypes.append(t)
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
    @IBOutlet weak var appIcon: NSImageView!
    @IBOutlet weak var infoLabel: NSTextField!

    @IBOutlet var gearContainerView: NSView!
    private let listener = NotificationListener()

    override func viewDidLoad() {
        super.viewDidLoad()
        progressView?.hidden = true

        listener.notificationHandler = {
            noteType, info in
            var color = NSColor.whiteColor()
            switch noteType {
            case .Error:
                color = Color.Red.ns
            case .Reminders:
                color = Color.Yellow.ns
            case .Warnings:
                break
            case .Recipes:
                break
            case .Icons:
                break
            }

            if let string = info["message"] as? String {
                let attrs = [NSForegroundColorAttributeName: color]
                self.infoLabel.attributedStringValue = NSAttributedString(string: string, attributes: attrs)
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
        if let icon = task.appIcon {
            appIcon.image = icon
        }
        if let name = task.appOrRecipeName {
            titleLabel.stringValue = "Making " + name + " recipes..."
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
                    let delay = NSTimeInterval(arc4random_uniform(2000)) / 1000
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
        self.task.createRecipes({[weak self] (progress) -> Void in

            if let pView = self?.progressView {
                pView.textStorage?.appendAttributedString(progress.parseANSI())
                pView.scrollToEndOfDocument(self)
            }

            }, completion: {[weak self]
                error in

                if error == nil {
                    self!.appIcon.image = NSImage(named: "NSFolder")
                    self!.titleLabel.stringValue = "All Done"
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
                    button.title = "Do Another?"
                }
        })
    }
    // MARK: IBActions
    @IBAction private func cancelTask(sender: NSButton){
        if self.task.isProcessing {
            cancelButton = sender
            self.task.cancel()
        }
        self.dismissController(sender)
    }
}



