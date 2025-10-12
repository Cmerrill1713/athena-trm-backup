import SwiftUI
#if os(macOS)
import AppKit
#endif

/// Confidence trend sparkline showing last N confidence scores
struct ConfidenceSparkline: View {
    let history: [Double]  // Last 5-10 confidence scores
    
    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width
            let h = geo.size.height
            let step = w / CGFloat(max(history.count - 1, 1))
            
            // Line path
            Path { path in
                guard !history.isEmpty else { return }
                path.move(to: CGPoint(x: 0, y: h * (1 - CGFloat(history[0]))))
                for (i, conf) in history.enumerated().dropFirst() {
                    path.addLine(to: CGPoint(x: step * CGFloat(i), y: h * (1 - CGFloat(conf))))
                }
            }
            .stroke(confidenceColor(history.last ?? 0), lineWidth: 2)
            
            // Dots at each point
            ForEach(Array(history.enumerated()), id: \.offset) { i, conf in
                Circle()
                    .fill(confidenceColor(conf))
                    .frame(width: 4, height: 4)
                    .position(x: step * CGFloat(i), y: h * (1 - CGFloat(conf)))
            }
        }
        .frame(height: 24)
    }
    
    private func confidenceColor(_ conf: Double) -> Color {
        switch conf {
        case 0.8...1.0: return .green
        case 0.6..<0.8: return .yellow
        default: return .red
        }
    }
}

// MARK: - Previews

#if DEBUG
struct ConfidenceSparkline_Previews: PreviewProvider {
    static var previews: some View {
        VStack(spacing: 20) {
            // Rising confidence
            ConfidenceSparkline(history: [0.3, 0.45, 0.62, 0.78, 0.91])
                .frame(height: 40)
                .padding()
            
            // Falling confidence
            ConfidenceSparkline(history: [0.85, 0.72, 0.58, 0.42, 0.28])
                .frame(height: 40)
                .padding()
            
            // Stable high
            ConfidenceSparkline(history: [0.88, 0.91, 0.89, 0.92, 0.87])
                .frame(height: 40)
                .padding()
        }
        #if os(macOS)
        .background(Color(NSColor.windowBackgroundColor))
        #else
        .background(Color(.systemGray6))
        #endif
    }
}
#endif

