import SwiftUI

#if os(macOS)
/// AppKit-backed text field that NEVER loses first responder
/// Use this when SwiftUI TextField focus is flaky
public struct StickyTextField: NSViewRepresentable {
    public final class Coordinator: NSObject, NSTextFieldDelegate {
        var vm: ChatInputVM
        
        init(vm: ChatInputVM) { 
            self.vm = vm 
        }
        
        public func controlTextDidChange(_ obj: Notification) {
            guard let tf = obj.object as? NSTextField else { return }
            vm.text = tf.stringValue
        }
        
        // Enter sends (Shift+Enter for future multiline support)
        public func control(_ control: NSControl, textView: NSTextView, doCommandBy commandSelector: Selector) -> Bool {
            if commandSelector == #selector(NSResponder.insertNewline(_:)) &&
               !NSEvent.modifierFlags.contains(.shift) {
                vm.submit()
                return true  // Swallow Enter
            }
            return false
        }
    }

    @ObservedObject var vm: ChatInputVM
    var placeholder: String
    
    public init(vm: ChatInputVM, placeholder: String) {
        self.vm = vm
        self.placeholder = placeholder
    }

    public func makeCoordinator() -> Coordinator { 
        Coordinator(vm: vm) 
    }

    public func makeNSView(context: Context) -> NSTextField {
        let tf = NSTextField()
        tf.placeholderString = placeholder
        tf.isBordered = true
        tf.isBezeled = true
        tf.bezelStyle = .roundedBezel
        tf.font = .systemFont(ofSize: 13)
        tf.lineBreakMode = .byTruncatingTail
        tf.delegate = context.coordinator
        tf.target = context.coordinator
        tf.action = #selector(NSResponder.insertNewline(_:))
        tf.usesSingleLineMode = true
        tf.maximumNumberOfLines = 1
        tf.isEditable = true
        tf.isSelectable = true
        
        // Grab focus once on creation
        DispatchQueue.main.async { 
            tf.window?.makeFirstResponder(tf) 
        }
        
        return tf
    }

    public func updateNSView(_ tf: NSTextField, context: Context) {
        // Don't fight while user is typing: update only if text changed externally
        if tf.stringValue != vm.text { 
            tf.stringValue = vm.text 
        }
        
        // If sending just finished, re-assert first responder
        if !vm.isSending {
            DispatchQueue.main.async {
                if tf.window?.firstResponder !== tf.currentEditor() {
                    tf.window?.makeFirstResponder(tf)
                }
            }
        }
        
        // Never disable: simulate busy via alpha
        tf.alphaValue = vm.isSending ? 0.96 : 1.0
        tf.isEnabled = true  // Always enabled!
    }
}
#endif

