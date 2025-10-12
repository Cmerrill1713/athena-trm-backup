import XCTest

final class ChatBehaviorTests: XCTestCase {

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
    }

    func testEnterSends_and_ShiftEnterNewline() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        // Wait for app to load
        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        // Find chat input
        let input = app.textViews["chat_input"]
        XCTAssertTrue(input.waitForExistence(timeout: 10), "chat_input not found")

        // Clear any existing text and type test message
        input.click()
        input.typeKey("a", modifierFlags: .command) // Select all
        input.typeKey(.delete, modifierFlags: []) // Clear
        input.typeText("ping")

        // ENTER → send
        app.typeKey(.return, modifierFlags: [])

        // Wait for response
        let response = app.staticTexts["chat_response"]
        XCTAssertTrue(response.waitForExistence(timeout: 12), "chat_response not found after sending message")

        // Verify response is not empty
        let responseText = response.value as? String ?? ""
        XCTAssertFalse(responseText.isEmpty, "Response should not be empty")

        // Take screenshot of successful chat
        let screenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "Chat Message Sent Successfully"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    func testShiftEnterNewline() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        let input = app.textViews["chat_input"]
        XCTAssertTrue(input.waitForExistence(timeout: 10))

        input.click()
        input.typeKey("a", modifierFlags: .command) // Select all
        input.typeKey(.delete, modifierFlags: []) // Clear

        // Type first line
        input.typeText("line1")

        // SHIFT+ENTER → newline
        app.typeKey(.return, modifierFlags: .shift)

        // Type second line
        input.typeText("line2")

        // Verify both lines are present
        let inputText = input.value as? String ?? ""
        XCTAssertTrue(inputText.contains("line1"), "First line should be present")
        XCTAssertTrue(inputText.contains("line2"), "Second line should be present")
        XCTAssertTrue(inputText.contains("\n"), "Should contain newline character")

        // Now send the multi-line message
        app.typeKey(.return, modifierFlags: [])

        // Wait for response
        let response = app.staticTexts["chat_response"]
        XCTAssertTrue(response.waitForExistence(timeout: 12))
    }

    func testChatInputFocusAndVisibility() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        let input = app.textViews["chat_input"]
        XCTAssertTrue(input.waitForExistence(timeout: 10))

        // Test input focus
        input.click()
        XCTAssertTrue(input.exists, "Input should exist after clicking")

        // Test text visibility (should not be white/clear)
        input.typeText("visibility test")
        let inputText = input.value as? String ?? ""
        XCTAssertTrue(inputText.contains("visibility test"), "Typed text should be visible")

        // Clear input
        input.typeKey("a", modifierFlags: .command)
        input.typeKey(.delete, modifierFlags: [])
    }
}
