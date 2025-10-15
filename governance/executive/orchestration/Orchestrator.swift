import Foundation

/// Orchestrator client for NeuroForge Adapter integration
actor Orchestrator {
    static let shared = Orchestrator()

    private let base = URL(string: ProcessInfo.processInfo.environment["API_BASE"] ?? "http://127.0.0.1:8014")!
    private let session = URLSession(configuration: .default)

    private init() {}

    private func get(_ path: String) async throws -> Data {
        let url = base.appendingPathComponent(path)
        let (data, response) = try await session.data(from: url)

        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode >= 400 {
            throw OrchestratorError.httpError(httpResponse.statusCode)
        }

        return data
    }

    private func post(_ path: String, body: Data) async throws -> Data {
        var request = URLRequest(url: base.appendingPathComponent(path))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let (data, response) = try await session.upload(for: request, from: body)

        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode >= 400 {
            throw OrchestratorError.httpError(httpResponse.statusCode)
        }

        return data
    }

    // MARK: - Health Check

    func health() async throws -> HealthResponse {
        let data = try await get("health")
        return try JSONDecoder.withISO8601.decode(HealthResponse.self, from: data)
    }

    // MARK: - Traces (UAT telemetry)

    func fetchTraces(capability: String? = nil, limit: Int = 100) async throws -> [TraceSummary] {
        var path = "traces?limit=\(limit)"
        if let capability = capability {
            path += "&capability=\(capability)"
        }

        let data = try await get(path)
        let response = try JSONDecoder.withISO8601.decode(TracesResponse.self, from: data)
        return response.traces.map { TraceSummary(from: $0) }
    }

    func fetchTrace(id: String) async throws -> TraceDetail {
        let data = try await get("trace/\(id)")
        return try JSONDecoder.withISO8601.decode(TraceDetail.self, from: data)
    }

    // MARK: - Chat (Athena)

    func chat(_ request: ChatRequest) async throws -> ChatResponse {
        let payload = try JSONEncoder().encode(request)
        let data = try await post("chat", body: payload)
        return try JSONDecoder.withISO8601.decode(ChatResponse.self, from: data)
    }

    // MARK: - Agents (Athena)

    func fetchAgents() async throws -> [AgentInfo] {
        let data = try await get("agents")
        return try JSONDecoder.withISO8601.decode([AgentInfo].self, from: data)
    }

    // MARK: - Capabilities (UAT)

    func fetchCapabilities() async throws -> [String] {
        let data = try await get("capabilities")
        return try JSONDecoder.withISO8601.decode([String].self, from: data)
    }

    // MARK: - Stats (UAT)

    func fetchStats() async throws -> StatsResponse {
        let data = try await get("stats")
        return try JSONDecoder.withISO8601.decode(StatsResponse.self, from: data)
    }
}

// MARK: - Models

struct HealthResponse: Codable {
    let status: String
    let adapter: String
    let uat: [String: AnyCodable]
    let athena: [String: AnyCodable]
    let timestamp: String

    var isHealthy: Bool {
        status == "healthy"
    }

    var uatStatus: String {
        uat["status"]?.stringValue ?? "unknown"
    }

    var athenaStatus: String {
        athena["status"]?.stringValue ?? "unknown"
    }
}

struct TracesResponse: Codable {
    let traces: [TraceDTO]
    let count: Int
}

struct TraceDTO: Codable {
    let id: String
    let capability: String
    let duration_ms: Int
    let started_at: Double
    let provider: String?
    let score: Double?
}

struct TraceSummary: Identifiable, Hashable {  // ✅ Added Hashable for List selection
    let id: String
    var capability: String
    let durationMs: Int
    let startedAt: Date
    let provider: String?
    let score: Double?

    init(from dto: TraceDTO) {
        self.id = dto.id
        self.capability = dto.capability
        self.durationMs = dto.duration_ms
        self.startedAt = Date(timeIntervalSince1970: dto.started_at)
        self.provider = dto.provider
        self.score = dto.score
    }
}

struct TraceDetail: Codable {
    let output: [String: AnyCodable]
    let trace: [String: AnyCodable]
}

struct ChatRequest: Codable {
    let text: String
    let context: [String: String]?
    let route: String?

    init(text: String, context: [String: String]? = nil, route: String? = nil) {
        self.text = text
        self.context = context
        self.route = route
    }
}

struct ChatResponse: Codable {
    let reply: String
    let route: String?
    let metadata: [String: AnyCodable]?
}

struct AgentInfo: Codable {
    let id: String
    let name: String
    let capabilities: [String]
}

struct StatsResponse: Codable {
    let stats: [String: AnyCodable]
}

// MARK: - Errors

enum OrchestratorError: Error, LocalizedError {
    case httpError(Int)
    case networkError(Error)
    case decodingError(Error)

    var errorDescription: String? {
        switch self {
        case .httpError(let code):
            return "HTTP Error: \(code)"
        case .networkError(let error):
            return "Network Error: \(error.localizedDescription)"
        case .decodingError(let error):
            return "Decoding Error: \(error.localizedDescription)"
        }
    }
}

// MARK: - JSON Decoder Extension

extension JSONDecoder {
    static var withISO8601: JSONDecoder {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }
}

// MARK: - AnyCodable Helper

struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map { $0.value }
        } else if let dict = try? container.decode([String: AnyCodable].self) {
            value = dict.mapValues { $0.value }
        } else {
            throw DecodingError.typeMismatch(AnyCodable.self, DecodingError.Context(codingPath: decoder.codingPath, debugDescription: "Unsupported type"))
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch value {
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let string as String:
            try container.encode(string)
        case let bool as Bool:
            try container.encode(bool)
        case let array as [Any]:
            try container.encode(array.map { AnyCodable($0) })
        case let dict as [String: Any]:
            try container.encode(dict.mapValues { AnyCodable($0) })
        default:
            throw EncodingError.invalidValue(value, EncodingError.Context(codingPath: encoder.codingPath, debugDescription: "Unsupported type"))
        }
    }

    var stringValue: String? {
        value as? String
    }

    var intValue: Int? {
        value as? Int
    }

    var doubleValue: Double? {
        value as? Double
    }

    var boolValue: Bool? {
        value as? Bool
    }
}
