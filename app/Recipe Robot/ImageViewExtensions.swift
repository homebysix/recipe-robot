//
//  ImageViewExtensions.swift
//  Recipe Robot
//
//  Created by Eldon on 9/28/15.
//  Copyright (c) 2015 Eldon Ahrold. All rights reserved.
//

import AppKit

extension NSImageView {
    public func stopRobotRotate(){

        if self.layer != nil {
            let opacity: Float = 0.20 //presentationLayer.opacity

            let colorize = CABasicAnimation(keyPath: "opacity")
            colorize.duration = CFTimeInterval(round(opacity * 10.00))
            colorize.fromValue = opacity
            colorize.toValue = 0.0
            colorize.timingFunction = CAMediaTimingFunction(name: kCAMediaTimingFunctionDefault)

            colorize.repeatCount = 0
            colorize.autoreverses = false

            self.layer!.addAnimation(colorize, forKey: "alpha0")
            self.layer!.removeAnimationForKey("colorize")

        }
        NSTimer.scheduledTimerWithTimeInterval(5.0, target: self, selector: "removeAnimations:", userInfo: nil, repeats: false)

    }

    public func robotRotate(){
        if self.layer != nil {
            self.wantsLayer = true
            self.layer!.anchorPoint = CGPointMake(0.5, 0.5)

            let rotation = CABasicAnimation(keyPath:"transform")
            rotation.duration = 50.0

            let angle = CGFloat(4*M_PI)
            rotation.toValue = angle

            rotation.timingFunction = CAMediaTimingFunction(name: kCAMediaTimingFunctionLinear)
            rotation.valueFunction = CAValueFunction(name:kCAValueFunctionRotateZ);

            self.layer!.addAnimation(rotation, forKey: "transform.rotation.z")

            let alphaPulse = CABasicAnimation(keyPath: "opacity")
            alphaPulse.duration = 1
            alphaPulse.fromValue = 0.0
            alphaPulse.toValue = 0.4
            alphaPulse.timingFunction = CAMediaTimingFunction(name: kCAMediaTimingFunctionEaseInEaseOut)
            alphaPulse.autoreverses = true
            alphaPulse.repeatCount = FLT_MAX
            self.layer!.addAnimation(alphaPulse, forKey: "colorize")
        }
    }


    internal func removeAnimations(timer: NSTimer){
        timer.invalidate()
        self.layer!.removeAnimationForKey("alpha0")
        self.layer!.removeAnimationForKey("transform.rotation.z")
    }
}
