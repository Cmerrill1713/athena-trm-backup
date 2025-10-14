import SwiftUI

struct SystemEmergencyWindow: View {
    @State var emergency: SystemEmergency
    @State private var remaining: Int

    init(emergency: SystemEmergency) {
        self.emergency = emergency
        self._remaining = State(initialValue: emergency.countdownSeconds)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("🚨 SYSTEM EMERGENCY").font(.title.bold()).foregroundColor(.red)

            HStack {
                Text(self.emergency.title).font(.headline)
                Spacer()
                Text("Risk: \(self.emergency.risk.rawValue.uppercased())").bold()
            }

            Text(self.emergency.analysis).font(.body)

            if !self.emergency.actions.isEmpty {
                Divider()
                Text("Emergency Actions").font(.subheadline.bold())
                ForEach(self.emergency.actions, id: \.self) { a in
                    Text("• \(a)")
                }
            }

            HStack {
                Text("Auto-execute in \(self.remaining)s")
                    .monospacedDigit()
                Spacer()
                Button("Execute Now") { /* execute action */ }
                    .buttonStyle(.borderedProminent)
            }
        }
        .padding(16)
        .onAppear {
            // simple countdown (no timers retained after window closes)
            Task { @MainActor in
                while self.remaining > 0 {
                    try? await Task.sleep(nanoseconds: 1_000_000_000)
                    self.remaining -= 1
                }
                // auto-execute hook here
            }
        }
        .frame(minWidth: 640)
    }
}
