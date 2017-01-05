//
//  ChainableTextControl.swift
//
//  Recipe Robot
//  Copyright 2015-2017 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
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
//

import Foundation
import ObjectiveC

typealias completionClosureType = (Void) -> (Void)

protocol ChainableTextControl {
    func stringChanged(changed:((Self) -> (Void))) -> Self
    func editingEnded(ended: completionClosureType) -> Self
    func editingStarted(began: completionClosureType) -> Self

}

/// Closure wrapper used to hold properties in NSObject extensions.
private class ObservationClosure {
    var beginEditingClosure: completionClosureType?
    var changeClosure: ((NSTextField) -> (Void))?
    var endEditingClosure: completionClosureType?
}

private var closureWrapperAssociationKey: UInt8 = 0

extension NSTextField: NSTextFieldDelegate, ChainableTextControl {

    private var editingObservationalClosure: ObservationClosure {
        delegate = self
        guard let closure = objc_getAssociatedObject(self, &closureWrapperAssociationKey) as? ObservationClosure else {
            let closure = ObservationClosure()
            objc_setAssociatedObject(self,
                &closureWrapperAssociationKey,
                closure,
                .OBJC_ASSOCIATION_RETAIN)
            return closure
        }
        return closure
    }

    func editingStarted(began: completionClosureType) -> Self {
        editingObservationalClosure.beginEditingClosure = began
        return self
    }

    func stringChanged(changed:((NSTextField) -> (Void))) -> Self {
        editingObservationalClosure.changeClosure = changed
        return self
    }

    func editingEnded(ended: completionClosureType) -> Self {
        editingObservationalClosure.endEditingClosure = ended
        return self
    }

    public override func controlTextDidBeginEditing(notification: NSNotification) {
        if let beginHandle = editingObservationalClosure.beginEditingClosure {
            beginHandle()
        }
    }

    public override func controlTextDidChange(notification: NSNotification) {
        guard let _self = notification.object as? NSTextField else {
            return
        }
        if let changeHandle = editingObservationalClosure.changeClosure {
            changeHandle(_self)
        }
    }

    public override func controlTextDidEndEditing(notification: NSNotification) {
        if let endHandle = editingObservationalClosure.endEditingClosure {
            endHandle()
        }
    }
}
