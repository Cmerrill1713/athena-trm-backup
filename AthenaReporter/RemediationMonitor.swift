import Foundation
import SwiftUI

/// Remediation Monitor - Production monitoring for auto-remediation system
/// Integrates with AthenaReporter for comprehensive governance visibility
struct RemediationMonitorView: View {
    @StateObject private var monitor = RemediationMonitor()
    @State private var selectedTab = 0

    var body: some View {
        VStack(spacing: 0) {
            // Header with status
            HStack {
                Image(systemName: "bolt.heart.fill")
                    .foregroundColor(.orange)
                    .font(.title)
                Text("Auto-Remediation System")
                    .font(.title.bold())
                Spacer()

                // Connection indicator
                HStack(spacing: 4) {
                    Circle()
                        .fill(monitor.isConnected ? Color.green : Color.red)
                        .frame(width: 10, height: 10)
                    Text(monitor.isConnected ? "LIVE" : "OFFLINE")
                        .font(.caption.bold())
                        .foregroundColor(monitor.isConnected ? .green : .red)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color(NSColor.controlBackgroundColor).opacity(0.5))
                .cornerRadius(12)

                Button(action: { monitor.refresh() }) {
                    Image(systemName: "arrow.clockwise")
                }
                .buttonStyle(.plain)
                .help("Refresh metrics")
            }
            .padding()
            .background(Color(NSColor.windowBackgroundColor))

            Divider()

            // Tab selector
            Picker("View", selection: $selectedTab) {
                Text("Metrics").tag(0)
                Text("Health").tag(1)
                Text("Events").tag(2)
            }
            .pickerStyle(.segmented)
            .padding()

            // Content
            TabView(selection: $selectedTab) {
                MetricsTab(monitor: monitor)
                    .tag(0)

                HealthTab(monitor: monitor)
                    .tag(1)

                EventsTab(monitor: monitor)
                    .tag(2)
            }
            .tabViewStyle(.automatic)
        }
        .frame(minWidth: 700, minHeight: 600)
        .onAppear {
            monitor.startMonitoring()
        }
        .onDisappear {
            monitor.stopMonitoring()
        }
    }
}

// MARK: - Metrics Tab
struct MetricsTab: View {
    @ObservedObject var monitor: RemediationMonitor

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Quick stats grid
                LazyVGrid(
                    columns: [
                        GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible()),
                        GridItem(.flexible()),
                    ], spacing: 16
                ) {
                    MetricCard(
                        title: "Requested",
                        value: "\(monitor.metrics.requested)",
                        icon: "arrow.up.circle.fill",
                        color: .blue,
                        subtitle: "Total remediation requests"
                    )

                    MetricCard(
                        title: "Completed",
                        value: "\(monitor.metrics.completed)",
                        icon: "checkmark.circle.fill",
                        color: .green,
                        subtitle: "Successfully processed"
                    )

                    MetricCard(
                        title: "Promoted",
                        value: "\(monitor.metrics.promoted)",
                        icon: "arrow.up.right.circle.fill",
                        color: .green,
                        subtitle: "Deployed to production"
                    )

                    MetricCard(
                        title: "Rolled Back",
                        value: "\(monitor.metrics.rolledBack)",
                        icon: "arrow.uturn.backward.circle.fill",
                        color: .orange,
                        subtitle: "Reverted due to failures"
                    )
                }

                // Success rate gauge
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Image(systemName: "gauge.high")
                            .foregroundColor(.purple)
                            .font(.title2)
                        Text("Success Rate")
                            .font(.title2.bold())
                        Spacer()
                        Text(String(format: "%.1f%%", monitor.metrics.successRate * 100))
                            .font(.system(size: 36, weight: .bold, design: .rounded))
                            .foregroundColor(
                                monitor.metrics.successRate > 0.7
                                    ? .green : monitor.metrics.successRate > 0.5 ? .orange : .red)
                    }

                    GeometryReader { geometry in
                        ZStack(alignment: .leading) {
                            // Background
                            RoundedRectangle(cornerRadius: 8)
                                .fill(Color.gray.opacity(0.2))
                                .frame(height: 40)

                            // Fill
                            RoundedRectangle(cornerRadius: 8)
                                .fill(
                                    LinearGradient(
                                        colors: [
                                            monitor.metrics.successRate > 0.7 ? .green : .orange,
                                            monitor.metrics.successRate > 0.7
                                                ? .green.opacity(0.7) : .orange.opacity(0.7),
                                        ],
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                                .frame(
                                    width: geometry.size.width * monitor.metrics.successRate,
                                    height: 40)
                        }
                    }
                    .frame(height: 40)

                    HStack {
                        Text("Target: >70%")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text(
                            monitor.metrics.completed > 0
                                ? "Based on \(monitor.metrics.completed) remediations"
                                : "No data yet"
                        )
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    }
                }
                .padding()
                .background(Color(NSColor.controlBackgroundColor))
                .cornerRadius(12)

                // Detailed metrics
                VStack(alignment: .leading, spacing: 8) {
                    Text("Detailed Metrics")
                        .font(.headline)

                    MetricDetailRow(
                        label: "Started", value: monitor.metrics.started, icon: "play.circle")
                    MetricDetailRow(
                        label: "Failed", value: monitor.metrics.failed, icon: "xmark.circle",
                        color: .red)
                    MetricDetailRow(
                        label: "Rollback Rate",
                        value: String(format: "%.1f%%", monitor.metrics.rollbackRate * 100),
                        icon: "arrow.uturn.backward", color: .orange)
                }
                .padding()
                .background(Color(NSColor.controlBackgroundColor))
                .cornerRadius(12)
            }
            .padding()
        }
    }
}

