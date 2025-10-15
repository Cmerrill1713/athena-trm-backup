import Foundation
import SwiftUI

class LayoutManager: ObservableObject {
    @Published var inputHeight: CGFloat = 20
    @Published var inputMaxHeight: CGFloat = 60
    @Published var inputPadding: CGFloat = 8
    @Published var cornerRadius: CGFloat = 16
    @Published var buttonSize: CGFloat = 16
    @Published var spacing: CGFloat = 12
    @Published var horizontalPadding: CGFloat = 16
    @Published var verticalPadding: CGFloat = 12

    func updateLayout(from message: String) {
        let lowercased = message.lowercased()

        // Height adjustments
        if lowercased.contains("taller") || lowercased.contains("increase height") {
            self.inputHeight = min(self.inputHeight + 10, 80)
            self.inputMaxHeight = min(self.inputMaxHeight + 20, 160)
        } else if lowercased.contains("shorter") || lowercased.contains("decrease height") {
            self.inputHeight = max(self.inputHeight - 10, 15)
            self.inputMaxHeight = max(self.inputMaxHeight - 20, 30)
        }

        // Padding adjustments
        if lowercased.contains("more padding") || lowercased.contains("bigger padding") {
            self.inputPadding = min(self.inputPadding + 2, 16)
            self.horizontalPadding = min(self.horizontalPadding + 4, 24)
            self.verticalPadding = min(self.verticalPadding + 2, 16)
        } else if lowercased.contains("less padding") || lowercased.contains("smaller padding") {
            self.inputPadding = max(self.inputPadding - 2, 4)
            self.horizontalPadding = max(self.horizontalPadding - 4, 8)
            self.verticalPadding = max(self.verticalPadding - 2, 4)
        }

        // Corner radius adjustments
        if lowercased.contains("more rounded") || lowercased.contains("rounder") {
            self.cornerRadius = min(self.cornerRadius + 4, 24)
        } else if lowercased.contains("less rounded") || lowercased.contains("square") {
            self.cornerRadius = max(self.cornerRadius - 4, 4)
        }

        // Button size adjustments
        if lowercased.contains("bigger buttons") || lowercased.contains("larger buttons") {
            self.buttonSize = min(self.buttonSize + 2, 20)
        } else if lowercased.contains("smaller buttons") || lowercased.contains("tiny buttons") {
            self.buttonSize = max(self.buttonSize - 2, 12)
        }

        // Spacing adjustments
        if lowercased.contains("more spacing") || lowercased.contains("wider spacing") {
            self.spacing = min(self.spacing + 2, 20)
        } else if lowercased.contains("less spacing") || lowercased.contains("tighter spacing") {
            self.spacing = max(self.spacing - 2, 4)
        }

        print("🎨 Layout updated: height=\(self.inputHeight)-\(self.inputMaxHeight), padding=\(self.inputPadding), radius=\(self.cornerRadius)")
    }

    func resetToDefault() {
        self.inputHeight = 20
        self.inputMaxHeight = 60
        self.inputPadding = 8
        self.cornerRadius = 16
        self.buttonSize = 16
        self.spacing = 12
        self.horizontalPadding = 16
        self.verticalPadding = 12
        print("🎨 Layout reset to defaults")
    }

    func getLayoutInfo() -> String {
        """
        Current Layout Settings:
        • Input height: \(self.inputHeight)-\(self.inputMaxHeight)px
        • Padding: \(self.inputPadding)px
        • Corner radius: \(self.cornerRadius)px
        • Button size: \(self.buttonSize)px
        • Spacing: \(self.spacing)px
        • Horizontal padding: \(self.horizontalPadding)px
        • Vertical padding: \(self.verticalPadding)px
        """
    }
}
