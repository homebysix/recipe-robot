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

// MARK: - Preference View Controller

class PreferenceViewController: RecipeRobotViewController {

    // MARK: IBOutlets
    @IBOutlet var tableView: NSTableView!
    @IBOutlet var scrollView: NSScrollView!

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
    
    private var enabledRecipeTypes = Defaults.sharedInstance.recipeTypes ?? [String]()

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
            let title = recipeTypes[row]
            cell.title = title
        }
    }

    func tableView(tableView: NSTableView, setObjectValue object: AnyObject?, forTableColumn tableColumn: NSTableColumn?, row: Int) {
        if let value = object as? Int {
            let type = recipeTypes[row]
            let idx = enabledRecipeTypes.indexOf(type)

            if (value == NSOnState) && ( idx == nil) {
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
    @IBOutlet weak var appIcon: NSImageView!
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

        listener.notificationHandler = {[weak self]
            noteType, info in
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

                    attrs[NSForegroundColorAttributeName] = color
                    attrs[NSFontAttributeName] =  NSFont(descriptor: descriptor, size: 0)

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
                    button.title = "Do another?"
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



