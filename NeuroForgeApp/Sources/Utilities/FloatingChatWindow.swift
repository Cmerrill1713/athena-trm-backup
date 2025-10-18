import AppKit

// MARK: - Floating Chat Window (pure AppKit, ~70 lines)

final class FloatingChatWindow: NSWindow, NSTextFieldDelegate {
    private let input = NSTextField()
    private let status = NSTextField(labelWithString: "Ready")

    private let gatewayURL = URL(string: "http://127.0.0.1:8015/v1/chat/completions")!

    init() {
        let frame = NSRect(x: 200, y: 200, width: 520, height: 90)
        super.init(contentRect: frame,
                   styleMask: [.titled, .closable, .miniaturizable],
                   backing: .buffered, defer: false)
        title = "Floating Chat → LLM Gateway"
        level = .floating
        isReleasedWhenClosed = false

        input.placeholderString = "Type message… (Return sends)"
        input.isEditable = true
        input.isBordered = true
        input.isBezeled = true
        input.bezelStyle = .roundedBezel
        input.font = .systemFont(ofSize: 14)
        input.delegate = self

        status.font = .systemFont(ofSize: 11)
        status.textColor = .secondaryLabelColor
        status.alignment = .right

        let stack = NSStackView(views: [input, status])
        stack.orientation = .vertical
        stack.spacing = 6
        stack.edgeInsets = NSEdgeInsets(top: 10, left: 12, bottom: 12, right: 12)

        contentView = NSView(frame: frame)
        contentView?.addSubview(stack)
        stack.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: contentView!.leadingAnchor),
            stack.trailingAnchor.constraint(equalTo: contentView!.trailingAnchor),
            stack.topAnchor.constraint(equalTo: contentView!.topAnchor),
            stack.bottomAnchor.constraint(equalTo: contentView!.bottomAnchor)
        ])

        makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        DispatchQueue.main.async { self.input.window?.makeFirstResponder(self.input) }
    }

    // Return sends (Shift+Return is just Return in NSTextField — single-line by design)
    func control(_ control: NSControl, textView: NSTextView, doCommandBy sel: Selector) -> Bool {
        if sel == #selector(NSResponder.insertNewline(_:)) {
            send(text: input.stringValue.trimmingCharacters(in: .whitespacesAndNewlines))
            return true // swallow Enter
        }
        return false
    }

    private func send(text: String) {
        guard !text.isEmpty else { return }
        print("📤 Sending to gateway: \(text)")
        setStatus("Sending...")
        let payload: [String: Any] = [
            "messages": [["role":"user","content": text]],
            "stream": false
        ]
        let reqData = try! JSONSerialization.data(withJSONObject: payload)
        var req = URLRequest(url: gatewayURL)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = reqData

        // async on a background queue; hop to main for UI updates
        URLSession.shared.dataTask(with: req) { [weak self] data, resp, err in
            if let err = err {
                print("❌ LLM error:", err.localizedDescription)
                self?.setStatus("Error")
                return
            }
            guard
                let http = resp as? HTTPURLResponse,
                http.statusCode == 200,
                let data = data,
                let json = try? JSONSerialization.jsonObject(with: data) as? [String:Any],
                let choices = json["choices"] as? [[String:Any]],
                let msg = choices.first?["message"] as? [String:Any],
                let content = msg["content"] as? String
            else {
                print("❌ LLM bad response:", String(data: data ?? Data(), encoding: .utf8) ?? "<nil>")
                self?.setStatus("Bad response")
                return
            }

            print("✅ LLM reply:\n\(content)\n")
            self?.setStatus("OK (\(content.prefix(20))...)")
        }.resume()

        input.stringValue = ""
        DispatchQueue.main.async { self.input.window?.makeFirstResponder(self.input) }
    }

    private func setStatus(_ s: String) {
        DispatchQueue.main.async {
            self.status.stringValue = s
            self.input.window?.makeFirstResponder(self.input)
        }
    }
}

// MARK: - Public API: one-liner to open (singleton)
private var _floatingChatWin: FloatingChatWindow?
func openFloatingChatWindow() {
    if let w = _floatingChatWin { 
        w.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        return 
    }
    _floatingChatWin = FloatingChatWindow()
    print("🪟 Floating chat window opened")
}

