import XCTest

@testable import NeuroForgeApp

/// Tests for RouterClient integration
@MainActor
final class RoutingClientTests: XCTestCase {

    var client: RouterClient!

    override func setUp() async throws {
        try await super.setUp()
        client = RouterClient()
    }

    override func tearDown() async throws {
        client = nil
        try await super.tearDown()
    }

    // MARK: - Health Check Tests

    func testHealthCheck() async throws {
        // Skip if router not running
        guard await canConnectToRouter() else {
            throw XCTSkip("Router not running at localhost:9113")
        }

        let health = try await client.checkHealth()

        XCTAssertEqual(health.status, "healthy")
        XCTAssertEqual(health.service, "athena-router")
        XCTAssertGreaterThan(health.modelsLoaded, 0)
        XCTAssertEqual(health.fallbackThreshold, 0.7)
    }

    // MARK: - Routing Tests

    func testRouteCodeQuery() async throws {
        guard await canConnectToRouter() else {
            throw XCTSkip("Router not running")
        }

        let result = try await client.route(
            query: "Write a Python function",
            domain: "code"
        )

        XCTAssertFalse(result.model.isEmpty)
        XCTAssertGreaterThan(result.confidence, 0)
        XCTAssertLessThan(result.latencyMs, 100)  // Should be < 100ms
    }

    func testRouteGeneralQuery() async throws {
        guard await canConnectToRouter() else {
            throw XCTSkip("Router not running")
        }

        let result = try await client.route(
            query: "What is quantum physics?",
            domain: "general"
        )

        XCTAssertFalse(result.model.isEmpty)
        XCTAssertGreaterThan(result.confidence, 0)
    }

    func testRouteUnknownDomain() async throws {
        guard await canConnectToRouter() else {
            throw XCTSkip("Router not running")
        }

        let result = try await client.route(
            query: "Solve x^2 = 4",
            domain: "math"
        )

        // Should fall back to a valid model
        XCTAssertFalse(result.model.isEmpty)
    }

    // MARK: - Model Listing Tests

    func testListModels() async throws {
        guard await canConnectToRouter() else {
            throw XCTSkip("Router not running")
        }

        let models = try await client.listModels()

        XCTAssertGreaterThan(models.count, 0)

        for model in models {
            XCTAssertFalse(model.modelId.isEmpty)
            XCTAssertFalse(model.domain.isEmpty)
            XCTAssertGreaterThanOrEqual(model.qualityScore, 0)
            XCTAssertLessThanOrEqual(model.qualityScore, 1)
            XCTAssertGreaterThan(model.cost, 0)
        }
    }

    // MARK: - Performance Tests

    func testRoutingLatency() async throws {
        guard await canConnectToRouter() else {
            throw XCTSkip("Router not running")
        }

        let iterations = 10
        var latencies: [Double] = []

        for _ in 0..<iterations {
            let start = Date()
            _ = try await client.route(
                query: "Test query",
                domain: "general"
            )
            let latency = Date().timeIntervalSince(start) * 1000  // ms
            latencies.append(latency)
        }

        let avgLatency = latencies.reduce(0, +) / Double(latencies.count)

        // Average latency should be < 100ms (including network overhead)
        XCTAssertLessThan(avgLatency, 100)

        print("Average routing latency: \(String(format: "%.2f", avgLatency))ms")
    }

    // MARK: - Helper Methods

    private func canConnectToRouter() async -> Bool {
        do {
            _ = try await client.checkHealth()
            return true
        } catch {
            return false
        }
    }
}
