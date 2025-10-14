import Foundation

// MARK: - Network Integration Helper

extension MetaPromptInfo {
    /// Parse meta from both headers and JSON body (fallback)
    /// Use this in your network layer after receiving a response
    static func from(headers: [AnyHashable: Any], fallbackBody data: Data?) -> MetaPromptInfo {
        var meta = MetaPromptInfo.from(headers: headers)

        // If body contains meta field, merge it
        if let data = data,
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let metaDict = json["meta"] as? [String: Any] {
            meta.merge(from: metaDict)
        }

        return meta
    }
}

// MARK: - ChatMessage Extension (Copy this to your ChatMessage file)

/* ✅ ADD TO YOUR ChatMessage STRUCT:

struct ChatMessage: Identifiable, Codable {
    let id: UUID
    var role: Role
    var content: String
    var timestamp: Date

    // ✅ ADD THIS
    var metaPrompt: MetaPromptInfo? = nil

    enum Role: String, Codable {
        case user
        case assistant
    }
}

*/

// MARK: - Example Network Integration

#if DEBUG

/// Example showing how to integrate in your API client
struct ExampleNetworkIntegration {

    /// Example: Sending a chat message and capturing meta
    func sendMessage(_ text: String) async throws -> ChatMessage {
        let url = URL(string: "http://127.0.0.1:8014/chat")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ["text": text]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        // ✅ KEY PART: Capture both data and response
        let (data, response) = try await URLSession.shared.data(for: request)

        // ✅ Parse meta from headers (and body if present)
        var meta = MetaPromptInfo(enabled: false)
        if let http = response as? HTTPURLResponse {
            meta = MetaPromptInfo.from(headers: http.allHeaderFields, fallbackBody: data)
        }

        // Parse your message content
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        let content = json?["message"] as? String ?? ""

        // ✅ Create message with meta attached
        let message = ChatMessage(
            role: .assistant,
            content: content,
            meta: meta  // Pass meta directly in init
        )

        return message
    }
}

#endif

// MARK: - SwiftUI Preview Helper

#if DEBUG

extension MetaPromptInfo {
    /// Sample meta for previews
    static var highConfidenceSample: MetaPromptInfo {
        MetaPromptInfo(
            enabled: true,
            confidence: 0.92,
            style: "reasoned",
            rag: true,
            reflection: false,
            plan: [
                "Parse user request",
                "Execute pytest with markers",
                "Summarize test results",
                "Return formatted output"
            ],
            tools: ["pytest", "grep", "truth"],
            latencyMs: 756,
            promptTokens: 142,
            completionTokens: 298
        )
    }

    static var lowConfidenceSample: MetaPromptInfo {
        MetaPromptInfo(
            enabled: true,
            confidence: 0.28,
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
    }

    static var mediumConfidenceSample: MetaPromptInfo {
        MetaPromptInfo(
            enabled: true,
            confidence: 0.65,
            style: "terse",
            rag: true,
            reflection: false,
            plan: [
                "Check service health",
                "Return status"
            ],
            tools: ["curl"],
            latencyMs: 312,
            promptTokens: 89,
            completionTokens: 124
        )
    }
}

#endif

// MARK: - Validation Helpers

extension MetaPromptInfo {
    /// Check if meta is actually useful (has data)
    var hasUsefulData: Bool {
        return enabled && (
            confidence != nil ||
            !((plan ?? []).isEmpty) ||
            !((tools ?? []).isEmpty) ||
            style != nil
        )
    }

    /// Debug description
    var debugDescription: String {
        var parts: [String] = []

        if let conf = confidence {
            parts.append("confidence: \(String(format: "%.2f", conf))")
        }
        if let style = style {
            parts.append("style: \(style)")
        }
        if rag == true { parts.append("rag: true") }
        if reflection == true { parts.append("reflection: true") }
        if let tools = tools, !tools.isEmpty {
            parts.append("tools: \(tools.joined(separator: ", "))")
        }
        if let plan = plan, !plan.isEmpty {
            parts.append("plan: \(plan.count) steps")
        }

        return "MetaPromptInfo(\(parts.joined(separator: ", ")))"
    }
}
