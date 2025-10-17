import Foundation

// MARK: - Request/Response Models

struct VerdictRequest: Codable {
    let task_id: String
    let verdict: String // PASS | SOFT_FAIL | HARD_FAIL
    let ece_post: Double?
    let entropy: Double?
    let actions: [String]? // PROMOTE | QUARANTINE | ROLLBACK | HOLD | FREEZE
    let ts: String // ISO8601

    init(
        taskId: String, verdict: String, ecePost: Double? = nil, entropy: Double? = nil,
        actions: [String]? = nil
    ) {
        task_id = taskId
        self.verdict = verdict
        ece_post = ecePost
        self.entropy = entropy
        self.actions = actions
        ts = ISO8601DateFormatter().string(from: Date())
    }
}

struct VerdictResponse: Codable {
    let status: String
    let task_id: String?
    let generation: Int?
    let timestamp: String?
}

struct HealthResponse: Codable {
    let status: String?
    let service: String?
    let version: String?
}

// MARK: - Governance Errors

enum GovernanceError: Error, LocalizedError {
    case badStatus(Int)
    case decode(String)
    case transport(Error)
    case timeout
    case invalidURL
    case noData

    var errorDescription: String? {
        switch self {
        case let .badStatus(code):
            "HTTP \(code)"
        case let .decode(msg):
            "Decode error: \(msg)"
        case let .transport(error):
            "Transport: \(error.localizedDescription)"
        case .timeout:
            "Request timeout"
        case .invalidURL:
            "Invalid URL"
        case .noData:
            "No data received"
        }
    }
}

// MARK: - Governance Client

final class GovernanceClient: @unchecked Sendable {
    // MARK: - Configuration

    private let baseURL: URL
    private let session: URLSession
    private let timeout: TimeInterval

    init(baseURL: String? = nil, timeout: TimeInterval = 4.0) {
        let urlString =
            baseURL
                ?? ProcessInfo.processInfo.environment["GOV_URL"]
                ?? ProcessInfo.processInfo.environment["ATHENA_ORCHESTRATOR_URL"]
                ?? "http://localhost:9110"

        self.baseURL = URL(string: urlString)!
        self.timeout = timeout

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = timeout
        config.timeoutIntervalForResource = timeout * 2
        session = URLSession(configuration: config)
    }

    // MARK: - Health Check

    func health() async throws -> Bool {
        var request = URLRequest(url: baseURL.appendingPathComponent("/health"))
        request.httpMethod = "GET"
        request.timeoutInterval = timeout

        do {
            let (_, response) = try await session.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse else { return false }
            return (200 ..< 300).contains(httpResponse.statusCode)
        } catch {
            return false
        }
    }

    func healthDetailed() async throws -> HealthResponse {
        var request = URLRequest(url: baseURL.appendingPathComponent("/health"))
        request.httpMethod = "GET"
        request.timeoutInterval = timeout

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw GovernanceError.badStatus(-1)
        }

        guard (200 ..< 300).contains(httpResponse.statusCode) else {
            throw GovernanceError.badStatus(httpResponse.statusCode)
        }

