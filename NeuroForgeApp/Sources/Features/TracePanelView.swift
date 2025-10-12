import SwiftUI

struct TraceSummary: Identifiable, Decodable {
    let id: String           // trace_id
    let capability: String
    let duration_ms: Int
    let started_at: Double
    let provider: String?
    let score: Double?
}

struct TraceDetail: Decodable {
    let output: [String: AnyDecodable]
    let trace: [String: AnyDecodable]
}

struct TracePanelView: View {
    @State private var capability = "summarize"
    @State private var traces: [TraceSummary] = []
    @State private var selected: TraceSummary?
    @State private var detailJSON = ""
    @State private var p50: Double = 0
    @State private var p95: Double = 0
    @State private var winrates: [String: Double] = [:]
    @State private var shadowDeltaMean: Double = 0

    private let apiBase = URL(string: ProcessInfo.processInfo.environment["API_BASE"] ?? "http://localhost:8014")!
    private let dashBase = URL(string: "http://localhost:8787")!

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Trace Panel").font(.largeTitle).bold()
                Spacer()
                Picker("Capability", selection: $capability) {
                    Text("summarize").tag("summarize")
                    Text("plan").tag("plan")
                    Text("generate").tag("generate")
                }
                .pickerStyle(.segmented)
                .accessibilityIdentifier("TP_CapabilityPicker")

                Button("Refresh") { Task { await refreshAll() } }
                    .keyboardShortcut("r")
                    .accessibilityIdentifier("TP_Refresh")
            }

            // Top metrics
            HStack {
                metric("p50", value: String(format: "%.0f ms", p50))
                metric("p95", value: String(format: "%.0f ms", p95))
                metric("Shadow Δ mean", value: String(format: "%.2f", shadowDeltaMean))
                Spacer()
            }

            HStack(spacing: 16) {
                // Left: trace list
                VStack(alignment: .leading) {
                    Text("Recent Traces").font(.headline)
                    List(traces, selection: $selected) { t in
                        Button {
                            selected = t
                            Task { await loadDetail(t.id) }
                        } label: {
                            HStack {
                                Text(t.capability.uppercased())
                                    .font(.caption2)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 3)
                                    .background(Color.secondary.opacity(0.15))
                                    .cornerRadius(4)

                                Text(t.provider ?? "—").foregroundColor(.secondary)
                                Spacer()
                                Text("\(t.duration_ms) ms").monospaced()
                                if let s = t.score {
                                    Text(String(format: "· %.2f", s)).monospaced()
                                }
                            }
                        }
                        .buttonStyle(.plain)
                    }
                    .accessibilityIdentifier("TP_TraceList")
                }
                .frame(minWidth: 300)

                // Right: detail
                VStack(alignment: .leading) {
                    Text("Trace Detail").font(.headline)
                    ScrollView {
                        Text(detailJSON)
                            .font(.system(.body, design: .monospaced))
                            .textSelection(.enabled)
                            .accessibilityIdentifier("TP_TraceDetail")
                    }
                }
            }
        }
        .padding(16)
        .frame(minWidth: 800, minHeight: 600)
        .onAppear { Task { await refreshAll() } }
        .onChange(of: capability) { _ in Task { await refreshAll() } }
        .accessibilityIdentifier("TP_Root")
    }

    @ViewBuilder private func metric(_ title: String, value: String) -> some View {
        VStack(alignment: .leading) {
            Text(title).font(.caption).foregroundColor(.secondary)
            Text(value).font(.headline).accessibilityIdentifier("TP_\(title.replacingOccurrences(of: " ", with: ""))")
        }
        .padding(8)
        .background(Color.secondary.opacity(0.08))
        .cornerRadius(6)
    }

    // MARK: - Networking
    private func refreshAll() async {
        await withTaskGroup(of: Void.self) { g in
            g.addTask { await loadLatency() }
            g.addTask { await loadWinrates() }
            g.addTask { await loadShadowDelta() }
            g.addTask { await loadTraces() }
        }
    }

    private func loadLatency() async {
        guard let url = URL(string: "\(dashBase)/metrics/latency?capability=\(capability)") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            if let obj = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                await MainActor.run {
                    p50 = (obj["p50"] as? Double) ?? 0
                    p95 = (obj["p95"] as? Double) ?? 0
                }
            }
        } catch {
            print("Failed to load latency: \(error)")
        }
    }

    private func loadWinrates() async {
        guard let url = URL(string: "\(dashBase)/metrics/winrates?capability=\(capability)") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            if let obj = try JSONSerialization.jsonObject(with: data) as? [String: Any],
               let providers = obj["providers"] as? [String: Any] {
                var wr: [String: Double] = [:]
                for (k, v) in providers {
                    if let d = v as? [String: Any], let rate = d["win_rate"] as? Double {
                        wr[k] = rate
                    }
                }
                await MainActor.run { winrates = wr }
            }
        } catch {
            print("Failed to load winrates: \(error)")
        }
    }

    private func loadShadowDelta() async {
        guard let url = URL(string: "\(dashBase)/metrics/shadow-delta?capability=\(capability)") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            if let obj = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                await MainActor.run {
                    shadowDeltaMean = (obj["mean_delta"] as? Double) ?? 0
                }
            }
        } catch {
            print("Failed to load shadow delta: \(error)")
        }
    }

    private func loadTraces() async {
        // For now, mock data if endpoint not available
        // Replace with actual /traces endpoint when ready
        await MainActor.run {
            traces = []  // Empty until /traces endpoint is implemented
        }
    }

    private func loadDetail(_ traceID: String) async {
        await MainActor.run {
            detailJSON = "Trace details: \(traceID)\n(Endpoint /trace/{id} not yet implemented)"
        }
    }
}

// Minimal AnyDecodable for generic JSON
struct AnyDecodable: Decodable {
    init(from decoder: Decoder) throws {
        // Placeholder - accepts any JSON
    }
}
