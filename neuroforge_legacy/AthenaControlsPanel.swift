import SwiftUI

// MARK: - Cadence & Policy Controls Panel

struct AthenaControlsPanel: View {
    @EnvironmentObject var athena: AthenaState
    @State private var selectedService: AthenaService?
    @State private var showingCadenceEditor = false

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Service Controls
                VStack(alignment: .leading, spacing: 16) {
                    Text("Service Cadences")
                        .font(.title2)
                        .bold()

                    Text("Adjust how frequently Athena performs monitoring and optimization tasks.")
                        .foregroundColor(.secondary)

                    ForEach(athena.services) { service in
                        ServiceControlCard(service: service) {
                            selectedService = service
                            showingCadenceEditor = true
                        }
                    }
                }

                Divider()

                // Global Settings
                VStack(alignment: .leading, spacing: 16) {
                    Text("Global Settings")
                        .font(.title2)
                        .bold()

                    // Alert Priority
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Alert Priority Level")
                            .font(.headline)

                        Text("Choose how many alerts Athena sends you.")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        Picker("Priority", selection: .constant("critical_warning")) {
                            Text("All Alerts").tag("all")
                            Text("Critical + Warning").tag("critical_warning")
                            Text("Critical Only").tag("critical_only")
                        }
                        .pickerStyle(.segmented)
                        .disabled(true) // TODO: Implement priority switching
                    }

                    // Quiet Hours
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Quiet Hours")
                                .font(.headline)

                            Spacer()

                            Circle()
                                .fill(athena.isCurrentlyQuietHours ? Color.blue : Color.gray)
                                .frame(width: 8, height: 8)

                            Text(athena.quietHoursStatusDescription)
                                .font(.caption)
                                .foregroundColor(athena.isCurrentlyQuietHours ? .blue : .secondary)
                        }

                        Text("Reduce alert frequency during specified hours. Critical alerts still go through.")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        Toggle("Enable Quiet Hours", isOn: $athena.quietHoursEnabled)
                            .onChange(of: athena.quietHoursEnabled) { _ in
                                athena.toggleQuietHours()
                            }

                        if athena.quietHoursEnabled {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Time Range")
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)

                                HStack {
                                    Picker("Start", selection: $athena.quietHoursStart) {
                                        ForEach(0..<24) { hour in
                                            Text(String(format: "%02d:00", hour)).tag(hour)
                                        }
                                    }
                                    .frame(width: 100)
                                    .disabled(!athena.quietHoursEnabled)

                                    Text("-")

                                    Picker("End", selection: $athena.quietHoursEnd) {
                                        ForEach(0..<24) { hour in
                                            Text(String(format: "%02d:00", hour)).tag(hour)
                                        }
                                    }
                                    .frame(width: 100)
                                    .disabled(!athena.quietHoursEnabled)
                                }
                                .onChange(of: athena.quietHoursStart) { _ in
                                    athena.setQuietHours(start: athena.quietHoursStart, end: athena.quietHoursEnd)
                                }
                                .onChange(of: athena.quietHoursEnd) { _ in
                                    athena.setQuietHours(start: athena.quietHoursStart, end: athena.quietHoursEnd)
                                }

                                if athena.queuedAlertsDuringQuiet.count > 0 {
                                    Text("\(athena.queuedAlertsDuringQuiet.count) alerts queued during quiet hours")
                                        .font(.caption)
                                        .foregroundColor(.orange)
                                }
                            }
                        }
                    }

                    // Voice Controls
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Voice Controls")
                            .font(.headline)

                        Text("Configure voice wake-word sensitivity.")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        Picker("Sensitivity", selection: .constant("low")) {
                            Text("Low (Fewer false positives)").tag("low")
                            Text("Medium (Balanced)").tag("medium")
                            Text("High (More responsive)").tag("high")
                        }
                        .pickerStyle(.menu)
                        .disabled(true) // TODO: Implement voice controls
                    }
                }

                Divider()

                // Quick Actions
                VStack(alignment: .leading, spacing: 16) {
                    Text("Quick Actions")
                        .font(.title2)
                        .bold()

                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 150))], spacing: 12) {
                        ActionButton(title: "Force Optimization", icon: "arrow.clockwise", color: .blue) {
                            athena.refreshAll()
                        }

                        ActionButton(title: "Send Test Alert", icon: "bell", color: .orange) {
                            athena.sendTestAlert()
                        }

                        ActionButton(title: "Acknowledge All", icon: "checkmark.circle", color: .green) {
                            athena.acknowledgeAllAlerts()
                        }

                        ActionButton(title: "View Logs", icon: "doc.text", color: .gray) {
                            athena.openLogs()
                        }

                        ActionButton(title: "Restart Services", icon: "arrow.triangle.2.circlepath", color: .red) {
                            // TODO: Implement service restart
                        }

                        ActionButton(title: "Emergency Stop", icon: "stop.circle", color: .red) {
                            // TODO: Implement emergency stop
                        }
                    }
                }

                Divider()

                // Advanced Settings
                VStack(alignment: .leading, spacing: 16) {
                    Text("Advanced Settings")
                        .font(.title2)
                        .bold()

                    VStack(alignment: .leading, spacing: 8) {
                        Text("Federation Settings")
                            .font(.headline)

                        Text("Configure multi-AI coordination settings.")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        HStack {
                            Text("Trust Threshold:")
                            Text("85%")
                                .bold()
                                .foregroundColor(.blue)
                        }

                        HStack {
                            Text("Peer Discovery:")
                            Text("Automatic")
                                .bold()
                                .foregroundColor(.green)
                        }

                        Button("Configure Federation") {
                            // TODO: Open federation settings
                        }
                        .buttonStyle(.bordered)
                    }
                }
            }
            .padding()
        }
        .sheet(item: $selectedService) { service in
            CadenceEditorView(service: service) { newCadence in
                athena.updateCadence(service: service.name, newCadence: newCadence)
                selectedService = nil
            }
        }
    }
}

