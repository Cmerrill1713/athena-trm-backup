import AVFoundation
import SwiftUI

struct ContentView: View {
    let profile: UserProfile

    var body: some View {
        NeuroForgeChatView(profile: self.profile)
    }
}
