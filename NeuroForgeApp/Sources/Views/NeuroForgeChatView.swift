import AVFoundation
import Combine
import SwiftUI

// MARK: - Design System (adapted for NeuroForge)

enum NFTheme {
    enum ColorToken {
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
        static let bubbleUser = LinearGradient(
            colors: [AppleColors.systemBlue, AppleColors.systemGray.opacity(0.8)],
            startPoint: .topLeading, endPoint: .bottomTrailing
        )
        static let bubbleBot = LinearGradient(
            colors: [AppleColors.systemGray5, AppleColors.systemGray6], startPoint: .top,
            endPoint: .bottom
        )
        static let inputBg = AppleColors.textBackground
    }

    enum Spacing {
        static let xs: CGFloat = 6
        static let sm: CGFloat = 10
        static let md: CGFloat = 14
        static let lg: CGFloat = 18
        static let xl: CGFloat = 24
    }

    enum Radius {
        static let sm: CGFloat = 12
        static let md: CGFloat = 16
        static let xl: CGFloat = 24
    }

    enum Shadow { static let soft = ShadowStyle(radius: 8, y: 4, opacity: 0.1) }
}

struct ShadowStyle {
    let radius: CGFloat
    let y: CGFloat
    let opacity: Double
}

extension View {
    func nfShadow(_ s: ShadowStyle = NFTheme.Shadow.soft) -> some View {
        shadow(color: .black.opacity(s.opacity), radius: s.radius, x: 0, y: s.y)
    }
}

// MARK: - Models (adapted for existing ChatMessage)

enum MessageSender { case user, assistant }

extension ChatMessage {
    var senderType: MessageSender {
        isUser ? .user : .assistant
    }
}

// MARK: - Components

struct ConnectionPill: View {
    var connected: Bool
    var body: some View {
        HStack(spacing: 8) {
            Circle().fill(connected ? AppleColors.systemGreen : AppleColors.systemRed).frame(
                width: 8, height: 8
            )
            Text(connected ? "Connected" : "Disconnected")
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(AppleColors.secondaryLabel)
        }
        .padding(.horizontal, 10).padding(.vertical, 6)
        .background(.thinMaterial, in: Capsule())
        .overlay(Capsule().stroke(AppleColors.systemGray4.opacity(0.3), lineWidth: 1))
        .allowsHitTesting(false)
    }
}

