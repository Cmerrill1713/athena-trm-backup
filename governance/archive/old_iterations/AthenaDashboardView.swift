import SwiftUI

struct AthenaDashboardView: View {
    @EnvironmentObject var state: AthenaState

    var body: some View {
        VStack(spacing: 16) {
            Text("Athena Dashboard").font(.largeTitle.bold())
            Text("Minimal, stable shell with pop-out triggers").foregroundStyle(.secondary)

            HStack {
                Button("Demo Critical Alert") {
                    state.trigger(CriticalAlert(
                        title: "DB p95 latency breach",
                        message: "Read pool saturated in us-east-1",
                        severity: .critical,
                        affectedSystems: ["db-read-replica-a","api-gateway"],
                        recommendations: ["Scale read replicas","Enable query cache","Switch traffic to us-west-2"]
                    ))
                }

                Button("Demo Tribunal Decision") {
                    state.trigger(TribunalCase(
                        caseID: "CASE-RAG-CE-001",
                        summary: "Rollback CE router? Uplift dipped by 0.3pts",
                        aiRecommendation: .modify,
                        confidence: 0.78
                    ))
                }

                Button("Demo System Emergency") {
                    state.trigger(SystemEmergency(
                        title: "Cluster Instability Detected",
                        analysis: "Pod churn > 20% / 5min; suspected node pressure.",
                        countdownSeconds: 20,
                        risk: .high,
                        actions: ["Drain suspect nodes","Throttle deploys","Scale control plane"]
                    ))
                }
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(24)
        .frame(minWidth: 800, minHeight: 500)
    }
}
