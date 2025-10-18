import SwiftUI

// Global notification for Cmd+Enter send
extension Notification.Name { 
    static let nf_sendMessage = Notification.Name("nf_sendMessage") 
}

@main
struct NeuroForgeApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject private var athenaState = AthenaState()
    @StateObject private var profileManager = ProfileManager()
    @StateObject private var focusCoordinator = InputFocusCoordinator()
    @State private var voice = VoiceManager()

    init() {
        #if os(macOS)
        // Install keyboard event monitor (diagnostic)
        AppKeyboardProbe.install()
        NSApp.activate(ignoringOtherApps: true)
        print("🚀 App activating, keyboard probe installed")
        #endif
        
        // Initialize avatar services (only if available - prevents CLI crashes)
        _ = AvatarNotificationService.shared
        // _ = MobileMetricsService.shared  // TODO: Add when metrics service available
    }

    var body: some Scene {
        // Main chat window
        WindowGroup(
            id: "main-window",
            content: {
                if let profile = profileManager.currentProfile {
                    ContentView(profile: profile)
                        .environmentObject(athenaState)
                        .environmentObject(profileManager)
                        .onAppear {
                            #if os(macOS)
                            // Activate app and make window key on launch (bulletproof)
                            NSApp.activate(ignoringOtherApps: true)
                            if let w = NSApp.windows.first { 
                                w.makeKeyAndOrderFront(nil) 
                            }
                            // Prevent background NSPanel or sheet from stealing first responder
                            NSApp.windows.forEach { $0.preventsApplicationTerminationWhenModal = false }
                            #endif
                        }
                        .onReceive(NotificationCenter.default.publisher(for: .ShowCriticalAlert)) {
                            note in
                            if let a = note.object as? CriticalAlert {
                                voice.speak("Critical alert: \(a.title)")
                                openWindow(id: "critical-alert")
                            }
                        }
                        .onReceive(NotificationCenter.default.publisher(for: .ShowTribunalDecision))
                    { note in
                        if let c = note.object as? TribunalCase {
                            voice.speak("Tribunal decision required for case \(c.caseID)")
                            openWindow(id: "tribunal-decision")
                        }
                    }
                        .onReceive(NotificationCenter.default.publisher(for: .ShowSystemEmergency))
                    { note in
                        if let e = note.object as? SystemEmergency {
                            voice.speak("System emergency: \(e.title)")
                            openWindow(id: "system-emergency")
                        }
                    }
                } else {
                    // Profile creation view (simplified - profile manager creates default)
                    VStack {
                        Text("Loading profile...")
                            .font(.title)
                    }
                    .frame(minWidth: 600, minHeight: 400)
                    .onAppear {
                        // ProfileManager creates default profile in init
                    }
                }
            }
        )
        .handlesExternalEvents(matching: Set(["*"]))
        .commands {
            CommandGroup(replacing: .newItem) {}
            
            // Global Cmd+Enter send shortcut
            CommandGroup(after: .textEditing) {
                Button("Send Message") {
                    NotificationCenter.default.post(name: .nf_sendMessage, object: nil)
                }
                .keyboardShortcut(.return, modifiers: [.command])
            }

            // Athena focus commands
            CommandMenu("Athena") {
                Button("Refocus Input") {
                    focusCoordinator.requestFocus()
                    NSApp.windows
                        .first { $0.identifier?.rawValue == "main-window" }?
                        .makeKeyAndOrderFront(nil)
                }
                .keyboardShortcut("l", modifiers: [.command, .shift])
            }
        }

        // Athena Dashboard window (Cmd+Shift+A)
        Window("Athena Dashboard", id: "athena-dashboard") {
            AthenaDashboardView()
                .environmentObject(athenaState)
                .frame(minWidth: 800, minHeight: 500)
        }
        .keyboardShortcut("a", modifiers: [.command, .shift])

        // Pop-out windows (triggered programmatically)
        Window("🚨 Critical Alert", id: "critical-alert") {
            if let a = athenaState.lastAlert {
                CriticalAlertWindow(alert: a)
            } else {
                Text("No alert").padding()
            }
        }
        .defaultPosition(.center)

        Window("⚖️ Tribunal Decision Required", id: "tribunal-decision") {
            if let c = athenaState.lastCase {
                TribunalDecisionWindow(case: c)
            } else {
                Text("No case").padding()
            }
        }
        .defaultPosition(.center)

        Window("🚨 SYSTEM EMERGENCY", id: "system-emergency") {
            if let e = athenaState.lastEmergency {
                SystemEmergencyWindow(emergency: e)
            } else {
                Text("No emergency").padding()
            }
        }
        .defaultPosition(.center)
    }

    private func openWindow(id: String) {
        #if canImport(AppKit)
            if let w = NSApp.windows.first(where: { $0.identifier?.rawValue == id }) {
                // Configure pop-out to not steal focus from main window
                configureNonStealingWindow(w)
            }
        #endif
    }
}
