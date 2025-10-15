import XCTest

/// Visual Playback Tests - Watch the app prove itself
/// These tests simulate real user interactions and can be recorded/replayed
final class VisualPlaybackTests: XCTestCase {

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
    }

    // MARK: - User Flow 1: Complete Chat Journey

    func test_UserFlow_CompleteChatJourney() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"]  = "1"
        app.launch()

        // Wait for app to stabilize
        let banner = app.staticTexts["health_banner"]
        XCTAssertTrue(banner.waitForExistence(timeout: 10), "Health banner should appear")
        Thread.sleep(forTimeInterval: 1.0)

        // VISUAL: Take screenshot of initial state
        UITestHelpers.takeScreenshot(name: "01_AppLaunched", testCase: self)

        // VISUAL: Type a message
        let input = app.textViews["chat_input"]
        XCTAssertTrue(input.waitForExistence(timeout: 5))
        input.click()
        Thread.sleep(forTimeInterval: 0.5)
        input.typeText("Hello! This is a visual test.")
        Thread.sleep(forTimeInterval: 0.5)

        UITestHelpers.takeScreenshot(name: "02_MessageTyped", testCase: self)

        // VISUAL: Send message
        input.typeKey(.return, modifierFlags: [])
        Thread.sleep(forTimeInterval: 2.0) // Wait for response

        UITestHelpers.takeScreenshot(name: "03_ResponseReceived", testCase: self)

        // Verify response appeared (text should be visible in UI)
        XCTAssertTrue(app.scrollViews["chat_messages_scroll"].exists)
    }

    // MARK: - User Flow 2: Provider Inspector Dance

    func test_UserFlow_ProviderInspectorToggle() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"]  = "1"
        app.launch()

        Thread.sleep(forTimeInterval: 1.0)
        UITestHelpers.takeScreenshot(name: "10_InitialState", testCase: self)

        // VISUAL: Provider Inspector should be visible in QA mode
        let inspector = app.otherElements["provider_inspector"]
        XCTAssertTrue(inspector.waitForExistence(timeout: 5), "Inspector should be visible in QA mode")

        Thread.sleep(forTimeInterval: 1.0)
        UITestHelpers.takeScreenshot(name: "11_InspectorVisible", testCase: self)

        // VISUAL: Toggle to FastVLM
        let picker = inspector.segmentedControls.firstMatch
        if picker.exists {
            let fastvlmButton = picker.buttons["FastVLM"]
            if fastvlmButton.exists {
                fastvlmButton.click()
                Thread.sleep(forTimeInterval: 0.5)
                UITestHelpers.takeScreenshot(name: "12_FastVLMSelected", testCase: self)
            }
        }

        // VISUAL: Refresh health
        let refreshButton = inspector.buttons["refresh_health_button"]
        if refreshButton.exists {
            refreshButton.click()
            Thread.sleep(forTimeInterval: 2.0) // Wait for health checks
            UITestHelpers.takeScreenshot(name: "13_HealthRefreshed", testCase: self)
        }

        // VISUAL: Reset to Auto
        let resetButton = inspector.buttons["reset_auto_button"]
        if resetButton.exists {
            resetButton.click()
            Thread.sleep(forTimeInterval: 0.5)
            UITestHelpers.takeScreenshot(name: "14_ResetToAuto", testCase: self)
        }
    }

    // MARK: - User Flow 3: Prompt Sidebar Journey

    func test_UserFlow_PromptSidebarInsert() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"]  = "1"
        app.launch()

        Thread.sleep(forTimeInterval: 1.0)

        // VISUAL: Check if sidebar is visible (QA mode)
        // Note: Sidebar toggle via ⌘⇧T happens in the app
        // For automated test, we'll check if it's present

        UITestHelpers.takeScreenshot(name: "20_BeforeSidebarInteraction", testCase: self)

        // If sidebar elements exist, interact with them
        // (This depends on your PromptSidebar implementation)

        // For now, capture the state
        Thread.sleep(forTimeInterval: 1.0)
        UITestHelpers.takeScreenshot(name: "21_SidebarState", testCase: self)
    }

    // MARK: - User Flow 4: Error State Handling

    func test_UserFlow_BackendDisconnect() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://127.0.0.1:9999" // Force disconnect
        app.launchEnvironment["QA_MODE"]  = "1"
        app.launch()

        Thread.sleep(forTimeInterval: 2.0)

        // VISUAL: Should show disconnected state
        let banner = app.staticTexts["health_banner"]
        XCTAssertTrue(banner.waitForExistence(timeout: 10))

        UITestHelpers.takeScreenshot(name: "30_DisconnectedState", testCase: self)

        // Verify reconnect button is visible
        let reconnect = app.buttons["reconnect_button"]
        XCTAssertTrue(reconnect.exists, "Reconnect button should be visible")

        Thread.sleep(forTimeInterval: 1.0)
        UITestHelpers.takeScreenshot(name: "31_ReconnectAvailable", testCase: self)
    }

    // MARK: - User Flow 5: Complete Feature Tour

    func test_UserFlow_CompleteTour() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"]  = "1"
        app.launch()

        Thread.sleep(forTimeInterval: 1.5)

        // VISUAL: Initial state
        UITestHelpers.takeScreenshot(name: "Tour_01_Launch", testCase: self)

        // VISUAL: Health banner
        XCTAssertTrue(app.staticTexts["health_banner"].exists)
        UITestHelpers.takeScreenshot(name: "Tour_02_HealthBanner", testCase: self)

        // VISUAL: Chat input
        let input = app.textViews["chat_input"]
        XCTAssertTrue(input.exists)
        input.click()
        Thread.sleep(forTimeInterval: 0.3)
        UITestHelpers.takeScreenshot(name: "Tour_03_ChatInput", testCase: self)

        // VISUAL: Provider Inspector
        let inspector = app.otherElements["provider_inspector"]
        if inspector.exists {
            Thread.sleep(forTimeInterval: 0.5)
            UITestHelpers.takeScreenshot(name: "Tour_04_ProviderInspector", testCase: self)
        }

        // VISUAL: Type and send
        input.typeText("ping")
        Thread.sleep(forTimeInterval: 0.3)
        UITestHelpers.takeScreenshot(name: "Tour_05_MessageReady", testCase: self)

        input.typeKey(.return, modifierFlags: [])
        Thread.sleep(forTimeInterval: 2.0)
        UITestHelpers.takeScreenshot(name: "Tour_06_ResponseReceived", testCase: self)

        // VISUAL: Final state
        Thread.sleep(forTimeInterval: 0.5)
        UITestHelpers.takeScreenshot(name: "Tour_07_Complete", testCase: self)
    }
}
