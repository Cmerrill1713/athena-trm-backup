import Foundation

// MARK: - Chat Message Model

struct ChatMessage: Identifiable {
    let id = UUID()
    let role: Role
    let content: String
    let timestamp: Date
    var meta: MetaPromptInfo?  // ✅ Updated to use MetaPromptInfo
    
    enum Role {
        case user
        case userVoice
        case assistant
        case system
        
        var isUser: Bool {
            self == .user || self == .userVoice
        }
    }
    
    init(role: Role, content: String, meta: MetaPromptInfo? = nil) {
        self.role = role
        self.content = content
        self.timestamp = Date()
        self.meta = meta
    }
}

// MARK: - Chat Task (existing)

enum ChatTaskKind: String, Codable {
    case smalltalk
    case coding
    case reasoning
    case visionDescribe = "vision_describe"
}

struct ChatTask: Codable {
    let kind: ChatTaskKind
    let text: String
    let imageBase64: String?
}

