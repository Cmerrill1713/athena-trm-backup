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

// MARK: - Governance Models

public enum GovernanceMode: String, Codable, CaseIterable, Identifiable {
    case shadow, canary, enforce
    public var id: String { rawValue }

    public var displayName: String {
        switch self {
        case .shadow: return "Shadow"
        case .canary: return "Canary"
        case .enforce: return "Enforce"
        }
    }

    public var description: String {
        switch self {
        case .shadow: return "0% impact - Observe only"
        case .canary: return "1-5% impact - Partial enforcement"
        case .enforce: return "100% impact - Full governance"
        }
    }
}

public struct GovernanceHealth: Codable {
    public let status: String
    public let service: String?
    public let timestamp: Double?
}

public struct GovernanceKPIs: Codable {
    public var ece: Double
    public var entropy: Double
    public var verdicts_5m: Int
    public var actions_5m: Int
    public var hard_fails_5m: Int

    public static let empty = GovernanceKPIs(
        ece: .nan,
        entropy: .nan,
        verdicts_5m: 0,
        actions_5m: 0,
        hard_fails_5m: 0
    )
}

public struct VerdictPayload: Codable {
    public let task_id: String
    public let verdict: String
    public let ece_post: Double?
    public let entropy: Double?
    public let actions: [String]?
    public let ts: String

    public init(
        task_id: String, verdict: String, ece_post: Double?, entropy: Double?, actions: [String]?,
        ts: String
    ) {
        self.task_id = task_id
        self.verdict = verdict
        self.ece_post = ece_post
        self.entropy = entropy
        self.actions = actions
        self.ts = ts
    }
}

public struct VerdictResponse: Codable {
    public let status: String
    public let task_id: String?
    public let message: String?
}

public struct GovernanceAlert: Identifiable {
    public let id = UUID()
    public let message: String
    public let severity: AlertSeverity
    public let timestamp: Date

    public init(message: String, severity: AlertSeverity) {
        self.message = message
        self.severity = severity
        self.timestamp = Date()
    }
}
