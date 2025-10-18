#!/usr/bin/env python3
"""
Test Swift Reflex Agent auto-patch capability
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from swift_reflex import SwiftReflexHandler


def test_focus_issue_detection():
    """Test that focus issues are detected correctly."""
    content = """
import SwiftUI

struct TestView: View {
    @FocusState private var isFocused: Bool
    
    var body: some View {
        TextField("Enter text", text: .constant(""))
            .focused($isFocused)
    }
}
"""
    
    handler = SwiftReflexHandler(
        watch_patterns=["*.swift"],
        build_cmd="echo 'build'",
        test_cmd="echo 'test'"
    )
    
    result = handler._has_focus_issues(content)
    print(f"✓ Focus issue detection: {result}")
    assert result == True, "Should detect missing focus management"
    

def test_focus_fix_application():
    """Test that focus fixes are applied correctly."""
    content = """
import SwiftUI

struct TestView: View {
    @FocusState private var isFocused: Bool
    
    var body: some View {
        TextField("Enter text", text: .constant(""))
            .focused($isFocused)
    }
}
"""
    
    handler = SwiftReflexHandler(
        watch_patterns=["*.swift"],
        build_cmd="echo 'build'",
        test_cmd="echo 'test'"
    )
    
    fixed_content = handler._fix_focus_issues(content)
    
    # Check that fixes were applied
    assert '.contentShape(Rectangle())' in fixed_content, "Should add contentShape"
    assert '.zIndex(' in fixed_content, "Should add z-index"
    
    print("✓ Focus fixes applied correctly")
    print("\n--- Fixed Content ---")
    print(fixed_content)
    print("--- End ---\n")


def test_overlay_issue_detection():
    """Test overlay hit-testing detection."""
    content = """
    .overlay(
        Text("Overlay")
    )
"""
    
    handler = SwiftReflexHandler(
        watch_patterns=["*.swift"],
        build_cmd="echo 'build'",
        test_cmd="echo 'test'"
    )
    
    result = handler._has_overlay_issues(content)
    print(f"✓ Overlay issue detection: {result}")
    assert result == True, "Should detect overlay without hit testing"


def test_design_token_detection():
    """Test hardcoded value detection."""
    content = """
    TextField("Test", text: .constant(""))
        .padding(12)
        .cornerRadius(8)
"""
    
    handler = SwiftReflexHandler(
        watch_patterns=["*.swift"],
        build_cmd="echo 'build'",
        test_cmd="echo 'test'"
    )
    
    result = handler._uses_hardcoded_values(content)
    print(f"✓ Hardcoded value detection: {result}")
    assert result == True, "Should detect hardcoded padding"


def test_design_token_replacement():
    """Test that design tokens replace hardcoded values."""
    content = """
    TextField("Test", text: .constant(""))
        .padding(12)
        .cornerRadius(8)
"""
    
    handler = SwiftReflexHandler(
        watch_patterns=["*.swift"],
        build_cmd="echo 'build'",
        test_cmd="echo 'test'"
    )
    
    fixed_content = handler._apply_design_tokens(content)
    
    assert 'NFToken.Spacing.lg' in fixed_content, "Should replace padding(12)"
    assert 'NFToken.Radius.sm' in fixed_content, "Should replace cornerRadius(8)"
    
    print("✓ Design tokens applied correctly")
    print("\n--- Fixed Content ---")
    print(fixed_content)
    print("--- End ---\n")


def test_full_fix_pipeline():
    """Test the complete fix pipeline on a realistic file."""
    content = """
import SwiftUI

struct ChatView: View {
    @FocusState private var isFocused: Bool
    @State private var text = ""
    
    var body: some View {
        VStack(spacing: 8) {
            TextField("Type a message", text: $text)
                .padding(12)
                .focused($isFocused)
                .onAppear {
                    isFocused = true
                }
            
            Button("Send") {
                print(text)
            }
            .padding(8)
        }
        .overlay(
            Text("Beta")
                .font(.caption)
        )
    }
}
"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.swift', delete=False) as f:
        f.write(content)
        temp_file = f.name
    
    try:
        handler = SwiftReflexHandler(
            watch_patterns=["*.swift"],
            build_cmd="echo 'build'",
            test_cmd="echo 'test'"
        )
        
        # Apply all fixes
        handler.apply_fixes(temp_file)
        
        # Read fixed content
        with open(temp_file, 'r') as f:
            fixed_content = f.read()
        
        print("✓ Full fix pipeline completed")
        print("\n--- Original ---")
        print(content)
        print("\n--- Fixed ---")
        print(fixed_content)
        print("--- End ---\n")
        
        # Verify fixes
        checks = [
            ('.contentShape(Rectangle())' in fixed_content, "contentShape added"),
            ('.zIndex(' in fixed_content, "z-index added"),
            ('NFToken.Spacing' in fixed_content, "Design tokens applied"),
        ]
        
        for check, description in checks:
            if check:
                print(f"✓ {description}")
            else:
                print(f"✗ {description}")
        
        assert all(check for check, _ in checks), "All fixes should be applied"
        
    finally:
        # Clean up
        os.unlink(temp_file)


def main():
    """Run all tests."""
    print("🧪 Testing Swift Reflex Agent Auto-Patch Capability\n")
    print("=" * 60)
    
    tests = [
        ("Focus Issue Detection", test_focus_issue_detection),
        ("Focus Fix Application", test_focus_fix_application),
        ("Overlay Issue Detection", test_overlay_issue_detection),
        ("Design Token Detection", test_design_token_detection),
        ("Design Token Replacement", test_design_token_replacement),
        ("Full Fix Pipeline", test_full_fix_pipeline),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Test: {test_name}")
        print("-" * 60)
        try:
            test_func()
            passed += 1
            print(f"✅ PASSED\n")
        except AssertionError as e:
            failed += 1
            print(f"❌ FAILED: {e}\n")
        except Exception as e:
            failed += 1
            print(f"❌ ERROR: {e}\n")
    
    print("=" * 60)
    print(f"\n📊 Test Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    
    if failed == 0:
        print("🎉 All tests passed! Swift Reflex auto-patch capability validated.")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

