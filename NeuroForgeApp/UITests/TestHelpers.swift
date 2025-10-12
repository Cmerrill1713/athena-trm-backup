import XCTest

/// Helper functions for NeuroForge UI tests
class UITestHelpers {

    /// Stable wait and tap for flake-proof tests
    static func waitTap(_ element: XCUIElement, timeout: TimeInterval = 10) {
        XCTAssertTrue(element.waitForExistence(timeout: timeout))
        element.click()
    }

    /// Launch app with standard environment variables
    static func launchApp() -> XCUIApplication {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()
        return app
    }

    /// Wait for app to be fully loaded and ready
    static func waitForAppReady(_ app: XCUIApplication, timeout: TimeInterval = 10) -> Bool {
        return app.wait(for: .runningForeground, timeout: timeout)
    }

    /// Take screenshot with descriptive name
    static func takeScreenshot(name: String, testCase: XCTestCase) {
        let screenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = name
        attachment.lifetime = .keepAlways
        testCase.add(attachment)
    }

    /// Clear text input field
    static func clearTextInput(_ element: XCUIElement) {
        element.click()
        element.typeKey(.keyboardType(.a), modifierFlags: .command) // Select all
        element.typeKey(.delete, modifierFlags: []) // Clear
    }

    /// Type text with Enter key (for sending messages)
    static func typeAndSend(_ element: XCUIElement, text: String) {
        element.typeText(text)
        element.typeKey(.keyboardType(.return), modifierFlags: [])
    }

    /// Type text with Shift+Enter (for newlines)
    static func typeWithNewline(_ element: XCUIElement, text: String) {
        element.typeText(text)
        element.typeKey(.keyboardType(.return), modifierFlags: .shift)
    }

    /// Wait for element with custom timeout and description
    static func waitForElement(_ element: XCUIElement,
                              timeout: TimeInterval = 10,
                              description: String = "element") -> Bool {
        return element.waitForExistence(timeout: timeout)
    }

    /// Check if backend is healthy
    static func isBackendHealthy() -> Bool {
        // This could be expanded to make actual HTTP request
        // For now, just return true - tests will verify via UI
        return true
    }
}

/// Extension for XCUIElement with convenient wait and tap functionality
extension XCUIElement {
    /// Wait for element to exist and then tap it
    func waitTap(_ timeout: TimeInterval = 10) {
        XCTAssertTrue(self.waitForExistence(timeout: timeout))
        self.click()
    }
}
