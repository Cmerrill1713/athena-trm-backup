import AppKit

/// Keyboard event monitor - proves keys reach the window
enum AppKeyboardProbe {
    static func install() {
        #if os(macOS)
        NSEvent.addLocalMonitorForEvents(matching: [.keyDown]) { ev in
            print("🔑 keyDown in app: \(ev.charactersIgnoringModifiers ?? "?")  mods:\(ev.modifierFlags.rawValue)")
            return ev
        }
        print("🔍 Keyboard probe installed - will log every keyDown event")
        #endif
    }
}

