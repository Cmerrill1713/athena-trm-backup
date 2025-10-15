import AppKit
import SwiftUI

/// Bulletproof non-stealing pop-out window configuration
/// Prevents pop-outs from stealing keyboard focus from main window
@MainActor
func configureNonStealingWindow(_ window: NSWindow) {
    // Store current key window to restore later
    let previousKeyWindow = NSApp.keyWindow

    // Never become key/main automatically
    window.isReleasedWhenClosed = false
    window.hidesOnDeactivate = false
    window.collectionBehavior = [.transient, .ignoresCycle]
    window.level = .floating
    window.isOpaque = false
    window.hasShadow = true

    // Make it a non-activating panel (if it's an NSPanel)
    if let panel = window as? NSPanel {
        panel.isFloatingPanel = true
        panel.becomesKeyOnlyIfNeeded = true
        panel.worksWhenModal = true
        panel.hidesOnDeactivate = false
    }

    // Show without activating
    window.orderFrontRegardless()

    // Restore focus to previous key window
    if let prev = previousKeyWindow {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.12) {
            prev.makeKeyAndOrderFront(nil)
            prev.makeFirstResponder(nil)
        }
    }
}

/// Window accessor extension for easier pop-out configuration
extension NSWindow {
    /// Configure this window as a non-stealing pop-out
    func configureAsNonStealingPopout() {
        configureNonStealingWindow(self)
    }
}
