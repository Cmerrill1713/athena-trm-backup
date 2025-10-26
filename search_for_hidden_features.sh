#!/bin/bash
echo "🕵️  SEARCHING FOR HIDDEN FEATURES"
echo "========================================================================"
echo ""

echo "1️⃣  Checking for background workers/cron jobs..."
echo "--------------------------------------------------------------------"
# Look for cron, background, worker files
find services/ agi_core/ -name "*worker*" -o -name "*cron*" -o -name "*background*" -o -name "*scheduler*" 2>/dev/null | head -10

echo ""
echo "2️⃣  Checking for WebSocket endpoints..."
echo "--------------------------------------------------------------------"
grep -r "websocket\|WebSocket\|ws://" --include="*.py" --include="*.js" \
  services/ AI-Projects/universal-ai-tools/ ui/ 2>/dev/null | \
  grep -v node_modules | head -10

echo ""
echo "3️⃣  Checking for CLI tools/scripts..."
echo "--------------------------------------------------------------------"
find services/ agi_core/ ai_republic/ -name "cli.py" -o -name "*_cli.py" -o -name "main.py" 2>/dev/null | head -10

echo ""
echo "4️⃣  Checking for admin/debug endpoints..."
echo "--------------------------------------------------------------------"
grep -r "@app.*admin\|@app.*debug\|/admin\|/debug" --include="*.py" \
  services/ agi_core/ ai_republic/ AI-Projects/universal-ai-tools/ 2>/dev/null | head -10

echo ""
echo "5️⃣  Checking for batch/bulk operations..."
echo "--------------------------------------------------------------------"
grep -r "batch\|bulk\|/import\|/export" --include="*.py" \
  services/ AI-Projects/universal-ai-tools/api/ 2>/dev/null | \
  grep "@app\|@router" | head -10

echo ""
echo "6️⃣  Checking for internal APIs not exposed..."
echo "--------------------------------------------------------------------"
grep -r "internal_only\|private\|_internal" --include="*.py" \
  services/ agi_core/ 2>/dev/null | head -10

echo ""
echo "✅ Hidden feature search complete!"
