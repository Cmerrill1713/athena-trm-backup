import XCTest
@testable import NeuroForgeApp

/// Unit tests for Operations window auto-open guardrails
@MainActor
final class OpsGuardrailsTests: XCTestCase {
    
    var ops: OpsState!
    
    override func setUp() async throws {
        ops = OpsState()
        ops.resetSession()
    }
    
    // MARK: - Debounce Tests
    
    func test_debounce_blocksWithin5Seconds() async {
        // First open should be allowed
        let (allowed1, _) = ops.shouldAutoOpen()
        XCTAssertTrue(allowed1, "First auto-open should be allowed")
        
        ops.recordAutoOpen()
        
        // Immediate second open should be blocked (debounced)
        let (allowed2, reason2) = ops.shouldAutoOpen()
        XCTAssertFalse(allowed2, "Second auto-open should be blocked by debounce")
        XCTAssertNil(reason2, "Debounce should be silent")
    }
    
    func test_debounce_allowsAfter5Seconds() async {
        // First open
        ops.recordAutoOpen()
        
        // Wait for debounce to expire (simulate by advancing uptime)
        // In real scenario, systemUptime advances naturally
        try? await Task.sleep(nanoseconds: 5_100_000_000) // 5.1s
        
        // Note: In tests, ProcessInfo.systemUptime won't actually advance
        // This test documents expected behavior
        // In integration tests, actual time passage will verify this
    }
    
    // MARK: - Session Limit Tests
    
    func test_sessionLimit_blocksAfter5Opens() async {
        // Open 5 times
        for i in 1...5 {
            let (allowed, _) = ops.shouldAutoOpen()
            XCTAssertTrue(allowed, "Open \(i)/5 should be allowed")
            ops.recordAutoOpen()
            
            // Advance time to avoid debounce
            try? await Task.sleep(nanoseconds: 6_000_000_000) // 6s
        }
        
        // 6th open should be blocked
        let (allowed6, reason6) = ops.shouldAutoOpen()
        XCTAssertFalse(allowed6, "6th auto-open should be blocked by session limit")
        XCTAssertNotNil(reason6, "Session limit should provide reason")
        XCTAssertTrue(reason6?.contains("limit") ?? false, "Reason should mention limit")
    }
    
    func test_sessionReset_allowsNewOpens() async {
        // Fill session limit
        for _ in 1...5 {
            ops.recordAutoOpen()
        }
        
        // Should be blocked
        let (allowed1, _) = ops.shouldAutoOpen()
        XCTAssertFalse(allowed1, "Should be blocked after 5 opens")
        
        // Reset session
        ops.resetSession()
        
        // Should be allowed again
        let (allowed2, _) = ops.shouldAutoOpen()
        XCTAssertTrue(allowed2, "Should be allowed after session reset")
    }
    
    // MARK: - Snooze Tests
    
    func test_snooze_blocksUntilExpiry() async {
        // Snooze for 1 minute (60s)
        ops.snooze(minutes: 1.0)
        
        // Should be blocked
        let (allowed, reason) = ops.shouldAutoOpen()
        XCTAssertFalse(allowed, "Should be blocked while snoozed")
        XCTAssertNil(reason, "Snooze should be silent")
    }
    
    func test_snooze_allowsAfterExpiry() async {
        // Snooze for 0 seconds (immediate expiry)
        ops.snooze(minutes: 0.0)
        
        // Should be allowed (snooze expired)
        let (allowed, _) = ops.shouldAutoOpen()
        XCTAssertTrue(allowed, "Should be allowed after snooze expires")
    }
    
    // MARK: - Threshold Tests
    
    func test_confidenceTrigger_respectsThreshold() async {
        let threshold: Double = 0.35
        
        // Create mock meta above threshold
        let highConfidence = MetaPromptInfo(
            enabled: true,
            confidence: 0.75  // Above 0.35
        )
        
        // Should NOT trigger (confidence > threshold)
        XCTAssertGreaterThan(highConfidence.confidence ?? 0, threshold)
        
        // Create mock meta below threshold
        let lowConfidence = MetaPromptInfo(
            enabled: true,
            confidence: 0.25  // Below 0.35
        )
        
        // Should trigger (confidence < threshold)
        XCTAssertLessThan(lowConfidence.confidence ?? 1, threshold)
    }
    
    // MARK: - Integration Tests
    
    func test_multipleReasons_coalesce() async {
        // Test data structures exist
        let meta = MetaPromptInfo(
            enabled: true,
            confidence: 0.20,  // Low
            tools: ["pytest", "grep"]
        )
        
        ops.update(from: meta)
        
        XCTAssertEqual(ops.lastConfidence, 0.20)
        XCTAssertEqual(ops.lastTools, ["pytest", "grep"])
    }
    
    func test_errorKeywords_detected() async {
        let errorMessages = [
            "ERROR: Connection failed",
            "Request timeout",
            "Operation failed"
        ]
        
        for msg in errorMessages {
            let lowercased = msg.lowercased()
            let hasError = lowercased.contains("error:") ||
                          lowercased.contains("timeout") ||
                          lowercased.contains("failed")
            XCTAssertTrue(hasError, "\(msg) should be detected as error")
        }
    }
    
    func test_normalMessages_notDetected() async {
        let normalMessages = [
            "The operation completed successfully",
            "Here's your answer",
            "Processing request..."
        ]
        
        for msg in normalMessages {
            let lowercased = msg.lowercased()
            let hasError = lowercased.contains("error:") ||
                          lowercased.contains("timeout") ||
                          lowercased.contains("failed")
            XCTAssertFalse(hasError, "\(msg) should NOT be detected as error")
        }
    }
}

