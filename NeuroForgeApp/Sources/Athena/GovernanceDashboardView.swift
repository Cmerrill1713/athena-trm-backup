import SwiftUI

/// Governance Dashboard - Shows KPIs, Mode Control, Alerts
struct GovernanceDashboardView: View {
    @EnvironmentObject var state: AthenaState
    
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Header with health status
            HStack {
                Circle()
                    .fill(state.isOrchestratorHealthy ? .green : .red)
                    .frame(width: 12, height: 12)
                Text("Governance Orchestrator")
                    .font(.title2.bold())
                
                Spacer()
                
                Button(action: {
                    Task { await state.refreshGovernance() }
                }) {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
            }
            
            // Mode Switcher
            ModeSwitcherView()
            
            Divider()
            
            // KPI Grid
            KPIGridView()
            
            Divider()
            
            // Alerts
            if !state.governanceAlerts.isEmpty {
                GovernanceAlertsView()
                Divider()
            }
            
            // Quick Actions
            QuickActionsView()
            
            // Error Display
            if let error = state.lastError {
                Text(error)
                    .foregroundStyle(.red)
                    .font(.caption)
                    .padding(8)
                    .background(Color.red.opacity(0.1))
                    .cornerRadius(6)
            }
            
            Spacer()
        }
        .padding(24)
        .frame(minWidth: 900, minHeight: 600)
        .onAppear {
            state.startGovernanceMonitoring()
        }
        .onDisappear {
            state.stopGovernanceMonitoring()
        }
    }
}

// MARK: - Mode Switcher

private struct ModeSwitcherView: View {
    @EnvironmentObject var state: AthenaState
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Governance Mode")
                .font(.headline)
            
            Picker("", selection: Binding(
                get: { state.governanceMode },
                set: { newMode in
                    Task { await state.setGovernanceMode(newMode) }
                }
            )) {
                ForEach(GovernanceMode.allCases) { mode in
                    VStack(alignment: .leading, spacing: 2) {
                        Text(mode.displayName)
                            .font(.headline)
                        Text(mode.description)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .tag(mode)
                }
            }
            .pickerStyle(.segmented)
            
            // Mode description
            HStack {
                Image(systemImage: modeIcon)
                    .foregroundStyle(modeColor)
                Text(state.governanceMode.description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(Color(.controlBackgroundColor))
        .cornerRadius(8)
    }
    
    private var modeIcon: String {
        switch state.governanceMode {
        case .shadow: return "eye.fill"
        case .canary: return "bird.fill"
        case .enforce: return "shield.fill"
        }
    }
    
    private var modeColor: Color {
        switch state.governanceMode {
        case .shadow: return .blue
        case .canary: return .yellow
        case .enforce: return .green
        }
    }
}

// MARK: - KPI Grid

private struct KPIGridView: View {
    @EnvironmentObject var state: AthenaState
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Key Performance Indicators")
                .font(.headline)
            
            Grid(alignment: .leading, horizontalSpacing: 20, verticalSpacing: 16) {
                GridRow {
                    KPICard(
                        title: "ECE",
                        value: state.kpis.ece.isNaN ? "—" : String(format: "%.3f", state.kpis.ece),
                        subtitle: "Expected Calibration Error",
                        status: eceStatus,
                        icon: "chart.line.uptrend.xyaxis"
                    )
                    
                    KPICard(
                        title: "Entropy",
                        value: state.kpis.entropy.isNaN ? "—" : String(format: "%.3f", state.kpis.entropy),
                        subtitle: "System Entropy Drift",
                        status: entropyStatus,
                        icon: "waveform.path.ecg"
                    )
                    
                    KPICard(
                        title: "Verdicts",
                        value: "\(state.kpis.verdicts_5m)",
                        subtitle: "Last 5 minutes",
                        status: .normal,
                        icon: "checkmark.seal.fill"
                    )
                }
                
                GridRow {
                    KPICard(
                        title: "Actions",
                        value: "\(state.kpis.actions_5m)",
                        subtitle: "Executed actions",
                        status: .normal,
                        icon: "bolt.fill"
                    )
                    
                    KPICard(
                        title: "Hard Fails",
                        value: "\(state.kpis.hard_fails_5m)",
                        subtitle: "Critical verdicts",
                        status: state.kpis.hard_fails_5m > 0 ? .warning : .normal,
                        icon: "exclamationmark.triangle.fill"
                    )
                    
                    KPICard(
                        title: "Status",
                        value: state.lastVerdictStatus.isEmpty ? "Ready" : state.lastVerdictStatus,
                        subtitle: "Last verdict",
                        status: .normal,
                        icon: "info.circle.fill"
                    )
                }
            }
        }
    }
    
    private var eceStatus: KPIStatus {
        if state.kpis.ece > 0.08 { return .critical }
        if state.kpis.ece > 0.06 { return .warning }
        return .normal
    }
    
    private var entropyStatus: KPIStatus {
        if state.kpis.entropy >= 0.25 { return .critical }
        return .normal
    }
}

private enum KPIStatus {
    case normal, warning, critical
    
    var color: Color {
        switch self {
        case .normal: return .green
        case .warning: return .orange
        case .critical: return .red
        }
    }
}

private struct KPICard: View {
    let title: String
    let value: String
    let subtitle: String
    let status: KPIStatus
    let icon: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemImage: icon)
                    .foregroundStyle(status.color)
                Text(title)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            
            Text(value)
                .font(.system(size: 28, weight: .bold, design: .rounded))
                .foregroundStyle(status.color)
            
            Text(subtitle)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(minWidth: 150, alignment: .leading)
        .padding()
        .background(Color(.controlBackgroundColor))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(status.color.opacity(0.3), lineWidth: 2)
        )
    }
}

