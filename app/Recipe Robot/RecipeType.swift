//
//  RecipeType.swift
//  Recipe Robot
//
//  Created by Eldon on 11/3/15.
//  Copyright © 2015 Linde Group. All rights reserved.
//

import Foundation

enum RecipeType: Int {
    case Download, Munki, Pkg, Install, JSS, AbsoluteManage, SCCM, DS, Filewave

    var value: String {
        switch self {
        case Download: return "download"
        case Munki: return "munki"
        case Pkg: return "pkg"
        case Install: return "install"
        case JSS: return "jss"
        case AbsoluteManage: return "absolute"
        case SCCM: return "sccm"
        case DS: return "ds"
        case Filewave: return "filewave"
        }
    }

    var requiredTypes: [RecipeType] {
        var types = Set([self])
        switch self {
        case Munki, Pkg, Install, Filewave:
            // Requires Download
            types.unionInPlace([Download])
        case JSS, AbsoluteManage, SCCM, DS:
            // Requires Package (inherits Download)
            types.unionInPlace([Pkg])
        default:
            break
        }

        for i in types where i != self {
            types.unionInPlace(i.requiredTypes)
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
            idx++
        }
        return cases
    }
}