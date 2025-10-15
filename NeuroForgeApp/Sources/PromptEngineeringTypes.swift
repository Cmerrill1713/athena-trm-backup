/// Prompt engineering types (stubs for fast-track demo)

struct PromptEngineeringRequest {
    let task: String
    let context: [String: String]
    let constraints: [String]
    let examples: [String]
}

struct PromptEngineeringResponse {
    let success: Bool
    let code: String?
    let explanation: String?
}

