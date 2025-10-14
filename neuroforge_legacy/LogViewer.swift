import SwiftUI

// MARK: - Log Viewer for Services

struct LogViewer: View {
    let service: ServiceInfo
    @State private var logs: String = ""
    @State private var isLoading = false
    @State private var lastRefresh: Date?
    @State private var autoRefresh = false
    @State private var refreshTimer: Timer?
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("\(service.name) Logs")
                        .font(.headline)
                    if let last = lastRefresh {
                        Text("Last updated: \(last, style: .time)")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
                
                Spacer()
                
                Toggle("Auto", isOn: $autoRefresh)
                    .toggleStyle(.switch)
                    .controlSize(.small)
                    .help("Auto-refresh every 3 seconds")
                
                Button("Refresh") {
                    Task { await fetchLogs() }
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
                .disabled(isLoading)
                
                Button("Clear") {
                    logs = ""
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
            }
            .padding(12)
            .background(.ultraThinMaterial)
            
            Divider()
            
            // Logs content
            ScrollViewReader { proxy in
                ScrollView {
                    if isLoading && logs.isEmpty {
                        ProgressView("Loading logs...")
                            .padding()
                    } else if logs.isEmpty {
                        VStack(spacing: 12) {
                            Image(systemName: "doc.text")
                                .font(.system(size: 48))
                                .foregroundStyle(.tertiary)
                            Text("No logs yet")
                                .font(.headline)
                                .foregroundStyle(.secondary)
                            Text("Click Refresh to load logs")
                                .font(.caption)
                                .foregroundStyle(.tertiary)
                        }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .padding()
                    } else {
                        Text(logs)
                            .font(.system(size: 11).monospaced())
                            .textSelection(.enabled)
                            .padding(12)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .id("logBottom")
                    }
                }
                .background(Color(nsColor: .textBackgroundColor))
                .onChange(of: logs) {
                    withAnimation {
                        proxy.scrollTo("logBottom", anchor: .bottom)
                    }
                }
            }
        }
        .frame(minWidth: 600, minHeight: 400)
        .onAppear {
            Task { await fetchLogs() }
        }
        .onChange(of: autoRefresh) { _, enabled in
            if enabled {
                startAutoRefresh()
            } else {
                stopAutoRefresh()
            }
        }
        .onDisappear {
            stopAutoRefresh()
        }
    }
    
    // MARK: - Log Fetching
    
    private func fetchLogs() async {
        isLoading = true
        defer { isLoading = false }
        
        // Try to get logs from Bridge (which can tail service logs)
        let logURL = service.baseURL + "/api/logs?service=\(service.name.lowercased())&lines=100"
        
        do {
            let url = URL(string: logURL)!
            let (data, response) = try await URLSession.shared.data(from: url)
            
            if let httpResp = response as? HTTPURLResponse, httpResp.statusCode == 200 {
                if let logText = String(data: data, encoding: .utf8) {
                    await MainActor.run {
                        logs = logText
                        lastRefresh = Date()
                    }
                }
            } else {
                // Fallback: Try reading local log file
                await tryLocalLogFile()
            }
        } catch {
            // Fallback to local file
            await tryLocalLogFile()
        }
    }
    
    private func tryLocalLogFile() async {
        // Try to read from local logs directory
        let logPath = "/Users/christianmerrill/Documents/GitHub/logs/\(service.name.lowercased())_\(service.port).log"
        
        if let content = try? String(contentsOfFile: logPath) {
            let lines = content.split(separator: "\n")
            let last100 = lines.suffix(100).joined(separator: "\n")
            
            await MainActor.run {
                logs = last100
                lastRefresh = Date()
            }
        } else {
            await MainActor.run {
                logs = "⚠️ Logs not available for \(service.name)\n\nTried:\n• \(service.baseURL)/api/logs\n• \(logPath)\n\nService may not be running or logs not accessible."
                lastRefresh = Date()
            }
        }
    }
    
    // MARK: - Auto-Refresh
    
    private func startAutoRefresh() {
        stopAutoRefresh()
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 3.0, repeats: true) { _ in
            Task { await fetchLogs() }
        }
    }
    
    private func stopAutoRefresh() {
        refreshTimer?.invalidate()
        refreshTimer = nil
    }
}

// MARK: - Preview

#Preview {
    LogViewer(service: ServiceRegistry.athena)
}

