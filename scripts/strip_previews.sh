#!/usr/bin/env bash
set -euo pipefail
# Comment out PreviewProvider blocks (safe for CI)
find NeuroForgeApp/Sources -name "*.swift" -type f | while read -r f; do
  awk '
    /struct .*PreviewProvider/ {inprev=1}
    inprev==1 {print "//[PREVIEW] " $0; if ($0 ~ /}/) c++}
    inprev!=1 {print $0}
    /struct .*PreviewProvider/ { }
    { if(inprev==1 && $0 ~ /^}/) depth++ }
  ' "$f" > "$f.tmp" || true
  # Only replace if we actually tagged something
  if grep -q '\[PREVIEW\]' "$f.tmp" 2>/dev/null; then mv "$f.tmp" "$f"; else rm -f "$f.tmp"; fi
done
