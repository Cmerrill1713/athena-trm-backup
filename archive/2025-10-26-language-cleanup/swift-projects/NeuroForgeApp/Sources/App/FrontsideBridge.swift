import AppKit
import SwiftUI

@MainActor
final class FrontsideBridge: NSObject, ObservableObject {
    static let shared = FrontsideBridge()
    func handle(_ url: URL) {
        guard url.scheme == "athena" else { return }
        let items = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems
        let kind = items?.first(where: { $0.name == "kind" })?.value ?? ""
        switch kind {
        case "critical": NotificationCenter.default.post(name: .ShowCriticalAlert, object: nil)
        case "tribunal": NotificationCenter.default.post(name: .ShowTribunalDecision, object: nil)
        case "emergency": NotificationCenter.default.post(name: .ShowSystemEmergency, object: nil)
        default: break
        }
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_: Notification) {
        // Headless E2E demo mode: auto-show windows, write report, exit
        if ProcessInfo.processInfo.environment["ATHENA_E2E"] == "1" {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                NotificationCenter.default.post(name: .ShowCriticalAlert, object: nil)
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                NotificationCenter.default.post(name: .ShowTribunalDecision, object: nil)
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                NotificationCenter.default.post(name: .ShowSystemEmergency, object: nil)
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 3.5) {
                let payload = ["status": "ok", "shown": ["critical", "tribunal", "emergency"]]
                if let data = try? JSONSerialization.data(withJSONObject: payload, options: [.prettyPrinted]) {
                    let url = URL(fileURLWithPath: NSHomeDirectory()).appendingPathComponent("athena_e2e.json")
                    try? data.write(to: url)
                }
                NSApp.terminate(nil)
            }
        }
    }

    func application(_: NSApplication, open urls: [URL]) {
        urls.forEach { FrontsideBridge.shared.handle($0) }
    }
}

// Notification names are already defined in Notifications+App.swift
