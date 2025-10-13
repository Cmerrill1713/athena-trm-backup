import SwiftUI
import Combine

// MARK: - Operations State (Shared across windows)

final class OpsState: ObservableObject {
    @Published var currentTab: OpsTab = .traces
    @Published var recentEvents: [OpsEvent] = []
    @Published var healthStatus: HealthStatus = .unknown
    @Published var lastConfidence: Double? = nil
    @Published var isWindowOpen = false
    
    // Auto-open settings
    @AppStorage("opsAutoOpenOnLowConfidence") var autoOpenOnLowConfidence = true
    @AppStorage("opsLowConfidenceThreshold") var lowConfidenceThreshold = 0.35
    
    // Session tracking for auto-open
    private var sessionAutoOpenCount = 0
    private var lastAutoOpenTime: Date?
    private var snoozeUntil: Date?
    
    func recordEvent(_ event: OpsEvent) {
        recentEvents.insert(event, at: 0)
        if recentEvents.count > 50 {
            recentEvents = Array(recentEvents.prefix(50))
        }
    }
    
    func updateConfidence(_ confidence: Double) {
        lastConfidence = confidence
    }
    
    func resetSession() {
        sessionAutoOpenCount = 0
        lastAutoOpenTime = nil
    }
    
    // TODO: Re-enable when MetaInfo type is defined
    // func update(from meta: MetaInfo) {
    //     updateConfidence(meta.confidence)
    // }
    
    func updateHealth(summary: String) {
        // Update health status based on summary
        if summary.contains("✅") {
            healthStatus = .healthy
        } else if summary.contains("⚠️") {
            healthStatus = .degraded
        } else {
            healthStatus = .unhealthy
        }
    }
    
    func shouldAutoOpen() -> (Bool, String?) {
        // Check snooze
        if let until = snoozeUntil, Date() < until {
            return (false, "snoozed")
        }
        
        // Check session limit (max 5 auto-opens per session)
        if sessionAutoOpenCount >= 5 {
            return (false, "session limit")
        }
        
        // Check debounce (5s between auto-opens)
        if let last = lastAutoOpenTime, Date().timeIntervalSince(last) < 5 {
            return (false, "debounce")
        }
        
        return (true, nil)
    }
    
    func recordAutoOpen() {
        sessionAutoOpenCount += 1
        lastAutoOpenTime = Date()
    }
    
    func snooze(minutes: Int) {
        snoozeUntil = Date().addingTimeInterval(TimeInterval(minutes * 60))
    }
}

enum OpsTab: String, CaseIterable, Identifiable {
    case traces
    case health
    case meta
    case metrics
    
    var id: String { rawValue }
    
    var title: String {
        switch self {
        case .traces: return "Traces"
        case .health: return "Health"
        case .meta: return "Meta"
        case .metrics: return "Metrics"
        }
    }
    
    var icon: String {
        switch self {
        case .traces: return "list.bullet.rectangle"
        case .health: return "heart.text.square"
        case .meta: return "brain.head.profile"
        case .metrics: return "chart.line.uptrend.xyaxis"
        }
    }
}

struct OpsEvent: Identifiable {
    let id = UUID()
    let timestamp: Date
    let type: EventType
    let message: String
    let confidence: Double?
    
    enum EventType {
        case lowConfidence
        case error
        case warning
        case info
        
        var color: Color {
            switch self {
            case .lowConfidence: return .red
            case .error: return .red
            case .warning: return .yellow
            case .info: return .blue
            }
        }
    }
}

enum HealthStatus {
    case unknown
    case healthy
    case degraded
    case unhealthy
    
    var color: Color {
        switch self {
        case .unknown: return .gray
        case .healthy: return .green
        case .degraded: return .yellow
        case .unhealthy: return .red
        }
    }
}

