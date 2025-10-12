import XCTest

/// Error path tests for NeuroForge - testing graceful degradation
final class ErrorPathTests: XCTestCase {

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
    }

    func testBackendDisconnectionErrorHandling() {
        let app = XCUIApplication()

        // Start with a different backend URL that will fail
        app.launchEnvironment["API_BASE"] = "http://localhost:9999"  // Non-existent port
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        // Wait for health banner to show disconnected state
        let banner = app.staticTexts["health_banner"]
        XCTAssertTrue(UITestHelpers.waitForElement(banner, timeout: 15, description: "health banner"))

        // Verify banner shows disconnected state
        let bannerText = banner.value as? String ?? ""
        XCTAssertTrue(bannerText.contains("Disconnected") || bannerText.contains("backend unavailable"),
                     "Health banner should show disconnected state when backend is unavailable")

        // Test that chat input still works (graceful degradation)
        let input = app.textViews["chat_input"]
        XCTAssertTrue(UITestHelpers.waitForElement(input, description: "chat input"))

        // Verify input is still functional
        input.click()
        XCTAssertTrue(input.exists, "Input should still exist even when backend is down")

        // Type a message
        UITestHelpers.clearTextInput(input)
        input.typeText("test message")

        // Verify text is visible (no white text issues)
        let inputText = input.value as? String ?? ""
        XCTAssertTrue(inputText.contains("test message"), "Typed text should be visible even when backend is down")

        // Take screenshot of error state
        UITestHelpers.takeScreenshot(name: "Backend Disconnection Error State", testCase: self)

        // Test that send button is still clickable (should show error message)
        let sendButton = app.buttons["send_button"]
        if sendButton.exists && sendButton.isEnabled {
            sendButton.click()

            // Wait for error message
            Thread.sleep(forTimeInterval: 2.0)

            // Look for error message in chat
            let response = app.staticTexts["chat_response"]
            if response.exists {
                let responseText = response.value as? String ?? ""
                XCTAssertTrue(responseText.contains("⚠️") || responseText.contains("error") ||
                             responseText.contains("unavailable") || responseText.contains("disconnected"),
                             "Should show error message when backend is unavailable")
            }
        }
    }

    func testReconnectButtonFunctionality() {
        let app = XCUIApplication()

        // Start with disconnected backend
        app.launchEnvironment["API_BASE"] = "http://localhost:9999"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        // Wait for disconnected banner
        let banner = app.staticTexts["health_banner"]
        XCTAssertTrue(UITestHelpers.waitForElement(banner, timeout: 15))

        // Find and click reconnect button
        let reconnectButton = app.buttons["reconnect_button"]
        if reconnectButton.exists {
            reconnectButton.click()

            // Wait for reconnect attempt
            Thread.sleep(forTimeInterval: 3.0)

            // Verify banner still exists after reconnect attempt
            XCTAssertTrue(banner.exists, "Health banner should still exist after reconnect attempt")

            // Take screenshot of reconnect attempt
            UITestHelpers.takeScreenshot(name: "Reconnect Button Test", testCase: self)
        }
    }

    func testGracefulDegradationWithPartialBackend() {
        let app = XCUIApplication()

        // Test with backend that responds to health but fails on chat
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        // Health banner should show connected initially
        let banner = app.staticTexts["health_banner"]
        XCTAssertTrue(UITestHelpers.waitForElement(banner, timeout: 15))

        // Test chat input functionality
        let input = app.textViews["chat_input"]
        XCTAssertTrue(UITestHelpers.waitForElement(input, description: "chat input"))

        // Clear and type a message
        UITestHelpers.clearTextInput(input)
        input.typeText("graceful degradation test")

        // Send the message
        let sendButton = app.buttons["send_button"]
        if sendButton.exists && sendButton.isEnabled {
            sendButton.click()

            // Wait for response (may be error if chat endpoint is down)
            Thread.sleep(forTimeInterval: 5.0)

            // Verify we got some response (success or error)
            let response = app.staticTexts["chat_response"]
            if response.exists {
                let responseText = response.value as? String ?? ""
                XCTAssertFalse(responseText.isEmpty, "Should receive some response (success or error)")

                // Take screenshot of partial backend response
                UITestHelpers.takeScreenshot(name: "Partial Backend Response", testCase: self)
            }
        }
    }
}
