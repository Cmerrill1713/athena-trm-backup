import SwiftUI

struct AthenaDashboardView: View {
    @EnvironmentObject var state: AthenaState
    // @StateObject private var promptEngineer = PromptEngineerService() // v1.0.3: fix ObservableObject
    @State private var promptResult: String = ""
    @State private var isEngineering = false

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                Text("Athena Dashboard").font(.largeTitle.bold())
                Text("AI Operations Center with UAT & Prompt Engineering").foregroundStyle(.secondary)

                // Service Status
                ServiceStatusView()

                Divider()

                // AI Team Prompt Engineering
                VStack(alignment: .leading, spacing: 12) {
                    Text("AI Team Prompt Engineering").font(.title2.bold())

                    VStack(alignment: .leading, spacing: 8) {
                        Text("Test the AI Team pipeline:")
                            .font(.headline)

                        Button("Engineer Redis Monitoring Service") {
                            engineerPrompt()
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(isEngineering)

                        if isEngineering {
                            HStack {
                                ProgressView()
                                    .scaleEffect(0.8)
                                Text("AI Team working...")
                                    .foregroundStyle(.secondary)
                            }
                        }

                        if !promptResult.isEmpty {
                            ScrollView {
                                Text(promptResult)
                                    .font(.system(.body, design: .monospaced))
                                    .padding(12)
                                    .background(Color(.textBackgroundColor))
                                    .cornerRadius(8)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                            }
                            .frame(height: 300)
                        }
                    }
                }

                Divider()

                // Avatar Morph Settings
                AvatarMorphSettingsView()

                Divider()

                // Demo Triggers
                VStack(alignment: .leading, spacing: 12) {
                    Text("System Triggers").font(.title2.bold())

                    HStack(spacing: 12) {
                        Button("Demo Critical Alert") {
                            self.state.trigger(CriticalAlert(
                                title: "DB p95 latency breach",
                                message: "Read pool saturated in us-east-1",
                                severity: .critical,
                                affectedSystems: ["db-read-replica-a", "api-gateway"],
                                recommendations: ["Scale read replicas", "Enable query cache", "Switch traffic to us-west-2"]
                            ))
                        }

                        Button("Demo Tribunal Decision") {
                            self.state.trigger(TribunalCase(
                                caseID: "CASE-RAG-CE-001",
                                summary: "Rollback CE router? Uplift dipped by 0.3pts",
                                aiRecommendation: .modify,
                                confidence: 0.78
                            ))
                        }

                        Button("Demo System Emergency") {
                            self.state.trigger(SystemEmergency(
                                title: "Cluster Instability Detected",
                                analysis: "Pod churn > 20% / 5min; suspected node pressure.",
                                countdownSeconds: 20,
                                risk: .high,
                                actions: ["Drain suspect nodes", "Throttle deploys", "Scale control plane"]
                            ))
                        }
                    }
                    .buttonStyle(.borderedProminent)
                }
            }
            .padding(24)
            .frame(minWidth: 1000, minHeight: 800)
        }
    }

    private func engineerPrompt() {
        isEngineering = true
        promptResult = ""

        Task {
            do {
                let request = PromptEngineeringRequest(
                    task: "Write a Python service to monitor Redis memory and alert at 80% usage",
                    context: ["language": "python", "monitoring": "redis"],
                    constraints: ["Use redis-py library", "Send alerts via email", "Log to stdout"],
                    examples: ["Monitor CPU usage", "Check disk space"]
                )

                // v1.0.2: PromptEngineerService disabled (needs ObservableObject)
                // v1.0.3: Restore with proper conformance
                // let response = try await promptEngineer.engineerPrompt(payload: request)

                promptResult = """
                🧠 **AI Team Engineering (v1.0.2: Stub)**

                **Status:** Feature temporarily disabled for v1.0.2
                **Note:** Will be restored in v1.0.3 with proper ObservableObject conformance

                **Planned Restoration:**
                • PromptEngineerService with ObservableObject
                • Full AI team orchestration
                • Real-time team contributions
                • Full reviewer feedback system
                """

            } catch {
                promptResult = "❌ Prompt engineering failed: \(error.localizedDescription)"
            }

            isEngineering = false
        }
    }
}
