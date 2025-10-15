import Foundation

// MARK: - Service Registry (Single source of truth for all services)

struct ServiceInfo: Identifiable, Hashable {
    let id: String
    let name: String
    let baseURL: String
    let healthEndpoint: String
    let port: Int
    let tier: ServiceTier
    let required: Bool

    init(id: String? = nil, name: String, baseURL: String, healthEndpoint: String = "/health", tier: ServiceTier = .core, required: Bool = true) {
        self.id = id ?? name.lowercased()
        self.name = name
        self.baseURL = baseURL
        self.healthEndpoint = healthEndpoint
        self.port = Int(baseURL.split(separator: ":").last ?? "0") ?? 0
        self.tier = tier
        self.required = required
    }

    var healthURL: String {
        baseURL + healthEndpoint
    }

    var readyURL: String {
        baseURL + "/ready"
    }
}

enum ServiceTier: String, CaseIterable {
    case core = "Core"
    case voice = "Voice"
    case rag = "RAG"
    case vision = "Vision"
    case monitoring = "Monitoring"

    var color: Color {
        switch self {
        case .core: return .blue
        case .voice: return .purple
        case .rag: return .green
        case .vision: return .orange
        case .monitoring: return .gray
        }
    }
}

// MARK: - Service Registry

enum ServiceRegistry {
    // Core Services (Required)
    static let bridge = ServiceInfo(
        name: "Bridge",
        baseURL: "http://127.0.0.1:8014",
        healthEndpoint: "/health",
        tier: .core,
        required: true
    )

    static let athena = ServiceInfo(
        name: "Athena",
        baseURL: "http://127.0.0.1:8090",
        healthEndpoint: "/health",
        tier: .core,
        required: true
    )

    static let uat = ServiceInfo(
        name: "UAT",
        baseURL: "http://127.0.0.1:8181",
        healthEndpoint: "/health",
        tier: .core,
        required: true
    )

    // Voice Services (Optional)
    static let kokoro = ServiceInfo(
        name: "Kokoro TTS",
        baseURL: "http://127.0.0.1:8020",
        healthEndpoint: "/health",
        tier: .voice,
        required: false
    )

    // RAG Services (Optional)
    static let rag = ServiceInfo(
        name: "RAG Service",
        baseURL: "http://127.0.0.1:8015",
        healthEndpoint: "/ready",
        tier: .rag,
        required: false
    )

    static let weaviate = ServiceInfo(
        name: "Weaviate",
        baseURL: "http://127.0.0.1:8080",
        healthEndpoint: "/v1/meta",
        tier: .rag,
        required: false
    )

    // Vision Services (Optional)
    static let fastvlm = ServiceInfo(
        name: "FastVLM",
        baseURL: "http://127.0.0.1:8811",
        healthEndpoint: "/health",
        tier: .vision,
        required: false
    )

    static let visionRAG = ServiceInfo(
        name: "Vision RAG",
        baseURL: "http://127.0.0.1:8016",
        healthEndpoint: "/ready",
        tier: .vision,
        required: false
    )

    // AI/ML Services (Optional)
    static let ollama = ServiceInfo(
        name: "Ollama",
        baseURL: "http://127.0.0.1:11434",
        healthEndpoint: "/api/tags",
        tier: .core,
        required: false
    )

    // MCP Services (Optional)
    static let mcpChat = ServiceInfo(
        name: "MCP Chat",
        baseURL: "http://127.0.0.1:8081",
        healthEndpoint: "/health",
        tier: .core,
        required: false
    )

    static let mcpOrchestration = ServiceInfo(
        name: "MCP Orchestration",
        baseURL: "http://127.0.0.1:8084",
        healthEndpoint: "/health",
        tier: .core,
        required: false
    )

    // Monitoring Services (Optional)
    static let prometheus = ServiceInfo(
        name: "Prometheus",
        baseURL: "http://127.0.0.1:9090",
        healthEndpoint: "/-/ready",
        tier: .monitoring,
        required: false
    )

    static let netdata = ServiceInfo(
        name: "Netdata",
        baseURL: "http://127.0.0.1:19999",
        healthEndpoint: "/",
        tier: .monitoring,
        required: false
    )

    static let grafana = ServiceInfo(
        name: "Grafana",
        baseURL: "http://127.0.0.1:3000",
        healthEndpoint: "/api/health",
        tier: .monitoring,
        required: false
    )

    // All services grouped
    static let all: [ServiceInfo] = [
        bridge, athena, uat, ollama,    // Core
        mcpChat, mcpOrchestration,      // MCP
        kokoro,                          // Voice
        rag, weaviate,                   // RAG
        fastvlm, visionRAG,              // Vision
        prometheus, netdata, grafana     // Monitoring
    ]

    static let core: [ServiceInfo] = [bridge, athena, uat, ollama]
    static let mcp: [ServiceInfo] = [mcpChat, mcpOrchestration]
    static let voice: [ServiceInfo] = [kokoro]
    static let ragServices: [ServiceInfo] = [rag, weaviate]
    static let visionServices: [ServiceInfo] = [fastvlm, visionRAG]
    static let monitoringServices: [ServiceInfo] = [prometheus, netdata, grafana]

    static func byTier(_ tier: ServiceTier) -> [ServiceInfo] {
        all.filter { $0.tier == tier }
    }

    // Shared instance for easier access
    static let shared = ServiceRegistryHelper()
}

// MARK: - Service Registry Helper

struct ServiceRegistryHelper {
    // Health check URLs
    var healthChecks: [(String, String)] {
        ServiceRegistry.all.map { ($0.name, $0.healthURL) }
    }

    // Quick access URLs
    var ragURL: String { ServiceRegistry.rag.baseURL }
    var visionURL: String { ServiceRegistry.fastvlm.baseURL }
    var bridgeURL: String { ServiceRegistry.bridge.baseURL }
    var athenaURL: String { ServiceRegistry.athena.baseURL }
}

// MARK: - Service Health Check

import SwiftUI

@MainActor
class ServiceHealthChecker: ObservableObject {
    @Published var statuses: [String: ServiceHealth] = [:]

    struct ServiceHealth {
        let service: ServiceInfo
        var isHealthy: Bool = false
        var lastCheck: Date?
        var latencyMs: Int?
        var error: String?
    }

    func checkAll(services: [ServiceInfo]) async {
        await withTaskGroup(of: (String, ServiceHealth).self) { group in
            for service in services {
                group.addTask {
                    await self.check(service)
                }
            }

            for await (id, health) in group {
                statuses[id] = health
            }
        }
    }

    private func check(_ service: ServiceInfo) async -> (String, ServiceHealth) {
        let start = Date()
        var health = ServiceHealth(service: service)

        do {
            let url = URL(string: service.healthURL)!
            let (_, response) = try await URLSession.shared.data(from: url)

            if let httpResp = response as? HTTPURLResponse, (200...299).contains(httpResp.statusCode) {
                health.isHealthy = true
                health.latencyMs = Int(-start.timeIntervalSinceNow * 1000)
            } else {
                health.isHealthy = false
                health.error = "Non-200 response"
            }
        } catch {
            health.isHealthy = false
            health.error = error.localizedDescription
        }

        health.lastCheck = Date()
        return (service.id, health)
    }
}
