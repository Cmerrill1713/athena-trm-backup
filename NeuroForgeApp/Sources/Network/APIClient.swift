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
    @MainActor
    func chat(_ task: ChatTask) async throws -> String {
        var req = URLRequest(url: base.appendingPathComponent("api/chat"))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONEncoder().encode(task)

        // Inject provider override header if set
        NetworkInterceptor.injectProviderHeader(into: &req)

        let start = Date()
        let (data, resp) = try await session.data(for: req)
        let rtt = Int(-start.timeIntervalSinceNow * 1000)
        let code = (resp as? HTTPURLResponse)?.statusCode ?? -1

        // Log request with override header if present
        let overrideHeader = req.value(forHTTPHeaderField: "X-Provider-Override") ?? "none"
        print("[APIClient] POST /api/chat hdr:X-Provider-Override=\(overrideHeader) rtt=\(rtt)ms code=\(code)")

        guard (200..<300).contains(code) || code == 422 else {
            throw APIError.badStatus(code, data)
        }
        // Expect { "text": "..." } or 422 body with message
        if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let text = json["text"] as? String { return text }
        if let txt = String(data: data, encoding: .utf8) { return txt }
        throw APIError.decode
    }

    // Generic POST helper for typed requests/responses
    @MainActor
    func post<Req: Encodable, Res: Decodable>(_ path: String, body: Req) async throws -> Res {
        let url = base.appendingPathComponent(path.hasPrefix("/") ? String(path.dropFirst()) : path)
        var req = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 60)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Inject provider override header if set
        NetworkInterceptor.injectProviderHeader(into: &req)

        req.httpBody = try JSONEncoder().encode(body)

        let start = Date()
        let (data, resp) = try await session.data(for: req)
        let rtt = Int(-start.timeIntervalSinceNow * 1000)
        let code = (resp as? HTTPURLResponse)?.statusCode ?? -1

        print("[APIClient] POST \(path) rtt=\(rtt)ms code=\(code)")

        guard (200..<300).contains(code) else {
            throw APIError.badStatus(code, data)
        }

        return try JSONDecoder().decode(Res.self, from: data)
    }
}
