import SwiftUI

/// Lifecycle probe - shows when views appear/disappear (remount detection)
struct LifePing: ViewModifier {
    let name: String
    func body(content: Content) -> some View {
        content
            .onAppear { print("👶 APPEAR \(name)") }
            .onDisappear { print("💀 DISAPPEAR \(name)") }
    }
}

/// Hit test guard - logs when gestures are intercepted
struct HitTestGuard: ViewModifier {
    let name: String
    func body(content: Content) -> some View {
        content
            .highPriorityGesture(DragGesture(minimumDistance: 0).onChanged { _ in
                print("🧱 \(name) consumed drag")
            })
            .onTapGesture { 
                print("🧱 \(name) tap") 
            }
    }
}

extension View {
    /// Log lifecycle (appear/disappear)
    func life(_ name: String) -> some View {
        modifier(LifePing(name: name))
    }
    
    /// Log hit testing
    func hitGuard(_ name: String) -> some View {
        modifier(HitTestGuard(name: name))
    }
}

