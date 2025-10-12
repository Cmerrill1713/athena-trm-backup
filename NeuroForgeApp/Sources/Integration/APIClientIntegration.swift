#if false
// ✅ EXAMPLE CODE ONLY - Not compiled to avoid type conflicts
// Copy patterns below into your actual APIClient

import Foundation

// MARK: - API Client Integration Example
// Copy these patterns into your existing APIClient

/// Example showing how to capture meta-prompt info from responses
extension URLSession {
    /// Send chat and capture meta-prompt headers
    func sendChatWithMeta(
        request: URLRequest
    ) async throws -> (message: String, meta: MetaPromptInfo?) {
        let (data, response) = try await self.data(for: request)
        
        // Parse response message
        struct ChatResponse: Decodable {
            let message: String
            let text: String?
            
            var content: String { message.isEmpty ? (text ?? "") : message }
        }
        
        let decoded = try JSONDecoder().decode(ChatResponse.self, from: data)
        
        // ✅ Capture meta from headers (and fallback to JSON body)
        var meta: MetaPromptInfo? = nil
        if let http = response as? HTTPURLResponse {
            let parsed = MetaPromptInfo.from(headers: http.allHeaderFields, fallbackBody: data)
            if parsed.enabled {
                meta = parsed
            }
        }
        
        return (decoded.content, meta)
    }
}

// MARK: - Usage in your chat flow

/*

Example integration in your existing code:

```swift
// When sending a chat message
func sendMessage(_ text: String) async {
    var request = URLRequest(url: URL(string: "\(apiBase)/chat")!)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    
    let body = ["text": text]
    request.httpBody = try? JSONEncoder().encode(body)
    
    do {
        let (message, meta) = try await URLSession.shared.sendChatWithMeta(request: request)
        
        // Create chat message with meta attached
        let chatMessage = ChatMessage(
            role: .assistant,
            content: message,
            meta: meta  // ✅ Meta automatically attached
        )
        
        messages.append(chatMessage)
        
        // Update confidence history for sparkline
        if let confidence = meta?.confidence {
            confidenceHistory.append(confidence)
            if confidenceHistory.count > 10 {
                confidenceHistory.removeFirst()
            }
        }
    } catch {
        print("Chat error: \(error)")
    }
}
```

*/

// MARK: - Streaming Integration (if you use SSE/streaming)

extension URLSession {
    /// For streaming responses, capture meta when stream completes
    func streamChatWithMeta(
        request: URLRequest,
        onChunk: @escaping (String) -> Void
    ) async throws -> MetaPromptInfo? {
        let (bytes, response) = try await self.bytes(for: request)
        
        var fullText = ""
        for try await line in bytes.lines {
            // Process your SSE/streaming format
            if line.hasPrefix("data: ") {
                let chunk = String(line.dropFirst(6))
                fullText += chunk
                onChunk(chunk)
            }
        }
        
        // ✅ After stream completes, parse meta from headers
        if let http = response as? HTTPURLResponse {
            let meta = MetaPromptInfo.from(headers: http.allHeaderFields, fallbackBody: nil)
            return meta.enabled ? meta : nil
        }
        
        return nil
    }
}

// MARK: - Quick Test Helper

#if DEBUG
struct MetaPromptIntegrationTests {
    static func testHeaderParsing() {
        let mockHeaders: [AnyHashable: Any] = [
            "x-meta-enabled": "true",
            "x-meta-confidence": "0.89",
            "x-meta-style": "reasoned",
            "x-meta-rag": "1",
            "x-meta-reflection": "0",
            "x-meta-plan": #"["Parse request","Execute tool","Summarize"]"#,
            "x-meta-tools": #"["pytest","grep"]"#,
            "x-latency-ms": "756",
            "x-prompt-tokens": "142",
            "x-completion-tokens": "298"
        ]
        
        let meta = MetaPromptInfo.from(headers: mockHeaders, fallbackBody: nil)
        
        assert(meta.enabled == true)
        assert(meta.confidence == 0.89)
        assert(meta.style == "reasoned")
        assert(meta.rag == true)
        assert(meta.plan?.count == 3)
        assert(meta.tools == ["pytest", "grep"])
        assert(meta.latencyMs == 756)
        
        print("✅ Meta parsing test passed")
    }
}
#endif

#endif  // ✅ End example code