// MARK: - Health Tab
struct HealthTab: View {
    @ObservedObject var monitor: RemediationMonitor

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                // Service health cards
                ServiceHealthCard(
                    name: "Remediator",
                    port: 9112,
                    status: monitor.services.remediator,
                    description: "Auto-remediation engine"
                )

                ServiceHealthCard(
                    name: "Orchestrator",
                    port: 9110,
                    status: monitor.services.orchestrator,
                    description: "Verdict processor and event publisher"
                )

                ServiceHealthCard(
                    name: "Prometheus",
                    port: 9090,
                    status: monitor.services.prometheus,
                    description: "Metrics aggregation and storage"
                )

                // System status
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Image(systemName: "server.rack")
                            .foregroundColor(.blue)
                        Text("System Status")
                            .font(.headline)
                    }

                    let allHealthy =
                        monitor.services.remediator == .healthy
                        && monitor.services.orchestrator == .healthy
                        && monitor.services.prometheus == .healthy

                    HStack {
                        Image(
                            systemName: allHealthy
                                ? "checkmark.shield.fill" : "exclamationmark.shield.fill"
                        )
                        .foregroundColor(allHealthy ? .green : .orange)
                        .font(.title2)

                        VStack(alignment: .leading) {
                            Text(allHealthy ? "All Systems Operational" : "Some Services Degraded")
                                .font(.headline)
                            Text(
                                allHealthy
                                    ? "Auto-remediation loop active"
                                    : "Check service logs for details"
                            )
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        }
                    }
                    .padding()
                    .background(allHealthy ? Color.green.opacity(0.1) : Color.orange.opacity(0.1))
                    .cornerRadius(8)
                }
                .padding()
                .background(Color(NSColor.controlBackgroundColor))
                .cornerRadius(12)
            }
            .padding()
        }
    }
}

// MARK: - Events Tab
struct EventsTab: View {
    @ObservedObject var monitor: RemediationMonitor

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Image(systemName: "clock.arrow.circlepath")
                        .foregroundColor(.blue)
                    Text("Recent Remediation Events")
                        .font(.headline)
                    Spacer()
                    Text("Last 24 hours")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                if monitor.recentEvents.isEmpty {
                    VStack(spacing: 8) {
                        Image(systemName: "tray")
                            .font(.system(size: 48))
                            .foregroundStyle(.tertiary)
                        Text("No recent events")
                            .font(.title3)
                            .foregroundStyle(.secondary)
                        Text("System is stable - no remediations needed")
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(40)
                } else {
                    ForEach(monitor.recentEvents) { event in
                        EventCard(event: event)
                    }
                }
            }
            .padding()
        }
    }
}

// MARK: - Component Views

struct MetricCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    let subtitle: String

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 40))
                .foregroundColor(color)

            Text(value)
                .font(.system(size: 32, weight: .bold, design: .rounded))

            VStack(spacing: 2) {
                Text(title)
                    .font(.subheadline.bold())
                Text(subtitle)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(12)
    }
}

struct MetricDetailRow: View {
    let label: String
    let value: Any
    let icon: String
    var color: Color = .primary

    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(color)
                .frame(width: 20)
            Text(label)
            Spacer()
            Text("\(value)")
                .font(.system(.body, design: .monospaced))
                .bold()
        }
        .padding(.vertical, 4)
    }
}

struct ServiceHealthCard: View {
    let name: String
    let port: Int
    let status: ServiceStatus
    let description: String

    var body: some View {
        HStack {
            // Status indicator
            ZStack {
                Circle()
                    .fill(statusColor.opacity(0.2))
                    .frame(width: 50, height: 50)
                Circle()
                    .fill(statusColor)
                    .frame(width: 20, height: 20)
            }

            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(name)
                        .font(.headline)
                    Text(":\(port)")
                        .font(.system(.caption, design: .monospaced))
                        .foregroundStyle(.secondary)
                }
                Text(description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(status.rawValue.uppercased())
                    .font(.caption.bold())
                    .foregroundColor(statusColor)
            }

            Spacer()

            Image(systemName: statusIcon)
                .font(.title2)
                .foregroundColor(statusColor)
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(12)
    }

    var statusColor: Color {
        switch status {
        case .healthy: return .green
        case .unhealthy: return .red
        case .unknown: return .gray
        }
    }

