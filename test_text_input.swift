#!/usr/bin/env swift
import SwiftUI
import AppKit

@main
struct TestApp: App {
    var body: some Scene {
        WindowGroup {
            TestView()
        }
    }
}

// KeyCatchingTextEditor (copied from NeuroForgeApp)
struct KeyCatchingTextEditor: NSViewRepresentable {
    @Binding var text: String
    var onSubmit: () -> Void
    var focusOnAppear: Bool = true

    func makeNSView(context: Context) -> NSScrollView {
        let scrollView = NSScrollView()
        let textView = KeyCatchingTextView()

        textView.delegate = context.coordinator
        textView.isRichText = false
        textView.font = .systemFont(ofSize: NSFont.systemFontSize)
        textView.string = text
        textView.onSubmit = onSubmit

        textView.applySafeColorsAndTypingAttributes()

        textView.minSize = NSSize(width: 0, height: 0)
        textView.isVerticallyResizable = true
        textView.isHorizontallyResizable = false
        textView.textContainer?.widthTracksTextView = true

        scrollView.hasVerticalScroller = true
        scrollView.documentView = textView
        scrollView.drawsBackground = true
        scrollView.backgroundColor = .textBackgroundColor

        if focusOnAppear {
            DispatchQueue.main.async {
                scrollView.window?.makeFirstResponder(textView)
                NSApp.activate(ignoringOtherApps: true)
            }
        }

        context.coordinator.textView = textView
        return scrollView
    }

    func updateNSView(_ scrollView: NSScrollView, context: Context) {
        guard let textView = context.coordinator.textView else { return }
        if textView.string != text {
            textView.string = text
            textView.applySafeColorsAndTypingAttributes()
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(parent: self)
    }

    final class Coordinator: NSObject, NSTextViewDelegate {
        let parent: KeyCatchingTextEditor
        weak var textView: KeyCatchingTextView?

        init(parent: KeyCatchingTextEditor) {
            self.parent = parent
        }

        func textDidChange(_ notification: Notification) {
            guard let tv = notification.object as? NSTextView else { return }
            parent.text = tv.string
        }
    }
}

final class KeyCatchingTextView: NSTextView {
    var onSubmit: (() -> Void)?

    func applySafeColorsAndTypingAttributes() {
        usesAdaptiveColorMappingForDarkAppearance = true
        drawsBackground = true

        let fg = NSColor.labelColor
        let bg = NSColor.textBackgroundColor
        let caret = NSColor.controlAccentColor

        backgroundColor = bg
        insertionPointColor = caret
        textColor = fg

        let font = self.font ?? .systemFont(ofSize: 15, weight: .regular)
        let typing: [NSAttributedString.Key: Any] = [
            .foregroundColor: fg,
            .font: font,
            .backgroundColor: NSColor.clear
        ]
        typingAttributes = typing

        if let storage = textStorage {
            let full = NSRange(location: 0, length: storage.length)
            storage.beginEditing()
            storage.removeAttribute(.foregroundColor, range: full)
            storage.removeAttribute(.font, range: full)
            storage.addAttributes(typing, range: full)
            storage.endEditing()
        }
    }

    override var string: String {
        didSet {
            applySafeColorsAndTypingAttributes()
        }
    }

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        applySafeColorsAndTypingAttributes()
    }

    override func viewDidChangeEffectiveAppearance() {
        super.viewDidChangeEffectiveAppearance()
        applySafeColorsAndTypingAttributes()
    }

    override var acceptsFirstResponder: Bool { true }

    override func keyDown(with event: NSEvent) {
        interpretKeyEvents([event])
    }

    override func doCommand(by selector: Selector) {
        switch selector {
        case #selector(insertNewline(_:)),
             #selector(NSResponder.insertNewlineIgnoringFieldEditor(_:)):
            onSubmit?()

        case #selector(insertLineBreak(_:)):
            super.doCommand(by: selector)

        default:
            super.doCommand(by: selector)
        }
    }
}

// Simple test to verify text input works
struct TestView: View {
    @State private var text = ""

    var body: some View {
        VStack {
            Text("Text Input Test")
                .font(.title)
            Text("Type below:")

            KeyCatchingTextEditor(text: $text, onSubmit: {
                print("Submitted: \(text)")
            }, focusOnAppear: true)
            .frame(height: 100)
            .border(Color.blue)

            Text("Current text: '\(text)'")
                .padding()

            Button("Print to Console") {
                print("Current text: \(text)")
            }
        }
        .padding()
        .frame(width: 400, height: 300)
    }
}
