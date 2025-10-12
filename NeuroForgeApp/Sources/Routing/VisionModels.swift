import Foundation

public struct VisionDescribeRequest: Codable {
    public let kind: String = "vision.describe"
    public let prompt: String
    public let imageBase64: String   // data:image/png;base64,....
    public let metadata: [String: String]?

    public init(prompt: String, imageBase64: String, metadata: [String: String]? = nil) {
        self.prompt = prompt
        self.imageBase64 = imageBase64
        self.metadata = metadata
    }
}

public struct VisionDescribeResponse: Codable {
    public let text: String              // caption/analysis
    public let citations: [Citation]?    // optional RAG context
    public let ingestedObjectID: String? // Weaviate UUID or record id
    public let provider: String?         // fastvlm/ollama/auto
    public let latencyMs: Int?

    enum CodingKeys: String, CodingKey {
        case text, citations, provider
        case ingestedObjectID = "ingested_object_id"
        case latencyMs = "latency_ms"
    }
}

public struct Citation: Codable, Identifiable {
    public let id: String
    public let title: String
    public let snippet: String
    public let source: String            // e.g., weaviate://class/id or http(s)://...

    public init(id: String, title: String, snippet: String, source: String) {
        self.id = id
        self.title = title
        self.snippet = snippet
        self.source = source
    }
}
