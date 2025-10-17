import SnapshotTesting
import SwiftUI
import XCTest

@testable import NeuroForgeApp

final class PromptViewSnapshotTests: XCTestCase {

    func testChatInputBarEmpty() {
        let view = ChatInputBar(
            text: .constant(""),
            onSend: { _ in },
            isSending: false
        )

        assertSnapshot(view, named: "chat-input-empty")
    }

    func testChatInputBarWithText() {
        let view = ChatInputBar(
            text: .constant("Hello, this is a test message"),
            onSend: { _ in },
            isSending: false
        )

        assertSnapshot(view, named: "chat-input-with-text")
    }

    func testChatInputBarSending() {
        let view = ChatInputBar(
            text: .constant("Sending this message..."),
            onSend: { _ in },
            isSending: true
        )

        assertSnapshot(view, named: "chat-input-sending")
    }

    func testChatInputBarFocused() {
        let view = ChatInputBar(
            text: .constant("Focused input field"),
            onSend: { _ in },
            isSending: false
        )
        // Note: Focus state can't be directly tested in snapshots
        // This tests the visual appearance without focus

        assertSnapshot(view, named: "chat-input-focused")
    }

    func testDesignTokens() {
        let view = VStack(spacing: NFToken.Spacing.lg) {
            NFCard {
                Text("Test Card")
                    .font(NFToken.Typography.title)
                Text("This is card content with design tokens.")
                    .font(NFToken.Typography.body)
            }

            HStack(spacing: NFToken.Spacing.md) {
                NFButton("Primary", style: .primary) {}
                NFButton("Secondary", style: .secondary) {}
                NFButton("Disabled", isEnabled: false) {}
            }

            NFStatusIndicator(status: .success, message: "Operation successful")
            NFStatusIndicator(status: .warning, message: "Check configuration")
            NFStatusIndicator(status: .error, message: "Connection failed")
        }
        .padding(NFToken.Spacing.xl)
        .background(NFToken.Color.background)
        .frame(width: 400, height: 300)

        assertSnapshot(view, named: "design-tokens")
    }
}

// MARK: - Snapshot Testing Helper

extension XCTestCase {
    func assertSnapshot<V: View>(
        _ view: V,
        named name: String,
        file: StaticString = #file,
        line: UInt = #line
    ) {
        let hostingController = UIHostingController(rootView: view)
        hostingController.view.frame = CGRect(x: 0, y: 0, width: 375, height: 667)

        // For macOS, we need to use NSView
        #if os(macOS)
            let view = NSHostingView(rootView: view)
            view.frame = CGRect(x: 0, y: 0, width: 800, height: 600)
            assertSnapshot(
                matching: view,
                as: .image,
                named: name,
                file: file,
                line: line
            )
        #else
            assertSnapshot(
                matching: hostingController,
                as: .image,
                named: name,
                file: file,
                line: line
            )
        #endif
    }
}
