import SwiftUI

// MARK: - Prompt Debug Data

struct PromptDebugData {
    let originalPrompt: String
    let rewrittenPrompt: String
    let confidenceDelta: Double
    let reflectionSteps: [String]
    let timestamp: Date
}

// MARK: - Prompt Debug Overlay

struct PromptDebugOverlay: View {
    @Binding var isShowing: Bool
    let history: [PromptDebugData]
    
    var body: some View {
        ZStack(alignment: .topTrailing) {
            // Backdrop
            Color.black.opacity(0.3)
                .ignoresSafeArea()
                .onTapGesture { isShowing = false }
            
            // Panel
            VStack(alignment: .leading, spacing: 0) {
                // Header
                HStack {
                    Image(systemName: "ladybug")
                        .font(.title3)
                    Text("Prompt Debug")
                        .font(.headline)
                    Spacer()
                    Button {
                        isShowing = false
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.title3)
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }
                .padding()
                .background(.ultraThinMaterial)
                
                Divider()
                
                // Content
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 16) {
                        ForEach(Array(history.enumerated()), id: \.offset) { i, debug in
                            debugEntry(debug, index: i)
                            if i < history.count - 1 {
                                Divider()
                            }
                        }
                    }
                    .padding()
                }
            }
            .frame(width: 500, height: 600)
            .background(.regularMaterial)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .shadow(color: .black.opacity(0.3), radius: 20, x: 0, y: 10)
            .padding(40)
        }
        .transition(.opacity.combined(with: .scale(scale: 0.95)))
    }
    
    private func debugEntry(_ debug: PromptDebugData, index: Int) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            // Timestamp
            Text(debug.timestamp, style: .time)
                .font(.caption.monospacedDigit())
                .foregroundStyle(.secondary)
            
            // Original
            VStack(alignment: .leading, spacing: 4) {
                Text("Original")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)
                Text(debug.originalPrompt)
                    .font(.caption.monospaced())
                    .padding(8)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(RoundedRectangle(cornerRadius: 6).fill(.red.opacity(0.1)))
            }
            
            // Arrow
            HStack {
                Spacer()
                Image(systemName: "arrow.down")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()
            }
            
            // Rewritten
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text("Rewritten")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                    Spacer()
                    Text("Δ\(String(format: "%+.0f%%", debug.confidenceDelta * 100))")
                        .font(.caption.monospacedDigit().weight(.medium))
                        .foregroundStyle(debug.confidenceDelta > 0 ? .green : .red)
                }
                Text(debug.rewrittenPrompt)
                    .font(.caption.monospaced())
                    .padding(8)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(RoundedRectangle(cornerRadius: 6).fill(.green.opacity(0.1)))
            }
            
            // Reflection steps
            if !debug.reflectionSteps.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Reflection")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                    ForEach(Array(debug.reflectionSteps.enumerated()), id: \.offset) { i, step in
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
                .padding(8)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(RoundedRectangle(cornerRadius: 6).fill(.purple.opacity(0.1)))
            }
        }
    }
}

// MARK: - Preview

#Preview {
    PromptDebugOverlay(
        isShowing: .constant(true),
        history: [
            PromptDebugData(
                originalPrompt: "check the logs",
                rewrittenPrompt: "Check backend logs for errors in the last 24h, compare error rates, and generate a summary of any incidents found.",
                confidenceDelta: 0.35,
                reflectionSteps: [
                    "Clarified timeframe (24h)",
                    "Added comparison requirement",
                    "Specified output format"
                ],
                timestamp: Date()
            ),
            PromptDebugData(
                originalPrompt: "what's wrong with the app",
                rewrittenPrompt: "Analyze frontend and backend health metrics, check for elevated error rates or latency, review recent deployments, and identify root cause of any performance degradation.",
                confidenceDelta: 0.42,
                reflectionSteps: [
                    "Expanded to frontend + backend",
                    "Added metric checks",
                    "Included deployment context"
                ],
                timestamp: Date().addingTimeInterval(-120)
            )
        ]
    )
}

