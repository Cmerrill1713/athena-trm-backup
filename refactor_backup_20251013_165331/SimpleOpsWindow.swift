import SwiftUI

struct SimpleOpsWindow: View {
    @StateObject private var serviceMonitor = ServiceMonitor()
    @State private var selectedTab = 0
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Operations")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Button(action: serviceMonitor.refresh) {
                    Image(systemName: "arrow.clockwise")
                }
                .disabled(serviceMonitor.isRefreshing)
                
                Button(action: {
                    NSApplication.shared.terminate(nil)
                }) {
                    Image(systemName: "xmark")
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
            
            Divider()
            
            // Tab bar
            HStack(spacing: 0) {
                TabButton(title: "Services", isSelected: selectedTab == 0) {
                    selectedTab = 0
                }
                
                TabButton(title: "Logs", isSelected: selectedTab == 1) {
                    selectedTab = 1
                }
                
                TabButton(title: "Metrics", isSelected: selectedTab == 2) {
                    selectedTab = 2
                }
                
                Spacer()
            }
            .padding(.horizontal)
            .background(Color(NSColor.controlBackgroundColor))
            
            Divider()
            
            // Content
            TabView(selection: $selectedTab) {
                ServicesView(serviceMonitor: serviceMonitor)
                    .tabItem { Text("Services") }
                    .tag(0)
                
                LogsView()
                    .tabItem { Text("Logs") }
                    .tag(1)
                
                MetricsView()
                    .tabItem { Text("Metrics") }
                    .tag(2)
            }
            .tabViewStyle(PlainTabViewStyle())
        }
        .frame(width: 600, height: 500)
        .onAppear {
            serviceMonitor.startMonitoring()
        }
    }
}

struct TabButton: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(isSelected ? .primary : .secondary)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(
                    Rectangle()
                        .fill(isSelected ? Color.accentColor.opacity(0.1) : Color.clear)
                )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct ServicesView: View {
    @ObservedObject var serviceMonitor: ServiceMonitor
    
    var body: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                ForEach(serviceMonitor.services, id: \.name) { service in
                    ServiceCard(service: service)
                }
            }
            .padding()
        }
        .refreshable {
            await serviceMonitor.refreshAsync()
        }
    }
}

struct ServiceCard: View {
    let service: ServiceStatus
    
    var body: some View {
        HStack(spacing: 12) {
            // Status indicator
            Circle()
                .fill(statusColor)
                .frame(width: 12, height: 12)
            
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(service.name)
                        .font(.system(size: 14, weight: .semibold))
                    
                    Spacer()
                    
                    Text(service.status.rawValue.uppercased())
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(statusColor)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(statusColor.opacity(0.2))
                        .cornerRadius(4)
                }
                
                HStack {
                    Text("Port: \(service.port)")
                        .font(.system(size: 12))
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    if let latency = service.latency {
                        Text("\(latency)ms")
                            .font(.system(size: 12))
                            .foregroundColor(.secondary)
                    }
                }
            }
            
            Spacer()
            
            Button(action: {
                if let url = URL(string: service.healthURL) {
                    NSWorkspace.shared.open(url)
                }
            }) {
                Image(systemName: "arrow.up.right.square")
                    .font(.system(size: 12))
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(service.status != .healthy)
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(statusColor.opacity(0.3), lineWidth: 1)
        )
    }
    
    private var statusColor: Color {
        switch service.status {
        case .healthy:
            return .green
        case .degraded:
            return .yellow
        case .unhealthy:
            return .red
        case .unknown:
            return .gray
        }
    }
}

struct LogsView: View {
    @StateObject private var logManager = LogManager()
    
