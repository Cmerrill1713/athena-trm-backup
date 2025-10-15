// Sources/NeuroForgeApp/Network/NetworkInterceptor.swift
import Foundation

/// Helper to inject provider override header into requests
struct NetworkInterceptor {

    /// Returns provider override header if set (not auto)
    @MainActor
    static func providerHeader() -> (name: String, value: String)? {
        let route = ProviderOverrideManager.shared.active
        guard route != .auto else { return nil }
        return ("X-Provider-Override", route.rawValue)
    }

    /// Inject provider override header into URLRequest if needed
    @MainActor
    static func injectProviderHeader(into request: inout URLRequest) {
        if let (name, value) = providerHeader() {
            request.setValue(value, forHTTPHeaderField: name)
        }
    }
}
