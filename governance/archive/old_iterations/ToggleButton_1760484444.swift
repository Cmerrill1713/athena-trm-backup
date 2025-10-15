import SwiftUI

struct ToggleButton: View {
    let icon: String
    @Binding var isOn: Bool

    var body: some View {
        Button(action: {
            withAnimation(.spring(response: 0.4, dampingFraction: 0.6, blendDuration: 0)) {
                self.isOn.toggle()
            }
        }) {
            Image(systemName: self.icon)
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(.white)
                .frame(width: 28, height: 28)
                .background(
                    Circle()
                        .fill(self.isOn ?
                            LinearGradient(
                                colors: [AppleColors.systemBlue, AppleColors.systemGray],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ) :
                            LinearGradient(
                                colors: [AppleColors.systemGray2, AppleColors.systemGray3],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .shadow(color: self.isOn ? AppleColors.systemBlue.opacity(0.4) : Color.clear, radius: 4, x: 0, y: 2)
                )
                .scaleEffect(self.isOn ? 1.05 : 1.0)
                .rotationEffect(.degrees(self.isOn ? 5 : 0))
        }
        .buttonStyle(.plain)
        .help(self.isOn ? "Disable" : "Enable")
        .animation(.spring(response: 0.3, dampingFraction: 0.7), value: self.isOn)
    }
}

#Preview {
    HStack {
        ToggleButton(icon: "doc.fill", isOn: .constant(true))
        ToggleButton(icon: "speaker.wave.2.fill", isOn: .constant(false))
        ToggleButton(icon: "arrow.clockwise", isOn: .constant(true))
    }
    .padding()
}
