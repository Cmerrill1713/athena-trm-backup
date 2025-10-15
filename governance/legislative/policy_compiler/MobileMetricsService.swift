import Foundation

/// Mobile metrics service for tracking avatar performance on iOS
final class MobileMetricsService {

    static let shared = MobileMetricsService()

    private let metricsURL = URL(string: "http://localhost:8035/metrics/mobile")!
    private let queue = DispatchQueue(label: "com.athena.mobilemetrics", qos: .utility)

    // Metrics cache for batch sending
    private var metricsBuffer: [MobileMetric] = []
    private var flushTimer: Timer?

    private init() {
        // Flush metrics every 30 seconds
        startPeriodicFlush()
    }

    deinit {
        flushTimer?.invalidate()
        flushMetrics() // Final flush
    }

    /// Track avatar morph switch
    func trackAvatarSwitch(target: AvatarMorphMode, success: Bool, duration: TimeInterval) {
        let metric = MobileMetric(
            type: .avatarSwitch,
            platform: "ios",
            target: target.rawValue,
            success: success,
            duration: duration,
            timestamp: Date()
        )
        addMetric(metric)
    }

    /// Track avatar morph failure
    func trackAvatarSwitchFailure(reason: String) {
        let metric = MobileMetric(
            type: .avatarSwitchFailure,
            platform: "ios",
            reason: reason,
            timestamp: Date()
        )
        addMetric(metric)
    }

    /// Track API latency
    func trackAPILatency(endpoint: String, duration: TimeInterval, statusCode: Int) {
        let metric = MobileMetric(
            type: .apiLatency,
            platform: "ios",
            endpoint: endpoint,
            duration: duration,
            statusCode: statusCode,
            timestamp: Date()
        )
        addMetric(metric)
    }

    /// Track notification delivery
    func trackNotification(kind: String, delivered: Bool) {
        let metric = MobileMetric(
            type: .notification,
            platform: "ios",
            kind: kind,
            delivered: delivered,
            timestamp: Date()
        )
        addMetric(metric)
    }

    /// Track connectivity status
    func trackConnectivity(status: String) {
        let metric = MobileMetric(
            type: .connectivity,
            platform: "ios",
            status: status,
            timestamp: Date()
        )
        addMetric(metric)
    }

    /// Track app lifecycle events
    func trackAppLifecycle(event: String) {
        let metric = MobileMetric(
            type: .appLifecycle,
            platform: "ios",
            event: event,
            timestamp: Date()
        )
        addMetric(metric)
    }

    private func addMetric(_ metric: MobileMetric) {
        queue.async {
            self.metricsBuffer.append(metric)

            // Flush immediately if buffer gets too large
            if self.metricsBuffer.count >= 10 {
                self.flushMetrics()
            }
        }
    }

    private func startPeriodicFlush() {
        flushTimer = Timer.scheduledTimer(withTimeInterval: 30.0, repeats: true) { [weak self] _ in
            self?.flushMetrics()
        }
    }

    private func flushMetrics() {
        queue.async {
            guard !self.metricsBuffer.isEmpty else { return }

            let metricsToSend = self.metricsBuffer
            self.metricsBuffer.removeAll()

            Task {
                await self.sendMetrics(metricsToSend)
            }
        }
    }

    private func sendMetrics(_ metrics: [MobileMetric]) async {
        guard let jsonData = try? JSONEncoder().encode(metrics) else {
            print("Failed to encode mobile metrics")
            return
        }

        var request = URLRequest(url: metricsURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(await getAuthToken())", forHTTPHeaderField: "Authorization")
        request.httpBody = jsonData

        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            if let httpResponse = response as? HTTPURLResponse,
               (200..<300).contains(httpResponse.statusCode) {
                print("Mobile metrics sent successfully")
            } else {
                print("Failed to send mobile metrics: HTTP \(String(describing: (response as? HTTPURLResponse)?.statusCode))")
            }
        } catch {
            print("Error sending mobile metrics: \(error.localizedDescription)")
            // Re-queue failed metrics
            queue.async {
                self.metricsBuffer.insert(contentsOf: metrics, at: 0)
            }
        }
    }

    private func getAuthToken() async -> String {
        // Get token from TokenManager
        do {
            return try await TokenManager.shared.getValidToken()
        } catch {
            return "unauthorized" // Fallback for metrics
        }
    }
}

/// Mobile metric data structure
struct MobileMetric: Codable {
    enum MetricType: String, Codable {
        case avatarSwitch
        case avatarSwitchFailure
        case apiLatency
        case notification
        case connectivity
        case appLifecycle
    }

    let type: MetricType
    let platform: String
    let target: String?
    let success: Bool?
    let duration: TimeInterval?
    let statusCode: Int?
    let endpoint: String?
    let reason: String?
    let kind: String?
    let delivered: Bool?
    let status: String?
    let event: String?
    let timestamp: Date

    init(type: MetricType,
         platform: String,
         target: String? = nil,
         success: Bool? = nil,
         duration: TimeInterval? = nil,
         statusCode: Int? = nil,
         endpoint: String? = nil,
         reason: String? = nil,
         kind: String? = nil,
         delivered: Bool? = nil,
         status: String? = nil,
         event: String? = nil,
         timestamp: Date) {

        self.type = type
        self.platform = platform
        self.target = target
        self.success = success
        self.duration = duration
        self.statusCode = statusCode
        self.endpoint = endpoint
        self.reason = reason
        self.kind = kind
        self.delivered = delivered
        self.status = status
        self.event = event
        self.timestamp = timestamp
    }
}
