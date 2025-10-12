import SwiftUI

struct ChatView: View {
    @State private var input = ""
    @State private var messages: [String] = []
    @State private var sending = false
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
                Text("Enter = send, Shift+Enter = newline")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()
                Button(sending ? "Sending…" : "Send") {
                    Task { await send() }
                }
                .disabled(sending || input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                .accessibilityIdentifier("send_button")
            }
        }
        .padding(12)
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
        } catch {
            await MainActor.run { append("⚠️ \(error.localizedDescription)") }
        }
    }
}
