import SwiftUI

// MARK: - Live Governance Dashboard

struct GovernanceDashboardLiveView: View {

    @StateObject private var viewModel = GovernanceViewModel()

    var body: some View {
        NavigationSplitView {
            // Sidebar
            List {
                Section("Status") {
                    HealthStatusRow(viewModel: viewModel)
                    PendingQueueRow(viewModel: viewModel)
                }

                Section("Actions") {
                    NavigationLink("Send Verdict") {
                        VerdictSubmissionView(viewModel: viewModel)
                    }

                    NavigationLink("View Metrics") {
                        MetricsDetailView(viewModel: viewModel)
                    }

                    NavigationLink("Settings") {
                        GovernanceSettingsView(viewModel: viewModel)
                    }
                }

                Section("Quick Actions") {
                    Button("Refresh Now") {
                        Task {
                            await viewModel.refresh()
                        }
                    }
                    .disabled(viewModel.isLoading)

                    Button("Send Demo Verdict") {
                        Task {
                            await viewModel.sendDemoVerdict()
                        }
                    }
                    .disabled(viewModel.healthStatus != .healthy)
                }
            }
            .navigationTitle("Governance")
            .listStyle(.sidebar)
        } detail: {
            // Main content
            VStack(spacing: 20) {
                // Health indicator
                GovernanceHealthBanner(viewModel: viewModel)

                // Verdict counts
                VerdictCountsCard(viewModel: viewModel)

                // Remediation metrics
                if let metrics = viewModel.remediationMetrics {
                    RemediationMetricsCard(metrics: metrics)
                }

                Spacer()
            }
            .padding()
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color(.windowBackgroundColor))
        }
        .task {
            await viewModel.checkHealth()
            await viewModel.refreshMetrics()
        }
    }
}

// MARK: - Health Status Row

struct HealthStatusRow: View {
    @ObservedObject var viewModel: GovernanceViewModel

    var body: some View {
        HStack {
            Text(viewModel.healthStatus.rawValue)
                .font(.title2)

            VStack(alignment: .leading, spacing: 4) {
                Text("Orchestrator")
                    .font(.headline)
                Text(viewModel.statusMessage)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            if viewModel.isLoading {
                ProgressView()
                    .scaleEffect(0.7)
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Pending Queue Row

struct PendingQueueRow: View {
    @ObservedObject var viewModel: GovernanceViewModel

    var body: some View {
        if !viewModel.pendingVerdicts.isEmpty {
            HStack {
                Image(systemName: "tray.full")
                    .foregroundColor(.orange)

                VStack(alignment: .leading) {
                    Text("Pending Verdicts")
                        .font(.headline)
                    Text("\(viewModel.pendingVerdicts.count) queued")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()

                if viewModel.healthStatus == .healthy {
                    Button("Flush") {
                        Task {
                            await viewModel.refresh()
                        }
                    }
                    .buttonStyle(.bordered)
                }
            }
            .padding(.vertical, 4)
        }
    }
}

// MARK: - Health Banner

struct GovernanceHealthBanner: View {
    @ObservedObject var viewModel: GovernanceViewModel

    var body: some View {
        HStack {
            Text(viewModel.healthStatus.rawValue)
                .font(.system(size: 48))

            VStack(alignment: .leading, spacing: 8) {
                Text("Governance Orchestrator")
                    .font(.title)
                    .fontWeight(.bold)

                Text(viewModel.statusMessage)
                    .font(.body)
                    .foregroundColor(.secondary)

                if let error = viewModel.lastError {
                    Text("Error: \(error)")
                        .font(.caption)
                        .foregroundColor(.red)
                }
            }

            Spacer()

            Button {
                Task {
                    await viewModel.checkHealthDetailed()
                }
            } label: {
                Image(systemName: "arrow.clockwise")
                    .font(.title2)
            }
            .buttonStyle(.bordered)
            .disabled(viewModel.isLoading)
        }
        .padding()
        .background(viewModel.healthStatus.color.opacity(0.1))
        .cornerRadius(12)
    }
}

// MARK: - Verdict Counts Card

struct VerdictCountsCard: View {
    @ObservedObject var viewModel: GovernanceViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Verdict Counts")
                .font(.headline)

            if viewModel.verdictCounts.isEmpty {
                Text("No verdicts recorded yet")
                    .foregroundColor(.secondary)
                    .padding(.vertical, 20)
            } else {
                LazyVGrid(
                    columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                    ], spacing: 16
                ) {
                    ForEach(
                        Array(viewModel.verdictCounts.sorted(by: { $0.key < $1.key })), id: \.key
                    ) { key, value in
                        VerdictCountBadge(type: key, count: value)
                    }
                }
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.controlBackgroundColor))
        .cornerRadius(12)
    }
}

struct VerdictCountBadge: View {
    let type: String
    let count: Int

    var color: Color {
        switch type.lowercased() {
        case "pass": return .green
        case "soft_fail", "soft-fail": return .yellow
        case "hard_fail", "hard-fail": return .red
        default: return .gray
        }
    }

    var body: some View {
        VStack(spacing: 8) {
            Text("\(count)")
                .font(.system(size: 32, weight: .bold))
                .foregroundColor(color)

            Text(type.uppercased())
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(color.opacity(0.1))
        .cornerRadius(8)
    }
}

// MARK: - Remediation Metrics Card

struct RemediationMetricsCard: View {
    let metrics: GovernanceClient.RemediationMetrics

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Auto-Remediation")
                .font(.headline)

            LazyVGrid(
                columns: [
                    GridItem(.flexible()),
                    GridItem(.flexible()),
                ], spacing: 12
            ) {
                MetricBadge(label: "Requested", value: metrics.requested, color: .blue)
                MetricBadge(label: "Completed", value: metrics.completed, color: .green)
                MetricBadge(label: "Promoted", value: metrics.promoted, color: .purple)
                MetricBadge(label: "Rolled Back", value: metrics.rolledBack, color: .orange)
                MetricBadge(label: "Failed", value: metrics.failed, color: .red)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.controlBackgroundColor))
        .cornerRadius(12)
    }
}

struct MetricBadge: View {
    let label: String
    let value: Int
    let color: Color

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(label)
                    .font(.caption)
                    .foregroundColor(.secondary)
                Text("\(value)")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(color)
            }
            Spacer()
        }
        .padding(8)
        .background(color.opacity(0.1))
        .cornerRadius(6)
    }
}

