import SwiftUI
import AppKit

// App delegate to ensure proper activation and focus
final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true) // Brings window & focus to front
    }
}

struct NeuroForgeApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    
    @State private var isLoggedIn = false
    @State private var selectedProfile: UserProfile?
    
    @StateObject private var errorCenter = ErrorCenter()
    @AppStorage("showDiagnosticsOverlay") private var showDiagnostics: Bool = false
    
    init() {
        // Register network interceptor for diagnostics
        registerNetworkInterceptor()
    }
    
    var body: some Scene {
        WindowGroup {
            productionInterface
                .environmentObject(errorCenter)
                .overlay(alignment: .topTrailing) {
                    if showDiagnostics {
                        DiagnosticsOverlay()
                    }
                }
                .overlay(alignment: .top) {
                    if let banner = errorCenter.activeBanner {
                        BannerOverlay(banner: banner) {
                            errorCenter.clearBanner()
                        }
                    }
                }
        }
        .defaultSize(width: 1000, height: 700)
        .windowStyle(.automatic)
        .windowToolbarStyle(.unified)
        .windowResizability(.contentSize)
        .commands {
            CommandGroup(replacing: .appInfo) {
                Button("About Athena") {
                    // About action
                }
            }
            
            CommandGroup(after: .appInfo) {
                Button("Switch Profile...") {
                    isLoggedIn = false
                }
                .keyboardShortcut("p", modifiers: [.command, .shift])
            }
            
            CommandGroup(after: .textEditing) {
                Button("Focus Chat Input") {
                    NotificationCenter.default.post(name: Notification.Name("chat:focusInput"), object: nil)
                }
                .keyboardShortcut("l", modifiers: [.command])
            }
        }
    }
    
    @ViewBuilder
    private var productionInterface: some View {
        if isLoggedIn, let profile = selectedProfile {
            ContentView(profile: profile)
        } else {
            LoginView(isLoggedIn: $isLoggedIn, selectedProfile: $selectedProfile)
        }
    }
}

/// Banner overlay for error display
private struct BannerOverlay: View {
    let banner: BannerData
    let onDismiss: () -> Void
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: banner.kind.icon)
                .foregroundColor(banner.kind.color)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(banner.kind.title)
                    .font(.caption.bold())
                
                Text(banner.message)
                    .font(.caption)
            }
            
            Spacer()
            
            Button {
                onDismiss()
            } label: {
                Image(systemName: "xmark.circle.fill")
                    .foregroundColor(.secondary)
            }
            .buttonStyle(.plain)
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(banner.kind.color.opacity(0.15))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(banner.kind.color.opacity(0.3), lineWidth: 1)
        )
        .padding()
        .shadow(radius: 4)
        .transition(.move(edge: .top).combined(with: .opacity))
        .animation(.easeInOut, value: banner.id)
    }
}

extension BannerData.BannerKind {
    var title: String {
        switch self {
        case .info: return "Info"
        case .warning: return "Warning"
        case .error: return "Error"
        }
    }
}

// Entry point
NeuroForgeApp.main()

