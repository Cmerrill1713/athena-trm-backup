import SwiftUI

// MARK: - Enhanced Chat View with Meta-Awareness

struct ChatViewEnhanced: View {
    @State private var input = ""
    @State private var messages: [ChatMessage] = []
    @State private var confidenceHistory: [Double] = []
    @State private var debugHistory: [PromptDebugData] = []
    @State private var sending = false
    @State private var showDebugOverlay = false
    @State private var toastMessage = ""
    @State private var showToast = false
    
    @StateObject private var voice = VoiceManager()
    @AppStorage("metaVoiceSummary") private var metaVoiceSummary = true
    @AppStorage("showMetaPanels") private var showMetaPanels = true
    @AppStorage("autoOpenOps") private var autoOpenOps = true  // Auto-open on interesting events
    @AppStorage("opsConfidenceThreshold") private var opsConfidenceThreshold: Double = 0.35
    
    @EnvironmentObject var ops: OpsState  // ← Operations monitoring
    @Environment(\.openWindow) private var openWindow
    
    let api = APIClient()
    
    var body: some View {
        ZStack {
            VStack(spacing: 0) {
                // Toolbar
                HStack {
                    // Health banner
                    HealthBanner()
                    
                    Spacer()
                    
                    // Operations window button
                    Button {
                        openWindow(id: "ops")
                    } label: {
                        Label("Operations", systemImage: "rectangle.badge.plus")
                            .font(.caption)
                    }
                    .buttonStyle(.bordered)
                    .help("Open Operations window (⌘⌥O)")
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                
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
                    .onChange(of: messages.count) {
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
                    
                    // Quick action buttons (feature-gated)
                    quickActionBar
                    
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
            
            // Toast notification
            if showToast {
                VStack {
                    Spacer()
                    Text(toastMessage)
                        .font(.callout)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .background(.ultraThinMaterial)
                        .clipShape(RoundedRectangle(cornerRadius: 10))
                        .shadow(radius: 8)
                        .padding(.bottom, 20)
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                }
                .zIndex(99)
            }
        }
        .onAppear {
            // Reset session counters on launch
            ops.resetSession()
        }
        .onChange(of: voice.state) { _, newState in
            if case .sending(let text) = newState {
                Task { await sendVoice(text) }
            }
        }
        .toolbar {
            ToolbarItem(placement: .automatic) {
                Button {
                    openWindow(id: "ops")
                } label: {
                    Label("Pop Out", systemImage: "rectangle.badge.plus")
                }
                .help("Open Operations in a separate window")
            }
        }
    }
    
    // MARK: - UI Components
    
    @ViewBuilder
    private var quickActionBar: some View {
        if Features.healthProbe || Features.rag || Features.vision {
            HStack(spacing: 8) {
                if Features.healthProbe {
                    Button {
                        Task { await probeAll() }
                    } label: {
                        Label("Health", systemImage: "heart.circle")
                            .font(.caption)
                    }
                }
                
                if Features.rag {
                    Button {
                        Task { await injectRAGContext() }
                    } label: {
                        Label("RAG", systemImage: "doc.text.magnifyingglass")
                            .font(.caption)
                    }
                    .disabled(messages.isEmpty)
                }
                
                if Features.vision {
                    Button {
                        Task { await pickAndDescribeImage() }
                    } label: {
                        Label("Vision", systemImage: "eye.circle")
                            .font(.caption)
                    }
                }
            }
            .buttonStyle(.bordered)
            .padding(.horizontal, 8)
            .padding(.top, 4)
        }
    }
    
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
                if let meta = meta, let confidence = meta.confidence {
                    debugHistory.append(PromptDebugData(
                        originalPrompt: text,
                        rewrittenPrompt: simulateRewrite(text),
                        confidenceDelta: confidence - 0.5,  // ✅ Unwrapped optional
                        reflectionSteps: meta.plan ?? [],  // ✅ Unwrapped optional with default
                        timestamp: Date()
                    ))
                    confidenceHistory.append(confidence)  // ✅ Unwrapped optional
                    if confidenceHistory.count > 10 {
                        confidenceHistory.removeFirst()
                    }
                    
                    // Update ops state
                    ops.updateConfidence(confidence)
                    
                    // Auto-open ops window on low confidence
                    if ops.autoOpenOnLowConfidence && confidence < ops.lowConfidenceThreshold && !ops.isWindowOpen {
                        ops.recordEvent(OpsEvent(
                            timestamp: Date(),
                            type: .lowConfidence,
                            message: "Low confidence: \(Int(confidence * 100))% - '\(text.prefix(40))...'",
                            confidence: confidence
                        ))
                        openWindow(id: "ops")
                        showToast(message: "Ops window opened (low confidence)")
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
                let newMessage = ChatMessage(role: .assistant, content: reply, meta: meta)
                messages.append(newMessage)
                
                // Update operations monitoring
                // TODO: Re-enable when MetaInfo integration is complete
                // if let meta = meta {
                //     ops.update(from: meta)
                // }
                
                // Auto-open Ops window on interesting events
                handleInterestingEvent(newMessage)
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
    
    private func generateMetaSummary(_ meta: MetaPromptInfo) -> String {
        guard let confidence = meta.confidence else {
            return "Let me help with that:"
        }
        let conf = Int(confidence * 100)
        if confidence >= 0.8 {
            return "I'm \(conf)% confident. Here's what I'll do:"
        } else if confidence >= 0.6 {
            return "I'm \(conf)% confident. Let me think through this:"
        } else {
            return "I'm only \(conf)% confident. Let me reason carefully:"
        }
    }
    
    private func simulateMetaResponse(for text: String) -> MetaPromptInfo? {
        // TODO: Parse from actual backend response headers or JSON
        let confidence = text.count > 20 ? 0.85 : 0.65
        return MetaPromptInfo(
            enabled: true,
            confidence: confidence,
            style: text.contains("why") ? "reasoned" : "direct",
            rag: text.count > 30,
            reflection: text.contains("?"),
            plan: [
                "Parse user intent",
                "Check relevant context",
                "Generate structured response"
            ],
            tools: text.contains("log") ? ["curl", "jq"] : [],
            latencyMs: nil,
            promptTokens: nil,
            completionTokens: nil
        )
    }
    
    private func simulateRewrite(_ text: String) -> String {
        // TODO: Get from backend
        return "Check backend logs for errors in the last 24h, compare error rates, and generate a summary."
    }
    
    // MARK: - Service Integration Helpers
    
    @MainActor
    private func probeAll() async {
        var summary: [String] = []
        for (name, urlString) in ServiceRegistry.shared.healthChecks {
            guard let url = URL(string: urlString) else { continue }
            let ok = await api.head(url)
            showToast(message: "\(name): \(ok ? "✅" : "⚠️")")
            summary.append("\(name) \(ok ? "✅" : "⚠️")")
            try? await Task.sleep(nanoseconds: 300_000_000) // 300ms between toasts
        }
        
        // Update ops monitoring
        ops.updateHealth(summary: summary.joined(separator: "  "))
    }
    
    @MainActor
    private func injectRAGContext() async {
        guard let lastPrompt = messages.last(where: { $0.role == .user })?.content else {
            showToast(message: "⚠️ No user message to query")
            return
        }
        
        let urlString = ServiceRegistry.shared.ragURL
        guard let url = URL(string: urlString) else { return }
        // RAG service expects {"query": "...", "k": N}, not "top_k"
        let payload = ["query": lastPrompt, "k": 5] as [String : Any]
        guard let body = try? JSONSerialization.data(withJSONObject: payload) else { return }
        
        do {
            let (data, _) = try await api.post(url, body: body)
            // Try to parse as RAG response with hits array
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let hits = json["hits"] as? [[String: Any]] {
                let contexts = hits.compactMap { $0["text"] as? String }
                let context = contexts.prefix(3).joined(separator: "\n\n")
                input = input.isEmpty ? "Context:\n\(context)" : "\(input)\n\nContext:\n\(context)"
                showToast(message: "✅ RAG: \(hits.count) results")
            } else if let context = String(data: data, encoding: .utf8) {
                input = input.isEmpty ? "Context:\n\(context)" : "\(input)\n\nContext:\n\(context)"
                showToast(message: "✅ RAG context injected")
            }
        } catch {
            showToast(message: "⚠️ RAG error: \(error.localizedDescription)")
        }
    }
    
    @MainActor
    private func pickAndDescribeImage() async {
        guard let image = await ImagePickerHelper.pick() else {
            showToast(message: "⚠️ No image selected")
            return
        }
        
        guard let png = image.pngData() else {
            showToast(message: "⚠️ Could not encode image")
            return
        }
        
        let urlString = ServiceRegistry.shared.visionURL
        guard let url = URL(string: urlString) else { return }
        // Vision service may expect {"image": "..."} key (check service docs)
        let payload = ["image": png.base64EncodedString()]
        guard let body = try? JSONSerialization.data(withJSONObject: payload) else { return }
        
        do {
            let (data, _) = try await api.post(url, body: body)
            if let desc = String(data: data, encoding: .utf8) {
                input = input.isEmpty ? desc : "\(input)\n\nImage: \(desc)"
                showToast(message: "✅ Image described")
            }
        } catch {
            showToast(message: "⚠️ Vision error: \(error.localizedDescription)")
        }
    }
    
    @MainActor
    private func showToast(message: String) {
        toastMessage = message
        withAnimation {
            showToast = true
        }
        Task {
            try? await Task.sleep(nanoseconds: 2_000_000_000) // 2s
            withAnimation {
                showToast = false
            }
        }
    }
    
    // MARK: - Auto-Open Operations Window
    
    @MainActor
    private func handleInterestingEvent(_ message: ChatMessage) {
        guard autoOpenOps else { return }
        
        // Check kill switch (environment override)
        if ProcessInfo.processInfo.environment["FEATURE_OPS_AUTOOPEN"] == "0" {
            return
        }
        
        // Collect all trigger reasons
        var reasons: [String] = []
        
        // Check confidence trigger
        if let meta = message.meta,
           let confidence = meta.confidence,
           confidence < opsConfidenceThreshold {
            reasons.append("Low confidence (\(Int(confidence * 100))%)")
        }
        
        // Check error triggers
        let content = message.content.lowercased()
        if content.contains("error:") || 
           content.contains("timeout") ||
           content.contains("failed") {
            reasons.append("Error detected")
        }
        
        // Nothing interesting? Exit early
        guard !reasons.isEmpty else { return }
        
        // Check guardrails (debounce + session limit + snooze)
        let (allowed, limitReason) = ops.shouldAutoOpen()
        if !allowed {
            if let reason = limitReason {
                // Show toast for session limit only
                showToast(message: reason)
            }
            // Silently block if debounced or snoozed
            return
        }
        
        // Coalesce reasons and open
        let merged = reasons.joined(separator: " · ")
        openOpsWindow(respectFocus: true)
        ops.recordAutoOpen()
        showToast(message: "⚠️ Opened Ops — \(merged)")
    }
    
    @MainActor
    private func openOpsWindow(respectFocus: Bool = true) {
        // Don't steal focus if user is typing
        if respectFocus, let event = NSApp.currentEvent, event.type == .keyDown {
            // Open in background without activation
            if let opsWindow = NSApp.windows.first(where: { $0.title == "Operations" }) {
                opsWindow.orderFront(nil)
            } else {
                openWindow(id: "ops")
            }
            return
        }
        
        // Normal open with activation
        openWindow(id: "ops")
    }
}

// MARK: - Preview

#Preview {
    ChatViewEnhanced()
}

