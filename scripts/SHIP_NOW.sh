#!/bin/bash
set -euo pipefail

# Final Ship Script for v0.9.2
# Run this to tag, push, and open GitHub Release

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║              🚀  SHIPPING v0.9.2 NOW!  🚀                    ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Ensure we're on main
echo "📌 Checking out main branch..."
git checkout main
git pull --ff-only
echo "✅ On main and up to date"
echo ""

# Tag the release
echo "🏷️  Tagging v0.9.2..."
git tag v0.9.2 -a -m "v0.9.2: AI Coding Knowledge Platform + Operational Excellence

Features:
- 170 AI coding transcripts from 9 creators
- RAG search (9.78ms)
- Vision + RAG integration
- Trace Panel with explainability
- First-Run Wizard
- 8 services (all healthy)
- Complete CI/CD automation
- 10/10 eval fixtures passing

Status: Production Ready 🟢"

echo "✅ Tagged v0.9.2"
echo ""

# Push
echo "📤 Pushing to GitHub..."
git push origin main
git push --tags

echo "✅ Pushed to GitHub"
echo ""

# Open GitHub Release page
echo "🌐 Opening GitHub Release page..."
sleep 2
open "https://github.com/Cmerrill1713/athena-trm-backup/releases/new?tag=v0.9.2&title=v0.9.2%20-%20AI%20Coding%20Knowledge%20Platform%20%2B%20Operational%20Excellence"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                   ✅  SHIPPED!  ✅                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 NEXT STEPS:"
echo "1. GitHub Release page should be open"
echo "2. Copy/paste from: RELEASE_NOTES_v0.9.2.md"
echo "3. Click 'Publish Release'"
echo "4. Share INTERNAL_ANNOUNCEMENT.md with team"
echo "5. Start POST_LAUNCH_7DAY_PLAN.md (Day 0)"
echo ""
echo "🎯 MONITORING:"
echo "  Dashboard: http://localhost:8787"
echo "  Eval API: http://localhost:8788"
echo "  Trace Panel: In NeuroForgeApp"
echo ""
echo "🏆 LAUNCH IS BORING. PERFECT!"
