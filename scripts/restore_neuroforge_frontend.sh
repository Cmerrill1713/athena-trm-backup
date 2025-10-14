#!/usr/bin/env zsh
set -euo pipefail

# Restore complete NeuroForge frontend from working implementation
# Integrates with existing Athena pop-out windows

ROOT="/Users/christianmerrill/Documents/GitHub"
SOURCE="$ROOT/AI-Projects/universal-ai-tools/NeuroForgeApp/Sources/NeuroForgeApp"
DEST="$ROOT/NeuroForgeApp/Sources"
BACKUP="$ROOT/neuroforge_restore_backup_$(date +%Y%m%d_%H%M%S)"

echo "🔄 Restoring NeuroForge frontend..."
echo "   Source: $SOURCE"
echo "   Dest:   $DEST"

# Create backup of current minimal state
mkdir -p "$BACKUP"
cp -R "$DEST" "$BACKUP/"
echo "✅ Backed up current state to $BACKUP"

# Keep our clean pop-out windows and core Athena files
KEEP_FILES=(
    "main.swift"
    "Notifications+App.swift"
    "AthenaModels.swift"
    "AthenaState.swift"
    "VoiceManager.swift"
    "AthenaDashboardView.swift"
    "Athena/CriticalAlertWindow.swift"
    "Athena/TribunalDecisionWindow.swift"
    "Athena/SystemEmergencyWindow.swift"
)

# Move our clean files to temp
TEMP_ATHENA="$ROOT/.temp_athena_clean"
mkdir -p "$TEMP_ATHENA"
for file in "${KEEP_FILES[@]}"; do
    if [[ -f "$DEST/$file" ]]; then
        mkdir -p "$TEMP_ATHENA/$(dirname "$file")"
        cp "$DEST/$file" "$TEMP_ATHENA/$file"
        echo "   Preserved: $file"
    fi
done

# Copy full NeuroForge implementation
echo ""
echo "📦 Copying NeuroForge implementation..."

# Models
mkdir -p "$DEST/Models"
cp -f "$SOURCE/Models/"*.swift "$DEST/Models/" 2>/dev/null || true

# Network
mkdir -p "$DEST/Network"
cp -f "$SOURCE/Network/"*.swift "$DEST/Network/" 2>/dev/null || true

# Config
mkdir -p "$DEST/Config"
cp -f "$SOURCE/Config/"*.swift "$DEST/Config/" 2>/dev/null || true

# Design
mkdir -p "$DEST/Design"
cp -f "$SOURCE/Design/"*.swift "$DEST/Design/" 2>/dev/null || true

# Features
mkdir -p "$DEST/Features"
cp -f "$SOURCE/Features/"*.swift "$DEST/Features/" 2>/dev/null || true

# Services
mkdir -p "$DEST/Services"
cp -f "$SOURCE/Services/"*.swift "$DEST/Services/" 2>/dev/null || true

# Views
mkdir -p "$DEST/Views"
cp -f "$SOURCE/Views/"*.swift "$DEST/Views/" 2>/dev/null || true

# Components
mkdir -p "$DEST/Components"
cp -f "$SOURCE/Components/"*.swift "$DEST/Components/" 2>/dev/null || true

# Diagnostics
mkdir -p "$DEST/Diagnostics"
cp -f "$SOURCE/Diagnostics/"*.swift "$DEST/Diagnostics/" 2>/dev/null || true

# Utils
mkdir -p "$DEST/Utils"
cp -f "$SOURCE/Utils/"*.swift "$DEST/Utils/" 2>/dev/null || true

# Root-level helpers
for file in VoiceRecorder.swift ProfileManager.swift LayoutManager.swift WakeWordDetector.swift ImagePicker.swift ToggleButton.swift LoginView.swift ContentView.swift; do
    if [[ -f "$SOURCE/$file" ]]; then
        cp -f "$SOURCE/$file" "$DEST/"
    fi
done

echo "✅ Copied NeuroForge implementation"

# Restore our clean Athena pop-out windows
echo ""
echo "🔗 Integrating Athena pop-out windows..."
for file in "${KEEP_FILES[@]}"; do
    if [[ -f "$TEMP_ATHENA/$file" ]]; then
        mkdir -p "$DEST/$(dirname "$file")"
        cp -f "$TEMP_ATHENA/$file" "$DEST/$file"
        echo "   Restored: $file"
    fi
