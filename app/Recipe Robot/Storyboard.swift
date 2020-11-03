//
//  Storyboard.swift
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

struct MainStoryboard {

    private let storyboard = NSStoryboard(name: "Main", bundle: Bundle.main)

    var preferenceViewController: PreferenceViewController {
        return self.storyboard.instantiateController(withIdentifier: "Preferences")
            as! PreferenceViewController
    }

    var processingViewController: ProcessingViewController {
        return self.storyboard.instantiateController(withIdentifier: "Processing")
            as! ProcessingViewController
    }

    var feedMeViewController: FeedMeViewController {
        return self.storyboard.instantiateController(withIdentifier: "FeedMe")
            as! FeedMeViewController
    }
}
