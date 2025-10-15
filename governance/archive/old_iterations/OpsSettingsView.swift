import SwiftUI

/// Quick settings for Operations window behavior
struct OpsSettingsView: View {
    @AppStorage("autoOpenOps") private var autoOpenOps = true
    @AppStorage("opsConfidenceThreshold") private var opsConfidenceThreshold: Double = 0.35
    @AppStorage("showMetaPanels") private var showMetaPanels = true
    @EnvironmentObject var ops: OpsState
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        Form {
            Section {
                Toggle("Auto-open Operations window", isOn: $autoOpenOps)
                    .help("Automatically open Ops window on low confidence or errors")

                if autoOpenOps {
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text("Confidence threshold:")
                            Spacer()
                            Text("\(Int(opsConfidenceThreshold * 100))%")
                                .foregroundStyle(.secondary)
                        }
                        Slider(value: $opsConfidenceThreshold, in: 0.0...0.8, step: 0.05)
                        Text("Open Ops when confidence falls below this level")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            } header: {
                Label("Operations Window", systemImage: "rectangle.badge.plus")
            } footer: {
                if autoOpenOps {
                    Text("Ops will open automatically when confidence is below \(Int(opsConfidenceThreshold * 100))% or when errors are detected.")
                } else {
                    Text("Manually open Ops with ⌘⌥O or the toolbar button.")
                }
            }

            Section {
                Toggle("Show meta-prompt panels", isOn: $showMetaPanels)
                    .help("Display confidence and meta info below each message")
            } header: {
                Label("Meta-Prompt Display", systemImage: "brain")
            }

            Section {
                HStack(spacing: 8) {
                    Button("Snooze 30 min") {
                        ops.snooze(minutes: 30)
                        dismiss()
                    }
                    .buttonStyle(.bordered)

                    Button("Snooze 2 hours") {
                        ops.snooze(minutes: 120)
                        dismiss()
                    }
                    .buttonStyle(.bordered)
                }
            } header: {
                Label("Quick Actions", systemImage: "moon.zzz")
            } footer: {
                Text("Temporarily disable auto-open without changing settings")
            }

            Section {
                Button("Restore Defaults") {
                    autoOpenOps = true
                    opsConfidenceThreshold = 0.35
                    showMetaPanels = true
                    ops.resetSession()
                }
                .buttonStyle(.bordered)
            }
        }
        .formStyle(.grouped)
        .frame(width: 450, height: 300)
        .toolbar {
            ToolbarItem(placement: .confirmationAction) {
                Button("Done") {
                    dismiss()
                }
            }
        }
    }
}

#Preview {
    OpsSettingsView()
}
