import Foundation
import AVFoundation
import AppKit

// MARK: - Preferred Voice Configuration

enum PreferredVoice {
    static let name = "Samantha"             // primary voice
    static let fallbacks = [                 // optional alternates
        "com.apple.voice.premium.en-US.Samantha",
        "com.apple.voice.compact.en-US.Samantha",
        "com.apple.ttsbundle.Samantha-compact"
    ]
}

// MARK: - Voice Sentinel (Hard-lock + Mismatch Detection)

final class VoiceSentinel: NSObject, AVSpeechSynthesizerDelegate {
    static let shared = VoiceSentinel()
    private let synth = AVSpeechSynthesizer()
    private(set) var locked: AVSpeechSynthesisVoice?

    override init() {
        super.init()
        synth.delegate = self
        resolveVoice()
    }

    func resolveVoice() {
        let voices = AVSpeechSynthesisVoice.speechVoices()
        
        // Try exact name match first (highest quality)
        if let byName = voices
            .filter({ $0.name == PreferredVoice.name })
            .sorted(by: { $0.quality.rawValue > $1.quality.rawValue })
            .first {
            locked = byName
            print("🔊 Locked voice by name: \(byName.name) [\(byName.identifier)] \(byName.language) q=\(byName.quality.rawValue)")
            return
        }
        
        // Try known identifiers
        for id in PreferredVoice.fallbacks {
            if let v = AVSpeechSynthesisVoice(identifier: id) {
                locked = v
                print("🔊 Locked voice by id: \(v.name) [\(v.identifier)]")
                return
            }
        }
        
        // Hard stop - no fallback
        locked = nil
        print("❌ \(PreferredVoice.name) not available — will not speak.")
    }

    func speak(_ text: String,
               rate: Float = AVSpeechUtteranceDefaultSpeechRate * 0.92,
               pitch: Float = 1.05,
               volume: Float = 0.88) {
        guard let v = locked else {
            NSSound.beep()
            DispatchQueue.main.async {
                let a = NSAlert()
                a.alertStyle = .critical
                a.messageText = "Athena voice missing"
                a.informativeText = "Install \(PreferredVoice.name) (Enhanced) in System Settings → Accessibility → Spoken Content → Voices."
                a.addButton(withTitle: "OK")
                a.runModal()
            }
            return
        }
        
        synth.stopSpeaking(at: .immediate)
        let u = AVSpeechUtterance(string: text)
        u.voice = v
        u.rate = rate
        u.pitchMultiplier = pitch
        u.volume = volume
        print("🎙️  Queueing with \(v.name) [\(v.identifier)]")
        synth.speak(u)
    }
    
    func stop() {
        synth.stopSpeaking(at: .immediate)
    }

    // MARK: - AVSpeechSynthesizerDelegate (PROOF of actual voice used)

    func speechSynthesizer(_ s: AVSpeechSynthesizer, didStart u: AVSpeechUtterance) {
        let used = u.voice?.identifier ?? "unknown"
        let name = u.voice?.name ?? "unknown"
        let ok = (name == PreferredVoice.name)
        let emoji = ok ? "✅" : "⚠️"
        print("\(emoji) didStart with \(name) [\(used)] \(ok ? "MATCH" : "MISMATCH")")
        
        if !ok {
            // Stop immediately to avoid hearing the wrong voice
            s.stopSpeaking(at: .immediate)
            NSSound.beep()
            print("🚨 VOICE MISMATCH – stopped playback.")
            
            // Show alert
            DispatchQueue.main.async {
                let a = NSAlert()
                a.alertStyle = .warning
                a.messageText = "Voice mismatch detected"
                a.informativeText = "Expected \(PreferredVoice.name), got \(name). Speech stopped."
                a.addButton(withTitle: "OK")
                a.runModal()
            }
        }
    }
    
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        print("✅ didFinish speech")
    }
    
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) {
        print("🛑 didCancel speech")
    }
}

