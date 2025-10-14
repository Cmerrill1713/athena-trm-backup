import Foundation

public struct PromptTemplate: Identifiable, Codable, Hashable {
    public let id: UUID
    public var title: String
    public var category: String
    public var body: String
    public var tags: [String]

    public init(id: UUID = .init(), title: String, category: String, body: String, tags: [String] = []) {
        self.id = id
        self.title = title
        self.category = category
        self.body = body
        self.tags = tags
    }

    public var variableKeys: [String] {
        // Finds {{var}} tokens
        let regex = try! NSRegularExpression(pattern: #"\{\{([a-zA-Z0-9_]+)\}\}"#)
        let s = body as NSString
        return regex.matches(in: body, range: NSRange(location: 0, length: s.length))
            .compactMap { Range($0.range(at: 1), in: body).map { String(body[$0]) } }
    }

    public func filled(with vars: [String: String]) -> String {
        var out = body
        for (k, v) in vars {
            out = out.replacingOccurrences(of: "{{\(k)}}", with: v)
        }
        return out
    }
}
