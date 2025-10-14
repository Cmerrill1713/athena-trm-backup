import Foundation

public enum AlertSeverity: String, Codable, CaseIterable {
    case info, warning, critical
}

public enum RiskLevel: String, Codable, CaseIterable {
    case low, medium, high, extreme
}

public enum TribunalDecisionOption: String, Codable, CaseIterable {
    case uphold, overturn, modify, escalate
}

public struct CriticalAlert: Identifiable, Codable {
    public let id = UUID()
    public var title: String
    public var message: String
    public var severity: AlertSeverity
    public var affectedSystems: [String]
    public var recommendations: [String]
}

public struct TribunalCase: Identifiable, Codable {
    public let id = UUID()
    public var caseID: String
    public var summary: String
    public var aiRecommendation: TribunalDecisionOption
    public var confidence: Double
}

public struct SystemEmergency: Identifiable, Codable {
    public let id = UUID()
    public var title: String
    public var analysis: String
    public var countdownSeconds: Int
    public var risk: RiskLevel
    public var actions: [String]
}

