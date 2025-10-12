import SwiftUI

struct HealthBanner: View {
    @State private var healthy = false
    @State private var checking = false
    @State private var connectionMessage = ""
    let api = APIClient()

    var body: some View {
        HStack(spacing: 8) {
            Circle()
              .fill(healthy ? Color.green : Color.red)
              .frame(width: 10, height: 10)
            Text(healthy ? "Connected" : "Disconnected backend")
                .font(.caption)
            Spacer()
            Button(checking ? "…" : "Reconnect") {
                Task { await reconnectNow() }
            }
            .disabled(checking)
            .accessibilityIdentifier("reconnect_button")
        }
        .padding(8)
        .background(.thinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .accessibilityIdentifier("health_banner")
        .task { await runCheck() }

        // Environment info footer (QA mode only)
        if ProcessInfo.processInfo.environment["QA_MODE"] == "1" {
            VStack(spacing: 2) {
                HStack {
                    Text("API: \(ProcessInfo.processInfo.environment["API_BASE"] ?? "n/a")")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    Text("•")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    Text("QA_MODE: \(ProcessInfo.processInfo.environment["QA_MODE"] ?? "0")")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    Spacer()
                }
                if !connectionMessage.isEmpty {
                    HStack {
                        Text(connectionMessage)
                            .font(.caption2)
                            .foregroundStyle(.orange)
                        Spacer()
                    }
                }
            }
            .padding(.horizontal, 8)
            .padding(.bottom, 4)
        }
    }

    private func runCheck() async {
        checking = true
        defer { checking = false }
        healthy = await api.health()
    }

    @MainActor
    private func reconnectNow() async {
        checking = true
        connectionMessage = "Reconnecting..."

        let success = await api.health()

        if success {
            healthy = true
            connectionMessage = "Reconnected successfully"
            DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                connectionMessage = ""
            }
        } else {
            healthy = false
            connectionMessage = "Reconnection failed"
            DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                connectionMessage = ""
            }
        }

        checking = false
    }
}
