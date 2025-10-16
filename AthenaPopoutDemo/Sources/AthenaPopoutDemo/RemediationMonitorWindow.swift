import SwiftUI

/// Remediation Monitor Window
/// Displays live auto-remediation metrics from the deployed system
struct RemediationMonitorWindow: View {
    @StateObject private var monitor = RemediationMonitor()
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Image(systemName: "bolt.fill")
                    .foregroundColor(.orange)
                    .font(.title2)
                Text("Auto-Remediation Monitor")
                    .font(.title2.bold())
                Spacer()
                Circle()
                    .fill(monitor.isConnected ? Color.green : Color.red)
                    .frame(width: 12, height: 12)
                Text(monitor.isConnected ? "LIVE" : "OFFLINE")
                    .font(.caption.bold())
                    .foregroundColor(monitor.isConnected ? .green : .red)
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
            
            Divider()
            
            // Metrics Grid
            ScrollView {
                VStack(spacing: 16) {
                    // Quick Stats
                    HStack(spacing: 16) {
                        MetricCard(
                            title: "Requested",
                            value: "\(monitor.metrics.requested)",
                            icon: "arrow.up.circle.fill",
                            color: .blue
                        )
                        
                        MetricCard(
                            title: "Completed",
                            value: "\(monitor.metrics.completed)",
                            icon: "checkmark.circle.fill",
                            color: .green
                        )
                        
                        MetricCard(
                            title: "Promoted",
                            value: "\(monitor.metrics.promoted)",
                            icon: "arrow.up.right.circle.fill",
                            color: .green
                        )
                        
                        MetricCard(
                            title: "Rolled Back",
                            value: "\(monitor.metrics.rolledBack)",
                            icon: "arrow.uturn.backward.circle.fill",
                            color: .orange
                        )
                    }
                    
                    // Success Rate
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Image(systemName: "chart.line.uptrend.xyaxis")
                                .foregroundColor(.purple)
                            Text("Success Rate")
                                .font(.headline)
                            Spacer()
                            Text(String(format: "%.1f%%", monitor.metrics.successRate * 100))
                                .font(.title2.bold())
                                .foregroundColor(monitor.metrics.successRate > 0.7 ? .green : .orange)
                        }
                        
                        ProgressView(value: monitor.metrics.successRate, total: 1.0)
                            .tint(monitor.metrics.successRate > 0.7 ? .green : .orange)
                    }
                    .padding()
                    .background(Color(NSColor.controlBackgroundColor))
                    .cornerRadius(8)
                    
                    // Recent Events
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Image(systemName: "list.bullet.rectangle")
                                .foregroundColor(.blue)
                            Text("Recent Events")
                                .font(.headline)
                            Spacer()
                            Button(action: { monitor.refresh() }) {
                                Image(systemName: "arrow.clockwise")
                            }
                            .buttonStyle(.plain)
                        }
                        
                        if monitor.recentEvents.isEmpty {
                            Text("No recent remediation events")
                                .foregroundStyle(.secondary)
                                .padding(.vertical, 8)
                        } else {
                            ForEach(monitor.recentEvents) { event in
                                EventRow(event: event)
                            }
                        }
                    }
                    .padding()
                    .background(Color(NSColor.controlBackgroundColor))
                    .cornerRadius(8)
                    
                    // Service Health
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Image(systemName: "heart.fill")
                                .foregroundColor(.pink)
                            Text("Service Health")
                                .font(.headline)
                        }
                        
                        ServiceHealthRow(name: "Remediator", port: 9112, status: monitor.services.remediator)
                        ServiceHealthRow(name: "Orchestrator", port: 9110, status: monitor.services.orchestrator)
                        ServiceHealthRow(name: "Prometheus", port: 9090, status: monitor.services.prometheus)
                    }
                    .padding()
                    .background(Color(NSColor.controlBackgroundColor))
                    .cornerRadius(8)
                }
                .padding()
            }
        }
        .frame(minWidth: 600, minHeight: 500)
        .onAppear {
            monitor.startMonitoring()
        }
        .onDisappear {
            monitor.stopMonitoring()
        }
    }
}

struct MetricCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title)
                .foregroundColor(color)
            Text(value)
                .font(.title.bold())
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
    }
}

struct EventRow: View {
    let event: RemediationEvent
    
    var body: some View {
        HStack {
            Circle()
                .fill(event.decision == "PROMOTE" ? Color.green : event.decision == "ROLLBACK" ? Color.orange : Color.gray)
                .frame(width: 8, height: 8)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(event.decision)
                    .font(.system(.body, design: .monospaced))
                    .bold()
                Text("Plan: \(event.planId)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            
            Spacer()
            
            Text(event.timestamp, style: .relative)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
    }
}

struct ServiceHealthRow: View {
    let name: String
    let port: Int
    let status: ServiceStatus
    
    var body: some View {
        HStack {
            Circle()
                .fill(status == .healthy ? Color.green : status == .unhealthy ? Color.red : Color.gray)
                .frame(width: 8, height: 8)
            
            Text(name)
                .font(.body)
            
            Spacer()
            
            Text(":\(port)")
                .font(.system(.caption, design: .monospaced))
                .foregroundStyle(.secondary)
            
            Text(status.rawValue.uppercased())
                .font(.caption.bold())
                .foregroundColor(status == .healthy ? .green : status == .unhealthy ? .red : .gray)
        }
        .padding(.vertical, 2)
    }
}

// MARK: - Data Models

struct RemediationEvent: Identifiable {
    let id = UUID()
    let planId: String
    let decision: String
    let timestamp: Date
}

enum ServiceStatus: String {
    case healthy = "healthy"
    case unhealthy = "unhealthy"
    case unknown = "unknown"
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
}

struct ServiceHealth {
    var remediator: ServiceStatus = .unknown
    var orchestrator: ServiceStatus = .unknown
    var prometheus: ServiceStatus = .unknown
}

// MARK: - Monitor Class

@MainActor
final class RemediationMonitor: ObservableObject {
    @Published var metrics = RemediationMetrics()
    @Published var services = ServiceHealth()
    @Published var recentEvents: [RemediationEvent] = []
    @Published var isConnected = false
    
    private var timer: Timer?
    
    func startMonitoring() {
        print("[RemediationMonitor] Starting monitoring...")
        refresh()
        
        // Poll every 5 seconds
        timer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.refresh()
            }
        }
    }
    
    func stopMonitoring() {
        print("[RemediationMonitor] Stopping monitoring...")
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
        guard let url = URL(string: "http://localhost:9112/metrics") else { return }
        
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let text = String(data: data, encoding: .utf8) ?? ""
            
            // Parse Prometheus metrics
            metrics.requested = parseMetric(text, name: "governance_remediations_requested_total")
            metrics.started = parseMetric(text, name: "governance_remediations_started_total")
            metrics.completed = parseMetric(text, name: "governance_remediations_completed_total")
            metrics.promoted = parseMetric(text, name: "governance_remediations_promoted_total")
            metrics.rolledBack = parseMetric(text, name: "governance_remediations_rolled_back_total")
            metrics.failed = parseMetric(text, name: "governance_remediations_failed_total")
            
            isConnected = true
            
        } catch {
            print("[RemediationMonitor] Error fetching metrics: \(error)")
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
        // Parse Prometheus format: metric_name value
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

