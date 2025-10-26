import AppKit
import SwiftUI

/// Global "who has the keyboard?" truth.
@MainActor
final class InputFocusCoordinator: ObservableObject {
    @Published var chatInputFocused: Bool = false
    private var localMonitor: Any?

    /// Call when a text input gains focus.
    func beginTextEntry() {
        chatInputFocused = true
        suspendGlobalKeyStealers()
    }

    /// Call when text input resigns.
    func endTextEntry() {
        chatInputFocused = false
        resumeGlobalKeyStealers()
    }

    private func suspendGlobalKeyStealers() {
        // Remove any existing local monitors that might intercept keyDown
        if let m = localMonitor { NSEvent.removeMonitor(m); localMonitor = nil }
        // Install a pass-through monitor that *never* eats events while an NSTextView is first responder
        localMonitor = NSEvent.addLocalMonitorForEvents(matching: [.keyDown, .flagsChanged]) { ev in
            if let first = NSApp.keyWindow?.firstResponder,
               first.isKind(of: NSTextView.self) {
                // Let the text system handle it
                return ev
            }
            // Otherwise, allow normal app shortcuts to work
            return ev
        }
    }

    private func resumeGlobalKeyStealers() {
        if let m = localMonitor { NSEvent.removeMonitor(m); localMonitor = nil }
    }

    /// Request focus programmatically (e.g., from Cmd+Shift+L)
    func requestFocus() {
        chatInputFocused = true
    }
}
