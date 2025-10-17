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

    static var bridgeToken: String {
        // Prefer Keychain; fallback to env (for dev)
        ProcessInfo.processInfo.environment["BRIDGE_TOKEN"] ?? ""
    }

    static var bridgeAuthEnabled: Bool {
        Bundle.main.object(forInfoDictionaryKey: "BRIDGE_AUTH") as? Bool ?? false
    }
}
