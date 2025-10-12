// Sources/NeuroForgeApp/Routing/ProviderOverrideManager.swift
import Foundation

@MainActor
final class ProviderOverrideManager: ObservableObject {

    static let shared = ProviderOverrideManager()
    private init() { load() }

    @Published var active: ProviderRoute = .auto
    @Published var remoteApplied: Bool = false
    @Published var health: [ProviderRoute: ProviderHealth] = [:]
    @Published var errorMessage: String? = nil

    private let storeKey = "ProviderOverride.active"
    private var backendBase: String {
        return APIBase.url.absoluteString
    }

    func load() {
        if let raw = UserDefaults.standard.string(forKey: storeKey),
           let route = ProviderRoute(rawValue: raw) {
            active = route
        }
    }

    func set(_ route: ProviderRoute) {
        let timestamp = ISO8601DateFormatter().string(from: Date())
        print("[ProviderInspector] override=\(route.rawValue) source=client timestamp=\(timestamp)")
        active = route
        UserDefaults.standard.set(route.rawValue, forKey: storeKey)
        Task { await pushToBackendIfSupported() }
    }

    func resetToAuto() { set(.auto) }

    /// Best-effort: try backend override, otherwise client header fallback (handled by NetworkInterceptor)
    func pushToBackendIfSupported() async {
        guard let url = URL(string: "\(backendBase)/api/router/override") else { return }
        do {
            var req = URLRequest(url: url)
            req.httpMethod = "POST"
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            req.httpBody = try JSONEncoder().encode(["provider": active.rawValue])
            let (_, resp) = try await URLSession.shared.data(for: req)
            if let http = resp as? HTTPURLResponse, (200..<300).contains(http.statusCode) {
                remoteApplied = true
                errorMessage = nil
            } else {
                remoteApplied = false // server doesn't support it, we'll rely on header
            }
        } catch {
            remoteApplied = false // fallback to header path
        }
    }

    /// Ping providers for health + latency; safe if endpoints are absent.
    func refreshHealth() async {
        await withTaskGroup(of: (ProviderRoute, ProviderHealth?).self) { group in
            for route in ProviderRoute.allCases {
                group.addTask { [weak self] in
                    guard let self else { return (route, nil) }
                    let start = Date()
                    let ok = await self.probe(route: route)
                    let ms = Int(-start.timeIntervalSinceNow * 1000)
                    return (route, ProviderHealth(route: route, healthy: ok, latencyMs: ok ? ms : nil, lastChecked: Date()))
                }
            }
            var map: [ProviderRoute: ProviderHealth] = [:]
            for await (route, health) in group {
                if let health { map[route] = health }
            }
            self.health = map
        }
    }

    private func probe(route: ProviderRoute) async -> Bool {
        // Direct URLs to actual services (not proxied through backend)
        let urlString: String
        switch route {
        case .auto:
            // Generic app health through backend
            urlString = "\(backendBase)/health"
        case .fastvlm:
            // Direct FastVLM health check
            urlString = "http://127.0.0.1:8811/health"
        case .ollama:
            // Direct Ollama health check (api/version or api/tags)
            urlString = "http://127.0.0.1:11434/api/version"
        case .trm:
            // TRM router health (could be through backend or direct)
            // Check if TRM is at :3033 or through backend
            urlString = "\(backendBase)/health"  // Adjust if TRM has separate endpoint
        }

        guard let url = URL(string: urlString) else { return false }
        var req = URLRequest(url: url)
        req.timeoutInterval = 3.0
        // Tell backend which probe we're doing; harmless if ignored
        req.setValue(route.rawValue, forHTTPHeaderField: "X-Provider-Probe")

        do {
            let (_, resp) = try await URLSession.shared.data(for: req)
            if let http = resp as? HTTPURLResponse {
                return (200..<300).contains(http.statusCode)
            }
        } catch {
            print("⚠️ Provider probe failed for \(route.rawValue): \(error.localizedDescription)")
        }
        return false
    }
}
