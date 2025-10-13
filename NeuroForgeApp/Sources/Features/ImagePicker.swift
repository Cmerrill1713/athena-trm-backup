import SwiftUI
import AppKit

struct ImagePickerButton: View {
    var label: String = "Attach Image"
    var onPick: (NSImage, Data) -> Void

    var body: some View {
        Button(label) { openPanel() }
            .accessibilityIdentifier("attach_image_button")
    }

    private func openPanel() {
        let p = NSOpenPanel()
        p.allowedContentTypes = [.png, .jpeg, .tiff, .heic]
        p.canChooseDirectories = false
        p.allowsMultipleSelection = false
        if p.runModal() == .OK, let url = p.url, let img = NSImage(contentsOf: url),
           let data = try? Data(contentsOf: url) {
            onPick(img, data)
        }
    }
}

// MARK: - Async Image Picker Helper

enum ImagePickerHelper {
    @MainActor
    static func pick() async -> NSImage? {
        await withCheckedContinuation { continuation in
            let panel = NSOpenPanel()
            panel.allowedContentTypes = [.png, .jpeg, .tiff, .heic]
            panel.canChooseDirectories = false
            panel.allowsMultipleSelection = false
            panel.begin { response in
                if response == .OK, let url = panel.url, let image = NSImage(contentsOf: url) {
                    continuation.resume(returning: image)
                } else {
                    continuation.resume(returning: nil)
                }
            }
        }
    }
}

// MARK: - NSImage PNG Data Extension

extension NSImage {
    func pngData() -> Data? {
        guard let tiffData = self.tiffRepresentation,
              let bitmap = NSBitmapImageRep(data: tiffData) else {
            return nil
        }
        return bitmap.representation(using: .png, properties: [:])
    }
}
