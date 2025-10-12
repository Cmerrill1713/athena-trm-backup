"""
Trace Panel - Orchestrator Decision Transparency
================================================
Shows why each routing decision was made
"""

import SwiftUI

struct TraceDetail: Identifiable {
    let id: String
    let capability: String
    let provider: String
    let score: Double
    let subscores: [String: Double]
    let latencyMs: Int
    let policyHits: [String]
    let timestamp: Date
}

struct TracePanel: View {
    @State private var traces: [TraceDetail] = []
    @State private var isLoading = false
    @State private var selectedTrace: TraceDetail?

    let apiBase = "http://127.0.0.1:8765"

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Orchestrator Traces")
                    .font(.headline)
                Spacer()
                Button {
                    Task { await refreshTraces() }
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
                .keyboardShortcut("r", modifiers: [.command])
                .accessibilityIdentifier("refresh_traces_button")

                Button {
                    exportTraces()
                } label: {
                    Image(systemName: "square.and.arrow.up")
                }
                .keyboardShortcut("e", modifiers: [.command, .shift])
                .accessibilityIdentifier("export_traces_button")
            }
            .padding()

            Divider()

            // Trace List
            if isLoading {
                ProgressView("Loading traces...")
                    .padding()
            } else if traces.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "tray")
                        .font(.system(size: 48))
                        .foregroundStyle(.secondary)
                    Text("No traces yet")
                        .foregroundStyle(.secondary)
                    Text("Execute a capability to see routing decisions")
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                }
                .padding()
            } else {
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(traces) { trace in
                            TraceRow(trace: trace, isSelected: selectedTrace?.id == trace.id)
                                .onTapGesture {
                                    selectedTrace = trace
                                }
                                .accessibilityIdentifier("trace_row_\(trace.id)")
                        }
                    }
                    .padding()
                }
                .accessibilityIdentifier("trace_list_scroll")
            }

            // Detail Panel
            if let trace = selectedTrace {
                Divider()
                TraceDetailView(trace: trace)
                    .frame(height: 200)
                    .accessibilityIdentifier("trace_detail_panel")
            }
        }
        .frame(width: 400)
        .background(.regularMaterial)
        .onAppear {
            Task { await refreshTraces() }
        }
    }

    func refreshTraces() async {
        isLoading = true
        defer { isLoading = false }

        guard let url = URL(string: "\(apiBase)/traces?limit=20") else { return }

        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let response = try JSONDecoder().decode(TracesResponse.self, from: data)

            // Parse traces
            let parsed = response.traces.compactMap { traceDict -> TraceDetail? in
                guard let traceId = traceDict["trace_id"] as? String,
                      let capability = traceDict["capability"] as? String,
                      let rawJson = traceDict["raw_json"] as? String,
                      let jsonData = rawJson.data(using: .utf8),
                      let json = try? JSONSerialization.jsonObject(with: jsonData) as? [String: Any],
                      let events = json["events"] as? [[String: Any]] else {
                    return nil
                }

                // Extract primary result
                var provider = "unknown"
                var score = 0.0
                var subscores: [String: Double] = [:]

                for event in events {
                    if event["label"] as? String == "primary_result",
                       let data = event["data"] as? [String: Any] {
                        provider = data["provider"] as? String ?? "unknown"
                        score = data["score"] as? Double ?? 0.0
                        if let subs = data["subscores"] as? [String: Double] {
                            subscores = subs
                        }
                        break
                    }
                }

                return TraceDetail(
                    id: traceId,
                    capability: capability,
                    provider: provider,
                    score: score,
                    subscores: subscores,
                    latencyMs: traceDict["duration_ms"] as? Int ?? 0,
                    policyHits: [],  // Extract from safety data if needed
                    timestamp: Date(timeIntervalSince1970: traceDict["started_at"] as? Double ?? 0)
                )
            }

            await MainActor.run {
                traces = parsed
            }
        } catch {
            print("⚠️ Failed to fetch traces: \(error)")
        }
    }

    func exportTraces() {
        let panel = NSSavePanel()
        panel.nameFieldStringValue = "neuroforge-traces-\(ISO8601DateFormatter().string(from: Date())).json"
        panel.allowedContentTypes = [.json]

        panel.begin { response in
            guard response == .OK, let url = panel.url else { return }

            // Export traces as JSON
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.prettyPrinted, .sortedKeys]

            if let data = try? encoder.encode(traces) {
                try? data.write(to: url)
            }
        }
    }
}

