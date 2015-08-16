//
//  ViewController.swift
//  RecipeRobot
//
//  Created by Eldon Ahrold on 8/14/15.
//  Copyright (c) 2015 Eldon Ahrold. All rights reserved.
//

import Cocoa
import AudioToolbox

import AVFoundation

// MARK: Subclases
// MARK: -- Segue --
class ReplaceSegue: NSStoryboardSegue {
    override func perform() {
        if let fromViewController = sourceController as? RecipeRobotViewController {
            if let toViewController = destinationController as? RecipeRobotViewController {
                // no animation.
                toViewController.task = fromViewController.task;
                fromViewController.view.window?.contentViewController = toViewController
            }
        }
    }
}

// MARK: -- Views --
class feedMeDropView: NSView, NSDraggingDestination {
    override init(frame: NSRect) {
        super.init(frame: frame)
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        registerForDraggedTypes([NSFilenamesPboardType])
    }

    override func drawRect(dirtyRect: NSRect)  {
        super.drawRect(dirtyRect)
        NSColor.gridColor().set()
        NSRectFill(dirtyRect)
    }

    override func prepareForDragOperation(sender: NSDraggingInfo) -> Bool {
        return true
    }

    override func performDragOperation(sender: NSDraggingInfo) -> Bool {
        if let feedMeViewController = sender.draggingDestinationWindow().contentViewController as? FeedMeViewController,
            files = sender.draggingPasteboard().propertyListForType(NSFilenamesPboardType) as? NSArray,
            file = files.firstObject as? String {
                feedMeViewController.task.appOrRecipe = file
                feedMeViewController.segueButton?.performClick(self)
                let item = sender.draggingPasteboard().pasteboardItems
        }
        return true
    }

    override func concludeDragOperation(sender: NSDraggingInfo?) {
        // All done.
    }

    override func draggingEntered(sender: NSDraggingInfo) -> NSDragOperation  {
        return NSDragOperation.Copy
    }
}

// MARK: -- TableCellView --
class recipeTypeCellView: NSTableCellView {
    @IBOutlet var checkBox: NSButton?
}

// MARK: View Controllers
/// Base view Controller for Recipe-Robot story board.
class RecipeRobotViewController: NSViewController {

    var task: RecipeRobotTask = RecipeRobotTask()
    @IBOutlet var segueButton: NSButton?

    override func viewDidLoad() {
        super.viewDidLoad()
        // Do any additional setup after loading the view.
    }

    override var representedObject: AnyObject? {
        didSet {
        // Update the view, if already loaded.
        }
    }

    override func prepareForSegue(segue: NSStoryboardSegue, sender: AnyObject?) {
        if let x = segue.sourceController as? RecipeRobotViewController,
            y = segue.destinationController as? RecipeRobotViewController {
                // Here we pass off the task object during the seague transition.
                // So in the future make sure to call super.prepareForSegue() on any
                // additional viewControllers.
                y.task = x.task
        }
    }
}

class FeedMeViewController: RecipeRobotViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        self.task = RecipeRobotTask()
    }
}

class RecipeChoiceViewController: RecipeRobotViewController, NSTableViewDataSource, NSTableViewDelegate {

    // MARK: IBOutlets
    @IBOutlet var appIconImageView: NSImageView?


    private let recipeTypes = ["download", "munki", "pkg", "install", "jss", "absolute", "sccm", "ds"]
    private var enabledRecipeTypes = NSUserDefaults.standardUserDefaults().objectForKey("RecipeTypes") as? [String]


    // MARK: Overrides
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do view setup here.
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

class ProcessingViewController: RecipeRobotViewController {

    @IBOutlet private var progressView: NSTextView?
    @IBOutlet private var cancelButton: NSButton?

    override func viewDidLoad() {
        super.viewDidLoad()
        // Do view setup here.
        self.task.createRecipes({ (progress) -> Void in
            let attrStr = NSAttributedString(string: progress)
            self.progressView?.textStorage?.appendAttributedString(attrStr)
        }, completion: {(error) -> Void in
            if let sound = NSSound(named: "Glass"){
                sound.play()
            }

            if let button = self.cancelButton {
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
            self.segueButton?.performClick(self)
        }
    }
}

