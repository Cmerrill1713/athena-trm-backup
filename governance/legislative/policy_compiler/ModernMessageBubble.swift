import SwiftUI

// MARK: - Modern Message Bubble with Glassmorphism

struct ModernMessageBubble: View {
    let message: ChatMessage
    let showMeta: Bool
    @State private var isHovered = false
    @State private var showingFullMeta = false

    var body: some View {
        VStack(alignment: message.role.isUser ? .trailing : .leading, spacing: DesignSystem.Spacing.sm) {
            // Main bubble
            HStack {
                if message.role.isUser { Spacer(minLength: 60) }

                VStack(alignment: .leading, spacing: DesignSystem.Spacing.xs) {
                    // Voice indicator
                    if message.role == .userVoice {
                        HStack(spacing: 4) {
                            Image(systemName: "waveform")
                                .font(.system(size: 10))
                            Text("Voice")
                                .font(DesignSystem.Typography.caption)
                        }
                        .foregroundStyle(DesignSystem.Colors.bridge)
                    }

                    // Message content
                    Text(message.content)
                        .font(DesignSystem.Typography.body)
                        .textSelection(.enabled)
                        .lineSpacing(4)
                }
                .padding(.horizontal, DesignSystem.Spacing.md)
                .padding(.vertical, DesignSystem.Spacing.md)
                .background(bubbleBackground)
                .clipShape(BubbleShape(isUser: message.role.isUser))
                .shadow(
                    color: .black.opacity(isHovered ? 0.15 : 0.08),
                    radius: isHovered ? 12 : 8,
                    x: 0,
                    y: isHovered ? 6 : 4
                )
                .scaleEffect(isHovered ? 1.02 : 1.0)
                .animation(DesignSystem.Animation.quick, value: isHovered)
                .onHover { hovering in
                    isHovered = hovering
                }

                if !message.role.isUser { Spacer(minLength: 60) }
            }

            // Meta panel (assistant only)
            if !message.role.isUser, let meta = message.meta, showMeta {
                ModernMetaPanel(meta: meta, showingFull: $showingFullMeta)
                    .transition(.asymmetric(
                        insertion: .move(edge: .top).combined(with: .opacity),
                        removal: .opacity
                    ))
            }
        }
        .animation(DesignSystem.Animation.springy, value: message.meta != nil)
    }

