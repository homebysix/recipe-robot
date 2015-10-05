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

let BGColor = NSColor(SRGBRed: 245/255, green: 245/255, blue: 220/255, alpha: 1).CGColor


extension CAGradientLayer {
    func baseGradient() -> CAGradientLayer {
        let gradientColors: [CGColor] = [BGColor, NSColor.whiteColor().CGColor ]

        let gradientLocations: [Float] = [0.0, 1.0]

        let layer = CAGradientLayer()
        layer.colors = gradientColors
        layer.locations = gradientLocations
        return layer
    }
}

// MARK: Subclases
// MARK: -- Segue --


// MARK: -- Views --
class feedMeDropImageView: NSImageView, NSDraggingDestination {
    override func performDragOperation(sender: NSDraggingInfo) -> Bool {
        if let feedMeViewController = sender.draggingDestinationWindow().contentViewController as? FeedMeViewController,
            files = sender.draggingPasteboard().propertyListForType(NSFilenamesPboardType) as? NSArray,
            file = files.firstObject as? String {
                feedMeViewController.task.appOrRecipe = file
                feedMeViewController.performSegueWithIdentifier("feedMeSegue", sender: self)

                let item = sender.draggingPasteboard().pasteboardItems
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

    var task: RecipeRobotTask = RecipeRobotTask()

    override func viewDidLoad() {
        super.viewDidLoad()
        self.view.wantsLayer = true
    }

    override func awakeFromNib() {
        super.awakeFromNib()
        if let layer = self.view.layer {
            view.layer = CAGradientLayer().baseGradient()
            view.layer?.needsDisplay()
        }
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
                if let dest = dest as? RecipeChoiceViewController {
                    dest.configure()
                } else if let dest = dest as? ProcessingViewController {
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
class RecipeChoiceViewController: RecipeRobotViewController, NSTableViewDataSource, NSTableViewDelegate {

    // MARK: IBOutlets
    @IBOutlet var appIconImageView: NSImageView?

    private let recipeTypes = [
        "download",
        "munki",
        "pkg",
        "install",
        "jss",
        "absolute",
        "sccm",
        "ds"
    ]
    
    private var enabledRecipeTypes = NSUserDefaults.standardUserDefaults().objectForKey("RecipeTypes") as? [String]


    // MARK: Overrides
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do view setup here.
    }

    func configure(){
        let appOrRecipe = self.task.appOrRecipe as NSString
        switch appOrRecipe.pathExtension {
        case "app":
            let icon = NSWorkspace.sharedWorkspace().iconForFile(appOrRecipe as String)
            self.appIconImageView?.image = icon
        case "recipe":
            let icon = NSWorkspace.sharedWorkspace().iconForFile(appOrRecipe as String)
        default :
            self.appIconImageView?.image = NSImage()
        }
    }

    override func prepareForSegue(segue: NSStoryboardSegue, sender: AnyObject?) {
        super.prepareForSegue(segue, sender: sender)
        if let currentTypes = self.enabledRecipeTypes {
            NSUserDefaults.standardUserDefaults().setObject(currentTypes, forKey:"RecipeTypes")
            self.task.recipeTypes = currentTypes
        }
    }

    // MARK: IBActions
    @IBAction func recipeTypeClicked(sender: AnyObject){
        if let obj = sender as? NSButton {
                if let t = obj.identifier {
                    if (obj.state == NSOnState){
                        enabledRecipeTypes?.append(t)
                    } else {
                        if enabledRecipeTypes?.count > 0 {
                            if let idx = find(enabledRecipeTypes!, t){
                                enabledRecipeTypes?.removeAtIndex(idx)
                            }
                        }
                    }
                }
        }
    }

    // MARK: TableView Data & Delegate
    func numberOfRowsInTableView(tableView: NSTableView) -> Int {
        return recipeTypes.count
    }

    func tableView(tableView: NSTableView, viewForTableColumn tableColumn: NSTableColumn?, row: Int) -> NSView? {

        let cell = tableView.makeViewWithIdentifier("recipeCell", owner: self) as? recipeTypeCellView

        let recipeType = recipeTypes[row]

        if let checkBox = cell?.checkBox {
            checkBox.title = recipeType
            checkBox.identifier = recipeType

            if let types = self.enabledRecipeTypes,
                idx = find(types , recipeType)
            {
                checkBox.state = NSOnState
            }
        }
        return cell
    }
}

// MARK: - Processing
class ProcessingViewController: RecipeRobotViewController {

    @IBOutlet private var progressView: NSTextView?
    @IBOutlet private var cancelButton: NSButton?

    @IBOutlet var gearContainerView: NSView!


    override func viewDidLoad() {
        super.viewDidLoad()
        self.progressView?.backgroundColor = NSColor.clearColor()
        self.progressView?.drawsBackground = false
        if let clipView = self.progressView?.superview as? NSClipView,
                scrollView = clipView.superview as? NSScrollView {
            scrollView.backgroundColor = NSColor.clearColor()
            scrollView.drawsBackground = false
        }
    }

    override func awakeFromNib() {
        super.awakeFromNib()
    }

    func gearsShouldRotate(start: Bool){
        for view in gearContainerView.subviews {
            if let view = view as? NSImageView {
                if start {
                    view.rotate()
                    view.colorize()
                }  else {
                    view.stopRotation()
                    view.stopColorize()
                }
            }
        }
    }

    func processRecipes() {

        gearsShouldRotate(true)

        // Do view setup here.
        self.task.createRecipes({[weak self] (progress) -> Void in
            let attrStr = NSAttributedString(string: progress)

            if let pView = self?.progressView {
                pView.textStorage?.appendAttributedString(attrStr)
            }

            }, completion: {[weak self](error) ->
                Void in

                if let pView = self?.progressView, error = error {
                    let attrString = NSAttributedString(string: error.localizedDescription)
                    pView.textStorage?.appendAttributedString(attrString)
                }

                if let sound = NSSound(named: "Glass"){
                    sound.play()
                }

                self!.gearsShouldRotate(false)
                if let button = self!.cancelButton {
                    button.title = "Let's Do Another!"
                }
        })
    }
    // MARK: IBActions
    @IBAction private func cancelTask(sender: NSButton){
        if self.task.isProcessing {
            cancelButton = sender
            self.task.cancel()
        } else {
            self.performSegueWithIdentifier("allDoneSegue", sender: self)
        }
    }
}