    var statusIcon: String {
        switch status {
        case .healthy: return "checkmark.circle.fill"
        case .unhealthy: return "exclamationmark.triangle.fill"
        case .unknown: return "questionmark.circle"
        }
    }
}

struct EventCard: View {
    let event: RemediationEvent

    var body: some View {
        HStack(spacing: 12) {
            // Decision indicator
            ZStack {
                Circle()
                    .fill(decisionColor.opacity(0.2))
                    .frame(width: 40, height: 40)
                Image(systemName: decisionIcon)
                    .foregroundColor(decisionColor)
            }

            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(event.decision)
                        .font(.headline)
                    Spacer()
                    Text(event.timestamp, style: .relative)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Text("Plan: \(event.planId)")
                    .font(.system(.caption, design: .monospaced))
                    .foregroundStyle(.secondary)
            }

            Spacer()
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
    }

    var decisionColor: Color {
        switch event.decision {
        case "PROMOTE": return .green
        case "ROLLBACK": return .orange
        case "HOLD": return .blue
        default: return .gray
        }
    }

    var decisionIcon: String {
        switch event.decision {
        case "PROMOTE": return "arrow.up.right.circle.fill"
        case "ROLLBACK": return "arrow.uturn.backward.circle.fill"
        case "HOLD": return "pause.circle.fill"
        default: return "circle"
        }
    }
}

// MARK: - Data Models

struct RemediationEvent: Identifiable, Codable {
    let id = UUID()
    let planId: String
    let decision: String
    let timestamp: Date
}

enum ServiceStatus: String {
    case healthy, unhealthy, unknown
}

struct RemediationMetrics {
    var requested: Int = 0
    var started: Int = 0
    var completed: Int = 0
    var promoted: Int = 0
    var rolledBack: Int = 0
    var failed: Int = 0

    var successRate: Double {
        guard completed > 0 else { return 0.0 }
        return Double(promoted) / Double(completed)
    }

    var rollbackRate: Double {
        guard completed > 0 else { return 0.0 }
        return Double(rolledBack) / Double(completed)
    }
}

struct ServiceHealth {
    var remediator: ServiceStatus = .unknown
    var orchestrator: ServiceStatus = .unknown
    var prometheus: ServiceStatus = .unknown
}

// MARK: - Monitor
@MainActor
final class RemediationMonitor: ObservableObject {
    @Published var metrics = RemediationMetrics()
    @Published var services = ServiceHealth()
    @Published var recentEvents: [RemediationEvent] = []
    @Published var isConnected = false

    private var timer: Timer?
    private let baseURL = "http://localhost:9112"

    func startMonitoring() {
        NSLog("[RemediationMonitor] Starting monitoring of \(baseURL)")
        refresh()

        timer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.refresh()
            }
        }
    }

    func stopMonitoring() {
        NSLog("[RemediationMonitor] Stopping monitoring")
        timer?.invalidate()
        timer = nil
    }

    func refresh() {
        Task {
            await fetchMetrics()
            await checkServiceHealth()
        }
    }

    func fetchMetrics() async {
        guard let url = URL(string: "\(baseURL)/metrics") else { return }

        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let text = String(data: data, encoding: .utf8) ?? ""

            // Parse Prometheus metrics
            metrics.requested = parseMetric(text, name: "governance_remediations_requested_total")
            metrics.started = parseMetric(text, name: "governance_remediations_started_total")
            metrics.completed = parseMetric(text, name: "governance_remediations_completed_total")
            metrics.promoted = parseMetric(text, name: "governance_remediations_promoted_total")
            metrics.rolledBack = parseMetric(
                text, name: "governance_remediations_rolled_back_total")
            metrics.failed = parseMetric(text, name: "governance_remediations_failed_total")

            isConnected = true
            NSLog(
                "[RemediationMonitor] Metrics updated: requested=\(metrics.requested), completed=\(metrics.completed)"
            )

        } catch {
            NSLog("[RemediationMonitor] Error fetching metrics: \(error)")
            isConnected = false
        }
    }

    func checkServiceHealth() async {
        services.remediator = await checkHealth(port: 9112)
        services.orchestrator = await checkHealth(port: 9110)
        services.prometheus = await checkHealth(port: 9090, path: "/-/healthy")
    }

    private func checkHealth(port: Int, path: String = "/health") async -> ServiceStatus {
        guard let url = URL(string: "http://localhost:\(port)\(path)") else {
            return .unknown
        }

        do {
            let (_, response) = try await URLSession.shared.data(from: url)
            if let httpResponse = response as? HTTPURLResponse {
                return httpResponse.statusCode == 200 ? .healthy : .unhealthy
            }
            return .unknown
        } catch {
            return .unhealthy
        }
    }

    private func parseMetric(_ text: String, name: String) -> Int {
        let lines = text.components(separatedBy: .newlines)
        for line in lines {
            if line.hasPrefix(name), !line.hasPrefix("#") {
                let parts = line.components(separatedBy: .whitespaces)
                if let value = parts.last, let intValue = Int(value) {
                    return intValue
                }
            }
        }
        return 0
    }
}
