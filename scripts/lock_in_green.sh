#!/usr/bin/env bash
set -euo pipefail

# 0) preflight
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "Not a git repo."; exit 1; }
mkdir -p .github/workflows scripts

# 1) Weekly audit workflow (separate file, safe to add)
cat > .github/workflows/weekly-audit.yml <<'YAML'
name: Weekly Audit (Comprehensive Smoke)
on:
  schedule:
    - cron: '0 5 * * 1'  # Every Monday 05:00 UTC
  workflow_dispatch:

jobs:
  weekly-audit:
    runs-on: macos-14
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v4

      - name: Cache Swift DerivedData
        uses: actions/cache@v4
        with:
          path: ~/Library/Developer/Xcode/DerivedData
          key: swift-${{ runner.os }}-${{ hashFiles('**/Package.resolved') }}

      - name: Run comprehensive audit smoke
        run: bash scripts/audit_smoke.sh

      - name: Upload Audit Artifacts (always)
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: audit-artifacts-${{ github.sha }}
          path: artifacts/audit-*/

      - name: Publish JUnit Test Results
        if: always()
        uses: mikepenz/action-junit-report@v4
        with:
          report_paths: 'artifacts/audit-*/junit.xml'
          fail_on_failure: true
YAML

# 2) Local pre-push hook (skip for docs-only commits)
mkdir -p .git/hooks
cat > .git/hooks/pre-push <<'HOOK'
#!/usr/bin/env bash
set -euo pipefail
echo "🔎 Running audit smoke before push…"
if git diff --cached --name-only | grep -vqE '^(README|docs/|.*\.md)$'; then
  make audit-smoke
else
  echo "📝 Docs-only changes detected, skipping audit."
fi
HOOK
chmod +x .git/hooks/pre-push

# 3) Commit the automation bits (idempotent)
git add .github/workflows/weekly-audit.yml .git/hooks/pre-push || true
if ! git diff --cached --quiet; then
  git commit -m "chore: automation guardrails (weekly audit + pre-push)"
fi

# 4) Tag a known-good baseline (only if not already tagged)
TAG="v1.0.0-audit-green"
if ! git rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
  # only tag if working tree is clean; otherwise just skip tag
  if git diff --quiet && git diff --cached --quiet; then
    git tag "$TAG"
  else
    echo "⚠️ Working tree not clean; skipping tag $TAG. You can tag later with: git tag $TAG && git push origin $TAG"
  fi
fi

# 5) Push (branch + tags)
git push -u origin "$(git rev-parse --abbrev-ref HEAD)" || true
git push origin --tags || true

# 6) Try to enable branch protection via gh (best effort)
set +e
if command -v gh >/dev/null 2>&1; then
  ORIGIN_URL="$(git remote get-url origin || true)"
  if [[ "$ORIGIN_URL" =~ github.com[:/]+([^/]+)/([^/.]+) ]]; then
    OWNER="${BASH_REMATCH[1]}"; REPO="${BASH_REMATCH[2]}"
    echo "🔐 Attempting to set branch protection on ${OWNER}/${REPO}…"
    gh api \
      -X PUT \
      -H "Accept: application/vnd.github+json" \
      "/repos/${OWNER}/${REPO}/branches/main/protection" \
      -f required_status_checks.strict=true \
      -f enforce_admins=true \
      -f restrictions='' \
      -F required_status_checks.contexts[]="audit-smoke" \
      -F required_status_checks.contexts[]="ci-core" \
      -F required_status_checks.contexts[]="build-frontend" \
      -F required_status_checks.contexts[]="ci-summary" \
      -F required_pull_request_reviews.required_approving_review_count=1 >/dev/null 2>&1 \
      && echo "✅ Branch protection applied." \
      || echo "ℹ️ Could not set branch protection via gh (check auth/permissions)."
  else
    echo "ℹ️ Could not parse origin repo for branch protection."
  fi
else
  echo "ℹ️ gh not installed. Set branch protection in GitHub UI:"
  echo "   Settings → Branches → Add rule for 'main' → Require checks: audit-smoke, ci-core, build-frontend, ci-summary"
fi
set -e

echo
echo "🎉 Done:"
echo "• Weekly audit workflow: .github/workflows/weekly-audit.yml"
echo "• Pre-push hook installed (runs audit-smoke before push)"
echo "• Baseline tag: $TAG (created if working tree was clean)"
echo "• Branch protection attempted via gh (see notes above)"
