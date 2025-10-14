import SwiftUI
import AppKit

final class KeyCatchingNSTextView: NSTextView {
    var onSubmit: (() -> Void)?
    override func becomeFirstResponder() -> Bool {
        // Bulletproof visibility
        self.textColor = .labelColor
        self.backgroundColor = .textBackgroundColor
        self.insertionPointColor = .labelColor
        typingAttributes[.foregroundColor] = NSColor.labelColor
        return super.becomeFirstResponder()
    }
    override func keyDown(with event: NSEvent) { interpretKeyEvents([event]) }
    override func doCommand(by selector: Selector) {
        switch selector {
        case #selector(insertNewline(_:)),
             #selector(NSResponder.insertNewlineIgnoringFieldEditor(_:)):
            onSubmit?()                  // ENTER → send
        case #selector(insertLineBreak(_:)):
            super.doCommand(by: selector) // SHIFT+ENTER → newline
        default:
            super.doCommand(by: selector)
        }
    }
}

struct KeyCatchingTextView: NSViewRepresentable {
    @Binding var text: String
    var onSubmit: () -> Void

    func makeNSView(context: Context) -> NSScrollView {
        let tv = KeyCatchingNSTextView()
        tv.isRichText = false
        tv.isAutomaticQuoteSubstitutionEnabled = false
        tv.isAutomaticDashSubstitutionEnabled = false
        tv.font = .monospacedSystemFont(ofSize: 13, weight: .regular)
        tv.onSubmit = onSubmit
        tv.string = text
        tv.textColor = .labelColor
        tv.backgroundColor = .textBackgroundColor
        let scroll = NSScrollView()
        scroll.documentView = tv
        return scroll
    }
    func updateNSView(_ view: NSScrollView, context: Context) {
        (view.documentView as? NSTextView)?.string = text
    }
}
