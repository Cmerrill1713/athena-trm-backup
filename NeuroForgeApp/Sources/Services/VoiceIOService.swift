import AVFoundation
import Foundation

// MARK: - TTS Models

struct TTSSynthesizeRequest: Codable {
    let text: String
    let voice: String?
}

struct TTSSynthesizeResponse: Codable {
    let audio_b64: String
    let duration_ms: Int
    let sample_rate: Int
    let route: String
    let latency_ms: Int
    let modality: String
}

// MARK: - Voice I/O Service

/// VoiceIOService - Local-first TTS via Kokoro-82M
@MainActor
final class VoiceIOService: ObservableObject {
    @Published var lastLatency: Int = 0
    @Published var lastRoute: String = "kokoro-82m"
    @Published var isSpeaking: Bool = false

    private let routerBase = AppConfig.routerURL  // http://127.0.0.1:9113
    private let session = URLSession(configuration: .default)
    private var audioPlayer: AVAudioPlayer?

    /// Synthesize and play speech from text
    func speak(
        _ text: String,
        voice: String? = nil
    ) async throws {
        isSpeaking = true
        defer { isSpeaking = false }

        // Call router TTS endpoint
        let request = TTSSynthesizeRequest(text: text, voice: voice)
        let response: TTSSynthesizeResponse = try await postJSON(
            endpoint: "/tts/synthesize",
            payload: request
        )

        // Update published properties
        lastLatency = response.latency_ms
        lastRoute = response.route

        // Decode audio from base64
        guard let audioData = Data(base64Encoded: response.audio_b64) else {
            throw NSError(
                domain: "VoiceIO",
                code: 1,
                userInfo: [NSLocalizedDescriptionKey: "Failed to decode audio data"]
            )
        }

        // Play audio
        try await playAudio(data: audioData)
    }

    /// Synthesize without playing (returns audio data)
    func synthesize(
        _ text: String,
        voice: String? = nil
    ) async throws -> Data {
        let request = TTSSynthesizeRequest(text: text, voice: voice)
        let response: TTSSynthesizeResponse = try await postJSON(
            endpoint: "/tts/synthesize",
            payload: request
        )

        lastLatency = response.latency_ms
        lastRoute = response.route

        guard let audioData = Data(base64Encoded: response.audio_b64) else {
            throw NSError(
                domain: "VoiceIO",
                code: 1,
                userInfo: [NSLocalizedDescriptionKey: "Failed to decode audio data"]
            )
        }

        return audioData
    }

    // MARK: - Audio Playback

    private func playAudio(data: Data) async throws {
        // Create audio player
        audioPlayer = try AVAudioPlayer(data: data)
        audioPlayer?.prepareToPlay()
        audioPlayer?.play()

        // Wait for completion using Task
        while audioPlayer?.isPlaying == true {
            try await Task.sleep(nanoseconds: 100_000_000)  // 0.1 seconds
        }
    }

    /// Stop current playback
    func stop() {
        audioPlayer?.stop()
        isSpeaking = false
    }

    // MARK: - HTTP Helper

    private func postJSON<T: Codable, R: Codable>(
        endpoint: String,
        payload: T
    ) async throws -> R {
        var request = URLRequest(url: routerBase.appendingPathComponent(endpoint))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 5.0

        request.httpBody = try JSONEncoder().encode(payload)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        guard httpResponse.statusCode == 200 else {
            let errorText = String(data: data, encoding: .utf8) ?? "HTTP \(httpResponse.statusCode)"
            throw NSError(
                domain: "VoiceIO",
                code: httpResponse.statusCode,
                userInfo: [NSLocalizedDescriptionKey: errorText]
            )
        }

        return try JSONDecoder().decode(R.self, from: data)
    }
}