        // Try to decode as JSON, fallback to simple status
        if let health = try? JSONDecoder().decode(HealthResponse.self, from: data) {
            return health
        } else {
            let status = String(data: data, encoding: .utf8) ?? "OK"
            return HealthResponse(status: status, service: "orchestrator", version: nil)
        }
    }

    // MARK: - Verdict Submission

    func postVerdict(_ verdict: VerdictRequest) async throws -> VerdictResponse {
        var request = URLRequest(url: baseURL.appendingPathComponent("/verdict"))
        request.httpMethod = "POST"
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = timeout

        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        request.httpBody = try encoder.encode(verdict)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw GovernanceError.badStatus(-1)
        }

        guard (200 ..< 300).contains(httpResponse.statusCode) else {
            throw GovernanceError.badStatus(httpResponse.statusCode)
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase

        guard let verdictResponse = try? decoder.decode(VerdictResponse.self, from: data) else {
            // Fallback: try to extract status from plain text or create generic response
            if let text = String(data: data, encoding: .utf8), !text.isEmpty {
                return VerdictResponse(
                    status: text.contains("applied") ? "applied" : "received",
                    task_id: verdict.task_id,
                    generation: nil,
                    timestamp: verdict.ts
                )
            }
            throw GovernanceError.decode("Could not decode verdict response")
        }

        return verdictResponse
    }

    // MARK: - Metrics

    func metricsRaw() async throws -> String {
        let url = baseURL.appendingPathComponent("/metrics")
        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw GovernanceError.badStatus(-1)
        }

        guard (200 ..< 300).contains(httpResponse.statusCode) else {
            throw GovernanceError.badStatus(httpResponse.statusCode)
        }

        return String(decoding: data, as: UTF8.self)
    }

    func verdictCounts() async throws -> [String: Int] {
        let metricsText = try await metricsRaw()
        return parseVerdictCounts(from: metricsText)
    }

    // MARK: - State

    func currentState() async throws -> String {
        let url = baseURL.appendingPathComponent("/state")
        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw GovernanceError.badStatus(-1)
        }

        guard (200 ..< 300).contains(httpResponse.statusCode) else {
            throw GovernanceError.badStatus(httpResponse.statusCode)
        }

        return String(decoding: data, as: UTF8.self)
    }

    // MARK: - Helpers

    private func parseVerdictCounts(from text: String) -> [String: Int] {
        var counts = [String: Int]()

        for line in text.split(separator: "\n") where line.contains("governance_verdicts_total") {
            // Format: governance_verdicts_total{verdict_type="pass"} 193
            let components = line.split(separator: "\"")
            guard components.count >= 2 else { continue }

            let verdictType = String(components[1])

            if let countStr = line.split(separator: " ").last,
               let count = Int(countStr) {
                counts[verdictType] = count
            }
        }

        return counts
    }
}

// MARK: - Metrics Parser Extensions

extension GovernanceClient {
    struct MetricsSummary: Codable {
        let verdicts: [String: Int]
        let remediations: RemediationMetrics
        let health: String
        let timestamp: Date
    }

    struct RemediationMetrics: Codable {
        let requested: Int
        let completed: Int
        let promoted: Int
        let rolledBack: Int
        let failed: Int
    }

    func metricsSummary() async throws -> MetricsSummary {
        let text = try await metricsRaw()

        let verdicts = parseVerdictCounts(from: text)
        let remediations = parseRemediationMetrics(from: text)

        return MetricsSummary(
            verdicts: verdicts,
            remediations: remediations,
            health: "up",
            timestamp: Date()
        )
    }

    private func parseRemediationMetrics(from text: String) -> RemediationMetrics {
        var requested = 0
        var completed = 0
        var promoted = 0
        var rolledBack = 0
        var failed = 0

        for line in text.split(separator: "\n") {
            if line.contains("governance_remediations_requested_total"),
               let countStr = line.split(separator: " ").last {
                requested = Int(countStr) ?? 0
            } else if line.contains("governance_remediations_completed_total"),
                      let countStr = line.split(separator: " ").last {
                completed = Int(countStr) ?? 0
            } else if line.contains("governance_remediations_promoted_total"),
                      let countStr = line.split(separator: " ").last {
                promoted = Int(countStr) ?? 0
            } else if line.contains("governance_remediations_rolled_back_total"),
                      let countStr = line.split(separator: " ").last {
                rolledBack = Int(countStr) ?? 0
            } else if line.contains("governance_remediations_failed_total"),
                      let countStr = line.split(separator: " ").last {
                failed = Int(countStr) ?? 0
            }
        }

        return RemediationMetrics(
            requested: requested,
            completed: completed,
            promoted: promoted,
            rolledBack: rolledBack,
            failed: failed
        )
    }
}
