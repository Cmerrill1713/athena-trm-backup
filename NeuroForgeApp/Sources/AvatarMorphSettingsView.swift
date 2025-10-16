import SwiftUI

/// Avatar morph settings view with Ghost/Auto/Photoreal toggle
struct AvatarMorphSettingsView: View {
    @AppStorage("avatarMorphMode") private var morphMode: AvatarMode = .ghost
    @StateObject private var avatarService = AvatarService()
    @StateObject private var notificationService = AvatarNotificationService.shared
    @State private var isMorphing = false
    @State private var lastMorphResult: String?
    @State private var isTestingConnectivity = false
    @State private var connectivityStatus = false

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Avatar Morph Settings")
                .font(.title2.bold())

            Text("Control how Athena's avatar responds to awareness levels")
                .foregroundStyle(.secondary)

            // Morph mode picker
            VStack(alignment: .leading, spacing: 12) {
                Text("Morph Mode")
                    .font(.headline)

                Picker("Avatar Behavior", selection: $morphMode) {
                    Text("👻 Ghost").tag(AvatarMode.ghost)
                    Text("🧍‍♀️ Photoreal").tag(AvatarMode.photoreal)
                }
                .pickerStyle(.segmented)
                .onChange(of: morphMode) { _, newMode in
                    handleMorphModeChange(to: newMode)
                }

                // Mode descriptions
                Text(modeDescription(for: morphMode))
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .padding(.top, 4)
            }

            // Manual morph controls
            VStack(alignment: .leading, spacing: 12) {
                Text("Manual Controls")
                    .font(.headline)

                HStack(spacing: 12) {
                    Button(action: { morphTo(.ghost) }) {
                        Label("Force Ghost", systemImage: "moon.stars")
                    }
                    .buttonStyle(.bordered)
                    .disabled(isMorphing)

                    Button(action: { morphTo(.photoreal) }) {
                        Label("Force Photoreal", systemImage: "sun.max")
                    }
                    .buttonStyle(.bordered)
                    .disabled(isMorphing)
                }
            }

            // Mobile Connectivity
            VStack(alignment: .leading, spacing: 12) {
                Text("Mobile Connectivity")
                    .font(.headline)

                HStack {
                    Button(action: testConnectivity) {
                        Label("Test LAN Connection", systemImage: "wifi")
                    }
                    .buttonStyle(.bordered)
                    .disabled(isTestingConnectivity)

                    if isTestingConnectivity {
                        ProgressView()
                            .scaleEffect(0.8)
                    } else {
                        Circle()
                            .frame(width: 8, height: 8)
                            .foregroundStyle(connectivityStatus ? .green : .red)
                    }
                }

                Text(connectivityStatus ? "✅ Connected to backend" : "❌ Backend unreachable")
                    .font(.caption)
                    .foregroundStyle(connectivityStatus ? .green : .red)
            }

