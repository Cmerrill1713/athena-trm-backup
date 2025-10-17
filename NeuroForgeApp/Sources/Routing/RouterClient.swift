import Foundation
import OSLog

/// Client for Athena routing service
///
/// Handles communication with the routing API to intelligently
/// route queries to appropriate AI models based on domain.
@MainActor
final class RouterClient: ObservableObject {

    // MARK: - Properties

    private let baseURL: URL
    private let session: URLSession
    private let logger = Logger(subsystem: "com.athena.neuroforge", category: "RouterClient")

    @Published var isHealthy: Bool = false
    @Published var modelsAvailable: [ModelInfo] = []
    @Published var lastError: String?

    // MARK: - Initialization

    init(baseURL: URL = URL(string: "http://localhost:9113")!) {
        self.baseURL = baseURL
        self.session = URLSession.shared

        logger.info("RouterClient initialized with baseURL: \(baseURL.absoluteString)")
    }

    // MARK: - Public API

    /// Check router health
    func checkHealth() async throws -> RouterHealthResponse {
        let url = baseURL.appendingPathComponent("/health")

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
            (200...299).contains(httpResponse.statusCode)
        else {
            throw RouterError.invalidResponse
        }

        let healthResponse = try JSONDecoder().decode(RouterHealthResponse.self, from: data)

        DispatchQueue.main.async {
            self.isHealthy = (healthResponse.status == "healthy")
        }

        logger.info(
            "Health check: \(healthResponse.status), models: \(healthResponse.modelsLoaded)")

        return healthResponse
    }

    /// Route a query to appropriate model
    func route(query: String, domain: String = "general") async throws -> RoutingChoice {
        let url = baseURL.appendingPathComponent("/route")

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let routingRequest = RoutingRequestPayload(
            query: query,
            domain: domain,
            metadata: [:]
        )

        request.httpBody = try JSONEncoder().encode(routingRequest)

        let startTime = Date()
        let (data, response) = try await session.data(for: request)
        let requestDuration = Date().timeIntervalSince(startTime) * 1000  // ms

        guard let httpResponse = response as? HTTPURLResponse,
            (200...299).contains(httpResponse.statusCode)
        else {
            throw RouterError.invalidResponse
        }

        let routingChoice = try JSONDecoder().decode(RoutingChoice.self, from: data)

        logger.info(
            "Routed query to \(routingChoice.model) (confidence: \(String(format: "%.2f", routingChoice.confidence)), latency: \(String(format: "%.1f", requestDuration))ms)"
        )

        return routingChoice
    }

    /// List available models
    func listModels() async throws -> [ModelInfo] {
        let url = baseURL.appendingPathComponent("/models")

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
            (200...299).contains(httpResponse.statusCode)
        else {
            throw RouterError.invalidResponse
        }

        let modelsResponse = try JSONDecoder().decode(ModelsResponse.self, from: data)

        DispatchQueue.main.async {
            self.modelsAvailable = modelsResponse.models
        }

        logger.info("Loaded \(modelsResponse.models.count) models")

        return modelsResponse.models
    }

    /// Reload model profiles
    func reload() async throws {
        let url = baseURL.appendingPathComponent("/reload")

        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
            (200...299).contains(httpResponse.statusCode)
        else {
            throw RouterError.invalidResponse
        }

        let reloadResponse = try JSONDecoder().decode(ReloadResponse.self, from: data)

        logger.info("Reloaded profiles: \(reloadResponse.modelsLoaded) models")
    }
}

// MARK: - Models

struct RouterHealthResponse: Codable {
    let status: String
    let service: String
    let modelsLoaded: Int
    let fallbackThreshold: Double

    enum CodingKeys: String, CodingKey {
        case status, service
        case modelsLoaded = "models_loaded"
        case fallbackThreshold = "fallback_threshold"
    }
}

struct RoutingRequestPayload: Codable {
    let query: String
    let domain: String
    let metadata: [String: String]
}

struct RoutingChoice: Codable {
    let model: String
    let confidence: Double
    let domain: String
    let latencyMs: Double
    let metadata: [String: AnyCodable]

    enum CodingKeys: String, CodingKey {
        case model, confidence, domain, metadata
        case latencyMs = "latency_ms"
    }
}

struct ModelInfo: Codable, Identifiable {
    let modelId: String
    let domain: String
    let qualityScore: Double
    let cost: Double
    let latencyP50Ms: Double
    let latencyP95Ms: Double
    let isApproximate: Bool
    let confidence: Double
    let metadata: ModelMetadata

    var id: String { modelId }

    enum CodingKeys: String, CodingKey {
        case modelId = "model_id"
        case domain
        case qualityScore = "quality_score"
        case cost
        case latencyP50Ms = "latency_p50_ms"
        case latencyP95Ms = "latency_p95_ms"
        case isApproximate = "is_approximate"
        case confidence
        case metadata
    }
}

struct ModelMetadata: Codable {
    let description: String?
    let provider: String?
    let contextWindow: Int?
    let maxOutputTokens: Int?

    enum CodingKeys: String, CodingKey {
        case description, provider
        case contextWindow = "context_window"
        case maxOutputTokens = "max_output_tokens"
    }
}

struct ModelsResponse: Codable {
    let models: [ModelInfo]
}

struct ReloadResponse: Codable {
    let status: String
    let modelsLoaded: Int

    enum CodingKeys: String, CodingKey {
        case status
        case modelsLoaded = "models_loaded"
    }
}

// MARK: - Errors

enum RouterError: LocalizedError {
    case invalidResponse
    case networkError(Error)
    case decodingError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "Invalid response from router"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .decodingError(let error):
            return "Decoding error: \(error.localizedDescription)"
        }
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

        if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map { $0.value }
        } else if let dict = try? container.decode([String: AnyCodable].self) {
            value = dict.mapValues { $0.value }
        } else {
            value = NSNull()
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()

        switch value {
        case let bool as Bool:
            try container.encode(bool)
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let string as String:
            try container.encode(string)
        case let array as [Any]:
            try container.encode(array.map { AnyCodable($0) })
        case let dict as [String: Any]:
            try container.encode(dict.mapValues { AnyCodable($0) })
        default:
            try container.encodeNil()
        }
    }
}
