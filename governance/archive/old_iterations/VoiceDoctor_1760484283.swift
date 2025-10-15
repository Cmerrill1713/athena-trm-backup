import AVFoundation
import AppKit

enum VoiceDoctor {
    static let preferred = "Samantha"
    static let locale = "en-US"

    static func run() {
        let voices = AVSpeechSynthesisVoice.speechVoices()
        print("🔎 Installed voices (\(voices.count)):")
        
        // Print all voices (useful for debugging)
        for v in voices {
            print("   • \(v.name) [\(v.identifier)] \(v.language) q=\(v.quality.rawValue)")
        }

        if let match = voices.first(where: { $0.name == preferred }) {
            print("✅ Found \(preferred): \(match.identifier) \(match.language) q=\(match.quality.rawValue)")
        } else {
            print("❌ \(preferred) missing — install Enhanced pack.")
            DispatchQueue.main.async {
                let a = NSAlert()
                a.alertStyle = .warning
                a.messageText = "Athena voice missing"
                a.informativeText = "Install \(preferred) (Enhanced) in System Settings → Accessibility → Spoken Content → Voices."
                a.addButton(withTitle: "OK")
                a.runModal()
            }
        }
    }
}

