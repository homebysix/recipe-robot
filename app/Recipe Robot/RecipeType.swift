//
//  RecipeType.swift
//
//  Recipe Robot
//  Copyright 2015-2018 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
//

import Foundation

enum RecipeType: Int {
    case Download, Munki, Pkg, Install, JSS, LANrev, SCCM, DS, Filewave, BigFix

    var value: String {
        switch self {
        case .Download: return "download"
        case .Munki: return "munki"
        case .Pkg: return "pkg"
        case .Install: return "install"
        case .JSS: return "jss"
        case .LANrev: return "lanrev"
        case .SCCM: return "sccm"
        case .DS: return "ds"
        case .Filewave: return "filewave"
        case .BigFix: return "bigfix"
        }
    }

    var requiredTypes: [RecipeType] {
        var types = Set([self])
        switch self {
        case .Munki, .Pkg, .Install, .Filewave, .BigFix:
            // Requires Download
            types = types.union([.Download])
        case .JSS, .LANrev, .SCCM, .DS:
            // Requires Package (inherits Download)
            types = types.union([.Pkg])
        default:
            break
        }

        for i in types where i != self {
            types = types.union(i.requiredTypes)
        }
        return Array(types)
    }

    var requiredTypeValues: [String] {
        return self.requiredTypes.map({ return $0.value })
    }

    static var values: [String] {
        return self.cases.map({ return $0.value })
    }

    static var cases:[RecipeType] {
        var cases = [RecipeType]()
        var idx = 0
        while let type = RecipeType(rawValue: idx){
            cases.append(type)
            idx += 1
        }
        return cases
    }
}
