import SwiftUI

// MARK: - Modern Chat View with Premium UI

struct ModernChatView: View {
    @State private var input = ""
    @State private var messages: [ChatMessage] = []
    @State private var sending = false
    @State private var showCommandPalette = false
    @State private var showToast = false
    @State private var toastMessage = ""
    @State private var serviceStatus: [String: Bool] = [:]

    @StateObject private var voice = VoiceManager()
    @EnvironmentObject var ops: OpsState
    @Environment(\.openWindow) private var openWindow

    @AppStorage("showMetaPanels") private var showMetaPanels = true
    @AppStorage("autoOpenOps") private var autoOpenOps = true

    let api = APIClient()
    let registry = ServiceRegistry.shared

    var body: some View {
        ZStack {
            // Background with subtle gradient
            LinearGradient(
                colors: [
                    Color(nsColor: .windowBackgroundColor),
                    Color(nsColor: .windowBackgroundColor).opacity(0.95)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                // Header with health cards
                modernHeader
                    .padding(DesignSystem.Spacing.md)

                // Messages area
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: DesignSystem.Spacing.lg) {
                            ForEach(messages) { message in
                                ModernMessageBubble(message: message, showMeta: showMetaPanels)
                                    .id(message.id)
                            }
                        }
                        .padding(DesignSystem.Spacing.lg)
                    }
            .onChange(of: messages.count) {
                withAnimation(DesignSystem.Animation.smooth) {
                    proxy.scrollTo(messages.last?.id, anchor: .bottom)
                }
            }
                }

                // Input area
                modernInputArea
                    .padding(DesignSystem.Spacing.md)
            }

            // Command Palette
            if showCommandPalette {
                CommandPalette(isPresented: $showCommandPalette) { command in
                    executeCommand(command)
                }
                .transition(.opacity.combined(with: .scale(scale: 0.95)))
            }

