import Foundation
import OSLog
import SwiftUI

// MARK: - Governance View Model

@MainActor
final class GovernanceViewModel: ObservableObject {

    // MARK: - Published State

    @Published var healthStatus: HealthStatus = .unknown
    @Published var statusMessage: String = "Initializing..."
    @Published var verdictCounts: [String: Int] = [:]
    @Published var remediationMetrics: GovernanceClient.RemediationMetrics?
    @Published var isLoading: Bool = false
    @Published var lastError: String?
    @Published var lastVerdict: VerdictResponse?
    @Published var pendingVerdicts: [VerdictRequest] = []

    // MARK: - Configuration

    @Published var autoRefresh: Bool = true
    @Published var refreshInterval: TimeInterval = 5.0

    // MARK: - Dependencies

    private let client: GovernanceClient
    private let logger = Logger(subsystem: "com.athena.neuroforge", category: "governance.ui")

    private var refreshTimer: Timer?
    private let pendingQueuePath: URL

    // MARK: - Health Status

    enum HealthStatus: String {
        case unknown = "⚪️"
        case healthy = "🟢"
        case degraded = "🟡"
        case down = "🔴"

        var color: Color {
            switch self {
            case .unknown: return .gray
            case .healthy: return .green
            case .degraded: return .yellow
            case .down: return .red
            }
        }
    }

    // MARK: - Initialization

    init(client: GovernanceClient? = nil) {
        self.client = client ?? GovernanceClient()

        // Setup pending queue path
        let appSupport = FileManager.default.urls(
            for: .applicationSupportDirectory,
            in: .userDomainMask
        ).first!
        let athenaDir = appSupport.appendingPathComponent("Athena")
        try? FileManager.default.createDirectory(at: athenaDir, withIntermediateDirectories: true)
        self.pendingQueuePath = athenaDir.appendingPathComponent("PendingVerdicts.jsonl")

        // Load pending verdicts
        loadPendingVerdicts()

        // Start auto-refresh if enabled
        if autoRefresh {
            startAutoRefresh()
        }

        // Initial health check
        Task {
            await checkHealth()
        }
    }

    deinit {
        // Timer will be cleaned up automatically
        // Note: Can't call @MainActor methods from deinit
    }

    // MARK: - Health Check

    func checkHealth() async {
        logger.info("Checking governance orchestrator health")

        do {
            let isHealthy = try await client.health()

            if isHealthy {
                healthStatus = .healthy
                statusMessage = "🟢 Orchestrator healthy"
                logger.info("Health check: UP")

                // Flush pending verdicts if we're back online
                if !pendingVerdicts.isEmpty {
                    await flushPendingVerdicts()
                }
            } else {
                healthStatus = .down
                statusMessage = "🔴 Orchestrator unavailable"
                logger.warning("Health check: DOWN")
            }

            lastError = nil
        } catch {
            healthStatus = .down
            statusMessage = "🔴 Connection error"
            lastError = error.localizedDescription
            logger.error("Health check failed: \(error.localizedDescription)")
        }
    }

    func checkHealthDetailed() async {
        do {
            let health = try await client.healthDetailed()
            healthStatus = .healthy
            statusMessage = "🟢 \(health.service ?? "orchestrator") - \(health.status ?? "OK")"
            if let version = health.version {
                statusMessage += " (v\(version))"
            }
        } catch {
            healthStatus = .down
            statusMessage = "🔴 \(error.localizedDescription)"
            lastError = error.localizedDescription
        }
    }

    // MARK: - Metrics

    func refreshMetrics() async {
        guard healthStatus == .healthy else {
            logger.info("Skipping metrics refresh (orchestrator down)")
            return
        }

        isLoading = true
        defer { isLoading = false }

        do {
            let summary = try await client.metricsSummary()
            verdictCounts = summary.verdicts
            remediationMetrics = summary.remediations

            let totalVerdicts = verdictCounts.values.reduce(0, +)
            logger.info("Metrics refreshed: \(totalVerdicts) total verdicts")
        } catch {
            logger.error("Failed to refresh metrics: \(error.localizedDescription)")
            lastError = "Metrics error: \(error.localizedDescription)"
        }
    }

    // MARK: - Verdict Submission

    func sendDemoVerdict() async {
        let taskId = "ui-demo-\(Int(Date().timeIntervalSince1970))"
        let verdict = VerdictRequest(
            taskId: taskId,
            verdict: "PASS",
            ecePost: 0.04,
            entropy: 0.03,
            actions: ["PROMOTE"]
        )

        await sendVerdict(verdict)
    }

