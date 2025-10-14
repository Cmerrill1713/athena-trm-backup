#!/usr/bin/env python3
"""
Add new Athena files to NeuroForgeApp Xcode project
"""

import os
import sys
import subprocess

def main():
    print("🔧 Adding Athena files to Xcode project...")
    
    # Files to add (relative to NeuroForgeApp directory)
    files_to_add = [
        "Sources/AthenaModels.swift",
        "Sources/AthenaState.swift",
        "Sources/VoiceManager.swift",
        "Sources/Notifications+App.swift",
        "Sources/AthenaDashboardView.swift",
        "Sources/Athena/CriticalAlertWindow.swift",
        "Sources/Athena/TribunalDecisionWindow.swift",
        "Sources/Athena/SystemEmergencyWindow.swift",
    ]
    
    os.chdir("NeuroForgeApp")
    
    # Verify files exist
    print("\n📂 Verifying files...")
    missing = []
    for f in files_to_add:
        if os.path.exists(f):
            print(f"  ✅ {f}")
        else:
            print(f"  ❌ {f} (MISSING)")
            missing.append(f)
    
    if missing:
        print(f"\n❌ {len(missing)} files missing. Aborting.")
        sys.exit(1)
    
    print("\n🛠️  Using xed (Xcode command line) to add files...")
    
    # Use xed to add files to the currently open project
    # This is simpler than manipulating pbxproj directly
    for f in files_to_add:
        # Open each file in Xcode, which will prompt to add to project
        try:
            subprocess.run(['xed', '-a', f], check=False)
        except Exception as e:
            print(f"⚠️  Could not auto-add {f}: {e}")
    
    print("\n✅ Files opened in Xcode!")
    print("\n📝 Next steps:")
    print("1. In Xcode, you'll see prompts to add files to target")
    print("2. For each file, click 'Add to NeuroForgeApp target'")
    print("3. Or: Right-click Sources → Add Files... → Select all 8 files manually")
    print("4. Clean (Shift+Cmd+K)")
    print("5. Build (Cmd+B)")
    print("6. Run (Cmd+R)")
    print("\n🎯 Expected: Zero errors, app launches with Athena Dashboard!")

if __name__ == "__main__":
    main()

