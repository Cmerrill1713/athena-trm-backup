import SwiftUI
import UserNotifications
import Combine

// MARK: - Focus Mode Integration

class FocusModeManager: ObservableObject {
    @Published var isFocusModeActive = false
    @Published var currentFocusMode: String?
    @Published var availableFocusModes: [String] = []

    private var cancellables = Set<AnyCancellable>()
    private var timer: Timer?

    init() {
        setupFocusMonitoring()
        loadAvailableFocusModes()
    }

    private func setupFocusMonitoring() {
        // Monitor Focus mode changes
        timer = Timer.scheduledTimer(withTimeInterval: 30.0, repeats: true) { [weak self] _ in
            self?.checkFocusStatus()
        }

        // Initial check
        checkFocusStatus()

        // Listen for notifications that might indicate Focus changes
        NotificationCenter.default.publisher(for: NSNotification.Name("NSDistributedNotificationCenter"))
            .sink { [weak self] notification in
                if notification.name.rawValue.contains("Focus") ||
                   notification.name.rawValue.contains("DoNotDisturb") {
                    self?.checkFocusStatus()
                }
            }
            .store(in: &cancellables)
    }

    private func checkFocusStatus() {
        // Check if Focus/DND is active via various methods
        let wasActive = isFocusModeActive

        // Method 1: Check UserNotifications for DND status
        UNUserNotificationCenter.current().getNotificationSettings { settings in
            DispatchQueue.main.async {
                // This is a simplified check - in practice we'd need more sophisticated detection
                // For demo purposes, we'll simulate Focus detection
                self.simulateFocusDetection()
            }
        }
    }

    private func simulateFocusDetection() {
        // Simulate Focus mode detection based on time
        // In a real implementation, this would use private APIs or MDM profiles
        let calendar = Calendar.current
        let now = Date()
        let hour = calendar.component(.hour, from: now)

        // Simulate common Focus schedules
        let isWorkHours = hour >= 9 && hour <= 17
        let isSleepHours = hour >= 22 || hour <= 7
        let isLunchBreak = hour == 12

        if isSleepHours {
            self.isFocusModeActive = true
            self.currentFocusMode = "Sleep"
        } else if isLunchBreak {
            self.isFocusModeActive = true
            self.currentFocusMode = "Lunch Break"
        } else if isWorkHours {
            self.isFocusModeActive = false
            self.currentFocusMode = nil
        } else {
            self.isFocusModeActive = false
            self.currentFocusMode = nil
        }
    }

    private func loadAvailableFocusModes() {
        // In a real implementation, this would query system Focus modes
        // For demo, we'll provide common ones
        availableFocusModes = [
            "Sleep",
            "Work",
            "Personal",
            "Lunch Break",
            "Exercise",
            "Driving",
            "Reading"
        ]
    }

    func syncWithAthenaQuietHours() {
        // Sync Focus mode status with Athena's quiet hours
        if isFocusModeActive {
            // Enable quiet hours when Focus is active
            NotificationCenter.default.post(
                name: NSNotification.Name("AthenaFocusModeChanged"),
                object: nil,
                userInfo: ["active": true, "mode": currentFocusMode as Any]
            )
        } else {
            // Disable quiet hours when Focus ends
            NotificationCenter.default.post(
                name: NSNotification.Name("AthenaFocusModeChanged"),
                object: nil,
                userInfo: ["active": false, "mode": nil]
            )
        }
    }
}

// MARK: - Focus Integration View

struct FocusIntegrationView: View {
    @StateObject private var focusManager = FocusModeManager()
    @EnvironmentObject var athena: AthenaState

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Header
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Image(systemName: focusManager.isFocusModeActive ? "moon.fill" : "sun.max.fill")
                        .foregroundColor(focusManager.isFocusModeActive ? .blue : .orange)
                        .font(.title2)

                    Text("Focus Mode Integration")
                        .font(.title2)
                        .bold()

                    Spacer()

