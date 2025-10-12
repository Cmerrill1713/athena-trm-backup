// Sources/NeuroForgeApp/Diagnostics/ProviderInspectorOverlay.swift
import SwiftUI

struct ProviderInspectorOverlay: View {
    @ObservedObject var vm = ProviderOverrideManager.shared
    @State private var isVisible: Bool = true

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Provider Inspector")
                    .font(.headline)
                Spacer()
                Button(vm.active == .auto ? "Auto" : "Reset Auto") {
                    vm.resetToAuto()
                }
                .keyboardShortcut("0", modifiers: [.command, .shift])
                .accessibilityIdentifier("reset_auto_button")
            }

            Picker("Route", selection: $vm.active) {
                ForEach(ProviderRoute.allCases, id: \.self) { r in
                    Text(label(r)).tag(r)
                }
            }
            .pickerStyle(.segmented)
            .onChange(of: vm.active) { _, newValue in
                Task { await vm.pushToBackendIfSupported() }
            }
            .accessibilityIdentifier("provider_picker")

            Divider().padding(.vertical, 4)

            HStack {
                Text("Remote Override:")
                    .font(.caption)
                Circle()
                    .fill(vm.remoteApplied ? .green : .gray)
                    .frame(width: 10, height: 10)
                Text(vm.remoteApplied ? "applied" : "client-side header")
                    .foregroundStyle(.secondary)
                    .font(.caption)
                Spacer()
                Button("Refresh Health") {
                    Task { await vm.refreshHealth() }
                }
                .keyboardShortcut("R", modifiers: [.command, .shift])
                .accessibilityIdentifier("refresh_health_button")
            }

            VStack(alignment: .leading, spacing: 8) {
                ForEach(ProviderRoute.allCases, id: \.self) { r in
                    let h = vm.health[r]
                    HStack {
                        Text(label(r))
                            .frame(width: 100, alignment: .leading)
                            .font(.body)
                        Circle()
                            .fill((h?.healthy ?? false) ? .green : .red)
                            .frame(width: 10, height: 10)
                        Text(latencyText(h?.latencyMs))
                            .foregroundStyle(latencyColor(h?.latencyMs))
                            .font(.caption)
                        Spacer()
                        if vm.active == r {
                            Text("ACTIVE")
                                .font(.caption2)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(.blue.opacity(0.15))
                                .clipShape(RoundedRectangle(cornerRadius: 4))
                                .accessibilityIdentifier("active_tag")
                        }
                    }
                    .accessibilityIdentifier("provider_row_\(r.rawValue)")
                }
            }

            if let msg = vm.errorMessage {
                Text(msg)
                    .foregroundStyle(.orange)
                    .font(.caption)
                    .accessibilityIdentifier("error_message")
            }
        }
        .padding(12)
        .frame(minWidth: 300, maxWidth: 400)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 10))
        .shadow(radius: 10)
        .overlay(alignment: .topTrailing) {
            Button {
                withAnimation { isVisible.toggle() }
            } label: {
                Image(systemName: isVisible ? "eye.slash" : "eye")
                    .foregroundStyle(.secondary)
            }
            .buttonStyle(.plain)
            .padding(6)
            .accessibilityIdentifier("toggle_visibility_button")
        }
        .opacity(isVisible ? 1 : 0.35)
        .onAppear {
            Task { await vm.refreshHealth() }
        }
        .accessibilityIdentifier("provider_inspector")
    }

    private func label(_ r: ProviderRoute) -> String {
        switch r {
        case .auto: return "Auto"
        case .fastvlm: return "FastVLM"
        case .ollama: return "Ollama"
        case .trm: return "TRM"
        }
    }

    private func latencyText(_ ms: Int?) -> String {
        ms.map { "\($0) ms" } ?? "—"
    }

    private func latencyColor(_ ms: Int?) -> Color {
        guard let ms = ms else { return .secondary }
        // ≤150ms 🟢, 150–600ms 🟡, >600ms 🟠
        if ms <= 150 { return .green }
        if ms <= 600 { return .orange }
        return .red
    }
}
