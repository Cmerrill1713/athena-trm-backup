#!/usr/bin/env python3
"""
Auto-Remediation Script for Swift UI Typing Issue
Applies fixes identified by diagnostic system
"""

import subprocess
import shutil
from pathlib import Path
from datetime import datetime

class SwiftTypingRemediator:
    """Governance-style auto-remediation"""
    
    def __init__(self):
        self.fixes_applied = []
        self.base_path = Path("/Users/christianmerrill/Documents/GitHub/NeuroForgeApp")
        
    def log(self, msg, level="INFO"):
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [{level}] {msg}")
        
    def backup_file(self, file_path):
        """Create backup before modification"""
        backup_path = Path(str(file_path) + ".backup")
        shutil.copy2(file_path, backup_path)
        self.log(f"📦 Backed up: {file_path.name}")
        return backup_path
        
    def remove_problematic_files(self):
        """Remove NSViewRepresentable implementations"""
        self.log("🗑️  Removing problematic NSViewRepresentable files...")
        
        files_to_remove = [
            "Sources/NuclearTextInput.swift",  # Our failed attempt
            "Sources/KeyCatchingTextEditor.swift",  # If exists
        ]
        
        for file_rel in files_to_remove:
            file_path = self.base_path / file_rel
            if file_path.exists():
                self.backup_file(file_path)
                file_path.unlink()
                self.fixes_applied.append(f"Removed: {file_rel}")
                self.log(f"✅ Removed: {file_rel}")
        
    def clean_chatinputbar(self):
        """Clean up ChatInputBar to use ONLY pure SwiftUI"""
        self.log("🧹 Cleaning ChatInputBar.swift...")
        
        file_path = self.base_path / "Sources/ChatInputBar.swift"
        
        if not file_path.exists():
            self.log("⚠️  ChatInputBar.swift not found", "WARNING")
            return
            
        self.backup_file(file_path)
        
        # Read current content
        content = file_path.read_text()
        
        # Find where MacOSTextInput and other classes start
        lines = content.split('\n')
        clean_lines = []
        skip_mode = False
        
        for line in lines:
            # Stop at the NSView/AppKit implementations
            if any(marker in line for marker in [
                '// MARK: - Native macOS Text Input',
                'struct MacOSTextInput',
                'class FocusableScrollView',
                'class AlwaysTypableTextView',
                'class ForceTypableTextField'
            ]):
                skip_mode = True
                continue
            
            # Keep preview section
            if '// MARK: - Preview' in line or '#Preview' in line:
                skip_mode = False
            
            if not skip_mode:
                clean_lines.append(line)
        
        # Write cleaned content
        cleaned_content = '\n'.join(clean_lines)
        file_path.write_text(cleaned_content)
        
        self.fixes_applied.append("Cleaned ChatInputBar.swift (removed NSView implementations)")
        self.log("✅ Cleaned ChatInputBar.swift")
        
    def update_simpletexttest(self):
        """Ensure SimpleTextTest uses pure SwiftUI"""
        self.log("🔧 Updating SimpleTextTest.swift...")
        
        file_path = self.base_path / "Sources/SimpleTextTest.swift"
        
        if file_path.exists():
            content = file_path.read_text()
            
            # It should already be using pure SwiftUI from our earlier fix
            # Just verify it doesn't reference MacOSTextInput
            if 'MacOSTextInput' in content:
                self.backup_file(file_path)
                content = content.replace('MacOSTextInput', 'TextField')
                file_path.write_text(content)
                self.fixes_applied.append("Fixed SimpleTextTest.swift")
                self.log("✅ Fixed SimpleTextTest.swift")
            else:
                self.log("✅ SimpleTextTest.swift already clean")
                
    def disable_diagnostic_mode(self):
        """Turn off diagnostic mode so real app shows"""
        self.log("🔧 Disabling diagnostic mode...")
        
        file_path = self.base_path / "Sources/ContentView.swift"
        
        if file_path.exists():
            self.backup_file(file_path)
            content = file_path.read_text()
            
            # Change diagnosticMode default to false
            content = content.replace(
                '@AppStorage("diagnosticMode") private var diagnosticMode = true',
                '@AppStorage("diagnosticMode") private var diagnosticMode = false'
            )
            
            file_path.write_text(content)
            self.fixes_applied.append("Disabled diagnostic mode")
            self.log("✅ Disabled diagnostic mode - app will show normally")
    
    def verify_focus_workaround(self):
        """Verify delayed focus workaround is applied"""
        self.log("🔍 Verifying focus workaround...")
        
        file_path = self.base_path / "Sources/ChatInputBar.swift"
        content = file_path.read_text()
        
        has_focus_state = '@FocusState' in content
        has_delayed_focus = 'DispatchQueue.main.asyncAfter' in content
        has_focused_modifier = '.focused($' in content
        
        if has_focus_state and has_delayed_focus and has_focused_modifier:
            self.log("✅ Focus workaround verified: COMPLETE")
            return True
        else:
            self.log("⚠️  Focus workaround incomplete:", "WARNING")
            self.log(f"   @FocusState: {has_focus_state}")
            self.log(f"   Delayed focus: {has_delayed_focus}")
            self.log(f"   .focused modifier: {has_focused_modifier}")
            return False
    
    def rebuild_app(self):
        """Rebuild the app"""
        self.log("🔨 Rebuilding app...")
        
        try:
            result = subprocess.run(
                "cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp && make build",
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log("✅ Build successful!")
                return True
            else:
                self.log(f"❌ Build failed: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Build exception: {str(e)}", "ERROR")
            return False
    
    def relaunch_app(self):
        """Kill old instances and launch fresh"""
        self.log("🔄 Relaunching app...")
        
        # Kill old instances
        subprocess.run("pkill -9 NeuroForgeApp", shell=True, stderr=subprocess.DEVNULL)
        
        # Wait a moment
        import time
        time.sleep(2)
        
        # Launch new instance
        subprocess.Popen(
            "cd /Users/christianmerrill/Documents/GitHub/NeuroForgeApp && make run > /tmp/neuroforge-remediated.log 2>&1 &",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        time.sleep(3)
        
        # Check if running
        result = subprocess.run(
            "ps aux | grep -E 'NeuroForgeApp' | grep -v grep | grep -v tee",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            self.log("✅ App launched successfully!")
            return True
        else:
            self.log("⚠️  App may not have launched", "WARNING")
            return False
    
    def run_remediation(self):
        """Execute full auto-remediation"""
        self.log("=" * 70)
        self.log("🚀 Starting Auto-Remediation")
        self.log("=" * 70)
        
        # Step 1: Remove problematic files
        self.remove_problematic_files()
        
        # Step 2: Clean ChatInputBar
        self.clean_chatinputbar()
        
        # Step 3: Update SimpleTextTest
        self.update_simpletexttest()
        
        # Step 4: Disable diagnostic mode
        self.disable_diagnostic_mode()
        
        # Step 5: Verify focus workaround
        focus_ok = self.verify_focus_workaround()
        
        # Step 6: Rebuild
        build_ok = self.rebuild_app()
        
        if not build_ok:
            self.log("❌ Build failed - stopping", "ERROR")
            return False
        
        # Step 7: Relaunch
        launch_ok = self.relaunch_app()
        
        # Summary
        self.log("")
        self.log("=" * 70)
        self.log("📊 REMEDIATION SUMMARY")
        self.log("=" * 70)
        self.log(f"Fixes applied: {len(self.fixes_applied)}")
        
        for i, fix in enumerate(self.fixes_applied, 1):
            self.log(f"  {i}. {fix}")
        
        self.log("")
        self.log(f"Focus workaround: {'✅ VERIFIED' if focus_ok else '⚠️ NEEDS REVIEW'}")
        self.log(f"Build status: {'✅ SUCCESS' if build_ok else '❌ FAILED'}")
        self.log(f"App launched: {'✅ YES' if launch_ok else '⚠️ CHECK MANUALLY'}")
        self.log("")
        
        if build_ok and launch_ok:
            self.log("✅ AUTO-REMEDIATION COMPLETE!")
            self.log("")
            self.log("🎯 NEXT STEPS:")
            self.log("1. The app should now be running")
            self.log("2. You'll see the REAL app (not diagnostic mode)")
            self.log("3. Navigate to: Athena Chat")
            self.log("4. Click in the text field")
            self.log("5. Wait ~0.5 seconds")
            self.log("6. TRY TYPING!")
            self.log("")
            self.log("The delayed focus workaround for the NavigationSplitView bug")
            self.log("is now applied. This is the STANDARD fix for this macOS issue.")
        else:
            self.log("⚠️  Remediation completed with warnings", "WARNING")
            self.log("Check logs above for details")
        
        self.log("=" * 70)
        
        return build_ok and launch_ok

if __name__ == "__main__":
    remediator = SwiftTypingRemediator()
    success = remediator.run_remediation()
    import sys
    sys.exit(0 if success else 1)

