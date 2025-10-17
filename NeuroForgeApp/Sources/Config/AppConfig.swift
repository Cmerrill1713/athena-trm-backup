import Foundation

/// Single source of truth for app configuration
enum AppConfig {
    static let apiBase: URL = {
        let urlString =
            Bundle.main.object(forInfoDictionaryKey: "API_BASE") as? String
                ?? "http://127.0.0.1:8014"
        guard let url = URL(string: urlString) else {
            fatalError("Invalid API_BASE URL: \(urlString)")
        }
        return url
    }()

    // Service-specific endpoints
    static let routerURL: URL = {
        let urlString =
            ProcessInfo.processInfo.environment["ATHENA_ROUTER_URL"]
            ?? "http://127.0.0.1:9113"
        return URL(string: urlString)!
    }()

    static let orchestratorURL: URL = {
        let urlString =
            ProcessInfo.processInfo.environment["ATHENA_ORCHESTRATOR_URL"]
            ?? "http://127.0.0.1:9110"
        return URL(string: urlString)!
    }()

    static let remediatorURL: URL = {
        let urlString =
            ProcessInfo.processInfo.environment["ATHENA_REMEDIATOR_URL"]
            ?? "http://127.0.0.1:9112"
        return URL(string: urlString)!
    }()

    static var bridgeToken: String {
        // Prefer Keychain; fallback to env (for dev)
        ProcessInfo.processInfo.environment["BRIDGE_TOKEN"] ?? ""
    }

    static var bridgeAuthEnabled: Bool {
        Bundle.main.object(forInfoDictionaryKey: "BRIDGE_AUTH") as? Bool ?? false
    }
}