    func sendVerdict(_ verdict: VerdictRequest) async {
        guard healthStatus == .healthy else {
            logger.warning("Cannot send verdict: orchestrator down. Queuing for later.")
            queueVerdict(verdict)
            statusMessage = "🟡 Verdict queued (orchestrator offline)"
            return
        }

        isLoading = true
        defer { isLoading = false }

        logger.info("Sending verdict: \(verdict.task_id) - \(verdict.verdict)")

        do {
            let response = try await retryWithJitter {
                try await self.client.postVerdict(verdict)
            }

            lastVerdict = response
            statusMessage = "✅ Verdict: \(response.status)"

            if response.status.contains("idempotent") || response.status.contains("skip") {
                logger.info("Verdict was idempotent: \(verdict.task_id)")
                statusMessage = "ℹ️ Verdict idempotent (already processed)"
            } else {
                logger.info("Verdict applied: \(verdict.task_id)")
            }

            lastError = nil

            // Refresh metrics to show updated counts
            await refreshMetrics()

        } catch let error as GovernanceError {
            lastError = error.errorDescription
            statusMessage = "❌ \(error.errorDescription ?? "Unknown error")"
            logger.error("Verdict failed: \(error.errorDescription ?? "unknown")")

            // Queue for retry if transport error
            if case .transport = error {
                queueVerdict(verdict)
                statusMessage += " (queued for retry)"
            }
        } catch {
            lastError = error.localizedDescription
            statusMessage = "❌ Error: \(error.localizedDescription)"
            logger.error("Verdict failed: \(error.localizedDescription)")
        }
    }

    func sendCustomVerdict(taskId: String, verdict: String, actions: [String]) async {
        let request = VerdictRequest(
            taskId: taskId,
            verdict: verdict,
            ecePost: Double.random(in: 0.03...0.08),
            entropy: Double.random(in: 0.02...0.05),
            actions: actions.isEmpty ? nil : actions
        )

        await sendVerdict(request)
    }

    // MARK: - Retry Logic

    private func retryWithJitter<T>(maxAttempts: Int = 3, operation: @escaping () async throws -> T)
        async throws -> T
    {
        var lastError: Error?

        for attempt in 1...maxAttempts {
            do {
                return try await operation()
            } catch {
                lastError = error

                if attempt < maxAttempts {
                    let jitterMs = Int.random(in: 200...800)
                    logger.info("Retry \(attempt)/\(maxAttempts) after \(jitterMs)ms")
                    try? await Task.sleep(nanoseconds: UInt64(jitterMs) * 1_000_000)
                }
            }
        }

        logger.error("All \(maxAttempts) attempts failed")
        throw lastError ?? GovernanceError.timeout
    }

    // MARK: - Pending Queue

    private func queueVerdict(_ verdict: VerdictRequest) {
        pendingVerdicts.append(verdict)
        savePendingVerdicts()
        logger.info("Queued verdict: \(verdict.task_id)")
    }

    private func flushPendingVerdicts() async {
        guard !self.pendingVerdicts.isEmpty else { return }

        logger.info("Flushing \(self.pendingVerdicts.count) pending verdicts")
        statusMessage = "⏳ Flushing \(self.pendingVerdicts.count) queued verdicts..."

        let toFlush = self.pendingVerdicts
        self.pendingVerdicts.removeAll()
        savePendingVerdicts()

        for verdict in toFlush {
            do {
                _ = try await client.postVerdict(verdict)
                logger.info("Flushed verdict: \(verdict.task_id)")
            } catch {
                logger.error(
                    "Failed to flush verdict \(verdict.task_id): \(error.localizedDescription)")
                // Re-queue if failed
                pendingVerdicts.append(verdict)
            }
        }

        savePendingVerdicts()

        if pendingVerdicts.isEmpty {
            statusMessage = "✅ All queued verdicts flushed"
        } else {
            statusMessage = "⚠️ \(pendingVerdicts.count) verdicts still pending"
        }
    }

    private func savePendingVerdicts() {
        do {
            let encoder = JSONEncoder()
            let lines = try self.pendingVerdicts.map { verdict in
                try encoder.encode(verdict)
            }
            let jsonl = lines.map { String(data: $0, encoding: .utf8)! }.joined(separator: "\n")
            try jsonl.write(to: pendingQueuePath, atomically: true, encoding: .utf8)
            logger.debug("Saved \(self.pendingVerdicts.count) pending verdicts")
        } catch {
            logger.error("Failed to save pending verdicts: \(error.localizedDescription)")
        }
    }

    private func loadPendingVerdicts() {
        guard FileManager.default.fileExists(atPath: pendingQueuePath.path) else {
            return
        }

        do {
            let jsonl = try String(contentsOf: pendingQueuePath, encoding: .utf8)
            let decoder = JSONDecoder()
            self.pendingVerdicts = jsonl.split(separator: "\n").compactMap { line in
                guard let data = String(line).data(using: .utf8) else { return nil }
                return try? decoder.decode(VerdictRequest.self, from: data)
            }
            logger.info("Loaded \(self.pendingVerdicts.count) pending verdicts")
        } catch {
            logger.error("Failed to load pending verdicts: \(error.localizedDescription)")
        }
    }

    // MARK: - Auto-refresh

    func startAutoRefresh() {
        stopAutoRefresh()

        refreshTimer = Timer.scheduledTimer(withTimeInterval: self.refreshInterval, repeats: true) {
            [weak self] _ in
            Task { @MainActor in
                await self?.checkHealth()
                await self?.refreshMetrics()
            }
        }

        logger.info("Auto-refresh started (interval: \(self.refreshInterval)s)")
    }

    func stopAutoRefresh() {
        refreshTimer?.invalidate()
        refreshTimer = nil
        logger.info("Auto-refresh stopped")
    }

    // MARK: - Manual Actions

    func refresh() async {
        await checkHealth()
        await refreshMetrics()
    }
}
