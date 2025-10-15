import Foundation
import Combine
import SwiftUI

// Minimal fallback VoiceManager for builds when full Voice module isn't compiled into the target.
final class VoiceManager: ObservableObject {
    enum State: Equatable {
        case idle
        case requestingPermission
        case listening
        case transcribing(String)
        case sending(String)
        case speaking
        case error(String)
    }

    @Published var state: State = .idle
    @Published var level: CGFloat = 0
    @Published var transcript: String = ""

    var ttsEnabled: Bool = true

    init() {}

    func ensurePermissions() async -> Bool { true }

    func startListening() async {
        // minimal simulation
        await MainActor.run { self.state = .listening }
    }

    func finishListening() {
        Task { @MainActor in self.state = .idle }
    }

    func cancel() {
        Task { @MainActor in self.state = .idle }
    }

    func speak(_ text: String) {
        // no-op fallback
        Task { @MainActor in self.state = .speaking }
        Task { @MainActor in self.state = .idle }
    }
}