            // Notifications
            VStack(alignment: .leading, spacing: 12) {
                Text("Notifications")
                    .font(.headline)

                HStack {
                    Circle()
                        .frame(width: 8, height: 8)
                        .foregroundStyle(notificationService.isAuthorized ? .green : .orange)

                    VStack(alignment: .leading) {
                        Text(
                            notificationService.isAuthorized
                                ? "Notifications enabled" : "Notifications disabled")
                        Text(
                            notificationService.isAuthorized
                                ? "You'll receive avatar alerts" : "Grant permission for alerts"
                        )
                        .font(.caption)
                        .foregroundStyle(notificationService.isAuthorized ? .green : .orange)
                    }
                }

                if !notificationService.isAuthorized {
                    Button("Enable Notifications") {
                        notificationService.requestAuthorization()
                    }
                    .buttonStyle(.bordered)
                }

                if let lastNotification = notificationService.lastNotification {
                    Text("Last: \(lastNotification.message)")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
            }

            // Current status
            VStack(alignment: .leading, spacing: 8) {
                Text("Current Status")
                    .font(.headline)

                HStack {
                    Circle()
                        .frame(width: 8, height: 8)
                        .foregroundStyle(avatarService.isHealthy ? .green : .red)

                    VStack(alignment: .leading) {
                        Text(avatarService.currentState?.rawValue ?? "unknown")
                        if let awareness = avatarService.lastAwarenessLevel {
                            Text(String(format: "Awareness: %.1f", awareness))
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        Text(avatarService.isHealthy ? "System healthy" : "System issues detected")
                            .font(.caption)
                            .foregroundStyle(avatarService.isHealthy ? .green : .red)
                    }
                }

                if let result = lastMorphResult {
                    Text(result)
                        .font(.caption)
                        .foregroundStyle(result.contains("✅") ? .green : .red)
                        .padding(.top, 4)
                }
            }

            // Hysteresis settings (advanced)
            DisclosureGroup("Advanced Settings") {
                VStack(alignment: .leading, spacing: 12) {
                    Text("Morph Hysteresis")
                        .font(.subheadline)

                    HStack {
                        Text("Morph Above:")
                        TextField("0.65", text: .constant("0.65"))
                            .frame(width: 60)
                            .textFieldStyle(.roundedBorder)
                        Text("(awareness level)")
                    }

                    HStack {
                        Text("Revert Below:")
                        TextField("0.45", text: .constant("0.45"))
                            .frame(width: 60)
                            .textFieldStyle(.roundedBorder)
                        Text("(awareness level)")
                    }

                    Text("Hysteresis prevents rapid oscillation between states")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                .padding(.top, 8)
            }
        }
        .padding()
        .frame(minWidth: 400)
        .task {
            await avatarService.checkStatus()
        }
    }

    private func modeDescription(for mode: AvatarMode) -> String {
        switch mode {
        case .ghost:
            return "Always show ghost avatar - minimal resources, consistent experience"
        case .photoreal:
            return "Always show photoreal avatar - maximum fidelity, higher resources"
        case .morphing:
            return "Currently transitioning between modes"
        }
    }

    private func handleMorphModeChange(to newMode: AvatarMode) {
        morphTo(newMode)
    }

    private func morphTo(_ target: AvatarMode) {
        guard target != .ghost else { return }

        isMorphing = true
        lastMorphResult = nil

        Task {
            do {
                let success = try await avatarService.morph(to: target)
                lastMorphResult =
                    success
                    ? "✅ Successfully morphed to \(target.rawValue)"
                    : "❌ Failed to morph to \(target.rawValue)"
            } catch {
                lastMorphResult = "❌ Morph failed: \(error.localizedDescription)"
            }
            isMorphing = false
        }
    }

    private func testConnectivity() {
        isTestingConnectivity = true
        connectivityStatus = false

        Task {
            let isConnected = await avatarService.testLANConnectivity()
            await MainActor.run {
                connectivityStatus = isConnected
                isTestingConnectivity = false
            }
        }
    }
}

/// Avatar service for morph operations
class AvatarService: ObservableObject {
    @Published var currentState: AvatarMode?
    @Published var isHealthy = false
    @Published var lastAwarenessLevel: Double?

    private let baseURL = URL(string: "http://localhost:8000")!  // TODO: Wire to AppConfig
    private var previousState: AvatarMode?

    // Mock state for fast-track mode
    private var mockMode = ProcessInfo.processInfo.environment["DISABLE_BACKEND_CHECKS"] == "1"

    func checkStatus() async {
        if mockMode {
            // Mock status for fast-track mode
            await MainActor.run {
                self.currentState = self.currentState ?? .ghost
                self.lastAwarenessLevel = 0.3  // Low awareness = ghost mode
                self.isHealthy = true
            }
            return
        }

        do {
            let response = try await URLSession.shared.data(
                from: baseURL.appendingPathComponent("status"))
            let status = try JSONDecoder().decode(AvatarStatus.self, from: response.0)
            await MainActor.run {
                // Trigger notification if state changed
                if self.currentState != status.state {
                    AvatarNotificationService.shared.notifyMorph(
                        from: self.currentState ?? .ghost,
                        to: status.state,
                        awarenessLevel: status.awarenessLevel
                    )
                    self.previousState = self.currentState
                }

                self.currentState = status.state
                self.lastAwarenessLevel = status.awarenessLevel
                self.isHealthy = status.healthy
            }
        } catch {
            await MainActor.run {
                self.isHealthy = false
                AvatarNotificationService.shared.notifyError(
                    "Status check failed: \(error.localizedDescription)")
            }
        }
    }

