import Foundation

/// API Client for Athena Governance Orchestrator
/// Connects to local governance services (9109, 9110, 9111, 9090)
final class GovernanceAPIClient {

    // MARK: - Configuration

    private let orchestratorURL: URL
    private let prometheusURL: URL
    private let session: URLSession

    init(
        orchestratorURL: URL = URL(string: "http://localhost:9110")!,
        prometheusURL: URL = URL(string: "http://localhost:9090")!
    ) {
        self.orchestratorURL = orchestratorURL
        self.prometheusURL = prometheusURL
        self.session = URLSession(configuration: .default)
    }

    // MARK: - Health Checks

    func checkHealth() async -> Bool {
        do {
            let url = orchestratorURL.appendingPathComponent("health")
            let (data, response) = try await session.data(from: url)

            guard let httpResponse = response as? HTTPURLResponse,
                httpResponse.statusCode == 200
            else {
                return false
            }

            let health = try? JSONDecoder().decode(GovernanceHealth.self, from: data)
            return health?.status == "healthy" || health?.status == "ok"
        } catch {
            return false
        }
    }

    // MARK: - Mode Control

    func setMode(_ mode: GovernanceMode) async throws {
        var request = URLRequest(url: orchestratorURL.appendingPathComponent("mode"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = [
            "mode": mode.rawValue, "timestamp": ISO8601DateFormatter().string(from: Date()),
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
            (200..<300).contains(httpResponse.statusCode)
        else {
            throw URLError(.badServerResponse)
        }
    }

    // MARK: - Verdicts

    func sendVerdict(_ payload: VerdictPayload) async throws -> VerdictResponse {
        var request = URLRequest(url: orchestratorURL.appendingPathComponent("verdict"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(payload)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
            (200..<300).contains(httpResponse.statusCode)
        else {
            throw URLError(.badServerResponse)
        }

        return try JSONDecoder().decode(VerdictResponse.self, from: data)
    }

    // MARK: - KPIs from Prometheus

    func fetchKPIs() async -> GovernanceKPIs {
        async let ece = queryPrometheus("governance_ece_post")
        async let entropy = queryPrometheus("governance_entropy_drift")
        async let verdicts5m = queryPrometheus("sum(increase(governance_verdicts_total[5m]))")
        async let actions5m = queryPrometheus("sum(increase(governance_actions_total[5m]))")
        async let hardFails5m = queryPrometheus(
            "sum(increase(governance_verdicts_total{verdict_type=\"hard_fail\"}[5m]))")

        do {
            let values = try await (ece, entropy, verdicts5m, actions5m, hardFails5m)
            return GovernanceKPIs(
                ece: values.0,
                entropy: values.1,
                verdicts_5m: Int(values.2),
                actions_5m: Int(values.3),
                hard_fails_5m: Int(values.4)
            )
        } catch {
            return .empty
        }
    }

    private func queryPrometheus(_ query: String) async throws -> Double {
        guard let encoded = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed)
        else {
            return 0
        }

        let urlString = prometheusURL.absoluteString + "/api/v1/query?query=" + encoded
        guard let url = URL(string: urlString) else {
            return 0
        }

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
            httpResponse.statusCode == 200
        else {
            throw URLError(.badServerResponse)
        }

        // Parse Prometheus response
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
            let dataDict = json["data"] as? [String: Any],
            let result = dataDict["result"] as? [[String: Any]],
            let firstResult = result.first,
            let value = firstResult["value"] as? [Any],
            let stringValue = value.last as? String,
            let doubleValue = Double(stringValue)
        else {
            return 0
        }

        return doubleValue
    }
}
