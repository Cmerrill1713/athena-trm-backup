import SwiftUI

@main
struct NeuroForgeApp: App {

    init() {
        // Set the app icon
        AppIcon.setIcon()
    }

    var body: some Scene {
        WindowGroup {
            ChatView() // uses HealthBanner + model-agnostic routing
        }
        .windowStyle(.hiddenTitleBar)
    }
}
