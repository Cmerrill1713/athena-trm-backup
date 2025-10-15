import SwiftUI
import Charts

// MARK: - Metrics & Analytics Panel

struct AthenaMetricsPanel: View {
    @EnvironmentObject var athena: AthenaState

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Performance Overview
                VStack(alignment: .leading, spacing: 16) {
                    Text("Performance Overview")
                        .font(.title2)
                        .bold()

                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 200))], spacing: 16) {
                        MetricCard(
                            title: "Memory Optimization",
                            value: athena.metrics.memorySavingsDescription,
                            subtitle: "Space saved",
                            icon: "memorychip",
                            color: .blue
                        )

                        MetricCard(
                            title: "Tribunal Scans",
                            value: "\(athena.metrics.tribunalScansToday)",
                            subtitle: "Today",
                            icon: "magnifyingglass",
                            color: .orange
                        )

                        MetricCard(
                            title: "Alerts Triggered",
                            value: "\(athena.metrics.alertsTriggeredToday)",
                            subtitle: "Today",
                            icon: "bell",
                            color: .red
                        )

                        MetricCard(
                            title: "Response Time",
                            value: athena.metrics.responseTimeDescription,
                            subtitle: "Average",
                            icon: "timer",
                            color: .green
                        )

                        MetricCard(
                            title: "System Health",
                            value: athena.metrics.healthScoreDescription,
                            subtitle: "Overall score",
                            icon: "heart.fill",
                            color: athena.metrics.systemHealthScore > 0.8 ? .green : .red
                        )
                    }
                }

                // Charts Section
                VStack(alignment: .leading, spacing: 16) {
                    Text("Activity Trends")
                        .font(.title2)
                        .bold()

                    // Memory Usage Chart
                    VStack(alignment: .leading) {
                        Text("Memory Usage Over Time")
                            .font(.headline)

                        Chart(mockMemoryData) { point in
                            LineMark(
                                x: .value("Time", point.time),
                                y: .value("Usage", point.usage)
                            )
                            .foregroundStyle(.blue)
                        }
                        .frame(height: 200)
                        .chartYAxis {
                            AxisMarks(position: .leading)
                        }
                    }
                    .padding()
                    .background(.ultraThinMaterial)
                    .cornerRadius(12)

                    // Alert Frequency Chart
                    VStack(alignment: .leading) {
                        Text("Alert Frequency (Last 7 Days)")
                            .font(.headline)

                        Chart(mockAlertData) { point in
                            BarMark(
                                x: .value("Day", point.day),
                                y: .value("Alerts", point.count)
                            )
                            .foregroundStyle(.orange)
                        }
                        .frame(height: 200)
                        .chartYAxis {
                            AxisMarks(position: .leading)
                        }
                    }
                    .padding()
                    .background(.ultraThinMaterial)
                    .cornerRadius(12)
                }

                // Service Performance
                VStack(alignment: .leading, spacing: 16) {
                    Text("Service Performance")
                        .font(.title2)
                        .bold()

                    ForEach(athena.services) { service in
                        ServicePerformanceRow(service: service)
                    }
                }
            }
            .padding()
        }
        .refreshable {
            athena.refreshMetrics()
        }
    }
}

// MARK: - Metric Card

struct MetricCard: View {
    let title: String
    let value: String
    let subtitle: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundColor(color)

                Spacer()

                Text(value)
                    .font(.title)
                    .bold()
                    .foregroundColor(color)
            }

            Text(title)
                .font(.headline)
                .foregroundColor(.primary)

            Text(subtitle)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(.ultraThinMaterial)
        .cornerRadius(12)
    }
}

// MARK: - Service Performance Row

struct ServicePerformanceRow: View {
    let service: AthenaService

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(service.name)
                    .font(.headline)

                Spacer()

                Circle()
                    .fill(statusColor)
                    .frame(width: 8, height: 8)
            }

            HStack(spacing: 16) {
                VStack(alignment: .leading) {
                    Text("Uptime")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text("99.9%")
                        .font(.body)
                        .bold()
                }

                VStack(alignment: .leading) {
                    Text("Executions")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text("24")
                        .font(.body)
                        .bold()
                }

                VStack(alignment: .leading) {
                    Text("Avg Duration")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text("2.3s")
                        .font(.body)
                        .bold()
                }

                Spacer()
            }
        }
        .padding()
        .background(.ultraThinMaterial)
        .cornerRadius(12)
    }

    private var statusColor: Color {
        switch service.status {
        case .running: return .green
        case .idle: return .blue
        case .error: return .red
        case .stopped: return .gray
        }
    }
}

// MARK: - Mock Data for Charts

struct MemoryDataPoint: Identifiable {
    let id = UUID()
    let time: Date
    let usage: Double
}

struct AlertDataPoint: Identifiable {
    let id = UUID()
    let day: String
    let count: Int
}

let mockMemoryData: [MemoryDataPoint] = {
    let now = Date()
    return (0..<24).map { hour in
        let time = now.addingTimeInterval(Double(hour - 12) * 3600)
        let usage = 60.0 + Double.random(in: -10...20) // Mock memory usage 50-80%
        return MemoryDataPoint(time: time, usage: usage)
    }
}()

let mockAlertData: [AlertDataPoint] = [
    AlertDataPoint(day: "Mon", count: 2),
    AlertDataPoint(day: "Tue", count: 1),
    AlertDataPoint(day: "Wed", count: 3),
    AlertDataPoint(day: "Thu", count: 1),
    AlertDataPoint(day: "Fri", count: 2),
    AlertDataPoint(day: "Sat", count: 0),
    AlertDataPoint(day: "Sun", count: 1)
]

// MARK: - Preview

#Preview {
    let mockAthena = AthenaState()
    mockAthena.metrics = AthenaMetrics(
        memoryOptimizationSavings: 0.35,
        tribunalScansToday: 24,
        alertsTriggeredToday: 3,
        averageResponseTime: 0.8,
        systemHealthScore: 0.95
    )

    return AthenaMetricsPanel()
        .environmentObject(mockAthena)
        .frame(width: 800, height: 600)
}
