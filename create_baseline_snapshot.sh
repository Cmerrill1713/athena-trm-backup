#!/bin/bash
set -euo pipefail

# ============================================================================
# CREATE BASELINE SNAPSHOT
# Captures the "golden state" for drift detection
# ============================================================================

SNAPSHOT_DIR="artifacts/snapshots"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BASELINE_DIR="$SNAPSHOT_DIR/baseline_$TIMESTAMP"

echo "🔒 Creating Athena Baseline Snapshot"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

mkdir -p "$BASELINE_DIR"

# ============================================================================
# 1. DOCKER STATE
# ============================================================================

echo "1️⃣  Capturing Docker state..."
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' > "$BASELINE_DIR/docker_ps.txt"
docker-compose ps > "$BASELINE_DIR/docker_compose_ps.txt"
echo "  ✅ Docker state saved"

# ============================================================================
# 2. SERVICE HEALTH
# ============================================================================

echo "2️⃣  Capturing service health..."

curl -s http://127.0.0.1:8090/v1/.well-known/ready > "$BASELINE_DIR/weaviate_health.json" 2>/dev/null || echo '{"error":"unreachable"}' > "$BASELINE_DIR/weaviate_health.json"
curl -s http://127.0.0.1:9113/health > "$BASELINE_DIR/router_health.json" 2>/dev/null || echo '{"error":"unreachable"}' > "$BASELINE_DIR/router_health.json"
curl -s http://127.0.0.1:8080/health > "$BASELINE_DIR/uai_health.json" 2>/dev/null || echo '{"error":"unreachable"}' > "$BASELINE_DIR/uai_health.json"

echo "  ✅ Service health saved"

# ============================================================================
# 3. KNOWLEDGE BASE COUNT
# ============================================================================

echo "3️⃣  Capturing knowledge base state..."

DOC_COUNT=$(curl -s http://127.0.0.1:8090/v1/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ Aggregate { DocsV2 { meta { count } } } }"}' 2>/dev/null | jq -r '.data.Aggregate.DocsV2[0].meta.count // 0')

echo "$DOC_COUNT" > "$BASELINE_DIR/doc_count.txt"
echo "$DOC_COUNT" > "$SNAPSHOT_DIR/baseline_doc_count.txt"  # Current baseline
echo "  ✅ DocsV2 count: $DOC_COUNT"

# ============================================================================
# 4. METRICS BASELINE
# ============================================================================

echo "4️⃣  Capturing metrics baseline..."

curl -s http://127.0.0.1:9113/metrics > "$BASELINE_DIR/router_metrics.txt" 2>/dev/null || true
curl -s http://127.0.0.1:8080/metrics > "$BASELINE_DIR/uai_metrics.txt" 2>/dev/null || true
curl -s http://127.0.0.1:9090/metrics > "$BASELINE_DIR/prometheus_metrics.txt" 2>/dev/null || true

echo "  ✅ Metrics saved"

# ============================================================================
# 5. GIT STATE
# ============================================================================

echo "5️⃣  Capturing git state..."

git rev-parse HEAD > "$BASELINE_DIR/git_commit.txt"
git status --short > "$BASELINE_DIR/git_status.txt"
git tag -l "athena-baseline-*" | tail -1 > "$BASELINE_DIR/last_baseline_tag.txt"

# Create git tag for this baseline
BASELINE_TAG="athena-baseline-$(date +%Y%m%d)"
git tag -f "$BASELINE_TAG" -m "Athena baseline snapshot: $TIMESTAMP"
echo "  ✅ Git tag created: $BASELINE_TAG"

# ============================================================================
# 6. CONFIGURATION SNAPSHOT
# ============================================================================

echo "6️⃣  Capturing configuration..."

cp docker-compose.yml "$BASELINE_DIR/docker-compose.yml.snapshot"
cp .athena/config.yml "$BASELINE_DIR/athena-config.yml.snapshot" 2>/dev/null || true
cp capability_registry.json "$BASELINE_DIR/capability_registry.json.snapshot" 2>/dev/null || true

echo "  ✅ Configuration saved"

# ============================================================================
# 7. BACKUP CRITICAL VOLUMES
# ============================================================================

echo "7️⃣  Backing up critical volumes..."

# Weaviate data (if not too large)
WEAVIATE_SIZE=$(du -sm volumes/weaviate_data 2>/dev/null | cut -f1 || echo "0")

if [ "$WEAVIATE_SIZE" -lt 1000 ]; then
    echo "  Backing up Weaviate data (${WEAVIATE_SIZE}MB)..."
    tar -czf "$BASELINE_DIR/weaviate_backup.tar.gz" volumes/weaviate_data/ 2>/dev/null || echo "  ⚠️  Weaviate backup skipped (too large or missing)"
else
    echo "  ⚠️  Weaviate data too large (${WEAVIATE_SIZE}MB), skipping backup"
    echo "  💡 Use external backup for volumes/"
fi

# Governance policies
if [ -d "governance/legislative" ]; then
    tar -czf "$BASELINE_DIR/governance_backup.tar.gz" governance/ 2>/dev/null
    echo "  ✅ Governance policies backed up"
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ BASELINE SNAPSHOT COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Snapshot location: $BASELINE_DIR"
echo "Git tag: $BASELINE_TAG"
echo "DocsV2 count: $DOC_COUNT"
echo ""
echo "To restore this baseline:"
echo "  git checkout $BASELINE_TAG"
echo "  tar -xzf $BASELINE_DIR/weaviate_backup.tar.gz"
echo "  docker-compose down && docker-compose up -d"
echo ""
echo "💙 Golden state locked!"

