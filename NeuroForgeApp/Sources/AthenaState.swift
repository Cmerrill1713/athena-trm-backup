import Combine
import Foundation

@MainActor
final class AthenaState: ObservableObject {
    @Published var lastAlert: CriticalAlert?
    @Published var lastCase: TribunalCase?
    @Published var lastEmergency: SystemEmergency?

    // MARK: - Governance State
    @Published var governanceMode: GovernanceMode = .shadow
    @Published var isOrchestratorHealthy = false
    @Published var kpis = GovernanceKPIs.empty
    @Published var governanceAlerts: [GovernanceAlert] = []
    @Published var lastVerdictStatus: String = ""
    @Published var lastError: String?

    private var refreshTimer: Timer?
    private let apiClient = GovernanceAPIClient()

    func trigger(_ alert: CriticalAlert) {
        self.lastAlert = alert
        NotificationCenter.default.post(name: .ShowCriticalAlert, object: alert)
    }

    func trigger(_ tribunal: TribunalCase) {
        self.lastCase = tribunal
        NotificationCenter.default.post(name: .ShowTribunalDecision, object: tribunal)
    }

    func trigger(_ emergency: SystemEmergency) {
        self.lastEmergency = emergency
        NotificationCenter.default.post(name: .ShowSystemEmergency, object: emergency)
    }

    // MARK: - Governance Methods

    func startGovernanceMonitoring() {
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { [weak self] _ in
            Task { await self?.refreshGovernance() }
        }
        Task { await refreshGovernance() }
    }

    func stopGovernanceMonitoring() {
        refreshTimer?.invalidate()
        refreshTimer = nil
    }

    func refreshGovernance() async {
        await checkOrchestratorHealth()
        await refreshKPIs()
        updateAlerts()
    }

    func checkOrchestratorHealth() async {
        isOrchestratorHealthy = await apiClient.checkHealth()
    }

    func refreshKPIs() async {
        kpis = await apiClient.fetchKPIs()
    }

    func setGovernanceMode(_ mode: GovernanceMode) async {
        do {
            try await apiClient.setMode(mode)
            governanceMode = mode
            lastError = nil
        } catch {
            lastError = "Mode switch failed: \(error.localizedDescription)"
        }
    }

    func sendTestVerdict(verdict: String, ecePost: Double, entropy: Double, actions: [String]) async
    {
        let taskId = "ui-test-\(Int(Date().timeIntervalSince1970))"
        let iso = ISO8601DateFormatter().string(from: Date())

        let payload = VerdictPayload(
            task_id: taskId,
            verdict: verdict,
            ece_post: ecePost,
            entropy: entropy,
            actions: actions,
            ts: iso
        )

        do {
            let response = try await apiClient.sendVerdict(payload)
            lastVerdictStatus = response.status
            lastError = nil
            await refreshKPIs()
        } catch {
            lastError = "Verdict failed: \(error.localizedDescription)"
        }
    }

    private func updateAlerts() {
        var alerts: [GovernanceAlert] = []

        // Check ECE
        if kpis.ece > 0.08 {
            alerts.append(
                GovernanceAlert(
                    message: "ECE Critical (>0.08) - Immediate rollback recommended",
                    severity: .critical
                ))
        } else if kpis.ece > 0.06 {
            alerts.append(
                GovernanceAlert(
                    message: "ECE Warning (>0.06) - Monitor closely",
                    severity: .warning
                ))
        }

        // Check Entropy
        if kpis.entropy >= 0.25 {
            alerts.append(
                GovernanceAlert(
                    message: "Entropy Drift Critical (≥0.25) - Rollback required",
                    severity: .critical
                ))
        }

        // Check Hard Fails
        if kpis.hard_fails_5m > 0 {
            alerts.append(
                GovernanceAlert(
                    message: "\(kpis.hard_fails_5m) HARD_FAIL verdict(s) in last 5 minutes",
                    severity: .warning
                ))
        }

        // Check orchestrator health
        if !isOrchestratorHealthy {
            alerts.append(
                GovernanceAlert(
                    message: "Governance Orchestrator is DOWN",
                    severity: .critical
                ))
        }

        governanceAlerts = alerts
    }
}
