import SwiftUI

/// Service status view (stub for fast-track demo)
struct ServiceStatusView: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Service Status")
                .font(.headline)

            HStack {
                Circle()
                    .frame(width: 8, height: 8)
                    .foregroundStyle(.green)
                Text("Fast-Track Mode: Services mocked")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(Color(.textBackgroundColor).opacity(0.5))
        .cornerRadius(8)
    }
}
