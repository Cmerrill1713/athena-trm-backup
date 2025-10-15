import SwiftUI

// MARK: - Alert History & Acknowledgment Panel

struct AthenaAlertsPanel: View {
    @EnvironmentObject var athena: AthenaState

    var body: some View {
        VStack(spacing: 0) {
            // Alert Summary Header
            HStack {
                Text("Alert History")
                    .font(.title2)
                    .bold()

                Spacer()

                // Alert counts
                let unackedCount = athena.alerts.filter { !$0.acknowledged }.count
                if unackedCount > 0 {
                    Text("\(unackedCount) unacknowledged")
                        .font(.caption)
                        .foregroundColor(.orange)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(.orange.opacity(0.1))
                        .cornerRadius(8)
                }

                Button(action: { athena.acknowledgeAllAlerts() }) {
                    Label("Acknowledge All", systemImage: "checkmark.circle")
                }
                .disabled(unackedCount == 0)
            }
            .padding()

            Divider()

            // Alerts List
            if athena.alerts.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "bell.slash")
                        .font(.largeTitle)
                        .foregroundColor(.secondary)

                    Text("No alerts")
                        .font(.title3)
                        .foregroundColor(.secondary)

                    Button("Send Test Alert") {
                        athena.sendTestAlert()
                    }
                    .buttonStyle(.bordered)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(athena.alerts.sorted(by: { $0.timestamp > $1.timestamp })) { alert in
                            AlertCard(alert: alert)
                        }
                    }
                    .padding()
                }
            }
        }
        .refreshable {
            athena.refreshAlerts()
        }
    }
}

// MARK: - Alert Card

struct AlertCard: View {
    let alert: AthenaAlert
    @EnvironmentObject var athena: AthenaState

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                // Severity indicator
                Circle()
                    .fill(alert.severity.color)
                    .frame(width: 8, height: 8)

                Image(systemName: alert.severity.icon)
                    .foregroundColor(alert.severity.color)

                Text(alert.title)
                    .font(.headline)
                    .lineLimit(1)

                Spacer()

                // Acknowledgment status
                if alert.acknowledged {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                        .font(.caption)
                } else {
                    Button(action: { athena.acknowledgeAlert(alert) }) {
                        Text("Acknowledge")
                            .font(.caption)
                            .bold()
                            .foregroundColor(.white)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.blue)
                            .cornerRadius(6)
                    }
                }

                Text(alert.timeAgo)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            // Message
            Text(alert.message)
                .font(.body)
                .foregroundColor(.secondary)
                .lineLimit(3)

            // Actions (if applicable)
            if !alert.acknowledged {
                HStack {
                    Button("Acknowledge") {
                        athena.acknowledgeAlert(alert)
                    }
                    .buttonStyle(.borderedProminent)

                    Spacer()

                    Menu {
                        Button("Escalate") {
                            // TODO: Implement escalation
                        }
                        Button("View Details") {
                            // TODO: Show detailed alert view
                        }
                        Button("Silence Similar") {
                            // TODO: Silence alerts of this type
                        }
                    } label: {
                        Label("More", systemImage: "ellipsis")
                    }
                }
            }
        }
        .padding()
        .background(alert.acknowledged ? .ultraThinMaterial : .ultraThinMaterial.opacity(0.8))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(alert.acknowledged ? Color.clear : alert.severity.color.opacity(0.3), lineWidth: 1)
        )
        .opacity(alert.acknowledged ? 0.7 : 1.0)
    }
}

// MARK: - Alert Filters

struct AlertFilters: View {
    @Binding var selectedSeverity: AlertSeverity?
    @Binding var showAcknowledged: Bool

    var body: some View {
        HStack {
            Picker("Severity", selection: $selectedSeverity) {
                Text("All").tag(AlertSeverity?.none)
                Text("Critical").tag(AlertSeverity?.some(.critical))
                Text("Error").tag(AlertSeverity?.some(.error))
                Text("Warning").tag(AlertSeverity?.some(.warning))
                Text("Info").tag(AlertSeverity?.some(.info))
            }
            .pickerStyle(.menu)

            Toggle("Show Acknowledged", isOn: $showAcknowledged)
        }
        .padding(.horizontal)
    }
}

// MARK: - Preview

#Preview {
    let mockAthena = AthenaState()
    mockAthena.alerts = [
        AthenaAlert(id: "1", timestamp: Date().addingTimeInterval(-300), severity: .critical,
                   title: "Memory Corruption Detected", message: "Critical memory corruption detected in archive files. Immediate attention required.", acknowledged: false),
        AthenaAlert(id: "2", timestamp: Date().addingTimeInterval(-1800), severity: .warning,
                   title: "High Memory Usage", message: "Memory utilization at 85%. Optimization scheduled for next cycle.", acknowledged: false),
        AthenaAlert(id: "3", timestamp: Date().addingTimeInterval(-3600), severity: .info,
                   title: "Optimization Complete", message: "Successfully optimized memory usage by 35%", acknowledged: true)
    ]

    return AthenaAlertsPanel()
        .environmentObject(mockAthena)
        .frame(width: 800, height: 600)
}
