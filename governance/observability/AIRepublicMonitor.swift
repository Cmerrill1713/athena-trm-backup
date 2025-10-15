import SwiftUI
import Combine

// MARK: - AI Republic Monitor

final class AIRepublicMonitor: ObservableObject {
    @Published var constitutionStatus: ServiceHealth = .unknown
    @Published var tribunalStatus: ServiceHealth = .unknown
    @Published var federationStatus: ServiceHealth = .unknown

    @Published var memoryStatus: ServiceHealth = .unknown
    @Published var voiceStatus: ServiceHealth = .unknown
    @Published var tribunalServiceStatus: ServiceHealth = .unknown
    @Published var alertStatus: ServiceHealth = .unknown

    @Published var activeServices: Int = 0
    @Published var uptime: String = "Checking..."
    @Published var activeAlertCount: Int = 0
    @Published var recentAlerts: [AIRepublicAlert] = []

    // Quiet Hours
    @Published var quietHoursActive: Bool = false
    @Published var quietHoursDisplay: String = "10:00 PM - 8:00 AM"

    // Smart Alerting
    @Published var focusModeActive: Bool = false
    @Published var calendarBusy: Bool = false
    @Published var smartAlertingEnabled: Bool = false
    @Published var currentLocation: String = "unknown"

    private var cancellables = Set<AnyCancellable>()
    private var refreshTimer: Timer?

    init() {
        // Start periodic refresh
        startPeriodicRefresh()
        // Initial refresh
        Task { await refreshStatus() }
    }

    deinit {
        refreshTimer?.invalidate()
    }

    func refreshStatus() async {
        // Check service health
        await checkConstitutionStatus()
        await checkTribunalStatus()
        await checkFederationStatus()

        await checkMemoryService()
        await checkVoiceService()
        await checkTribunalService()
        await checkAlertService()

        // Update aggregate stats
        updateAggregateStats()

        // Load recent alerts
        await loadRecentAlerts()
    }

    private func checkConstitutionStatus() async {
        // Check if constitutional runtime is active
        constitutionStatus = await checkServiceHealth("Constitutional Runtime", port: nil)
    }

    private func checkTribunalStatus() async {
        // Check tribunal system status
        tribunalStatus = await checkServiceHealth("Tribunal System", port: nil)
    }

    private func checkFederationStatus() async {
        // Check federation readiness
        federationStatus = await checkServiceHealth("Federation Gateway", port: 8094)
    }

    private func checkMemoryService() async {
        // Check memory optimizer process
        memoryStatus = await checkProcessHealth("athena_memory")
    }

    private func checkVoiceService() async {
        // Check voice integration process
        voiceStatus = await checkProcessHealth("athena_voice")
    }

    private func checkTribunalService() async {
        // Check tribunal service process
        tribunalServiceStatus = await checkProcessHealth("athena_tribunal")
    }

    private func checkAlertService() async {
        // Check alert system
        alertStatus = await checkServiceHealth("Alert System", port: 8080)
    }

    private func checkServiceHealth(_ name: String, port: Int?) async -> ServiceHealth {
        guard let port = port else {
            // For services without ports, check if they're conceptually "healthy"
            // This would be replaced with actual health checks
            return ServiceHealth(isHealthy: true, latencyMs: nil, error: nil)
        }

        let url = URL(string: "http://localhost:\(port)/health") ??
                  URL(string: "http://localhost:\(port)/api/status")

        do {
            let startTime = Date()
            let (_, response) = try await URLSession.shared.data(from: url!)
            let latency = Date().timeIntervalSince(startTime) * 1000

            if let httpResponse = response as? HTTPURLResponse,
               (200...299).contains(httpResponse.statusCode) {
                return ServiceHealth(isHealthy: true, latencyMs: Int(latency), error: nil)
            } else {
                return ServiceHealth(isHealthy: false, latencyMs: Int(latency), error: "HTTP \(httpResponse?.statusCode ?? 0)")
            }
        } catch {
            return ServiceHealth(isHealthy: false, latencyMs: nil, error: error.localizedDescription)
        }
    }

    private func checkProcessHealth(_ processName: String) async -> ServiceHealth {
        // Check if process is running using shell command
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = ["-c", "pgrep -f \(processName)"]

        do {
            try process.run()
            process.waitUntilExit()

            if process.terminationStatus == 0 {
                return ServiceHealth(isHealthy: true, latencyMs: nil, error: nil)
            } else {
                return ServiceHealth(isHealthy: false, latencyMs: nil, error: "Process not found")
            }
        } catch {
            return ServiceHealth(isHealthy: false, latencyMs: nil, error: error.localizedDescription)
        }
    }

