import Foundation
import AppKit
import AVFoundation

/// Vision Reporter - Display vision analysis with thumbnail + voice output
/// Integrates FastVLM results into Athena Reporter with visual + audio
class VisionReporter {
    
    // MARK: - Vision Report Structure
    
    struct VisionReport {
        let imagePath: String
        let prompt: String
        let response: String
        let latencyMs: Double
        let model: String
        let timestamp: Date
        let ragSources: [RagSource]?
        
        init(
            imagePath: String,
            prompt: String,
            response: String,
            latencyMs: Double,
            model: String,
            ragSources: [RagSource]? = nil
        ) {
            self.imagePath = imagePath
            self.prompt = prompt
            self.response = response
            self.latencyMs = latencyMs
            self.model = model
            self.timestamp = Date()
            self.ragSources = ragSources
        }
    }
    
    struct RagSource {
        let title: String
        let url: String?
        let relevance: Double?
    }
    
    // MARK: - Display Methods
    
    /// Show vision report in window with thumbnail + text
    static func show(report: VisionReport, speak: Bool = true) {
        let markdown = formatAsMarkdown(report: report)
        
        // Open in Athena Reporter window
        openReporterWindow(markdown: markdown, imagePath: report.imagePath)
        
        // Speak summary (not raw markdown)
        if speak {
            let summary = extractSummary(from: report.response)
            speakText(summary)
        }
    }
    
    /// Format vision report as markdown
    static func formatAsMarkdown(report: VisionReport) -> String {
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "MMM dd, yyyy 'at' h:mm a"
        let timestamp = dateFormatter.string(from: report.timestamp)
        
        var markdown = """
        # Vision Analysis
        
        **Image:** `\(URL(fileURLWithPath: report.imagePath).lastPathComponent)`  
        **Time:** \(timestamp)  
        **Model:** \(report.model)  
        **Latency:** \(String(format: "%.0fms", report.latencyMs))
        
        ---
        
        ## 💬 Prompt
        
        > \(report.prompt)
        
        ## 🔍 Analysis
        
        \(report.response)
        
        """
        
        // Add RAG sources if present
        if let sources = report.ragSources, !sources.isEmpty {
            markdown += "\n---\n\n## 📚 Sources\n\n"
            for (index, source) in sources.enumerated() {
                markdown += "\(index + 1). **\(source.title)**"
                if let url = source.url, !url.isEmpty {
                    markdown += " • [\(url)](\(url))"
                }
                if let relevance = source.relevance {
                    markdown += " • Relevance: \(String(format: "%.0f%%", relevance * 100))"
                }
                markdown += "\n"
            }
        }
        
        markdown += """
        
        ---
        
        *Powered by FastVLM • Athena Reporter*
        """
        
        return markdown
    }
    
    /// Extract summary for voice (first 2-3 sentences)
    static func extractSummary(from text: String) -> String {
        // Split into sentences
        let sentences = text.components(separatedBy: CharacterSet(charactersIn: ".!?"))
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
        
        // Take first 2-3 sentences for voice
        let maxSentences = min(3, sentences.count)
        let summary = sentences.prefix(maxSentences).joined(separator: ". ")
        
        return summary.isEmpty ? text : summary + "."
    }
    
    /// Speak text using system voice
    static func speakText(_ text: String) {
        let cleanText = text
            .replacingOccurrences(of: "*", with: "")
            .replacingOccurrences(of: "_", with: "")
            .replacingOccurrences(of: "#", with: "")
            .replacingOccurrences(of: "`", with: "")
            .replacingOccurrences(of: "[", with: "")
            .replacingOccurrences(of: "]", with: "")
        
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/say")
        task.arguments = ["-v", "Samantha", cleanText]
        
        try? task.run()
    }
    
    /// Open reporter window with image thumbnail
    static func openReporterWindow(markdown: String, imagePath: String) {
        // Save markdown to temp file
        let tempDir = FileManager.default.temporaryDirectory
        let reportFile = tempDir.appendingPathComponent("vision_report_\(Date().timeIntervalSince1970).md")
        
        try? markdown.write(to: reportFile, atomically: true, encoding: .utf8)
        
        // Launch Athena Reporter with the markdown file
        // (assumes reporter can accept file path and display with image thumbnail)
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/open")
        task.arguments = ["-a", "AthenaReporter", reportFile.path]
        
        try? task.run()
        
        print("📊 Vision report opened in Athena Reporter")
        print("   Report: \(reportFile.path)")
        print("   Image:  \(imagePath)")
    }
    
    // MARK: - CLI Integration
    
    /// Create report from FastVLM response JSON
    static func fromFastVLMResponse(json: [String: Any]) -> VisionReport? {
        guard let text = json["text"] as? String,
              let latency = json["latency_ms"] as? Double,
              let model = json["model"] as? String else {
            return nil
        }
        
        let imagePath = json["image_path"] as? String ?? "unknown"
        let prompt = json["prompt"] as? String ?? "Describe the image"
        
        // Parse RAG sources if present
        var ragSources: [RagSource]?
        if let sourcesData = json["rag_sources"] as? [[String: Any]] {
            ragSources = sourcesData.compactMap { source in
                guard let title = source["title"] as? String else { return nil }
                return RagSource(
                    title: title,
                    url: source["url"] as? String,
                    relevance: source["relevance"] as? Double
                )
            }
        }
        
        return VisionReport(
            imagePath: imagePath,
            prompt: prompt,
            response: text,
            latencyMs: latency,
            model: model,
            ragSources: ragSources
        )
    }
}

// MARK: - Usage Examples

/*
 // From Python/CLI:
 
 let jsonData = """
 {
   "text": "This image shows a bar chart with quarterly sales data...",
   "latency_ms": 487.5,
   "model": "fastvlm-1.5b",
   "image_path": "/Users/.../chart.png",
   "prompt": "Describe this chart",
   "rag_sources": [
     {"title": "Q3 Sales Report", "url": "https://...", "relevance": 0.89}
   ]
 }
 """.data(using: .utf8)!
 
 if let json = try? JSONSerialization.jsonObject(with: jsonData) as? [String: Any],
    let report = VisionReporter.fromFastVLMResponse(json: json) {
     VisionReporter.show(report: report, speak: true)
 }
 
 // Direct usage:
 
 let report = VisionReporter.VisionReport(
     imagePath: "/tmp/screenshot.png",
     prompt: "What's in this image?",
     response: "This image shows a macOS desktop with...",
     latencyMs: 512.3,
     model: "fastvlm-1.5b"
 )
 
 VisionReporter.show(report: report, speak: true)
 */

