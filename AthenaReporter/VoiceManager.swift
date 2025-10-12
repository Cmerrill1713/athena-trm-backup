import Foundation
import AVFoundation
import AppKit

// MARK: - TTS Backend Selection

enum TTSBackend {
    case system                          // AVSpeech (macOS built-in voices)
    case http(url: URL, voice: String?)  // Kokoro/HTTP TTS server
}

// MARK: - VoiceManager (Hard-locked with delegate verification)

final class VoiceManager: NSObject, AVSpeechSynthesizerDelegate {
    static let shared = VoiceManager()
    
    private let synth = AVSpeechSynthesizer()
    private(set) var voice: AVSpeechSynthesisVoice?
    private(set) var reason = "unresolved"
    
    // Preferred voice configuration
    private let preferredName = "Samantha"
    private let candidateIds = [
        "com.apple.voice.compact.en-US.Samantha",
        "com.apple.voice.premium.en-US.Samantha",
        "com.apple.ttsbundle.Samantha-compact",
        "com.apple.speech.synthesis.voice.samantha"
    ]
    
    override init() {
        super.init()
        synth.delegate = self
        print("🎤 VoiceManager initialized with delegate")
    }
    
    /// Call once on app launch to lock in the voice
    func resolve() {
        let voices = AVSpeechSynthesisVoice.speechVoices()
        
        // Try exact name match first (highest quality)
        if let byName = voices
            .filter({ $0.name == preferredName })
            .sorted(by: { $0.quality.rawValue > $1.quality.rawValue })
            .first {
            voice = byName
            reason = "locked by name \(byName.identifier) q=\(byName.quality.rawValue)"
            print("🔊 Athena: \(reason)")
            return
        }
        
        // Try known identifiers
        for id in candidateIds {
            if let v = AVSpeechSynthesisVoice(identifier: id) {
                voice = v
                reason = "locked by id \(id) q=\(v.quality.rawValue)"
                print("🔊 Athena: \(reason)")
                return
            }
        }
        
        // Hard stop - no fallback
        voice = nil
        reason = "\(preferredName) not installed"
        print("❌ Athena Voice: \(reason)")
        
        // Show alert
        DispatchQueue.main.async {
            let alert = NSAlert()
            alert.alertStyle = .critical
            alert.messageText = "Athena voice not ready"
            alert.informativeText = "\(self.preferredName) isn't available. Install Enhanced or restart after download completes."
            alert.addButton(withTitle: "OK")
            alert.runModal()
        }
    }
    
    /// Speak text with the hard-locked voice (or refuse to speak)
    func speak(_ text: String, rate: Float = 0.92, pitch: Float = 1.05, volume: Float = 0.88) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        
        guard let v = voice else {
            NSSound.beep()
            print("🚫 Skipping speech: \(reason)")
            return
        }
        
        let utt = AVSpeechUtterance(string: trimmed)
        utt.voice = v
        utt.rate = AVSpeechUtteranceDefaultSpeechRate * rate
        utt.pitchMultiplier = pitch
        utt.volume = volume
        
        print("🎙️  Queueing with \(v.name) [\(v.identifier)] \(v.language) q=\(v.quality.rawValue)")
        
        // Stop any current speech to prevent overlap
        synth.stopSpeaking(at: .immediate)
        synth.speak(utt)
    }
    
    /// Stop all speech immediately
    func stop() {
        synth.stopSpeaking(at: .immediate)
    }
    
    // MARK: - AVSpeechSynthesizerDelegate (PROOF of actual voice used)
    
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didStart utterance: AVSpeechUtterance) {
        if let v = utterance.voice {
            let matches = v.name == preferredName
            let emoji = matches ? "✅" : "⚠️"
            print("\(emoji) didStart with \(v.name) [\(v.identifier)] \(v.language) q=\(v.quality.rawValue) matches_preferred=\(matches)")
            
            // Alert if mismatch
            if !matches {
                NSSound.beep()
                print("🚨 VOICE MISMATCH: Expected \(preferredName), got \(v.name)")
            }
        } else {
            print("⚠️  didStart without explicit voice (unexpected)")
        }
    }
    
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        print("✅ didFinish speech")
    }
    
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) {
        print("🛑 didCancel speech")
    }
    
    /// Print voice status
    func printStatus() {
        if let v = voice {
            print("✅ Using voice: \(v.name) [\(v.identifier)] \(v.language) quality=\(v.quality.rawValue)")
        } else {
            print("⚠️  No voice locked. \(reason)")
        }
    }
    
    /// List all available voices (for debugging)
    static func listAvailableVoices() -> [String] {
        return AVSpeechSynthesisVoice.speechVoices().map { voice in
            "\(voice.name) [\(voice.identifier)] (\(voice.language)) q=\(voice.quality.rawValue)"
        }
    }
}

