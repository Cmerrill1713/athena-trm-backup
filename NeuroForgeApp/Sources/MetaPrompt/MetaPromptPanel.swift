import SwiftUI

/// Visual dashboard showing Athena's meta-prompt orchestration data
/// Displays: confidence, style, flags (RAG/reflection), plan, tools, metrics
struct MetaPromptPanel: View {
    let meta: MetaPromptInfo
    
    @State private var planExpanded: Bool = false
    @State private var showCopyConfirmation: Bool = false
    
    var body: some View {
        if !meta.enabled {
            EmptyView()
        } else {
            content
        }
    }
    
    private var content: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header with confidence
            HStack(spacing: 8) {
                Label {
                    Text("Meta-Prompt Insight")
                        .font(.headline)
                } icon: {
                    Image(systemName: "brain.head.profile")
                        .foregroundColor(.purple)
                }
                
                Spacer()
                
                if let conf = meta.confidence {
                    ConfidencePill(confidence: conf)
                }
            }
            
            // Flags row (style, RAG, reflection, metrics)
            flagsRow
            
            // Tools chips
            if let tools = meta.tools, !tools.isEmpty {
                toolsRow(tools)
            }
            
            // Orchestrator plan (expandable)
            if let plan = meta.plan, !plan.isEmpty {
                planSection(plan)
            }
        }
        .padding(14)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .strokeBorder(Color.purple.opacity(0.15), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.05), radius: 8, x: 0, y: 2)
        .animation(.easeInOut(duration: 0.2), value: planExpanded)
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Meta Prompt Insight")
    }
    
    private var flagsRow: some View {
        HStack(spacing: 8) {
            if let style = meta.style {
                Badge(label: style.capitalized, systemName: "wand.and.stars", color: .blue)
            }
            
            if meta.rag == true {
                Badge(label: "RAG", systemName: "book.pages", color: .green)
            }
            
            if meta.reflection == true {
                Badge(label: "Reflection", systemName: "arrow.triangle.2.circlepath", color: .orange)
            }
            
            if let ms = meta.latencyMs {
                Badge(label: "\(ms)ms", systemName: "clock", color: .gray)
            }
            
            if let total = meta.totalTokens {
                Badge(label: "\(total) tok", systemName: "number", color: .gray)
            }
        }
    }
    
    private func toolsRow(_ tools: [String]) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Suggested Tools")
                .font(.caption)
                .foregroundColor(.secondary)
            
            FlowLayout(spacing: 6) {
                ForEach(tools, id: \.self) { tool in
                    Badge(label: tool, systemName: "hammer.fill", color: .purple)
                }
            }
        }
    }
    
    private func planSection(_ plan: [String]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Button(action: { planExpanded.toggle() }) {
                HStack {
                    Label("Orchestrator Plan", systemImage: "list.bullet.rectangle")
                        .font(.subheadline.bold())
                        .foregroundColor(.primary)
                    
                    Spacer()
                    
                    Image(systemName: planExpanded ? "chevron.up" : "chevron.down")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .buttonStyle(PlainButtonStyle())
            
            if planExpanded {
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(plan.indices, id: \.self) { i in
                        HStack(alignment: .top, spacing: 8) {
                            Text("\(i + 1).")
                                .font(.caption)
                                .bold()
                                .foregroundColor(.secondary)
                                .frame(width: 20, alignment: .trailing)
                            
                            Text(plan[i])
                                .font(.subheadline)
                                .foregroundColor(.primary)
                            
                            Spacer()
                        }
                    }
                    
                    // Copy plan button
                    Button(action: copyPlan) {
                        Label(showCopyConfirmation ? "Copied!" : "Copy Plan", 
                              systemImage: showCopyConfirmation ? "checkmark" : "doc.on.doc")
                            .font(.caption)
                            .foregroundColor(.blue)
                    }
                    .buttonStyle(PlainButtonStyle())
                    .padding(.top, 4)
                }
                .padding(.leading, 8)
                .transition(.opacity.combined(with: .scale(scale: 0.95, anchor: .top)))
            }
        }
        .padding(10)
        .background(Color.secondary.opacity(0.05), in: RoundedRectangle(cornerRadius: 8))
    }
    
    private func copyPlan() {
        guard let plan = meta.plan else { return }
        let text = plan.enumerated().map { "\($0.offset + 1). \($0.element)" }.joined(separator: "\n")
        
        #if os(macOS)
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(text, forType: .string)
        #else
        UIPasteboard.general.string = text
        #endif
        
        showCopyConfirmation = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            showCopyConfirmation = false
        }
    }
}

