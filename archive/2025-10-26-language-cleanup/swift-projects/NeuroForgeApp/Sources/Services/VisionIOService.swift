import Foundation
import SwiftUI

// MARK: - Vision Models

struct VisionAnalyzeRequest: Codable {
    let image_b64: String
    let prompt: String
}

struct VisionResult: Codable {
    let caption: String
    let boxes: [BoundingBox]?
    let confidence: Double
    let modality: String
}

struct BoundingBox: Codable {
    let x: Double
    let y: Double
    let width: Double
    let height: Double
    let label: String?
}

struct VisionAnalyzeResponse: Codable {
    let result: VisionResult
    let route: String
    let latency_ms: Int
    let modality: String
}

// MARK: - Vision I/O Service

/// VisionIOService - Local-first vision analysis via FastVLM
@MainActor
final class VisionIOService: ObservableObject {
    @Published var lastLatency: Int = 0
    @Published var lastRoute: String = "fastvlm"
    @Published var isProcessing: Bool = false

    private let routerBase = AppConfig.routerURL  // http://127.0.0.1:9113
    private let session = URLSession(configuration: .default)

    /// Analyze image using FastVLM
    func analyze(
        image: NSImage,
        prompt: String = "Describe the image in detail"
    ) async throws -> VisionAnalyzeResponse {
        isProcessing = true
        defer { isProcessing = false }

        // Convert image to base64 PNG
        guard let tiffData = image.tiffRepresentation,
            let bitmapImage = NSBitmapImageRep(data: tiffData),
            let pngData = bitmapImage.representation(using: .png, properties: [:])
        else {
            throw NSError(
                domain: "VisionIO",
                code: 1,
                userInfo: [NSLocalizedDescriptionKey: "Failed to convert image to PNG"]
            )
        }

        let base64Image = pngData.base64EncodedString()

        // Call router vision endpoint
        let request = VisionAnalyzeRequest(image_b64: base64Image, prompt: prompt)
        let response: VisionAnalyzeResponse = try await postJSON(
            endpoint: "/vision/analyze",
            payload: request
        )

        // Update published properties
        lastLatency = response.latency_ms
        lastRoute = response.route

        return response
    }

    /// Analyze image from file path
    func analyzeFile(
        path: URL,
        prompt: String = "Describe the image in detail"
    ) async throws -> VisionAnalyzeResponse {
        guard let image = NSImage(contentsOf: path) else {
            throw NSError(
                domain: "VisionIO",
                code: 2,
                userInfo: [NSLocalizedDescriptionKey: "Failed to load image from \(path.path)"]
            )
        }

        return try await analyze(image: image, prompt: prompt)
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
                domain: "VisionIO",
                code: httpResponse.statusCode,
                userInfo: [NSLocalizedDescriptionKey: errorText]
            )
        }

        return try JSONDecoder().decode(R.self, from: data)
    }
}

// MARK: - NSImage Extension

extension NSImage {
    func toBase64PNG() throws -> String {
        guard let tiffData = self.tiffRepresentation,
            let bitmapImage = NSBitmapImageRep(data: tiffData),
            let pngData = bitmapImage.representation(using: .png, properties: [:])
        else {
            throw NSError(
                domain: "NSImage",
                code: 1,
                userInfo: [NSLocalizedDescriptionKey: "Failed to convert to PNG"]
            )
        }

        return pngData.base64EncodedString()
    }
}
