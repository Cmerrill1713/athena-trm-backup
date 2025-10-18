import SwiftUI

#if os(macOS)
/// Nuclear-reliable AppKit-backed multiline input for macOS
/// Enter sends, Shift+Enter = newline
/// Use this if TextField focus is still flaky
struct MultilineChatInput: NSViewRepresentable {
    final class Coordinator: NSObject, NSTextViewDelegate {
        var onSend: (String) -> Void
        
        init(onSend: @escaping (String) -> Void) { 
            self.onSend = onSend 
        }
        
        func textView(_ tv: NSTextView, doCommandBy sel: Selector) -> Bool {
            let enter = sel == #selector(NSResponder.insertNewline(_:))
            let shifted = NSEvent.modifierFlags.contains(.shift)
            
            if enter && !shifted {
                let msg = tv.string.trimmingCharacters(in: .whitespacesAndNewlines)
                if !msg.isEmpty { 
                    onSend(msg)
                    tv.string = "" 
                }
                return true  // Swallow Enter
            }
            return false
        }
    }
    
    var onSend: (String) -> Void
    
    func makeCoordinator() -> Coordinator { 
        .init(onSend: onSend) 
    }
    
    func makeNSView(context: Context) -> NSScrollView {
        let scroll = NSTextView.scrollableTextView()
        let tv = scroll.documentView as! NSTextView
        tv.delegate = context.coordinator
        tv.isRichText = false
        tv.font = .monospacedSystemFont(ofSize: 13, weight: .regular)
        tv.usesAdaptiveColorMappingForDarkAppearance = true
        tv.drawsBackground = true
        tv.backgroundColor = NSColor.textBackgroundColor
        
        // Immediately become first responder
        DispatchQueue.main.async {
            tv.window?.makeFirstResponder(tv)
        }
        
        return scroll
    }
    
    func updateNSView(_ nsView: NSScrollView, context: Context) {
        // Maintain first responder status
        if let tv = nsView.documentView as? NSTextView {
            if tv.window != nil, tv.window?.firstResponder != tv {
                DispatchQueue.main.async {
                    tv.window?.makeFirstResponder(tv)
                }
            }
        }
    }
}

// MARK: - Usage Example (if TextField is still flaky)

/*
 Replace ChatInputBar TextField with:
 
 MultilineChatInput { text in
     Task {
         await chatService.sendMessage(text)
     }
 }
 .frame(minHeight: 40)
 .background(.ultraThinMaterial)
 
 Benefits:
 - Enter sends (Shift+Enter for newline)
 - Guaranteed first responder
 - No SwiftUI focus quirks
 - Multiline support built-in
*/

#endif

