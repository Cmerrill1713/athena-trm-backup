import Foundation

/// Mobile Metrics Service - Stub for compatibility
/// TODO: Integrate with Prometheus/governance metrics
final class MobileMetricsService {
    static let shared = MobileMetricsService()

    private init() {}

    func trackAvatarSwitch(target: AvatarMode, success: Bool, duration: TimeInterval) {
        NSLog("[MobileMetrics] Avatar switch: \(target) success=\(success) duration=\(duration)s")
    }

    func trackAPILatency(endpoint: String, duration: TimeInterval, statusCode: Int) {
        NSLog("[MobileMetrics] API \(endpoint): \(duration)s status=\(statusCode)")
    }

    func trackAvatarSwitchFailure(reason: String) {
        NSLog("[MobileMetrics] Avatar switch failed: \(reason)")
    }
}
