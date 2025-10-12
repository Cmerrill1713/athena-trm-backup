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
