import SwiftUI

struct ChatInputView: View {
    @EnvironmentObject var focus: InputFocusCoordinator
    @FocusState private var isFocused: Bool
    @State private var text: String = ""

    var onSend: (String) -> Void

    var body: some View {
        VStack(spacing: 8) {
            TextEditor(text: self.$text)
                .font(.body)
                .padding(10)
                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))
                .focused(self.$isFocused)
                .onChange(of: self.isFocused) { now in
                    now ? self.focus.beginTextEntry() : self.focus.endTextEntry()
                }
                .onAppear {
                    // Defer one runloop so view is in window hierarchy
                    DispatchQueue.main.async { self.isFocused = true }
                }
                .onReceive(NotificationCenter.default.publisher(for: NSApplication.didBecomeActiveNotification)) { _ in
                    // If app regains focus, restore chat focus
                    if self.focus.chatInputFocused { self.isFocused = true }
                }

            HStack {
                Spacer()
                Button(action: self.send) {
                    Label("Send", systemImage: "paperplane.fill")
                }
                .keyboardShortcut(.return, modifiers: [.command])
            }
        }
        .onAppear { self.focus.beginTextEntry() }
        .onDisappear { self.focus.endTextEntry() }
        // Global "focus chat" shortcut
        .onExitCommand {} // prevent accidental focus loss on ESC
        .onReceive(
            NotificationCenter.default.publisher(for: NSApplication.didBecomeActiveNotification)
        ) { _ in
            if self.focus.chatInputFocused { self.isFocused = true }
        }
        .background(
            // ⌘K focuses input from anywhere
            FocusHotkey(isFocused: Binding(
                get: { self.isFocused },
                set: { self.isFocused = $0 }
            ))
        )
    }

    private func send() {
        let trimmed = self.text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        self.onSend(trimmed)
        self.text = ""
        self.isFocused = true
    }
}

/// Local view that registers a keyboard shortcut to focus the editor
private struct FocusHotkey: NSViewRepresentable {
    @Binding var isFocused: Bool
    func makeNSView(context: Context) -> NSView {
        let v = NSView()
        let cmdK = NSEvent.ModifierFlags.command
        NSEvent.addLocalMonitorForEvents(matching: .keyDown) { ev in
            if ev.modifierFlags.contains(cmdK), ev.charactersIgnoringModifiers == "k" {
                DispatchQueue.main.async { self.isFocused = true }
                return nil // don't bubble; we handled it
            }
            return ev
        }
        return v
    }

    func updateNSView(_ nsView: NSView, context: Context) {}
}
