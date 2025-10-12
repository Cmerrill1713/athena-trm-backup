import Foundation

struct APIClient {
    private let base = APIBase.url
    private let session: URLSession = {
        let cfg = URLSessionConfiguration.default
        cfg.timeoutIntervalForRequest = 20
        cfg.timeoutIntervalForResource = 30
        return URLSession(configuration: cfg)
    }()

    // /health → 200
    func health() async -> Bool {
        do {
            let (data, resp) = try await session.data(from: base.appendingPathComponent("health"))
            guard (resp as? HTTPURLResponse)?.statusCode == 200 else { return false }
            return data.count >= 0
        } catch { return false }
    }

    // Model-agnostic chat endpoint
    func chat(_ task: ChatTask) async throws -> String {
        var req = URLRequest(url: base.appendingPathComponent("api/chat"))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONEncoder().encode(task)

        let (data, resp) = try await session.data(for: req)
        let code = (resp as? HTTPURLResponse)?.statusCode ?? -1
        guard (200..<300).contains(code) || code == 422 else {
            throw APIError.badStatus(code, data)
        }
        // Expect { "text": "..." } or 422 body with message
        if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let text = json["text"] as? String { return text }
        if let txt = String(data: data, encoding: .utf8) { return txt }
        throw APIError.decode
    }
}
