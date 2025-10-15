import SwiftUI
import Combine
import AVFoundation
import SpriteKit

// MARK: - Design System (adapted for NeuroForge)
struct NFTheme {
    struct ColorToken {
        static let bg = AppleColors.controlBackground
        static let surface = AppleColors.windowBackground
        static let surfaceElev = AppleColors.controlBackground
        static let primary = AppleColors.systemBlue
        static let primaryText = AppleColors.label
        static let secondary = AppleColors.secondaryLabel
        static let accent = AppleColors.systemBlue
        static let success = AppleColors.systemGreen
        static let warn = AppleColors.systemOrange
        static let error = AppleColors.systemRed
        static let outline = AppleColors.systemGray4
        static let bubbleUser = LinearGradient(colors: [AppleColors.systemBlue, AppleColors.systemGray.opacity(0.8)], startPoint: .topLeading, endPoint: .bottomTrailing)
        static let bubbleBot = LinearGradient(colors: [AppleColors.systemGray5, AppleColors.systemGray6], startPoint: .top, endPoint: .bottom)
        static let inputBg = AppleColors.textBackground
    }
    struct Spacing { static let xs: CGFloat = 6; static let sm: CGFloat = 10; static let md: CGFloat = 14; static let lg: CGFloat = 18; static let xl: CGFloat = 24 }
    struct Radius { static let sm: CGFloat = 12; static let md: CGFloat = 16; static let xl: CGFloat = 24 }
    struct Shadow { static let soft = ShadowStyle(radius: 8, y: 4, opacity: 0.1) }
}
struct ShadowStyle { let radius: CGFloat; let y: CGFloat; let opacity: Double }
extension View { func nfShadow(_ s: ShadowStyle = NFTheme.Shadow.soft) -> some View { shadow(color: .black.opacity(s.opacity), radius: s.radius, x: 0, y: s.y) } }

// MARK: - Models (adapted for existing ChatMessage)
enum MessageSender { case user, assistant }

extension ChatMessage {
    var senderType: MessageSender {
        return self.isUser ? .user : .assistant
    }
}

// MARK: - Components
struct ConnectionPill: View {
    var connected: Bool
    var body: some View {
        HStack(spacing: 8) {
            Circle().fill(connected ? AppleColors.systemGreen : AppleColors.systemRed).frame(width: 8, height: 8)
            Text(connected ? "Connected" : "Disconnected")
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(AppleColors.secondaryLabel)
        }
        .padding(.horizontal, 10).padding(.vertical, 6)
        .background(.thinMaterial, in: Capsule())
        .overlay(Capsule().stroke(AppleColors.systemGray4.opacity(0.3), lineWidth: 1))
    }
}

struct ChatHeader: View {
    var connected: Bool
    var profile: UserProfile
    @ObservedObject var avatarEngine: AvatarEngine

    var body: some View {
        HStack(alignment: .center, spacing: NFTheme.Spacing.md) {
            // Athena Avatar - advanced 3D with fallback
            AvatarRenderer.athenaAvatar(awareness: $avatarEngine.sentienceScore)
                .frame(width: 60, height: 60)
            VStack(alignment: .leading, spacing: 2) {
                Text("NeuroForge · Athena")
                    .font(.system(size: 18, weight: .bold, design: .rounded))
                    .foregroundColor(AppleColors.label)
                HStack(spacing: 8) {
                    Text("AI Assistant")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundStyle(AppleColors.secondaryLabel)
                    ConnectionPill(connected: connected)
                }
            }
            Spacer()
        }
        .padding(.horizontal, NFTheme.Spacing.lg)
        .padding(.vertical, NFTheme.Spacing.md)
        .background(.ultraThinMaterial)
        .overlay(Divider(), alignment: .bottom)
    }
}

