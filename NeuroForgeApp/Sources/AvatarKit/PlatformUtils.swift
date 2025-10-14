//
//  PlatformUtils.swift
//  AvatarKit - Shared platform detection and utilities
//

import Foundation

// MARK: - Platform Detection

/// Platform detection constants - use these instead of #if os() in logic
public enum Platform {
    /// True if running on iOS (iPhone/iPad)
    public static let isIOS: Bool = {
        #if os(iOS)
        return true
        #else
        return false
        #endif
    }()

    /// True if running on macOS
    public static let isMacOS: Bool = {
        #if os(macOS)
        return true
        #else
        return false
        #endif
    }()

    /// True if running on iOS simulator
    public static let isSimulator: Bool = {
        #if targetEnvironment(simulator)
        return true
        #else
        return false
        #endif
    }()

    /// Human-readable platform name
    public static var name: String {
        if isIOS {
            return isSimulator ? "iOS Simulator" : "iOS"
        } else if isMacOS {
            return "macOS"
        } else {
            return "Unknown"
        }
    }
}

// MARK: - Feature Availability

/// Feature availability checks based on platform
public enum FeatureAvailability {
    /// Avatar morphing capabilities available on this platform
    public static var avatarMorphing: Bool {
        Platform.isIOS  // Only iOS supports full morphing currently
    }

    /// Mobile notifications available
    public static var notifications: Bool {
        Platform.isIOS  // Only iOS has local notifications
    }

    /// Haptic feedback available
    public static var haptics: Bool {
        Platform.isIOS  // Only iOS has Taptic Engine
    }

    /// Authentication interceptor available
    public static var authInterceptor: Bool {
        Platform.isIOS  // Only iOS needs mobile auth
    }
}

// MARK: - Network Utilities

/// Network configuration for different platforms
public enum NetworkConfig {
    /// Default backend URL - can be overridden by environment
    public static var defaultBaseURL: URL {
        if let envURL = ProcessInfo.processInfo.environment["AVATAR_BASE_URL"],
           let url = URL(string: envURL) {
            return url
        }

        // Platform-specific defaults
        if Platform.isIOS {
            // On iOS, default to localhost for development
            return URL(string: "http://localhost:8035")!
        } else {
            // On macOS, use localhost
            return URL(string: "http://localhost:8035")!
        }
    }

    /// Timeout for avatar operations
    public static var avatarTimeout: TimeInterval {
        Platform.isSimulator ? 30.0 : 10.0  // Longer timeout for simulator
    }
}

// MARK: - Logging Utilities

/// Platform-aware logging for avatar operations
public enum AvatarLogger {
    public static func debug(_ message: String) {
        #if DEBUG
        print("[AvatarKit] \(message)")
        #endif
    }

    public static func info(_ message: String) {
        print("[AvatarKit] \(message)")
    }

    public static func error(_ message: String) {
        print("[AvatarKit ERROR] \(message)")
    }

    public static func morphEvent(from: AvatarMode, to: AvatarMode, awareness: Double? = nil) {
        let awarenessStr = awareness.map { String(format: " (awareness: %.2f)", $0) } ?? ""
        info("Morph: \(from.rawValue) → \(to.rawValue)\(awarenessStr)")
    }
}

// MARK: - Type Aliases for Compatibility

/// Backward compatibility aliases
@available(*, deprecated, renamed: "AvatarMode", message: "Use AvatarMode directly")
public typealias AvatarMorphMode = AvatarMode

@available(*, deprecated, renamed: "AvatarStatus", message: "Use AvatarStatus directly")
public typealias AvatarState = AvatarStatus