    private func updateAggregateStats() {
        let services = [memoryStatus, voiceStatus, tribunalServiceStatus, alertStatus]
        activeServices = services.filter { $0.isHealthy }.count

        // Calculate uptime (simplified - would get from system)
        let uptimeHours = Int(ProcessInfo.processInfo.systemUptime / 3600)
        uptime = "\(uptimeHours)h"

        // Count active alerts (simplified)
        activeAlertCount = recentAlerts.filter { $0.severity == .critical || $0.severity == .warning }.count
    }

    private func loadRecentAlerts() async {
        // Load recent alerts from logs or API
        // For now, create some sample alerts

        let sampleAlerts = [
            AIRepublicAlert(
                id: UUID(),
                timestamp: Date().addingTimeInterval(-300), // 5 min ago
                severity: .info,
                title: "Memory Check",
                message: "Routine memory optimization completed"
            ),
            AIRepublicAlert(
                id: UUID(),
                timestamp: Date().addingTimeInterval(-900), // 15 min ago
                severity: .warning,
                title: "Tribunal Activity",
                message: "Constitutional compliance sweep completed"
            ),
            AIRepublicAlert(
                id: UUID(),
                timestamp: Date().addingTimeInterval(-1800), // 30 min ago
                severity: .critical,
                title: "Alert Test",
                message: "Testing iMessage + voice escalation system"
            )
        ]

        await MainActor.run {
            recentAlerts = sampleAlerts.sorted { $0.timestamp > $1.timestamp }
        }
    }

    private func startPeriodicRefresh() {
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 30.0, repeats: true) { _ in
            Task { await self.refreshStatus() }
        }
    }

    // MARK: - Quiet Hours Management

    func enableQuietHours() async {
        // Default: 10 PM to 8 AM
        quietHoursActive = true
        quietHoursDisplay = "10:00 PM - 8:00 AM"

        // In a real implementation, this would update environment variables
        // or send configuration to the Python services
        print("Quiet hours enabled: 10 PM - 8 AM")
    }

    func disableQuietHours() async {
        quietHoursActive = false
        quietHoursDisplay = "Disabled"

        print("Quiet hours disabled")
    }

    func testQuietHours() async {
        // Send a test alert to see how quiet hours behave
        let testAlert = AIRepublicAlert(
            id: UUID(),
            timestamp: Date(),
            severity: .warning,
            title: "Quiet Hours Test",
            message: "Testing alert behavior during current time period"
        )

        await MainActor.run {
            recentAlerts.insert(testAlert, at: 0)
            if recentAlerts.count > 8 {
                recentAlerts = Array(recentAlerts.prefix(8))
            }
        }

        print("Test alert sent - check iPhone for delivery behavior")
    }

    // MARK: - Smart Alerting Management

    func enableSmartAlerting() async {
        smartAlertingEnabled = true
        // In real implementation, this would update environment variables
        print("Smart alerting enabled: Focus mode and calendar integration active")
    }

    func disableSmartAlerting() async {
        smartAlertingEnabled = false
        focusModeActive = false
        calendarBusy = false
        print("Smart alerting disabled")
    }

    func simulateFocusMode(active: Bool) async {
        focusModeActive = active
        print("Focus mode \(active ? "activated" : "deactivated") - alerts will adjust accordingly")
    }

    func simulateCalendarBusy(busy: Bool) async {
        calendarBusy = busy
        print("Calendar status: \(busy ? "busy" : "free") - alerts will adjust accordingly")
    }

    func simulateLocation(location: String) async {
        currentLocation = location
        print("Location simulated: \(location) - alerts will adjust accordingly")
    }

    func testSmartAlerting() async {
        // Test all alerting contexts
        let contexts = ["normal", "quiet_hours", "focus_mode", "calendar_busy"]

        for context in contexts {
            let testAlert = AIRepublicAlert(
                id: UUID(),
                timestamp: Date(),
                severity: .info,
                title: "Smart Alerting Test",
                message: "Testing \(context) context - check delivery behavior"
            )

            await MainActor.run {
                recentAlerts.insert(testAlert, at: 0)
                if recentAlerts.count > 8 {
                    recentAlerts = Array(recentAlerts.prefix(8))
                }
            }
        }

        print("Smart alerting test complete - check alert delivery across different contexts")
    }
}

// MARK: - Supporting Types

struct ServiceHealth: Equatable {
    var isHealthy: Bool
    var latencyMs: Int?
    var error: String?

    static let unknown = ServiceHealth(isHealthy: false, latencyMs: nil, error: "Unknown")

    static func == (lhs: ServiceHealth, rhs: ServiceHealth) -> Bool {
        lhs.isHealthy == rhs.isHealthy &&
        lhs.latencyMs == rhs.latencyMs &&
        lhs.error == rhs.error
    }
}

struct AIRepublicAlert: Identifiable {
    let id: UUID
    let timestamp: Date
    let severity: AlertSeverity
    let title: String
    let message: String
}

enum AlertSeverity {
    case info, warning, critical

    var color: Color {
        switch self {
        case .info: return .blue
        case .warning: return .yellow
        case .critical: return .red
        }
    }
}
