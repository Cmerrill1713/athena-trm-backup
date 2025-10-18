import SwiftUI

/// Latency badge that reflects current router route and p95 latency
public struct LatencyBadge: View {
    let route: String
    let latencyMs: Int
    let isHealthy: Bool

    public init(route: String, latencyMs: Int, isHealthy: Bool = true) {
        self.route = route
        self.latencyMs = latencyMs
        self.isHealthy = isHealthy
    }

    private var badgeColor: Color {
        if !isHealthy {
            return AppleColors.systemRed
        }

        switch latencyMs {
        case 0..<50:
            return AppleColors.systemGreen
        case 50..<200:
            return AppleColors.systemOrange
        default:
            return AppleColors.systemRed
        }
    }

    private var routeIcon: String {
        switch route.lowercased() {
        case "mlx":
            return "bolt.horizontal.circle.fill"
        case "ollama":
            return "server.rack"
        case "cloud":
            return "cloud.fill"
        case "mcp":
            return "link.circle.fill"
        default:
            return "questionmark.circle.fill"
        }
    }

    private var latencyText: String {
        if latencyMs < 1000 {
            return "\(latencyMs)ms"
        } else {
            return String(format: "%.1fs", Double(latencyMs) / 1000.0)
        }
    }

    public var body: some View {
        HStack(spacing: 4) {
            Image(systemName: routeIcon)
                .font(.system(size: 10, weight: .semibold))
                .foregroundColor(.white)

            Text(route.uppercased())
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundColor(.white)

            Text(latencyText)
                .font(.system(size: 9, weight: .medium, design: .monospaced))
                .foregroundColor(.white.opacity(0.8))
        }
        .padding(.horizontal, 6)
        .padding(.vertical, 3)
        .background(
            Capsule()
                .fill(badgeColor)
                .shadow(color: badgeColor.opacity(0.3), radius: 2, x: 0, y: 1)
        )
        .animation(.easeInOut(duration: 0.2), value: latencyMs)
        .animation(.easeInOut(duration: 0.2), value: route)
        .allowsHitTesting(false)  // Passive - never steals events or focus
        .accessibilityLabel("Router: \(route), Latency: \(latencyText)")
    }
}

// MARK: - Preview
#if DEBUG
    struct LatencyBadge_Previews: PreviewProvider {
        static var previews: some View {
            VStack(spacing: 8) {
                LatencyBadge(route: "mlx", latencyMs: 15, isHealthy: true)
                LatencyBadge(route: "ollama", latencyMs: 150, isHealthy: true)
                LatencyBadge(route: "cloud", latencyMs: 2500, isHealthy: true)
                LatencyBadge(route: "mcp", latencyMs: 45, isHealthy: false)
            }
            .padding()
            .background(AppleColors.controlBackground)
        }
    }
#endif
