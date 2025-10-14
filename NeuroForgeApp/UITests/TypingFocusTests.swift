import XCTest

/// UI tests to ensure pop-outs don't steal keyboard focus from main input
final class TypingFocusTests: XCTestCase {
    
    override func setUpWithError() throws {
        continueAfterFailure = false
    }
    
    func testMainInputAcceptsTypingAfterPopouts() throws {
        let app = XCUIApplication()
        app.launchEnvironment["POPUPS_ENABLED"] = "1"
        app.launchEnvironment["AUTOEXEC_GUARD"] = "1"
        app.launch()
        
        // Wait for app to be ready
        sleep(2)
        
        // Find the main input (ChatComposer uses chat_input identifier)
        let input = app.textFields["chat_input"].firstMatch
        XCTAssertTrue(input.waitForExistence(timeout: 5), "Main chat input not found")
        
        // Click and type initial text
        input.click()
        input.typeText("hello")
        
        // Verify typing worked
        let value = input.value as? String ?? ""
        XCTAssertTrue(value.contains("hello"), "Initial typing failed: got '\(value)'")
        
        // Note: To fully test pop-outs, you'd need to:
        // 1. Fire a backend event (or trigger via menu command)
        // 2. Wait for pop-out window to appear
        // 3. Try typing again in main input
        // 4. Verify input still accepts text
        
        // For now, this tests basic input functionality
        // Add pop-out triggers when backend integration is complete
    }
    
    func testRefocusShortcutWorks() throws {
        let app = XCUIApplication()
        app.launch()
        
        sleep(2)
        
        // Find main input
        let input = app.textFields["chat_input"].firstMatch
        XCTAssertTrue(input.waitForExistence(timeout: 5), "Main chat input not found")
        
        // Type something
        input.click()
        input.typeText("test")
        
        // Simulate focus loss (click elsewhere)
        let window = app.windows.firstMatch
        window.click()
        
        // Use refocus shortcut (Cmd+Shift+L)
        app.typeKey("l", modifierFlags: [.command, .shift])
        
        // Verify we can type again
        input.typeText(" refocused")
        
        let value = input.value as? String ?? ""
        XCTAssertTrue(value.contains("refocused"), "Refocus shortcut didn't work")
    }
    
    func testInputRetainsFocusOnAppActivation() throws {
        let app = XCUIApplication()
        app.launch()
        
        sleep(2)
        
        // Find and focus main input
        let input = app.textFields["chat_input"].firstMatch
        XCTAssertTrue(input.waitForExistence(timeout: 5), "Main chat input not found")
        
        input.click()
        input.typeText("before")
        
        // Simulate app deactivation/reactivation
        // (In real scenario, this would test the didBecomeActiveNotification handler)
        NSRunningApplication.current.activate(options: [.activateIgnoringOtherApps])
        
        sleep(0.5)
        
        // Should still be able to type
        input.typeText(" after")
        
        let value = input.value as? String ?? ""
        XCTAssertTrue(value.contains("before after"), "Focus lost on app activation")
    }
}

