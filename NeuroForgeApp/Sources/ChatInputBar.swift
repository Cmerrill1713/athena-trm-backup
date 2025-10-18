import OSLog
import SwiftUI

#if canImport(UIKit)
    import UIKit
#endif

/// A polished, focus-aware chat input bar - PRODUCTION-READY with all fixes applied
public struct ChatInputBar: View {
    @Binding public var text: String
    public var onSend: (String) -> Void
    public var isSending: Bool = false
    public var focusTrigger: Bool = false  // For external focus control

    @FocusState private var isFocused: Bool
    @State private var stableId = UUID()  // Keep identity stable across rebuilds

    // UI logging for debugging
    private let uiLog = Logger(subsystem: "com.neuroforge.athena", category: "ui")

    public init(
        text: Binding<String>, onSend: @escaping (String) -> Void, isSending: Bool = false,
        focusTrigger: Bool = false
    ) {
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
        HStack(spacing: 8) {
            // SwiftUI field - NEVER disabled (to keep focus)
            TextField("Type a message…", text: $text)
                .id(stableId)
                .focused($isFocused)
                .textFieldStyle(.roundedBorder)
                .disableAutocorrection(true)
                .onAppear { 
                    isFocused = true
                    uiLog.info("ChatInput appeared, focus set")
                }
                .onReceive(NotificationCenter.default.publisher(for: .nf_sendMessage)) { _ in 
                    submit() 
                }
                .onSubmit { submit() }  // Enter sends
                .onChange(of: focusTrigger) { _, _ in
                    // External focus trigger (e.g., from NavigationSplitView)
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                        isFocused = true
                        uiLog.info("Focus triggered externally")
                    }
                }
                .onChange(of: isSending) { _, newValue in
                    // Re-assert focus when sending completes (critical!)
                    if !newValue {
                        DispatchQueue.main.async {
                            isFocused = true
                            uiLog.info("Send complete, refocusing input")
                        }
                    }
                }
            
            Button("Send") { submit() }
                .buttonStyle(.borderedProminent)
                .keyboardShortcut(.return, modifiers: [.command])
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .overlay(alignment: .trailing) {
            if isSending { 
                ProgressView()
                    .padding(.trailing, 56) 
            }
        }
        // Visual "disabled" without .disabled() - never drops focus!
        .background(isSending ? Color.black.opacity(0.04) : Color.clear)
        .background(.ultraThinMaterial)
    }

    private func submit() {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        uiLog.info("Send tapped; length=\(trimmed.count)")
        onSend(trimmed)
        text.removeAll()
        reclaimFocus()
    }

    private func reclaimFocus() {
        DispatchQueue.main.async {
            // nudge focus without recreating the view
            isFocused = true
            uiLog.info("Send complete; refocusing input")
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
