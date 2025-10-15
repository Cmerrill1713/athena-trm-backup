import SwiftUI
import AVFoundation
import AppKit

// Global flag to prevent duplicate processing
private var isProcessingURL = false

struct AthenaReporterApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject private var store = ReportStore.shared
    @State private var selectedId: String?

    var body: some Scene {
        WindowGroup("Athena Report") {
            ReportView(selectedId: $selectedId)
                .environmentObject(store)
                .onReceive(NotificationCenter.default.publisher(for: .init("athena.present"), object: nil)) { _ in
                    // legacy path, ignore
                }
                .onReceive(NotificationCenter.default.publisher(for: .init("athena.focus.\(selectedId ?? "")"))) { _ in
                    NSApp.activate(ignoringOtherApps: true)
                }
                .onOpenURL { url in
                    handleAthenaURL(url)
                }
        }
        .defaultSize(width: 900, height: 640)
        .windowStyle(.titleBar)
        .windowToolbarStyle(.automatic)
        .commands {
            CommandMenu("Athena") {
                Button("Stop Speaking") { 
                    AthenaSpeaker.shared.stop()
                }
                    .keyboardShortcut(".", modifiers: [.command])
                
                Button("Speak Again") { 
                    if let report = store.getLatestReport() {
                        AthenaSpeaker.shared.speak(report.summary)
                    }
                }
                    .keyboardShortcut("s", modifiers: [.command])
                
                Button("Test Voice") { 
                    AthenaSpeaker.shared.speak("Hi, I am Athena. This is a voice test using your pinned voice settings.")
                }
                    .keyboardShortcut("t", modifiers: [.command])
                
                Button("Say More") {
                    if let report = store.getLatestReport() {
                        if let concerns = extractConcernsSection(from: report.body) {
                            AthenaSpeaker.shared.stop()
                            AthenaSpeaker.shared.speak(concerns)
                        } else {
                            AthenaSpeaker.shared.stop()
                            AthenaSpeaker.shared.speak("No additional concerns to report.")
                        }
                    }
                }
                    .keyboardShortcut("l", modifiers: [.command])
                
                Divider()
                
                Button("Use System Voice") {
                    AthenaSpeaker.shared.backend = .system
                    print("🎤 Switched to system voice (AVSpeech)")
                }
                
                Button("Use Kokoro (localhost:8020)") {
                    if let url = URL(string: "http://127.0.0.1:8020/tts") {
                        if AthenaSpeaker.isKokoroAvailable(url: url.deletingLastPathComponent()) {
                            AthenaSpeaker.shared.backend = .http(url: url, voice: "athena")
                            print("🌐 Switched to Kokoro TTS")
                        } else {
                            print("⚠️  Kokoro not reachable at \(url)")
                        }
                    }
                }
            }
        }
        .handlesExternalEvents(matching: ["report"]) // for URL scheme deep link
    }
    
    func handleAthenaURL(_ url: URL) {
        guard let comps = URLComponents(url: url, resolvingAgainstBaseURL: false),
              comps.host == "report" else { return }

        print("🔗 Received URL: \(url.absoluteString)")

        let q = queryParams(from: url)
        let reportId = q["report_id"] ?? UUID().uuidString    // still unique if missing
        let title    = q["title"]    ?? "Athena Report"
        let summary  = q["summary"]  ?? ""
        let tsInt    = Int(q["ts"] ?? "") ?? Int(Date().timeIntervalSince1970)

        var body = "(empty)"
        if let mdPath = q["md_path"], !mdPath.isEmpty {
            body = (try? String(contentsOfFile: mdPath, encoding: .utf8)) ?? "(empty)"
            print("📄 Loaded markdown from file: \(mdPath)")
        } else if let md = q["md"] {
            body = md
            print("📄 Using markdown from URL")
        }

        let store = ReportStore.shared

        // If same report came in within 60s, just bring the window to front and bail.
        if store.recentlySaw(reportId) {
            focusWindow(for: reportId)
            return
        }

        // Update or insert model
        let model = ReportModel(id: reportId, title: title, summary: summary, body: body, ts: Date(timeIntervalSince1970: TimeInterval(tsInt)))
        store.addOrUpdateReport(model)

        // Show or update window (one per report_id)
        presentOrUpdateWindow(for: reportId, with: model)

        // Speak once (stop any current speech to avoid overlap)
        // Clean up the summary before speaking
        let cleanSummary = summary.trimmingCharacters(in: .whitespacesAndNewlines)
        AthenaSpeaker.shared.stop()
        if !cleanSummary.isEmpty {
            AthenaSpeaker.shared.speak(cleanSummary)
        }
    }

    func presentOrUpdateWindow(for id: String, with model: ReportModel) {
        selectedId = id
        NotificationCenter.default.post(name: .init("athena.present.\(id)"), object: model)
        NSApp.activate(ignoringOtherApps: true)
    }

    func focusWindow(for id: String) {
        selectedId = id
        NotificationCenter.default.post(name: .init("athena.focus.\(id)"), object: nil)
        NSApp.activate(ignoringOtherApps: true)
    }
}

