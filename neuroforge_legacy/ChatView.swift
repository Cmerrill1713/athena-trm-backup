import SwiftUI

// Ensure notification names exist in this compilation unit as a fallback for Xcode projects
extension Notification.Name {
    static let nfInsertPrompt = Notification.Name("nf.insertPrompt")
}

// Fallback minimal VoiceManager for targets that don't compile the full Voice module.
// This lives here to ensure the ChatView compilation unit always has a VoiceManager type.
final class VoiceManager: ObservableObject {
    enum State: Equatable {
        case idle, requestingPermission, listening, transcribing(String), sending(String), speaking, error(String)
    }
    @Published var state: State = .idle
    @Published var level: CGFloat = 0
    @Published var transcript: String = ""
    var ttsEnabled = false
    init() {}
    func speak(_ text: String) { /* no-op fallback */ }
    func startListening() async { await MainActor.run { state = .listening } }
    func finishListening() { Task { @MainActor in self.state = .idle } }
}

struct ChatView: View {
    @State private var input = ""
    @State private var messages: [String] = []
    @State private var sending = false
    @StateObject private var voice = VoiceManager()
    let api = APIClient()

    var body: some View {
        VStack(spacing: 10) {
            HealthBanner()

            ScrollView {
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(messages.indices, id: \.self) { i in
                        Text(messages[i])
                            .padding(8)
                            .background(Color.secondary.opacity(0.08))
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                            .accessibilityIdentifier(i == messages.count-1 ? "chat_response" : "chat_response_\((i))")
                    }
                }.frame(maxWidth: .infinity, alignment: .leading)
            }
            .accessibilityIdentifier("chat_messages_scroll")

            KeyCatchingTextView(text: $input) {
                Task { await send() } // Enter → send
            }
            .frame(height: 120)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.secondary.opacity(0.25), lineWidth: 1)
            )
            .accessibilityIdentifier("chat_input")

            HStack {
                Text("Enter = send, Shift+Enter = newline, Space = voice")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()

                // Voice button (push-to-talk)
                Button {
                    Task {
                        if case .listening = voice.state {
                            voice.finishListening()
                        } else {
                            await voice.startListening()
                        }
                    }
                } label: {
                    Image(systemName: voice.state == .listening ? "waveform.circle.fill" : "mic.fill")
                        .font(.system(size: 16))
                        .foregroundColor(voice.state == .listening ? .blue : .primary)
                }
                .help("Hold to talk (Space also works)")
                .accessibilityIdentifier("voice_button")

                Button(sending ? "Sending…" : "Send") {
                    Task { await send() }
                }
                .disabled(sending || input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                .accessibilityIdentifier("send_button")
            }
        }
        .padding(12)
        .onChange(of: voice.state) { _, newState in
            // When voice finishes transcribing, auto-send
            if case .sending(let text) = newState {
                Task { await sendVoiceMessage(text) }
            }
        }
        .onReceive(NotificationCenter.default.publisher(for: .nfInsertPrompt)) { note in
            guard let txt = note.object as? String else { return }
            // Insert at end or append with newline if not empty
            if input.isEmpty {
                input = txt
            } else {
                input += (input.hasSuffix("\n") ? "" : "\n") + txt
            }
        }
    }

    @MainActor private func append(_ s: String) {
        messages.append(s)
    }

    private func send() async {
        let text = input.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        sending = true
        defer { sending = false }
        await MainActor.run { append("You: \(text)") }
        do {
            // classify client-side; backend routes by task
            let kind: ChatTaskKind = text.contains("image:") ? .visionDescribe :
                                     text.contains("code") ? .coding :
                                     text.contains("why") ? .reasoning : .smalltalk
            let task = ChatTask(kind: kind, text: text, imageBase64: nil)
            let reply = try await api.chat(task)
            await MainActor.run { append("AI: \(reply)") }
            await MainActor.run { input = "" }

            // TTS response if enabled
            if voice.ttsEnabled {
                voice.speak(reply)
            }
        } catch {
            await MainActor.run { append("⚠️ \(error.localizedDescription)") }
        }
    }

    private func sendVoiceMessage(_ text: String) async {
        sending = true
        defer { sending = false }
        await MainActor.run { append("You (voice): \(text)") }
        do {
            // classify client-side; backend routes by task
            let kind: ChatTaskKind = text.contains("image") ? .visionDescribe :
                                     text.contains("code") ? .coding :
                                     text.contains("why") ? .reasoning : .smalltalk
            let task = ChatTask(kind: kind, text: text, imageBase64: nil)
            let reply = try await api.chat(task)
            await MainActor.run { append("AI: \(reply)") }

            // TTS response (voice triggered voice response)
            voice.speak(reply)
        } catch {
            await MainActor.run { append("⚠️ \(error.localizedDescription)") }
        }
    }
}
