import Foundation

enum APIBase {
    static let envKey = "API_BASE"

    static var url: URL {
        if let env = ProcessInfo.processInfo.environment[envKey],
           let u = URL(string: env) { return u }
        for candidate in [
            "http://localhost:8014",
            "http://localhost:8888",
            "http://localhost:8013",
            "http://localhost:8080"
        ] {
            if let u = URL(string: candidate) { return u }
        }
        return URL(string: "http://localhost:8014")!
    }
}
