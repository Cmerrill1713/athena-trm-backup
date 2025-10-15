import SwiftUI

// MARK: - Behavioral Learning View

struct BehavioralLearningView: View {
    @EnvironmentObject var athena: AthenaState

    @State private var learningEnabled = true
    @State private var adaptationEnabled = false
    @State private var totalObservations = 0
    @State private var overallConfidence = 0.0
    @State private var patternsLearned = 0
    @State private var recommendations: [BehavioralRecommendation] = []
    @State private var weeklySummary: WeeklySummary? = nil
    @State private var showWeeklySummary = false

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Header
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Image(systemName: adaptationEnabled ? "brain" : "brain.head.profile")
                        .foregroundColor(adaptationEnabled ? .purple : .gray)
                        .font(.title2)

                    Text("Behavioral Learning")
                        .font(.title2)
                        .bold()

                    Spacer()

                    if learningEnabled {
                        Text(adaptationEnabled ? "ADAPTING" : "LEARNING")
                            .font(.caption)
                            .bold()
                            .foregroundColor(.white)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(adaptationEnabled ? Color.purple : Color.blue)
                            .cornerRadius(8)
                    }
                }

                Text("Athena learns your alert preferences and optimizes timing automatically.")
                    .foregroundColor(.secondary)
            }

            // Learning Status
            VStack(alignment: .leading, spacing: 12) {
                Text("Learning Status")
                    .font(.headline)

                HStack {
                    Circle()
                        .fill(learningEnabled ? Color.blue : Color.gray)
                        .frame(width: 12, height: 12)

                    VStack(alignment: .leading) {
                        Text(learningEnabled ? "Behavioral Learning Active" : "Learning Disabled")
                            .bold()

                        HStack {
                            Text("Observations: \(totalObservations)")
                            Text("•")
                            Text("Confidence: \(String(format: "%.1f", overallConfidence * 100))%")
                        }
                        .font(.caption)
                        .foregroundColor(.secondary)
                    }

                    Spacer()

                    if adaptationEnabled {
                        Text("🤖 Auto-Adjusting")
                            .font(.caption)
                            .foregroundColor(.purple)
                    } else {
                        Text("👁️ Observation Only")
                            .font(.caption)
                            .foregroundColor(.blue)
                    }
                }
                .padding()
                .background(.ultraThinMaterial)
                .cornerRadius(12)
            }

            // Learning Progress
            if learningEnabled {
                VStack(alignment: .leading, spacing: 12) {
                    Text("Learning Progress")
                        .font(.headline)

                    VStack(spacing: 12) {
                        // Confidence Progress
                        VStack(alignment: .leading, spacing: 4) {
                            HStack {
                                Text("Learning Confidence")
                                Spacer()
                                Text("\(String(format: "%.0f", overallConfidence * 100))%")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }

                            ProgressView(value: overallConfidence)
                                .tint(.blue)
                        }

                        // Patterns Learned
                        HStack {
                            Image(systemName: "chart.bar.fill")
                                .foregroundColor(.green)
                            Text("Patterns Identified: \(patternsLearned)")
                            Spacer()
                            if patternsLearned == 0 {
                                Text("Need more usage data")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding(.vertical, 4)

                        // Recommendations Available
                        HStack {
                            Image(systemName: "lightbulb.fill")
                                .foregroundColor(.orange)
                            Text("Recommendations Ready: \(recommendations.count)")
                            Spacer()
                            if recommendations.isEmpty {
                                Text("Continue using system normally")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                    .padding()
                    .background(.ultraThinMaterial.opacity(0.5))
                    .cornerRadius(12)
                }
            }

            // Recommendations
            if !recommendations.isEmpty {
                VStack(alignment: .leading, spacing: 12) {
                    Text("Behavioral Recommendations")
                        .font(.headline)

                    ForEach(recommendations) { recommendation in
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Image(systemName: recommendation.icon)
                                    .foregroundColor(recommendation.color)
                                Text(recommendation.title)
                                    .bold()
                                Spacer()
                                Text("\(String(format: "%.0f", recommendation.confidence * 100))% confidence")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }

                            Text(recommendation.description)
                                .font(.caption)
                                .foregroundColor(.secondary)

                            if let suggestion = recommendation.suggestion {
                                Text(suggestion)
                                    .font(.caption)
                                    .bold()
                                    .foregroundColor(.blue)
                                    .padding(.vertical, 4)
                                    .padding(.horizontal, 8)
                                    .background(Color.blue.opacity(0.1))
                                    .cornerRadius(6)
                            }
                        }
                        .padding()
                        .background(.ultraThinMaterial.opacity(0.5))
                        .cornerRadius(12)
                    }
                }
            }

            // Control Panel
            VStack(alignment: .leading, spacing: 12) {
                Text("Learning Controls")
                    .font(.headline)

                VStack(spacing: 12) {
                    // Learning Toggle
                    Toggle("Enable behavioral learning", isOn: $learningEnabled)
                        .onChange(of: learningEnabled) { _ in
                            updateLearningStatus()
                        }

                    if learningEnabled {
                        // Adaptation Toggle
                        VStack(alignment: .leading, spacing: 8) {
                            Toggle("Enable active adaptation (auto-adjust settings)", isOn: $adaptationEnabled)
                                .onChange(of: adaptationEnabled) { _ in
                                    updateAdaptationStatus()
                                }

                            if adaptationEnabled {
                                Text("⚠️ System will automatically modify alert timing and filtering based on learned patterns")
                                    .font(.caption)
                                    .foregroundColor(.orange)
                                    .padding(.horizontal, 8)
                            } else {
                                Text("👁️ System learns your preferences but doesn't change behavior yet")
                                    .font(.caption)
                                    .foregroundColor(.blue)
                                    .padding(.horizontal, 8)
                            }
                        }

                        // Manual Actions
                        HStack(spacing: 12) {
                            Button(action: {
                                analyzePatterns()
                            }) {
                                Label("Analyze Now", systemImage: "magnifyingglass")
                                    .frame(maxWidth: .infinity)
                            }
                            .buttonStyle(.bordered)

                            Button(action: {
                                resetLearning()
                            }) {
                                Label("Reset Data", systemImage: "arrow.counterclockwise")
                                    .frame(maxWidth: .infinity)
                            }
                            .buttonStyle(.borderedProminent)
                        }
                    }
                }
                .padding()
                .background(.ultraThinMaterial.opacity(0.5))
                .cornerRadius(12)
            }

            // Learning Insights
            VStack(alignment: .leading, spacing: 8) {
                Text("Learning Insights")
                    .font(.headline)

                VStack(alignment: .leading, spacing: 4) {
                    Text("• Athena observes your alert interactions and timing preferences")
                    Text("• Patterns emerge after 2+ weeks of normal system usage")
                    Text("• Recommendations require 70%+ confidence before suggestions")
                    Text("• All learning data stays local on your device")
                    Text("• You can disable learning or reset data anytime")
                }
                .font(.caption)
                .foregroundColor(.secondary)
            }

            // Weekly Summary Section
            if learningEnabled {
                VStack(alignment: .leading, spacing: 12) {
                    Text("Weekly Summary")
                        .font(.headline)

                    VStack(alignment: .leading, spacing: 12) {
                        if let summary = weeklySummary {
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Image(systemName: "calendar.badge.clock")
                                        .foregroundColor(.blue)
                                    Text("Last Summary: \(summary.weekOf)")
                                        .bold()
                                    Spacer()
                                    Text("\(String(format: "%.1f", summary.confidenceLevel * 100))% confidence")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }

                                Text("📊 \(summary.learningProgress)")
                                    .font(.caption)
                                    .foregroundColor(.secondary)

                                Text("💡 \(summary.keyInsight)")
                                    .font(.caption)
                                    .foregroundColor(.secondary)

                                HStack {
                                    Text("\(summary.recommendationsCount) recommendations")
                                    Text("•")
                                    Text("\(summary.patternsDiscovered) patterns")
                                    Text("•")
                                    Text("\(summary.totalObservations) observations")
                                }
                                .font(.caption)
                                .foregroundColor(.secondary)
                            }
                            .padding()
                            .background(.ultraThinMaterial.opacity(0.5))
                            .cornerRadius(12)
                        } else {
                            Text("No weekly summaries yet")
                                .foregroundColor(.secondary)
                                .italic()
                                .padding()
                                .frame(maxWidth: .infinity)
                                .background(.ultraThinMaterial.opacity(0.5))
                                .cornerRadius(12)
                        }

                        // Summary Controls
                        HStack(spacing: 12) {
                            Button(action: {
                                generateWeeklySummary()
                            }) {
                                Label("Generate Summary", systemImage: "doc.text.fill")
                                    .frame(maxWidth: .infinity)
                            }
                            .buttonStyle(.bordered)

                            Button(action: {
                                showWeeklySummary = true
                            }) {
                                Label("View Details", systemImage: "eye.fill")
                                    .frame(maxWidth: .infinity)
                            }
                            .buttonStyle(.bordered)
                            .disabled(weeklySummary == nil)
                        }
                    }
                    .padding()
                    .background(.ultraThinMaterial.opacity(0.5))
                    .cornerRadius(12)
                }
            }
        }
        .padding()
        .onAppear {
            loadLearningStatus()
        }
        .sheet(isPresented: $showWeeklySummary) {
            if let summary = weeklySummary {
                WeeklySummaryDetailView(summary: summary)
            }
        }
    }

    private func updateLearningStatus() {
        // Update learning status via API
        let status = learningEnabled
        print("🧠 Behavioral learning: \(status ? "enabled" : "disabled")")
    }

    private func updateAdaptationStatus() {
        // Update adaptation status via API
        let status = adaptationEnabled
        print("🤖 Behavioral adaptation: \(status ? "enabled" : "disabled")")
    }

    private func analyzePatterns() {
        // Trigger pattern analysis
        print("🔍 Analyzing behavioral patterns...")
        // This would call the learning system to analyze current data
    }

    private func resetLearning() {
        // Reset all learning data
        totalObservations = 0
        overallConfidence = 0.0
        patternsLearned = 0
        recommendations = []
        print("🔄 Behavioral learning data reset")
    }

    private func loadLearningStatus() {
        // Load current learning status
        // In a real implementation, this would fetch from the behavioral learning API
        learningEnabled = true
        adaptationEnabled = false
        totalObservations = 245
        overallConfidence = 0.73
        patternsLearned = 6

        recommendations = [
            BehavioralRecommendation(
                title: "Meeting Lead Time",
                description: "Based on 15 meeting observations, you prefer 8 minutes of preparation time",
                suggestion: "Increase lead time from 5 to 8 minutes for meetings",
                confidence: 0.85,
                icon: "clock.fill",
                color: .blue
            ),
            BehavioralRecommendation(
                title: "Info Alert Filtering",
                description: "You respond to only 25% of info alerts during work hours",
                suggestion: "Reduce info alert frequency during work hours",
                confidence: 0.78,
                icon: "exclamationmark.bubble.fill",
                color: .orange
            )
        ]

        // Load weekly summary data
        loadWeeklySummary()
    }

    private func loadWeeklySummary() {
        // Load the latest weekly summary
        // In a real implementation, this would fetch from the API
        weeklySummary = WeeklySummary(
            timestamp: "2024-01-15T10:00:00Z",
            weekOf: "2024-01-15",
            learningProgress: "Good progress this week with 67 new observations",
            keyInsight: "You prefer 8 minutes of preparation before meetings",
            recommendationsCount: 2,
            confidenceLevel: 0.73,
            totalObservations: 245,
            patternsDiscovered: 6
        )
    }

    private func generateWeeklySummary() {
        // Generate a new weekly summary
        // In a real implementation, this would call the API
        print("📊 Generating weekly behavioral summary...")

        // Simulate API call delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            // Update with new summary data
            weeklySummary = WeeklySummary(
                timestamp: Date().ISO8601Format(),
                weekOf: "2024-01-22", // Current week
                learningProgress: "Excellent progress with 89 new observations",
                keyInsight: "Your meeting preparation preferences are now highly confident",
                recommendationsCount: 3,
                confidenceLevel: 0.85,
                totalObservations: 312,
                patternsDiscovered: 8
            )

            totalObservations = 312
            overallConfidence = 0.85
            patternsLearned = 8

            print("✅ Weekly summary generated successfully")
        }
    }
}

