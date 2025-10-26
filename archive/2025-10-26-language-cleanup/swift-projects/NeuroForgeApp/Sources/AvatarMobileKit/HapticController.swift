//
//  HapticController.swift
//  AvatarMobileKit - iOS-only haptic feedback for avatar interactions
//

#if os(iOS)
    import UIKit

    /// Haptic feedback controller for avatar interactions - iOS only
    public enum HapticController {
        /// Light impact for successful morph completion
        public static func morphSuccess() {
            UIImpactFeedbackGenerator(style: .light).impactOccurred()
        }

        /// Medium impact for morph initiation
        public static func morphStart() {
            UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        }

        /// Heavy impact for morph failure or error
        public static func morphError() {
            UIImpactFeedbackGenerator(style: .heavy).impactOccurred()
        }

        /// Warning notification for rollback events
        public static func rollbackWarning() {
            UINotificationFeedbackGenerator().notificationOccurred(.warning)
        }

        /// Success notification for completed operations
        public static func operationSuccess() {
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        }

        /// Selection feedback for UI interactions
        public static func selection() {
            UISelectionFeedbackGenerator().selectionChanged()
        }
    }

#else

    // MARK: - Stub Implementation for non-iOS platforms

    /// Stub implementation for non-iOS platforms - no-op
    public enum HapticController {
        public static func morphSuccess() { /* no-op */ }
        public static func morphStart() { /* no-op */ }
        public static func morphError() { /* no-op */ }
        public static func rollbackWarning() { /* no-op */ }
        public static func operationSuccess() { /* no-op */ }
        public static func selection() { /* no-op */ }
    }

#endif
