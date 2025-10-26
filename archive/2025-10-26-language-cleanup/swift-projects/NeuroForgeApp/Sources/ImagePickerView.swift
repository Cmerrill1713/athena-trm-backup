import SwiftUI
import AppKit

struct ImagePickerView: NSViewControllerRepresentable {
    @Binding var selectedImage: NSImage?
    @Environment(\.dismiss) private var dismiss
    
    func makeNSViewController(context: Context) -> NSViewController {
        let controller = NSViewController()
        
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.canChooseFiles = true
        panel.allowedContentTypes = [.image]
        
        panel.begin { response in
            if response == .OK, let url = panel.url {
                if let image = NSImage(contentsOf: url) {
                    selectedImage = image
                }
            }
            dismiss()
        }
        
        return controller
    }
    
    func updateNSViewController(_ nsViewController: NSViewController, context: Context) {
    }
}



