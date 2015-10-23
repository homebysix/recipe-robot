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


let sound = NSSound(named: "Glass")


extension CAGradientLayer {
    func baseGradient() -> CAGradientLayer {
        let gradientColors: [CGColor] = [rrBlueColor.CGColor, rrLtBlueColor.CGColor, rrBlueColor.CGColor ]

        let gradientLocations: [Float] = [0.0, 0.5, 1.0]

        let layer = CAGradientLayer()
        layer.colors = gradientColors
        layer.locations = gradientLocations
        return layer
    }
}

// MARK: Subclases
// MARK: -- Segue --


// MARK: -- Views --
class feedMeDropImageView: NSImageView {

    override func performDragOperation(sender: NSDraggingInfo) -> Bool {
        if let controller = sender.draggingDestinationWindow()!.contentViewController as? FeedMeViewController,
            files = sender.draggingPasteboard().propertyListForType(NSFilenamesPboardType) as? NSArray,
            file = files.firstObject as? String {

                controller.task = RecipeRobotTask()
                controller.task.appOrRecipe = file
                controller.performSegueWithIdentifier("feedMeSegue", sender: self)

//                let item = sender.draggingPasteboard().pasteboardItems
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
        if view.layer != nil {
            view.layer = CAGradientLayer().baseGradient()
            view.layer!.needsDisplay()
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

    // MARK: IBOutlets
    @IBOutlet var appIconImageView: NSImageView?

    @IBOutlet var downloadButton: NSButton!
    @IBOutlet var munkiButton: NSButton!
    @IBOutlet var pkgButton: NSButton!
    @IBOutlet var installButton: NSButton!
    @IBOutlet var jssButton: NSButton!
    @IBOutlet var absoluteButton: NSButton!
    @IBOutlet var sccmButton: NSButton!
    @IBOutlet var dsButton: NSButton!

    var buttons: [String: NSButton] { return [
        "download": downloadButton!,
        "munki": munkiButton!,
        "pkg": pkgButton!,
        "install": installButton!,
        "jss": jssButton!,
        "absolute": absoluteButton!,
        "sccm": sccmButton!,
        "ds": dsButton!
        ]
    }
    
    private var enabledRecipeTypes = NSUserDefaults.standardUserDefaults().objectForKey("RecipeTypes") as? [String] ?? [String]()


    // MARK: Overrides
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do view setup here.
    }

    override func viewWillAppear() {
        configure()
    }

    override func viewWillDisappear() {
        NSUserDefaults.standardUserDefaults().setObject(self.enabledRecipeTypes, forKey:"RecipeTypes")
    }

    func configure(){
        for (k, b) in buttons {
            b.target = self

            b.action = "recipeTypeClicked:"
            b.identifier = k

            b.attributedTitle = NSAttributedString(string: k, attributes: [NSForegroundColorAttributeName: NSColor.whiteColor()])

            var color: NSColor!
            if enabledRecipeTypes.indexOf(k) != nil {
                b.state = NSOnState
                color = rrYellowColor
            } else {
                color = rrGreenColor
            }

            let image = NSImage(size: b.bounds.size)
            image.lockFocus()
            color.drawSwatchInRect(b.bounds)
            image.unlockFocus()
            b.image = image
        }

    }

    // MARK: IBActions
    @IBAction func recipeTypeClicked(sender: AnyObject){
        if let obj = sender as? NSButton {
            if let t = obj.identifier {
                var color: NSColor!
                if (obj.state == NSOnState){
                    enabledRecipeTypes.append(t)
                    color = rrYellowColor
                } else {
                    color = rrGreenColor
                    if enabledRecipeTypes.count > 0 {
                        if let idx = enabledRecipeTypes.indexOf(t){
                            enabledRecipeTypes.removeAtIndex(idx)
                        }
                    }
                }
                let image = NSImage(size: obj.bounds.size)
                image.lockFocus()
                color.drawSwatchInRect(obj.bounds)
                image.unlockFocus()
                obj.image = image
            }
        }
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
                    let delay = NSTimeInterval(arc4random_uniform(2000)+500) / 1000
                    NSTimer.scheduledTimerWithTimeInterval(delay, target: view, selector: "robotRotate", userInfo: nil, repeats: false)
                }  else {
                    view.stopRobotRotate()
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

            }, completion: {[weak self](error) ->
                Void in

                if let pView = self?.progressView, error = error {
                    let attrString = NSAttributedString(string: error.localizedDescription)
                    pView.textStorage?.appendAttributedString(attrString)
                    pView.scrollToEndOfDocument(self)

                }

                if let sound = sound{
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
            self.dismissController(sender)
        }
    }
}



