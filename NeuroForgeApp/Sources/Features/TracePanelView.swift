import SwiftUI
#if os(macOS)
import AppKit
#endif

// MARK: - WHY THIS CHOICE: models & parsing

struct ChoiceExplain {
    let provider: String
    let subscores: [String: Double]   // correctness/structure/safety/latency/acceptance
    let composite: Double
    let policyHits: [String]
}

struct TracePanelView: View {
    @State private var capability = "summarize"
    @State private var traces: [TraceSummary] = []
    @State private var selected: TraceSummary?
    @State private var detailJSON = ""
    @State private var whyExplain: ChoiceExplain? = nil
    @State private var selectedTraceRawJSON: Any? = nil
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

                Button("Export JSON") { exportTraceJSON() }
                    .disabled(detailJSON.isEmpty)
                    .accessibilityIdentifier("TP_ExportJSON")

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
                VStack(alignment: .leading, spacing: 12) {
                    Text("Trace Detail").font(.headline)

                    // Why this choice panel
                    if let explain = whyExplain {
                        WhyThisChoiceView(explain: explain)
                    }

                    // Raw JSON
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
        .onChange(of: capability) { oldValue, newValue in
            Task { await refreshAll() }
        }
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
        guard let url = URL(string: "\(apiBase)/trace/\(traceID)") else {
            await MainActor.run {
                detailJSON = "Invalid URL for trace: \(traceID)"
                selectedTraceRawJSON = nil
                whyExplain = nil
            }
            return
        }

        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let obj = try JSONSerialization.jsonObject(with: data, options: [.fragmentsAllowed])
            let pretty = try JSONSerialization.data(withJSONObject: obj, options: [.prettyPrinted])

            await MainActor.run {
                self.detailJSON = String(data: pretty, encoding: .utf8) ?? ""
                self.selectedTraceRawJSON = obj
                self.whyExplain = extractChoiceExplain(from: obj)
            }
        } catch {
            await MainActor.run {
                self.detailJSON = "Failed to load trace: \(error.localizedDescription)\n\nTrace ID: \(traceID)\n(Endpoint /trace/{id} may not be implemented yet)"
                self.selectedTraceRawJSON = nil
                self.whyExplain = nil
            }
        }
    }

    private func extractChoiceExplain(from traceJSON: Any) -> ChoiceExplain? {
        guard let dict = traceJSON as? [String: Any],
              let events = dict["events"] as? [[String: Any]] else { return nil }

        // Find primary result (provider, score, subscores)
        let primary = events.last { ($0["label"] as? String) == "primary_result" }
        let pdata = primary?["data"] as? [String: Any]
        let provider = (pdata?["provider"] as? String) ?? "unknown"
        let composite = (pdata?["score"] as? Double) ?? 0.0
        let subs = (pdata?["subs"] as? [String: Any]) ?? [:]

        // Subscores normalized to double
        var subscores: [String: Double] = [:]
        for k in ["correctness", "structure", "safety", "latency", "acceptance"] {
            if let v = subs[k] as? Double {
                subscores[k] = v
            } else if let v = subs[k] as? NSNumber {
                subscores[k] = v.doubleValue
            }
        }

        // Pick up policy hits (if you logged them in any event, e.g. "constraints" or "policy_hit")
        var hits: [String] = []
        for ev in events {
            if let label = ev["label"] as? String,
               ["constraints_applied", "policy_hit"].contains(label),
               let d = ev["data"] as? [String: Any] {
                if let arr = d["policy_hits"] as? [String] {
                    hits.append(contentsOf: arr)
                }
                if let msg = d["message"] as? String {
                    hits.append(msg)
                }
            }
        }
        // De-dupe
        let policyHits = Array(Set(hits)).sorted()

        return ChoiceExplain(provider: provider, subscores: subscores, composite: composite, policyHits: policyHits)
    }

    #if os(macOS)
    private func exportTraceJSON() {
        guard let text = self.detailJSON.data(using: .utf8) else { return }
        let panel = NSSavePanel()
        panel.title = "Export Trace JSON"
        panel.nameFieldStringValue = "trace_\(selected?.id ?? "unknown").json"
        panel.allowedContentTypes = [.json]
        panel.directoryURL = FileManager.default.urls(for: .desktopDirectory, in: .userDomainMask).first

        if panel.runModal() == .OK, let url = panel.url {
            do {
                try text.write(to: url)
                print("✅ Exported trace to: \(url.path)")
            } catch {
                print("❌ Export failed: \(error)")
            }
        }
    }
    #else
    private func exportTraceJSON() {
        // iOS/other platforms - could use share sheet
        print("Export not implemented for this platform")
    }
    #endif
}

// Minimal AnyDecodable for generic JSON
struct AnyDecodable: Decodable {
    init(from decoder: Decoder) throws {
        // Placeholder - accepts any JSON
    }
}

// MARK: - WHY THIS CHOICE: view

struct WhyThisChoiceView: View {
    let explain: ChoiceExplain

    private func meter(_ v: Double) -> some View {
        GeometryReader { geo in
            ZStack(alignment: .leading) {
                RoundedRectangle(cornerRadius: 3)
                    .fill(Color.secondary.opacity(0.15))
                RoundedRectangle(cornerRadius: 3)
                    .fill(Color.accentColor)
                    .frame(width: max(0, min(1.0, v)) * geo.size.width)
            }
        }
        .frame(height: 6)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Why this choice?")
                    .font(.headline)
                Spacer()
                Text(explain.provider)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.secondary.opacity(0.12))
                    .cornerRadius(6)
            }

            // composite
            HStack(spacing: 8) {
                Text(String(format: "Composite: %.2f", explain.composite))
                    .font(.subheadline)
                    .bold()
                meter(explain.composite)
            }

            // subscores
            VStack(alignment: .leading, spacing: 6) {
                ForEach(["correctness", "structure", "safety", "latency", "acceptance"], id: \.self) { key in
                    HStack {
                        Text(key.capitalized)
                            .frame(width: 100, alignment: .leading)
                            .foregroundColor(.secondary)
                        meter(explain.subscores[key] ?? 0.0)
                        Text(String(format: "%.2f", explain.subscores[key] ?? 0.0))
                            .monospacedDigit()
                            .frame(width: 48, alignment: .trailing)
                    }
                    .font(.caption)
                }
            }

            if !explain.policyHits.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Policy/Constraint hits")
                        .font(.subheadline)
                    ForEach(explain.policyHits, id: \.self) { s in
                        HStack(spacing: 6) {
                            Circle()
                                .fill(Color.secondary.opacity(0.4))
                                .frame(width: 6, height: 6)
                            Text(s).font(.caption)
                        }
                    }
                }
                .padding(.top, 6)
            }
        }
        .accessibilityIdentifier("TP_WhyThisChoice")
        .padding(10)
        .background(Color.secondary.opacity(0.06))
        .cornerRadius(8)
    }
}
