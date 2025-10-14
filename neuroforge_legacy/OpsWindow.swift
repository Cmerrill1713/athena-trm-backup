import SwiftUI

// MARK: - Operations Dashboard Window

struct OpsWindow: View {
    @EnvironmentObject var ops: OpsState
    @SceneStorage("opsWindowFrame") private var frameData: Data?
    @State private var selectedService: ServiceInfo?

    var body: some View {
        VStack(spacing: 0) {
            // Tab picker
            Picker("View", selection: $ops.currentTab) {
                ForEach(OpsTab.allCases) { tab in
                    Label(tab.title, systemImage: tab.icon)
                        .tag(tab)
                }
            }
            .pickerStyle(.segmented)
            .padding(12)
            .background(.ultraThinMaterial)

            Divider()

            // Content
            Group {
                switch ops.currentTab {
                case .traces:
                    TracePanelView()
                case .health:
                    healthTab
                case .meta:
                    metaTab
                case .metrics:
                    metricsTab
                case .aiRepublic:
                    aiRepublicTab
                }
            }
        }
        .frame(minWidth: 640, minHeight: 420)
        .onAppear {
            ops.isWindowOpen = true
        }
        .onDisappear {
            ops.isWindowOpen = false
        }
        .sheet(item: $selectedService) { service in
            LogViewer(service: service)
        }
    }

    // MARK: - Health Tab

    @StateObject private var healthChecker = ServiceHealthChecker()

    private var healthTab: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Service health grid
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Service Health")
                            .font(.headline)
                        Spacer()
                        Button("Refresh") {
                            Task { await healthChecker.checkAll(services: ServiceRegistry.all) }
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                    }

