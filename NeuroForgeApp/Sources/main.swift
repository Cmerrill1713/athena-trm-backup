import SwiftUI

@main
struct NeuroForgeApp: App {

    @State private var showInspector = false

    init() {
        // Set the app icon
        AppIcon.setIcon()
    }

    var body: some Scene {
        WindowGroup {
            ChatView() // uses HealthBanner + model-agnostic routing
                .overlay(alignment: .bottomTrailing) {
                    if showInspector {
                        ProviderInspectorOverlay()
                            .padding(16)
                            .allowsHitTesting(true)
                    }
                }
                .onAppear {
                    #if DEBUG
                    showInspector = true
                    #endif
                    // Also check QA_MODE environment variable
                    if ProcessInfo.processInfo.environment["QA_MODE"] == "1" {
                        showInspector = true
                    }
                }
        }
        .windowStyle(.hiddenTitleBar)
        .commands {
            CommandMenu("QA") {
                Button("\(showInspector ? "Hide" : "Show") Provider Inspector") {
                    showInspector.toggle()
                }
                .keyboardShortcut("i", modifiers: [.command, .option])
            }
        }
    }
}
