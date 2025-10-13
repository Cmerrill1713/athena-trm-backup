import Foundation

/// Central registry for all service endpoints
public final class ServiceRegistry {
    public static let shared = ServiceRegistry()
    
    private init() {}
    
    // Base URLs (read from environment or defaults)
    public var apiBaseURL: URL {
        if let env = ProcessInfo.processInfo.environment["API_BASE"],
           let url = URL(string: env) {
            return url
        }
        return URL(string: "http://localhost:8014")!
    }
    
    public var ragBaseURL: URL {
        URL(string: "http://localhost:8015")!
    }
    
    public var visionBaseURL: URL {
        URL(string: "http://localhost:8016")!
    }
    
    public var weaviateURL: URL {
        URL(string: "http://localhost:8095")!
    }
    
    public var fastVLMURL: URL {
        URL(string: "http://127.0.0.1:8811")!
    }
    
    public var ollamaURL: URL {
        URL(string: "http://127.0.0.1:11434")!
    }
    
    // Health check endpoints
    public var healthChecks: [String: URL] {
        [
            "bridge": apiBaseURL.appendingPathComponent("/ready"),
            "athena": URL(string: "http://127.0.0.1:8090/ready")!,
            "uat": URL(string: "http://127.0.0.1:8181/ready")!,
            "kokoro": URL(string: "http://127.0.0.1:8020/health")!
        ]
    }
}
