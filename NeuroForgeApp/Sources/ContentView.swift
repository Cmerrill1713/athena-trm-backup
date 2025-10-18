import AVFoundation
import SwiftUI

// MARK: - Typing Focus Diagnostic View
/// Minimal test to isolate if SwiftUI TextField works at all
struct TypingFocusTester: View {
    @State private var text = ""
    @FocusState private var focused: Bool

    var body: some View {
        VStack(spacing: 20) {
            Text("🧪 Typing Focus Tester")
                .font(.title2)
                .fontWeight(.bold)

            Text(
                "If you can type in this field, SwiftUI works. If not, something global is intercepting events."
            )
            .multilineTextAlignment(.center)
            .foregroundColor(.secondary)
            .padding(.horizontal)

            TextField("Type here…", text: $text)
                .focused($focused)
                .textFieldStyle(.roundedBorder)
                .padding(.horizontal)
                .onAppear {
                    DispatchQueue.main.async { focused = true }
                }

            HStack {
                Text("Current text:")
                    .foregroundColor(.secondary)
                Text("\"\(text)\"")
                    .font(.system(.body, design: .monospaced))
                    .foregroundColor(text.isEmpty ? .red : .green)
            }

            Button("Clear & Refocus") {
                text = ""
                focused = true
            }
            .buttonStyle(.borderedProminent)

            Spacer()
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.windowBackgroundColor))
        .ignoresSafeArea(.keyboard, edges: .bottom)
    }
}

struct ContentView: View {
    let profile: UserProfile
    @EnvironmentObject var athenaState: AthenaState
    @EnvironmentObject var profileManager: ProfileManager

    // 🔧 DIAGNOSTIC MODE: Test if input works without NavigationSplitView
    @AppStorage("diagnosticMode") private var diagnosticMode = true  // Set to true for testing
    @State private var showTypingTester = false

    // Navigation selection for focus management
    @State private var navigationSelection: String = "chat"

    var body: some View {
        if diagnosticMode {
            // DIAGNOSTIC: Minimal test view with comprehensive debugging
            VStack {
                HStack {
                    Text("🔧 MINIMAL DIAGNOSTIC MODE")
                        .font(.headline)
                        .foregroundColor(.orange)
                    Spacer()
                    Button("Exit Diagnostic") {
                        diagnosticMode = false
                    }
                }
                .padding()
                .background(Color.orange.opacity(0.2))

                MinimalTestApp()
            }
            .onAppear {
                #if os(macOS)
                // Open floating chat window for testing
                openFloatingChatWindow()
                #endif
            }
        } else {
            // NORMAL MODE: Full app with navigation
            NavigationSplitView {
                // Sidebar with navigation
                List {
                    Section("Diagnostic") {
                        NavigationLink {
                            SimpleTextTestView()
                        } label: {
                            Label("🔧 Test Input", systemImage: "wrench.fill")
                        }

                        Button {
                            Task {
                                await pingLLM()
                            }
                        } label: {
                            Label("🎯 Ping LLM Gateway", systemImage: "bolt.fill")
                        }
                        .keyboardShortcut("p", modifiers: [.command, .shift])
                    }

                    Section("Chat") {
                        NavigationLink {
                            NeuroForgeChatView(
                                profile: profile, navigationSelection: navigationSelection)
                        } label: {
                            Label("Athena Chat", systemImage: "message.fill")
                        }
                        .tag("chat")
                    }

                    Section("Governance") {
                        NavigationLink {
                            GovernanceDashboardLiveView()
                        } label: {
                            Label("Dashboard", systemImage: "chart.bar.fill")
                        }

                        NavigationLink {
                            RoutingDashboardView()
                        } label: {
                            Label("Routing", systemImage: "arrow.triangle.branch")
                        }
                    }

                    Section("Settings") {
                        NavigationLink {
                            ProfileSettingsView(profile: profile)
                        } label: {
                            Label("Profile", systemImage: "person.circle.fill")
                        }

                        Button("Enable Diagnostic Mode") {
                            diagnosticMode = true
                        }

                        Button("🧪 Test Minimal Input") {
                            showTypingTester = true
                        }
                    }
                }
                .navigationTitle("Athena")
                .navigationSplitViewColumnWidth(min: 200, ideal: 250, max: 300)
            } detail: {
                // Default to chat view
                NeuroForgeChatView(profile: profile)
            }
            .frame(minWidth: 800, minHeight: 600)
            .sheet(isPresented: $showTypingTester) {
                TypingFocusTester()
                    .frame(minWidth: 400, minHeight: 300)
            }
        }
    }

    // MARK: - Debug Functions

    func pingLLM() async {
        print("🎯 PING LLM button pressed!")

        do {
            let url = URL(string: "http://127.0.0.1:8015/v1/chat/completions")!
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")

            let payload: [String: Any] = [
                "messages": [
                    ["role": "user", "content": "Say 'pong' in 3 words"]
                ],
                "stream": false,
            ]

            request.httpBody = try JSONSerialization.data(withJSONObject: payload)

            print("📡 Calling gateway at: \(url.absoluteString)")

            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ Bad response type")
                return
            }

            print("📥 Response code: \(httpResponse.statusCode)")

            if httpResponse.statusCode == 200 {
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                    let choices = json["choices"] as? [[String: Any]],
                    let message = choices.first?["message"] as? [String: Any],
                    let content = message["content"] as? String
                {
                    print("✅ Ping OK: \(content)")
                } else {
                    print("⚠️ Response OK but couldn't parse")
                    print(String(data: data, encoding: .utf8) ?? "")
                }
            } else {
                print("❌ HTTP \(httpResponse.statusCode)")
                print(String(data: data, encoding: .utf8) ?? "")
            }

        } catch {
            print("❌ Ping FAIL: \(error)")
        }
    }
}

// Simple profile settings view
struct ProfileSettingsView: View {
    let profile: UserProfile

    var body: some View {
        Form {
            Section("Profile") {
                LabeledContent("Name", value: profile.name)
                LabeledContent("ID", value: profile.id)
            }

            Section("About") {
                Text("NeuroForge Athena")
                    .font(.headline)
                Text("AI Assistant Platform")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
        }
        .formStyle(.grouped)
        .navigationTitle("Settings")
        .frame(minWidth: 400, minHeight: 300)
    }
}