// MARK: - Verdict Submission View

struct VerdictSubmissionView: View {
    @ObservedObject var viewModel: GovernanceViewModel

    @State private var taskId: String = ""
    @State private var selectedVerdict: String = "PASS"
    @State private var selectedActions: Set<String> = ["PROMOTE"]

    let verdictTypes = ["PASS", "SOFT_FAIL", "HARD_FAIL"]
    let actionTypes = ["PROMOTE", "HOLD", "QUARANTINE", "ROLLBACK", "FREEZE"]

    var body: some View {
        Form {
            Section("Verdict Details") {
                TextField(
                    "Task ID", text: $taskId,
                    prompt: Text("ui-custom-\(Int(Date().timeIntervalSince1970))"))

                Picker("Verdict Type", selection: $selectedVerdict) {
                    ForEach(verdictTypes, id: \.self) { type in
                        Text(type).tag(type)
                    }
                }
            }

            Section("Actions") {
                ForEach(actionTypes, id: \.self) { action in
                    Toggle(
                        action,
                        isOn: Binding(
                            get: { selectedActions.contains(action) },
                            set: { isSelected in
                                if isSelected {
                                    selectedActions.insert(action)
                                } else {
                                    selectedActions.remove(action)
                                }
                            }
                        ))
                }
            }

            Section {
                Button("Submit Verdict") {
                    Task {
                        let id =
                            taskId.isEmpty
                            ? "ui-custom-\(Int(Date().timeIntervalSince1970))" : taskId
                        await viewModel.sendCustomVerdict(
                            taskId: id,
                            verdict: selectedVerdict,
                            actions: Array(selectedActions)
                        )
                    }
                }
                .disabled(viewModel.healthStatus != .healthy || viewModel.isLoading)

                if viewModel.healthStatus != .healthy {
                    Text("⚠️ Orchestrator unavailable")
                        .font(.caption)
                        .foregroundColor(.orange)
                }
            }

            if let lastVerdict = viewModel.lastVerdict {
                Section("Last Response") {
                    LabeledContent("Status", value: lastVerdict.status)
                    if let taskId = lastVerdict.task_id {
                        LabeledContent("Task ID", value: taskId)
                    }
                    if let generation = lastVerdict.generation {
                        LabeledContent("Generation", value: "\(generation)")
                    }
                }
            }
        }
        .formStyle(.grouped)
        .navigationTitle("Submit Verdict")
    }
}

// MARK: - Metrics Detail View

struct MetricsDetailView: View {
    @ObservedObject var viewModel: GovernanceViewModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                VerdictCountsCard(viewModel: viewModel)

                if let metrics = viewModel.remediationMetrics {
                    RemediationMetricsCard(metrics: metrics)
                }

                Button("Refresh Metrics") {
                    Task {
                        await viewModel.refreshMetrics()
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(viewModel.isLoading)
            }
            .padding()
        }
        .navigationTitle("Metrics")
    }
}

// MARK: - Settings View

struct GovernanceSettingsView: View {
    @ObservedObject var viewModel: GovernanceViewModel

    var body: some View {
        Form {
            Section("Connection") {
                LabeledContent("Orchestrator URL") {
                    Text(ProcessInfo.processInfo.environment["GOV_URL"] ?? "http://localhost:9110")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            Section("Auto-Refresh") {
                Toggle("Enable Auto-Refresh", isOn: $viewModel.autoRefresh)
                    .onChange(of: viewModel.autoRefresh) { oldValue, newValue in
                        if newValue {
                            viewModel.startAutoRefresh()
                        } else {
                            viewModel.stopAutoRefresh()
                        }
                    }

                if viewModel.autoRefresh {
                    LabeledContent("Refresh Interval") {
                        Text("\(Int(viewModel.refreshInterval))s")
                    }
                }
            }

            Section("Queue") {
                LabeledContent("Pending Verdicts", value: "\(viewModel.pendingVerdicts.count)")

                if !viewModel.pendingVerdicts.isEmpty {
                    Button("Clear Queue") {
                        viewModel.pendingVerdicts.removeAll()
                    }
                    .foregroundColor(.red)
                }
            }
        }
        .formStyle(.grouped)
        .navigationTitle("Settings")
    }
}

// MARK: - Preview

#Preview("Dashboard") {
    GovernanceDashboardLiveView()
        .frame(width: 900, height: 600)
}

#Preview("Health Banner - Healthy") {
    GovernanceHealthBanner(
        viewModel: {
            let vm = GovernanceViewModel()
            vm.healthStatus = .healthy
            vm.statusMessage = "🟢 Orchestrator healthy"
            return vm
        }()
    )
    .padding()
}

#Preview("Verdict Counts") {
    VerdictCountsCard(
        viewModel: {
            let vm = GovernanceViewModel()
            vm.verdictCounts = ["pass": 193, "soft_fail": 12, "hard_fail": 5]
            return vm
        }()
    )
    .padding()
}