// MARK: - Alerts View

private struct GovernanceAlertsView: View {
    @EnvironmentObject var state: AthenaState
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Active Alerts")
                .font(.headline)
            
            ForEach(state.governanceAlerts) { alert in
                HStack(spacing: 12) {
                    Image(systemImage: alertIcon(for: alert.severity))
                        .foregroundStyle(alertColor(for: alert.severity))
                    
                    VStack(alignment: .leading, spacing: 4) {
                        Text(alert.message)
                            .font(.body)
                        Text(alert.timestamp, style: .relative)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    
                    Spacer()
                }
                .padding(12)
                .background(alertColor(for: alert.severity).opacity(0.1))
                .cornerRadius(8)
            }
        }
    }
    
    private func alertIcon(for severity: AlertSeverity) -> String {
        switch severity {
        case .info: return "info.circle.fill"
        case .warning: return "exclamationmark.triangle.fill"
        case .critical: return "exclamationmark.octagon.fill"
        }
    }
    
    private func alertColor(for severity: AlertSeverity) -> Color {
        switch severity {
        case .info: return .blue
        case .warning: return .orange
        case .critical: return .red
        }
    }
}

// MARK: - Quick Actions

private struct QuickActionsView: View {
    @EnvironmentObject var state: AthenaState
    @State private var showingVerdictSheet = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Quick Actions")
                .font(.headline)
            
            HStack(spacing: 12) {
                Button(action: {
                    Task {
                        await state.sendTestVerdict(
                            verdict: "PASS",
                            ecePost: 0.03,
                            entropy: 0.05,
                            actions: ["PROMOTE"]
                        )
                    }
                }) {
                    Label("Send PASS", systemImage: "checkmark.circle.fill")
                }
                .buttonStyle(.borderedProminent)
                .tint(.green)
                
                Button(action: {
                    Task {
                        await state.sendTestVerdict(
                            verdict: "SOFT_FAIL",
                            ecePost: 0.07,
                            entropy: 0.15,
                            actions: ["HOLD"]
                        )
                    }
                }) {
                    Label("Send SOFT_FAIL", systemImage: "exclamationmark.circle.fill")
                }
                .buttonStyle(.borderedProminent)
                .tint(.orange)
                
                Button(action: {
                    Task {
                        await state.sendTestVerdict(
                            verdict: "HARD_FAIL",
                            ecePost: 0.09,
                            entropy: 0.30,
                            actions: ["ROLLBACK"]
                        )
                    }
                }) {
                    Label("Send HARD_FAIL", systemImage: "xmark.octagon.fill")
                }
                .buttonStyle(.borderedProminent)
                .tint(.red)
                
                Divider()
                
                Button(action: {
                    showingVerdictSheet = true
                }) {
                    Label("Custom Verdict", systemImage: "slider.horizontal.3")
                }
                .buttonStyle(.bordered)
            }
        }
        .sheet(isPresented: $showingVerdictSheet) {
            CustomVerdictSheet()
                .environmentObject(state)
        }
    }
}

// MARK: - Custom Verdict Sheet

private struct CustomVerdictSheet: View {
    @EnvironmentObject var state: AthenaState
    @Environment(\.dismiss) var dismiss
    
    @State private var verdict: String = "PASS"
    @State private var ecePost: Double = 0.03
    @State private var entropy: Double = 0.05
    @State private var selectedActions: Set<String> = ["PROMOTE"]
    
    private let verdictOptions = ["PASS", "SOFT_FAIL", "HARD_FAIL"]
    private let actionOptions = ["PROMOTE", "HOLD", "ROLLBACK", "QUARANTINE", "FREEZE_PROMOTIONS"]
    
    var body: some View {
        NavigationStack {
            Form {
                Section("Verdict Type") {
                    Picker("Type", selection: $verdict) {
                        ForEach(verdictOptions, id: \.self) { option in
                            Text(option).tag(option)
                        }
                    }
                    .pickerStyle(.segmented)
                }
                
                Section("Metrics") {
                    HStack {
                        Text("ECE Post:")
                        Spacer()
                        TextField("0.03", value: $ecePost, format: .number)
                            .frame(width: 100)
                    }
                    
                    HStack {
                        Text("Entropy:")
                        Spacer()
                        TextField("0.05", value: $entropy, format: .number)
                            .frame(width: 100)
                    }
                }
                
                Section("Actions") {
                    ForEach(actionOptions, id: \.self) { action in
                        Toggle(action, isOn: Binding(
                            get: { selectedActions.contains(action) },
                            set: { isOn in
                                if isOn {
                                    selectedActions.insert(action)
                                } else {
                                    selectedActions.remove(action)
                                }
                            }
                        ))
                    }
                }
            }
            .navigationTitle("Custom Verdict")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .confirmationAction) {
                    Button("Send") {
                        Task {
                            await state.sendTestVerdict(
                                verdict: verdict,
                                ecePost: ecePost,
                                entropy: entropy,
                                actions: Array(selectedActions)
                            )
                            dismiss()
                        }
                    }
                    .disabled(selectedActions.isEmpty)
                }
            }
        }
        .frame(width: 500, height: 600)
    }
}

// MARK: - Preview

#if DEBUG
struct GovernanceDashboardView_Previews: PreviewProvider {
    static var previews: some View {
        GovernanceDashboardView()
            .environmentObject(AthenaState())
    }
}
#endif

