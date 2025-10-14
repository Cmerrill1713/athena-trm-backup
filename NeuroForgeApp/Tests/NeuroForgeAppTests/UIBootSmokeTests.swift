import XCTest
@testable import NeuroForgeApp

final class UIBootSmokeTests: XCTestCase {
    func test_canInstantiateDashboard() {
        // Compiles view graph; if any duplicate types or missing symbols, build will fail
        _ = AthenaDashboardView()
    }
    
    func test_canInstantiateInputCoordinator() {
        // Test that our focus coordinator can be created
        let coordinator = InputFocusCoordinator()
        XCTAssertNotNil(coordinator)
    }
    
    func test_canInstantiateChatInput() {
        // Test that our chat input can be created
        let coordinator = InputFocusCoordinator()
        let chatInput = ChatInputView { _ in }
        XCTAssertNotNil(chatInput)
    }
}
