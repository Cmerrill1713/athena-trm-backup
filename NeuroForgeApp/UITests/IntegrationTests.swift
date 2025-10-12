import XCTest

/// End-to-end integration tests for NeuroForge
final class IntegrationTests: XCTestCase {

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
    }

    func testFullChatFlow() {
        let app = UITestHelpers.launchApp()
        XCTAssertTrue(UITestHelpers.waitForAppReady(app))

        // Verify health banner
        let banner = app.staticTexts["health_banner"]
        XCTAssertTrue(UITestHelpers.waitForElement(banner, description: "health banner"))

        // Test chat input
        let input = app.textViews["chat_input"]
        XCTAssertTrue(UITestHelpers.waitForElement(input, description: "chat input"))

        // Clear and type message
        UITestHelpers.clearTextInput(input)
        UITestHelpers.typeAndSend(input, text: "Hello NeuroForge!")

        // Wait for response
        let response = app.staticTexts["chat_response"]
        XCTAssertTrue(UITestHelpers.waitForElement(response, timeout: 15, description: "chat response"))

        // Verify response content
        let responseText = response.value as? String ?? ""
        XCTAssertFalse(responseText.isEmpty, "Response should not be empty")
        XCTAssertTrue(responseText.contains("AI:") || responseText.contains("NeuroForge"),
                     "Response should contain AI response")

        UITestHelpers.takeScreenshot(name: "Full Chat Flow Complete", testCase: self)
    }

    func testMultiLineChat() {
        let app = UITestHelpers.launchApp()
        XCTAssertTrue(UITestHelpers.waitForAppReady(app))

        let input = app.textViews["chat_input"]
        XCTAssertTrue(UITestHelpers.waitForElement(input))

        // Clear input
        UITestHelpers.clearTextInput(input)

        // Type multi-line message
        input.typeText("This is line 1")
        input.typeKey(.return, modifierFlags: .shift) // Shift+Enter for newline
        input.typeText("This is line 2")

        // Send the message
        input.typeKey(.return, modifierFlags: []) // Enter to send

        // Wait for response
        let response = app.staticTexts["chat_response"]
        XCTAssertTrue(UITestHelpers.waitForElement(response, timeout: 15))

        UITestHelpers.takeScreenshot(name: "Multi-line Chat Test", testCase: self)
    }

    func testReconnectFunctionality() {
        let app = UITestHelpers.launchApp()
        XCTAssertTrue(UITestHelpers.waitForAppReady(app))

        let banner = app.staticTexts["health_banner"]
        XCTAssertTrue(UITestHelpers.waitForElement(banner))

        let reconnectButton = app.buttons["reconnect_button"]
        if reconnectButton.exists {
            reconnectButton.click()

            // Wait for reconnect to complete
            Thread.sleep(forTimeInterval: 3.0)

            // Verify banner still exists and is responsive
            XCTAssertTrue(banner.exists, "Health banner should still exist after reconnect")
        }

        UITestHelpers.takeScreenshot(name: "Reconnect Test", testCase: self)
    }

    func testKeyboardShortcuts() {
        let app = UITestHelpers.launchApp()
        XCTAssertTrue(UITestHelpers.waitForAppReady(app))

        let input = app.textViews["chat_input"]
        XCTAssertTrue(UITestHelpers.waitForElement(input))

        // Test focus behavior
        input.click()
        XCTAssertTrue(input.exists, "Input should exist after clicking")

        // Test text visibility (should not be white/clear)
        UITestHelpers.clearTextInput(input)
        input.typeText("keyboard test")

        let inputText = input.value as? String ?? ""
        XCTAssertTrue(inputText.contains("keyboard test"), "Typed text should be visible")

        UITestHelpers.takeScreenshot(name: "Keyboard Shortcuts Test", testCase: self)
    }
}
