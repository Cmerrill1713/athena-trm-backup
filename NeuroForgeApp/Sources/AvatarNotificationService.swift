import Foundation
#if canImport(UserNotifications)
import UserNotifications
#endif

/// Service for handling avatar-related notifications
final class AvatarNotificationService: NSObject, ObservableObject {
    static let shared = AvatarNotificationService()

    @Published var isAuthorized = false
    @Published var lastNotification: AvatarNotification?

    private override init() {
        super.init()
        #if canImport(UserNotifications)
        requestAuthorization()
        #else
        // For macOS or when UserNotifications not available
        isAuthorized = false
        #endif
    }

    /// Request notification permissions
    func requestAuthorization() {
        #if canImport(UserNotifications)
        // Check if we're in a proper app bundle context
        guard Bundle.main.bundleIdentifier != nil else {
            print("⚠️ Not in proper app bundle context, skipping notifications")
            isAuthorized = false
            return
        }
        
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) {
            granted, error in
            DispatchQueue.main.async {
                self.isAuthorized = granted
                if let error = error {
                    print("Notification authorization error: \(error.localizedDescription)")
                }
            }
        }
        UNUserNotificationCenter.current().delegate = self
        #else
        isAuthorized = false
        #endif
    }

    /// Trigger avatar morph notification
    func notifyMorph(from: AvatarMode, to: AvatarMode, awarenessLevel: Double? = nil) {
        guard isAuthorized else { return }
        
        #if canImport(UserNotifications)
        let content = UNMutableNotificationContent()
        content.title = "Avatar Morph"
        content.body = "Morphed from \(from.rawValue) to \(to.rawValue)"
        content.sound = .default
        content.categoryIdentifier = "AVATAR_MORPH"
        content.userInfo = [
            "type": "morph",
            "from": from.rawValue,
            "to": to.rawValue,
            "awarenessLevel": awarenessLevel ?? 0,
        ]

        let request = UNNotificationRequest(
            identifier: "avatar-morph-\(UUID().uuidString)",
            content: content,
            trigger: nil
        )

        UNUserNotificationCenter.current().add(request)
        #endif
        
        lastNotification = AvatarNotification(type: .morph, message: "Morphed from \(from.rawValue) to \(to.rawValue)")
    }

    /// Trigger avatar error notification
    func notifyError(_ error: String, isCritical: Bool = false) {
        guard isAuthorized else { return }
        
        #if canImport(UserNotifications)
        let content = UNMutableNotificationContent()
        content.title = isCritical ? "🚨 Avatar Critical Error" : "⚠️ Avatar Warning"
        content.body = error
        content.sound = isCritical ? .defaultCritical : .default
        content.categoryIdentifier = "AVATAR_ERROR"
        content.userInfo = [
            "type": "error",
            "message": error,
            "critical": isCritical,
        ]

        let request = UNNotificationRequest(
            identifier: "avatar-error-\(UUID().uuidString)",
            content: content,
            trigger: nil
        )

        UNUserNotificationCenter.current().add(request)
        #endif
        
        lastNotification = AvatarNotification(
            type: .error, message: error, isCritical: isCritical)
    }

    /// Trigger rollback notification
    func notifyRollback(to: AvatarMode) {
        guard isAuthorized else { return }
        
        #if canImport(UserNotifications)
        let content = UNMutableNotificationContent()
        content.title = "🔄 Avatar Rollback"
        content.body = "Automatically rolled back to \(to.rawValue)"
        content.sound = .default
        content.categoryIdentifier = "AVATAR_ROLLBACK"
        content.userInfo = [
            "type": "rollback",
            "target": to.rawValue,
        ]

        let request = UNNotificationRequest(
            identifier: "avatar-rollback-\(UUID().uuidString)",
            content: content,
            trigger: nil
        )

        UNUserNotificationCenter.current().add(request)
        #endif
        
        lastNotification = AvatarNotification(type: .rollback, message: "Automatically rolled back to \(to.rawValue)")
    }

    /// Trigger rollout phase change notification
    func notifyRolloutPhase(_ phase: String, percentage: Int) {
        guard isAuthorized else { return }
        
        #if canImport(UserNotifications)
        let content = UNMutableNotificationContent()
        content.title = "📈 Avatar Rollout"
        content.body = "Phase: \(phase) (\(percentage)% exposure)"
        content.sound = .default
        content.categoryIdentifier = "AVATAR_ROLLOUT"
        content.userInfo = [
            "type": "rollout",
            "phase": phase,
            "percentage": percentage,
        ]

        let request = UNNotificationRequest(
            identifier: "avatar-rollout-\(UUID().uuidString)",
            content: content,
            trigger: nil
        )

        UNUserNotificationCenter.current().add(request)
        #endif
        
        lastNotification = AvatarNotification(type: .rollout, message: "Phase: \(phase) (\(percentage)% exposure)")
    }

    /// Clear all avatar notifications
    func clearNotifications() {
        #if canImport(UserNotifications)
        UNUserNotificationCenter.current().removeAllDeliveredNotifications()
        UNUserNotificationCenter.current().removeAllPendingNotificationRequests()
        #endif
    }
}

// MARK: - UNUserNotificationCenterDelegate
#if canImport(UserNotifications)
extension AvatarNotificationService: UNUserNotificationCenterDelegate {
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler:
            @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        // Show notification even when app is in foreground
        completionHandler([.banner, .sound])
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        // Handle notification actions if needed
        completionHandler()
    }
}
#endif

// MARK: - Avatar Notification Model
struct AvatarNotification {
    enum NotificationType {
        case morph
        case error
        case rollback
        case rollout
    }

    let type: NotificationType
    let message: String
    let timestamp: Date = Date()
    let isCritical: Bool

    init(type: NotificationType, message: String, isCritical: Bool = false) {
        self.type = type
        self.message = message
        self.isCritical = isCritical
    }
}
