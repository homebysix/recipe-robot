//
//  CustomSegues.swift
//  Recipe Robot
//
//  Created by Eldon on 9/27/15.
//  Copyright (c) 2015 Linde Group. All rights reserved.
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

class FadeTransitionAnimator: NSObject, NSViewControllerPresentationAnimator {

    func animatePresentationOfViewController(toViewController: NSViewController, fromViewController: NSViewController) {

        toViewController.view.wantsLayer = true
        toViewController.view.layerContentsRedrawPolicy = .OnSetNeedsDisplay
        toViewController.view.alphaValue = 0
        fromViewController.view.addSubview(toViewController.view)
        toViewController.view.frame = fromViewController.view.frame

        NSAnimationContext.runAnimationGroup({ context in
            context.duration = 2
            toViewController.view.animator().alphaValue = 1
            }, completionHandler: nil)
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

        viewController.view.autoresizingMask = .ViewWidthSizable | .ViewHeightSizable
        fromViewController.view.addSubview(viewController.view)
        let dRect = fromViewController.view.frame
        let pRect = NSMakeRect(-dRect.size.width, 0, dRect.size.width, dRect.size.height)

        NSAnimationContext.runAnimationGroup({ (context) -> Void in
            context.duration = 0.5;
            context.timingFunction = CAMediaTimingFunction(name:kCAMediaTimingFunctionEaseOut)
            viewController.view.animator().frame = dRect
            fromViewController.view.animator().frame = pRect
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