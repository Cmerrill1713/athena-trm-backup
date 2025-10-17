import SwiftUI

struct CriticalAlertWindow: View {
    let alert: CriticalAlert

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("🚨 Critical Alert")
                .font(.title.bold())
                .foregroundColor(.red)

            Text(alert.title).font(.headline)
            Text(alert.message).font(.body)

            if !alert.affectedSystems.isEmpty {
                Divider()
                Text("Affected Systems").font(.subheadline.bold())
                ForEach(alert.affectedSystems, id: \.self) { s in
                    Text("• \(s)")
                }
            }

            if !alert.recommendations.isEmpty {
                Divider()
                Text("Recommendations").font(.subheadline.bold())
                ForEach(alert.recommendations, id: \.self) { r in
                    Text("• \(r)")
                }
            }

            HStack {
                Button("Acknowledge") { /* log/telemetry hook */ }
                Button("Investigate") { /* deep link hook */ }
                Button("Snooze 10m") { /* schedule hook */ }
            }
            .buttonStyle(.borderedProminent)
            .padding(.top, 8)
        }
        .padding(16)
        .frame(minWidth: 520)
    }
}
