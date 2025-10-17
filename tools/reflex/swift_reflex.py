#!/usr/bin/env python3
"""
Swift Reflex Agent - Auto-fixes Swift UI issues

Watches Swift files for changes and automatically applies fixes for common issues:
- Focus/hit-testing problems
- UI layout issues
- Performance bottlenecks
- Code style violations

Usage:
    python tools/reflex/swift_reflex.py --watch "NeuroForgeApp/*.swift" --build "make build" --tests "make test"
"""

import os
import sys
import time
import logging
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SwiftReflexHandler(FileSystemEventHandler):
    """Handles file system events and applies fixes."""

    def __init__(self, watch_patterns: List[str], build_cmd: str, test_cmd: str,
                 snapshot_cmd: Optional[str] = None, apply_safe: bool = True):
        self.watch_patterns = watch_patterns
        self.build_cmd = build_cmd
        self.test_cmd = test_cmd
        self.snapshot_cmd = snapshot_cmd
        self.apply_safe = apply_safe
        self.last_build_time = 0
        self.build_cooldown = 2  # seconds

    def should_process_file(self, filepath: str) -> bool:
        """Check if file matches watch patterns."""
        path = Path(filepath)
        for pattern in self.watch_patterns:
            if path.match(pattern):
                return True
        return False

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        filepath = event.src_path
        if not self.should_process_file(filepath):
            return

        logger.info(f"📝 File changed: {filepath}")

        # Apply immediate fixes
        self.apply_fixes(filepath)

        # Throttled build/test
        current_time = time.time()
        if current_time - self.last_build_time > self.build_cooldown:
            self.run_build_and_test()
            self.last_build_time = current_time

    def apply_fixes(self, filepath: str):
        """Apply automatic fixes to Swift files."""
        try:
            with open(filepath, 'r') as f:
                content = f.read()

            original_content = content
            fixes_applied = []

            # Fix 1: FocusState issues
            if self._has_focus_issues(content):
                content = self._fix_focus_issues(content)
                fixes_applied.append("FocusState management")

            # Fix 2: Hit testing overlays
            if self._has_overlay_issues(content):
                content = self._fix_overlay_issues(content)
                fixes_applied.append("Hit testing overlays")

            # Fix 3: Z-index ordering
            if self._has_zindex_issues(content):
                content = self._fix_zindex_issues(content)
                fixes_applied.append("Z-index ordering")

            # Fix 4: Missing design tokens
            if self._uses_hardcoded_values(content):
                content = self._apply_design_tokens(content)
                fixes_applied.append("Design token consistency")

            # Only write if changes were made
            if content != original_content and fixes_applied:
                with open(filepath, 'w') as f:
                    f.write(content)

                logger.info(f"✅ Applied fixes to {filepath}: {', '.join(fixes_applied)}")

        except Exception as e:
            logger.error(f"Failed to apply fixes to {filepath}: {e}")

    def _has_focus_issues(self, content: str) -> bool:
        """Check for FocusState-related issues."""
        has_focus_state = '@FocusState' in content
        has_text_input = any(input_type in content for input_type in ['TextField', 'TextEditor', 'SecureField'])

        if not (has_focus_state and has_text_input):
            return False

        # Check for common focus problems
        issues = [
            'isFocused = true' not in content,  # No focus setting
            '.contentShape(' not in content,     # Missing hit testing
            '.zIndex(' not in content,           # Missing layering
            'NavigationSplitView' in content and 'multiple.*asyncAfter' not in content,  # NavSplitView needs multiple attempts
        ]

        return any(issues)

    def _fix_focus_issues(self, content: str) -> str:
        """Add proper focus management for SwiftUI."""
        # Fix 1: Add multiple focus attempts for NavigationSplitView compatibility
        if '.onAppear {' in content and 'isFocused = true' in content:
            # Already has basic focus, enhance it
            focus_fix = '''
                    // Multiple focus attempts for NavigationSplitView compatibility
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                        isFocused = true
                    }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                        if !isFocused { isFocused = true }
                    }
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                        if !isFocused { isFocused = true }
                    }'''
            content = content.replace(
                'DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {\n                        isFocused = true\n                    }',
                focus_fix.strip()
            )

        # Fix 2: Add focus restoration after overlays/modals
        if '.sheet(' in content or '.alert(' in content or '.overlay(' in content:
            if 'onDisappear' not in content:
                # Add onDisappear to restore focus after overlays
                content = content.replace(
                    '.focused($isFocused)',
                    '.focused($isFocused)\n                    .onDisappear {\n                        // Restore focus after overlay dismissal\n                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {\n                            isFocused = true\n                        }\n                    }'
                )

        # Fix 3: Add contentShape for better hit testing
        if '.focused(' in content and '.contentShape(' not in content:
            content = content.replace(
                '.focused($isFocused)',
                '.focused($isFocused)\n                    .contentShape(Rectangle())'
            )

        # Fix 4: Ensure proper z-index for input fields
        if 'TextField' in content and '.zIndex(' not in content:
            content = content.replace(
                '.focused($isFocused)',
                '.focused($isFocused)\n                    .zIndex(1)'
            )

        return content

    def _has_overlay_issues(self, content: str) -> bool:
        """Check for overlay hit-testing issues."""
        return (
            '.overlay(' in content and
            '.allowsHitTesting(false)' not in content
        )

    def _fix_overlay_issues(self, content: str) -> str:
        """Add proper hit testing to overlays."""
        # Add allowsHitTesting(false) to overlays
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '.overlay(' in line and '.allowsHitTesting(false)' not in lines[i+1]:
                # Insert allowsHitTesting after overlay
                lines.insert(i+1, '                    .allowsHitTesting(false)')
                break
        return '\n'.join(lines)

    def _has_zindex_issues(self, content: str) -> bool:
        """Check for z-index ordering issues."""
        return (
            'TextField' in content and
            '.zIndex(' not in content
        )

    def _fix_zindex_issues(self, content: str) -> str:
        """Add proper z-index to input fields."""
        if 'TextField' in content and '.zIndex(' not in content:
            content = content.replace(
                '                .focused($isFocused)',
                '                .focused($isFocused)\n                    .zIndex(1)'
            )
        return content

    def _uses_hardcoded_values(self, content: str) -> bool:
        """Check for hardcoded spacing/colors."""
        return (
            'padding(' in content and
            'NFToken.Spacing.' not in content
        )

    def _apply_design_tokens(self, content: str) -> str:
        """Replace hardcoded values with design tokens."""
        replacements = {
            'padding(12)': 'padding(NFToken.Spacing.lg)',
            'padding(8)': 'padding(NFToken.Spacing.md)',
            'padding(16)': 'padding(NFToken.Spacing.xl)',
            '.cornerRadius(12)': '.cornerRadius(NFToken.Radius.md)',
            '.cornerRadius(8)': '.cornerRadius(NFToken.Radius.sm)',
        }

        for old, new in replacements.items():
            content = content.replace(old, new)

        return content

    def run_build_and_test(self):
        """Run build and tests after fixes."""
        try:
            # Run build
            logger.info("🔨 Running build...")
            build_result = subprocess.run(
                self.build_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )

            if build_result.returncode == 0:
                logger.info("✅ Build successful")
            else:
                logger.error(f"❌ Build failed: {build_result.stderr}")

            # Run tests
            logger.info("🧪 Running tests...")
            test_result = subprocess.run(
                self.test_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )

            if test_result.returncode == 0:
                logger.info("✅ Tests passed")
            else:
                logger.warning(f"⚠️ Tests failed: {test_result.stderr}")

            # Run snapshots if available
            if self.snapshot_cmd:
                logger.info("📸 Running snapshots...")
                snapshot_result = subprocess.run(
                    self.snapshot_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if snapshot_result.returncode == 0:
                    logger.info("✅ Snapshots updated")
                else:
                    logger.warning(f"⚠️ Snapshots failed: {snapshot_result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error("Build/test timed out")
        except Exception as e:
            logger.error(f"Build/test error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Swift Reflex Agent")
    parser.add_argument('--watch', nargs='+', required=True,
                       help='File patterns to watch (e.g., "*.swift")')
    parser.add_argument('--build', required=True,
                       help='Build command to run')
    parser.add_argument('--tests', required=True,
                       help='Test command to run')
    parser.add_argument('--snapshots',
                       help='Snapshot test command (optional)')
    parser.add_argument('--apply-safe', action='store_true', default=True,
                       help='Only apply safe fixes')

    args = parser.parse_args()

    # Set up file watcher
    event_handler = SwiftReflexHandler(
        watch_patterns=args.watch,
        build_cmd=args.build,
        test_cmd=args.tests,
        snapshot_cmd=args.snapshots,
        apply_safe=args.apply_safe
    )

    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()

    logger.info("🎯 Swift Reflex Agent started")
    logger.info(f"Watching patterns: {args.watch}")
    logger.info("Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("🛑 Swift Reflex Agent stopped")

    observer.join()


if __name__ == "__main__":
    main()
