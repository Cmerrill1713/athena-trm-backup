import AppKit
import SwiftUI

/// Pure Apple system colors following Human Interface Guidelines
enum AppleColors {
    // MARK: - Primary Apple System Colors (macOS compatible)

    static let systemBlue = Color(.systemBlue)
    static let systemGray = Color(.systemGray)

    // MARK: - Custom Gray Scale (Apple-inspired)

    static let systemGray2 = Color(red: 0.85, green: 0.85, blue: 0.85)
    static let systemGray3 = Color(red: 0.75, green: 0.75, blue: 0.75)
    static let systemGray4 = Color(red: 0.65, green: 0.65, blue: 0.65)
    static let systemGray5 = Color(red: 0.55, green: 0.55, blue: 0.55)
    static let systemGray6 = Color(red: 0.45, green: 0.45, blue: 0.45)

    // MARK: - Apple Semantic Colors

    static let label = Color(.labelColor)
    static let secondaryLabel = Color(.secondaryLabelColor)
    static let tertiaryLabel = Color(.tertiaryLabelColor)
    static let quaternaryLabel = Color(.quaternaryLabelColor)

    // MARK: - Apple Background Colors

    static let controlBackground = Color(.controlBackgroundColor)
    static let textBackground = Color(.textBackgroundColor)
    static let windowBackground = Color(.windowBackgroundColor)
    static let underPageBackground = Color(.underPageBackgroundColor)

    // MARK: - Apple Status Colors

    static let systemGreen = Color(.systemGreen)
    static let systemOrange = Color(.systemOrange)
    static let systemRed = Color(.systemRed)
    static let systemYellow = Color(.systemYellow)

    // MARK: - Apple Accent (Respects user preference)

    static let accent = Color.accentColor

    // MARK: - Apple Messages Style

    enum Messages {
        static let userBubble = systemBlue
        static let otherBubble = controlBackground
        static let bubbleCornerRadius: CGFloat = 18
        static let bubbleShadow = Color.black.opacity(0.1)
        static let bubbleShadowRadius: CGFloat = 1
    }
}
