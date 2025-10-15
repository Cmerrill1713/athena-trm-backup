import AVFoundation
import Foundation

@MainActor
class VoiceRecorder: NSObject, ObservableObject {
    @Published var isRecording = false

    private var audioRecorder: AVAudioRecorder?
    private var audioFileURL: URL?
    private var silenceTimer: Timer?

    func startRecording() async throws {
        // Create temporary file
        let tempDir = FileManager.default.temporaryDirectory
        self.audioFileURL = tempDir.appendingPathComponent("recording_\(UUID().uuidString).m4a")

        // Configure recorder for macOS
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 44100.0,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]

        guard let fileURL = self.audioFileURL else {
            throw NSError(domain: "VoiceRecorder", code: -1, userInfo: [NSLocalizedDescriptionKey: "Audio file URL not set"])
        }
        self.audioRecorder = try AVAudioRecorder(url: fileURL, settings: settings)
        self.audioRecorder?.isMeteringEnabled = true
        self.audioRecorder?.record()
        self.isRecording = true

        print("🎤 Recording started - speak now!")

        // Auto-stop after silence (5 seconds of no speech)
        self.startSilenceDetection()
    }

    private func startSilenceDetection() {
        // Simple timeout-based detection (5 seconds)
        // In production, use actual VAD (Voice Activity Detection)
        self.silenceTimer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: false) { [weak self] _ in
            Task { @MainActor in
                self?.isRecording = false
                print("🎤 Auto-stopped after silence")
            }
        }
    }

    func stopRecording() async throws -> Data? {
        self.silenceTimer?.invalidate()
        self.silenceTimer = nil

        self.audioRecorder?.stop()
        self.isRecording = false

        print("🎤 Recording stopped")

        // Read audio file
        guard let url = audioFileURL else { return nil }
        let data = try Data(contentsOf: url)

        // Clean up
        try? FileManager.default.removeItem(at: url)

        return data
    }
}
