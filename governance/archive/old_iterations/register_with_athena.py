#!/usr/bin/env python3
"""
Athena Tool Registration Script
Automatically registers NeuroForge platform tools with Athena
"""
import sys
import yaml
import requests
from pathlib import Path

def load_manifest():
    """Load tool manifest"""
    manifest_path = Path(__file__).parent / "athena_tools.yaml"
    with open(manifest_path) as f:
        return yaml.safe_load(f)

def register_via_api(tools, athena_url="http://127.0.0.1:8090"):
    """Register tools via Athena API"""
    print(f"🔌 Registering {len(tools)} tools with Athena at {athena_url}")

    for tool in tools:
        print(f"  → {tool['name']}")
        try:
            resp = requests.post(
                f"{athena_url}/api/tools/register",
                json=tool,
                timeout=5
            )
            if resp.status_code in (200, 201):
                print("    ✅ Registered")
            else:
                print(f"    ⚠️  {resp.status_code}: {resp.text[:100]}")
        except requests.exceptions.ConnectionError:
            print(f"    ⚠️  Athena not responding at {athena_url}")
            return False
        except Exception as e:
            print(f"    ❌ Error: {e}")

    return True

def register_via_file(tools, config_dir=None):
    """Register tools by writing to Athena's config directory"""
    if config_dir is None:
        config_dir = Path.home() / ".athena" / "config" / "tools"

    config_dir = Path(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)

    output_file = config_dir / "neuroforge.yaml"
    manifest_path = Path(__file__).parent / "athena_tools.yaml"

    print(f"📝 Writing tool manifest to {output_file}")

    # Copy full manifest
    with open(manifest_path) as f:
        content = f.read()

    with open(output_file, 'w') as f:
        f.write(content)

    print(f"✅ Wrote {len(tools)} tools to {output_file}")
    print("\n⚠️  Restart Athena to load new tools:")
    print("   cd athena && python restart.py")

    return True

def main():
    """Main registration flow"""
    manifest = load_manifest()
    tools = manifest['tools']

    print("🧠 Athena Tool Registration")
    print(f"   Tools: {len(tools)}")
    print(f"   Environment: {len(manifest.get('environment', {}))} vars")
    print()

    # Try API first, fall back to file
    if not register_via_api(tools):
        print("\n⚠️  API registration failed, trying file method...")
        register_via_file(tools)

    print("\n✅ Registration complete!")
    print("\nTest with:")
    print("  ./tools/stack_full.sh")
    print('  Say: "Bring everything online"')

if __name__ == "__main__":
    try:
        import yaml
    except ImportError:
        print("❌ PyYAML not found. Install with: pip install pyyaml")
        sys.exit(1)

    main()
