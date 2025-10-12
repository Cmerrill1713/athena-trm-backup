import XCTest

final class PromptSidebarTests: XCTestCase {

    override func setUp() {
        continueAfterFailure = false
    }

    func testSidebarToggle_InsertTemplate() throws {
        let app = XCUIApplication()
        app.launchEnvironment["QA_MODE"] = "1"
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launch()

        // Toggle sidebar with ⌘⇧T
        app.typeKey("t", modifierFlags: [.command, .shift])

        let list = app.tables["prompt_list"]
        XCTAssertTrue(list.waitForExistence(timeout: 5), "Prompt list should appear after toggle")

        // Double-click first item to insert
        let first = list.cells.element(boundBy: 0)
        XCTAssertTrue(first.waitForExistence(timeout: 5), "First template should exist")
        first.doubleClick()

        // If variables sheet shows up, just hit Insert (return)
        let insertBtn = app.buttons["Insert"]
        if insertBtn.waitForExistence(timeout: 1) {
            insertBtn.click()
        }

        // Verify text was inserted into chat input
        let input = app.textViews["chat_input"]
        XCTAssertTrue(input.waitForExistence(timeout: 5), "Chat input should exist")

        let inputValue = (input.value as? String ?? "")
        XCTAssertFalse(inputValue.isEmpty, "Chat input should contain inserted template")
    }

    func testPromptSidebar_OnlyVisibleInQAMode() throws {
        let app = XCUIApplication()
        app.launchEnvironment["QA_MODE"] = "0"  // Production mode
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launch()

        // Try to toggle sidebar
        app.typeKey("t", modifierFlags: [.command, .shift])

        // Sidebar should not appear in production mode
        let sidebar = app.otherElements["prompt_sidebar"]
        sleep(1)

        XCTAssertFalse(sidebar.exists, "Prompt sidebar should be hidden in production mode")
    }

    func testPromptSearch_FiltersTemplates() throws {
        let app = XCUIApplication()
        app.launchEnvironment["QA_MODE"] = "1"
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launch()

        // Open sidebar
        app.typeKey("t", modifierFlags: [.command, .shift])

        let searchField = app.textFields["prompt_search"]
        XCTAssertTrue(searchField.waitForExistence(timeout: 5), "Search field should exist")

        // Type search query
        searchField.click()
        searchField.typeText("bug")

        // Should filter to Bug Report template
        let list = app.tables["prompt_list"]
        XCTAssertTrue(list.waitForExistence(timeout: 2), "Filtered list should appear")

        // At least one result should remain (Bug Report)
        let cellCount = list.cells.count
        XCTAssertGreaterThan(cellCount, 0, "Should find at least one template matching 'bug'")
    }
}
