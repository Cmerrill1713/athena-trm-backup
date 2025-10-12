import Foundation

/// Task Intent - Classifies user input into routing categories
struct TaskIntent {
    let kind: String
    let requiresTools: Bool
    let latencyBudgetMs: Int

    init(kind: String, requiresTools: Bool = false, latencyBudgetMs: Int = 2500) {
        self.kind = kind
        self.requiresTools = requiresTools
        self.latencyBudgetMs = latencyBudgetMs
    }
}

/// Task Classifier - Model-agnostic routing
/// Routes by task type, not model names. TRM/LLM picks best model.
class TaskClassifier {

    /// Classify user input into a task type
    /// - Parameter text: User input text
    /// - Returns: Task intent for routing
    static func classify(_ text: String) -> TaskIntent {
        let lower = text.lowercased()

        // Reasoning tasks (use TRM)
        if containsAny(lower, ["explain", "why", "reason", "analyze", "think through"]) {
            return TaskIntent(
                kind: "chat.reasoning",
                requiresTools: false,
                latencyBudgetMs: 5000
            )
        }

        // Coding tasks (need tools + accuracy)
        if containsAny(lower, ["code", "build", "implement", "function", "debug", "refactor"]) {
            return TaskIntent(
                kind: "chat.coding",
                requiresTools: true,
                latencyBudgetMs: 4000
            )
        }

        // Vision tasks
        if containsAny(lower, ["image", "photo", "screenshot", "picture", "see this"]) {
            return TaskIntent(
                kind: "vision.describe",
                requiresTools: false,
                latencyBudgetMs: 3000
            )
        }

        // Chart/OCR specific
        if containsAny(lower, ["chart", "graph", "extract data"]) {
            return TaskIntent(
                kind: "vision.chart",
                requiresTools: false,
                latencyBudgetMs: 3000
            )
        }

        // RAG/search tasks
        if containsAny(lower, ["search", "find", "lookup", "docs", "documentation"]) {
            return TaskIntent(
                kind: "rag.query",
                requiresTools: true,
                latencyBudgetMs: 3500
            )
        }

        // Default: small talk (fast path)
        return TaskIntent(
            kind: "chat.smalltalk",
            requiresTools: false,
            latencyBudgetMs: 1500
        )
    }

    /// Check if text contains any of the keywords
    private static func containsAny(_ text: String, _ keywords: [String]) -> Bool {
        return keywords.contains { text.contains($0) }
    }
}

/// Routing Policy - Loads and resolves task-based routes
class RoutingPolicy {

    static let shared = RoutingPolicy()

    private var policy: [String: Any] = [:]
    private let policyPath = "config/routing_policy.json"

    init() {
        loadPolicy()
    }

    /// Load routing policy from JSON
    private func loadPolicy() {
        guard let url = Bundle.main.url(forResource: "routing_policy", withExtension: "json") ??
                       URL(fileURLWithPath: policyPath) else {
            print("⚠️  Routing policy not found, using defaults")
            return
        }

        do {
            let data = try Data(contentsOf: url)
            if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                policy = json
                print("✅ Loaded routing policy v\(json["version"] as? String ?? "unknown")")
            }
        } catch {
            print("⚠️  Failed to load routing policy: \(error)")
        }
    }

    /// Resolve task to endpoint and parameters
    /// - Parameter task: Task kind (e.g., "chat.reasoning")
    /// - Returns: (endpoint, parameters)
    func resolve(task: String) -> (endpoint: String, parameters: [String: Any]) {
        guard let tasks = policy["tasks"] as? [String: [String: Any]],
              let taskConfig = tasks[task],
              let providers = policy["providers"] as? [String: [String: Any]],
              let providerName = taskConfig["provider"] as? String,
              let providerConfig = providers[providerName],
              let endpoint = providerConfig["endpoint"] as? String else {
            // Fallback to defaults
            return (
                endpoint: "http://localhost:8014/api/chat",
                parameters: ["provider": "llm_router", "tier": "fast"]
            )
        }

        return (endpoint: endpoint, parameters: taskConfig)
    }
}

// MARK: - Usage Example

/*
 // In your chat view model:

 func sendMessage(_ text: String) async throws {
     // 1. Classify task
     let intent = TaskClassifier.classify(text)

     // 2. Resolve route
     let route = RoutingPolicy.shared.resolve(task: intent.kind)

     // 3. Build request
     let body: [String: Any] = [
         "input": text,
         "meta": [
             "task": intent.kind,
             "requires_tools": intent.requiresTools,
             "latency_budget_ms": intent.latencyBudgetMs
         ],
         "policy": route.parameters
     ]

     // 4. Send to endpoint
     try await APIClient.post(route.endpoint, body: body)
 }

 // Examples:
 // "Write a Swift function" → chat.coding → tools enabled
 // "Why is the sky blue?" → chat.reasoning → TRM path
 // "What's in this image?" → vision.describe → vision model
 // "Search docs about..." → rag.query → RAG router
 */
