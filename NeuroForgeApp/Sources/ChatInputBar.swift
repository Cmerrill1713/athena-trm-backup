import SwiftUI

#if canImport(UIKit)
import UIKit
#endif

/// A polished, focus-aware chat input bar - PURE SwiftUI workaround for macOS bug
public struct ChatInputBar: View {
    @Binding public var text: String
    public var onSend: (String) -> Void
    public var isSending: Bool = false
    public var focusTrigger: Bool = false

    @FocusState private var isFocused: Bool

    public init(text: Binding<String>, onSend: @escaping (String) -> Void, isSending: Bool = false, focusTrigger: Bool = false)
    {
        _text = text
        self.onSend = onSend
        self.isSending = isSending
        self.focusTrigger = focusTrigger
    }

    // MARK: - Known-Good Input Test (for debugging)
    /// Drop this in your detail view to test if basic input works
    static func knownGoodInput() -> some View {
        struct KnownGoodInput: View {
            @State private var text = ""
            @FocusState private var focused: Bool

            var body: some View {
                VStack {
                    Spacer()
                    TextField("Type here…", text: $text, axis: .vertical)
                        .focused($focused)
                        .textFieldStyle(.roundedBorder)
                        .padding()
                        .background(Color(nsColor: .textBackgroundColor))
                        .safeAreaInset(edge: .bottom) { Color.clear.frame(height: 0) }
                        .onAppear {
                            // Give layout a tick before focusing
                            DispatchQueue.main.async { focused = true }
                        }
                }
                .ignoresSafeArea(.keyboard, edges: .bottom)
            }
        }
        return KnownGoodInput()
    }

    public var body: some View {
        HStack(spacing: 12) {
            // MARK: - Hit Testing Debug (uncomment to test)
            // .modifier(HitTestProbe())

            // MARK: - UIKit Fallback (Guaranteed Focus) - Uncomment if SwiftUI fails
            /*
            FirstResponderField(text: $text) {
                submit()
            }
            .frame(maxWidth: .infinity)
            .padding(12)
            .background(Color(NSColor.textBackgroundColor))
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isFocused ? Color.accentColor : Color.gray.opacity(0.3), lineWidth: 1.5)
            )
            */

            // MARK: - SwiftUI TextField (Primary Implementation)
                TextField("Type a message...", text: $text, axis: .vertical)
                    .textFieldStyle(.plain)
                    .font(.body)
                    .padding(12)
                    .frame(minHeight: 44, maxHeight: 140)
                    .background(Color(NSColor.textBackgroundColor))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(
                                isFocused ? Color.accentColor : Color.gray.opacity(0.3),
                                lineWidth: 1.5)
                    )
                    .focused($isFocused)
                    .disabled(isSending)
                    .onChange(of: focusTrigger) { _, _ in
                        // External focus trigger (e.g., from NavigationSplitView)
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                            isFocused = true
                        }
                    }
                // MARK: - Enhanced Focus Management for NavigationSplitView
                .onAppear {
                    // Multiple focus attempts for NavigationSplitView compatibility
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                        isFocused = true
                    }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                        if !isFocused { isFocused = true }
                    }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) {
                        if !isFocused { isFocused = true }
                    }
                }
                .onSubmit {
                    submit()
                    // Keep focus after submit
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                        isFocused = true
                    }
                }
                // MARK: - Keyboard and Safe Area Fixes
                .ignoresSafeArea(.keyboard, edges: .bottom)
                .safeAreaInset(edge: .bottom) { Color.clear.frame(height: 0) }
                // MARK: - TextField Enhancements
                .textInputAutocapitalization(.sentences)
                .disableAutocorrection(false)
                .scrollDismissesKeyboard(.interactively)
                    // MARK: - Stable Identity for NavigationSplitView (CRITICAL)
                    .id("chat-input-stable")
                    .zIndex(1)

            Button(action: submit) {
                Image(systemName: isSending ? "hourglass" : "paperplane.fill")
                    .imageScale(.medium)
                    .foregroundColor(isSending ? .gray : .accentColor)
            }
            .buttonStyle(.plain)
            .keyboardShortcut(.return, modifiers: [.command])  // ⌘↩ to send
            .disabled(isSending || text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            .help(isSending ? "Sending..." : "Send (⌘↩)")
            .zIndex(2)
        }
        .padding(8)
        .background(.thinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        // MARK: - Safe Area and Keyboard Fixes
        .ignoresSafeArea(.keyboard, edges: .bottom)
        .safeAreaInset(edge: .bottom) { Color.clear.frame(height: 0) }
        // MARK: - Hit Testing - ensure the entire area is hittable
        .contentShape(Rectangle())
        .allowsHitTesting(true)
        .zIndex(10)  // Ensure it's above other content
    }

    private func submit() {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty, !isSending else { return }

        onSend(trimmed)
        text = ""

        // Restore focus after send - workaround for macOS bug
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            isFocused = true
        }
    }
}

// MARK: - Hit Testing Debug Modifier
/// Uncomment the .modifier(HitTestProbe()) line in the body to visualize hit testing
struct HitTestProbe: ViewModifier {
    func body(content: Content) -> some View {
        content
            .overlay(
                Rectangle().strokeBorder(.red, lineWidth: 1)
                    .allowsHitTesting(false)
            )
            .background(
                Color.clear.onTapGesture {
                    print("✅ Parent container tapped - hit testing working")
                }
            )
    }
}

// MARK: - UIKit Fallback (Guaranteed Focus)
/// UIKit-based TextField that guarantees focus - use if SwiftUI fails
#if canImport(UIKit)
struct FirstResponderField: UIViewRepresentable {
    @Binding var text: String
    var onReturn: () -> Void = {}

    func makeUIView(context: Context) -> UITextField {
        let tf = UITextField(frame: .zero)
        tf.borderStyle = .roundedRect
        tf.font = .systemFont(ofSize: 14)
        tf.delegate = context.coordinator
        tf.setContentCompressionResistancePriority(.required, for: .vertical)
        tf.placeholder = "Type a message..."
        return tf
    }

    func updateUIView(_ uiView: UITextField, context: Context) {
        if uiView.text != text { uiView.text = text }
        if uiView.window != nil, !uiView.isFirstResponder {
            DispatchQueue.main.async { uiView.becomeFirstResponder() }
        }
    }

    func makeCoordinator() -> Coord { Coord(self) }
    final class Coord: NSObject, UITextFieldDelegate {
        var parent: FirstResponderField
        init(_ parent: FirstResponderField) { self.parent = parent }
        func textFieldDidChangeSelection(_ tf: UITextField) { parent.text = tf.text ?? "" }
        func textFieldShouldReturn(_ tf: UITextField) -> Bool {
            parent.onReturn()
            return true
        }
    }
}
#endif

// MARK: - Preview

#Preview("Chat Input Bar") {
    VStack {
        Spacer()

        ChatInputBar(
            text: .constant("Type a message..."),
            onSend: { message in
                print("Sent: \(message)")
            }
        )
        .padding()
    }
    .frame(width: 600, height: 400)
}

#Preview("Chat Input Bar - Sending") {
    VStack {
        Spacer()

        ChatInputBar(
            text: .constant("Sending message..."),
            onSend: { _ in },
            isSending: true
        )
        .padding()
    }
    .frame(width: 600, height: 400)
}
