import Foundation

// Configuration for API base URL
private func apiBaseURL() -> URL {
    // Check environment variable
    if let envURL = ProcessInfo.processInfo.environment["API_BASE"],
       let url = URL(string: envURL) {
        return url
    }

    // Check Info.plist
    if let plistURL = Bundle.main.infoDictionary?["API_BASE"] as? String,
       let url = URL(string: plistURL) {
        return url
    }

    // Default fallback
    return URL(string: "http://localhost:8014")!
}

struct ChatMessage: Identifiable, Codable {
    let id: String
    let text: String
    let isUser: Bool
    let timestamp: Date
    
    init(id: String = UUID().uuidString, text: String, isUser: Bool, timestamp: Date = Date()) {
        self.id = id
        self.text = text
        self.isUser = isUser
        self.timestamp = timestamp
    }
}

struct ChatRequest: Codable {
    let message: String
    let model: String?
    let request_id: String?
    
    init(message: String, model: String? = nil, request_id: String? = nil) {
        self.message = message
        self.model = model
        self.request_id = request_id
    }
}

struct ChatResponse: Codable {
    let id: String
    let response: String
    let model: String
    let timestamp: String?
    let tokens_used: Int?
}

@MainActor
class ChatService: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var isConnected = false

    private var baseURL: URL { apiBaseURL() }
    private let session: URLSession
    
    init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 60
        config.timeoutIntervalForResource = 120
        self.session = URLSession(configuration: config)
        
        // Add welcome message
        messages.append(ChatMessage(
            text: "👋 Welcome to NeuroForge AI! I can help you with:\n\n" +
                  "🌐 Browser automation (\"Search Google for...\")\n" +
                  "💻 macOS control (\"Open Calculator\")\n" +
                  "🧮 Calculations (\"What's 456 × 789?\")\n" +
                  "💬 General questions\n\n" +
                  "Ask me anything!",
            isUser: false
        ))
    }
    
    func checkConnection() async {
        do {
            let url = baseURL.appendingPathComponent("health")
            let (_, response) = try await session.data(from: url)
            
            if let httpResponse = response as? HTTPURLResponse,
               httpResponse.statusCode == 200 {
                isConnected = true
                print("✅ Connected to NeuroForge backend")
            }
        } catch {
            isConnected = false
            print("❌ Failed to connect: \(error)")
        }
    }
    
    func sendMessage(_ text: String) async {
        print("🚀 ChatService.sendMessage called with: '\(text)'")
        
        // Add user message
        let userMessage = ChatMessage(text: text, isUser: true)
        messages.append(userMessage)
        print("✅ Added user message to UI, total messages: \(messages.count)")
        
        do {
            let url = baseURL.appendingPathComponent("api/chat")
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")

            let chatRequest = ChatRequest(
                message: text,
                model: "llama3.2:3b",
                request_id: UUID().uuidString
            )
            request.httpBody = try JSONEncoder().encode(chatRequest)

            print("📤 Sending POST to \(baseURL.absoluteString)/api/chat")
            
            let (data, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw URLError(.badServerResponse)
            }
            
            print("📥 Received response: HTTP \(httpResponse.statusCode)")
            
            guard httpResponse.statusCode == 200 else {
                let errorText = String(data: data, encoding: .utf8) ?? "Unknown error"
                print("❌ Error response: \(errorText)")
                throw URLError(.badServerResponse)
            }
            
            let chatResponse = try JSONDecoder().decode(ChatResponse.self, from: data)
            
            // Add AI response
            let aiMessage = ChatMessage(
                id: chatResponse.id,
                text: chatResponse.response,
                isUser: false
            )
            messages.append(aiMessage)
            
            print("✅ Message received from model: \(chatResponse.model)")
            
            // Update connection status
            isConnected = true
            
        } catch {
            print("❌ Error sending message: \(error)")
            
            // Add error message
            let errorMessage = ChatMessage(
                text: "❌ Error: \(error.localizedDescription)\n\nMake sure the backend is running on \(baseURL.absoluteString)",
                isUser: false
            )
            messages.append(errorMessage)
            
            isConnected = false
        }
    }
}

