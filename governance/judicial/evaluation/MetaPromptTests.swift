import XCTest
@testable import NeuroForgeApp

/// Unit tests for MetaPrompt parsing and rendering logic
final class MetaPromptTests: XCTestCase {
    
    // MARK: - Helper to fabricate headers
    
    private func makeHeaders(
        enabled: Bool = true,
        confidence: Double,
        style: String = "reasoned",
        rag: Bool = true,
        reflection: Bool = false,
        plan: [String] = ["Step 1", "Step 2"],
        tools: [String] = ["pytest", "grep"],
        latencyMs: Int = 742,
        promptTokens: Int = 120,
        completionTokens: Int = 256
    ) -> [AnyHashable: Any] {
        var headers: [AnyHashable: Any] = [
            "x-meta-enabled": enabled ? "true" : "false",
            "x-meta-confidence": String(confidence),
            "x-meta-style": style,
            "x-meta-rag": rag ? "1" : "0",
            "x-meta-reflection": reflection ? "1" : "0",
            "x-latency-ms": String(latencyMs),
            "x-prompt-tokens": String(promptTokens),
            "x-completion-tokens": String(completionTokens)
        ]
        
        // Encode arrays as JSON strings
        if let planData = try? JSONSerialization.data(withJSONObject: plan),
           let planString = String(data: planData, encoding: .utf8) {
            headers["x-meta-plan"] = planString
        }
        
        if !tools.isEmpty,
           let toolsData = try? JSONSerialization.data(withJSONObject: tools),
           let toolsString = String(data: toolsData, encoding: .utf8) {
            headers["x-meta-tools"] = toolsString
        }
        
        return headers
    }
    
    // MARK: - Tests
    
    func testParsesHighConfidenceHeaders() {
        let headers = makeHeaders(
            confidence: 0.91,
            rag: true,
            reflection: true
        )
        
        let meta = MetaPromptInfo.from(headers: headers, fallbackBody: nil)
        
        XCTAssertTrue(meta.enabled, "Meta should be enabled")
        XCTAssertEqual(meta.confidence, 0.91, accuracy: 0.0001, "Confidence should match")
        XCTAssertEqual(meta.style, "reasoned", "Style should match")
        XCTAssertEqual(meta.rag, true, "RAG flag should be true")
        XCTAssertEqual(meta.reflection, true, "Reflection flag should be true")
        XCTAssertEqual(meta.plan?.count, 2, "Should have 2 plan steps")
        XCTAssertEqual(meta.tools, ["pytest", "grep"], "Tools should match")
        XCTAssertEqual(meta.latencyMs, 742, "Latency should match")
        XCTAssertEqual(meta.promptTokens, 120, "Prompt tokens should match")
        XCTAssertEqual(meta.completionTokens, 256, "Completion tokens should match")
    }
    
    func testLowConfidenceClassifiesCorrectly() {
        let headers = makeHeaders(confidence: 0.28)
        let meta = MetaPromptInfo.from(headers: headers, fallbackBody: nil)
        
        XCTAssertTrue(meta.enabled)
        XCTAssertEqual(meta.confidence, 0.28, accuracy: 0.0001)
        
        // Check confidence level classification
        if let conf = meta.confidence {
            XCTAssertLessThan(conf, 0.34, "Should be classified as low")
        }
    }
    
    func testMediumConfidenceClassifiesCorrectly() {
        let headers = makeHeaders(confidence: 0.55)
        let meta = MetaPromptInfo.from(headers: headers, fallbackBody: nil)
        
        if let conf = meta.confidence {
            XCTAssertGreaterThanOrEqual(conf, 0.34, "Should be above low threshold")
            XCTAssertLessThan(conf, 0.67, "Should be below high threshold")
        }
    }
    
    func testHighConfidenceClassifiesCorrectly() {
        let headers = makeHeaders(confidence: 0.87)
        let meta = MetaPromptInfo.from(headers: headers, fallbackBody: nil)
        
        if let conf = meta.confidence {
            XCTAssertGreaterThanOrEqual(conf, 0.67, "Should be classified as high")
        }
    }
    
    func testDisabledMetaReturnsDisabled() {
        let headers = makeHeaders(enabled: false, confidence: 0.65)
        let meta = MetaPromptInfo.from(headers: headers, fallbackBody: nil)
        
        XCTAssertFalse(meta.enabled, "Meta should be disabled")
    }
    