    func morph(to mode: AvatarMode) async throws -> Bool {
        let fromMode = currentState ?? .ghost
        let startTime = Date()

        if mockMode {
            // Simulate morphing in fast-track mode
            try await Task.sleep(nanoseconds: 2_000_000_000)  // 2 second delay
            let _ = Date().timeIntervalSince(startTime)

            await MainActor.run {
                // MobileMetricsService.shared.trackAvatarSwitch(target: mode, success: true, duration: duration)
                self.previousState = self.currentState
                self.currentState = mode
                self.lastAwarenessLevel = mode == .photoreal ? 0.8 : 0.2  // Simulate awareness change
                AvatarNotificationService.shared.notifyMorph(from: fromMode, to: mode)
            }
            return true
        }

        let requestBody = AvatarMorphRequest(to: mode)
        let data = try JSONEncoder().encode(requestBody)

        // Use auth interceptor for mobile requests
        let interceptor = AuthInterceptor()
        var request = URLRequest(url: baseURL.appendingPathComponent("switch"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = data

        // Apply authentication
        request = try await interceptor.intercept(request: request)

        do {
            let (responseData, response) = try await URLSession.shared.data(for: request)
            let _ = Date().timeIntervalSince(startTime)

            if let httpResponse = response as? HTTPURLResponse,
                !(200..<300).contains(httpResponse.statusCode)
            {
                await MainActor.run {
                    AvatarNotificationService.shared.notifyError(
                        "Morph failed: HTTP \(httpResponse.statusCode)")
                    // MobileMetricsService.shared.trackAvatarSwitch(target: mode, success: false, duration: duration)
                }
                return false
            }

            let result = try JSONDecoder().decode(AvatarMorphResponse.self, from: responseData)

            await MainActor.run {
                MobileMetricsService.shared.trackAvatarSwitch(
                    target: mode, success: result.success, duration: 0.0)
                // MobileMetricsService.shared.trackAPILatency(endpoint: "avatar/switch", duration: duration, statusCode: 200)

                if result.success {
                    self.previousState = self.currentState
                    self.currentState = mode
                    AvatarNotificationService.shared.notifyMorph(from: fromMode, to: mode)
                } else {
                    AvatarNotificationService.shared.notifyError(
                        "Morph rejected: \(result.message ?? "Unknown error")")
                }
            }

            return result.success
        } catch {
            let _ = Date().timeIntervalSince(startTime)
            await MainActor.run {
                AvatarNotificationService.shared.notifyError(
                    "Morph failed: \(error.localizedDescription)", isCritical: false)
                MobileMetricsService.shared.trackAvatarSwitch(
                    target: mode, success: false, duration: 0.0)
                MobileMetricsService.shared.trackAvatarSwitchFailure(
                    reason: error.localizedDescription)
            }
            throw error
        }
    }

    /// Test LAN connectivity for mobile devices
    func testLANConnectivity() async -> Bool {
        if mockMode {
            // Simulate connectivity test in fast-track mode
            try? await Task.sleep(nanoseconds: 500_000_000)  // 0.5 second delay
            return true  // Always succeed in mock mode
        }

        // Try to connect to a known endpoint
        do {
            let testURL = baseURL.appendingPathComponent("health")
            let (_, response) = try await URLSession.shared.data(from: testURL)
            return (response as? HTTPURLResponse)?.statusCode == 200
        } catch {
            return false
        }
    }
}

// Avatar types moved to AvatarKit/AvatarTypes.swift - using those
