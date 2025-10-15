//
//  AvatarTypes.swift
//  AvatarKit - Shared platform types and enums
//

import Foundation

/// Avatar morph modes - shared across platforms
public enum AvatarMode: String, Codable, Equatable {
    case ghost      // Default ghost avatar
    case photoreal  // Photoreal avatar (iOS only)
    case morphing   // Currently morphing between states
}

/// Avatar status - shared data structure
public struct AvatarStatus: Codable, Equatable {
    public var state: AvatarMode
    public var identity: String?
    public var awarenessLevel: Double?
    public var lastUpdated: Date
    public var healthy: Bool

    public init(
        state: AvatarMode = .ghost,
        identity: String? = nil,
        awarenessLevel: Double? = nil,
        lastUpdated: Date = Date(),
        healthy: Bool = true
    ) {
        self.state = state
        self.identity = identity
        self.awarenessLevel = awarenessLevel
        self.lastUpdated = lastUpdated
        self.healthy = healthy
    }
}

/// Avatar morph request - API contract
public struct AvatarMorphRequest: Codable {
    public let to: String  // AvatarMode rawValue

    public init(to: AvatarMode) {
        self.to = to.rawValue
    }
}

/// Avatar morph response - API contract
public struct AvatarMorphResponse: Codable {
    public let success: Bool
    public let message: String?
    public let newState: AvatarMode?

    public init(success: Bool, message: String? = nil, newState: AvatarMode? = nil) {
        self.success = success
        self.message = message
        self.newState = newState
    }
}

/// Morph feature toggle - centralized control
public enum MorphFeature {
    /// Runtime feature flag - controlled by environment
    public static var enabled: Bool {
        ProcessInfo.processInfo.environment["MORPH_ENABLED"] == "true"
    }

    /// Compile-time check for morph availability on platform
    public static var available: Bool {
        #if os(iOS)
        return true  // iOS supports full morphing
        #else
        return false // macOS only supports ghost
        #endif
    }

    /// Combined check: enabled AND available
    public static var active: Bool {
        enabled && available
    }
}

/// Hysteresis configuration - prevents oscillation
public struct MorphHysteresis {
    public static let morphAbove: Double = 0.65  // Start morphing above this awareness
    public static let revertBelow: Double = 0.45 // Revert to ghost below this awareness

    /// Determine if should morph based on awareness level with hysteresis
    public static func shouldMorph(from currentMode: AvatarMode, awarenessLevel: Double) -> Bool {
        switch currentMode {
        case .ghost:
            return awarenessLevel >= morphAbove
        case .photoreal, .morphing:
            return awarenessLevel >= revertBelow
        }
    }
}

