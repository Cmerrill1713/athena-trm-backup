import SwiftUI

/// Active feature enum for dynamic send button icon
public enum ActiveFeature {
    case none
    case camera
    case microphone
    case document
}

/// Reusable chat input component with proper Enter key handling
public struct ChatComposer: View {
    @Binding var text: String
    @State private var isSending = false

    var placeholder: String = "Type your message..."
    var onSend: (String) async -> Void
    var isEnabled: Bool = true
    var activeFeature: ActiveFeature = .none

    public init(
        text: Binding<String>,
        placeholder: String = "Type your message...",
        isEnabled: Bool = true,
        activeFeature: ActiveFeature = .none,
        onSend: @escaping (String) async -> Void
    ) {
        self._text = text
        self.placeholder = placeholder
        self.isEnabled = isEnabled
        self.activeFeature = activeFeature
        self.onSend = onSend
    }

    public var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            // Input editor
            KeyCatchingTextEditor(text: self.$text, onSubmit: {
                Task { await self.send() }
            }, focusOnAppear: true)
                .frame(minHeight: 40, maxHeight: 120)
                .background(
                    RoundedRectangle(cornerRadius: 20)
                        .fill(
                            LinearGradient(
                                colors: [AppleColors.textBackground, AppleColors.systemGray6.opacity(0.3)],
                                startPoint: .top,
                                endPoint: .bottom
                            )
                        )
                        .overlay(
                            RoundedRectangle(cornerRadius: 20)
                                .stroke(
                                    LinearGradient(
                                        colors: [AppleColors.systemBlue.opacity(0.3), AppleColors.systemGray.opacity(0.2)],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    ),
                                    lineWidth: 1.5
                                )
                        )
                        .shadow(color: AppleColors.systemBlue.opacity(0.1), radius: 4, x: 0, y: 2)
                )
                .accessibilityIdentifier("chat_input")

            // Send button - enhanced with gradient and dynamic icon
            Button {
                Task { await self.send() }
            } label: {
                Image(systemName: self.sendButtonIcon)
                    .font(.system(size: 20, weight: .semibold))
                    .foregroundColor(.white)
                    .frame(width: 36, height: 36)
                    .background(
                        Circle()
                            .fill(self.canSend ?
                                LinearGradient(
                                    colors: [AppleColors.systemBlue, AppleColors.systemGray],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                ) :
                                LinearGradient(
                                    colors: [AppleColors.systemGray4, AppleColors.systemGray5],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .shadow(color: self.canSend ? AppleColors.systemBlue.opacity(0.4) : Color.clear, radius: 6, x: 0, y: 3)
                    )
            }
            .buttonStyle(.plain)
            .disabled(!self.canSend || self.isSending)
            .keyboardShortcut(.return, modifiers: [])
            .accessibilityIdentifier("chat_send")
            .scaleEffect(self.canSend ? 1.0 : 0.95)
            .animation(.easeInOut(duration: 0.15), value: self.canSend)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
    }

    private var canSend: Bool {
        self.isEnabled && !self.text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    private var sendButtonIcon: String {
        if self.isSending {
            return "stop.circle.fill"
        }

        switch self.activeFeature {
        case .camera:
            return "camera.fill"
        case .microphone:
            return "mic.fill"
        case .document:
            return "doc.fill"
        case .none:
            return "arrow.up.circle.fill"
        }
    }

    private func send() async {
        let trimmed = self.text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        self.isSending = true
        self.text = "" // Clear immediately for better UX

        await self.onSend(trimmed)

        self.isSending = false
    }
}
