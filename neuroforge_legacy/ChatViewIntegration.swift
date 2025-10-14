#if false
// ✅ EXAMPLE CODE ONLY - Not compiled to avoid type conflicts
// Copy patterns below into your actual ChatView

import SwiftUI

// MARK: - ChatView Integration Example
// Shows how to render MetaPromptPanel in your chat view

/*

Example integration in your existing ChatView:

```swift
import SwiftUI

struct ChatView: View {
    @State private var messages: [ChatMessage] = []
    @State private var input: String = ""
    @State private var confidenceHistory: [Double] = []

    @AppStorage("showMetaPanels") private var showMetaPanels = true

    var body: some View {
        VStack(spacing: 0) {
            // Optional: Confidence sparkline at top
            if !confidenceHistory.isEmpty && showMetaPanels {
                ConfidenceSparkline(history: confidenceHistory)
                    .frame(height: 24)
                    .padding()
                    .background(.ultraThinMaterial)
            }

            // Messages
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 12) {
                    ForEach(messages) { msg in
                        // Your existing chat bubble
                        ChatBubble(message: msg)

                        // ✅ Meta-prompt panel (only for assistant messages)
                        if showMetaPanels,
                           msg.role == .assistant,
                           let meta = msg.meta,
                           meta.enabled {
                            MetaPromptPanel(meta: meta)
                                .padding(.horizontal)
                                .padding(.bottom, 8)
                                .transition(.opacity.combined(with: .scale))
                        }
                    }
                }
                .padding(.top, 12)
            }

            // Input bar
            InputBar(text: $input, onSend: sendMessage)
        }
    }

    private func sendMessage() {
        guard !input.isEmpty else { return }

        // Add user message
        let userMsg = ChatMessage(role: .user, content: input)
        messages.append(userMsg)

        let text = input
        input = ""

        // Send to backend and get response with meta
        Task {
            do {
                let (response, meta) = try await apiClient.sendChat(text: text)

                let assistantMsg = ChatMessage(
                    role: .assistant,
                    content: response,
                    meta: meta  // ✅ Meta attached here
                )

                await MainActor.run {
                    messages.append(assistantMsg)

                    // Update confidence history for sparkline
                    if let conf = meta?.confidence {
                        confidenceHistory.append(conf)
                        if confidenceHistory.count > 10 {
                            confidenceHistory.removeFirst()
                        }
                    }
                }
            } catch {
                print("Error: \(error)")
            }
        }
    }
}
```

*/

// MARK: - Simple Chat Bubble Example

struct ChatBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack {
            if message.role == .user {
                Spacer(minLength: 60)
            }

            VStack(alignment: message.role == .user ? .trailing : .leading, spacing: 4) {
                Text(message.content)
                    .padding(12)
                    .background(
                        message.role == .user ? Color.blue : Color(.systemGray5),
                        in: RoundedRectangle(cornerRadius: 16, style: .continuous)
                    )
                    .foregroundColor(message.role == .user ? .white : .primary)

                Text(message.timestamp, style: .time)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }

            if message.role == .assistant {
                Spacer(minLength: 60)
            }
        }
        .padding(.horizontal)
    }
}

// MARK: - Input Bar Example

struct InputBar: View {
    @Binding var text: String
    let onSend: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            TextField("Message", text: $text)
                .textFieldStyle(.roundedBorder)
                .onSubmit(onSend)

            Button(action: onSend) {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.title2)
            }
            .disabled(text.isEmpty)
        }
        .padding()
        .background(.ultraThinMaterial)
    }
}

// MARK: - Confidence Sparkline (Simple Version)

/// Shows confidence trend over last N messages
struct ConfidenceSparkline: View {
    let history: [Double]

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "chart.line.uptrend.xyaxis")
                .font(.caption)
                .foregroundStyle(.secondary)

            GeometryReader { geo in
                let step = geo.size.width / CGFloat(max(history.count - 1, 1))
                let height = geo.size.height

                // Line
                Path { path in
                    guard !history.isEmpty else { return }
                    path.move(to: CGPoint(
                        x: 0,
                        y: height * (1 - CGFloat(history[0]))
                    ))
                    for (i, conf) in history.enumerated().dropFirst() {
                        path.addLine(to: CGPoint(
                            x: step * CGFloat(i),
                            y: height * (1 - CGFloat(conf))
                        ))
                    }
                }
                .stroke(lineColor, lineWidth: 2)

                // Dots
                ForEach(Array(history.enumerated()), id: \.offset) { i, conf in
                    Circle()
                        .fill(color(for: conf))
                        .frame(width: 4, height: 4)
                        .position(
                            x: step * CGFloat(i),
                            y: height * (1 - CGFloat(conf))
                        )
                }
            }

            Text("\(history.count)")
                .font(.caption2.monospacedDigit())
                .foregroundStyle(.tertiary)
        }
    }

    private var lineColor: Color {
        guard let last = history.last else { return .gray }
        return color(for: last)
    }

    private func color(for confidence: Double) -> Color {
        switch confidence {
        case ..<0.34: return .red
        case ..<0.67: return .orange
        default: return .green
        }
    }
}

// MARK: - Settings Toggle Example

/*

Add to your settings view:

```swift
struct SettingsView: View {
    @AppStorage("showMetaPanels") private var showMetaPanels = true

    var body: some View {
        Form {
            Section("Meta-Prompt Dashboard") {
                Toggle("Show confidence panels", isOn: $showMetaPanels)

                Text("Displays AI reasoning, confidence, and tool selection for each response")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }
}
```

*/

// MARK: - Preview Provider

#if DEBUG
struct ChatViewIntegration_Previews: PreviewProvider {
    static var previews: some View {
        VStack(spacing: 16) {
            // Sample message with high confidence meta
            ChatBubble(message: ChatMessage(
                role: .assistant,
                content: "I'll run the smoke tests for you.",
                meta: MetaPromptInfo(
                    enabled: true,
                    confidence: 0.92,
                    style: "reasoned",
                    rag: true,
                    reflection: false,
                    plan: [
                        "Parse test markers",
                        "Execute pytest suite",
                        "Summarize results"
                    ],
                    tools: ["pytest", "grep"],
                    latencyMs: 756,
                    promptTokens: 142,
                    completionTokens: 298
                )
            ))

            MetaPromptPanel(meta: MetaPromptInfo(
                enabled: true,
                confidence: 0.92,
                style: "reasoned",
                rag: true,
                reflection: false,
                plan: [
                    "Parse test markers",
                    "Execute pytest suite",
                    "Summarize results"
                ],
                tools: ["pytest", "grep"],
                latencyMs: 756,
                promptTokens: 142,
                completionTokens: 298
            ))
            .padding()

            Divider()

            // Sample with low confidence
            ChatBubble(message: ChatMessage(
                role: .assistant,
                content: "Could you clarify what you'd like me to check?",
                meta: MetaPromptInfo(
                    enabled: true,
                    confidence: 0.23,
                    style: "uncertain",
                    rag: false,
                    reflection: true,
                    plan: ["Request clarification"],
                    tools: nil,
                    latencyMs: 234,
                    promptTokens: 78,
                    completionTokens: 45
                )
            ))

            MetaPromptPanel(meta: MetaPromptInfo(
                enabled: true,
                confidence: 0.23,
                style: "uncertain",
                rag: false,
                reflection: true,
                plan: ["Request clarification"],
                tools: nil,
                latencyMs: 234,
                promptTokens: 78,
                completionTokens: 45
            ))
            .padding()
        }
    }
}
#endif

#endif  // ✅ End example code
