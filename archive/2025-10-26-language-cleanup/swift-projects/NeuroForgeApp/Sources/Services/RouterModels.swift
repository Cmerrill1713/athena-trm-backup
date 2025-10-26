// Router response format
struct RouterResponse: Codable {
    let response: String
    let route: String?
    let backend: String?
    let confidence: Double?
    let latency_ms: Int?
}

