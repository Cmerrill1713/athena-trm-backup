import SwiftUI

// MARK: - Enhanced Chat View with Meta-Awareness

struct ChatViewEnhanced: View {
    @State private var input = ""
    @State private var messages: [ChatMessage] = []
    @State private var confidenceHistory: [Double] = []
    @State private var debugHistory: [PromptDebugData] = []
    @State private var sending = false
    @State private var showDebugOverlay = false
    
    @StateObject private var voice = VoiceManager()
    @AppStorage("metaVoiceSummary") private var metaVoiceSummary = true
    @AppStorage("showMetaPanels") private var showMetaPanels = true
    
    let api = APIClient()
    
    var body: some View {
        ZStack {
            VStack(spacing: 0) {
                // Health banner
                HealthBanner()
                
                // Confidence sparkline (mini history above chat)
                if !confidenceHistory.isEmpty && showMetaPanels {
                    HStack(spacing: 8) {
                        Image(systemName: "chart.line.uptrend.xyaxis")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        ConfidenceSparkline(history: confidenceHistory)
                            .frame(height: 20)
                        Text("Last \(confidenceHistory.count)")
                            .font(.caption2.monospacedDigit())
                            .foregroundStyle(.tertiary)
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(.ultraThinMaterial)
                }
                
                // Messages
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(alignment: .leading, spacing: 12) {
                            ForEach(messages) { message in
                                messageBubble(for: message)
                                    .id(message.id)
                            }
                        }
                        .padding(12)
                    }
                    .onChange(of: messages.count) { _ in
                        withAnimation(.easeOut(duration: 0.3)) {
                            proxy.scrollTo(messages.last?.id, anchor: .bottom)
                        }
                    }
                }
                
                // Input area
                VStack(spacing: 8) {
                    // Voice state indicator
                    if case .transcribing(let partial) = voice.state {
                        transcriptionBar(partial: partial)
                    }
                    
                    // Text input
                    KeyCatchingTextView(text: $input) {
                        Task { await send() }
                    }
                    .frame(height: 80)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color.secondary.opacity(0.25), lineWidth: 1)
                    )
                    
                    // Controls
                    HStack(spacing: 8) {
                        Text("↵ send • ⇧↵ newline • Space voice • ⌘⇧P debug")
                            .font(.caption2)
                            .foregroundStyle(.tertiary)
                        
                        Spacer()
                        
                        // Voice button
                        voiceButton
                        
                        // Send button
                        Button {
                            Task { await send() }
                        } label: {
                            Image(systemName: "paperplane.fill")
                                .font(.system(size: 14))
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(sending || input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    }
                }
                .padding(12)
                .background(.ultraThinMaterial)
            }
            
            // Debug overlay
            if showDebugOverlay {
                PromptDebugOverlay(
                    isShowing: $showDebugOverlay,
                    history: debugHistory
                )
                .zIndex(100)
            }
        }
        .onAppear {
            // Enable meta features via environment
            // (Backend should read these from .env or config)
        }
        .onChange(of: voice.state) { newState in
            if case .sending(let text) = newState {
                Task { await sendVoice(text) }
            }
        }
        .keyboardShortcut("p", modifiers: [.command, .shift]) {
            withAnimation(.spring(response: 0.3)) {
                showDebugOverlay.toggle()
            }
        }
    }
    
    // MARK: - UI Components
    
    private func messageBubble(for message: ChatMessage) -> some View {
        VStack(alignment: message.role.isUser ? .trailing : .leading, spacing: 6) {
            // Message content
            HStack {
                if message.role.isUser { Spacer(minLength: 40) }
                
                VStack(alignment: .leading, spacing: 4) {
                    if message.role == .userVoice {
                        HStack(spacing: 4) {
                            Image(systemName: "waveform")
                                .font(.caption2)
                            Text("Voice")
                                .font(.caption2.weight(.medium))
                        }
                        .foregroundStyle(.blue.opacity(0.8))
                    }
                    
                    Text(message.content)
                        .textSelection(.enabled)
                }
                .padding(.vertical, 10)
                .padding(.horizontal, 12)
                .background(
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .fill(message.role.isUser ? Color.accentColor.opacity(0.12) : Color.secondary.opacity(0.08))
                        .shadow(color: .black.opacity(0.04), radius: 4, x: 0, y: 2)
                )
                
                if !message.role.isUser { Spacer(minLength: 40) }
            }
            
            // Meta panel (assistant messages only)
            if !message.role.isUser, let meta = message.meta, showMetaPanels {
                MetaPromptPanel(meta: meta)
                    .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
        .animation(.spring(response: 0.4, dampingFraction: 0.8), value: message.meta != nil)
    }
    
    private var voiceButton: some View {
        let listening = voice.state == .listening || (voice.state != .idle && voice.state != .error(""))
        
        return Button {
            Task {
                if listening {
                    voice.finishListening()
                } else {
                    await voice.startListening()
                }
            }
        } label: {
            Image(systemName: listening ? "waveform.circle.fill" : "mic.fill")
                .font(.system(size: 14))
                .foregroundStyle(listening ? .blue : .primary)
        }
        .buttonStyle(.bordered)
        .help("Hold Space or click to talk")
    }
    
    private func transcriptionBar(partial: String) -> some View {
        HStack(spacing: 8) {
            ProgressView()
                .scaleEffect(0.7)
            Text(partial.isEmpty ? "Listening..." : partial)
                .font(.callout)
                .lineLimit(2)
            Spacer()
            Button("Send") {
                Task { await sendVoice(partial) }
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.small)
            .disabled(partial.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
        }
        .padding(10)
        .background(RoundedRectangle(cornerRadius: 10).fill(.thinMaterial))
        .transition(.opacity.combined(with: .move(edge: .bottom)))
    }
    
    // MARK: - Send Logic
    
    private func send() async {
        let text = input.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        
        sending = true
        defer { sending = false }
        
        // Add user message
        await MainActor.run {
            messages.append(ChatMessage(role: .user, content: text))
            input = ""
        }
        
        // Send to backend
        await sendToBackend(text, isVoice: false)
    }
    
    private func sendVoice(_ text: String) async {
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        sending = true
        defer { sending = false }
        
        // Add user voice message
        await MainActor.run {
            messages.append(ChatMessage(role: .userVoice, content: text))
        }
        
        // Send to backend
        await sendToBackend(text, isVoice: true)
    }
    
    private func sendToBackend(_ text: String, isVoice: Bool) async {
        do {
            // Classify task
            let kind: ChatTaskKind = text.contains("image") ? .visionDescribe :
                                     text.contains("code") ? .coding :
                                     text.contains("why") ? .reasoning : .smalltalk
            
            let task = ChatTask(kind: kind, text: text, imageBase64: nil)
            
            // TODO: Get meta-response from backend
            // For now, simulate meta data
            let reply = try await api.chat(task)
            let meta = simulateMetaResponse(for: text)
            
            // Record debug data
            await MainActor.run {
                if let meta = meta {
                    debugHistory.append(PromptDebugData(
                        originalPrompt: text,
                        rewrittenPrompt: simulateRewrite(text),
                        confidenceDelta: meta.confidence - 0.5,
                        reflectionSteps: meta.plan,
                        timestamp: Date()
                    ))
                    confidenceHistory.append(meta.confidence)
                    if confidenceHistory.count > 10 {
                        confidenceHistory.removeFirst()
                    }
                }
            }
            
            // Speak meta summary first (if enabled and voice triggered)
            if isVoice && metaVoiceSummary && voice.ttsEnabled, let meta = meta {
                let summary = generateMetaSummary(meta)
                voice.speak(summary)
                try? await Task.sleep(nanoseconds: UInt64(summary.count * 50_000_000)) // ~50ms per char
            }
            
            // Add assistant message
            await MainActor.run {
                messages.append(ChatMessage(role: .assistant, content: reply, meta: meta))
            }
            
            // Speak reply
            if voice.ttsEnabled {
                voice.speak(reply)
            }
            
        } catch {
            await MainActor.run {
                messages.append(ChatMessage(role: .system, content: "⚠️ \(error.localizedDescription)"))
            }
        }
    }
    
    // MARK: - Helpers
    
    private func generateMetaSummary(_ meta: MetaPromptResponse) -> String {
        let conf = Int(meta.confidence * 100)
        if meta.confidence >= 0.8 {
            return "I'm \(conf)% confident. Here's what I'll do:"
        } else if meta.confidence >= 0.6 {
            return "I'm \(conf)% confident. Let me think through this:"
        } else {
            return "I'm only \(conf)% confident. Let me reason carefully:"
        }
    }
    
    private func simulateMetaResponse(for text: String) -> MetaPromptResponse? {
        // TODO: Parse from actual backend response headers or JSON
        let confidence = text.count > 20 ? 0.85 : 0.65
        return MetaPromptResponse(
            confidence: confidence,
            plan: [
                "Parse user intent",
                "Check relevant context",
                "Generate structured response"
            ],
            tools: text.contains("log") ? ["curl", "jq"] : [],
            style: text.contains("why") ? "reasoned" : "direct",
            flags: MetaPromptResponse.Flags(
                rag: text.count > 30,
                reflection: text.contains("?"),
                selfCritique: text.contains("why"),
                chaining: false
            )
        )
    }
    
    private func simulateRewrite(_ text: String) -> String {
        // TODO: Get from backend
        return "Check backend logs for errors in the last 24h, compare error rates, and generate a summary."
    }
}

// MARK: - Preview

#Preview {
    ChatViewEnhanced()
}

