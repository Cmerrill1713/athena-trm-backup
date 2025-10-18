import AppKit
import OSLog

// MARK: - Floating Chat Window (pure AppKit, ~70 lines)

final class FloatingChatWindow: NSWindow, NSTextFieldDelegate {
    private let logger = Logger(subsystem: "com.neuroforge.athena", category: "FloatingChat")
    private let input = NSTextField()
    private let status = NSTextField(labelWithString: "Ready")

    private let gatewayURL = URL(string: "http://127.0.0.1:8015/v1/chat/completions")!

    init() {
        let frame = NSRect(x: 200, y: 200, width: 520, height: 90)
        super.init(
            contentRect: frame,
            styleMask: [.titled, .closable, .miniaturizable],
            backing: .buffered, defer: false)
        title = "Floating Chat → LLM Gateway"
        level = .floating
        isReleasedWhenClosed = false

        input.placeholderString = "Type message… (Return sends) - Click me!"
        input.isEditable = true
        input.isBordered = true
        input.isBezeled = true
        input.bezelStyle = .roundedBezel
        input.font = .systemFont(ofSize: 14)
        input.delegate = self

        // Add click handler to verify events reach the field
        input.target = self
        input.action = #selector(fieldClicked)

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
            stack.bottomAnchor.constraint(equalTo: contentView!.bottomAnchor),
        ])

        makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)

        // EXTREME DIAGNOSTICS with OSLog
        logger.info("🪟 Window created")
        logger.info("   - isKeyWindow: \(self.isKeyWindow)")
        logger.info("   - canBecomeKey: \(self.canBecomeKey)")
        logger.info("   - level: \(self.level.rawValue)")

        DispatchQueue.main.async {
            let didBecomeFirstResponder = self.input.window?.makeFirstResponder(self.input) ?? false
            self.logger.info("   - makeFirstResponder: \(didBecomeFirstResponder)")
            self.logger.info("   - firstResponder exists: \(self.input.window?.firstResponder != nil)")
            self.logger.info("   - input.acceptsFirstResponder: \(self.input.acceptsFirstResponder)")

            // Force it again
            self.makeKey()
            self.orderFront(nil)
            _ = self.makeFirstResponder(self.input)

            self.logger.info("   - After force: isKeyWindow=\(self.isKeyWindow), firstResponder exists=\(self.firstResponder != nil)")
        }
    }

    // Click handler - verify events reach the field
    @objc private func fieldClicked() {
        logger.info("👆 Field clicked! Focus should be set now.")
        logger.info("   - firstResponder exists: \(self.firstResponder != nil)")
    }
    
    // Return sends (Shift+Return is just Return in NSTextField — single-line by design)
    func control(_ control: NSControl, textView: NSTextView, doCommandBy sel: Selector) -> Bool {
        logger.info("⌨️ control:doCommandBy called - selector: \(String(describing: sel))")
        if sel == #selector(NSResponder.insertNewline(_:)) {
            logger.info("↩️ Enter key detected, sending...")
            send(text: input.stringValue.trimmingCharacters(in: .whitespacesAndNewlines))
            return true  // swallow Enter
        }
        return false
    }
    
    // Text did change - verify typing works
    func controlTextDidChange(_ obj: Notification) {
        logger.info("✏️ Text changed: \"\(self.input.stringValue)\"")
    }

    private func send(text: String) {
        guard !text.isEmpty else { return }
        logger.info("📤 Sending to gateway: \(text)")
        setStatus("Sending...")
        let payload: [String: Any] = [
            "messages": [["role": "user", "content": text]],
            "stream": false,
        ]
        let reqData = try! JSONSerialization.data(withJSONObject: payload)
        var req = URLRequest(url: gatewayURL)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = reqData

        // async on a background queue; hop to main for UI updates
        URLSession.shared.dataTask(with: req) { [weak self] data, resp, err in
            if let err = err {
                self?.logger.error("❌ LLM error: \(err.localizedDescription)")
                self?.setStatus("Error")
                return
            }
            guard
                let http = resp as? HTTPURLResponse,
                http.statusCode == 200,
                let data = data,
                let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                let choices = json["choices"] as? [[String: Any]],
                let msg = choices.first?["message"] as? [String: Any],
                let content = msg["content"] as? String
            else {
                let responseText = String(data: data ?? Data(), encoding: .utf8) ?? "<nil>"
                self?.logger.error("❌ LLM bad response: \(responseText)")
                self?.setStatus("Bad response")
                return
            }

            self?.logger.info("✅ LLM reply: \(content.prefix(100))...")
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
private let openLogger = Logger(subsystem: "com.neuroforge.athena", category: "FloatingChat")

func openFloatingChatWindow() {
    if let w = _floatingChatWin {
        w.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        openLogger.info("🪟 Floating chat window reopened (already exists)")
        return
    }
    _floatingChatWin = FloatingChatWindow()
    openLogger.info("🪟 Floating chat window opened (NEW)")
}
