import SwiftUI

struct HealthBanner: View {
    @State private var healthy = false
    @State private var checking = false
    @State private var connectionMessage = ""
    @State private var servicesUp = 0
    @State private var totalServices = 0
    let api = APIClient()

    var body: some View {
        HStack(spacing: 8) {
            Circle()
              .fill(statusColor)
              .frame(width: 10, height: 10)
            Text(statusText)
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

    private var statusColor: Color {
        // Green if 3+ services up, yellow if 1-2, red if 0
        if servicesUp >= 3 { return .green }
        if servicesUp >= 1 { return .yellow }
        return .red
    }
    
    private var statusText: String {
        if checking { return "Checking..." }
        if totalServices > 0 {
            return "\(servicesUp)/\(totalServices) services up"
        }
        return healthy ? "Connected" : "Disconnected"
    }

    private func runCheck() async {
        checking = true
        defer { checking = false }
        
        // Check all services
        let checks = ServiceRegistry.shared.healthChecks
        totalServices = checks.count
        var upCount = 0
        
        for (_, urlString) in checks {
            guard let url = URL(string: urlString) else { continue }
            let ok = await api.head(url)
            if ok { upCount += 1 }
        }
        
        servicesUp = upCount
        healthy = upCount >= 3 // Consider healthy if at least 3 services are up
    }

    @MainActor
    private func reconnectNow() async {
        checking = true
        connectionMessage = "Reconnecting..."

        // Rerun check
        let checks = ServiceRegistry.shared.healthChecks
        totalServices = checks.count
        var upCount = 0
        
        for (_, urlString) in checks {
            guard let url = URL(string: urlString) else { continue }
            let ok = await api.head(url)
            if ok { upCount += 1 }
        }
        
        servicesUp = upCount
        let success = upCount >= 3

        if success {
            healthy = true
            connectionMessage = "Reconnected: \(upCount)/\(totalServices) services"
            DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                connectionMessage = ""
            }
        } else {
            healthy = false
            connectionMessage = "Reconnection failed: \(upCount)/\(totalServices) up"
            DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                connectionMessage = ""
            }
        }

        checking = false
    }
}
