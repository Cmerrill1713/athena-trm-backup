import Foundation

struct Features {
    static var rag: Bool { ProcessInfo.processInfo.environment["FEATURE_RAG"] == "1" }
    static var vision: Bool { ProcessInfo.processInfo.environment["FEATURE_VISION"] == "1" }
    static var voice: Bool { ProcessInfo.processInfo.environment["FEATURE_VOICE"] == "1" }
    static var healthProbe: Bool { ProcessInfo.processInfo.environment["FEATURE_HEALTH_PROBE"] == "1" }
    static var modernUI: Bool { ProcessInfo.processInfo.environment["FEATURE_MODERN_UI"] == "1" }
}
