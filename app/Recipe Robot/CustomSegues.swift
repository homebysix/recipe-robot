//
//  CustomSegues.swift
//  Recipe Robot
//
//  Created by Eldon on 9/27/15.
//  Copyright (c) 2015 Eldon Ahrold. All rights reserved.
//

import Cocoa
import QuartzCore

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

class PushSegue: NSStoryboardSegue {
    override func perform() {
        self.sourceController.presentViewController(
            self.destinationController as! NSViewController, animator: PushTransitionAnimator())
    }
}

class FadeSegue: NSStoryboardSegue {
    override func perform() {
        self.sourceController.presentViewController(
            self.destinationController as! NSViewController, animator: PushTransitionAnimator())
    }
}

class FadeTransitionAnimator: NSObject, NSViewControllerPresentationAnimator {

    func animatePresentationOfViewController(toViewController: NSViewController, fromViewController: NSViewController) {

        if let tvc = toViewController as? RecipeRobotViewController,
            fvc = fromViewController as? RecipeRobotViewController {
            tvc.view.wantsLayer = true
            tvc.view.layerContentsRedrawPolicy = .OnSetNeedsDisplay
            tvc.view.alphaValue = 0
            fvc.view.addSubview(tvc.view)
            tvc.view.frame = fvc.view.frame
            NSAnimationContext.runAnimationGroup({ context in
                context.duration = 2
                tvc.view.animator().alphaValue = 1
                }, completionHandler: {
            })
        }
    }

    func animateDismissalOfViewController(viewController: NSViewController, fromViewController: NSViewController) {

        viewController.view.wantsLayer = true
        viewController.view.layerContentsRedrawPolicy = .OnSetNeedsDisplay

        NSAnimationContext.runAnimationGroup({ (context) -> Void in
            context.duration = 0.5
            viewController.view.animator().alphaValue = 0
            }, completionHandler: {
                viewController.view.removeFromSuperview()
        })
    }
}


class PushTransitionAnimator: NSObject, NSViewControllerPresentationAnimator {
    func animatePresentationOfViewController(viewController: NSViewController, fromViewController: NSViewController) {
        viewController.view.frame = NSMakeRect(NSWidth(fromViewController.view.frame), // x
            0, // y
            NSWidth(fromViewController.view.frame), // width
            NSHeight(fromViewController.view.frame)); // height

        viewController.view.autoresizingMask = [.ViewWidthSizable, .ViewHeightSizable]
        fromViewController.view.addSubview(viewController.view)
        let dRect = fromViewController.view.frame

        NSAnimationContext.runAnimationGroup({ (context) -> Void in
            context.duration = 0.5;
            context.timingFunction = CAMediaTimingFunction(name:kCAMediaTimingFunctionEaseOut)
            viewController.view.animator().frame = dRect
            }, completionHandler: { () -> Void in
        })
    }


    func animateDismissalOfViewController(viewController: NSViewController, fromViewController: NSViewController) {
        let destinationRect = NSMakeRect(NSWidth(fromViewController.view.frame), // x
            0, // y
            NSWidth(fromViewController.view.frame), // width
            NSHeight(fromViewController.view.frame)); // height

        let dRect = fromViewController.view.frame
        NSAnimationContext.runAnimationGroup({ (context) -> Void in
            context.duration = 0.5;
            context.timingFunction = CAMediaTimingFunction(name:kCAMediaTimingFunctionEaseIn)
            viewController.view.animator().frame = dRect
            }, completionHandler: { () -> Void in
                viewController.view.removeFromSuperview()
        })

    }
}