                    // Group by tier
                    ForEach(ServiceTier.allCases, id: \.self) { tier in
                        let services = ServiceRegistry.byTier(tier)
                        if !services.isEmpty {
                            VStack(alignment: .leading, spacing: 6) {
                                Text(tier.rawValue)
                                    .font(.caption.weight(.semibold))
                                    .foregroundStyle(tier.color)

                                ForEach(services) { service in
                                    serviceRow(for: service)
                                }
                            }
                        }
                    }
                }
                .padding()
                .background(RoundedRectangle(cornerRadius: 10).fill(.ultraThinMaterial))

                // Health banner (overall)
                HealthBanner()
                    .padding()

                // Recent events
                if !ops.recentEvents.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Recent Events")
                            .font(.headline)

                        ForEach(ops.recentEvents.prefix(10)) { event in
                            HStack(spacing: 8) {
                                Circle()
                                    .fill(event.type.color)
                                    .frame(width: 8, height: 8)
                                Text(event.timestamp, style: .time)
                                    .font(.caption.monospacedDigit())
                                    .foregroundStyle(.secondary)
                                Text(event.message)
                                    .font(.caption)
                                if let conf = event.confidence {
                                    Text("\(Int(conf * 100))%")
                                        .font(.caption.monospacedDigit())
                                        .foregroundStyle(.tertiary)
                                }
                            }
                        }
                    }
                    .padding()
                }
            }
            .padding()
        }
        .onAppear {
            Task { await healthChecker.checkAll(services: ServiceRegistry.all) }
        }
    }

    @ViewBuilder
    private func serviceRow(for service: ServiceInfo) -> some View {
        if let health = healthChecker.statuses[service.id] {
            HStack(spacing: 8) {
                Circle()
                    .fill(health.isHealthy ? Color.green : Color.red)
                    .frame(width: 8, height: 8)

                Text(service.name)
                    .font(.caption)

                Text(":\(service.port)")
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(.tertiary)

                Spacer()

                if let latency = health.latencyMs {
                    Text("\(latency)ms")
                        .font(.caption2.monospacedDigit())
                        .foregroundStyle(.secondary)
                }

                if let error = health.error, !health.isHealthy {
                    Text(error)
                        .font(.caption2)
                        .foregroundStyle(.red)
                        .lineLimit(1)
                }

                // Logs button (opens sheet)
                Button {
                    selectedService = service
                } label: {
                    Image(systemName: "doc.text.magnifyingglass")
                        .font(.caption)
                }
                .buttonStyle(.borderless)
                .help("View \(service.name) logs")
            }
        } else {
            HStack(spacing: 8) {
                ProgressView()
                    .scaleEffect(0.6)
                Text(service.name)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }

    // MARK: - Meta Tab

    private var metaTab: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Confidence trend
                if let conf = ops.lastConfidence {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Last Confidence")
                            .font(.headline)

                        HStack {
                            Circle()
                                .fill(confidenceColor(conf))
                                .frame(width: 12, height: 12)
                            Text("\(Int(conf * 100))%")
                                .font(.title2.monospacedDigit().weight(.semibold))
                                .foregroundStyle(confidenceColor(conf))
                            Spacer()
                        }
                    }
                    .padding()
                    .background(RoundedRectangle(cornerRadius: 10).fill(.ultraThinMaterial))
                }

                // Meta settings
                VStack(alignment: .leading, spacing: 12) {
                    Text("Auto-Open Settings")
                        .font(.headline)

                    Toggle("Auto-open on low confidence", isOn: $ops.autoOpenOnLowConfidence)

                    HStack {
                        Text("Threshold:")
                        Slider(value: $ops.lowConfidenceThreshold, in: 0.1...0.5, step: 0.05)
                        Text("\(Int(ops.lowConfidenceThreshold * 100))%")
                            .font(.caption.monospacedDigit())
                    }
                }
                .padding()
            }
            .padding()
        }
    }

    // MARK: - Metrics Tab

    private var metricsTab: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("System Metrics")
                    .font(.headline)

                Text("Coming soon: Real-time metrics, charts, and performance data")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding()
        }
    }

    // MARK: - AI Republic Tab

    @StateObject private var aiRepublicMonitor = AIRepublicMonitor()

    private var aiRepublicTab: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Header with sovereignty badge
                HStack {
                    VStack(alignment: .leading) {
                        Text("🏛️ Sovereign AI Republic")
                            .font(.title2.bold())
                        Text("Constitutional Republic - Operational")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    Button("Refresh Status") {
                        Task { await aiRepublicMonitor.refreshStatus() }
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }

                // Constitution status
                VStack(alignment: .leading, spacing: 12) {
                    Text("Constitutional Framework")
                        .font(.headline)

                    HStack(spacing: 20) {
                        constitutionStatus("Articles I-II", aiRepublicMonitor.constitutionStatus)
                        constitutionStatus("Tribunal System", aiRepublicMonitor.tribunalStatus)
                        constitutionStatus("Federation Ready", aiRepublicMonitor.federationStatus)
                    }
                }
                .padding()
                .background(RoundedRectangle(cornerRadius: 10).fill(.ultraThinMaterial))

                // Service health grid
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("AI Republic Services")
                            .font(.headline)
                        Spacer()
                        Text("\(aiRepublicMonitor.activeServices)/4 Active")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

                    VStack(spacing: 8) {
                        aiRepublicServiceRow("Memory Optimizer", aiRepublicMonitor.memoryStatus, "brain")
                        aiRepublicServiceRow("Voice Integration", aiRepublicMonitor.voiceStatus, "waveform")
                        aiRepublicServiceRow("Tribunal Engine", aiRepublicMonitor.tribunalServiceStatus, "building.columns")
                        aiRepublicServiceRow("Alert System", aiRepublicMonitor.alertStatus, "exclamationmark.triangle")
                    }
                }
                .padding()
                .background(RoundedRectangle(cornerRadius: 10).fill(.ultraThinMaterial))

                // Recent alerts and tribunal activity
                if !aiRepublicMonitor.recentAlerts.isEmpty {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Recent Alerts & Tribunal Activity")
                            .font(.headline)

                        ForEach(aiRepublicMonitor.recentAlerts.prefix(8)) { alert in
                            HStack(spacing: 12) {
                                Circle()
                                    .fill(alert.severity.color)
                                    .frame(width: 8, height: 8)

                                VStack(alignment: .leading, spacing: 2) {
                                    Text(alert.title)
                                        .font(.caption.bold())
                                    Text(alert.message)
                                        .font(.caption2)
                                        .foregroundStyle(.secondary)
                                        .lineLimit(1)
                                }

                                Spacer()

                                Text(alert.timestamp, style: .time)
                                    .font(.caption2.monospacedDigit())
                                    .foregroundStyle(.tertiary)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                    .padding()
                    .background(RoundedRectangle(cornerRadius: 10).fill(.ultraThinMaterial))
                }

                // Quick actions
                VStack(alignment: .leading, spacing: 12) {
                    Text("Quick Actions")
                        .font(.headline)

                    HStack(spacing: 12) {
                        Button("Test Alert Cascade") {
                            // This would trigger a test alert
                            print("Test alert cascade triggered")
                        }
                        .buttonStyle(.bordered)

                        Button("View Tribunal Logs") {
                            // This would open tribunal logs
                            print("Open tribunal logs")
                        }
                        .buttonStyle(.bordered)

                        Button("Federation Status") {
                            // This would show federation connections
                            print("Show federation status")
                        }
                        .buttonStyle(.bordered)
                    }
                }
                .padding()
                .background(RoundedRectangle(cornerRadius: 10).fill(.ultraThinMaterial))

                // Sovereignty metrics
                VStack(alignment: .leading, spacing: 12) {
                    Text("Sovereignty Metrics")
                        .font(.headline)

                    HStack(spacing: 20) {
                        metricView("Compliance Rate", "99.9%", .green)
                        metricView("Uptime", aiRepublicMonitor.uptime, .blue)
                        metricView("Active Alerts", "\(aiRepublicMonitor.activeAlertCount)", .orange)
                        metricView("Constitution Version", "I-II (2024)", .purple)
                    }
                }
                .padding()
                .background(RoundedRectangle(cornerRadius: 10).fill(.ultraThinMaterial))

                // Quiet Hours Configuration
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Quiet Hours Configuration")
                            .font(.headline)
                        Spacer()
                        Text(aiRepublicMonitor.quietHoursActive ? "🕐 Active" : "🌅 Disabled")
                            .font(.caption)
                            .foregroundStyle(aiRepublicMonitor.quietHoursActive ? .orange : .green)
                    }

                    if aiRepublicMonitor.quietHoursActive {
                        HStack {
                            Text("Current: \(aiRepublicMonitor.quietHoursDisplay)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Spacer()
                            Button("Modify") {
                                // Could open a sheet for quiet hours configuration
                                print("Open quiet hours configuration")
                            }
                            .buttonStyle(.bordered)
                            .controlSize(.small)
                        }

                        Text("During quiet hours: Info alerts suppressed, warning alerts silent, critical alerts full escalation")
                            .font(.caption2)
                            .foregroundStyle(.tertiary)
                            .lineLimit(2)
                    } else {
                        HStack {
                            Text("Quiet hours disabled - all alerts active")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Spacer()
                            Button("Enable") {
                                // Enable quiet hours with default 10 PM - 8 AM
                                Task { await aiRepublicMonitor.enableQuietHours() }
                            }
                            .buttonStyle(.bordered)
                            .controlSize(.small)
                        }
                    }

                    HStack(spacing: 12) {
                        Button(aiRepublicMonitor.quietHoursActive ? "Disable" : "Enable") {
                            Task {
                                if aiRepublicMonitor.quietHoursActive {
                                    await aiRepublicMonitor.disableQuietHours()
                                } else {
                                    await aiRepublicMonitor.enableQuietHours()
                                }
                            }
                        }
                        .buttonStyle(.bordered)

                        Button("Test Alert") {
                            Task { await aiRepublicMonitor.testQuietHours() }
                        }
                        .buttonStyle(.bordered)
                    }
                }
                .padding()
                .background(RoundedRectangle(cornerRadius: 10).fill(.ultraThinMaterial))

                // Smart Alerting Configuration (Focus Mode & Calendar)
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Smart Alerting")
                            .font(.headline)
                        Spacer()
                        Text(aiRepublicMonitor.smartAlertingEnabled ? "🧠 Active" : "⚙️ Disabled")
                            .font(.caption)
                            .foregroundStyle(aiRepublicMonitor.smartAlertingEnabled ? .blue : .secondary)
                    }

                    if aiRepublicMonitor.smartAlertingEnabled {
                        VStack(alignment: .leading, spacing: 8) {
                            // Current Context Status
                            HStack(spacing: 12) {
                                Text("📱 Focus:")
                                    .font(.caption.bold())
                                Circle()
                                    .fill(aiRepublicMonitor.focusModeActive ? Color.red : Color.green)
                                    .frame(width: 8, height: 8)
                                Text(aiRepublicMonitor.focusModeActive ? "Active" : "Inactive")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }

                            HStack(spacing: 12) {
                                Text("📅 Calendar:")
                                    .font(.caption.bold())
                                Circle()
                                    .fill(aiRepublicMonitor.calendarBusy ? Color.orange : Color.green)
                                    .frame(width: 8, height: 8)
                                Text(aiRepublicMonitor.calendarBusy ? "Busy" : "Free")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }

                            HStack(spacing: 12) {
                                Text("📍 Location:")
                                    .font(.caption.bold())
                                let locationColor: Color = {
                                    switch aiRepublicMonitor.currentLocation {
                                    case "home": return .blue
                                    case "work": return .purple
                                    case "travel": return .orange
                                    default: return .gray
                                    }
                                }()
                                Circle()
                                    .fill(locationColor)
                                    .frame(width: 8, height: 8)
                                Text(aiRepublicMonitor.currentLocation.capitalized)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }

                            Text("Smart alerts adapt to your iPhone Focus modes and calendar status")
                                .font(.caption2)
                                .foregroundStyle(.tertiary)
                                .lineLimit(2)
                        }
                    } else {
                        Text("Enable smart alerting to automatically adjust notifications based on your iPhone Focus modes and calendar")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(3)
                    }

                    HStack(spacing: 12) {
                        Button(aiRepublicMonitor.smartAlertingEnabled ? "Disable" : "Enable") {
                            Task {
                                if aiRepublicMonitor.smartAlertingEnabled {
                                    await aiRepublicMonitor.disableSmartAlerting()
                                } else {
                                    await aiRepublicMonitor.enableSmartAlerting()
                                }
                            }
                        }
                        .buttonStyle(.bordered)

                        if aiRepublicMonitor.smartAlertingEnabled {
                            Button("Simulate Focus") {
                                Task {
                                    await aiRepublicMonitor.simulateFocusMode(active: !aiRepublicMonitor.focusModeActive)
                                }
                            }
                            .buttonStyle(.bordered)
                            .controlSize(.small)

                            Button("Simulate Busy") {
                                Task {
                                    await aiRepublicMonitor.simulateCalendarBusy(busy: !aiRepublicMonitor.calendarBusy)
                                }
                            }
                            .buttonStyle(.bordered)
                            .controlSize(.small)

                            Menu {
                                Button("🏠 Home") {
                                    Task { await aiRepublicMonitor.simulateLocation(location: "home") }
                                }
                                Button("🏢 Work") {
                                    Task { await aiRepublicMonitor.simulateLocation(location: "work") }
                                }
                                Button("✈️ Travel") {
                                    Task { await aiRepublicMonitor.simulateLocation(location: "travel") }
                                }
                            } label: {
                                Text("Location")
                                    .font(.caption)
                            }
                            .menuStyle(.borderedButton)
                            .fixedSize()
                        }

                        Button("Test Smart") {
                            Task { await aiRepublicMonitor.testSmartAlerting() }
                        }
                        .buttonStyle(.bordered)
                    }
                }
                .padding()
                .background(RoundedRectangle(cornerRadius: 10).fill(.ultraThinMaterial))
            }
            .padding()
        }
        .onAppear {
            Task { await aiRepublicMonitor.refreshStatus() }
        }
    }

    @ViewBuilder
    private func constitutionStatus(_ title: String, _ status: ServiceHealth) -> some View {
        VStack(spacing: 4) {
            Circle()
                .fill(status.isHealthy ? Color.green : Color.red)
                .frame(width: 8, height: 8)
            Text(title)
                .font(.caption)
                .multilineTextAlignment(.center)
        }
    }

    @ViewBuilder
    private func aiRepublicServiceRow(_ name: String, _ status: ServiceHealth, _ icon: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.caption)
                .foregroundStyle(.secondary)
                .frame(width: 20)

            Circle()
                .fill(status.isHealthy ? Color.green : Color.red)
                .frame(width: 8, height: 8)

            Text(name)
                .font(.caption)

            Spacer()

            if let latency = status.latencyMs {
                Text("\(latency)ms")
                    .font(.caption2.monospacedDigit())
                    .foregroundStyle(.tertiary)
            }

            if let error = status.error, !status.isHealthy {
                Text(error)
                    .font(.caption2)
                    .foregroundStyle(.red)
                    .lineLimit(1)
            }
        }
    }

    @ViewBuilder
    private func metricView(_ label: String, _ value: String, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.title3.monospacedDigit().bold())
                .foregroundStyle(color)
            Text(label)
                .font(.caption)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
    }

    // MARK: - Helpers

    private func confidenceColor(_ conf: Double) -> Color {
        switch conf {
        case 0.8...1.0: return .green
        case 0.6..<0.8: return .yellow
        default: return .red
        }
    }
}

// MARK: - Preview

#Preview {
    OpsWindow()
        .environmentObject(OpsState())
}
