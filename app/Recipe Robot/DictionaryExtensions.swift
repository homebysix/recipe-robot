//
//  DictionaryExtensions.swift
//
//  Recipe Robot
//  Copyright 2015-2020 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
//

import Foundation

// MARK: - Dictionary
extension Dictionary {
    mutating func update(other: Dictionary) {
        for (key, value) in other {
            self.updateValue(value, forKey: key)
        }
    }
}
