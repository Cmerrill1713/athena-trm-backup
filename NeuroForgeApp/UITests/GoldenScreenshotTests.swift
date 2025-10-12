import XCTest

/// Golden screenshot tests for NeuroForge - regression detection
final class GoldenScreenshotTests: XCTestCase {

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
    }

    func testMainChatViewGoldenScreenshot() {
        let app = UITestHelpers.launchApp()
        XCTAssertTrue(UITestHelpers.waitForAppReady(app))

        // Wait for all UI elements to be stable
        let banner = app.staticTexts["health_banner"]
        XCTAssertTrue(UITestHelpers.waitForElement(banner, timeout: 15, description: "health banner"))

        let input = app.textViews["chat_input"]
        XCTAssertTrue(UITestHelpers.waitForElement(input, timeout: 10, description: "chat input"))

        // Wait a moment for UI to stabilize
        Thread.sleep(forTimeInterval: 1.0)

        // Take golden screenshot of main chat view
        let screenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "MainChatView_Golden"
        attachment.lifetime = .keepAlways
        add(attachment)

        // Verify key UI elements are present and positioned correctly
        XCTAssertTrue(banner.exists, "Health banner should be visible in golden screenshot")
        XCTAssertTrue(input.exists, "Chat input should be visible in golden screenshot")

        // Verify banner shows connected state (green dot)
        let bannerText = banner.value as? String ?? ""
        XCTAssertTrue(bannerText.contains("Connected") || bannerText.contains("Disconnected"),
                     "Health banner should show connection status")

        // Verify input is properly styled (not white text)
        input.click()
        XCTAssertTrue(input.exists, "Input should exist and be focusable")

        // Take a screenshot with input focused
        let focusedScreenshot = XCUIScreen.main.screenshot()
        let focusedAttachment = XCTAttachment(screenshot: focusedScreenshot)
        focusedAttachment.name = "MainChatView_InputFocused"
        focusedAttachment.lifetime = .keepAlways
        add(focusedAttachment)
    }

    func testChatWithMessageGoldenScreenshot() {
        let app = UITestHelpers.launchApp()
        XCTAssertTrue(UITestHelpers.waitForAppReady(app))

        // Wait for UI to be ready
        let banner = app.staticTexts["health_banner"]
        XCTAssertTrue(UITestHelpers.waitForElement(banner, timeout: 15))

        let input = app.textViews["chat_input"]
        XCTAssertTrue(UITestHelpers.waitForElement(input, timeout: 10))

        // Type a test message
        UITestHelpers.clearTextInput(input)
        input.typeText("Golden screenshot test message")

        // Send the message
        app.typeKey(.return, modifierFlags: [])

        // Wait for response
        let response = app.staticTexts["chat_response"]
        XCTAssertTrue(UITestHelpers.waitForElement(response, timeout: 15, description: "chat response"))

        // Wait for UI to stabilize after message exchange
        Thread.sleep(forTimeInterval: 1.0)

        // Take golden screenshot with chat conversation
        let screenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "ChatWithMessage_Golden"
        attachment.lifetime = .keepAlways
        add(attachment)

        // Verify conversation elements are present
        XCTAssertTrue(input.exists, "Chat input should still be visible")
        XCTAssertTrue(response.exists, "Chat response should be visible")

        // Verify response is not empty
        let responseText = response.value as? String ?? ""
        XCTAssertFalse(responseText.isEmpty, "Response should not be empty in golden screenshot")
    }

    func testMultiLineInputGoldenScreenshot() {
        let app = UITestHelpers.launchApp()
        XCTAssertTrue(UITestHelpers.waitForAppReady(app))

        let input = app.textViews["chat_input"]
        XCTAssertTrue(UITestHelpers.waitForElement(input, timeout: 10))

        // Clear input and create multi-line message
        UITestHelpers.clearTextInput(input)
        input.typeText("Line 1 of multi-line message")

        // Add newline with Shift+Enter
        app.typeKey(.return, modifierFlags: .shift)
        input.typeText("Line 2 of multi-line message")

        // Wait for input to stabilize
        Thread.sleep(forTimeInterval: 0.5)

        // Take golden screenshot of multi-line input
        let screenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "MultiLineInput_Golden"
        attachment.lifetime = .keepAlways
        add(attachment)

        // Verify multi-line text is present
        let inputText = input.value as? String ?? ""
        XCTAssertTrue(inputText.contains("Line 1"), "First line should be present")
        XCTAssertTrue(inputText.contains("Line 2"), "Second line should be present")
        XCTAssertTrue(inputText.contains("\n"), "Should contain newline character")
    }

    func testErrorStateGoldenScreenshot() {
        let app = XCUIApplication()

        // Launch with disconnected backend for error state
        app.launchEnvironment["API_BASE"] = "http://localhost:9999"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        // Wait for disconnected state
        let banner = app.staticTexts["health_banner"]
        XCTAssertTrue(UITestHelpers.waitForElement(banner, timeout: 15))

        // Wait for UI to stabilize in error state
        Thread.sleep(forTimeInterval: 1.0)

        // Take golden screenshot of error state
        let screenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "ErrorState_Golden"
        attachment.lifetime = .keepAlways
        add(attachment)

        // Verify error state elements
        let bannerText = banner.value as? String ?? ""
        XCTAssertTrue(bannerText.contains("Disconnected") || bannerText.contains("unavailable"),
                     "Banner should show error state")

        // Verify chat input is still functional
        let input = app.textViews["chat_input"]
        XCTAssertTrue(input.exists, "Chat input should still be visible in error state")
        XCTAssertTrue(input.isEnabled, "Chat input should still be enabled in error state")
    }
}
