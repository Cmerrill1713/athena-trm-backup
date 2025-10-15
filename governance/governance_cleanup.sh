#!/usr/bin/env bash
# 🧭 GOVERNANCE CLEANUP SCRIPT
# Consolidates scattered iterations into a governed, tiered structure
# Non-destructive - creates backups and maintains history

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT="/Users/christianmerrill/Documents/GitHub"
GOVERNANCE_DIR="$REPO_ROOT/governance"
BACKUP_DIR="$REPO_ROOT/governance_backup_$(date +%Y%m%d_%H%M%S)"
ITERATION_LOG="$GOVERNANCE_DIR/iteration_log.yaml"
MANIFEST="$GOVERNANCE_DIR/governance_manifest.json"

# Create backup first
echo -e "${YELLOW}📦 Creating backup...${NC}"
mkdir -p "$BACKUP_DIR"
cp -r "$GOVERNANCE_DIR"/* "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✅ Backup created at: $BACKUP_DIR${NC}"

# Initialize governance structure if needed
echo -e "${BLUE}🏗️  Initializing governance structure...${NC}"
mkdir -p "$GOVERNANCE_DIR"/{legislative/{policy_compiler,canary_rules},judicial/{entropy_service.py,evaluation,calibration},executive/{start_server.sh,docker,orchestration},devil_advocate/{stress_tests,red_team_sets},observability,archive/old_iterations}

# Function to classify and move files
classify_and_move() {
    local file="$1"
    local category=""
    local subcategory=""

    # Skip if already in governance
    [[ "$file" == *"/governance/"* ]] && return

    # Legislative (Policy & Rules)
    if [[ "$file" == *"policy"* || "$file" == *"rule"* || "$file" == *"compiler"* ]]; then
        category="legislative"
        if [[ "$file" == *"compiler"* ]]; then
            subcategory="policy_compiler"
        else
            subcategory="canary_rules"
        fi
    # Judicial (Evaluation & Entropy)
    elif [[ "$file" == *"entropy"* || "$file" == *"evaluation"* || "$file" == *"calibration"* || "$file" == *"judge"* ]]; then
        category="judicial"
        if [[ "$file" == *"entropy"* ]]; then
            subcategory="entropy_service.py"
        elif [[ "$file" == *"evaluation"* ]]; then
            subcategory="evaluation"
        else
            subcategory="calibration"
        fi
    # Executive (Operations & Orchestration)
    elif [[ "$file" == *"start"* || "$file" == *"server"* || "$file" == *"docker"* || "$file" == *"orchestration"* ]]; then
        category="executive"
        if [[ "$file" == *"start"* ]]; then
            subcategory="start_server.sh"
        elif [[ "$file" == *"docker"* ]]; then
            subcategory="docker"
        else
            subcategory="orchestration"
        fi
    # Devil's Advocate (Testing & Stress)
    elif [[ "$file" == *"stress"* || "$file" == *"test"* || "$file" == *"red_team"* || "$file" == *"devil"* ]]; then
        category="devil_advocate"
        if [[ "$file" == *"stress"* ]]; then
            subcategory="stress_tests"
        else
            subcategory="red_team_sets"
        fi
    # Observability (Monitoring & Metrics)
    elif [[ "$file" == *"prometheus"* || "$file" == *"grafana"* || "$file" == *"monitor"* || "$file" == *"metric"* ]]; then
        category="observability"
        subcategory=""
    # Archive everything else as old iterations
    else
        category="archive"
        subcategory="old_iterations"
    fi

    if [[ -n "$category" ]]; then
        local target_dir="$GOVERNANCE_DIR/$category"
        [[ -n "$subcategory" ]] && target_dir="$target_dir/$subcategory"

        mkdir -p "$target_dir"
        local filename=$(basename "$file")
        local target_file="$target_dir/$filename"

        # Handle duplicates by adding timestamp
        if [[ -f "$target_file" ]]; then
            local timestamp=$(date +%s)
            target_file="$target_dir/${filename%.*}_$timestamp.${filename##*.}"
        fi

        cp "$file" "$target_file"
        echo "$file -> $target_file" >> "$GOVERNANCE_DIR/move_log.txt"
        echo -e "${CYAN}📁 Moved: $file → $category${subcategory:+/$subcategory}${NC}"
    fi
}

# Scan and classify files
echo -e "${PURPLE}🔍 Scanning and classifying files...${NC}"
find "$REPO_ROOT" -type f \
    \( -name "*.py" -o -name "*.sh" -o -name "*.swift" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.md" \) \
    ! -path "*/node_modules/*" \
    ! -path "*/.git/*" \
    ! -path "*/__pycache__/*" \
    ! -path "*/.build/*" \
    ! -path "*/build/*" \
    ! -path "*/governance_backup_*/*" \
    | while read -r file; do
        classify_and_move "$file"
    done

# Create iteration log
echo -e "${YELLOW}📝 Creating iteration log...${NC}"
cat > "$ITERATION_LOG" << EOF
version: v1.6
author: Governance Cleanup Script
date: $(date -Iseconds)
summary: "Consolidated scattered iterations into governed tiered structure - legislative/judicial/executive/devil_advocate/observability"
files_moved: $(wc -l < "$GOVERNANCE_DIR/move_log.txt" 2>/dev/null || echo "0")
backup_location: "$BACKUP_DIR"
categories:
  legislative:
    - policy_compiler: "Policy compilation and enforcement logic"
    - canary_rules: "Gradual rollout and safety rules"
  judicial:
    - entropy_service.py: "System entropy monitoring and drift detection"
    - evaluation: "Performance and correctness evaluation"
    - calibration: "Model calibration and fine-tuning"
  executive:
    - start_server.sh: "Service startup and orchestration"
    - docker: "Container deployment configurations"
    - orchestration: "Service coordination and scaling"
  devil_advocate:
    - stress_tests: "Load and failure scenario testing"
    - red_team_sets: "Adversarial testing scenarios"
  observability:
    - "Monitoring, metrics, and alerting configurations"
  archive:
    old_iterations: "Retired iterations and deprecated code"
changes:
  - "Moved $(wc -l < "$GOVERNANCE_DIR/move_log.txt" 2>/dev/null || echo "0") files into governance structure"
  - "Created backup at $BACKUP_DIR"
  - "Established iteration versioning system"
  - "Generated governance manifest"
EOF

# Create governance manifest
echo -e "${YELLOW}📋 Generating governance manifest...${NC}"
cat > "$MANIFEST" << EOF
{
  "version": "v1.6",
  "timestamp": "$(date -Iseconds)",
  "structure": {
    "legislative": {
      "purpose": "Policy compilation and rule enforcement",
      "subsystems": ["policy_compiler", "canary_rules"],
      "file_count": $(find "$GOVERNANCE_DIR/legislative" -type f 2>/dev/null | wc -l)
    },
    "judicial": {
      "purpose": "Evaluation, entropy monitoring, and calibration",
      "subsystems": ["entropy_service.py", "evaluation", "calibration"],
      "file_count": $(find "$GOVERNANCE_DIR/judicial" -type f 2>/dev/null | wc -l)
    },
    "executive": {
      "purpose": "Service orchestration and operations",
      "subsystems": ["start_server.sh", "docker", "orchestration"],
      "file_count": $(find "$GOVERNANCE_DIR/executive" -type f 2>/dev/null | wc -l)
    },
    "devil_advocate": {
      "purpose": "Testing, stress scenarios, and red teaming",
      "subsystems": ["stress_tests", "red_team_sets"],
      "file_count": $(find "$GOVERNANCE_DIR/devil_advocate" -type f 2>/dev/null | wc -l)
    },
    "observability": {
      "purpose": "Monitoring, metrics, and alerting",
      "subsystems": [],
      "file_count": $(find "$GOVERNANCE_DIR/observability" -type f 2>/dev/null | wc -l)
    },
    "archive": {
      "purpose": "Retired iterations and historical code",
      "subsystems": ["old_iterations"],
      "file_count": $(find "$GOVERNANCE_DIR/archive" -type f 2>/dev/null | wc -l)
    }
  },
  "total_files": $(find "$GOVERNANCE_DIR" -type f 2>/dev/null | wc -l),
  "backup_location": "$BACKUP_DIR"
}
EOF

# Create governance merge script
echo -e "${YELLOW}🔧 Creating governance merge script...${NC}"
cat > "$GOVERNANCE_DIR/merge_and_tag.sh" << 'EOF'
#!/bin/bash
# Governance Merge & Tag Script
# Automates iteration management and sanity checks

set -euo pipefail

ITERATION_LOG="iteration_log.yaml"
MANIFEST="governance_manifest.json"

# Auto-increment version
if [[ -f "$ITERATION_LOG" ]]; then
    current_version=$(grep "version:" "$ITERATION_LOG" | cut -d' ' -f2)
    major=$(echo "$current_version" | cut -d'.' -f1 | sed 's/v//')
    minor=$(echo "$current_version" | cut -d'.' -f2)
    new_minor=$((minor + 1))
    new_version="v${major}.${new_minor}"
else
    new_version="v1.0"
fi

# Update iteration log
cat >> "$ITERATION_LOG" << LOG_ENTRY

---
version: $new_version
author: $(whoami)
date: $(date -Iseconds)
summary: "Auto-merged governance iteration"
changes:
  - "Merged pending changes into governance structure"
LOG_ENTRY

# Regenerate manifest
./governance_cleanup.sh --manifest-only

echo "✅ Governance iteration $new_version created"
EOF
chmod +x "$GOVERNANCE_DIR/merge_and_tag.sh"

# Final report
echo -e "${GREEN}🎉 GOVERNANCE CLEANUP COMPLETE!${NC}"
echo ""
echo -e "${BLUE}📊 Summary:${NC}"
echo "  📁 Files organized: $(wc -l < "$GOVERNANCE_DIR/move_log.txt" 2>/dev/null || echo "0")"
echo "  📦 Backup location: $BACKUP_DIR"
echo "  📝 Iteration log: $ITERATION_LOG"
echo "  📋 Manifest: $MANIFEST"
echo "  🔧 Merge script: $GOVERNANCE_DIR/merge_and_tag.sh"
echo ""
echo -e "${PURPLE}🗂️  Governance Structure:${NC}"
echo "  🧠 Legislative: $(find "$GOVERNANCE_DIR/legislative" -type f 2>/dev/null | wc -l) files"
echo "  ⚖️  Judicial: $(find "$GOVERNANCE_DIR/judicial" -type f 2>/dev/null | wc -l) files"
echo "  🧑‍⚖️ Executive: $(find "$GOVERNANCE_DIR/executive" -type f 2>/dev/null | wc -l) files"
echo "  👹 Devil's Advocate: $(find "$GOVERNANCE_DIR/devil_advocate" -type f 2>/dev/null | wc -l) files"
echo "  📊 Observability: $(find "$GOVERNANCE_DIR/observability" -type f 2>/dev/null | wc -l) files"
echo "  📚 Archive: $(find "$GOVERNANCE_DIR/archive" -type f 2>/dev/null | wc -l) files"
echo ""
echo -e "${YELLOW}🚀 Next Steps:${NC}"
echo "  1. Review the moved files in governance/"
echo "  2. Use ./governance/merge_and_tag.sh for future iterations"
echo "  3. Check iteration_log.yaml for version history"
echo ""
echo -e "${RED}⚠️  Note: Original files remain in place. Remove manually if cleanup is satisfactory.${NC}"
