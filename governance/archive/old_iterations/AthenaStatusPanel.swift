import SwiftUI

// MARK: - Live Status Panel

struct AthenaStatusPanel: View {
    @EnvironmentObject var athena: AthenaState

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Connection Status Header
                HStack {
                    Circle()
                        .fill(athena.isConnected ? Color.green : Color.red)
                        .frame(width: 12, height: 12)

                    Text(athena.isConnected ? "Athena Connected" : "Athena Disconnected")
                        .font(.headline)

                    Spacer()

                    Text("Last update: \(athena.lastUpdate.formatted(date: .omitted, time: .shortened))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.horizontal)

                // Service Status Grid
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 300))], spacing: 16) {
                    ForEach(athena.services) { service in
                        ServiceStatusCard(service: service)
                    }
                }
                .padding(.horizontal)

                // Quick Actions
                VStack(alignment: .leading, spacing: 12) {
                    Text("Quick Actions")
                        .font(.title2)
                        .bold()

                    HStack(spacing: 12) {
                        Button(action: { athena.refreshAll() }) {
                            Label("Refresh Status", systemImage: "arrow.clockwise")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.borderedProminent)

                        Button(action: { athena.sendTestAlert() }) {
                            Label("Test Alerts", systemImage: "bell")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.bordered)

                        Button(action: { athena.openLogs() }) {
                            Label("View Logs", systemImage: "doc.text")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.bordered)
                    }
                }
                .padding(.horizontal)
                .padding(.top, 8)
            }
            .padding(.vertical)
        }
        .refreshable {
            athena.refreshAll()
        }
    }
}

// MARK: - Service Status Card

struct ServiceStatusCard: View {
    let service: AthenaService

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                // Status indicator
                Circle()
                    .fill(statusColor)
                    .frame(width: 8, height: 8)

                Text(service.name)
                    .font(.headline)

                Spacer()

                statusIcon
            }

            // Status details
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text("Status:")
                        .foregroundColor(.secondary)
                    Text(statusText)
                        .bold()
                        .foregroundColor(statusColor)
                }

                if let cadence = service.cadence {
                    HStack {
                        Text("Cadence:")
                            .foregroundColor(.secondary)
                        Text("\(cadence / 60)m")
                    }
                }

                HStack {
                    Text("Last Run:")
                        .foregroundColor(.secondary)
                    Text(service.lastRunDescription)
                }

                HStack {
                    Text("Next Run:")
                        .foregroundColor(.secondary)
                    Text(service.nextRunDescription)
                        .bold()
                        .foregroundColor(service.nextRunDescription == "Now" ? .orange : .primary)
                }
            }
            .font(.caption)
        }
        .padding()
        .background(.ultraThinMaterial)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(statusColor.opacity(0.3), lineWidth: 1)
        )
    }

    private var statusColor: Color {
        switch service.status {
        case .running: return .green
        case .idle: return .blue
        case .error: return .red
        case .stopped: return .gray
        }
    }

    private var statusText: String {
        switch service.status {
        case .running: return "Running"
        case .idle: return "Idle"
        case .error: return "Error"
        case .stopped: return "Stopped"
        }
    }

    private var statusIcon: some View {
        Group {
            switch service.status {
            case .running:
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(.green)
            case .idle:
                Image(systemName: "pause.circle.fill")
                    .foregroundColor(.blue)
            case .error:
                Image(systemName: "xmark.circle.fill")
                    .foregroundColor(.red)
            case .stopped:
                Image(systemName: "stop.circle.fill")
                    .foregroundColor(.gray)
            }
        }
    }
}

// MARK: - Preview

#Preview {
    AthenaStatusPanel()
        .environmentObject(AthenaState())
        .frame(width: 800, height: 600)
}
