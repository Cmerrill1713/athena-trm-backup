import SwiftUI

/// Floating diagnostics panel showing recent network activity
public struct DiagnosticsOverlay: View {
    @State private var recentEvents: [NetworkEvent] = []
    @State private var errorCounts: (e500: Int, e503: Int, e422: Int) = (0, 0, 0)

    public init() {}

    public var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("Network Diagnostics")
                    .font(.caption.bold())
                Spacer()
                Text("\(self.errorCounts.e500)×500 \(self.errorCounts.e503)×503 \(self.errorCounts.e422)×422")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 2) {
                    ForEach(Array(self.recentEvents.prefix(5)), id: \.timestamp) { event in
                        EventChip(event: event)
                    }
                }
            }
            .frame(maxHeight: 150)
        }
        .padding(8)
        .frame(width: 320)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color(nsColor: .controlBackgroundColor))
                .shadow(radius: 4)
        )
        .padding()
        .allowsHitTesting(false) // Don't steal clicks/typing
        .accessibilityHidden(true) // Hide from accessibility tree
        .onReceive(NotificationCenter.default.publisher(for: .networkEventRecorded)) { notification in
            self.updateFromNotification(notification)
        }
        .onAppear {
            self.updateEvents()
        }
    }

    private func updateFromNotification(_ notification: Notification) {
        guard let userInfo = notification.userInfo,
              let method = userInfo["method"] as? String,
              let url = userInfo["url"] as? String,
              let status = userInfo["status"] as? Int,
              let duration = userInfo["duration"] as? TimeInterval,
              let bytes = userInfo["bytes"] as? Int
        else {
            return
        }

        let event = NetworkEvent(
            method: method,
            url: url,
            statusCode: status,
            duration: duration,
            bytes: bytes,
            timestamp: Date()
        )

        self.recentEvents.insert(event, at: 0)
        if self.recentEvents.count > 20 {
            self.recentEvents.removeLast()
        }

        self.errorCounts = InterceptingURLProtocol.recentErrorCounts()
    }

    private func updateEvents() {
        self.recentEvents = InterceptingURLProtocol.getRecentEvents(limit: 20)
        self.errorCounts = InterceptingURLProtocol.recentErrorCounts()
    }
}

/// Visual chip for a single network event
private struct EventChip: View {
    let event: NetworkEvent

    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(self.statusColor)
                .frame(width: 6, height: 6)

            Text("\(self.event.method)")
                .font(.system(size: 9, weight: .medium, design: .monospaced))
                .frame(width: 35, alignment: .leading)

            Text("\(self.event.statusCode)")
                .font(.system(size: 9, weight: .semibold, design: .monospaced))
                .foregroundColor(self.statusColor)
                .frame(width: 30, alignment: .center)

            Text("\(Int(self.event.duration))ms")
                .font(.system(size: 9, design: .monospaced))
                .foregroundColor(.secondary)
                .frame(width: 40, alignment: .trailing)

            Text(self.shortURL)
                .font(.system(size: 9, design: .monospaced))
                .lineLimit(1)
                .truncationMode(.middle)
        }
        .padding(.vertical, 2)
        .padding(.horizontal, 4)
        .background(
            RoundedRectangle(cornerRadius: 4)
                .fill(self.statusColor.opacity(0.1))
        )
    }

    private var statusColor: Color {
        if self.event.statusCode >= 500, self.event.statusCode != 503 { return .red }
        if self.event.statusCode == 503 { return .orange }
        if self.event.statusCode == 422 { return .blue }
        if self.event.statusCode >= 400 { return .yellow }
        if self.event.statusCode >= 200, self.event.statusCode < 300 { return .green }
        return .gray
    }

    private var shortURL: String {
        let components = self.event.url.components(separatedBy: "/")
        if components.count > 2 {
            return "/" + components.suffix(2).joined(separator: "/")
        }
        return self.event.url
    }
}
