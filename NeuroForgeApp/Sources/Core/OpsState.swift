import Foundation

/// Minimal OpsState for build compatibility
/// Provides basic monitoring state without full feature implementation
@MainActor
public final class OpsState: ObservableObject {
    public static let shared = OpsState()
    
    @Published public private(set) var isConnected: Bool = false
    @Published public private(set) var lastLatencyMs: Int = 0
    @Published public private(set) var lastError: String?
    @Published public private(set) var lastConfidence: Double?
    @Published public var healthSummary: String = "—"
    
    private init() {}
    
    public func setConnected(latencyMs: Int? = nil) {
        isConnected = true
        if let ms = latencyMs {
            lastLatencyMs = ms
        }
        lastError = nil
    }
    
    public func setDisconnected(reason: String? = nil) {
        isConnected = false
        lastError = reason
    }
    
    public func setLatency(_ ms: Int) {
        lastLatencyMs = ms
    }
    
    public func updateHealth(summary: String) {
        healthSummary = summary
    }
    
    public func update(confidence: Double) {
        lastConfidence = confidence
    }
    
    public func resetSession() {
        // Reset session counters if full implementation added
    }
}
