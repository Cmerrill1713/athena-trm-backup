import SwiftUI

// MARK: - Meta-Prompt Response Model

struct MetaPromptResponse: Codable {
    let confidence: Double
    let plan: [String]
    let tools: [String]
    let style: String
    let flags: Flags
    
    struct Flags: Codable {
        let rag: Bool
        let reflection: Bool
        let selfCritique: Bool?
        let chaining: Bool?
    }
}

// MARK: - Confidence Sparkline

struct ConfidenceSparkline: View {
    let history: [Double]  // Last 5-10 confidence scores
    
    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width
            let h = geo.size.height
            let step = w / CGFloat(max(history.count - 1, 1))
            
            Path { path in
                guard !history.isEmpty else { return }
                path.move(to: CGPoint(x: 0, y: h * (1 - CGFloat(history[0]))))
                for (i, conf) in history.enumerated().dropFirst() {
                    path.addLine(to: CGPoint(x: step * CGFloat(i), y: h * (1 - CGFloat(conf))))
                }
            }
            .stroke(confidenceColor(history.last ?? 0), lineWidth: 2)
            
            // Dots
            ForEach(Array(history.enumerated()), id: \.offset) { i, conf in
                Circle()
                    .fill(confidenceColor(conf))
                    .frame(width: 4, height: 4)
                    .position(x: step * CGFloat(i), y: h * (1 - CGFloat(conf)))
            }
        }
        .frame(height: 24)
    }
    
    private func confidenceColor(_ conf: Double) -> Color {
        switch conf {
        case 0.8...1.0: return .green
        case 0.6..<0.8: return .yellow
        default: return .red
        }
    }
}

// MARK: - Meta Prompt Panel

struct MetaPromptPanel: View {
    let meta: MetaPromptResponse
    @State private var isExpanded = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Confidence header (always visible)
            HStack(spacing: 8) {
                confidenceBadge
                
                Text(meta.style.capitalized)
                    .font(.caption.weight(.medium))
                    .foregroundStyle(.secondary)
                
                if meta.flags.rag {
                    Image(systemName: "doc.text.magnifyingglass")
                        .font(.caption)
                        .foregroundStyle(.blue)
                        .help("RAG enabled")
                }
                
                if meta.flags.reflection {
                    Image(systemName: "arrow.triangle.2.circlepath")
                        .font(.caption)
                        .foregroundStyle(.purple)
                        .help("Reflection enabled")
                }
                
                if meta.flags.selfCritique == true {
                    Image(systemName: "checkmark.shield")
                        .font(.caption)
                        .foregroundStyle(.orange)
                        .help("Self-critique enabled")
                }
                
                Spacer()
                
                Button {
                    withAnimation(.spring(response: 0.3)) {
                        isExpanded.toggle()
                    }
                } label: {
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            
            // Expanded details
            if isExpanded {
                VStack(alignment: .leading, spacing: 6) {
                    if !meta.plan.isEmpty {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Plan")
                                .font(.caption2.weight(.semibold))
                                .foregroundStyle(.secondary)
                            ForEach(Array(meta.plan.enumerated()), id: \.offset) { i, step in
                                HStack(spacing: 6) {
                                    Text("\(i + 1).")
                                        .font(.caption2.monospacedDigit())
                                        .foregroundStyle(.tertiary)
                                    Text(step)
                                        .font(.caption2)
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                    
                    if !meta.tools.isEmpty {
                        HStack(spacing: 6) {
                            Text("Tools:")
                                .font(.caption2.weight(.semibold))
                                .foregroundStyle(.secondary)
                            ForEach(meta.tools, id: \.self) { tool in
                                Text(tool)
                                    .font(.caption2.monospacedDigit())
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Capsule().fill(.blue.opacity(0.15)))
                                    .foregroundStyle(.blue)
                            }
                        }
                    }
                }
                .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
        .padding(10)
        .background(
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .fill(.ultraThinMaterial)
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .strokeBorder(confidenceColor.opacity(0.3), lineWidth: 1)
                )
        )
        .shadow(color: .black.opacity(0.05), radius: 4, x: 0, y: 2)
    }
    
    private var confidenceBadge: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(confidenceColor)
                .frame(width: 6, height: 6)
            Text("\(Int(meta.confidence * 100))%")
                .font(.caption.monospacedDigit().weight(.semibold))
                .foregroundStyle(confidenceColor)
        }
    }
    
    private var confidenceColor: Color {
        switch meta.confidence {
        case 0.8...1.0: return .green
        case 0.6..<0.8: return .yellow
        default: return .red
        }
    }
}

// MARK: - Preview

#Preview {
    VStack(spacing: 16) {
        ConfidenceSparkline(history: [0.9, 0.85, 0.7, 0.92, 0.88])
            .padding()
        
        MetaPromptPanel(meta: MetaPromptResponse(
            confidence: 0.92,
            plan: [
                "Check backend logs for errors",
                "Compare error rates over last 24h",
                "Generate incident summary"
            ],
            tools: ["curl", "jq", "grep"],
            style: "reasoned",
            flags: MetaPromptResponse.Flags(
                rag: true,
                reflection: true,
                selfCritique: true,
                chaining: false
            )
        ))
        .padding()
    }
}