struct Bubble: View {
    var message: ChatMessage
    var isLastInGroup: Bool
    var body: some View {
        let isUser = message.isUser
        HStack(alignment: .bottom, spacing: NFTheme.Spacing.sm) {
            if !isUser { avatar }
            VStack(alignment: isUser ? .trailing : .leading, spacing: 4) {
                Text(message.text)
                    .textSelection(.enabled)
                    .font(.system(size: 15, weight: .medium))
                    .padding(.horizontal, NFTheme.Spacing.md)
                    .padding(.vertical, NFTheme.Spacing.sm)
                    .background(bubbleBackground(isUser))
                    .clipShape(RoundedRectangle(cornerRadius: NFTheme.Radius.xl, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: NFTheme.Radius.xl, style: .continuous)
                            .stroke(AppleColors.systemGray4.opacity(isUser ? 0 : 0.3), lineWidth: isUser ? 0 : 1)
                    )
                    .nfShadow()
                Text(message.timestamp, style: .time)
                    .font(.system(size: 10, weight: .medium))
                    .foregroundStyle(AppleColors.secondaryLabel)
                    .padding(isUser ? .trailing : .leading, 8)
            }
            if isUser { Spacer(minLength: 24) }
        }
        .frame(maxWidth: .infinity, alignment: message.isUser ? .trailing : .leading)
        .padding(.horizontal, NFTheme.Spacing.lg)
    }

    @ViewBuilder private var avatar: some View {
        Image(systemName: "bolt.horizontal.circle.fill")
            .font(.system(size: 22))
            .foregroundStyle(.white)
            .background(Circle().fill(AppleColors.systemBlue).frame(width: 28, height: 28))
            .offset(y: isLastInGroup ? 0 : 12)
            .accessibilityHidden(true)
    }

    @ViewBuilder private func bubbleBackground(_ isUser: Bool) -> some View {
        if isUser {
            NFTheme.ColorToken.bubbleUser
        } else {
            NFTheme.ColorToken.bubbleBot
        }
    }
}

struct TypingIndicator: View {
    @State private var phase: CGFloat = 0
    var body: some View {
        HStack(spacing: 6) {
            Circle().fill(AppleColors.secondaryLabel).frame(width: 6, height: 6).opacity(Double(0.3 + 0.7 * sin(phase)))
            Circle().fill(AppleColors.secondaryLabel).frame(width: 6, height: 6).opacity(Double(0.3 + 0.7 * sin(phase + .pi/2)))
            Circle().fill(AppleColors.secondaryLabel).frame(width: 6, height: 6).opacity(Double(0.3 + 0.7 * sin(phase + .pi)))
        }
        .padding(8)
        .background(.thinMaterial, in: Capsule())
        .onAppear { withAnimation(.easeInOut(duration: 1).repeatForever(autoreverses: false)) { phase = 2 * .pi } }
        .accessibilityLabel("Assistant is typing")
    }
}

struct InputBar: View {
    @Binding var text: String
    var connected: Bool
    var sending: Bool
    var onSend: () -> Void

    @FocusState private var focused: Bool

    var body: some View {
        HStack(spacing: NFTheme.Spacing.sm) {
            Button(action: {}) { Image(systemName: "paperclip") }
                .buttonStyle(.plain)
                .foregroundStyle(AppleColors.secondaryLabel)
                .accessibilityLabel("Attach")

            TextField("Type your message…", text: $text, axis: .vertical)
                .textFieldStyle(.plain)
                .font(.system(size: 15, weight: .medium))
                .padding(.horizontal, NFTheme.Spacing.md)
                .padding(.vertical, NFTheme.Spacing.sm)
                .background(NFTheme.ColorToken.inputBg, in: RoundedRectangle(cornerRadius: NFTheme.Radius.md, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: NFTheme.Radius.md).stroke(AppleColors.systemGray4.opacity(0.3)))
                .focused($focused)
                .disabled(!connected)

            Button(action: onSend) {
                Image(systemName: sending ? "hourglass" : "paperplane.fill").font(.system(size: 16, weight: .semibold))
            }
            .buttonStyle(.borderedProminent)
            .tint(AppleColors.systemBlue)
            .disabled(!connected || text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            .keyboardShortcut(.return, modifiers: [])
            .accessibilityLabel("Send")
        }
        .padding(NFTheme.Spacing.md)
        .background(.ultraThinMaterial)
        .overlay(Divider(), alignment: .top)
    }
}

// MARK: - Main Chat View
struct NeuroForgeChatView: View {
    let profile: UserProfile
    @StateObject private var chatService: ChatService
    @StateObject private var avatarEngine: AvatarEngine

