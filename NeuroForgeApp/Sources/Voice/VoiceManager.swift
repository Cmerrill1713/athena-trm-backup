// Sources/Voice/VoiceManager.swift
import Foundation
import AVFoundation
import Speech
import Combine

@MainActor
final class VoiceManager: ObservableObject {
    enum State: Equatable {
        case idle
        case requestingPermission
        case listening
        case transcribing(String)   // partial text
        case sending(String)        // final transcript
        case speaking               // TTS
        case error(String)
    }

    @Published var state: State = .idle
    @Published var level: CGFloat = 0           // 0…1 for waveform
    @Published var transcript: String = ""

    var ttsEnabled = true
    var autoSendOnRelease = true
    var inputLanguage = "en-US"

    private let audioEngine = AVAudioEngine()
    private let speechRecognizer: SFSpeechRecognizer
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let synthesizer = AVSpeechSynthesizer()
    private var meterTimer: Timer?
    private var cancellables = Set<AnyCancellable>()

    init(localeIdentifier: String? = nil) {
        let id = localeIdentifier ?? "en-US"
        self.speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: id)) ?? SFSpeechRecognizer()!
        synthesizer.delegate = self
    }

    // MARK: - Permissions

    func ensurePermissions() async -> Bool {
        state = .requestingPermission
        let micGranted = await withCheckedContinuation { (cont: CheckedContinuation<Bool, Never>) in
            AVAudioApplication.requestRecordPermission { cont.resume(returning: $0) }
        }
        guard micGranted else {
            state = .error("Microphone permission denied")
            return false
        }

        let sttAuth = await SFSpeechRecognizer.requestAuthorization()
        guard sttAuth == .authorized else {
            state = .error("Speech recognition permission denied")
            return false
        }
        return true
    }

    // MARK: - Recording / Transcription

    func startListening() async {
        guard await ensurePermissions() else { return }
        stopAll()

        transcript = ""
        state = .listening
        level = 0

        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        recognitionRequest?.shouldReportPartialResults = true
        recognitionTask = speechRecognizer.recognitionTask(with: recognitionRequest!) { [weak self] result, error in
            guard let self else { return }
            Task { @MainActor in
                if let res = result {
                    self.transcript = res.bestTranscription.formattedString
                    self.state = .transcribing(self.transcript)
                }
                if error != nil || (result?.isFinal ?? false) {
                    self.finishListening()
                }
            }
        }

        configureAudioSession()
        try? startEngine()
        beginMetering()
        
        // Haptic feedback
        NSHapticFeedbackManager.defaultPerformer.perform(.generic, performanceTime: .default)
    }

    func finishListening() {
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        stopMetering()

        let final = transcript.trimmingCharacters(in: .whitespacesAndNewlines)
        if final.isEmpty {
            state = .idle
        } else if autoSendOnRelease {
            state = .sending(final)
        } else {
            state = .transcribing(final)
        }
    }

    func cancel() {
        stopAll()
        state = .idle
    }

    private func stopAll() {
        stopMetering()
        if audioEngine.isRunning { audioEngine.stop() }
        audioEngine.inputNode.removeTap(onBus: 0)
        recognitionTask?.cancel()
        recognitionTask = nil
        recognitionRequest = nil
    }

    // MARK: - TTS (Kokoro-first, system fallback)

    func speak(_ text: String) {
        guard ttsEnabled, !text.isEmpty else { return }
        state = .speaking
        
        // Try Kokoro first
        if let kokoroURL = URL(string: "http://127.0.0.1:8020/tts") {
            speakViaKokoro(text, url: kokoroURL) { [weak self] success in
                if !success {
                    // Fallback to system voice
                    self?.speakViaSystem(text)
                }
            }
        } else {
            speakViaSystem(text)
        }
    }

    func stopSpeaking() {
        synthesizer.stopSpeaking(at: .immediate)
        httpPlayer?.stop()
        state = .idle
    }
    
    // MARK: - HTTP TTS (Kokoro)
    
    private var httpPlayer: AVAudioPlayer?
    
    private func speakViaKokoro(_ text: String, url: URL, completion: @escaping (Bool) -> Void) {
        var req = URLRequest(url: url, timeoutInterval: 10)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "text": text,
            "voice": "af_heart",  // Kokoro "serna" voice
            "format": "wav",
            "speed": 1.0
        ]
        
        guard let jsonData = try? JSONSerialization.data(withJSONObject: body) else {
            completion(false)
            return
        }
        
        req.httpBody = jsonData
        
        URLSession.shared.dataTask(with: req) { [weak self] data, response, error in
            guard let self else { return }
            
            if let error = error {
                print("🌐 Kokoro TTS failed: \(error.localizedDescription)")
                DispatchQueue.main.async { completion(false) }
                return
            }
            
            guard let data = data, data.count > 0 else {
                print("🌐 Kokoro TTS: No audio data")
                DispatchQueue.main.async { completion(false) }
                return
            }
            
            do {
                let player = try AVAudioPlayer(data: data)
                player.delegate = self
                self.httpPlayer = player
                player.play()
                print("🎙️  Playing Kokoro voice (af_heart): \(text.prefix(50))...")
                DispatchQueue.main.async { completion(true) }
            } catch {
                print("🌐 Kokoro TTS playback error: \(error.localizedDescription)")
                DispatchQueue.main.async { completion(false) }
            }
        }.resume()
    }
    
    private func speakViaSystem(_ text: String) {
        print("⚠️  Using system voice (Kokoro unavailable)")
        let utterance = AVSpeechUtterance(string: text)
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate * 0.92
        utterance.voice = AVSpeechSynthesisVoice(language: inputLanguage)
        synthesizer.speak(utterance)
    }

    // MARK: - Audio plumbing

    private func configureAudioSession() {
        let session = AVAudioSession.sharedInstance()
        try? session.setCategory(.playAndRecord, mode: .measurement, options: [.duckOthers, .defaultToSpeaker, .allowBluetooth])
        try? session.setActive(true, options: .notifyOthersOnDeactivation)
    }

    private func startEngine() throws {
        let input = audioEngine.inputNode
        let format = input.inputFormat(forBus: 0)
        input.installTap(onBus: 0, bufferSize: 1024, format: format) { [weak self] buffer, _ in
            self?.recognitionRequest?.append(buffer)
        }
        audioEngine.prepare()
        try audioEngine.start()
    }

    private func beginMetering() {
        stopMetering()
        meterTimer = Timer.scheduledTimer(withTimeInterval: 0.04, repeats: true) { [weak self] _ in
            guard let self else { return }
            Task { @MainActor in
                // Crude level approximation
                let base: CGFloat = self.audioEngine.isRunning ? 0.25 : 0
                let activity: CGFloat = self.transcript.isEmpty ? 0 : 0.15
                let shimmer = CGFloat.random(in: 0...0.1)
                self.level = min(1, max(0, base + activity + shimmer))
            }
        }
        RunLoop.main.add(meterTimer!, forMode: .common)
    }

    private func stopMetering() {
        meterTimer?.invalidate()
        meterTimer = nil
        level = 0
    }
}

extension VoiceManager: AVSpeechSynthesizerDelegate {
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        Task { @MainActor in
            state = .idle
        }
    }
}

extension VoiceManager: AVAudioPlayerDelegate {
    nonisolated func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        Task { @MainActor in
            state = .idle
            print("✅ Kokoro playback finished")
        }
    }
    
    nonisolated func audioPlayerDecodeErrorDidOccur(_ player: AVAudioPlayer, error: Error?) {
        Task { @MainActor in
            state = .idle
            if let error = error {
                print("❌ Kokoro playback error: \(error.localizedDescription)")
            }
        }
    }
}