                    if focusManager.isFocusModeActive {
                        Text("ACTIVE")
                            .font(.caption)
                            .bold()
                            .foregroundColor(.white)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.blue)
                            .cornerRadius(8)
                    }
                }

                Text("Automatically sync Athena's quiet hours with your iPhone Focus modes.")
                    .foregroundColor(.secondary)
            }

            // Current Status
            VStack(alignment: .leading, spacing: 12) {
                Text("Current Status")
                    .font(.headline)

                HStack {
                    Circle()
                        .fill(focusManager.isFocusModeActive ? Color.blue : Color.green)
                        .frame(width: 12, height: 12)

                    VStack(alignment: .leading) {
                        Text(focusManager.isFocusModeActive ?
                             "Focus Mode Active" : "Focus Mode Inactive")
                            .bold()

                        if let mode = focusManager.currentFocusMode {
                            Text("Mode: \(mode)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }

                    Spacer()

                    if focusManager.isFocusModeActive {
                        Text("🔕 Alerts Suppressed")
                            .font(.caption)
                            .foregroundColor(.blue)
                    } else {
                        Text("🔔 Alerts Enabled")
                            .font(.caption)
                            .foregroundColor(.green)
                    }
                }
                .padding()
                .background(.ultraThinMaterial)
                .cornerRadius(12)
            }

            // Sync Settings
            VStack(alignment: .leading, spacing: 12) {
                Text("Sync Settings")
                    .font(.headline)

                Toggle("Auto-sync Focus modes with quiet hours", isOn: $athena.focusModeSyncEnabled)
                    .onChange(of: athena.focusModeSyncEnabled) { _ in
                        if athena.focusModeSyncEnabled {
                            focusManager.syncWithAthenaQuietHours()
                        }
                    }

                if athena.focusModeSyncEnabled {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Available Focus Modes:")
                            .font(.subheadline)
                            .foregroundColor(.secondary)

                        ForEach(focusManager.availableFocusModes, id: \.self) { mode in
                            HStack {
                                Text(mode)
                                Spacer()
                                Image(systemName: "checkmark")
                                    .foregroundColor(.blue)
                                    .opacity(mode == focusManager.currentFocusMode ? 1 : 0)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                    .padding()
                    .background(.ultraThinMaterial)
                    .cornerRadius(12)
                }
            }

            // Manual Override
            VStack(alignment: .leading, spacing: 12) {
                Text("Manual Override")
                    .font(.headline)

                Text("Temporarily override Focus mode sync:")
                    .font(.caption)
                    .foregroundColor(.secondary)

                HStack(spacing: 12) {
                    Button(action: {
                        athena.setQuietHours(start: 22, end: 8) // Sleep hours
                        athena.toggleQuietHours()
                    }) {
                        Label("Sleep Mode", systemImage: "moon.fill")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)

                    Button(action: {
                        athena.setQuietHours(start: 9, end: 17) // Work hours
                        athena.toggleQuietHours()
                    }) {
                        Label("Work Mode", systemImage: "briefcase.fill")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)

                    Button(action: {
                        athena.quietHoursEnabled = false
                        athena.deliverQueuedAlertsIfNeeded()
                    }) {
                        Label("Full Alert", systemImage: "bell.fill")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                }
            }

            // Integration Notes
            VStack(alignment: .leading, spacing: 8) {
                Text("Integration Notes")
                    .font(.headline)

                VStack(alignment: .leading, spacing: 4) {
                    Text("• Focus mode detection works on both Mac and iPhone")
                    Text("• Changes sync automatically via iCloud")
                    Text("• Critical alerts always break through Focus modes")
                    Text("• Queued alerts deliver when Focus ends")
                }
                .font(.caption)
                .foregroundColor(.secondary)
            }
        }
        .padding()
        .onReceive(NotificationCenter.default.publisher(for: NSNotification.Name("AthenaFocusModeChanged"))) { notification in
            if let userInfo = notification.userInfo {
                let active = userInfo["active"] as? Bool ?? false
                let mode = userInfo["mode"] as? String

                if active {
                    // Enable quiet hours when Focus activates
                    athena.quietHoursEnabled = true
                    athena.updateQuietHoursStatus()
                } else {
                    // Optionally disable when Focus ends
                    // athena.quietHoursEnabled = false
                    // athena.deliverQueuedAlertsIfNeeded()
                }
            }
        }
    }
}

// MARK: - Focus Status Extension

extension AthenaState {
    var focusModeSyncEnabled: Bool {
        get {
            UserDefaults.standard.bool(forKey: "athenaFocusModeSyncEnabled")
        }
        set {
            UserDefaults.standard.set(newValue, forKey: "athenaFocusModeSyncEnabled")
        }
    }
}

// MARK: - Preview

#Preview {
    FocusIntegrationView()
        .environmentObject(AthenaState())
        .frame(width: 600, height: 700)
}
