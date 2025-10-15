import SwiftUI

// MARK: - Calendar Integration View

struct CalendarIntegrationView: View {
    @EnvironmentObject var athena: AthenaState

    @State private var calendarSyncEnabled = false
    @State private var currentEvent: String? = nil
    @State private var upcomingEvents: [String] = []
    @State private var isMonitoring = false
    @State private var predictiveEvent: String? = nil
    @State private var minutesUntilEvent: Double? = nil
    @State private var predictiveLeadTime: Int = 5

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Header
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Image(systemName: calendarSyncEnabled ? "calendar.circle.fill" : "calendar.circle")
                        .foregroundColor(calendarSyncEnabled ? .blue : .secondary)
                        .font(.title2)

                    Text("Calendar Integration")
                        .font(.title2)
                        .bold()

                    Spacer()

                    if calendarSyncEnabled {
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

                Text("Automatically enable quiet hours during Calendar meetings and focus time.")
                    .foregroundColor(.secondary)
            }

            // Current Status
            VStack(alignment: .leading, spacing: 12) {
                Text("Current Status")
                    .font(.headline)

                HStack {
                    Circle()
                        .fill(calendarSyncEnabled ? Color.blue : Color.gray)
                        .frame(width: 12, height: 12)

                    VStack(alignment: .leading) {
                        Text(calendarSyncEnabled ? "Calendar Sync Active" : "Calendar Sync Disabled")
                            .bold()

                        if let event = currentEvent {
                            Text("Active Event: \(event)")
                                .font(.caption)
                                .foregroundColor(.blue)
                        } else if let predictive = predictiveEvent, let minutes = minutesUntilEvent {
                            Text("🔮 Predictive: \(predictive)")
                                .font(.caption)
                                .foregroundColor(.orange)
                            Text("Starts in \(String(format: "%.1f", minutes)) min")
                                .font(.caption)
                                .foregroundColor(.orange)
                        } else if calendarSyncEnabled {
                            Text("Monitoring for upcoming events")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }

                    Spacer()

                    if calendarSyncEnabled && currentEvent != nil {
                        Text("🔕 Alerts Suppressed")
                            .font(.caption)
                            .foregroundColor(.blue)
                    } else {
                        Text("🔔 Alerts Normal")
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

                Toggle("Auto-sync Calendar events with quiet hours", isOn: $calendarSyncEnabled)
                    .onChange(of: calendarSyncEnabled) { _ in
                        updateCalendarSync()
                    }

                if calendarSyncEnabled {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Event Types That Trigger Quiet Hours:")
                            .font(.subheadline)
                            .foregroundColor(.secondary)

                        VStack(alignment: .leading, spacing: 6) {
                            Label("Meetings (standup, review, demo)", systemImage: "person.2.fill")
                            Label("Focus time blocks", systemImage: "brain.head.profile")
                            Label("Presentations and calls", systemImage: "phone.fill")
                        }
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding()
                        .background(.ultraThinMaterial.opacity(0.5))
                        .cornerRadius(8)

                        Text("Events excluded: lunch breaks, personal time, exercise")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .italic()
                    }

                    // Predictive Settings
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Image(systemName: "crystalball.fill")
                                .foregroundColor(.orange)
                            Text("Predictive Pre-Quiet")
                                .font(.subheadline)
                                .bold()
                        }

                        VStack(alignment: .leading, spacing: 6) {
                            Text("Automatically enable quiet hours before events start")
                                .font(.caption)
                                .foregroundColor(.secondary)

                            HStack {
                                Text("Lead time:")
                                Text("\(predictiveLeadTime) minutes")
                                    .bold()
                                    .foregroundColor(.orange)
                            }
                            .font(.caption)

                            if let predictive = predictiveEvent {
                                HStack {
                                    Circle()
                                        .fill(Color.orange)
                                        .frame(width: 8, height: 8)
                                    Text("Pre-quiet active for: \(predictive)")
                                        .font(.caption)
                                        .foregroundColor(.orange)
                                }
                            } else {
                                HStack {
                                    Circle()
                                        .fill(Color.gray.opacity(0.5))
                                        .frame(width: 8, height: 8)
                                    Text("Monitoring for upcoming events")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                            }
                        }
                        .padding()
                        .background(.ultraThinMaterial.opacity(0.5))
                        .cornerRadius(8)
                    }
                }
            }

            // Upcoming Events Preview
            if calendarSyncEnabled {
                VStack(alignment: .leading, spacing: 12) {
                    Text("Upcoming Events")
                        .font(.headline)

                    if upcomingEvents.isEmpty {
                        Text("No upcoming events in next 30 minutes")
                            .foregroundColor(.secondary)
                            .italic()
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(.ultraThinMaterial.opacity(0.5))
                            .cornerRadius(8)
                    } else {
                        ForEach(upcomingEvents, id: \.self) { event in
                            HStack {
                                Image(systemName: "clock.fill")
                                    .foregroundColor(.orange)
                                Text(event)
                                    .lineLimit(1)
                                Spacer()
                                Text("Will auto-enable quiet hours")
                                    .font(.caption)
                                    .foregroundColor(.blue)
                            }
                            .padding(.vertical, 4)
                        }
                        .padding()
                        .background(.ultraThinMaterial.opacity(0.5))
                        .cornerRadius(8)
                    }
                }
            }

            // Manual Override
            VStack(alignment: .leading, spacing: 12) {
                Text("Manual Override")
                    .font(.headline)

                Text("Force quiet hours for scheduled events:")
                    .font(.caption)
                    .foregroundColor(.secondary)

                HStack(spacing: 12) {
                    Button(action: {
                        // Simulate meeting start
                        currentEvent = "Team Standup Meeting"
                        updateCalendarSync()
                    }) {
                        Label("Meeting Mode", systemImage: "person.2.fill")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)

                    Button(action: {
                        // Simulate focus time
                        currentEvent = "Deep Focus Session"
                        updateCalendarSync()
                    }) {
                        Label("Focus Mode", systemImage: "brain.head.profile")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)

                    Button(action: {
                        // Clear all calendar events
                        currentEvent = nil
                        updateCalendarSync()
                    }) {
                        Label("Clear Events", systemImage: "xmark.circle.fill")
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
                    Text("• Monitors macOS Calendar app events in real-time")
                    Text("• Automatically detects meetings, calls, and focus sessions")
                    Text("• Critical alerts always break through during events")
                    Text("• Works alongside Focus mode integration")
                    Text("• Manual override available for testing")
                }
                .font(.caption)
                .foregroundColor(.secondary)
            }
        }
        .padding()
        .onAppear {
            loadCalendarStatus()
            startCalendarMonitoring()
        }
    }