// MARK: - Confidence Pill

private struct ConfidencePill: View {
    let confidence: Double
    
    private var label: String {
        switch confidence {
        case ..<0.34: return "Low"
        case ..<0.67: return "Med"
        default: return "High"
        }
    }
    
    private var color: Color {
        switch confidence {
        case ..<0.34: return .red
        case ..<0.67: return .orange
        default: return .green
        }
    }
    
    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)
            
            Text("\(label) • \(Int((confidence * 100).rounded()))%")
                .font(.caption)
                .monospacedDigit()
                .foregroundColor(color)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(color.opacity(0.12), in: Capsule())
        .overlay(Capsule().strokeBorder(color.opacity(0.3), lineWidth: 1))
    }
}

// MARK: - Badge

private struct Badge: View {
    let label: String
    let systemName: String
    var color: Color = .secondary
    
    var body: some View {
        Label {
            Text(label)
                .font(.caption)
                .foregroundColor(color)
        } icon: {
            Image(systemName: systemName)
                .font(.caption2)
                .foregroundColor(color)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(color.opacity(0.12), in: Capsule())
        .overlay(Capsule().strokeBorder(color.opacity(0.25), lineWidth: 1))
    }
}

// MARK: - Flow Layout (for tool chips)

private struct FlowLayout: Layout {
    var spacing: CGFloat = 8
    
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = FlowResult(in: proposal.replacingUnspecifiedDimensions().width, subviews: subviews, spacing: spacing)
        return result.size
    }
    
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = FlowResult(in: bounds.width, subviews: subviews, spacing: spacing)
        for (index, subview) in subviews.enumerated() {
            subview.place(at: CGPoint(x: bounds.minX + result.frames[index].minX,
                                     y: bounds.minY + result.frames[index].minY),
                         proposal: .unspecified)
        }
    }
    
    struct FlowResult {
        var frames: [CGRect] = []
        var size: CGSize = .zero
        
        init(in maxWidth: CGFloat, subviews: Subviews, spacing: CGFloat) {
            var x: CGFloat = 0
            var y: CGFloat = 0
            var lineHeight: CGFloat = 0
            
            for subview in subviews {
                let size = subview.sizeThatFits(.unspecified)
                
                if x + size.width > maxWidth && x > 0 {
                    x = 0
                    y += lineHeight + spacing
                    lineHeight = 0
                }
                
                frames.append(CGRect(x: x, y: y, width: size.width, height: size.height))
                
                lineHeight = max(lineHeight, size.height)
                x += size.width + spacing
            }
            
            self.size = CGSize(width: maxWidth, height: y + lineHeight)
        }
    }
}

// MARK: - Previews

#if DEBUG
struct MetaPromptPanel_Previews: PreviewProvider {
    static var previews: some View {
        VStack(spacing: 20) {
            // High confidence with full data
            MetaPromptPanel(meta: MetaPromptInfo(
                enabled: true,
                confidence: 0.92,
                style: "reasoned",
                rag: true,
                reflection: true,
                plan: [
                    "Clarify user intent",
                    "Select appropriate tools",
                    "Execute validation tests",
                    "Summarize results"
                ],
                tools: ["pytest", "truth", "watchdog"],
                latencyMs: 842,
                promptTokens: 216,
                completionTokens: 458
            ))
            
            // Low confidence
            MetaPromptPanel(meta: MetaPromptInfo(
                enabled: true,
                confidence: 0.28,
                style: "uncertain",
                rag: false,
                reflection: true,
                plan: ["Request clarification"],
                tools: nil,
                latencyMs: 312,
                promptTokens: 89,
                completionTokens: 124
            ))
            
            // Minimal data
            MetaPromptPanel(meta: MetaPromptInfo(
                enabled: true,
                confidence: 0.65,
                style: "terse",
                rag: nil,
                reflection: nil,
                plan: nil,
                tools: ["grep", "read_file"],
                latencyMs: nil,
                promptTokens: nil,
                completionTokens: nil
            ))
        }
        .padding()
        .background(Color(.systemBackground))
    }
}
#endif

