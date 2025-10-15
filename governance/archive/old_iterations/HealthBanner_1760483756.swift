import SwiftUI

// Uses apiBaseURL() function from APIBase.swift

/// Displays backend health status with autodiscovery and reconnect
public struct HealthBanner: View {
    enum HealthState { case checking, ok, degraded503, error, reconnecting }

    @State private var state: HealthState = .checking
    @State private var text = "Checking backend..."
    @State private var currentURL = ""

    private let client = APIClient()

    public init() {}

    public var body: some View {
        HStack(spacing: 8) {
            Circle()
                .frame(width: 8, height: 8)
                .foregroundStyle(self.color)

            VStack(alignment: .leading, spacing: 2) {
                Text(self.text)
                    .font(.caption)
                if !self.currentURL.isEmpty {
                    Text(self.currentURL)
                        .font(.system(size: 9))
                        .foregroundColor(.secondary)
                }
            }

            Spacer()

            // Reconnect button temporarily disabled due to Swift concurrency constraints
            // TODO: Implement reconnect with proper MainActor isolation
        }
        .padding(6)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(self.color.opacity(0.12))
        )
        .accessibilityIdentifier("health_banner")
        .task { @MainActor in
            await self.check()
        }
        .onReceive(Timer.publish(every: 30, on: .main, in: .common).autoconnect()) { _ in
            Task { @MainActor in await self.check() }
        }
    }

    private var color: Color {
        switch self.state {
        case .ok: .green
        case .degraded503: .yellow
        case .checking, .reconnecting: .gray
        case .error: .red
        }
    }

    @MainActor
    private func check() async {
        struct Health: Decodable { let status: String? }

        self.currentURL = apiBaseURL().absoluteString

        do {
            let _: Health = try await client.get("/health")
            self.state = .ok
            self.text = "Connected"
        } catch APIError.service503 {
            self.state = .degraded503
            self.text = "Degraded (503)"
        } catch let APIError.transport(error) {
            state = .error
            text = "Disconnected"
            print("❌ Health check failed: \(error.localizedDescription)")
        } catch {
            self.state = .error
            self.text = "Disconnected"
            print("❌ Health check failed: \(error.localizedDescription)")
        }
    }
}
