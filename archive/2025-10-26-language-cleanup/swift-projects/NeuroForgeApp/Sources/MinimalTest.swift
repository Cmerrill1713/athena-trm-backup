import SwiftUI

/// ABSOLUTE MINIMAL TEST - If this doesn't work, it's a system/permissions issue
struct MinimalTestApp: View {
    @State private var text = ""
    @FocusState private var focused: Bool

    var body: some View {
        VStack(spacing: 30) {
            Text("MINIMAL KEYBOARD TEST")
                .font(.title)

            Text("If buttons work but typing doesn't → System permissions issue")
                .foregroundColor(.orange)

            // Test 1: Button (should always work)
            Button("Test: Click Me") {
                text += "BUTTON WORKS! "
                print("✅ Button clicked - GUI events work")
            }
            .buttonStyle(.borderedProminent)

            // Test 2: TextField (the problem)
            TextField("Type here", text: $text)
                .textFieldStyle(.roundedBorder)
                .font(.system(size: 20))
                .padding()
                .focused($focused)
                .onAppear {
                    print("🔧 TextField appeared")
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                        focused = true
                        print("🔧 Focus set to: \(focused)")
                    }
                }
                .onChange(of: text) { old, new in
                    print("✅ TEXT CHANGED: '\(old)' → '\(new)'")
                }
                .onChange(of: focused) { old, new in
                    print("🔧 FOCUS CHANGED: \(old) → \(new)")
                }

            Text("Text: \"\(text)\"")
                .foregroundColor(.secondary)

            Text("Focused: \(focused ? "✅ YES" : "❌ NO")")
                .foregroundColor(focused ? .green : .red)

            Divider()

            // Test 3: Known-good input pattern (from ChatInputBar)
            VStack(alignment: .leading, spacing: 8) {
                Text("TEST 3: Known-Good Pattern")
                    .font(.headline)
                    .foregroundColor(.blue)

                ChatInputBar.knownGoodInput()
                    .frame(height: 100)
            }

            Divider()

            VStack(alignment: .leading, spacing: 8) {
                Text("DEBUG INFO:")
                    .font(.headline)
                Text("• If button works: GUI OK")
                Text("• If focus = YES but can't type: Keyboard routing issue")
                Text("• If focus = NO: Focus issue")
                Text("• Check Console.app for 🔧 debug logs")
                Text("• Known-good pattern should work if basic SwiftUI input works")
            }
            .font(.caption)
            .foregroundColor(.secondary)
        }
        .padding(40)
        .frame(width: 600, height: 500)
        .onAppear {
            print("🔧 ========================================")
            print("🔧 MinimalTestApp appeared")
            print("🔧 NSApp.isActive: \(NSApp.isActive)")
            print("🔧 Window key: \(NSApp.keyWindow != nil)")
            print("🔧 ========================================")

            // Make absolutely sure window is key
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                NSApp.activate(ignoringOtherApps: true)
                NSApp.keyWindow?.makeKey()
                print("🔧 Forced app to front")
            }
        }
    }
}

#Preview {
    MinimalTestApp()
}