    private func updateCalendarSync() {
        // Update Athena API with calendar sync status
        let payload: [String: Any] = [
            "calendar_event": currentEvent as Any,
            "source": "dashboard"
        ]

        // Send to Athena API (would use actual networking in real implementation)
        NotificationCenter.default.post(
            name: NSNotification.Name("AthenaCalendarSyncChanged"),
            object: nil,
            userInfo: payload
        )

        print("📅 Calendar sync updated: \(currentEvent ?? "No active events")")
    }

    private func loadCalendarStatus() {
        // Load current calendar sync status
        calendarSyncEnabled = UserDefaults.standard.bool(forKey: "athenaCalendarSyncEnabled")

        // Simulate some upcoming events for demo
        if calendarSyncEnabled {
            upcomingEvents = [
                "Client Presentation at 2:00 PM",
                "Team Standup at 3:30 PM"
            ]
        }
    }

    private func startCalendarMonitoring() {
        // Simulate calendar monitoring
        Timer.scheduledTimer(withTimeInterval: 60.0, repeats: true) { _ in
            // In a real implementation, this would check actual Calendar events
            // For demo purposes, we simulate occasional events

            let shouldTriggerEvent = Bool.random() && Bool.random() // ~25% chance

            if shouldTriggerEvent && calendarSyncEnabled && currentEvent == nil {
                let events = ["Team Standup", "Client Call", "Code Review", "Planning Meeting"]
                currentEvent = events.randomElement()
                updateCalendarSync()
            }
        }
    }
}

// MARK: - Calendar Status Extension

extension AthenaState {
    var calendarSyncEnabled: Bool {
        get {
            UserDefaults.standard.bool(forKey: "athenaCalendarSyncEnabled")
        }
        set {
            UserDefaults.standard.set(newValue, forKey: "athenaCalendarSyncEnabled")
        }
    }
}

// MARK: - Preview

#Preview {
    CalendarIntegrationView()
        .environmentObject(AthenaState())
        .frame(width: 600, height: 700)
}
