import Foundation

/// Meta-prompt orchestration data from Athena/Bridge
/// Captures confidence, style, flags (RAG, reflection), plan, tools, and metrics
struct MetaPromptInfo: Codable, Equatable {
    var enabled: Bool = false
    var confidence: Double? = nil     // 0.0–1.0
    var style: String? = nil          // e.g., "reasoned", "terse", "creative"
    var rag: Bool? = nil
    var reflection: Bool? = nil
    var plan: [String]? = nil
    var tools: [String]? = nil
    var latencyMs: Int? = nil
    var promptTokens: Int? = nil
    var completionTokens: Int? = nil
}

extension MetaPromptInfo {
    /// Parse meta-prompt data from HTTP response headers
    static func from(headers: [AnyHashable: Any]) -> MetaPromptInfo {
        func boolish(_ v: Any?) -> Bool? {
            guard let s = (v as? String)?.lowercased() else { return nil }
            if ["1", "true", "yes", "on"].contains(s) { return true }
            if ["0", "false", "no", "off"].contains(s) { return false }
            return nil
        }
        
        func double(_ v: Any?) -> Double? {
            if let d = v as? Double { return d }
            if let s = v as? String { return Double(s) }
            return nil
        }
        
        func int(_ v: Any?) -> Int? {
            if let i = v as? Int { return i }
            if let s = v as? String { return Int(s) }
            return nil
        }
        
        func jsonArray(_ v: Any?) -> [String]? {
            guard let s = v as? String,
                  let d = s.data(using: .utf8),
                  let arr = try? JSONDecoder().decode([String].self, from: d) else { return nil }
            return arr
        }

        let key = { (k: String) in headers.first { "\($0.key)".lowercased() == k }?.value }

        return MetaPromptInfo(
            enabled: boolish(key("x-meta-enabled")) ?? false,
            confidence: double(key("x-meta-confidence")),
            style: (key("x-meta-style") as? String),
            rag: boolish(key("x-meta-rag")),
            reflection: boolish(key("x-meta-reflection")),
            plan: jsonArray(key("x-meta-plan")),
            tools: jsonArray(key("x-meta-tools")),
            latencyMs: int(key("x-latency-ms")),
            promptTokens: int(key("x-prompt-tokens")),
            completionTokens: int(key("x-completion-tokens"))
        )
    }
    
    /// Merge body JSON meta if present (supplements header data)
    mutating func merge(from jsonDict: [String: Any]) {
        if enabled == false, let e = jsonDict["enabled"] as? Bool { enabled = e }
        if confidence == nil, let c = jsonDict["confidence"] as? Double { confidence = c }
        if style == nil, let s = jsonDict["style"] as? String { style = s }
        if rag == nil, let r = jsonDict["rag"] as? Bool { rag = r }
        if reflection == nil, let r = jsonDict["reflection"] as? Bool { reflection = r }
        if plan == nil, let p = jsonDict["plan"] as? [String] { plan = p }
        if tools == nil, let t = jsonDict["tools"] as? [String] { tools = t }
        if latencyMs == nil, let l = jsonDict["latency_ms"] as? Int { latencyMs = l }
        if promptTokens == nil, let pt = jsonDict["prompt_tokens"] as? Int { promptTokens = pt }
        if completionTokens == nil, let ct = jsonDict["completion_tokens"] as? Int { completionTokens = ct }
    }
    
    /// Total tokens (prompt + completion)
    var totalTokens: Int? {
        guard let p = promptTokens, let c = completionTokens else { return nil }
        return p + c
    }
    
    /// Confidence level label
    var confidenceLevel: String? {
        guard let conf = confidence else { return nil }
        switch conf {
        case ..<0.34: return "Low"
        case ..<0.67: return "Medium"
        default: return "High"
        }
    }
    
    /// Confidence color
    var confidenceColor: (red: Double, green: Double, blue: Double) {
        guard let conf = confidence else { return (0.5, 0.5, 0.5) }
        switch conf {
        case ..<0.34: return (1.0, 0.2, 0.2)  // Red
        case ..<0.67: return (1.0, 0.6, 0.0)  // Orange
        default: return (0.2, 0.8, 0.2)       // Green
        }
    }
}

