//
//  Storyboard.swift
//  Recipe Robot
//
//  Created by Eldon on 10/30/15.
//  Copyright (c) 2015 Eldon Ahrold. All rights reserved.
//

import Cocoa

struct MainStoryboard {

    private let storyboard = NSStoryboard(name: "Main", bundle: NSBundle.mainBundle())

    var preferenceViewController: PreferenceViewController {
        return self.storyboard.instantiateControllerWithIdentifier("Preferences")
            as! PreferenceViewController
    }

    var processingViewController: ProcessingViewController {
        return self.storyboard.instantiateControllerWithIdentifier("Processing")
            as! ProcessingViewController
    }

    var feedMeViewController: FeedMeViewController {
        return self.storyboard.instantiateControllerWithIdentifier("FeedMe")
            as! FeedMeViewController
    }
}