// MARK: - AthenaSpeaker (Multi-backend support with auto-detection)

final class AthenaSpeaker {
    static let shared = AthenaSpeaker()
    
    var backend: TTSBackend
    private var httpPlayer: AVAudioPlayer?
    
    private var hasAnnouncedFallback = false
    
    init() {
        // Auto-detect: Prefer Kokoro if available, fall back to system
        if let kokoroURL = URL(string: "http://127.0.0.1:8020/tts"),
           Self.isKokoroAvailable(url: kokoroURL.deletingLastPathComponent()) {
            self.backend = .http(url: kokoroURL, voice: "af_heart")
            print("🎙️  Using Kokoro voice=serna (af_heart)")
        } else {
            self.backend = .system
            print("⚠️  Kokoro unavailable → macOS TTS")
            hasAnnouncedFallback = false  // Will announce on first speak
        }
    }
    
    /// Speak using the configured backend
    func speak(_ text: String) {
        switch backend {
        case .system:
            // Announce fallback once per session
            if !hasAnnouncedFallback {
                hasAnnouncedFallback = true
                VoiceSentinel.shared.speak("Using fallback voice temporarily.")
                // Wait for announcement to finish
                Thread.sleep(forTimeInterval: 2)
            }
            VoiceSentinel.shared.speak(text)
        case .http(let url, let voice):
            speakViaHTTP(text, endpoint: url, voice: voice)
        }
    }
    
    /// Stop all speech
    func stop() {
        VoiceSentinel.shared.stop()
        httpPlayer?.stop()
    }
    
    // MARK: - HTTP TTS (Kokoro/Custom)
    
    private func speakViaHTTP(_ text: String, endpoint: URL, voice: String?) {
        print("🌐 HTTP TTS: \(endpoint)")
        
        var req = URLRequest(url: endpoint, timeoutInterval: 10)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "text": text,
            "voice": voice ?? "athena",
            "format": "wav"
        ]
        
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        let sema = DispatchSemaphore(value: 0)
        URLSession.shared.dataTask(with: req) { [weak self] data, response, err in
            defer { sema.signal() }
            
            if let err = err {
                print("❌ HTTP TTS error: \(err.localizedDescription)")
                DispatchQueue.main.async {
                    VoiceManager.shared.speak(text)
                }
                return
            }
            
            guard let data = data, !data.isEmpty else {
                print("❌ HTTP TTS: empty response")
                DispatchQueue.main.async {
                    VoiceManager.shared.speak(text)
                }
                return
            }
            
            if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
                print("❌ HTTP TTS: status \(http.statusCode)")
                DispatchQueue.main.async {
                    VoiceManager.shared.speak(text)
                }
                return
            }
            
            do {
                let player = try AVAudioPlayer(data: data)
                self?.httpPlayer = player
                player.prepareToPlay()
                player.play()
                print("✅ HTTP TTS: playing audio (\(data.count) bytes)")
            } catch {
                print("❌ HTTP TTS play error: \(error)")
                DispatchQueue.main.async {
                    VoiceManager.shared.speak(text)
                }
            }
        }.resume()
        
        _ = sema.wait(timeout: .now() + 10)
    }
    
    /// Check if Kokoro is reachable
    static func isKokoroAvailable(url: URL) -> Bool {
        let healthURL = url.appendingPathComponent("health")
        var req = URLRequest(url: healthURL, timeoutInterval: 1)
        req.httpMethod = "GET"
        
        let sema = DispatchSemaphore(value: 0)
        var reachable = false
        
        URLSession.shared.dataTask(with: req) { _, response, _ in
            if let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode) {
                reachable = true
            }
            sema.signal()
        }.resume()
        
        _ = sema.wait(timeout: .now() + 1)
        return reachable
    }
}