// Entry point
@main
struct AthenaReporterMain {
    static func main() {
        AthenaReporterApp.main()
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Register custom URL scheme: athena:// (done in Info.plist)
        
        print("🚀 Athena Reporter launched")
        print(String(repeating: "=", count: 60))
        
        // Initialize Voice Sentinel (hard-lock + mismatch detection)
        _ = VoiceSentinel.shared
        
        // Run voice doctor diagnostics
        VoiceDoctor.run()
        print(String(repeating: "=", count: 60))
        
        // Initialize speaker backend
        _ = AthenaSpeaker.shared
        print("🎤 Voice backend: Voice Sentinel (hard-locked with mismatch detection)")
        print(String(repeating: "=", count: 60))
    }
}


struct ReportView: View {
    @EnvironmentObject var store: ReportStore
    @Binding var selectedId: String?

    var body: some View {
        let id = selectedId ?? store.reports.keys.sorted().last
        if let id, let model = store.reports[id] {
            VStack(spacing: 0) {
                // Header with title and controls
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(model.title)
                            .font(.system(size: 24, weight: .semibold))
                        Text(model.ts, style: .relative)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    Button {
                        AthenaSpeaker.shared.stop()
                    } label: {
                        Image(systemName: "speaker.slash.fill")
                    }
                    .help("Stop speaking (⌘.)")
                    .buttonStyle(.plain)
                    
                    Button {
                        AthenaSpeaker.shared.speak(model.summary)
                    } label: {
                        Image(systemName: "speaker.wave.2.fill")
                    }
                    .help("Speak again (⌘S)")
                    .buttonStyle(.plain)
                }
                .padding()
                .background(Color(NSColor.controlBackgroundColor))
                
                Divider()
                
                // Content area
                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        // Synopsis section
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Image(systemName: "megaphone.fill")
                                    .foregroundColor(.blue)
                                Text("Synopsis")
                                    .font(.headline)
                            }
                            Text(model.summary)
                                .font(.body)
                                .padding()
                                .background(Color(NSColor.controlBackgroundColor))
                                .cornerRadius(8)
                        }
                        
                        Divider()
                        
                        // Full report section
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Image(systemName: "doc.text.fill")
                                    .foregroundColor(.green)
                                Text("Full Report")
                                    .font(.headline)
                            }
                            
                            // Render markdown as attributed string
                            if let attributed = try? AttributedString(markdown: model.body) {
                                Text(attributed)
                                    .textSelection(.enabled)
                            } else {
                                Text(model.body)
                                    .font(.system(.body, design: .monospaced))
                                    .textSelection(.enabled)
                            }
                        }
                    }
                    .padding()
                }
            }
            .frame(minWidth: 700, minHeight: 520)
            .onReceive(NotificationCenter.default.publisher(for: .init("athena.present.\(id)"))) { notif in
                if let nm = notif.object as? ReportModel {
                    store.addOrUpdateReport(nm)
                    NSApp.activate(ignoringOtherApps: true)
                }
            }
        } else {
            VStack {
                Text("Waiting for report…")
                    .font(.title2)
                    .foregroundColor(.secondary)
                Text("Use `make report-health` to generate a report")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
            .padding()
            .frame(minWidth: 700, minHeight: 520)
        }
    }
}

private extension String {
    var nonEmpty: String? { isEmpty ? nil : self }
    
    var urlQueryDecoded: String {
        // In URL query strings, '+' often means a space
        let plusFixed = self.replacingOccurrences(of: "+", with: " ")
        return plusFixed.removingPercentEncoding ?? plusFixed
    }
}

func queryParams(from url: URL) -> [String: String] {
    var out: [String: String] = [:]
    if let comps = URLComponents(url: url, resolvingAgainstBaseURL: false) {
        comps.queryItems?.forEach { qi in
            out[qi.name] = (qi.value ?? "").urlQueryDecoded
        }
    }
    return out
}

func extractConcernsSection(from markdown: String) -> String? {
    // Look for "## ⚠️  Concerns" or "## Concerns" section
    let patterns = [
        "## ⚠️\\s*Concerns\\s*\\n([\\s\\S]*?)(?=\\n##|$)",
        "## Concerns\\s*\\n([\\s\\S]*?)(?=\\n##|$)"
    ]
    
    for pattern in patterns {
        if let regex = try? NSRegularExpression(pattern: pattern, options: [.caseInsensitive]),
           let match = regex.firstMatch(in: markdown, range: NSRange(markdown.startIndex..., in: markdown)),
           match.numberOfRanges > 1 {
            let range = match.range(at: 1)
            if let swiftRange = Range(range, in: markdown) {
                let concerns = String(markdown[swiftRange])
                    .trimmingCharacters(in: .whitespacesAndNewlines)
                    .replacingOccurrences(of: "\\n- ", with: ". ")
                    .replacingOccurrences(of: "\\n", with: " ")
                return concerns.isEmpty ? nil : concerns
            }
        }
    }
    return nil
}

