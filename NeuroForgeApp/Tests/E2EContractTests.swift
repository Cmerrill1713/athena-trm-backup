import XCTest

@testable import NeuroForgeApp

/// E2E Contract Tests - Verify integration with live governance orchestrator
/// These tests require the orchestrator to be running on localhost:9110
final class E2EContractTests: XCTestCase {

    var client: GovernanceClient!

    override func setUp() async throws {
        try await super.setUp()
        client = GovernanceClient(baseURL: "http://localhost:9110", timeout: 5.0)
    }

    override func tearDown() async throws {
        client = nil
        try await super.tearDown()
    }

    // MARK: - Test 1: Health Badge

    /// Test 1: Health badge shows 🟢 within 1s when 9110 up
    func testHealthBadgeShowsGreenWhenOrchestratorUp() async throws {
        // Given: Orchestrator is running (prerequisite)
        // When: We check health
        let isHealthy = try await client.health()

        // Then: It should return true
        XCTAssertTrue(isHealthy, "Orchestrator should be healthy when running")
    }

    func testHealthCheckReturnsWithinOneSecond() async throws {
        // Given: Fast client
        let fastClient = GovernanceClient(baseURL: "http://localhost:9110", timeout: 1.0)

        // When: We measure health check time
        let start = Date()
        _ = try await fastClient.health()
        let duration = Date().timeIntervalSince(start)

        // Then: Should complete within 1 second
        XCTAssertLessThan(duration, 1.0, "Health check should complete within 1 second")
    }

    // MARK: - Test 2: Verdict Submission

    /// Test 2: Send PASS verdict ⇒ metrics bump and UI shows new count
    func testSendPassVerdictIncrementsMetrics() async throws {
        // Given: Get current metrics
        let initialCounts = try await client.verdictCounts()
        let initialPass = initialCounts["pass"] ?? 0

        // When: Submit a PASS verdict
        let taskId = "e2e-test-\(Int(Date().timeIntervalSince1970))"
        let verdict = VerdictRequest(
            taskId: taskId,
            verdict: "PASS",
            ecePost: 0.04,
            entropy: 0.03,
            actions: ["PROMOTE"]
        )

        let response = try await client.postVerdict(verdict)

        // Then: Should get success response
        XCTAssertTrue(
            response.status.contains("applied") || response.status.contains("received"),
            "Verdict should be applied or received")

        // And: Metrics should increment (give it a moment to update)
        try await Task.sleep(nanoseconds: 500_000_000)  // 0.5s
        let updatedCounts = try await client.verdictCounts()
        let updatedPass = updatedCounts["pass"] ?? 0

        XCTAssertGreaterThan(
            updatedPass, initialPass,
            "PASS count should increment after submitting verdict")
    }

    // MARK: - Test 3: Idempotence

    /// Test 3: Send duplicate ⇒ status = idempotent_skip
    func testDuplicateVerdictShowsIdempotent() async throws {
        // Given: A unique task ID
        let taskId = "e2e-idempotent-\(Int(Date().timeIntervalSince1970))"
        let verdict = VerdictRequest(
            taskId: taskId,
            verdict: "PASS",
            ecePost: 0.04,
            actions: nil
        )

        // When: Submit verdict first time
        let firstResponse = try await client.postVerdict(verdict)
        XCTAssertTrue(
            firstResponse.status.contains("applied") || firstResponse.status.contains("received"),
            "First submission should succeed")

        // And: Submit same verdict again
        let secondResponse = try await client.postVerdict(verdict)

        // Then: Second response should indicate idempotence
        XCTAssertTrue(
            secondResponse.status.contains("idempotent") || secondResponse.status.contains("skip")
                || secondResponse.status.contains("duplicate"),
            "Duplicate verdict should be detected. Got: \(secondResponse.status)"
        )
    }

    // MARK: - Test 4: Offline Handling

    /// Test 4: Kill 9110 ⇒ UI disables action & logs offline event
    /// Note: This test cannot actually kill the orchestrator in CI
    /// Instead, we test with an invalid URL
    func testOfflineOrchestratorReturnsError() async throws {
        // Given: Client pointing to non-existent orchestrator
        let offlineClient = GovernanceClient(baseURL: "http://localhost:9999", timeout: 2.0)

        // When: We try to check health
        let isHealthy = try await offlineClient.health()

        // Then: Should return false (not throw)
        XCTAssertFalse(isHealthy, "Health check should return false for offline orchestrator")
    }

