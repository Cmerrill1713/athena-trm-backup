import XCTest

final class RAGTests: XCTestCase {

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
    }

    func testRAGIngestAndSearch_ifPresent() throws {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        // Check if RAG UI elements are present
        let ingestButton = app.buttons["ingest_button"]
        let searchInput = app.textFields["rag_search_input"]

        // Skip test if RAG UI is not present
        guard ingestButton.exists && searchInput.exists else {
            throw XCTSkip("RAG UI not present - skipping RAG tests")
        }

        // Test ingest functionality
        if ingestButton.isEnabled {
            ingestButton.click()

            // Wait for any ingest UI to appear (file picker, etc.)
            Thread.sleep(forTimeInterval: 1.0)

            // Take screenshot of ingest UI
            let ingestScreenshot = XCUIScreen.main.screenshot()
            let ingestAttachment = XCTAttachment(screenshot: ingestScreenshot)
            ingestAttachment.name = "RAG Ingest UI"
            ingestAttachment.lifetime = .keepAlways
            add(ingestAttachment)
        }

        // Test search functionality
        searchInput.click()
        searchInput.typeText("What is NeuroForge?")

        // Press Enter to search
        app.typeKey(.return, modifierFlags: [])

        // Wait for results
        let resultsList = app.tables["rag_results_list"]
        XCTAssertTrue(resultsList.waitForExistence(timeout: 12),
                     "RAG results list should appear after search")

        // Verify results are not empty
        XCTAssertTrue(resultsList.cells.count > 0, "RAG search should return results")

        // Take screenshot of search results
        let resultsScreenshot = XCUIScreen.main.screenshot()
        let resultsAttachment = XCTAttachment(screenshot: resultsScreenshot)
        resultsAttachment.name = "RAG Search Results"
        resultsAttachment.lifetime = .keepAlways
        add(resultsAttachment)
    }

    func testRAGSearchInputFocus() throws {
        let app = XCUIApplication()
        app.launchEnvironment["API_BASE"] = "http://localhost:8014"
        app.launchEnvironment["QA_MODE"] = "1"
        app.launch()

        XCTAssertTrue(app.wait(for: .runningForeground, timeout: 10))

        let searchInput = app.textFields["rag_search_input"]

        // Skip if RAG UI not present
        guard searchInput.exists else {
            throw XCTSkip("RAG search input not present")
        }

        // Test input focus and text visibility
        searchInput.click()
        XCTAssertTrue(searchInput.hasFocus, "RAG search input should have focus")

        searchInput.typeText("test query")
        let inputText = searchInput.value as? String ?? ""
        XCTAssertTrue(inputText.contains("test query"), "Typed text should be visible in RAG search")
    }
}
