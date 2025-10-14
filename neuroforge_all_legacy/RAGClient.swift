import Foundation

/// RAG (Retrieval Augmented Generation) Client
/// Provides semantic search over AI coding video transcript knowledge base
@available(macOS 12.0, *)
public actor RAGClient {
    private let baseURL: URL
    private let urlSession: URLSession

    public init(baseURL: String = "http://localhost:8014") {
        self.baseURL = URL(string: baseURL)!
        self.urlSession = URLSession.shared
    }

    // MARK: - Models

    public struct RAGQuery: Codable {
        let query: String
        let k: Int
        let alpha: Double
        let includeSource: Bool

        enum CodingKeys: String, CodingKey {
            case query, k, alpha
            case includeSource = "include_sources"
        }

        public init(query: String, k: Int = 8, alpha: Double = 0.45, includeSource: Bool = true) {
            self.query = query
            self.k = k
            self.alpha = alpha
            self.includeSource = includeSource
        }
    }

    public struct RAGHit: Codable, Identifiable {
        public let id = UUID()
        public let title: String
        public let text: String
        public let source: String?
        public let url: String?
        public let tags: [String]?
        public let publishedAt: String?
        public let score: Double?
        public let channel: String?

        enum CodingKeys: String, CodingKey {
            case title, text, source, url, tags, score, channel
            case publishedAt = "published_at"
        }
    }

    public struct RAGResponse: Codable {
        public let hits: [RAGHit]
        public let query: String
        public let count: Int
        public let latencyMs: Double

        enum CodingKeys: String, CodingKey {
            case hits, query, count
            case latencyMs = "latency_ms"
        }
    }

    public struct RAGStats: Codable {
        public let totalTranscripts: Int
        public let totalCharacters: Int
        public let channels: [String: Int]
        public let topTopics: [String: Int]
        public let timestamp: String

        enum CodingKeys: String, CodingKey {
            case totalTranscripts = "total_transcripts"
            case totalCharacters = "total_characters"
            case channels
            case topTopics = "top_topics"
            case timestamp
        }
    }

    // MARK: - API Methods

    /// Search the knowledge base
    public func search(query: String, k: Int = 8, alpha: Double = 0.45) async throws -> RAGResponse {
        let url = baseURL.appendingPathComponent("/api/rag/query")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let queryData = RAGQuery(query: query, k: k, alpha: alpha)
        request.httpBody = try JSONEncoder().encode(queryData)

        let (data, response) = try await urlSession.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw RAGError.requestFailed
        }

        return try JSONDecoder().decode(RAGResponse.self, from: data)
    }

    /// Get RAG statistics
    public func stats() async throws -> RAGStats {
        let url = baseURL.appendingPathComponent("/api/rag/stats")
        let (data, _) = try await urlSession.data(from: url)
        return try JSONDecoder().decode(RAGStats.self, from: data)
    }

    /// Check RAG service health
    public func health() async throws -> Bool {
        let url = baseURL.appendingPathComponent("/api/rag/health")
        let (data, response) = try await urlSession.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            return false
        }

        if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let status = json["status"] as? String {
            return status == "healthy"
        }

        return false
    }
}

// MARK: - Errors

public enum RAGError: Error, LocalizedError {
    case requestFailed
    case decodingFailed
    case serviceUnavailable

    public var errorDescription: String? {
        switch self {
        case .requestFailed: return "RAG request failed"
        case .decodingFailed: return "Failed to decode RAG response"
        case .serviceUnavailable: return "RAG service unavailable"
        }
    }
}
