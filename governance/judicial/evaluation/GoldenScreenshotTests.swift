import XCTest

/// Golden screenshot tests for NeuroForge - regression detection with pixel diff
final class GoldenScreenshotTests: XCTestCase {

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
    }

    func test_MainChat_Golden() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"]  = "1"
        app.launch()

        // Wait for banner & input to stabilize
        XCTAssertTrue(app.staticTexts["health_banner"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.textViews["chat_input"].waitForExistence(timeout: 10))
        Thread.sleep(forTimeInterval: 1.0)

        let res = GoldenDiff.compareOrUpdate(name: "MainChatView_Golden", testCase: self)
        XCTAssertTrue(res.passed, "Mismatch rate \(res.mismatchRate) exceeds tolerance")
    }

    func test_ProviderInspector_Golden() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"]  = "1"
        app.launch()

        // Wait for inspector to appear
        let inspector = app.otherElements["provider_inspector"]
        XCTAssertTrue(inspector.waitForExistence(timeout: 10))
        Thread.sleep(forTimeInterval: 2.0) // Wait for health checks

        let res = GoldenDiff.compareOrUpdate(name: "ProviderInspector_Golden", testCase: self)
        XCTAssertTrue(res.passed, "Mismatch rate \(res.mismatchRate) exceeds tolerance")
    }

    func test_ErrorBanner_Golden() throws {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://127.0.0.1:9999" // force disconnect
        app.launchEnvironment["QA_MODE"]  = "1"
        app.launch()

        XCTAssertTrue(app.staticTexts["health_banner"].waitForExistence(timeout: 10))
        Thread.sleep(forTimeInterval: 1.0)

        let res = GoldenDiff.compareOrUpdate(name: "ErrorState_Golden", testCase: self)
        XCTAssertTrue(res.passed, "Mismatch rate \(res.mismatchRate) exceeds tolerance")
    }
}