    var body: some View {
        VStack(spacing: 0) {
            // Log controls
            HStack {
                Picker("Service", selection: $logManager.selectedService) {
                    Text("All Services").tag("all")
                    ForEach(logManager.availableServices, id: \.self) { service in
                        Text(service).tag(service)
                    }
                }
                .frame(width: 150)
                
                Picker("Level", selection: $logManager.selectedLevel) {
                    Text("All").tag("all")
                    Text("Error").tag("error")
                    Text("Warning").tag("warning")
                    Text("Info").tag("info")
                    Text("Debug").tag("debug")
                }
                .frame(width: 100)
                
                Spacer()
                
                Toggle("Auto-scroll", isOn: $logManager.autoScroll)
                    .toggleStyle(SwitchToggleStyle())
                
                Button("Clear") {
                    logManager.clearLogs()
                }
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
            
            Divider()
            
            // Log display
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 2) {
                        ForEach(logManager.filteredLogs, id: \.id) { log in
                            LogEntryView(log: log)
                                .id(log.id)
                        }
                    }
                    .padding()
                }
                .onChange(of: logManager.filteredLogs.count) { _ in
                    if logManager.autoScroll, let lastLog = logManager.filteredLogs.last {
                        withAnimation {
                            proxy.scrollTo(lastLog.id, anchor: .bottom)
                        }
                    }
                }
            }
        }
        .onAppear {
            logManager.startLogging()
        }
    }
}

struct LogEntryView: View {
    let log: LogEntry
    
    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Text(log.timestamp)
                .font(.system(size: 10, family: .monospaced))
                .foregroundColor(.secondary)
                .frame(width: 80, alignment: .leading)
            
            Text(log.level.uppercased())
                .font(.system(size: 9, weight: .bold))
                .foregroundColor(levelColor)
                .frame(width: 50, alignment: .leading)
            
            Text(log.service)
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(.blue)
                .frame(width: 80, alignment: .leading)
            
            Text(log.message)
                .font(.system(size: 11, family: .monospaced))
                .textSelection(.enabled)
        }
        .padding(.vertical, 1)
    }
    
    private var levelColor: Color {
        switch log.level.lowercased() {
        case "error":
            return .red
        case "warning":
            return .yellow
        case "info":
            return .blue
        case "debug":
            return .gray
        default:
            return .primary
        }
    }
}

struct MetricsView: View {
    @StateObject private var metricsManager = MetricsManager()
    
    var body: some View {
        ScrollView {
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 16) {
                ForEach(metricsManager.metrics, id: \.name) { metric in
                    MetricCard(metric: metric)
                }
            }
            .padding()
        }
        .onAppear {
            metricsManager.startMonitoring()
        }
    }
}

struct MetricCard: View {
    let metric: Metric
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(metric.name)
                .font(.system(size: 14, weight: .semibold))
            
            Text(metric.value)
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(.primary)
            
            Text(metric.description)
                .font(.system(size: 12))
                .foregroundColor(.secondary)
                .lineLimit(2)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
    }
}

// MARK: - Data Models

struct ServiceStatus {
    let name: String
    let port: Int
    let status: HealthStatus
    let latency: Int?
    let healthURL: String
    let lastChecked: Date
}

enum HealthStatus: String {
    case healthy = "healthy"
    case degraded = "degraded"
    case unhealthy = "unhealthy"
    case unknown = "unknown"
}

struct LogEntry {
    let id = UUID()
    let timestamp: String
    let level: String
    let service: String
    let message: String
}

struct Metric {
    let name: String
    let value: String
    let description: String
}

// MARK: - Managers

class ServiceMonitor: ObservableObject {
    @Published var services: [ServiceStatus] = []
    @Published var isRefreshing = false
    
    private let serviceConfigs = [
        ("Bridge API", 8014, "http://localhost:8014/health"),
        ("Athena", 8090, "http://localhost:8090/health"),
        ("UAT", 8181, "http://localhost:8181/health"),
        ("RAG", 8015, "http://localhost:8015/health"),
        ("Vision", 8016, "http://localhost:8016/health"),
        ("Kokoro", 8020, "http://localhost:8020/health"),
        ("FastVLM", 8811, "http://localhost:8811/health"),
        ("Ollama", 11434, "http://localhost:11434/api/tags"),
        ("Prometheus", 9090, "http://localhost:9090/metrics"),
        ("Netdata", 19999, "http://localhost:19999")
    ]
    
