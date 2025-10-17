import Combine
import Foundation

/// Minimal, correct ChatService using canonical config
final class ChatService: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var isConnected = false
    @Published var inputText = ""

    private let base = AppConfig.apiBase
    private let token = AppConfig.bridgeToken
    private let session = URLSession(configuration: .default)
    private var cancellables = Set<AnyCancellable>()

    init(userID _: String = "default", threadID _: String = "default-thread") {
        print("🌐 ChatService initialized with base: \(base.absoluteString)")
        print(
            "🔐 Auth enabled: \(AppConfig.bridgeAuthEnabled), token present: \(!token.isEmpty)")

        // Add welcome message
        messages.append(
            ChatMessage(
                text: "✨ Hi! I'm Athena, your AI assistant. How can I help you today?",
                isUser: false
            ))

        // Start connectivity monitoring
        startConnectivityCheck()
    }

    private func startConnectivityCheck() {
        Timer.publish(every: 5, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                self?.checkHealth()
            }
            .store(in: &cancellables)
    }

    func checkHealth() {
        let url = base.appendingPathComponent("health")
        session.dataTask(with: url) { [weak self] _, response, _ in
            let connected = (response as? HTTPURLResponse)?.statusCode == 200
            DispatchQueue.main.async {
                self?.isConnected = connected
            }
        }.resume()
    }

    func sendCurrentMessage() async {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }

        inputText = ""
        await sendMessage(text)
    }

    func sendMessage(_ text: String) async {
        // Add user message
        let userMessage = ChatMessage(text: text, isUser: true)
        messages.append(userMessage)

        do {
            let reply = try await sendToBackend(text)
            let aiMessage = ChatMessage(text: reply, isUser: false)
            messages.append(aiMessage)
        } catch {
            let errorMessage = ChatMessage(
                text: "❌ Error: \(error.localizedDescription)",
                isUser: false
            )
            messages.append(errorMessage)
        }
    }

    private func sendToBackend(_ text: String) async throws -> String {
        var request = URLRequest(url: base.appendingPathComponent("api/chat"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let payload: [String: Any] = ["kind": "chat", "message": text]
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            let errorText = String(data: data, encoding: .utf8) ?? "HTTP \(httpResponse.statusCode)"
            throw NSError(
                domain: "bridge", code: httpResponse.statusCode,
                userInfo: [NSLocalizedDescriptionKey: errorText]
            )
        }

        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let reply = json["response"] as? String
        else {
            throw NSError(
                domain: "bridge", code: -1,
                userInfo: [NSLocalizedDescriptionKey: "Invalid response format"]
            )
        }

        return reply
    }
}
