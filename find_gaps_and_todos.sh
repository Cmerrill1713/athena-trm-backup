#!/bin/bash
echo "🔍 SEARCHING FOR GAPS, TODOS, AND PLACEHOLDERS"
echo "========================================================================"
echo ""

# Search for TODOs
echo "1️⃣  Searching for TODO comments..."
echo "--------------------------------------------------------------------"
grep -r "TODO\|FIXME\|XXX\|HACK" \
  --include="*.py" --include="*.go" --include="*.rs" --include="*.js" \
  services/ agi_core/ ai_republic/ AI-Projects/universal-ai-tools/ \
  2>/dev/null | head -30

echo ""
echo "2️⃣  Searching for placeholders..."
echo "--------------------------------------------------------------------"
grep -ri "placeholder\|not implemented\|coming soon\|stub\|mock" \
  --include="*.py" --include="*.go" --include="*.rs" \
  services/ agi_core/ ai_republic/ AI-Projects/universal-ai-tools/ \
  2>/dev/null | head -30

echo ""
echo "3️⃣  Searching for missing error handling..."
echo "--------------------------------------------------------------------"
grep -r "pass$\|pass #" \
  --include="*.py" \
  services/ agi_core/ ai_republic/ AI-Projects/universal-ai-tools/ \
  2>/dev/null | head -20

echo ""
echo "4️⃣  Searching for hardcoded values..."
echo "--------------------------------------------------------------------"
grep -r "localhost\|127\.0\.0\.1\|qwen" \
  --include="*.py" --include="*.html" --include="*.js" \
  services/ AI-Projects/universal-ai-tools/ ui/ \
  2>/dev/null | grep -v "BASE_URL\|BASE\|#" | head -20

echo ""
echo "5️⃣  Searching for disabled features..."
echo "--------------------------------------------------------------------"
grep -ri "disabled\|commented out\|skip\|ignore" \
  --include="*.py" \
  services/ agi_core/ ai_republic/ AI-Projects/universal-ai-tools/ \
  2>/dev/null | grep -v "gitignore\|.git/" | head -20

echo ""
echo "✅ Gap search complete!"
