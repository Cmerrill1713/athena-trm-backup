import Foundation

/// Prevents duplicate URL handling within a TTL window
final class Dedupe {
    static let shared = Dedupe()
    
    private var recent: [String: Date] = [:]
    private let ttl: TimeInterval = 5  // Ignore repeats within 5 seconds
    private let lock = NSLock()
    
    private init() {}
    
    /// Returns true if this token is new (should be processed)
    /// Returns false if seen recently (should be ignored)
    func claim(_ token: String) -> Bool {
        lock.lock()
        defer { lock.unlock() }
        
        let now = Date()
        
        // Purge old entries
        recent = recent.filter { now.timeIntervalSince($0.value) < ttl }
        
        // Check if we've seen this token recently
        if let lastSeen = recent[token] {
            print("🔇 Token \(token.prefix(8))... seen \(now.timeIntervalSince(lastSeen))s ago")
            return false  // Duplicate - ignore
        }
        
        // New token - claim it
        recent[token] = now
        print("✅ Claimed new token: \(token.prefix(8))...")
        return true
    }
    
    /// Clear all tracked tokens (useful for testing)
    func reset() {
        lock.lock()
        defer { lock.unlock() }
        recent.removeAll()
    }
}

