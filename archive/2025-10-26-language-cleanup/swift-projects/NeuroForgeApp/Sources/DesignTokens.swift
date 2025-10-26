import SwiftUI

// MARK: - Design Tokens

enum NFToken {
    // Spacing
    enum Spacing {
        static let xs: CGFloat = 6
        static let sm: CGFloat = 10
        static let md: CGFloat = 12
        static let lg: CGFloat = 16
        static let xl: CGFloat = 24
        static let xxl: CGFloat = 32
    }

    // Corner Radius
    enum Radius {
        static let sm: CGFloat = 8
        static let md: CGFloat = 12
        static let lg: CGFloat = 16
        static let xl: CGFloat = 24
    }

    // Typography
    enum Typography {
        static let title = Font.system(size: 18, weight: .semibold)
        static let headline = Font.system(size: 16, weight: .medium)
        static let body = Font.system(size: 14)
        static let caption = Font.system(size: 12)
        static let mono = Font.system(size: 12, design: .monospaced)
    }

    // Colors
    enum Color {
        static let background = SwiftUI.Color(NSColor.windowBackgroundColor)
        static let secondaryBackground = SwiftUI.Color(NSColor.controlBackgroundColor)
        static let card = SwiftUI.Color.secondary.opacity(0.1)
        static let accent = SwiftUI.Color.accentColor
        static let success = SwiftUI.Color.green
        static let warning = SwiftUI.Color.orange
        static let error = SwiftUI.Color.red
        static let text = SwiftUI.Color.primary
        static let textSecondary = SwiftUI.Color.secondary
    }

    // Shadow parameters (not a type)
    enum ShadowParams {
        static let soft = (color: SwiftUI.Color.black.opacity(0.1), radius: 4.0, x: 0.0, y: 2.0)
        static let medium = (color: SwiftUI.Color.black.opacity(0.15), radius: 8.0, x: 0.0, y: 4.0)
    }
}

// MARK: - Reusable Components

struct NFCard<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: NFToken.Spacing.md) {
            content
        }
        .padding(NFToken.Spacing.lg)
        .background(NFToken.Color.card)
        .clipShape(RoundedRectangle(cornerRadius: NFToken.Radius.md))
        .shadow(
            color: NFToken.ShadowParams.soft.color,
            radius: NFToken.ShadowParams.soft.radius,
            x: NFToken.ShadowParams.soft.x,
            y: NFToken.ShadowParams.soft.y
        )
    }
}

struct NFButton: View {
    let title: String
    let action: () -> Void
    let style: Style
    let isEnabled: Bool

    enum Style {
        case primary
        case secondary
        case danger
    }

    init(
        _ title: String, style: Style = .primary, isEnabled: Bool = true,
        action: @escaping () -> Void
    ) {
        self.title = title
        self.style = style
        self.isEnabled = isEnabled
        self.action = action
    }

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(NFToken.Typography.body.weight(.medium))
                .foregroundColor(buttonColor)
                .padding(.horizontal, NFToken.Spacing.lg)
                .padding(.vertical, NFToken.Spacing.md)
                .frame(minWidth: 80)
                .background(buttonBackground)
                .clipShape(RoundedRectangle(cornerRadius: NFToken.Radius.sm))
                .overlay(
                    RoundedRectangle(cornerRadius: NFToken.Radius.sm)
                        .stroke(buttonBorder, lineWidth: 1)
                )
        }
        .disabled(!isEnabled)
        .opacity(isEnabled ? 1.0 : 0.6)
    }

    private var buttonColor: Color {
        if !isEnabled { return NFToken.Color.textSecondary }
        switch style {
        case .primary: return .white
        case .secondary, .danger: return NFToken.Color.accent
        }
    }

    private var buttonBackground: Color {
        if !isEnabled { return NFToken.Color.secondaryBackground }
        switch style {
        case .primary: return NFToken.Color.accent
        case .secondary: return .clear
        case .danger: return NFToken.Color.error.opacity(0.1)
        }
    }

    private var buttonBorder: Color {
        switch style {
        case .primary: return .clear
        case .secondary: return NFToken.Color.accent.opacity(0.3)
        case .danger: return NFToken.Color.error
        }
    }
}

struct NFStatusIndicator: View {
    let status: Status
    let message: String

    enum Status {
        case success
        case warning
        case error
        case info
    }

    var body: some View {
        HStack(spacing: NFToken.Spacing.sm) {
            Circle()
                .fill(statusColor)
                .frame(width: 8, height: 8)

            Text(message)
                .font(NFToken.Typography.caption)
                .foregroundColor(statusTextColor)
        }
        .padding(.horizontal, NFToken.Spacing.md)
        .padding(.vertical, NFToken.Spacing.sm)
        .background(statusBackground)
        .clipShape(Capsule())
    }

    private var statusColor: Color {
        switch status {
        case .success: return NFToken.Color.success
        case .warning: return NFToken.Color.warning
        case .error: return NFToken.Color.error
        case .info: return NFToken.Color.accent
        }
    }

    private var statusTextColor: Color {
        switch status {
        case .success: return NFToken.Color.success.opacity(0.8)
        case .warning: return NFToken.Color.warning.opacity(0.8)
        case .error: return NFToken.Color.error.opacity(0.8)
        case .info: return NFToken.Color.textSecondary
        }
    }

    private var statusBackground: Color {
        switch status {
        case .success: return NFToken.Color.success.opacity(0.1)
        case .warning: return NFToken.Color.warning.opacity(0.1)
        case .error: return NFToken.Color.error.opacity(0.1)
        case .info: return NFToken.Color.secondaryBackground
        }
    }
}

// MARK: - Previews

#Preview("Design Tokens") {
    VStack(spacing: NFToken.Spacing.lg) {
        NFCard {
            Text("Card Title")
                .font(NFToken.Typography.title)
            Text("Card content with some description text.")
                .font(NFToken.Typography.body)
        }

        HStack(spacing: NFToken.Spacing.md) {
            NFButton("Primary", style: .primary) {}
            NFButton("Secondary", style: .secondary) {}
            NFButton("Disabled", isEnabled: false) {}
        }

        NFStatusIndicator(status: .success, message: "Operation successful")
        NFStatusIndicator(status: .warning, message: "Check configuration")
        NFStatusIndicator(status: .error, message: "Connection failed")
    }
    .padding(NFToken.Spacing.xl)
    .background(NFToken.Color.background)
}