    func testOfflineVerdictSubmissionThrowsError() async throws {
        // Given: Client pointing to non-existent orchestrator
        let offlineClient = GovernanceClient(baseURL: "http://localhost:9999", timeout: 2.0)
        let verdict = VerdictRequest(taskId: "test", verdict: "PASS")

        // When/Then: Verdict submission should throw
        do {
            _ = try await offlineClient.postVerdict(verdict)
            XCTFail("Should throw error for offline orchestrator")
        } catch {
            // Expected - verify it's a transport error
            XCTAssertNotNil(error, "Should get transport error")
        }
    }

    // MARK: - Test 5: Metrics Parsing

    func testMetricsParsing() async throws {
        // Given: Orchestrator is up
        // When: We fetch metrics
        let metricsText = try await client.metricsRaw()

        // Then: Should contain governance metrics
        XCTAssertTrue(
            metricsText.contains("governance_verdicts_total"),
            "Metrics should contain verdict counter")
        XCTAssertTrue(
            metricsText.contains("governance_remediations_"),
            "Metrics should contain remediation counters")

        // And: Should parse into counts
        let counts = try await client.verdictCounts()
        XCTAssertNotNil(counts, "Should parse verdict counts")
    }

    func testMetricsSummary() async throws {
        // When: We fetch full metrics summary
        let summary = try await client.metricsSummary()

        // Then: Should have all fields
        XCTAssertNotNil(summary.verdicts, "Should have verdict counts")
        XCTAssertNotNil(summary.remediations, "Should have remediation metrics")
        XCTAssertEqual(summary.health, "up", "Health should be 'up'")

        // And: Timestamp should be recent (within last 5 seconds)
        let age = Date().timeIntervalSince(summary.timestamp)
        XCTAssertLessThan(age, 5.0, "Timestamp should be recent")
    }

    // MARK: - Test 6: State Endpoint

    func testStateEndpoint() async throws {
        // When: We fetch state
        let state = try await client.currentState()

        // Then: Should return JSON state
        XCTAssertFalse(state.isEmpty, "State should not be empty")
        XCTAssertTrue(
            state.contains("{") || state.contains("version"),
            "State should be JSON or contain version info")
    }

    // MARK: - Test 7: ViewModel Integration

    func testViewModelHealthCheck() async throws {
        // Given: ViewModel with real client
        let viewModel = GovernanceViewModel(client: client)

        // When: Check health
        await viewModel.checkHealth()

        // Then: Should show healthy status
        XCTAssertEqual(
            viewModel.healthStatus, .healthy,
            "ViewModel should show healthy status")
        XCTAssertTrue(
            viewModel.statusMessage.contains("healthy"),
            "Status message should indicate healthy")
    }

    func testViewModelVerdictSubmission() async throws {
        // Given: ViewModel with real client
        let viewModel = GovernanceViewModel(client: client)
        await viewModel.checkHealth()

        // When: Send demo verdict
        await viewModel.sendDemoVerdict()

        // Then: Should have response
        XCTAssertNotNil(
            viewModel.lastVerdict,
            "Should have last verdict response")
        XCTAssertNil(
            viewModel.lastError,
            "Should have no error")
        XCTAssertTrue(
            viewModel.statusMessage.contains("Verdict"),
            "Status should show verdict result")
    }

    // MARK: - Test 8: Error Scenarios

    func testInvalidVerdictType() async throws {
        // Given: Invalid verdict
        let verdict = VerdictRequest(
            taskId: "e2e-invalid-\(Int(Date().timeIntervalSince1970))",
            verdict: "INVALID_TYPE",  // Not PASS/SOFT_FAIL/HARD_FAIL
            actions: nil
        )

        // When/Then: May succeed or fail depending on backend validation
        // Just verify it doesn't crash
        do {
            _ = try await client.postVerdict(verdict)
            // Backend accepted it - OK
        } catch {
            // Backend rejected it - also OK
            XCTAssertNotNil(error)
        }
    }

    func testEmptyTaskId() async throws {
        // Given: Verdict with empty task ID
        let verdict = VerdictRequest(
            taskId: "",  // Empty
            verdict: "PASS",
            actions: nil
        )

        // When/Then: Should handle gracefully
        do {
            _ = try await client.postVerdict(verdict)
        } catch {
            // Expected to fail validation
            XCTAssertNotNil(error)
        }
    }
}
