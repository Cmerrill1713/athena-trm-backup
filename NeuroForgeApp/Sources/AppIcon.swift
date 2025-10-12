import SwiftUI
import AppKit

/// Helper to set the app icon programmatically
struct AppIcon {
    static func setIcon() {
        // Get the main bundle
        let bundle = Bundle.main

        // Try to find the icon file
        let iconName = "AppIcon"
        let iconExtensions = ["icns", "png"]

        for ext in iconExtensions {
            if let iconPath = bundle.path(forResource: iconName, ofType: ext) {
                let iconURL = URL(fileURLWithPath: iconPath)

                // Set the icon for the current app
                NSWorkspace.shared.setIcon(nil, forFile: iconURL.path, options: [])

                print("✅ Set app icon: \(iconPath)")
                return
            }
        }

        print("⚠️ App icon not found, using system default")
    }
}
