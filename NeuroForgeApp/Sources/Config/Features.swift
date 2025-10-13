import Foundation

/// Feature flags loaded from environment variables
enum Features {
    static var rag: Bool {
        ProcessInfo.processInfo.environment["FEATURE_RAG"] == "1"
    }
    
    static var vision: Bool {
        ProcessInfo.processInfo.environment["FEATURE_VISION"] == "1"
    }
    
    static var voice: Bool {
        ProcessInfo.processInfo.environment["FEATURE_VOICE"] == "1"
    }
    
    static var healthProbe: Bool {
        ProcessInfo.processInfo.environment["FEATURE_HEALTH_PROBE"] == "1"
    }
}

