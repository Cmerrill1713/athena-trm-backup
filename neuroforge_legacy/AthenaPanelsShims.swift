import SwiftUI

// MARK: - Minimal shims for legacy panels/views
// These compile and keep the app running while we finish the refactor.
// Remove this file once the new views replace all references.

@MainActor
private struct _ShimCard: View {
    let title: String
    var body: some View {
        VStack(spacing: 8) {
            Text(title).font(.headline)
            Text("Temporarily shimmed. Refactor in progress.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, minHeight: 120)
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
    }
}

// If any of these types are still referenced, these shims satisfy the compiler.

public struct AthenaAlertsPanel: View {
    public init() {}
    public var body: some View { _ShimCard(title: "Athena Alerts Panel") }
}

public struct AthenaControlsPanel: View {
    public init() {}
    public var body: some View { _ShimCard(title: "Athena Controls Panel") }
}

public struct AthenaMetricsPanel: View {
    public init() {}
    public var body: some View { _ShimCard(title: "Athena Metrics Panel") }
}

public struct AthenaStatusPanel: View {
    public init() {}
    public var body: some View { _ShimCard(title: "Athena Status Panel") }
}

public struct ModernChatView: View {
    public init() {}
    public var body: some View { _ShimCard(title: "Modern Chat View") }
}

public struct ChatView: View {
    public init() {}
    public var body: some View { _ShimCard(title: "Chat View") }
}

public struct ChatViewEnhanced: View {
    public init() {}
    public var body: some View { _ShimCard(title: "Chat View (Enhanced)") }
}

// If OpsWindow was an AppKit window wrapper, use a neutral SwiftUI stub:
public struct OpsWindow: View {
    public init() {}
    public var body: some View { _ShimCard(title: "Ops Window") }
}

// Additional shims for other potential conflicts
public struct BehavioralLearningView: View {
    public init() {}
    public var body: some View { _ShimCard(title: "Behavioral Learning") }
}

public struct CalendarIntegrationView: View {
    public init() {}
    public var body: some View { _ShimCard(title: "Calendar Integration") }
}

public struct FocusIntegrationView: View {
    public init() {}
    public var body: some View { _ShimCard(title: "Focus Integration") }
}

// OpsState shim
@MainActor
public class OpsState: ObservableObject {
    public init() {}
}

// Features shim
public struct Features {
    public static var modernUI: Bool { false }
}

// Additional type shims to satisfy any lingering references
public struct FirstRunWizardView: View {
    let onComplete: () -> Void
    public init(onComplete: @escaping () -> Void) {
        self.onComplete = onComplete
    }
    public var body: some View { _ShimCard(title: "First Run Wizard") }
}

public struct TracePanelView: View {
    public init() {}
    public var body: some View { _ShimCard(title: "Trace Panel") }
}

public struct SimpleOpsWindow: View {
    public init() {}
    public var body: some View { _ShimCard(title: "Simple Ops Window") }
}

public struct OpsSettingsView: View {
    public init() {}
    public var body: some View { _ShimCard(title: "Ops Settings") }
}