struct ChatHeader: View {
    var connected: Bool
    var profile: UserProfile
    var body: some View {
        HStack(alignment: .center, spacing: NFTheme.Spacing.md) {
            // Modern profile avatar with gradient (matching existing design)
            ZStack {
                if let imageData = profile.profileImageData,
                    let nsImage = NSImage(data: imageData)
                {
                    Image(nsImage: nsImage)
                        .resizable()
                        .scaledToFill()
                        .frame(width: 40, height: 40)
                        .clipShape(Circle())
                } else {
                    Image(systemName: profile.avatar)
                        .font(.system(size: 20, weight: .medium))
                        .foregroundColor(.white)
                        .frame(width: 40, height: 40)
                        .background(
                            Circle()
                                .fill(
                                    LinearGradient(
                                        colors: [AppleColors.systemBlue, AppleColors.systemGray],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                        )
                }
            }
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
                    .clipShape(
                        RoundedRectangle(cornerRadius: NFTheme.Radius.xl, style: .continuous)
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: NFTheme.Radius.xl, style: .continuous)
                            .stroke(
                                AppleColors.systemGray4.opacity(isUser ? 0 : 0.3),
                                lineWidth: isUser ? 0 : 1
                            )
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
            Circle().fill(AppleColors.secondaryLabel).frame(width: 6, height: 6).opacity(
                Double(0.3 + 0.7 * sin(phase)))
            Circle().fill(AppleColors.secondaryLabel).frame(width: 6, height: 6).opacity(
                Double(0.3 + 0.7 * sin(phase + .pi / 2)))
            Circle().fill(AppleColors.secondaryLabel).frame(width: 6, height: 6).opacity(
                Double(0.3 + 0.7 * sin(phase + .pi)))
        }
        .padding(NFToken.Spacing.md)
        .background(.thinMaterial, in: Capsule())
        .onAppear {
            withAnimation(.easeInOut(duration: 1).repeatForever(autoreverses: false)) {
                phase = 2 * .pi
            }
        }
        .accessibilityLabel("Assistant is typing")
    }
}

// InputBar removed - using ChatComposer now

// MARK: - Main Chat View

struct NeuroForgeChatView: View {
    let profile: UserProfile
    let navigationSelection: String?
    @StateObject private var chatService: ChatService
    @State private var focusTrigger = false

    init(profile: UserProfile, navigationSelection: String? = nil) {
        self.profile = profile
        self.navigationSelection = navigationSelection
        // Initialize ChatService with profile ID
        _chatService = StateObject(
            wrappedValue: ChatService(
                userID: profile.id, threadID: "thread_\(profile.id)_\(UUID().uuidString)"
            ))
    }

    var body: some View {
        VStack(spacing: 0) {
            ChatHeader(connected: chatService.isConnected, profile: profile)
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: NFTheme.Spacing.md, pinnedViews: []) {
                        ForEach(Array(chatService.messages.enumerated()), id: \.1.id) {
                            idx, msg in
                            Bubble(message: msg, isLastInGroup: groupBoundary(at: idx))
                                .id(msg.id)
                        }
                        Color.clear.frame(height: 8)
                    }
                    .padding(.top, NFTheme.Spacing.md)
                }
                .background(AppleColors.controlBackground.ignoresSafeArea())
                .onChange(of: chatService.messages.count) { _, _ in
                    withAnimation {
                        if let last = chatService.messages.last {
                            proxy.scrollTo(last.id, anchor: .bottom)
                        }
                    }
                }
            }
            // MARK: - Debug: Known-Good Input Test
            // Uncomment ONE of these to debug:

            // 1. Test basic input functionality:
            // ChatInputBar.knownGoodInput()

            // 2. Test UIKit fallback (guaranteed focus):
            /*
            FirstResponderField(text: $chatService.inputText) {
                Task {
                    await chatService.sendMessage(chatService.inputText)
                    chatService.inputText = ""
                }
            }
            .frame(maxWidth: .infinity)
            .padding(12)
            .background(Color(NSColor.textBackgroundColor))
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color.accentColor, lineWidth: 1.5)
            )
            */

            // 3. Production Input (with debugging enabled)
            ChatInputBar(
                text: $chatService.inputText,
                onSend: { text in
                    Task {
                        await chatService.sendMessage(text)
                    }
                },
                isSending: false,
                focusTrigger: focusTrigger
            )
            .onChange(of: navigationSelection) { _, newSelection in
                // Re-focus input when navigating back to chat
                if newSelection == "chat" {
                    focusTrigger.toggle()  // Trigger focus
                }
            }
            .modifier(HitTestProbe())  // Enable to visualize hit testing
        }
        .background(AppleColors.controlBackground)
    }

    private func groupBoundary(at index: Int) -> Bool {
        guard index + 1 < chatService.messages.count else { return true }
        let a = chatService.messages[index]
        let b = chatService.messages[index + 1]
        return a.isUser != b.isUser
    }
}

// MARK: - Preview

// [PREVIEW] struct NeuroForgeChatView_Previews: PreviewProvider {
// [PREVIEW]     static var previews: some View {
// [PREVIEW]         let mockProfile = UserProfile(name: "Test User", avatar: "person.circle.fill")
// [PREVIEW]         Group {
// [PREVIEW]             NeuroForgeChatView(profile: mockProfile)
// [PREVIEW]                 .preferredColorScheme(.dark)
// [PREVIEW]             NeuroForgeChatView(profile: mockProfile)
// [PREVIEW]         }
// [PREVIEW]     }
// [PREVIEW] }