// MARK: - Service Control Card

struct ServiceControlCard: View {
    let service: AthenaService
    let onEditCadence: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(service.name)
                    .font(.headline)

                Spacer()

                Circle()
                    .fill(statusColor)
                    .frame(width: 8, height: 8)

                Text(statusText)
                    .font(.caption)
                    .foregroundColor(statusColor)
            }

            HStack {
                VStack(alignment: .leading) {
                    Text("Current Cadence:")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    if let cadence = service.cadence {
                        Text("\(cadence / 60) minutes")
                            .font(.body)
                            .bold()
                    } else {
                        Text("Continuous")
                            .font(.body)
                            .bold()
                            .foregroundColor(.blue)
                    }
                }

                Spacer()

                Button(action: onEditCadence) {
                    Label("Edit", systemImage: "slider.horizontal.3")
                        .font(.caption)
                }
                .buttonStyle(.bordered)
            }
        }
        .padding()
        .background(.ultraThinMaterial)
        .cornerRadius(12)
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
        case .running: return "Active"
        case .idle: return "Idle"
        case .error: return "Error"
        case .stopped: return "Stopped"
        }
    }
}

// MARK: - Cadence Editor

struct CadenceEditorView: View {
    let service: AthenaService
    let onSave: (Int) -> Void

    @State private var selectedCadence: Int
    @Environment(\.dismiss) private var dismiss

    init(service: AthenaService, onSave: @escaping (Int) -> Void) {
        self.service = service
        self.onSave = onSave
        self._selectedCadence = State(initialValue: service.cadence ?? 3600)
    }

    let cadenceOptions = [
        ("5 minutes", 300),
        ("10 minutes", 600),
        ("15 minutes", 900),
        ("30 minutes", 1800),
        ("1 hour", 3600),
        ("2 hours", 7200),
        ("6 hours", 21600),
        ("12 hours", 43200),
        ("24 hours", 86400)
    ]

    var body: some View {
        VStack(spacing: 20) {
            Text("Edit Cadence")
                .font(.title2)
                .bold()

            Text("Configure how often \(service.name) runs.")
                .foregroundColor(.secondary)

            VStack(alignment: .leading, spacing: 12) {
                Text("Frequency")
                    .font(.headline)

                Picker("Cadence", selection: $selectedCadence) {
                    ForEach(cadenceOptions, id: \.1) { option in
                        Text(option.0).tag(option.1)
                    }
                }
                .pickerStyle(.wheel)

                Text("Selected: Every \(selectedCadence / 60) minutes")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            HStack {
                Button("Cancel") {
                    dismiss()
                }
                .buttonStyle(.bordered)

                Spacer()

                Button("Save Changes") {
                    onSave(selectedCadence)
                    dismiss()
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(24)
        .frame(width: 400, height: 400)
    }
}

// MARK: - Action Button

struct ActionButton: View {
    let title: String
    let icon: String
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundColor(color)

                Text(title)
                    .font(.caption)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity, minHeight: 80)
            .background(.ultraThinMaterial)
            .cornerRadius(12)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Preview

#Preview {
    let mockAthena = AthenaState()
    mockAthena.services = [
        AthenaService(name: "Memory Optimizer", status: .running, lastRun: Date().addingTimeInterval(-300), nextRun: Date().addingTimeInterval(3300), cadence: 3600),
        AthenaService(name: "Tribunal Monitor", status: .running, lastRun: Date().addingTimeInterval(-900), nextRun: Date().addingTimeInterval(0), cadence: 900)
    ]

    return AthenaControlsPanel()
        .environmentObject(mockAthena)
        .frame(width: 800, height: 600)
}
