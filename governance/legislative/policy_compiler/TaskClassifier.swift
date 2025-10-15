import Foundation

public enum ChatTaskKind: String, Codable {
    case smalltalk, coding, reasoning, visionDescribe, ragQuery
}

public struct ChatTask: Codable {
    public let kind: ChatTaskKind
    public let text: String
    public let imageBase64: String?
    public init(kind: ChatTaskKind, text: String, imageBase64: String? = nil) {
        self.kind = kind; self.text = text; self.imageBase64 = imageBase64
    }
}
