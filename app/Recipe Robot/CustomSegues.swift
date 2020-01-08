//
//  CustomSegues.swift
//
//  Recipe Robot
//  Copyright 2015-2020 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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
import AppKit
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
        guard let sourceViewController = sourceController as? NSViewController else {
            print ("error coercing sourceController to ViewController")
            return
        }
        guard let destinationViewController = destinationController as? NSViewController else  {
            print ("error coercing destinationController to ViewController")
            return
        }
        sourceViewController.present( destinationViewController, animator: PushTransitionAnimator())
    }
}

class FadeSegue: NSStoryboardSegue {
    override func perform() {
        guard let sourceViewController = sourceController as? NSViewController else {
            print ("error coercing sourceController to ViewController")
            return
        }
        guard let destinationViewController = destinationController as? NSViewController else  {
            print ("error coercing destinationController to ViewController")
            return
        }

        sourceViewController.present(destinationViewController, animator: FadeTransitionAnimator())
    }
}

class FadeTransitionAnimator: NSObject, NSViewControllerPresentationAnimator {
    func animatePresentation(of toViewController: NSViewController, from fromViewController: NSViewController) {
        if let tvc = toViewController as? RecipeRobotViewController,
            let fvc = fromViewController as? RecipeRobotViewController {
            tvc.view.wantsLayer = true
            tvc.view.layerContentsRedrawPolicy = .onSetNeedsDisplay
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

    func animateDismissal(of viewController: NSViewController, from fromViewController: NSViewController) {
        viewController.view.wantsLayer = true
        viewController.view.layerContentsRedrawPolicy = .onSetNeedsDisplay

        NSAnimationContext.runAnimationGroup({ (context) -> Void in
            context.duration = 0.5
            viewController.view.animator().alphaValue = 0
            }, completionHandler: {
                viewController.view.removeFromSuperview()
        })
    }
}


class PushTransitionAnimator: NSObject, NSViewControllerPresentationAnimator {
    func animatePresentation(of viewController: NSViewController, from fromViewController: NSViewController) {
        viewController.view.frame = NSMakeRect(NSWidth(fromViewController.view.frame), // x
            0, // y
            NSWidth(fromViewController.view.frame), // width
            NSHeight(fromViewController.view.frame)); // height

        viewController.view.autoresizingMask = [NSView.AutoresizingMask.width, NSView.AutoresizingMask.height]

        fromViewController.view.addSubview(viewController.view)
        let dRect = fromViewController.view.frame

        NSAnimationContext.runAnimationGroup({ (context) -> Void in
            context.duration = 0.5;
            context.timingFunction = CAMediaTimingFunction(name:CAMediaTimingFunctionName.easeOut)
            viewController.view.animator().frame = dRect
            }, completionHandler: { () -> Void in
        })
    }

    func animateDismissal(of viewController: NSViewController, from fromViewController: NSViewController) {
        let dRect = fromViewController.view.frame
        NSAnimationContext.runAnimationGroup({ (context) -> Void in
            context.duration = 0.5;
            context.timingFunction = CAMediaTimingFunction(name:CAMediaTimingFunctionName.easeIn)
            viewController.view.animator().frame = dRect
            }, completionHandler: { () -> Void in
                viewController.view.removeFromSuperview()
        })
    }
}
