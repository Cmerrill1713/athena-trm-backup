import SwiftUI

@main
struct NeuroForgeApp: App {

    @StateObject private var prompts = PromptStore()
    @StateObject private var ops = OpsState()  // ← Operations state for monitoring
    @State private var showInspector = false
    @State private var showSidebar = false
    @State private var showTracePanel = false
    @AppStorage("hasCompletedFirstRun") private var hasCompletedFirstRun = false
    @Environment(\.scenePhase) private var scenePhase

    init() {
        // Set the app icon
        AppIcon.setIcon()
    }

    var body: some Scene {
        WindowGroup {
            if hasCompletedFirstRun {
                ChatViewEnhanced() // ✅ Meta-aware + voice + confidence sparkline
                .environmentObject(prompts)
                .environmentObject(ops)  // ← Provide OpsState to main window
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

                    // Silence evolution recommendations in QA mode
                    if ProcessInfo.processInfo.environment["EVO_SUGGESTIONS"] == "0" {
                        UserDefaults.standard.set(true, forKey: "SuppressEvolutionRecommendations")
                    }
                }
            } else {
                FirstRunWizardView(onComplete: {
                    hasCompletedFirstRun = true
                })
            }
        }
        .windowStyle(.hiddenTitleBar)
        .onChange(of: scenePhase) {
            // Reset session counters when app becomes active
            if scenePhase == .active {
                ops.resetSession()
            }
        }

        // Dedicated Trace Panel window
        Window("Trace Panel", id: "trace-panel") {
            TracePanelView()
        }
        .defaultSize(width: 1100, height: 700)
        
        // Operations window (pop-out from chat)
        WindowGroup("Operations", id: "ops") {
            OpsWindow()  // Shows health, meta-prompt confidence, tools, traces
                .environmentObject(ops)
        }
        .defaultSize(width: 720, height: 520)
        .windowStyle(.titleBar)
        
        // Operations settings window
        Window("Operations Settings", id: "ops-settings") {
            OpsSettingsView()
                .environmentObject(ops)
        }
        .defaultSize(width: 450, height: 350)
        .windowResizability(.contentSize)
        
        .commands {
            CommandMenu("Prompts") {
                Button("Toggle Prompt Sidebar") {
                    NotificationCenter.default.post(name: .togglePromptSidebar, object: nil)
                }
                .keyboardShortcut("T", modifiers: [.command, .shift])
            }

            CommandMenu("Tools") {
                Button("Show Operations Window") {
                    // Window opening handled via @Environment(\.openWindow) in views
                    // This menu item provides discoverability
                }
                .keyboardShortcut("o", modifiers: [.command, .option])
                
                Button("Open Trace Panel") {
                    if let window = NSApp.windows.first(where: { $0.identifier?.rawValue == "trace-panel" }) {
                        window.makeKeyAndOrderFront(nil)
                    } else {
                        NSApp.activate(ignoringOtherApps: true)
                    }
                }
                .keyboardShortcut("t", modifiers: [.command, .shift])
            }

            CommandMenu("QA") {
                Button("\(showInspector ? "Hide" : "Show") Provider Inspector") {
                    showInspector.toggle()
                }
                .keyboardShortcut("i", modifiers: [.command, .option])
            }
            
            CommandMenu("Settings") {
                Button("Operations Settings...") {
                    // Settings window opening handled via toolbar/views
                    // This menu item provides discoverability
                }
                .keyboardShortcut(",", modifiers: [.command, .option])
            }
        }
    }
}

// MARK: - Notifications

extension Notification.Name {
    static let togglePromptSidebar = Notification.Name("nf.togglePromptSidebar")
    static let nfInsertPrompt = Notification.Name("nf.insertPrompt")
}
