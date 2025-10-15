import SwiftUI
import AVFoundation

struct ContentView: View {
    let profile: UserProfile

    var body: some View {
        NeuroForgeChatView(profile: profile)
    }
}
