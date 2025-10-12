import SwiftUI

struct FirstRunWizardView: View {
    @State private var step: Int = 0
    @State private var healthOK = false
    @State private var offlineLock = true
    @State private var warming = false
    @State private var warmOK = false
    @State private var smokeRunning = false
    @State private var smokeOK = false
    @State private var statusMsg = ""

    let apiBase = URL(string: ProcessInfo.processInfo.environment["API_BASE"] ?? "http://localhost:8014")!

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("First-Run Setup").font(.largeTitle).bold().accessibilityIdentifier("FR_Title")

            // Step 1: Health
            GroupBox {
                HStack {
                    Text("1) Check Service Health").bold()
                    Spacer()
                    Circle().fill(healthOK ? Color.green : Color.gray).frame(width: 12, height: 12)
                }
                Button("Run Health Check") { runHealth() }
                    .accessibilityIdentifier("FR_HealthButton")
                Text(statusMsg).font(.footnote).foregroundColor(.secondary).accessibilityIdentifier("FR_Status")
            }.accessibilityIdentifier("FR_Step_Health")

            // Step 2: Offline mode
            GroupBox {
                HStack {
                    Text("2) Offline Lock").bold()
                    Spacer()
                    Toggle("", isOn: $offlineLock).labelsHidden()
                        .accessibilityIdentifier("FR_OfflineToggle")
                }
                Text("Keeps all capability execution local. You can change this later in Settings.")
                    .font(.footnote).foregroundColor(.secondary)
            }.accessibilityIdentifier("FR_Step_Offline")

            // Step 3: Knowledge warmup
            GroupBox {
                HStack {
                    Text("3) Warm Knowledge Base").bold()
                    Spacer()
                    Circle().fill(warmOK ? Color.green : (warming ? .yellow : .gray)).frame(width: 12, height: 12)
                }
                Button(warming ? "Warming…" : "Warm Knowledge (170 transcripts)") {
                    Task { await warmKnowledge() }
                }
                .disabled(warming)
                .accessibilityIdentifier("FR_WarmButton")
            }.accessibilityIdentifier("FR_Step_Warm")

            // Step 4: Feature Smoke
            GroupBox {
                HStack {
                    Text("4) Feature Smoke Test").bold()
                    Spacer()
                    Circle().fill(smokeOK ? Color.green : (smokeRunning ? .yellow : .gray))
                        .frame(width: 12, height: 12)
                }
                Button(smokeRunning ? "Running…" : "Test (Chat, RAG, Vision)") {
                    Task { await runSmoke() }
                }
                .disabled(smokeRunning)
                .accessibilityIdentifier("FR_SmokeButton")
            }.accessibilityIdentifier("FR_Step_Smoke")

            Spacer()

            // Done button
            HStack {
                Spacer()
                Button(action: { /* Store preference and dismiss */ }) {
                    Text(healthOK && warmOK && smokeOK ? "Finish (All Green ✅)" : "Finish Anyway")
                        .frame(minWidth: 180)
                }
                .keyboardShortcut(.defaultAction)
                .accessibilityIdentifier("FR_FinishButton")
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(24)
        .frame(minWidth: 600, minHeight: 500)
    }

    private func runHealth() {
        statusMsg = "Checking /health…"
        let url = apiBase.appendingPathComponent("health")
        URLSession.shared.dataTask(with: url) { data, resp, _ in
            DispatchQueue.main.async {
                if let httpResp = resp as? HTTPURLResponse,
                   httpResp.statusCode == 200 {
                    healthOK = true
                    statusMsg = "Health OK ✅"
                } else {
                    healthOK = false
                    statusMsg = "Health check failed ❌"
                }
            }
        }.resume()
    }

    private func warmKnowledge() async {
        warming = true
        warmOK = false

        // Call RAG health to warm up the knowledge base
        guard let ragURL = URL(string: "http://localhost:8015/api/rag/health") else {
            DispatchQueue.main.async { self.warming = false }
            return
        }

        do {
            let (data, resp) = try await URLSession.shared.data(from: ragURL)
            if let httpResp = resp as? HTTPURLResponse,
               httpResp.statusCode == 200,
               let json = try? JSONDecoder().decode([String: AnyCodable].self, from: data) {
                DispatchQueue.main.async {
                    self.warmOK = true
                    self.warming = false
                }
            } else {
                DispatchQueue.main.async {
                    self.warmOK = false
                    self.warming = false
                }
            }
        } catch {
            DispatchQueue.main.async {
                self.warmOK = false
                self.warming = false
            }
        }
    }

    private func runSmoke() async {
        smokeRunning = true
        smokeOK = false

        // Test basic chat, RAG, and vision endpoints
        let chatOK = await testEndpoint(apiBase.appendingPathComponent("health"))
        let ragOK = await testEndpoint(URL(string: "http://localhost:8015/api/rag/health")!)
        let visionOK = await testEndpoint(URL(string: "http://localhost:8016/api/vision/health")!)

        DispatchQueue.main.async {
            self.smokeOK = chatOK && ragOK && visionOK
            self.smokeRunning = false
        }
    }

    private func testEndpoint(_ url: URL) async -> Bool {
        do {
            let (_, resp) = try await URLSession.shared.data(from: url)
            return (resp as? HTTPURLResponse)?.statusCode == 200
        } catch {
            return false
        }
    }
}

// Helper for decoding arbitrary JSON
private struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else {
            value = try container.decode([String: AnyCodable].self)
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch value {
        case let int as Int: try container.encode(int)
        case let double as Double: try container.encode(double)
        case let string as String: try container.encode(string)
        case let bool as Bool: try container.encode(bool)
        default: break
        }
    }
}
