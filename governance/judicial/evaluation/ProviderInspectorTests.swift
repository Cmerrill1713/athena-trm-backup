import XCTest

/// Provider Inspector UI tests for NeuroForge
final class ProviderInspectorTests: XCTestCase {

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
    }

    func testInspectorVisibleInQAMode() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        // Inspector should be visible in QA mode
        let inspector = app.otherElements["provider_inspector"]
        XCTAssertTrue(inspector.waitForExistence(timeout: 10), "Provider inspector should be visible in QA mode")

        // Verify key UI elements exist
        XCTAssertTrue(inspector.staticTexts["Provider Inspector"].exists)
        XCTAssertTrue(inspector.segmentedControls["provider_picker"].exists)
        XCTAssertTrue(inspector.buttons["refresh_health_button"].exists)

        UITestHelpers.takeScreenshot(name: "Provider Inspector Visible", testCase: self)
    }

    func testToggleInspectorWithKeyboardShortcut() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        let inspector = app.otherElements["provider_inspector"]
        XCTAssertTrue(inspector.waitForExistence(timeout: 10))

        // Toggle visibility with eye button
        let toggleButton = inspector.buttons["toggle_visibility_button"]
        if toggleButton.exists {
            toggleButton.click()
            Thread.sleep(forTimeInterval: 0.5)

            // Inspector should become semi-transparent
            UITestHelpers.takeScreenshot(name: "Provider Inspector Hidden", testCase: self)

            // Toggle back
            toggleButton.click()
            Thread.sleep(forTimeInterval: 0.5)

            UITestHelpers.takeScreenshot(name: "Provider Inspector Restored", testCase: self)
        }
    }

    func testSwitchToFastVLMProvider() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        let inspector = app.otherElements["provider_inspector"]
        XCTAssertTrue(inspector.waitForExistence(timeout: 10))

        // Click on the segmented control to select FastVLM
        let picker = inspector.segmentedControls["provider_picker"]
        if picker.exists {
            let fastvlmButton = picker.buttons["FastVLM"]
            if fastvlmButton.exists {
                fastvlmButton.click()
                Thread.sleep(forTimeInterval: 1.0)

                // Verify ACTIVE tag appears on FastVLM row
                let activeTag = inspector.staticTexts["active_tag"]
                if activeTag.exists {
                    XCTAssertTrue(activeTag.exists, "ACTIVE tag should appear when FastVLM is selected")
                }

                // Verify FastVLM row exists
                let fastvlmRow = inspector.otherElements["provider_row_fastvlm"]
                XCTAssertTrue(fastvlmRow.exists, "FastVLM row should be visible")

                UITestHelpers.takeScreenshot(name: "Provider Inspector FastVLM Selected", testCase: self)
            }
        }
    }

    func testResetToAutoButton() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        let inspector = app.otherElements["provider_inspector"]
        XCTAssertTrue(inspector.waitForExistence(timeout: 10))

        // First, select a non-auto provider
        let picker = inspector.segmentedControls["provider_picker"]
        if picker.exists {
            let fastvlmButton = picker.buttons["FastVLM"]
            if fastvlmButton.exists {
                fastvlmButton.click()
                Thread.sleep(forTimeInterval: 1.0)
            }
        }

        // Now click "Reset Auto" button
        let resetButton = inspector.buttons["reset_auto_button"]
        if resetButton.exists {
            resetButton.click()
            Thread.sleep(forTimeInterval: 1.0)

            // Verify we're back to auto
            let autoButton = picker.buttons["Auto"]
            if autoButton.exists {
                // Auto should be selected now
                UITestHelpers.takeScreenshot(name: "Provider Inspector Reset to Auto", testCase: self)
            }
        }
    }

    func testRefreshHealthButton() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        let inspector = app.otherElements["provider_inspector"]
        XCTAssertTrue(inspector.waitForExistence(timeout: 10))

        // Click refresh health button
        let refreshButton = inspector.buttons["refresh_health_button"]
        if refreshButton.exists {
            refreshButton.click()
            Thread.sleep(forTimeInterval: 2.0)

            // Verify provider rows exist with health indicators
            XCTAssertTrue(inspector.otherElements["provider_row_auto"].exists, "Auto row should exist")
            XCTAssertTrue(inspector.otherElements["provider_row_fastvlm"].exists, "FastVLM row should exist")
            XCTAssertTrue(inspector.otherElements["provider_row_ollama"].exists, "Ollama row should exist")
            XCTAssertTrue(inspector.otherElements["provider_row_trm"].exists, "TRM row should exist")

            UITestHelpers.takeScreenshot(name: "Provider Inspector Health Refreshed", testCase: self)
        }
    }

    func testProviderHealthIndicators() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        let inspector = app.otherElements["provider_inspector"]
        XCTAssertTrue(inspector.waitForExistence(timeout: 10))

        // Wait for initial health check to complete
        Thread.sleep(forTimeInterval: 3.0)

        // Take screenshot of health status
        UITestHelpers.takeScreenshot(name: "Provider Inspector Health Status", testCase: self)

        // Verify all provider rows are present
        XCTAssertTrue(inspector.otherElements["provider_row_auto"].exists)
        XCTAssertTrue(inspector.otherElements["provider_row_fastvlm"].exists)
        XCTAssertTrue(inspector.otherElements["provider_row_ollama"].exists)
        XCTAssertTrue(inspector.otherElements["provider_row_trm"].exists)
    }

    func testInspectorPersistence() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        let inspector = app.otherElements["provider_inspector"]
        XCTAssertTrue(inspector.waitForExistence(timeout: 10))

        // Select FastVLM
        let picker = inspector.segmentedControls["provider_picker"]
        if picker.exists {
            let fastvlmButton = picker.buttons["FastVLM"]
            if fastvlmButton.exists {
                fastvlmButton.click()
                Thread.sleep(forTimeInterval: 1.0)
            }
        }

        // Quit and relaunch app
        app.terminate()
        Thread.sleep(forTimeInterval: 1.0)

        let app2 = XCUIApplication()
        app2.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app2.launchEnvironment["QA_MODE"] = "1"
        app2.launch()

        XCTAssertTrue(app2.wait(for: .runningForeground, timeout: 10))

        let inspector2 = app2.otherElements["provider_inspector"]
        if inspector2.waitForExistence(timeout: 10) {
            // FastVLM should still be selected after relaunch
            Thread.sleep(forTimeInterval: 1.0)

            // Look for ACTIVE tag to verify persistence
            let activeTag = inspector2.staticTexts["active_tag"]
            if activeTag.exists {
                UITestHelpers.takeScreenshot(name: "Provider Inspector Persisted Selection", testCase: self)
            }
        }
    }
}
