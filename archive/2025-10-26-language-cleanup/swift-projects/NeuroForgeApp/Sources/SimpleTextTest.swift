import SwiftUI

/// DIAGNOSTIC VIEW - Using PURE SwiftUI TextField (workaround for known macOS bug)
struct SimpleTextTestView: View {
    @State private var text: String = ""
    @FocusState private var isFocused: Bool
    
    var body: some View {
        VStack(spacing: 20) {
            Text("🔧 PURE SWIFTUI TEST")
                .font(.largeTitle)
                .padding()
            
            Text("This uses pure SwiftUI TextField")
                .padding()
            
            Text("Known bug workaround: .defaultFocus() + aggressive focus")
                .padding()
            
            Divider()
            
            // PURE SwiftUI TextField - simplest possible
            TextField("Type anything here...", text: $text, axis: .vertical)
                .textFieldStyle(.plain)
                .font(.system(size: 16))
                .padding(16)
                .background(Color(NSColor.textBackgroundColor))
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(isFocused ? Color.blue : Color.gray, lineWidth: 2)
                )
                .focused($isFocused)
                .frame(minHeight: 100)
                .padding()
                .onAppear {
                    // Aggressively claim focus
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                        isFocused = true
                    }
                }
                .onSubmit {
                    print("✅ Submitted: \(text)")
                    text = ""
                    isFocused = true
                }
            
            HStack {
                Text("Current text: \"\(text)\"")
                    .foregroundColor(.secondary)
                Spacer()
                Text("Focus: \(isFocused ? "✅ YES" : "❌ NO")")
                    .foregroundColor(isFocused ? .green : .red)
            }
            .padding()
            
            HStack(spacing: 12) {
                Button("Clear") {
                    text = ""
                }
                
                Button("Force Focus") {
                    isFocused = true
                }
                
                Button("Test: Add 'Hello'") {
                    text += "Hello "
                }
            }
            .padding()
            
            Spacer()
        }
        .frame(minWidth: 600, minHeight: 400)
        .padding()
    }
}

#Preview {
    SimpleTextTestView()
}
