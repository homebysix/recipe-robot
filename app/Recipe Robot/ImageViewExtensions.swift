//
//  ImageViewExtensions.swift
//  Recipe Robot
//
//  Created by Eldon on 9/28/15.
//  Copyright (c) 2015 Linde Group. All rights reserved.
//

import AppKit

extension NSImageView {
    public func stopRotation(){
        if self.layer != nil {
            self.layer!.removeAnimationForKey("transform.rotation.z")
        }
    }

    public func rotate(){
        if self.layer != nil {
            self.wantsLayer = true
            self.layer!.anchorPoint = CGPointMake(0.5, 0.5)

            let rotation = CABasicAnimation(keyPath:"transform")
            rotation.duration = 100.0

            let angle = CGFloat(4*M_PI)
            rotation.toValue = angle

            rotation.timingFunction = CAMediaTimingFunction(name: kCAMediaTimingFunctionLinear)
            rotation.valueFunction = CAValueFunction(name:kCAValueFunctionRotateZ);

            self.layer!.addAnimation(rotation, forKey: "transform.rotation.z")
        }
    }

    public func colorize(){
        if self.layer != nil {
            let colorize = CABasicAnimation(keyPath: "opacity")
            colorize.duration = 1
            colorize.fromValue = 0.2
            colorize.toValue = 0.4
            colorize.timingFunction = CAMediaTimingFunction(name: kCAMediaTimingFunctionEaseInEaseOut)
            colorize.autoreverses = true
            colorize.repeatCount = FLT_MAX
            self.layer!.addAnimation(colorize, forKey: "colorize")
        }
    }

    public func stopColorize(){
        if self.layer != nil {
            self.layer!.removeAnimationForKey("colorize")
        }
    }
}
