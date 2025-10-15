import SwiftUI

// MARK: - NeuroForge Design System

enum DesignSystem {

    // MARK: - Colors
    enum Colors {
        static let bridge = Color(red: 0.2, green: 0.6, blue: 1.0)
        static let athena = Color(red: 0.8, green: 0.4, blue: 1.0)
        static let uat = Color(red: 1.0, green: 0.6, blue: 0.2)
        static let kokoro = Color(red: 0.2, green: 0.8, blue: 0.6)

        static let successGreen = Color(red: 0.2, green: 0.8, blue: 0.4)
        static let warningYellow = Color(red: 1.0, green: 0.8, blue: 0.2)
        static let errorRed = Color(red: 1.0, green: 0.3, blue: 0.3)

        static let glassBorder = Color.white.opacity(0.2)
        static let glassBackground = Color.white.opacity(0.05)
    }

    // MARK: - Typography
    enum Typography {
        static let largeTitle = Font.system(size: 28, weight: .bold, design: .rounded)
        static let title = Font.system(size: 20, weight: .semibold, design: .rounded)
        static let headline = Font.system(size: 16, weight: .semibold, design: .rounded)
        static let body = Font.system(size: 14, weight: .regular, design: .default)
        static let caption = Font.system(size: 12, weight: .medium, design: .default)
        static let mono = Font.system(size: 13, weight: .regular, design: .monospaced)
    }

    // MARK: - Spacing
    enum Spacing {
        static let xs: CGFloat = 4
        static let sm: CGFloat = 8
        static let md: CGFloat = 12
        static let lg: CGFloat = 16
        static let xl: CGFloat = 24
        static let xxl: CGFloat = 32
    }

    // MARK: - Corner Radius
    enum Radius {
        static let sm: CGFloat = 8
        static let md: CGFloat = 12
        static let lg: CGFloat = 16
        static let xl: CGFloat = 20
        static let round: CGFloat = 999
    }

    // MARK: - Animations
    enum Animation {
        static let springy = SwiftUI.Animation.spring(response: 0.4, dampingFraction: 0.7)
        static let smooth = SwiftUI.Animation.easeInOut(duration: 0.3)
        static let quick = SwiftUI.Animation.easeOut(duration: 0.2)
    }
}

// MARK: - Glassmorphism Modifiers

struct GlassCardModifier: ViewModifier {
    var intensity: Double = 0.3
    var borderOpacity: Double = 0.2

    func body(content: Content) -> some View {
        content
            .background(
                RoundedRectangle(cornerRadius: DesignSystem.Radius.lg, style: .continuous)
                    .fill(.ultraThinMaterial.opacity(intensity))
                    .overlay(
                        RoundedRectangle(cornerRadius: DesignSystem.Radius.lg, style: .continuous)
                            .strokeBorder(DesignSystem.Colors.glassBorder.opacity(borderOpacity), lineWidth: 1)
                    )
                    .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 4)
            )
    }
}

struct PulsatingModifier: ViewModifier {
    @State private var isAnimating = false
    var color: Color
    var duration: Double = 2.0

    func body(content: Content) -> some View {
        content
            .overlay(
                Circle()
                    .stroke(color.opacity(0.4), lineWidth: 2)
                    .scaleEffect(isAnimating ? 1.5 : 1.0)
                    .opacity(isAnimating ? 0 : 1)
            )
            .onAppear {
                withAnimation(.easeOut(duration: duration).repeatForever(autoreverses: false)) {
                    isAnimating = true
                }
            }
    }
}

extension View {
    func glassCard(intensity: Double = 0.3, borderOpacity: Double = 0.2) -> some View {
        modifier(GlassCardModifier(intensity: intensity, borderOpacity: borderOpacity))
    }

    func pulsating(color: Color, duration: Double = 2.0) -> some View {
        modifier(PulsatingModifier(color: color, duration: duration))
    }
}

// MARK: - Service Status Badge

struct ServiceStatusBadge: View {
    let name: String
    let status: ServiceStatus
    let color: Color

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(statusColor)
                .frame(width: 8, height: 8)
                .pulsating(color: statusColor, duration: status == .healthy ? 2.5 : 1.5)

            Text(name)
                .font(DesignSystem.Typography.caption)
                .fontWeight(.medium)
        }
        .padding(.horizontal, DesignSystem.Spacing.md)
        .padding(.vertical, DesignSystem.Spacing.sm)
        .glassCard(intensity: 0.2)
    }

    private var statusColor: Color {
        switch status {
        case .healthy: return DesignSystem.Colors.successGreen
        case .degraded: return DesignSystem.Colors.warningYellow
        case .down: return DesignSystem.Colors.errorRed
        }
    }

    enum ServiceStatus {
        case healthy, degraded, down
    }
}

// MARK: - Confidence Meter

struct ConfidenceMeter: View {
    let confidence: Double
    var showLabel: Bool = true

    private var color: Color {
        if confidence >= 0.75 { return DesignSystem.Colors.successGreen }
        if confidence >= 0.45 { return DesignSystem.Colors.warningYellow }
        return DesignSystem.Colors.errorRed
    }

    var body: some View {
        VStack(spacing: DesignSystem.Spacing.sm) {
            if showLabel {
                HStack {
                    Text("Confidence")
                        .font(DesignSystem.Typography.caption)
                        .foregroundStyle(.secondary)
                    Spacer()
                    Text("\(Int(confidence * 100))%")
                        .font(DesignSystem.Typography.caption)
                        .fontWeight(.bold)
                        .foregroundStyle(color)
                }
            }

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    // Background
                    RoundedRectangle(cornerRadius: DesignSystem.Radius.round)
                        .fill(Color.secondary.opacity(0.2))

                    // Progress bar
                    RoundedRectangle(cornerRadius: DesignSystem.Radius.round)
                        .fill(
                            LinearGradient(
                                colors: [color.opacity(0.8), color],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .frame(width: geo.size.width * confidence)
                        .shadow(color: color.opacity(0.5), radius: 4, x: 0, y: 2)
                }
            }
            .frame(height: 6)
        }
        .animation(DesignSystem.Animation.springy, value: confidence)
    }
}