    func testFallbackToBodyJson() {
        // Simulate missing headers; backend sends JSON meta in body
        let bodyJson: [String: Any] = [
            "message": "Test response",
            "meta": [
                "enabled": true,
                "confidence": 0.72,
                "style": "terse",
                "rag": false,
                "reflection": true,
                "plan": ["Tighten prompt", "Ask clarifier"],
                "tools": [] as [String],
                "latency_ms": 388,
                "prompt_tokens": 64,
                "completion_tokens": 128
            ]
        ]
        
        let body = try! JSONSerialization.data(withJSONObject: bodyJson)
        let meta = MetaPromptInfo.from(headers: [:], fallbackBody: body)
        
        XCTAssertTrue(meta.enabled, "Meta should be enabled from body")
        XCTAssertEqual(meta.confidence, 0.72, accuracy: 0.0001)
        XCTAssertEqual(meta.style, "terse")
        XCTAssertEqual(meta.rag, false)
        XCTAssertEqual(meta.reflection, true)
        XCTAssertEqual(meta.plan?.first, "Tighten prompt")
        XCTAssertEqual(meta.latencyMs, 388)
    }
    
    func testHeadersAndBodyMerge() {
        // Headers have partial data
        let headers: [AnyHashable: Any] = [
            "x-meta-enabled": "true",
            "x-meta-confidence": "0.85"
        ]
        
        // Body has additional data
        let bodyJson: [String: Any] = [
            "meta": [
                "style": "reasoned",
                "plan": ["Step 1", "Step 2", "Step 3"],
                "tools": ["pytest"]
            ]
        ]
        
        let body = try! JSONSerialization.data(withJSONObject: bodyJson)
        var meta = MetaPromptInfo.from(headers: headers, fallbackBody: nil)
        
        // Before merge
        XCTAssertEqual(meta.confidence, 0.85)
        XCTAssertNil(meta.style)
        
        // After merge
        meta = MetaPromptInfo.from(headers: headers, fallbackBody: body)
        XCTAssertEqual(meta.confidence, 0.85, "Confidence from headers")
        XCTAssertEqual(meta.style, "reasoned", "Style from body")
        XCTAssertEqual(meta.plan?.count, 3, "Plan from body")
        XCTAssertEqual(meta.tools, ["pytest"], "Tools from body")
    }
    
    func testEmptyToolsAndPlan() {
        let headers = makeHeaders(
            confidence: 0.65,
            plan: [],
            tools: []
        )
        
        let meta = MetaPromptInfo.from(headers: headers, fallbackBody: nil)
        
        XCTAssertTrue(meta.enabled)
        XCTAssertEqual(meta.plan?.count, 0, "Plan should be empty array")
        XCTAssertEqual(meta.tools?.count, 0, "Tools should be empty array")
    }
    
    func testTotalTokensCalculation() {
        let headers = makeHeaders(
            confidence: 0.75,
            promptTokens: 100,
            completionTokens: 200
        )
        
        let meta = MetaPromptInfo.from(headers: headers, fallbackBody: nil)
        
        XCTAssertEqual(meta.totalTokens, 300, "Total should be sum of prompt + completion")
    }
    
    func testConfidenceLevel() {
        let low = MetaPromptInfo(enabled: true, confidence: 0.25)
        let medium = MetaPromptInfo(enabled: true, confidence: 0.50)
        let high = MetaPromptInfo(enabled: true, confidence: 0.90)
        
        XCTAssertEqual(low.confidenceLevel, "Low")
        XCTAssertEqual(medium.confidenceLevel, "Medium")
        XCTAssertEqual(high.confidenceLevel, "High")
    }
    
    func testChatMessageIntegration() {
        let meta = MetaPromptInfo(
            enabled: true,
            confidence: 0.87,
            style: "reasoned",
            rag: true,
            reflection: false,
            plan: ["Step 1", "Step 2"],
            tools: ["pytest"],
            latencyMs: 456,
            promptTokens: 89,
            completionTokens: 234
        )
        
        let message = ChatMessage(
            role: .assistant,
            content: "Test response",
            meta: meta
        )
        
        XCTAssertNotNil(message.meta, "Meta should be attached to message")
        XCTAssertEqual(message.meta?.confidence, 0.87)
        XCTAssertEqual(message.meta?.style, "reasoned")
        XCTAssertEqual(message.meta?.tools, ["pytest"])
    }
}

// MARK: - Performance Tests

extension MetaPromptTests {
    func testHeaderParsingPerformance() {
        let headers = makeHeaders(confidence: 0.85)
        
        measure {
            for _ in 0..<1000 {
                _ = MetaPromptInfo.from(headers: headers, fallbackBody: nil)
            }
        }
        
        // Parsing should be fast (<1ms per call)
    }
    
    func testBodyParsingPerformance() {
        let bodyJson: [String: Any] = [
            "meta": [
                "enabled": true,
                "confidence": 0.75,
                "style": "reasoned",
                "plan": ["Step 1", "Step 2", "Step 3"],
                "tools": ["pytest", "grep", "truth"]
            ]
        ]
        let body = try! JSONSerialization.data(withJSONObject: bodyJson)
        
        measure {
            for _ in 0..<1000 {
                _ = MetaPromptInfo.from(headers: [:], fallbackBody: body)
            }
        }
    }
}