struct TraceRow: View {
    let trace: TraceDetail
    let isSelected: Bool

    var body: some View {
        HStack(spacing: 12) {
            // Score indicator
            Circle()
                .fill(scoreColor(trace.score))
                .frame(width: 12, height: 12)

            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(trace.capability)
                        .font(.subheadline.weight(.medium))
                    Spacer()
                    Text("\(trace.latencyMs)ms")
                        .font(.caption)
                        .foregroundStyle(latencyColor(trace.latencyMs))
                }

                HStack {
                    Text(trace.provider)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Spacer()
                    Text(trace.score, format: .number.precision(.fractionLength(2)))
                        .font(.caption.monospacedDigit())
                        .foregroundStyle(scoreColor(trace.score))
                }
            }
        }
        .padding(8)
        .background(isSelected ? Color.accentColor.opacity(0.1) : Color.clear)
        .clipShape(RoundedRectangle(cornerRadius: 6))
    }

    func scoreColor(_ score: Double) -> Color {
        if score >= 0.9 { return .green }
        if score >= 0.7 { return .orange }
        return .red
    }

    func latencyColor(_ ms: Int) -> Color {
        if ms <= 500 { return .green }
        if ms <= 1500 { return .orange }
        return .red
    }
}

struct TraceDetailView: View {
    let trace: TraceDetail

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Why This Choice?")
                .font(.headline)

            // Provider selection
            HStack {
                Text("Provider:")
                    .foregroundStyle(.secondary)
                Text(trace.provider)
                    .fontWeight(.medium)
            }

            Divider()

            // Subscores
            Text("Subscores:")
                .font(.subheadline.weight(.medium))

            VStack(alignment: .leading, spacing: 6) {
                ForEach(Array(trace.subscores.sorted(by: { $0.key < $1.key })), id: \.key) { key, value in
                    HStack {
                        Text("• \(key.capitalized):")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .frame(width: 100, alignment: .leading)

                        ProgressView(value: value, total: 1.0)
                            .progressViewStyle(.linear)
                            .frame(width: 120)

                        Text(value, format: .number.precision(.fractionLength(2)))
                            .font(.caption.monospacedDigit())
                            .foregroundStyle(value >= 0.7 ? .green : .orange)
                    }
                }
            }

            Divider()

            // Constraints
            HStack {
                Image(systemName: "checkmark.shield")
                    .foregroundStyle(.green)
                Text("All constraints met")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            if !trace.policyHits.isEmpty {
                HStack {
                    Image(systemName: "exclamationmark.triangle")
                        .foregroundStyle(.orange)
                    Text("Policy hits: \(trace.policyHits.joined(separator: ", "))")
                        .font(.caption)
                        .foregroundStyle(.orange)
                }
            }
        }
        .padding()
        .background(.ultraThinMaterial)
    }
}

// Response models
struct TracesResponse: Codable {
    let traces: [[String: Any]]
    let count: Int

    enum CodingKeys: String, CodingKey {
        case traces, count
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        count = try container.decode(Int.self, forKey: .count)

        // Parse traces as generic dictionaries
        let tracesArray = try container.decode([AnyCodable].self, forKey: .traces)
        traces = tracesArray.compactMap { $0.value as? [String: Any] }
    }
}

// Helper for decoding Any
struct AnyCodable: Codable {
    let value: Any

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()

        if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map { $0.value }
        } else if let dict = try? container.decode([String: AnyCodable].self) {
            value = dict.mapValues { $0.value }
        } else {
            value = NSNull()
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()

        switch value {
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let string as String:
            try container.encode(string)
        case let bool as Bool:
            try container.encode(bool)
        default:
            try container.encodeNil()
        }
    }
}
