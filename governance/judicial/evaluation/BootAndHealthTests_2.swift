import XCTest

final class BootAndHealthTests: XCTestCase {

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
    }

    override func tearDown() {
        super.tearDown()
    }

    func testBootAndHealthBanner() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        // Wait for app to fully load
        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        // Check for health banner
        let banner = app.staticTexts["health_banner"]
        XCTAssertTrue(banner.waitForExistence(timeout: 12), "health_banner missing - app may not have loaded properly")

        // Verify health banner content
        let bannerText = banner.value as? String ?? ""
        XCTAssertTrue(bannerText.contains("Connected") || bannerText.contains("Disconnected"),
                     "Health banner should show connection status")

        // Take screenshot for verification
        let screenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "App Launch with Health Banner"
        attachment.lifetime = .keepAlways
        add(attachment)

        // Verify app is responsive
        XCTAssertTrue(app.windows.count > 0, "App should have at least one window")
    }

    func testHealthBannerReconnect() {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        // Wait for health banner
        let banner = app.staticTexts["health_banner"]
        XCTAssertTrue(banner.waitForExistence(timeout: 10))

        // Find and click reconnect button
        let reconnectButton = app.buttons["Reconnect"]
        if reconnectButton.exists {
            reconnectButton.click()

            // Wait a moment for reconnect to process
            Thread.sleep(forTimeInterval: 2.0)

            // Verify banner still exists after reconnect
            XCTAssertTrue(banner.exists, "Health banner should still exist after reconnect")
        }
    }
}