    private var bubbleBackground: some View {
        Group {
            if message.role.isUser {
                LinearGradient(
                    colors: [
                        Color.accentColor.opacity(0.15),
                        Color.accentColor.opacity(0.25)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            } else {
                LinearGradient(
                    colors: [
                        Color.secondary.opacity(0.06),
                        Color.secondary.opacity(0.12)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            }
        }
        .overlay(
            BubbleShape(isUser: message.role.isUser)
                .stroke(
                    LinearGradient(
                        colors: [
                            DesignSystem.Colors.glassBorder.opacity(0.3),
                            DesignSystem.Colors.glassBorder.opacity(0.1)
                        ],
                        startPoint: .top,
                        endPoint: .bottom
                    ),
                    lineWidth: 1
                )
        )
        .background(.ultraThinMaterial.opacity(0.3))
    }
}

// MARK: - Modern Meta Panel

struct ModernMetaPanel: View {
    let meta: MetaPromptInfo
    @Binding var showingFull: Bool

    private func sendFeedback(interactionId: String, thumbsUp: Bool) {
        guard let url = URL(string: "http://127.0.0.1:8014/api/feedback") else { return }

        let feedbackData: [String: Any] = [
            "interaction_id": interactionId,
            "thumbs_up": thumbsUp,
            "thumbs_down": !thumbsUp
        ]

        guard let jsonData = try? JSONSerialization.data(withJSONObject: feedbackData) else { return }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = jsonData

        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Feedback error: \(error)")
                return
            }

            if let httpResponse = response as? HTTPURLResponse,
               (200...299).contains(httpResponse.statusCode) {
                print("✅ Feedback sent successfully")
            } else {
                print("❌ Feedback failed")
            }
        }.resume()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: DesignSystem.Spacing.sm) {
            // Quick stats
            HStack(spacing: DesignSystem.Spacing.md) {
                // Confidence meter
                if let confidence = meta.confidence {
                    HStack(spacing: 6) {
                        Circle()
                            .fill(confidenceColor(confidence))
                            .frame(width: 8, height: 8)
                        Text("\(Int(confidence * 100))%")
                            .font(DesignSystem.Typography.caption)
                            .fontWeight(.semibold)
                            .foregroundStyle(confidenceColor(confidence))
                    }
                }

                // Flags
                if meta.rag ?? false {
                    MetaBadge(icon: "doc.text", label: "RAG", color: DesignSystem.Colors.athena)
                }
                if meta.reflection ?? false {
                    MetaBadge(icon: "brain", label: "Reflection", color: DesignSystem.Colors.kokoro)
                }

                // Tools - FIXED: Properly unwrap optional array
                if let tools = meta.tools, !tools.isEmpty {
                    MetaBadge(icon: "wrench.and.screwdriver", label: "\(tools.count) tools", color: DesignSystem.Colors.bridge)
                }

                // Bandit variant indicator
                if meta.banditEnabled, let variant = meta.promptVariant {
                    MetaBadge(icon: "brain", label: variant, color: DesignSystem.Colors.athena)
                }

                Spacer()

                // Bandit feedback buttons (only if interaction_id present)
                if meta.banditEnabled, let interactionId = meta.interactionId {
                    HStack(spacing: 8) {
                        Button {
                            sendFeedback(interactionId: interactionId, thumbsUp: true)
                        } label: {
                            Image(systemName: "hand.thumbsup")
                                .font(.system(size: 12))
                                .foregroundStyle(.green.opacity(0.7))
                        }
                        .buttonStyle(.plain)

                        Button {
                            sendFeedback(interactionId: interactionId, thumbsUp: false)
                        } label: {
                            Image(systemName: "hand.thumbsdown")
                                .font(.system(size: 12))
                                .foregroundStyle(.red.opacity(0.7))
                        }
                        .buttonStyle(.plain)
                    }
                    .padding(.horizontal, 4)
                }

                // Expand button
                Button {
                    withAnimation(DesignSystem.Animation.springy) {
                        showingFull.toggle()
                    }
                } label: {
                    Image(systemName: showingFull ? "chevron.up" : "chevron.down")
                        .font(.system(size: 10))
                        .foregroundStyle(.secondary)
                }
                .buttonStyle(.plain)
            }

            // Expanded details
            if showingFull {
                Divider()
                    .padding(.vertical, DesignSystem.Spacing.xs)

                // Plan steps
                if let plan = meta.plan, !plan.isEmpty {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Plan")
                            .font(DesignSystem.Typography.caption)
                            .foregroundStyle(.secondary)
                        ForEach(Array(plan.enumerated()), id: \.offset) { index, step in
                            HStack(spacing: 6) {
                                Text("\(index + 1).")
                                    .font(DesignSystem.Typography.caption)
                                    .foregroundStyle(.tertiary)
                                    .monospacedDigit()
                                Text(step)
                                    .font(DesignSystem.Typography.caption)
                            }
                        }
                    }
                }

                // Tools used - FIXED: Properly unwrap optional array
                if let tools = meta.tools, !tools.isEmpty {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Tools")
                            .font(DesignSystem.Typography.caption)
                            .foregroundStyle(.secondary)
                        HStack(spacing: 4) {
                            ForEach(tools, id: \.self) { tool in
                                Text(tool)
                                    .font(DesignSystem.Typography.caption)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Color.accentColor.opacity(0.15))
                                    .clipShape(RoundedRectangle(cornerRadius: 4))
                            }
                        }
                    }
                }

                // Performance
                if let latency = meta.latencyMs {
                    HStack {
                        Image(systemName: "speedometer")
                            .font(.system(size: 10))
                        Text("\(latency)ms")
                            .font(DesignSystem.Typography.caption)
                    }
                    .foregroundStyle(.secondary)
                }
            }
        }
        .padding(DesignSystem.Spacing.sm)
        .glassCard(intensity: 0.15)
    }

    private func confidenceColor(_ confidence: Double) -> Color {
        if confidence >= 0.75 { return DesignSystem.Colors.successGreen }
        if confidence >= 0.45 { return DesignSystem.Colors.warningYellow }
        return DesignSystem.Colors.errorRed
    }
}

// MARK: - Meta Badge

struct MetaBadge: View {
    let icon: String
    let label: String
    let color: Color

    var body: some View {
        HStack(spacing: 3) {
            Image(systemName: icon)
                .font(.system(size: 9))
            Text(label)
                .font(DesignSystem.Typography.caption)
        }
        .foregroundStyle(color)
        .padding(.horizontal, 6)
        .padding(.vertical, 3)
        .background(color.opacity(0.15))
        .clipShape(RoundedRectangle(cornerRadius: 6))
    }
}

