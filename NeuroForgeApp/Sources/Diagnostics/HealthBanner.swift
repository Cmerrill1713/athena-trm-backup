import SwiftUI

struct HealthBanner: View {
    @State private var healthy = false
    @State private var checking = false
    let api = APIClient()

    var body: some View {
        HStack(spacing: 8) {
            Circle()
              .fill(healthy ? Color.green : Color.red)
              .frame(width: 10, height: 10)
            Text(healthy ? "Connected" : "Disconnected backend")
                .font(.caption)
            Spacer()
            Button(checking ? "…" : "Reconnect") {
                Task { await runCheck() }
            }
            .disabled(checking)
            .accessibilityIdentifier("reconnect_button")
        }
        .padding(8)
        .background(.thinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .accessibilityIdentifier("health_banner")
        .task { await runCheck() }
    }
    private func runCheck() async {
        checking = true
        defer { checking = false }
        healthy = await api.health()
    }
}
