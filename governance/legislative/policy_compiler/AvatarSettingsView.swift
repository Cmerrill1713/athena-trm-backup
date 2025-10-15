//
//  AvatarSettingsView.swift
//  Athena Avatar Settings
//
//  Optional settings panel for avatar behavior controls
//

import SwiftUI

/// Settings model for avatar behavior (persisted via UserDefaults)
final class AvatarSettings: ObservableObject {
    @AppStorage("avatar_morphEnabled") var morphEnabled = true
    @AppStorage("avatar_mode") var avatarMode = "auto" // "ghost", "photoreal", "auto"
    @AppStorage("avatar_morphUp") var morphUpThreshold: Double = 0.65
    @AppStorage("avatar_morphDown") var morphDownThreshold: Double = 0.45
    @AppStorage("avatar_soundEnabled") var soundEnabled = true

    var currentMode: AvatarMode {
        switch avatarMode {
        case "ghost": return .ghost
        case "photoreal": return .photoreal
        case "auto": return .auto
        default: return .auto
        }
    }

    func setMode(_ mode: AvatarMode) {
        switch mode {
        case .ghost: avatarMode = "ghost"
        case .photoreal: avatarMode = "photoreal"
        case .auto: avatarMode = "auto"
        }
    }
}

/// Avatar behavior modes
enum AvatarMode: String, CaseIterable {
    case ghost = "ghost"
    case photoreal = "photoreal"
    case auto = "auto"

    var displayName: String {
        switch self {
        case .ghost: return "Always Ghost"
        case .photoreal: return "Always Photoreal"
        case .auto: return "Auto (Awareness-Driven)"
        }
    }

    var description: String {
        switch self {
        case .ghost:
            return "Always show ghost avatar - minimal resources, consistent experience"
        case .photoreal:
            return "Always show photoreal avatar - maximum fidelity, higher resources"
        case .auto:
            return "Automatically morph based on awareness levels - adaptive experience"
        }
    }
}

/// Settings view for avatar behavior configuration
struct AvatarSettingsView: View {
    @StateObject private var settings = AvatarSettings()
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section(header: Text("Avatar Mode")) {
                    Picker("Mode", selection: $settings.avatarMode) {
                        ForEach(AvatarMode.allCases, id: \.rawValue) { mode in
                            VStack(alignment: .leading, spacing: 4) {
                                Text(mode.displayName)
                                    .font(.headline)
                                Text(mode.description)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            .tag(mode.rawValue)
                        }
                    }
                    .pickerStyle(.inline)
                }

                Section(header: Text("Morphing Behavior")) {
                    Toggle("Enable Morphing", isOn: $settings.morphEnabled)
                        .disabled(settings.avatarMode != "auto")

                    if settings.morphEnabled && settings.avatarMode == "auto" {
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text("Morph Up Threshold")
                                Spacer()
                                Text(String(format: "%.2f", settings.morphUpThreshold))
                                    .foregroundColor(.secondary)
                            }
                            Slider(value: $settings.morphUpThreshold, in: 0.5...0.9, step: 0.05)
                            Text("When awareness exceeds this level, morph to photoreal")
                                .font(.caption)
                                .foregroundColor(.secondary)

                            Divider()

                            HStack {
                                Text("Morph Down Threshold")
                                Spacer()
                                Text(String(format: "%.2f", settings.morphDownThreshold))
                                    .foregroundColor(.secondary)
                            }
                            Slider(value: $settings.morphDownThreshold, in: 0.1...0.5, step: 0.05)
                            Text("When awareness drops below this level, morph to ghost")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .padding(.vertical, 4)
                    }
                }

                Section(header: Text("Audio Feedback")) {
                    Toggle("Sound Effects", isOn: $settings.soundEnabled)
                    Text("Play subtle sounds during morph transitions")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Section {
                    Button("Reset to Defaults") {
                        resetToDefaults()
                    }
                    .foregroundColor(.red)
                }
            }
            .navigationTitle("Avatar Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }

    private func resetToDefaults() {
        settings.morphEnabled = true
        settings.avatarMode = "auto"
        settings.morphUpThreshold = 0.65
        settings.morphDownThreshold = 0.45
        settings.soundEnabled = true
    }
}

// MARK: - Preview

#if DEBUG
struct AvatarSettingsView_Previews: PreviewProvider {
    static var previews: some View {
        AvatarSettingsView()
            .preferredColorScheme(.light)

        AvatarSettingsView()
            .preferredColorScheme(.dark)
    }
}
#endif
