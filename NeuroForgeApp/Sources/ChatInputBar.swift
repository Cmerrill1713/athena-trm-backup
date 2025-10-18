import SwiftUI

/// Bulletproof chat input using AppKit-backed field
/// No focus loss, no keystroke drops, rock-solid on macOS
public struct ChatInputBar: View {
    @ObservedObject var vm: ChatInputVM

    public init(vm: ChatInputVM) {
        self.vm = vm
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
            #if os(macOS)
            // AppKit-backed field - bulletproof first responder
            StickyTextField(vm: vm, placeholder: "Type a message…")
                .frame(minHeight: 28)
            #else
            // iOS fallback
            TextField("Type a message…", text: $vm.text)
                .textFieldStyle(.roundedBorder)
                .onSubmit { vm.submit() }
            #endif

            Button {
                vm.submit()
            } label: {
                if vm.isSending { 
                    ProgressView()
                        .controlSize(.small) 
                } else { 
                    Text("Send") 
                }
            }
            .keyboardShortcut(.return, modifiers: [.command])  // Cmd+Enter
            .disabled(false)  // Never disable!
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(.thinMaterial)
        .animation(.easeInOut(duration: 0.15), value: vm.isSending)
        .allowsHitTesting(true)
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
    struct PreviewWrapper: View {
        @StateObject private var vm = ChatInputVM()
        
        var body: some View {
            VStack {
                Spacer()
                ChatInputBar(vm: vm)
                    .onAppear {
                        vm.onSend = { text in
                            print("Sent: \(text)")
                        }
                    }
                    .padding()
            }
            .frame(width: 600, height: 400)
        }
    }
    return PreviewWrapper()
}

#Preview("Chat Input Bar - Sending") {
    struct PreviewWrapper: View {
        @StateObject private var vm = ChatInputVM()
        
        var body: some View {
            VStack {
                Spacer()
                ChatInputBar(vm: vm)
                    .onAppear {
                        vm.isSending = true
                        vm.onSend = { _ in }
                    }
                    .padding()
            }
            .frame(width: 600, height: 400)
        }
    }
    return PreviewWrapper()
}
