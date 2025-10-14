import SwiftUI

struct TribunalDecisionWindow: View {
    let `case`: TribunalCase
    @State private var selection: TribunalDecisionOption = .uphold
    @State private var notes: String = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("⚖️ Tribunal Decision Required")
                .font(.title.bold())

            Text("Case: \(self.case.caseID)").font(.headline)
            Text(self.case.summary).font(.body)
            Text("AI Recommendation: \(self.case.aiRecommendation.rawValue.uppercased()) (\(Int(self.case.confidence * 100))%)")
                .font(.subheadline).foregroundStyle(.secondary)

            Picker("Decision", selection: self.$selection) {
                ForEach(TribunalDecisionOption.allCases, id: \.self) { opt in
                    Text(opt.rawValue.capitalized).tag(opt)
                }
            }

            TextField("Decision notes (required for Modify/Overturn)", text: self.$notes)
                .textFieldStyle(.roundedBorder)

            HStack {
                Button("Submit") {
                    // Validate notes for modify/overturn, then log decision
                }
                .buttonStyle(.borderedProminent)

                Spacer()

                Button("Escalate") { /* escalation hook */ }
                Button("Request Extension") { /* extension hook */ }
            }
        }
        .padding(16)
        .frame(minWidth: 620)
    }
}
