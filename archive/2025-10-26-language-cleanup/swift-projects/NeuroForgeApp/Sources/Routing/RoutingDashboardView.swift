import Charts
import SwiftUI

/// Routing dashboard for Athena router monitoring
struct RoutingDashboardView: View {

    @StateObject private var routerClient = RouterClient()
    @State private var testQuery: String = ""
    @State private var selectedDomain: String = "general"
    @State private var routingResult: RoutingChoice?
    @State private var isRouting: Bool = false
    @State private var showError: Bool = false
    @State private var errorMessage: String = ""

    let domains = ["general", "code", "math"]

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Header
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Image(systemName: "arrow.triangle.branch")
                            .font(.title)
                            .foregroundColor(.accentColor)

                        Text("Routing Dashboard")
                            .font(.largeTitle)
                            .fontWeight(.bold)

                        Spacer()

                        // Health indicator
                        HStack(spacing: 6) {
                            Circle()
                                .fill(routerClient.isHealthy ? Color.green : Color.red)
                                .frame(width: 8, height: 8)

                            Text(routerClient.isHealthy ? "Healthy" : "Offline")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }

                    Text("Intelligent model routing for Athena")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .padding()

                Divider()

                // Test Query Section
                VStack(alignment: .leading, spacing: 12) {
                    Text("Test Routing")
                        .font(.headline)

                    HStack(spacing: 12) {
                        TextField("Enter a query to route...", text: $testQuery)
                            .textFieldStyle(.roundedBorder)
                            .frame(maxWidth: 400)

                        Picker("Domain", selection: $selectedDomain) {
                            ForEach(domains, id: \.self) { domain in
                                Text(domain.capitalized).tag(domain)
                            }
                        }
                        .pickerStyle(.segmented)
                        .frame(width: 250)

                        Button(action: routeQuery) {
                            if isRouting {
                                ProgressView()
                                    .controlSize(.small)
                            } else {
                                Label("Route", systemImage: "arrow.right.circle.fill")
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(testQuery.isEmpty || isRouting)
                    }

                    // Routing result
                    if let result = routingResult {
                        RoutingResultCard(result: result)
                    }
                }
                .padding()
                .background(Color(.controlBackgroundColor))
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .padding(.horizontal)

                // Available Models
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Available Models")
                            .font(.headline)

                        Spacer()

                        Button {
                            Task {
                                await loadModels()
                            }
                        } label: {
                            Label("Refresh", systemImage: "arrow.clockwise")
                                .font(.caption)
                        }
                        .buttonStyle(.bordered)
                    }

                    if routerClient.modelsAvailable.isEmpty {
                        Text("Loading models...")
                            .foregroundColor(.secondary)
                            .frame(maxWidth: .infinity, alignment: .center)
                            .padding()
                    } else {
                        LazyVStack(spacing: 8) {
                            ForEach(routerClient.modelsAvailable) { model in
                                ModelInfoCard(model: model)
                            }
                        }
                    }
                }
                .padding()
                .background(Color(.controlBackgroundColor))
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .padding(.horizontal)
            }
            .padding(.vertical)
        }
        .alert("Router Error", isPresented: $showError) {
            Button("OK") {}
        } message: {
            Text(errorMessage)
        }
        .task {
            Task {
                await checkHealth()
                await loadModels()
            }
        }
    }

    // MARK: - Actions

    private func checkHealth() async {
        do {
            _ = try await routerClient.checkHealth()
        } catch {
            errorMessage = error.localizedDescription
            showError = true
        }
    }

    private func loadModels() async {
        do {
            _ = try await routerClient.listModels()
        } catch {
            errorMessage = error.localizedDescription
            showError = true
        }
    }

    private func routeQuery() {
        Task {
            isRouting = true
            defer { isRouting = false }

            do {
                let result = try await routerClient.route(
                    query: testQuery,
                    domain: selectedDomain
                )
                routingResult = result
            } catch {
                errorMessage = error.localizedDescription
                showError = true
            }
        }
    }
}

// MARK: - Supporting Views

struct RoutingResultCard: View {
    let result: RoutingChoice

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Label("Routing Result", systemImage: "checkmark.circle.fill")
                    .font(.subheadline.weight(.semibold))
                    .foregroundColor(.green)

                Spacer()

                Text(String(format: "%.1fms", result.latencyMs))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Divider()

            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Model")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(result.model)
                        .font(.body.weight(.medium))
                }

                Spacer()

                VStack(alignment: .trailing, spacing: 4) {
                    Text("Confidence")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(String(format: "%.1f%%", result.confidence * 100))
                        .font(.body.weight(.medium))
                        .foregroundColor(confidenceColor(result.confidence))
                }

                Spacer()

                VStack(alignment: .trailing, spacing: 4) {
                    Text("Domain")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(result.domain.capitalized)
                        .font(.body.weight(.medium))
                }
            }
        }
        .padding()
        .background(Color.green.opacity(0.1))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private func confidenceColor(_ confidence: Double) -> Color {
        if confidence >= 0.8 {
            return .green
        } else if confidence >= 0.5 {
            return .orange
        } else {
            return .red
        }
    }
}

struct ModelInfoCard: View {
    let model: ModelInfo

    var body: some View {
        HStack(spacing: 12) {
            // Domain icon
            Circle()
                .fill(domainColor(model.domain))
                .frame(width: 40, height: 40)
                .overlay(
                    Image(systemName: domainIcon(model.domain))
                        .foregroundColor(.white)
                )

            // Model info
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(model.modelId)
                        .font(.body.weight(.medium))

                    if model.isApproximate {
                        Text("APPROX")
                            .font(.caption2)
                            .padding(.horizontal, 4)
                            .padding(.vertical, 2)
                            .background(Color.orange.opacity(0.2))
                            .foregroundColor(.orange)
                            .clipShape(Capsule())
                    }
                }

                HStack(spacing: 12) {
                    Label(model.domain.capitalized, systemImage: "tag")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Label(String(format: "%.2f", model.qualityScore), systemImage: "star.fill")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Label(String(format: "$%.4f/1K", model.cost), systemImage: "dollarsign.circle")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            Spacer()

            // Latency info
            VStack(alignment: .trailing, spacing: 2) {
                Text("p50: \(Int(model.latencyP50Ms))ms")
                    .font(.caption)
                    .foregroundColor(.secondary)
                Text("p95: \(Int(model.latencyP95Ms))ms")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.windowBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private func domainColor(_ domain: String) -> Color {
        switch domain.lowercased() {
        case "code":
            return .blue
        case "general":
            return .purple
        case "math":
            return .green
        default:
            return .gray
        }
    }

    private func domainIcon(_ domain: String) -> String {
        switch domain.lowercased() {
        case "code":
            return "chevron.left.forwardslash.chevron.right"
        case "general":
            return "brain.head.profile"
        case "math":
            return "function"
        default:
            return "questionmark"
        }
    }
}

// MARK: - Preview

#Preview {
    RoutingDashboardView()
        .frame(width: 900, height: 700)
}
