//
//  DictionaryExtensions.swift
//  Recipe Robot
//
//  Created by Eldon on 11/2/15.
//  Copyright © 2015 Linde Group. All rights reserved.
//

import Foundation

// MARK: - Dictionary
extension Dictionary {
    mutating func update(other:Dictionary) {
        for (key,value) in other {
            self.updateValue(value, forKey:key)
        }
    }
}