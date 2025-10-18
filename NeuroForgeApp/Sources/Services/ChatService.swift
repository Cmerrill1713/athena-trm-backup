import Combine
import Foundation

// MARK: - Chat Contract Models
struct ContractChatMessage: Codable {
    let role: String
    let content: String
}

struct ContractChatRequest: Codable {
    let session_id: String
    let messages: [ContractChatMessage]
    let stream: Bool
    let metadata: [String: String]
}

struct ContractChatUsage: Codable {
    let input_tokens: Int
    let output_tokens: Int
}

struct ContractChatResponse: Codable {
    let reply: String
    let mode: String
    let usage: ContractChatUsage
    let latency_ms: Int
    let trace_id: String
    let router_route: String?
    let router_backend: String?
    let router_confidence: Double?
}

/// Minimal, correct ChatService using canonical config
@MainActor
final class ChatService: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var isConnected = false
    @Published var inputText = ""
    @Published var isSending = false

    // Router status for latency badge
    @Published var currentRoute = "mlx"
    @Published var currentLatency = 0
    @Published var routerHealthy = true

    private let base = AppConfig.apiBase
    private let token = AppConfig.bridgeToken
    private let session = URLSession(configuration: .default)
    private var cancellables = Set<AnyCancellable>()

    init(userID _: String = "default", threadID _: String = "default-thread") {
        print("🌐 ChatService initialized with base: \(base.absoluteString)")
        print(
            "🔐 Auth enabled: \(AppConfig.bridgeAuthEnabled), token present: \(!token.isEmpty)")

        // Add welcome message with personality
        messages.append(
            ChatMessage(
                text: "Hello! I'm Athena ✨\n\nI'm your AI assistant, running locally on your machine with powerful models. I'm here to help you think through problems, write better code, and explore ideas together.\n\nWhat would you like to work on today?",
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
        // Set sending state (but don't disable input!)
        isSending = true
        
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
        
        // Clear sending state - this triggers focus restoration in ChatInputBar
        isSending = false
    }

    private func sendToBackend(_ text: String) async throws -> String {
        var request = URLRequest(url: base.appendingPathComponent("api/chat"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30

        if !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        // Use proper contract format
        let payload = ContractChatRequest(
            session_id: "ios-dev",
            messages: [ContractChatMessage(role: "user", content: text)],
            stream: false,
            metadata: ["client": "NeuroForgeApp", "version": "1.0.0"]
        )

        request.httpBody = try JSONEncoder().encode(payload)

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

        let chatResponse = try JSONDecoder().decode(ContractChatResponse.self, from: data)

        // Update router status for latency badge
        currentRoute = chatResponse.router_route ?? "unknown"
        currentLatency = chatResponse.latency_ms
        routerHealthy = chatResponse.mode == "prod"

        // Log mode for debugging
        print("🔧 Chat response mode: \(chatResponse.mode)")
        print("🔧 Chat latency: \(chatResponse.latency_ms)ms")
        print("🔧 Router route: \(currentRoute)")

        return chatResponse.reply
    }
}
