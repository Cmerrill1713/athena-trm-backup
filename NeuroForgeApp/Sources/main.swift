import SwiftUI

@main
struct NeuroForgeApp: App {

    @StateObject private var prompts = PromptStore()
    @State private var showInspector = false
    @State private var showSidebar = false
    @AppStorage("hasCompletedFirstRun") private var hasCompletedFirstRun = false

    init() {
        // Set the app icon
        AppIcon.setIcon()
    }

    var body: some Scene {
        WindowGroup {
            if hasCompletedFirstRun {
                ChatView() // uses HealthBanner + model-agnostic routing
                .environmentObject(prompts)
                .overlay(alignment: .leading) {
                    if ProcessInfo.processInfo.environment["QA_MODE"] == "1",
                       showSidebar {
                        PromptSidebar(store: prompts) { text in
                            NotificationCenter.default.post(name: .nfInsertPrompt, object: text)
                        }
                        .transition(.move(edge: .leading).combined(with: .opacity))
                        .zIndex(2)
                    }
                }
                .overlay(alignment: .bottomTrailing) {
                    if showInspector {
                        ProviderInspectorOverlay()
                            .padding(16)
                            .allowsHitTesting(true)
                    }
                }
                .onReceive(NotificationCenter.default.publisher(for: .togglePromptSidebar)) { _ in
                    withAnimation {
                        showSidebar.toggle()
                    }
                }
                .onAppear {
                    prompts.load()

                    #if DEBUG
                    showInspector = true
                    #endif
                    // Also check QA_MODE environment variable
                    if ProcessInfo.processInfo.environment["QA_MODE"] == "1" {
                        showInspector = true
                    }
                }
            } else {
                FirstRunWizardView(onComplete: {
                    hasCompletedFirstRun = true
                })
            }
        }
        .windowStyle(.hiddenTitleBar)
        .commands {
            CommandMenu("Prompts") {
                Button("Toggle Prompt Sidebar") {
                    NotificationCenter.default.post(name: .togglePromptSidebar, object: nil)
                }
                .keyboardShortcut("T", modifiers: [.command, .shift])
            }

            CommandMenu("QA") {
                Button("\(showInspector ? "Hide" : "Show") Provider Inspector") {
                    showInspector.toggle()
                }
                .keyboardShortcut("i", modifiers: [.command, .option])
            }
        }
    }
}

// MARK: - Notifications

extension Notification.Name {
    static let togglePromptSidebar = Notification.Name("nf.togglePromptSidebar")
    static let nfInsertPrompt = Notification.Name("nf.insertPrompt")
}