// MARK: - Custom Bubble Shape

struct BubbleShape: Shape {
    let isUser: Bool

    func path(in rect: CGRect) -> Path {
        let radius = DesignSystem.Radius.lg
        let tailSize: CGFloat = 8

        var path = Path()

        if isUser {
            // Right-aligned bubble with tail on right
            path.move(to: CGPoint(x: rect.minX + radius, y: rect.minY))
            path.addLine(to: CGPoint(x: rect.maxX - radius, y: rect.minY))
            path.addQuadCurve(
                to: CGPoint(x: rect.maxX, y: rect.minY + radius),
                control: CGPoint(x: rect.maxX, y: rect.minY)
            )
            path.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY - radius - tailSize))
            path.addQuadCurve(
                to: CGPoint(x: rect.maxX - radius, y: rect.maxY - tailSize),
                control: CGPoint(x: rect.maxX, y: rect.maxY - tailSize)
            )
            path.addLine(to: CGPoint(x: rect.maxX - tailSize, y: rect.maxY - tailSize))
            path.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY))
            path.addLine(to: CGPoint(x: rect.maxX - tailSize, y: rect.maxY - tailSize))
            path.addLine(to: CGPoint(x: rect.minX + radius, y: rect.maxY - tailSize))
            path.addQuadCurve(
                to: CGPoint(x: rect.minX, y: rect.maxY - radius - tailSize),
                control: CGPoint(x: rect.minX, y: rect.maxY - tailSize)
            )
            path.addLine(to: CGPoint(x: rect.minX, y: rect.minY + radius))
            path.addQuadCurve(
                to: CGPoint(x: rect.minX + radius, y: rect.minY),
                control: CGPoint(x: rect.minX, y: rect.minY)
            )
        } else {
            // Left-aligned bubble with tail on left
            path.move(to: CGPoint(x: rect.maxX - radius, y: rect.minY))
            path.addLine(to: CGPoint(x: rect.minX + radius, y: rect.minY))
            path.addQuadCurve(
                to: CGPoint(x: rect.minX, y: rect.minY + radius),
                control: CGPoint(x: rect.minX, y: rect.minY)
            )
            path.addLine(to: CGPoint(x: rect.minX, y: rect.maxY - radius - tailSize))
            path.addQuadCurve(
                to: CGPoint(x: rect.minX + radius, y: rect.maxY - tailSize),
                control: CGPoint(x: rect.minX, y: rect.maxY - tailSize)
            )
            path.addLine(to: CGPoint(x: rect.minX + tailSize, y: rect.maxY - tailSize))
            path.addLine(to: CGPoint(x: rect.minX, y: rect.maxY))
            path.addLine(to: CGPoint(x: rect.minX + tailSize, y: rect.maxY - tailSize))
            path.addLine(to: CGPoint(x: rect.maxX - radius, y: rect.maxY - tailSize))
            path.addQuadCurve(
                to: CGPoint(x: rect.maxX, y: rect.maxY - radius - tailSize),
                control: CGPoint(x: rect.maxX, y: rect.maxY - tailSize)
            )
            path.addLine(to: CGPoint(x: rect.maxX, y: rect.minY + radius))
            path.addQuadCurve(
                to: CGPoint(x: rect.maxX - radius, y: rect.minY),
                control: CGPoint(x: rect.maxX, y: rect.minY)
            )
        }

        path.closeSubpath()
        return path
    }
}

// MARK: - Preview

#Preview {
    VStack(spacing: 20) {
        ModernMessageBubble(
            message: ChatMessage(
                role: .user,
                content: "Can you explain how the bridge service routes requests?"
            ),
            showMeta: true
        )

        ModernMessageBubble(
            message: ChatMessage(
                role: .assistant,
                content: "The Bridge service acts as an API gateway that routes incoming requests to the appropriate backend services (Athena, UAT, Kokoro) based on the request type and current system state.",
                meta: MetaPromptInfo(
                    enabled: true,
                    confidence: 0.87,
                    style: "detailed",
                    rag: true,
                    reflection: true,
                    plan: ["Parse request", "Check routing policy", "Forward to service"],
                    tools: ["curl", "jq"],
                    latencyMs: 145,
                    promptTokens: nil,
                    completionTokens: nil
                )
            ),
            showMeta: true
        )
    }
    .padding()
    .background(Color(nsColor: .windowBackgroundColor))
}