done

# Create unified main.swift that combines both
cat > "$DEST/main.swift" <<'SWIFT'
import SwiftUI

@main
struct NeuroForgeApp: App {
    @StateObject private var athenaState = AthenaState()
    @StateObject private var profileManager = ProfileManager()
    @State private var voice = VoiceManager()
    
    var body: some Scene {
        // Main chat window
        WindowGroup {
            if profileManager.hasProfile {
                ContentView()
                    .environmentObject(athenaState)
                    .environmentObject(profileManager)
                    .onReceive(NotificationCenter.default.publisher(for: .ShowCriticalAlert)) { note in
                        if let a = note.object as? CriticalAlert {
                            voice.speak("Critical alert: \(a.title)")
                            openWindow(id: "critical-alert")
                        }
                    }
                    .onReceive(NotificationCenter.default.publisher(for: .ShowTribunalDecision)) { note in
                        if let c = note.object as? TribunalCase {
                            voice.speak("Tribunal decision required for case \(c.caseID)")
                            openWindow(id: "tribunal-decision")
                        }
                    }
                    .onReceive(NotificationCenter.default.publisher(for: .ShowSystemEmergency)) { note in
                        if let e = note.object as? SystemEmergency {
                            voice.speak("System emergency: \(e.title)")
                            openWindow(id: "system-emergency")
                        }
                    }
            } else {
                LoginView()
                    .environmentObject(profileManager)
            }
        }
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
        
        // Athena Dashboard window (Cmd+Shift+A)
        Window("Athena Dashboard", id: "athena-dashboard") {
            AthenaDashboardView()
                .environmentObject(athenaState)
                .frame(minWidth: 800, minHeight: 500)
        }
        .keyboardShortcut("a", modifiers: [.command, .shift])
        
        // Pop-out windows (triggered programmatically)
        Window("🚨 Critical Alert", id: "critical-alert") {
            if let a = athenaState.lastAlert {
                CriticalAlertWindow(alert: a)
            } else {
                Text("No alert").padding()
            }
        }
        .defaultPosition(.center)
        
        Window("⚖️ Tribunal Decision Required", id: "tribunal-decision") {
            if let c = athenaState.lastCase {
                TribunalDecisionWindow(case: c)
            } else {
                Text("No case").padding()
            }
        }
        .defaultPosition(.center)
        
        Window("🚨 SYSTEM EMERGENCY", id: "system-emergency") {
            if let e = athenaState.lastEmergency {
                SystemEmergencyWindow(emergency: e)
            } else {
                Text("No emergency").padding()
            }
        }
        .defaultPosition(.center)
    }
    
    private func openWindow(id: String) {
        #if canImport(AppKit)
        if let w = NSApp.windows.first(where: { $0.identifier?.rawValue == id }) {
            NSApp.activate(ignoringOtherApps: true)
            w.makeKeyAndOrderFront(nil)
        }
        #endif
    }
}
SWIFT

echo "✅ Created unified main.swift"

# Clean up temp
rm -rf "$TEMP_ATHENA"

echo ""
echo "🧹 Stripping SwiftUI previews..."
if command -v gsed >/dev/null 2>&1; then SED=gsed; else SED=sed; fi
find "$DEST" -name '*.swift' -print0 | xargs -0 "$SED" -E -i '' '/^#if DEBUG *$/,/#endif/{ /#Preview/,/^}/d }'

echo ""
echo "✅ Restoration complete!"
echo ""
echo "📁 Structure:"
echo "   ✅ Models (ChatMessage, ChatTask, etc.)"
echo "   ✅ Network (APIClient, NetworkInterceptor)"
echo "   ✅ Config (AppConfig, APIBase)"
echo "   ✅ Design (AppleColors, AppleTypography)"
echo "   ✅ Features (HealthBanner, etc.)"
echo "   ✅ Services (ChatService)"
echo "   ✅ Views (NeuroForgeChatView)"
echo "   ✅ Athena pop-outs (3 windows)"
echo ""
echo "🚀 Next: Update Package.swift dependencies"
echo "   cd NeuroForgeApp"
echo "   swift build"