// MARK: - Behavioral Recommendation Model

struct BehavioralRecommendation: Identifiable {
    let id = UUID()
    let title: String
    let description: String
    let suggestion: String?
    let confidence: Double
    let icon: String
    let color: Color
}

// MARK: - Weekly Summary Model

struct WeeklySummary: Identifiable {
    let id = UUID()
    let timestamp: String
    let weekOf: String
    let learningProgress: String
    let keyInsight: String
    let recommendationsCount: Int
    let confidenceLevel: Double
    let totalObservations: Int
    let patternsDiscovered: Int
}

// MARK: - Weekly Summary Detail View

struct WeeklySummaryDetailView: View {
    let summary: WeeklySummary
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Header
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Image(systemName: "calendar.badge.clock")
                                .foregroundColor(.blue)
                                .font(.title2)

                            VStack(alignment: .leading) {
                                Text("Weekly Behavioral Summary")
                                    .font(.title2)
                                    .bold()

                                Text("Week of \(summary.weekOf)")
                                    .foregroundColor(.secondary)
                            }

                            Spacer()

                            Button(action: {
                                dismiss()
                            }) {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundColor(.secondary)
                            }
                        }
                    }

                    // Key Metrics
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Key Metrics")
                            .font(.headline)

                        HStack(spacing: 20) {
                            MetricCard(
                                title: "Total Observations",
                                value: "\(summary.totalObservations)",
                                icon: "eye.fill",
                                color: .blue
                            )

                            MetricCard(
                                title: "Patterns Found",
                                value: "\(summary.patternsDiscovered)",
                                icon: "chart.bar.fill",
                                color: .green
                            )

                            MetricCard(
                                title: "Recommendations",
                                value: "\(summary.recommendationsCount)",
                                icon: "lightbulb.fill",
                                color: .orange
                            )
                        }
                    }

                    // Learning Progress
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Learning Progress")
                            .font(.headline)

                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text("Confidence Level")
                                Spacer()
                                Text("\(String(format: "%.1f", summary.confidenceLevel * 100))%")
                                    .foregroundColor(.secondary)
                            }

                            ProgressView(value: summary.confidenceLevel)
                                .tint(.blue)
                        }

                        Text(summary.learningProgress)
                            .foregroundColor(.secondary)
                            .padding()
                            .background(.ultraThinMaterial.opacity(0.5))
                            .cornerRadius(8)
                    }

                    // Key Insights
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Key Insights")
                            .font(.headline)

                        Text(summary.keyInsight)
                            .foregroundColor(.secondary)
                            .padding()
                            .background(.ultraThinMaterial.opacity(0.5))
                            .cornerRadius(8)
                    }

                    // Recommendations Preview
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Recommendations Preview")
                            .font(.headline)

                        Text("You have \(summary.recommendationsCount) personalized recommendations ready for review in the Learning tab.")
                            .foregroundColor(.secondary)
                            .padding()
                            .background(.ultraThinMaterial.opacity(0.5))
                            .cornerRadius(8)
                    }

                    // Next Steps
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Next Steps")
                            .font(.headline)

                        VStack(alignment: .leading, spacing: 8) {
                            Text("• Continue using Athena normally to gather more behavioral data")
                            Text("• Review recommendations in the Learning tab when confidence reaches 80%+")
                            Text("• Consider enabling adaptation mode for automatic optimization")
                            Text("• Check back next Friday for your next weekly summary")
                        }
                        .foregroundColor(.secondary)
                        .padding()
                        .background(.ultraThinMaterial.opacity(0.5))
                        .cornerRadius(8)
                    }
                }
                .padding()
            }
            .navigationBarHidden(true)
        }
    }
}

// MARK: - Metric Card Component

struct MetricCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .foregroundColor(color)
                .font(.title2)

            Text(value)
                .font(.title)
                .bold()

            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(.ultraThinMaterial.opacity(0.5))
        .cornerRadius(12)
    }
}

// MARK: - Preview

#Preview {
    BehavioralLearningView()
        .environmentObject(AthenaState())
        .frame(width: 600, height: 700)
}
