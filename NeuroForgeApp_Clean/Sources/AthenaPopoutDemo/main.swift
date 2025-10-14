import SwiftUI

@main
struct NeuroForgeApp: App {
    @StateObject private var state = AthenaState()
    @State private var voice = VoiceManager()

    var body: some Scene {
        WindowGroup {
            AthenaDashboardView()
                .environmentObject(state)
                .onReceive(NotificationCenter.default.publisher(for: .ShowCriticalAlert)) { note in
                    if let a = note.object as? CriticalAlert {
                        voice.speak("Critical alert: \(a.title)")
                        openWindow(id: "critical-alert")
                    }
                }
                .onReceive(NotificationCenter.default.publisher(for: .ShowTribunalDecision)) { note in
                    if let c = note.object as? TribunalCase {
                        voice.speak("Tribunal decision required for case \(c.caseID)")
                        openWindow(id: "tribunal-decision")
                    }
                }
                .onReceive(NotificationCenter.default.publisher(for: .ShowSystemEmergency)) { note in
                    if let e = note.object as? SystemEmergency {
                        voice.speak("System emergency: \(e.title)")
                        openWindow(id: "system-emergency")
                    }
                }
        }

        Window("🚨 Critical Alert", id: "critical-alert") {
            if let a = state.lastAlert {
                CriticalAlertWindow(alert: a)
            } else {
                Text("No alert").padding()
            }
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)

        Window("⚖️ Tribunal Decision Required", id: "tribunal-decision") {
            if let c = state.lastCase {
                TribunalDecisionWindow(case: c)
            } else {
                Text("No case").padding()
            }
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)

        Window("🚨 SYSTEM EMERGENCY", id: "system-emergency") {
            if let e = state.lastEmergency {
                SystemEmergencyWindow(emergency: e)
            } else {
                Text("No emergency").padding()
            }
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)
    }
    
    // Helper to bring a window forward
    private func openWindow(id: String) {
        #if canImport(AppKit)
        DispatchQueue.main.async {
            if let w = NSApp.windows.first(where: { $0.identifier?.rawValue == id }) {
                NSApp.activate(ignoringOtherApps: true)
                w.makeKeyAndOrderFront(nil)
            }
        }
        #endif
    }
}
