// Sources/NeuroForgeApp/Routing/ProviderOverride.swift
import Foundation

/// Available provider routing options
public enum ProviderRoute: String, CaseIterable, Codable, Sendable {
    case auto = "auto"
    case fastvlm = "fastvlm"
    case ollama = "ollama"
    case trm = "trm"
}

/// Health status for a specific provider
public struct ProviderHealth: Sendable {
    public var route: ProviderRoute
    public var healthy: Bool
    public var latencyMs: Int?
    public var lastChecked: Date
}
