// Frontend Helpers for Model-Agnostic Athena Integration
// Drop these into your SwiftUI project

import Foundation
import AppKit

// MARK: - Task Models (No Model Names!)

enum ChatTaskKind: String, Encodable {
    case text
    case visionDescribe
    case visionOCR
    case reasoning
}

struct ChatTask: Encodable {
    let kind: ChatTaskKind
    let text: String?
    let imageBase64: String?
}

struct ChatResponse: Decodable {
    let text: String
    let latency_ms: Double?
    let provider: String?  // For debugging only
}

// MARK: - API Client

class AthenaAPI {
    let baseURL: String

    init(baseURL: String = "http://127.0.0.1:8014") {
        self.baseURL = baseURL
    }

    func send(_ task: ChatTask) async throws -> ChatResponse {
        let url = URL(string: "\(baseURL)/api/chat")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.addValue("application/json", "Content-Type")
        request.httpBody = try JSONEncoder().encode(task)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            throw APIError.httpError(httpResponse.statusCode)
        }

        return try JSONDecoder().decode(ChatResponse.self, from: data)
    }
}

enum APIError: Error {
    case invalidResponse
    case httpError(Int)
}

// MARK: - Image Picker Helper

func pickImage() -> NSImage? {
    let panel = NSOpenPanel()
    panel.allowsMultipleSelection = false
    panel.canChooseDirectories = false
    panel.allowedContentTypes = [.png, .jpeg, .gif, .tiff]
    panel.message = "Select an image for vision analysis"

    guard panel.runModal() == .OK,
          let url = panel.url,
          let image = NSImage(contentsOf: url) else {
        return nil
    }

    return image
}

// MARK: - NSImage Extensions

extension NSImage {
    func base64String() -> String? {
        guard let tiffData = self.tiffRepresentation,
              let bitmap = NSBitmapImageRep(data: tiffData),
              let pngData = bitmap.representation(using: .png, properties: [:]) else {
            return nil
        }
        return pngData.base64EncodedString()
    }

    func resized(to targetSize: CGSize) -> NSImage? {
        let newImage = NSImage(size: targetSize)
        newImage.lockFocus()
        defer { newImage.unlockFocus() }

        self.draw(
            in: NSRect(origin: .zero, size: targetSize),
            from: NSRect(origin: .zero, size: self.size),
            operation: .sourceOver,
            fraction: 1.0
        )

        return newImage
    }
}

// MARK: - Usage Example

/*
// In your ViewModel:

@MainActor
class ChatViewModel: ObservableObject {
    @Published var input: String = ""
    @Published var messages: [Message] = []
    @Published var selectedImage: NSImage?

    private let api = AthenaAPI()

    func send() {
        let task = ChatTask(
            kind: selectedImage != nil ? .visionDescribe : .text,
            text: input.isEmpty ? nil : input,
            imageBase64: selectedImage?.base64String()
        )

        Task {
            do {
                let response = try await api.send(task)
                messages.append(Message(
                    role: .assistant,
                    content: response.text
                ))

                // Clear input
                input = ""
                selectedImage = nil
            } catch {
                // Handle error
                print("Error: \(error)")
            }
        }
    }

    func attachImage() {
        if let image = pickImage() {
            // Optionally resize large images
            if image.size.width > 1024 {
                selectedImage = image.resized(to: CGSize(width: 1024, height: 1024))
            } else {
                selectedImage = image
            }
        }
    }
}

// In your View:

TextField("Message", text: $viewModel.input)
    .accessibilityIdentifier("chat_input")
    .onKeyPress(.return) { press in
        if press.modifiers.isEmpty {
            viewModel.send()
            return .handled
        }
        return .ignored  // Shift+Enter = newline
    }

Button("Attach Image") {
    viewModel.attachImage()
}

Button("Send") {
    viewModel.send()
}

if let image = viewModel.selectedImage {
    Image(nsImage: image)
        .resizable()
        .frame(width: 100, height: 100)
}

ScrollView {
    ForEach(viewModel.messages) { msg in
        Text(msg.content)
            .accessibilityIdentifier("chat_response")
    }
}
*/
