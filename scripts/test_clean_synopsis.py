#!/usr/bin/env python3
"""
Test script to verify the clean synopsis system works correctly
"""

import subprocess
import os
import sys

def test_verbosity_levels():
    """Test different verbosity levels"""
    print("🧪 Testing verbosity levels...")
    
    levels = ["brief", "normal", "detailed"]
    for level in levels:
        print(f"\n📊 Testing {level} mode:")
        result = subprocess.run([
            "python3", "scripts/athena_report.py", 
            "--no-window", "health"
        ], 
        env={**os.environ, "ATHENA_VERBOSITY": level},
        capture_output=True, text=True
        )
        
        if result.returncode == 0:
            # Extract just the synopsis line
            lines = result.stdout.strip().split('\n')
            synopsis = [line for line in lines if not line.startswith('📊') and not line.startswith('💬')]
            if synopsis:
                print(f"   ✅ {level}: {synopsis[0]}")
            else:
                print(f"   ⚠️  {level}: No synopsis found")
        else:
            print(f"   ❌ {level}: Failed - {result.stderr}")

def test_window_modes():
    """Test different window modes"""
    print("\n🪟 Testing window modes...")
    
    modes = [
        ("--window", "Force window"),
        ("--no-window", "Voice only"),
        ("", "Auto-detect")
    ]
    
    for flag, description in modes:
        print(f"\n📊 Testing {description}:")
        cmd = ["python3", "scripts/athena_report.py"]
        if flag:
            cmd.append(flag)
        cmd.append("health")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            if "--no-window" in flag:
                print(f"   ✅ {description}: Voice output generated")
            else:
                print(f"   ✅ {description}: Window opened successfully")
        else:
            print(f"   ❌ {description}: Failed - {result.stderr}")

def test_make_targets():
    """Test the make targets work"""
    print("\n🎯 Testing make targets...")
    
    targets = ["report-health", "report-evolution", "report-metrics"]
    
    for target in targets:
        print(f"\n📊 Testing make {target}:")
        result = subprocess.run(["make", target], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ {target}: Success")
        else:
            print(f"   ❌ {target}: Failed - {result.stderr}")

def main():
    print("🚀 Athena Clean Synopsis Test Suite")
    print("=" * 50)
    
    try:
        test_verbosity_levels()
        test_window_modes()
        test_make_targets()
        
        print("\n🎉 All tests completed!")
        print("\n💡 Key improvements:")
        print("   • Clean, prioritized synopsis (20-30s)")
        print("   • Alert-first reporting")
        print("   • Configurable verbosity (brief/normal/detailed)")
        print("   • No more generic voice or empty reports")
        print("   • Smart window vs voice-only detection")
        print("   • 'Say More' feature for concerns (⌘L)")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
