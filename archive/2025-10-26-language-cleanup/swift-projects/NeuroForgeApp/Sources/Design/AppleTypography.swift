import SwiftUI

/// Apple native typography scale following HIG
enum AppleTypography {
    static let largeTitle = Font.largeTitle
    static let title = Font.title
    static let title2 = Font.title2
    static let title3 = Font.title3
    static let headline = Font.headline
    static let body = Font.body
    static let callout = Font.callout
    static let subheadline = Font.subheadline
    static let footnote = Font.footnote
    static let caption = Font.caption
    static let caption2 = Font.caption2

    // MARK: - Chat Specific

    enum Chat {
        static let message = Font.system(size: 15, weight: .regular)
        static let timestamp = Font.system(size: 12, weight: .regular)
        static let name = Font.system(size: 14, weight: .medium)
        static let input = Font.system(size: 15, weight: .regular)
    }
}
