import SwiftUI
import OSLog

/// Stable input view model - survives parent re-renders
@MainActor
public final class ChatInputVM: ObservableObject {
    @Published public var text: String = ""
    @Published public var isSending: Bool = false
    
    // UI logging
    private let uiLog = Logger(subsystem: "com.neuroforge.athena", category: "ui")
    
    // External handler provided by parent
    public var onSend: ((String) async -> Void)?
    
    public init() {}
    
    public func submit() {
        let msg = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !msg.isEmpty, !isSending else { return }
        
        uiLog.info("Send tapped; len=\(msg.count)")
        isSending = true
        
        Task {
            await onSend?(msg)
            await MainActor.run {
                self.text = ""
                self.isSending = false
                self.uiLog.info("Send complete; field ready for next input")
            }
        }
    }
}

