import SwiftUI

struct ChatInputView: View {
    @EnvironmentObject var focus: InputFocusCoordinator
    @FocusState private var isFocused: Bool
    @State private var text: String = ""

    var onSend: (String) -> Void

    var body: some View {
        VStack(spacing: 8) {
            TextEditor(text: $text)
                .font(.body)
                .padding(10)
                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))
                .focused($isFocused)
                .onChange(of: isFocused) { _, now in
                    now ? focus.beginTextEntry() : focus.endTextEntry()
                }
                .onAppear {
                    // Defer one runloop so view is in window hierarchy
                    DispatchQueue.main.async { isFocused = true }
                }
                .onReceive(
                    NotificationCenter.default.publisher(
                        for: NSApplication.didBecomeActiveNotification)
                ) { _ in
                    // If app regains focus, restore chat focus
                    if focus.chatInputFocused { isFocused = true }
                }

            HStack {
                Spacer()
                Button(action: send) {
                    Label("Send", systemImage: "paperplane.fill")
                }
                .keyboardShortcut(.return, modifiers: [.command])
            }
        }
        .onAppear { focus.beginTextEntry() }
        .onDisappear { focus.endTextEntry() }
        // Global "focus chat" shortcut
        .onExitCommand {} // prevent accidental focus loss on ESC
        .onReceive(
            NotificationCenter.default.publisher(for: NSApplication.didBecomeActiveNotification)
        ) { _ in
            if focus.chatInputFocused { isFocused = true }
        }
        .background(
            // ⌘K focuses input from anywhere
            FocusHotkey(
                isFocused: Binding(
                    get: { isFocused },
                    set: { isFocused = $0 }
                ))
        )
    }

    private func send() {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        onSend(trimmed)
        text = ""
        isFocused = true
    }
}

/// Local view that registers a keyboard shortcut to focus the editor
private struct FocusHotkey: NSViewRepresentable {
    @Binding var isFocused: Bool
    func makeNSView(context _: Context) -> NSView {
        let v = NSView()
        let cmdK = NSEvent.ModifierFlags.command
        NSEvent.addLocalMonitorForEvents(matching: .keyDown) { ev in
            if ev.modifierFlags.contains(cmdK), ev.charactersIgnoringModifiers == "k" {
                DispatchQueue.main.async { isFocused = true }
                return nil // don't bubble; we handled it
            }
            return ev
        }
        return v
    }

    func updateNSView(_: NSView, context _: Context) {}
}
