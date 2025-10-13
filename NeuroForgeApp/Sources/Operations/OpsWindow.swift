import SwiftUI

// MARK: - Operations Dashboard Window

struct OpsWindow: View {
    @EnvironmentObject var ops: OpsState
    @SceneStorage("opsWindowFrame") private var frameData: Data?
    @State private var selectedService: ServiceInfo?
    
    var body: some View {
        VStack(spacing: 0) {
            // Tab picker
            Picker("View", selection: $ops.currentTab) {
                ForEach(OpsTab.allCases) { tab in
                    Label(tab.title, systemImage: tab.icon)
                        .tag(tab)
                }
            }
            .pickerStyle(.segmented)
            .padding(12)
            .background(.ultraThinMaterial)
            
            Divider()
            
            // Content
            Group {
                switch ops.currentTab {
                case .traces:
                    TracePanelView()
                case .health:
                    healthTab
                case .meta:
                    metaTab
                case .metrics:
                    metricsTab
                }
            }
        }
        .frame(minWidth: 640, minHeight: 420)
        .onAppear {
            ops.isWindowOpen = true
        }
        .onDisappear {
            ops.isWindowOpen = false
        }
        .sheet(item: $selectedService) { service in
            LogViewer(service: service)
        }
    }
    
    // MARK: - Health Tab
    
    @StateObject private var healthChecker = ServiceHealthChecker()
    
    private var healthTab: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Service health grid
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Service Health")
                            .font(.headline)
                        Spacer()
                        Button("Refresh") {
                            Task { await healthChecker.checkAll(services: ServiceRegistry.all) }
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                    }
                    
                    // Group by tier
                    ForEach(ServiceTier.allCases, id: \.self) { tier in
                        let services = ServiceRegistry.byTier(tier)
                        if !services.isEmpty {
                            VStack(alignment: .leading, spacing: 6) {
                                Text(tier.rawValue)
                                    .font(.caption.weight(.semibold))
                                    .foregroundStyle(tier.color)
                                
                                ForEach(services) { service in
                                    serviceRow(for: service)
                                }
                            }
                        }
                    }
                }
                .padding()
                .background(RoundedRectangle(cornerRadius: 10).fill(.ultraThinMaterial))
                
                // Health banner (overall)
                HealthBanner()
                    .padding()
                
                // Recent events
                if !ops.recentEvents.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Recent Events")
                            .font(.headline)
                        
                        ForEach(ops.recentEvents.prefix(10)) { event in
                            HStack(spacing: 8) {
                                Circle()
                                    .fill(event.type.color)
                                    .frame(width: 8, height: 8)
                                Text(event.timestamp, style: .time)
                                    .font(.caption.monospacedDigit())
                                    .foregroundStyle(.secondary)
                                Text(event.message)
                                    .font(.caption)
                                if let conf = event.confidence {
                                    Text("\(Int(conf * 100))%")
                                        .font(.caption.monospacedDigit())
                                        .foregroundStyle(.tertiary)
                                }
                            }
                        }
                    }
                    .padding()
                }
            }
            .padding()
        }
        .onAppear {
            Task { await healthChecker.checkAll(services: ServiceRegistry.all) }
        }
    }
    
    @ViewBuilder
    private func serviceRow(for service: ServiceInfo) -> some View {
        if let health = healthChecker.statuses[service.id] {
            HStack(spacing: 8) {
                Circle()
                    .fill(health.isHealthy ? Color.green : Color.red)
                    .frame(width: 8, height: 8)
                
                Text(service.name)
                    .font(.caption)
                
                Text(":\(service.port)")
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(.tertiary)
                
                Spacer()
                
                if let latency = health.latencyMs {
                    Text("\(latency)ms")
                        .font(.caption2.monospacedDigit())
                        .foregroundStyle(.secondary)
                }
                
                if let error = health.error, !health.isHealthy {
                    Text(error)
                        .font(.caption2)
                        .foregroundStyle(.red)
                        .lineLimit(1)
                }
                
                // Logs button (opens sheet)
                Button {
                    selectedService = service
                } label: {
                    Image(systemName: "doc.text.magnifyingglass")
                        .font(.caption)
                }
                .buttonStyle(.borderless)
                .help("View \(service.name) logs")
            }
        } else {
            HStack(spacing: 8) {
                ProgressView()
                    .scaleEffect(0.6)
                Text(service.name)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }
    
    // MARK: - Meta Tab
    
    private var metaTab: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Confidence trend
                if let conf = ops.lastConfidence {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Last Confidence")
                            .font(.headline)
                        
                        HStack {
                            Circle()
                                .fill(confidenceColor(conf))
                                .frame(width: 12, height: 12)
                            Text("\(Int(conf * 100))%")
                                .font(.title2.monospacedDigit().weight(.semibold))
                                .foregroundStyle(confidenceColor(conf))
                            Spacer()
                        }
                    }
                    .padding()
                    .background(RoundedRectangle(cornerRadius: 10).fill(.ultraThinMaterial))
                }
                
                // Meta settings
                VStack(alignment: .leading, spacing: 12) {
                    Text("Auto-Open Settings")
                        .font(.headline)
                    
                    Toggle("Auto-open on low confidence", isOn: $ops.autoOpenOnLowConfidence)
                    
                    HStack {
                        Text("Threshold:")
                        Slider(value: $ops.lowConfidenceThreshold, in: 0.1...0.5, step: 0.05)
                        Text("\(Int(ops.lowConfidenceThreshold * 100))%")
                            .font(.caption.monospacedDigit())
                    }
                }
                .padding()
            }
            .padding()
        }
    }
    
    // MARK: - Metrics Tab
    
    private var metricsTab: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("System Metrics")
                    .font(.headline)
                
                Text("Coming soon: Real-time metrics, charts, and performance data")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding()
        }
    }
    
    // MARK: - Helpers
    
    private func confidenceColor(_ conf: Double) -> Color {
        switch conf {
        case 0.8...1.0: return .green
        case 0.6..<0.8: return .yellow
        default: return .red
        }
    }
}

// MARK: - Preview

#Preview {
    OpsWindow()
        .environmentObject(OpsState())
}

