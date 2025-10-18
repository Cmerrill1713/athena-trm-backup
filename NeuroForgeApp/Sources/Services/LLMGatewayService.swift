import Foundation
import OSLog

/// Simple service that calls LLM Gateway directly
/// Bypasses broken router/UAT chain
@MainActor
final class LLMGatewayService: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var isConnected = false
    @Published var isSending = false
    
    // Router status for latency badge
    @Published var currentRoute = "ollama"
    @Published var currentLatency = 0
    @Published var routerHealthy = true
    
    private let gatewayURL = URL(string: "http://127.0.0.1:8015")!
    private let session = URLSession(configuration: .default)
    private let log = Logger(subsystem: "com.neuroforge.athena", category: "llm")
    
    init() {
        log.info("🌐 LLM Gateway Service initialized: \(self.gatewayURL.absoluteString)")
        
        // Add welcome message
        messages.append(
            ChatMessage(
                text: "Hello! I'm Athena ✨\n\nI'm your AI assistant, running locally on your machine with powerful models. I'm here to help you think through problems, write better code, and explore ideas together.\n\nWhat would you like to work on today?",
                isUser: false
            ))
        
        // Start connectivity check
        checkHealth()
    }
    
    func checkHealth() {
        let url = gatewayURL.appendingPathComponent("health")
        session.dataTask(with: url) { [weak self] _, response, _ in
            let connected = (response as? HTTPURLResponse)?.statusCode == 200
            DispatchQueue.main.async {
                self?.isConnected = connected
            }
        }.resume()
    }
    
    func sendMessage(_ text: String) async {
        isSending = true
        
        // Add user message
        let userMessage = ChatMessage(text: text, isUser: true)
        messages.append(userMessage)
        
        do {
            let reply = try await callGateway(text)
            let aiMessage = ChatMessage(text: reply, isUser: false)
            messages.append(aiMessage)
        } catch {
            let errorMessage = ChatMessage(
                text: "❌ Error: \(error.localizedDescription)",
                isUser: false
            )
            messages.append(errorMessage)
            log.error("Send failed: \(error.localizedDescription)")
        }
        
        isSending = false
    }
    
    private func callGateway(_ text: String) async throws -> String {
        let url = gatewayURL.appendingPathComponent("v1/chat/completions")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30
        
        // OpenAI-style payload
        let payload: [String: Any] = [
            "messages": [
                ["role": "user", "content": text]
            ],
            "model": "qwen2.5:0.5b",
            "stream": false
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)
        
        let startTime = Date()
        let (data, response) = try await session.data(for: request)
        let latencyMs = Int(Date().timeIntervalSince(startTime) * 1000)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }
        
        guard httpResponse.statusCode == 200 else {
            let errorText = String(data: data, encoding: .utf8) ?? "HTTP \(httpResponse.statusCode)"
            throw NSError(
                domain: "llm-gateway", code: httpResponse.statusCode,
                userInfo: [NSLocalizedDescriptionKey: errorText]
            )
        }
        
        // Parse response
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let choices = json["choices"] as? [[String: Any]],
              let firstChoice = choices.first,
              let message = firstChoice["message"] as? [String: Any],
              let content = message["content"] as? String else {
            throw URLError(.cannotParseResponse)
        }
        
        // Update router status for latency badge
        currentRoute = "ollama"
        currentLatency = latencyMs
        routerHealthy = true
        
        log.info("✅ LLM response: \(content.prefix(50))... (\(latencyMs)ms)")
        
        return content
    }
}

