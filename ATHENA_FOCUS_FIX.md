# Athena Focus & Window Behavior Fixes

## Problem
- Can't type in input field after pop-outs appear
- Pop-out windows steal keyboard focus
- Main window doesn't reclaim first responder

## Solution

### 1. Fix Input Focus with @FocusState

Add this to your `ChatInputBar` or main input component:

```swift
import SwiftUI

struct ChatInputBar: View {
    @FocusState private var isFocused: Bool
    @State private var text = ""

    var body: some View {
        HStack {
            TextField("Type a message…", text: $text, axis: .vertical)
                .focused($isFocused)
                .textFieldStyle(.roundedBorder)
                .onAppear { 
                    DispatchQueue.main.async { isFocused = true } 
                }
                .onReceive(NotificationCenter.default.publisher(for: NSApplication.didBecomeActiveNotification)) { _ in
                    // Regain focus when app re-activates or pop-out closes
                    DispatchQueue.main.async { isFocused = true }
                }

            Button("Send") { 
                // Send logic here
            }
            .keyboardShortcut(.return, modifiers: [.command])
        }
        .padding(8)
    }
}
```

### 2. Fix Pop-Out Windows (Don't Steal Focus)

Add this helper function and apply to all pop-out windows:

```swift
import AppKit

func configureNonStealingWindow(_ window: NSWindow) {
    window.level = .floating
    window.collectionBehavior = [.moveToActiveSpace]
    window.hidesOnDeactivate = false
    window.isMovableByWindowBackground = true
    window.isReleasedWhenClosed = true
    window.becomesKeyOnlyIfNeeded = true
    
    window.makeKeyAndOrderFront(nil)
    NSApp.activate(ignoringOtherApps: true)

    // Return focus to main window after 150ms
    DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
        NSApp.windows
            .first { $0.identifier?.rawValue == "main-window" }?
            .makeFirstResponder(nil)
    }
}
```

### 3. Tag Main Window

In your main App struct:

```swift
@main
struct AthenaApp: App {
    var body: some Scene {
        Window("Athena", id: "main-window") {
            AthenaDashboardView()
        }
        
        // ... other windows
    }
}
```

### 4. Add Refocus Keyboard Shortcut

Add this Commands block:

```swift
struct AppCommands: Commands {
    var body: some Commands {
        CommandMenu("Athena") {
            Button("Refocus Input") {
                NSApp.windows
                    .first { $0.identifier?.rawValue == "main-window" }?
                    .makeKeyAndOrderFront(nil)
            }
            .keyboardShortcut("L", modifiers: [.command, .shift])
        }
    }
}
```

Then register it in your App:

```swift
@main
struct AthenaApp: App {
    var body: some Scene {
        // ... windows
    }
    
    var body: some Commands {
        AppCommands()
    }
}
```

### 5. Apply to Pop-Out Windows

In your CriticalAlert, Tribunal, and Emergency pop-out creation code:

```swift
// When creating the pop-out window:
let window = NSWindow(contentViewController: NSHostingController(rootView: yourView))
configureNonStealingWindow(window)
```

## Testing

1. Build and run Athena
2. Type in the main input field
3. Trigger a pop-out (critical alert, tribunal, or emergency)
4. Pop-out should appear but input field should still accept typing
5. If focus is lost, press Cmd+Shift+L to refocus
6. Close pop-out - focus returns automatically

## Keyboard Shortcuts

- **Cmd+Return**: Send message
- **Cmd+Shift+L**: Refocus input field

## Implementation Locations

- **ChatInputBar**: Add `@FocusState` and focus management
- **Pop-out creation**: Apply `configureNonStealingWindow()`
- **Main App**: Tag main window, add AppCommands
- **All three pop-outs**: Critical, Tribunal, Emergency

