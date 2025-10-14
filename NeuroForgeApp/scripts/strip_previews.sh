#!/usr/bin/env bash
set -euo pipefail

# Remove SwiftUI Preview provider membership by compiling them only for PREVIEWS build
# Or compile-guard them if they lack guards
echo "🧹 Stripping SwiftUI previews from app target..."

find Sources -name '*.swift' -type f | while read -r f; do
  if grep -q 'struct .*_Previews' "$f" && ! grep -q '#if DEBUG' "$f"; then
    echo "  → Adding DEBUG guards to $f"
    perl -0777 -pe 's/(struct\s+\w+_Previews[\s\S]*?})/#if DEBUG \1 \n#endif/g' -i "$f"
  fi
done

# Also remove any standalone preview blocks
find Sources -name '*.swift' -type f -exec sed -i '' '/^#Preview/,/^}/d' {} \;

echo "✅ SwiftUI previews stripped"
