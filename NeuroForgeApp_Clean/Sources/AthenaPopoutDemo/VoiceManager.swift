import Foundation

@MainActor
final class VoiceManager {
    func speak(_ text: String) {
        // no-op stub; wire to AVSpeechSynthesizer later if needed
        NSLog("[VoiceManager] \(text)")
    }
}
