import SwiftUI

/// Apple native spacing system (8pt grid)
enum AppleSpacing {
    static let xs: CGFloat = 4 // 4pt
    static let sm: CGFloat = 8 // 8pt
    static let md: CGFloat = 16 // 16pt
    static let lg: CGFloat = 24 // 24pt
    static let xl: CGFloat = 32 // 32pt
    static let xxl: CGFloat = 40 // 40pt

    // MARK: - Chat Specific

    enum Chat {
        static let bubblePadding: CGFloat = 16
        static let messageSpacing: CGFloat = 16
        static let inputPadding: CGFloat = 12
        static let sidebarWidth: CGFloat = 280
    }
}