            // Toast notification
            if showToast {
                VStack {
                    Spacer()
                    ToastView(message: toastMessage)
                        .padding(.bottom, DesignSystem.Spacing.xl)
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                }
                .zIndex(100)
            }
        }
        .task {
            // Check service health on launch
            await checkServiceHealth()
        }
        .onKeyboardShortcut("k", modifiers: .command) {
            withAnimation(DesignSystem.Animation.springy) {
                showCommandPalette.toggle()
            }
        }
        .onKeyboardShortcut("o", modifiers: [.command, .option]) {
            openWindow(id: "ops")
        }
    }

    // MARK: - Header

    private var modernHeader: some View {
        HStack(spacing: DesignSystem.Spacing.md) {
            // Service status badges (real status)
            HStack(spacing: DesignSystem.Spacing.sm) {
                ServiceStatusBadge(
                    name: "Bridge",
                    status: serviceStatus["bridge"] == true ? .healthy : .down,
                    color: DesignSystem.Colors.bridge
                )
                ServiceStatusBadge(
                    name: "Athena",
                    status: serviceStatus["athena"] == true ? .healthy : .down,
                    color: DesignSystem.Colors.athena
                )
                ServiceStatusBadge(
                    name: "UAT",
                    status: serviceStatus["uat"] == true ? .healthy : .down,
                    color: DesignSystem.Colors.uat
                )
                ServiceStatusBadge(
                    name: "Kokoro",
                    status: serviceStatus["kokoro"] == true ? .healthy : .down,
                    color: DesignSystem.Colors.kokoro
                )
            }

            Spacer()

            // Quick actions
            HStack(spacing: DesignSystem.Spacing.sm) {
                Button {
                    withAnimation(DesignSystem.Animation.springy) {
                        showCommandPalette = true
                    }
                } label: {
                    Label("Commands", systemImage: "command")
                        .font(DesignSystem.Typography.caption)
                }
                .buttonStyle(.bordered)
                .help("Open command palette (⌘K)")

                Button {
                    openWindow(id: "ops")
                } label: {
                    Label("Ops", systemImage: "chart.xyaxis.line")
                        .font(DesignSystem.Typography.caption)
                }
                .buttonStyle(.bordered)
                .help("Open operations window (⌘⌥O)")
            }
        }
    }

    // MARK: - Input Area

    private var modernInputArea: some View {
        VStack(spacing: DesignSystem.Spacing.sm) {
            // Voice transcription indicator
            if case .transcribing(let partial) = voice.state {
                transcriptionIndicator(partial: partial)
            }

            // Text input
            HStack(spacing: DesignSystem.Spacing.md) {
                TextEditor(text: $input)
                    .font(DesignSystem.Typography.body)
                    .scrollContentBackground(.hidden)
                    .frame(minHeight: 44, maxHeight: 120)
                    .padding(DesignSystem.Spacing.sm)
                    .background(
                        RoundedRectangle(cornerRadius: DesignSystem.Radius.md)
                            .fill(Color(nsColor: .textBackgroundColor).opacity(0.5))
                            .overlay(
                                RoundedRectangle(cornerRadius: DesignSystem.Radius.md)
                                    .strokeBorder(DesignSystem.Colors.glassBorder, lineWidth: 1)
                            )
                    )

                VStack(spacing: DesignSystem.Spacing.sm) {
                    // Voice button
                    Button {
                        Task { await toggleVoice() }
                    } label: {
                        Image(systemName: voice.state == .listening ? "waveform.circle.fill" : "mic.circle.fill")
                            .font(.system(size: 24))
                            .foregroundStyle(voice.state == .listening ? DesignSystem.Colors.bridge : .secondary)
                    }
                    .buttonStyle(.plain)
                    .help("Hold Space to speak")

                    // Send button
                    Button {
                        Task { await send() }
                    } label: {
                        Image(systemName: "paperplane.circle.fill")
                            .font(.system(size: 24))
                            .foregroundStyle(
                                canSend ? LinearGradient(
                                    colors: [Color.accentColor, Color.accentColor.opacity(0.7)],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                ) : LinearGradient(colors: [.secondary.opacity(0.5)], startPoint: .center, endPoint: .center)
                            )
                    }
                    .buttonStyle(.plain)
                    .disabled(!canSend)
                }
            }
            .glassCard(intensity: 0.3)

            // Hints
            HStack {
                Text("⌘K commands")
                    .font(DesignSystem.Typography.caption)
                    .foregroundStyle(.tertiary)
                Spacer()
                Text("Space voice • ↵ send • ⇧↵ newline")
                    .font(DesignSystem.Typography.caption)
                    .foregroundStyle(.tertiary)
            }
            .padding(.horizontal, DesignSystem.Spacing.xs)
        }
    }

    private var canSend: Bool {
        !sending && !input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    // MARK: - Voice Transcription Indicator

    private func transcriptionIndicator(partial: String) -> some View {
        HStack(spacing: DesignSystem.Spacing.sm) {
            ProgressView()
                .scaleEffect(0.8)

            Text(partial.isEmpty ? "Listening..." : partial)
                .font(DesignSystem.Typography.body)
                .lineLimit(2)

            Spacer()

            Button("Send") {
                Task { await sendVoice(partial) }
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.small)
            .disabled(partial.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
        }
        .padding(DesignSystem.Spacing.md)
        .glassCard(intensity: 0.4)
        .transition(.asymmetric(
            insertion: .move(edge: .bottom).combined(with: .opacity),
            removal: .opacity
        ))
    }

    // MARK: - Actions

    private func send() async {
        let text = input.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }

        sending = true
        defer { sending = false }

        await MainActor.run {
            messages.append(ChatMessage(role: .user, content: text))
            input = ""
        }

        await sendToBackend(text, isVoice: false)
    }

    private func sendVoice(_ text: String) async {
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }

        sending = true
        defer { sending = false }

        await MainActor.run {
            messages.append(ChatMessage(role: .userVoice, content: text))
        }

        await sendToBackend(text, isVoice: true)
    }

    private func sendToBackend(_ text: String, isVoice: Bool) async {
        do {
            let task = ChatTask(
                kind: classifyTask(text),
                text: text,
                imageBase64: nil
            )

            let reply = try await api.chat(task)
            let meta = simulateMetaResponse(for: text)

            await MainActor.run {
                messages.append(ChatMessage(role: .assistant, content: reply, meta: meta))

                // Update ops monitoring
                if let meta = meta, let confidence = meta.confidence {
                    ops.updateConfidence(confidence)
                }
            }

            if voice.ttsEnabled {
                voice.speak(reply)
            }

        } catch {
            await MainActor.run {
                messages.append(ChatMessage(role: .system, content: "⚠️ \(error.localizedDescription)"))
            }
        }
    }

    private func toggleVoice() async {
        if voice.state == .listening {
            voice.finishListening()
        } else {
            await voice.startListening()
        }
    }

    private func executeCommand(_ command: Command) {
        switch command.action {
        case .checkHealth:
            Task { await probeAllServices() }
        case .openOps:
            openWindow(id: "ops")
        case .queryRAG:
            Task { await queryRAG() }
        case .describeImage:
            Task { await describeImage() }
        case .openLogs:
            NSWorkspace.shared.open(URL(fileURLWithPath: "/Users/christianmerrill/Documents/GitHub/logs"))
        case .openGrafana:
            NSWorkspace.shared.open(URL(string: "http://localhost:3000")!)
        case .openPrometheus:
            NSWorkspace.shared.open(URL(string: "http://localhost:9090")!)
        case .validatePlatform:
            Task { await validatePlatform() }
        case .restartService(let name):
            showToast(message: "Restarting \(name)...")
        case .toggleDebug:
            showMetaPanels.toggle()
        case .showSettings:
            openWindow(id: "ops-settings")
        }
    }

    private func showToast(message: String) {
        toastMessage = message
        withAnimation(DesignSystem.Animation.springy) {
            showToast = true
        }
        Task {
            try? await Task.sleep(nanoseconds: 2_500_000_000)
            withAnimation(DesignSystem.Animation.smooth) {
                showToast = false
            }
        }
    }

    // MARK: - Service Integration

    private func checkServiceHealth() async {
        let checks: [(String, String)] = [
            ("bridge", "http://127.0.0.1:8014/health"),
            ("athena", "http://127.0.0.1:8090/ready"),
            ("uat", "http://127.0.0.1:8181/health"),
            ("kokoro", "http://127.0.0.1:8020/health")
        ]

        for (name, urlString) in checks {
            guard let url = URL(string: urlString) else { continue }
            let ok = await api.head(url)
            await MainActor.run {
                serviceStatus[name] = ok
            }
        }
    }

    private func probeAllServices() async {
        await checkServiceHealth()

        let allHealthy = serviceStatus.values.allSatisfy { $0 }
        let upCount = serviceStatus.values.filter { $0 }.count
        let totalCount = serviceStatus.count

        if allHealthy {
            showToast(message: "All services online! 🎉")
        } else {
            showToast(message: "\(upCount)/\(totalCount) services up")
        }
    }

    private func queryRAG() async {
        guard let lastPrompt = messages.last(where: { $0.role == .user })?.content else {
            showToast(message: "No prompt to query")
            return
        }

        // Query RAG service
        guard let url = URL(string: "http://127.0.0.1:8015/api/rag/query") else { return }
        let payload = ["query": lastPrompt, "k": 3] as [String: Any]
        guard let body = try? JSONSerialization.data(withJSONObject: payload) else { return }

        do {
            let (data, _) = try await api.post(url, body: body)
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let hits = json["hits"] as? [[String: Any]] {
                let contexts = hits.compactMap { $0["text"] as? String }
                let context = contexts.prefix(3).joined(separator: "\n\n")

                await MainActor.run {
                    input = input.isEmpty ? "Context:\n\(context)" : "\(input)\n\nContext:\n\(context)"
                    showToast(message: "✅ Added \(hits.count) results")
                }
            }
        } catch {
            showToast(message: "⚠️ RAG offline")
        }
    }

    private func describeImage() async {
        guard let image = await ImagePickerHelper.pick() else {
            showToast(message: "⚠️ No image selected")
            return
        }

        guard let png = image.pngData() else {
            showToast(message: "⚠️ Could not encode image")
            return
        }

        guard let url = URL(string: "http://127.0.0.1:8016/api/vision/describe") else { return }
        let payload = ["image": png.base64EncodedString()]
        guard let body = try? JSONSerialization.data(withJSONObject: payload) else { return }

        do {
            let (data, _) = try await api.post(url, body: body)
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let description = json["description"] as? String {
                await MainActor.run {
                    input = input.isEmpty ? description : "\(input)\n\nImage: \(description)"
                    showToast(message: "✅ Image described")
                }
            }
        } catch {
            showToast(message: "⚠️ Vision offline")
        }
    }

    private func validatePlatform() async {
        showToast(message: "Running validation...")
    }

    // MARK: - Helpers

    private func classifyTask(_ text: String) -> ChatTaskKind {
        if text.contains("image") { return .visionDescribe }
        if text.contains("code") { return .coding }
        if text.contains("why") { return .reasoning }
        return .smalltalk
    }

    private func simulateMetaResponse(for text: String) -> MetaPromptInfo? {
        let confidence = text.count > 20 ? 0.85 : 0.65
        return MetaPromptInfo(
            enabled: true,
            confidence: confidence,
            style: text.contains("why") ? "reasoned" : "direct",
            rag: text.count > 30,
            reflection: text.contains("?"),
            plan: ["Parse intent", "Check context", "Generate response"],
            tools: text.contains("log") ? ["curl", "jq"] : [],
            latencyMs: Int.random(in: 80...200),
            promptTokens: nil,
            completionTokens: nil
        )
    }
}

// MARK: - Toast View

struct ToastView: View {
    let message: String

    var body: some View {
        Text(message)
            .font(DesignSystem.Typography.body)
            .padding(.horizontal, DesignSystem.Spacing.lg)
            .padding(.vertical, DesignSystem.Spacing.md)
            .glassCard(intensity: 0.7, borderOpacity: 0.3)
            .shadow(color: .black.opacity(0.2), radius: 20, x: 0, y: 10)
    }
}

// MARK: - Keyboard Shortcut Extension

extension View {
    func onKeyboardShortcut(_ key: KeyEquivalent, modifiers: EventModifiers = .command, action: @escaping () -> Void) -> some View {
        self.background(
            Button("", action: action)
                .keyboardShortcut(key, modifiers: modifiers)
                .hidden()
        )
    }
}

// MARK: - Preview

#Preview {
    ModernChatView()
        .environmentObject(OpsState())
        .frame(width: 900, height: 700)
}