    init(profile: UserProfile) {
        self.profile = profile
        // Initialize ChatService with profile ID
        _chatService = StateObject(wrappedValue: ChatService(userID: profile.id, threadID: "thread_\(profile.id)_\(UUID().uuidString)"))
        // Initialize Athena Avatar
        _avatarEngine = StateObject(wrappedValue: AvatarEngine())
    }

    var body: some View {
        VStack(spacing: 0) {
            ChatHeader(connected: chatService.isConnected, profile: profile, avatarEngine: avatarEngine)
                .onAppear {
                    updateAvatarMetrics()
                }
                .onChange(of: chatService.isConnected) { _ in
                    updateAvatarMetrics()
                }
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: NFTheme.Spacing.md, pinnedViews: []) {
                        ForEach(Array(chatService.messages.enumerated()), id: \.1.id) { idx, msg in
                            Bubble(message: msg, isLastInGroup: groupBoundary(at: idx))
                                .id(msg.id)
                        }
                        Color.clear.frame(height: 8)
                    }
                    .padding(.top, NFTheme.Spacing.md)
                }
                .background(AppleColors.controlBackground.ignoresSafeArea())
                .onChange(of: chatService.messages.count) { _ in
                    withAnimation {
                        if let last = chatService.messages.last {
                            proxy.scrollTo(last.id, anchor: .bottom)
                        }
                    }
                }
            }
            InputBar(text: $chatService.inputText, connected: chatService.isConnected, sending: false) {
                Task {
                    // Simulate voice energy when sending message
                    avatarEngine.setSpeakingEnergy(rms: 0.8)
                    await chatService.sendCurrentMessage()
                    // Reset voice energy after a delay
                    try? await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
                    avatarEngine.setSpeakingEnergy(rms: 0.0)
                    updateAvatarMetrics() // Update sentience after conversation
                }
            }
            .onChange(of: chatService.inputText) { newText in
                // Simulate subtle voice energy while typing
                let energy = min(Double(newText.count) / 50.0, 0.3)
                avatarEngine.setSpeakingEnergy(rms: energy)
            }
        }
        .background(AppleColors.controlBackground)
    }

    private func updateAvatarMetrics() {
        // Calculate sentience score based on system health
        let connectionScore = chatService.isConnected ? 1.0 : 0.0
        let messageCount = Double(chatService.messages.count)
        let uptimeScore = min(messageCount / 10.0, 1.0) // Increase over time/conversation
        let successRate = 0.9 // Assume good success rate for now

        avatarEngine.updateFromMetrics(
            confidence: connectionScore,
            uptimeHrs: uptimeScore * 24, // Scale to hours
            successRate: successRate
        )
    }

    private func groupBoundary(at index: Int) -> Bool {
        guard index + 1 < chatService.messages.count else { return true }
        let a = chatService.messages[index], b = chatService.messages[index + 1]
        return a.isUser != b.isUser
    }
}

// MARK: - Preview
struct NeuroForgeChatView_Previews: PreviewProvider {
    static var previews: some View {
        let mockProfile = UserProfile(name: "Test User", avatar: "person.circle.fill")
        Group {
            NeuroForgeChatView(profile: mockProfile)
                .preferredColorScheme(.dark)
            NeuroForgeChatView(profile: mockProfile)
        }
    }
}