    func startMonitoring() {
        refresh()
        Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { _ in
            self.refresh()
        }
    }
    
    func refresh() {
        isRefreshing = true
        Task {
            await refreshAsync()
        }
    }
    
    @MainActor
    func refreshAsync() async {
        var newServices: [ServiceStatus] = []
        
        for (name, port, url) in serviceConfigs {
            let startTime = Date()
            let status = await checkServiceHealth(url: url)
            let latency = Int(Date().timeIntervalSince(startTime) * 1000)
            
            let serviceStatus = ServiceStatus(
                name: name,
                port: port,
                status: status,
                latency: latency,
                healthURL: url,
                lastChecked: Date()
            )
            
            newServices.append(serviceStatus)
        }
        
        services = newServices
        isRefreshing = false
    }
    
    private func checkServiceHealth(url: String) async -> HealthStatus {
        guard let url = URL(string: url) else { return .unknown }
        
        do {
            let (_, response) = try await URLSession.shared.data(from: url)
            if let httpResponse = response as? HTTPURLResponse {
                switch httpResponse.statusCode {
                case 200...299:
                    return .healthy
                case 300...499:
                    return .degraded
                default:
                    return .unhealthy
                }
            }
        } catch {
            return .unhealthy
        }
        
        return .unknown
    }
}

class LogManager: ObservableObject {
    @Published var logs: [LogEntry] = []
    @Published var selectedService = "all"
    @Published var selectedLevel = "all"
    @Published var autoScroll = true
    
    var availableServices: [String] {
        Array(Set(logs.map { $0.service })).sorted()
    }
    
    var filteredLogs: [LogEntry] {
        logs.filter { log in
            let serviceMatch = selectedService == "all" || log.service == selectedService
            let levelMatch = selectedLevel == "all" || log.level.lowercased() == selectedLevel.lowercased()
            return serviceMatch && levelMatch
        }
    }
    
    func startLogging() {
        // Simulate log entries for demo
        Timer.scheduledTimer(withTimeInterval: 2, repeats: true) { _ in
            self.addLogEntry()
        }
    }
    
    private func addLogEntry() {
        let services = ["Bridge", "Athena", "UAT", "RAG", "Vision", "Kokoro"]
        let levels = ["info", "warning", "error", "debug"]
        let messages = [
            "Service started successfully",
            "Processing request",
            "Connection timeout",
            "Database query completed",
            "Cache miss detected",
            "Health check passed"
        ]
        
        let log = LogEntry(
            timestamp: DateFormatter.logFormatter.string(from: Date()),
            level: levels.randomElement() ?? "info",
            service: services.randomElement() ?? "Unknown",
            message: messages.randomElement() ?? "No message"
        )
        
        DispatchQueue.main.async {
            self.logs.append(log)
            if self.logs.count > 1000 {
                self.logs.removeFirst(100)
            }
        }
    }
    
    func clearLogs() {
        logs.removeAll()
    }
}

class MetricsManager: ObservableObject {
    @Published var metrics: [Metric] = []
    
    func startMonitoring() {
        loadMetrics()
        Timer.scheduledTimer(withTimeInterval: 10, repeats: true) { _ in
            self.loadMetrics()
        }
    }
    
    private func loadMetrics() {
        metrics = [
            Metric(name: "Active Requests", value: "\(Int.random(in: 10...100))", description: "Current active API requests"),
            Metric(name: "Response Time", value: "\(Int.random(in: 50...500))ms", description: "Average response time"),
            Metric(name: "Error Rate", value: "\(Double.random(in: 0...5))%", description: "Current error rate"),
            Metric(name: "Memory Usage", value: "\(Int.random(in: 200...800))MB", description: "System memory usage"),
            Metric(name: "CPU Usage", value: "\(Int.random(in: 10...80))%", description: "CPU utilization"),
            Metric(name: "Disk Usage", value: "\(Int.random(in: 20...90))%", description: "Disk space usage")
        ]
    }
}

extension DateFormatter {
    static let logFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss"
        return formatter
    }()
}

#Preview {
    SimpleOpsWindow()
}
