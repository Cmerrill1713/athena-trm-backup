import SwiftUI

// MARK: - Example Integration

/// Example showing how to integrate MetaPromptPanel into your chat view
/// Copy-paste the relevant parts into your actual ChatView

#if DEBUG

struct MetaPromptExampleChatView: View {
    @State private var messages: [ExampleMessage] = [
        ExampleMessage(
            role: .user,
            content: "Check logs and run tests",
            meta: nil
        ),
        ExampleMessage(
            role: .assistant,
            content: "I'll check the logs and run the test suite for you.",
            meta: MetaPromptInfo(
                enabled: true,
                confidence: 0.89,
                style: "reasoned",
                rag: true,
                reflection: false,
                plan: [
                    "Parse user intent",
                    "Check log files for errors",
                    "Run pytest suite",
                    "Summarize findings"
                ],
                tools: ["grep", "pytest", "tail"],
                latencyMs: 756,
                promptTokens: 142,
                completionTokens: 298
            )
        ),
        ExampleMessage(
            role: .user,
            content: "What about?",
            meta: nil
        ),
        ExampleMessage(
            role: .assistant,
            content: "Could you clarify what you'd like me to check?",
            meta: MetaPromptInfo(
                enabled: true,
                confidence: 0.23,
                style: "uncertain",
                rag: false,
                reflection: true,
                plan: [
                    "Request clarification from user"
                ],
                tools: nil,
                latencyMs: 234,
                promptTokens: 78,
                completionTokens: 45
            )
        )
    ]

    @State private var inputText: String = ""
    @AppStorage("showMetaPrompt") private var showMetaPrompt = true

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Live meta panel at top (shows latest assistant message)
                if showMetaPrompt, let latestMeta = messages.last(where: { $0.role == .assistant })?.meta {
                    VStack {
                        MetaPromptPanel(meta: latestMeta)
                            .padding()
                            .transition(.move(edge: .top).combined(with: .opacity))

                        Divider()
                    }
                }

                // Message list
                ScrollView {
                    LazyVStack(spacing: 16) {
                        ForEach(messages) { message in
                            MessageRowExample(message: message, showMeta: showMetaPrompt)
                        }
                    }
                    .padding()
                }

                Divider()

                // Input bar
                HStack {
                    TextField("Message", text: $inputText)
                        .textFieldStyle(.roundedBorder)

                    Button("Send") {
                        sendMessage()
                    }
                    .disabled(inputText.isEmpty)
                }
                .padding()
            }
            .navigationTitle("Chat with Athena")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button(action: { showMetaPrompt.toggle() }) {
                        Label("Toggle Meta", systemImage: showMetaPrompt ? "brain.head.profile.fill" : "brain.head.profile")
                    }
                }
            }
        }
    }

    private func sendMessage() {
        let userMessage = ExampleMessage(role: .user, content: inputText, meta: nil)
        messages.append(userMessage)
        inputText = ""

        // Simulate assistant response
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            let assistantMessage = ExampleMessage(
                role: .assistant,
                content: "I received your message: \"\(userMessage.content)\"",
                meta: MetaPromptInfo(
                    enabled: true,
                    confidence: 0.75,
                    style: "terse",
                    rag: false,
                    reflection: false,
                    plan: ["Echo user message"],
                    tools: nil,
                    latencyMs: 156,
                    promptTokens: 34,
                    completionTokens: 67
                )
            )
            messages.append(assistantMessage)
        }
    }
}

// MARK: - Message Row

struct MessageRowExample: View {
    let message: ExampleMessage
    var showMeta: Bool

    var body: some View {
        HStack {
            if message.role == .assistant {
                Spacer(minLength: 40)
            }

            VStack(alignment: message.role == .user ? .trailing : .leading, spacing: 8) {
                // Message bubble
                Text(message.content)
                    .padding(12)
                    .background(
                        message.role == .user ? Color.blue : Color.gray.opacity(0.2),
                        in: RoundedRectangle(cornerRadius: 16, style: .continuous)
                    )
                    .foregroundColor(message.role == .user ? .white : .primary)

                // Meta panel (only for assistant messages)
                if showMeta,
                   message.role == .assistant,
                   let meta = message.meta,
                   meta.enabled {
                    MetaPromptPanel(meta: meta)
                }
            }

            if message.role == .user {
                Spacer(minLength: 40)
            }
        }
    }
}

// MARK: - Example Models

struct ExampleMessage: Identifiable, Equatable {
    let id = UUID()
    let role: Role
    let content: String
    let meta: MetaPromptInfo?

    enum Role {
        case user
        case assistant
    }
}

// MARK: - Preview

struct MetaPromptExampleChatView_Previews: PreviewProvider {
    static var previews: some View {
        MetaPromptExampleChatView()
    }
}

#endif
