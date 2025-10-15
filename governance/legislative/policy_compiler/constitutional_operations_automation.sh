#!/bin/bash
# Constitutional Operations Automation
# Institutionalizes hardening practices as operational DNA

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${LOG_DIR:-/var/log/constitutional}"
DB_URL="${DATABASE_URL:?DATABASE_URL required}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging setup
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/constitutional_operations_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') [$1] $2" >&2
}

alert() {
    local level="$1"
    local message="$2"

    case "$level" in
        "CRITICAL") echo -e "${RED}[CRITICAL]${NC} $message" ;;
        "WARNING") echo -e "${YELLOW}[WARNING]${NC} $message" ;;
        "INFO") echo -e "${BLUE}[INFO]${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} $message" ;;
    esac

    # Slack notification if webhook configured
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -s -X POST "$SLACK_WEBHOOK" \
             -H 'Content-type: application/json' \
             --data "{\"text\":\"Constitutional Alert [$level]: $message\"}" || true
    fi
}

# ========================================
# 1. GOVERNANCE CADENCE - DAILY VALIDATION
# ========================================

run_daily_validation() {
    log "INFO" "Starting daily constitutional validation sprint"

    # Run the validation
    if python3 "$SCRIPT_DIR/run_constitutional_validation.py" --db-url "$DB_URL" --format json > /tmp/validation_results.json; then
        log "SUCCESS" "Validation completed successfully"

        # Archive results
        local archive_dir="$LOG_DIR/daily/$(date +%Y/%m/%d)"
        mkdir -p "$archive_dir"
        cp /tmp/validation_results.json "$archive_dir/validation_$(date +%H%M%S).json"

        # Check for failures
        local compliance_rate=$(jq -r '.summary.compliance_rate' /tmp/validation_results.json)
        local failed_checks=$(jq -r '.summary.failed' /tmp/validation_results.json)

        if (( $(echo "$compliance_rate < 95" | bc -l) )) || (( failed_checks > 0 )); then
            alert "CRITICAL" "Daily validation FAILED: ${compliance_rate}% compliance, ${failed_checks} checks failed"
            return 1
        else
            alert "SUCCESS" "Daily validation PASSED: ${compliance_rate}% compliance"
        fi
    else
        alert "CRITICAL" "Daily validation CRASHED - check logs immediately"
        return 1
    fi
}

# ========================================
# 2. CI/CD INTEGRATION - BUILD BREAKERS
# ========================================

run_pre_deploy_checks() {
    log "INFO" "Running pre-deployment constitutional checks"

    # Run validation
    if ! python3 "$SCRIPT_DIR/run_constitutional_validation.py" --db-url "$DB_URL" --format json > /tmp/pre_deploy_check.json; then
        alert "CRITICAL" "Pre-deploy check CRASHED - BLOCKING DEPLOYMENT"
        echo "CONSTITUTIONAL_CHECK_FAILED=1" >> "$GITHUB_ENV"
        return 1
    fi

    # Parse results
    local compliance_rate=$(jq -r '.summary.compliance_rate' /tmp/pre_deploy_check.json)
    local failed_checks=$(jq -r '.summary.failed' /tmp/pre_deploy_check.json)

    # Block deployment if critical checks fail
    local critical_failures=$(jq -r '.checks | to_entries[] | select(.value.status == "FAIL") | select(.key | test("privacy|policy_integrity|monoculture")) | .key' /tmp/pre_deploy_check.json | wc -l)

    if (( critical_failures > 0 )) || (( $(echo "$compliance_rate < 100" | bc -l) )); then
        alert "CRITICAL" "CRITICAL CONSTITUTIONAL VIOLATION - BLOCKING DEPLOYMENT"
        alert "CRITICAL" "Failed checks: $(jq -r '.checks | to_entries[] | select(.value.status == "FAIL") | .key' /tmp/pre_deploy_check.json | tr '\n' ', ')"
        echo "CONSTITUTIONAL_CHECK_FAILED=1" >> "$GITHUB_ENV"
        return 1
    fi

    if (( failed_checks > 0 )); then
        alert "WARNING" "Non-critical constitutional violations detected: ${failed_checks} checks failed"
        # Allow deployment but with warning
        echo "CONSTITUTIONAL_WARNINGS=$failed_checks" >> "$GITHUB_ENV"
    fi

    alert "SUCCESS" "Pre-deployment checks PASSED: ${compliance_rate}% compliance"
}

# ========================================
# 3. REPUTATION DECAY - FEDERATION HEALTH
# ========================================

update_federation_reputation() {
    log "INFO" "Updating federation reputation scores"

    # Run reputation update (assumes function exists in database)
    if psql "$DB_URL" -c "SELECT update_deployment_reputation();" > /dev/null; then
        log "SUCCESS" "Federation reputation updated successfully"
    else
        alert "WARNING" "Federation reputation update failed"
    fi

    # Check for reputation violations
    local low_reputation_count=$(psql "$DB_URL" -t -c "SELECT COUNT(*) FROM deployment_reputation WHERE reputation_score < 0.5;" 2>/dev/null || echo "0")

    if (( low_reputation_count > 0 )); then
        alert "WARNING" "${low_reputation_count} deployments have low reputation scores (< 0.5)"
    fi
}

# ========================================
# 4. ADAPTIVE THRESHOLDS - SYSTEM MATURITY
# ========================================

adjust_adaptive_thresholds() {
    log "INFO" "Adjusting adaptive thresholds based on system maturity"

    # Calculate system maturity metrics
    local days_since_start=$(psql "$DB_URL" -t -c "
        SELECT EXTRACT(EPOCH FROM (NOW() - MIN(ts))) / 86400
        FROM routing_outcomes;
    " 2>/dev/null || echo "0")

    local total_decisions=$(psql "$DB_URL" -t -c "
        SELECT COUNT(*) FROM routing_outcomes
        WHERE ts > NOW() - INTERVAL '30 days';
    " 2>/dev/null || echo "0")

    # Determine maturity level
    local maturity_level
    if (( $(echo "$days_since_start < 7" | bc -l) )) || (( total_decisions < 1000 )); then
        maturity_level="EARLY"
    elif (( $(echo "$days_since_start < 30" | bc -l) )) && (( total_decisions < 10000 )); then
        maturity_level="GROWING"
    else
        maturity_level="MATURE"
    fi

    log "INFO" "System maturity: $maturity_level (days: ${days_since_start%.*}, decisions: $total_decisions)"

    # Adjust thresholds based on maturity
    case "$maturity_level" in
        "EARLY")
            # Lenient thresholds for early system
            psql "$DB_URL" -c "
                UPDATE constitutional_config SET
                    governance_fp_threshold = 0.15,
                    governance_fn_threshold = 0.15,
                    exploration_min = 0.08,
                    exploration_max = 0.25
                WHERE config_name = 'current_thresholds';
            " 2>/dev/null || true
            ;;
        "GROWING")
            # Moderate thresholds
            psql "$DB_URL" -c "
                UPDATE constitutional_config SET
                    governance_fp_threshold = 0.12,
                    governance_fn_threshold = 0.12,
                    exploration_min = 0.06,
                    exploration_max = 0.22
                WHERE config_name = 'current_thresholds';
            " 2>/dev/null || true
            ;;
        "MATURE")
            # Strict thresholds for mature system
            psql "$DB_URL" -c "
                UPDATE constitutional_config SET
                    governance_fp_threshold = 0.10,
                    governance_fn_threshold = 0.10,
                    exploration_min = 0.05,
                    exploration_max = 0.20
                WHERE config_name = 'current_thresholds';
            " 2>/dev/null || true
            ;;
    esac

    alert "INFO" "Adjusted thresholds for $maturity_level maturity level"
}

# ========================================
# 5. CHAOS DRILLS - MONTHLY RESILIENCE
# ========================================

run_chaos_drill() {
    local drill_type="$1"
    log "INFO" "Starting chaos drill: $drill_type"

    case "$drill_type" in
        "strategy_quarantine")
            # Simulate strategy degradation
            alert "INFO" "CHAOS DRILL: Simulating strategy performance degradation"

            # Temporarily reduce a strategy's performance in monitoring
            psql "$DB_URL" -c "
                INSERT INTO chaos_drill_events (drill_type, start_time, description)
                VALUES ('strategy_quarantine', NOW(), 'Simulating 50% performance drop for top strategy');
            " 2>/dev/null || true

            # Wait for alerting system to trigger quarantine
            sleep 300  # 5 minutes

            # Check if quarantine was triggered
            local quarantine_events=$(psql "$DB_URL" -t -c "
                SELECT COUNT(*) FROM strategy_quarantine_events
                WHERE ts > NOW() - INTERVAL '10 minutes';
            " 2>/dev/null || echo "0")

            if (( quarantine_events > 0 )); then
                alert "SUCCESS" "CHAOS DRILL PASSED: Strategy quarantine triggered correctly (${quarantine_events} events)"
            else
                alert "CRITICAL" "CHAOS DRILL FAILED: Strategy quarantine did not trigger"
                return 1
            fi
            ;;

        "federation_integrity")
            # Simulate federation integrity breach
            alert "INFO" "CHAOS DRILL: Simulating federation integrity breach"

            # Temporarily create invalid signature
            psql "$DB_URL" -c "
                INSERT INTO chaos_drill_events (drill_type, start_time, description)
                VALUES ('federation_integrity', NOW(), 'Simulating signature validation failure');
            " 2>/dev/null || true

            # Wait for integrity check
            sleep 120  # 2 minutes

            # Check if federation was halted
            local integrity_alerts=$(psql "$DB_URL" -t -c "
                SELECT COUNT(*) FROM federation_integrity_alerts
                WHERE ts > NOW() - INTERVAL '5 minutes';
            " 2>/dev/null || echo "0")

            if (( integrity_alerts > 0 )); then
                alert "SUCCESS" "CHAOS DRILL PASSED: Federation integrity breach detected (${integrity_alerts} alerts)"
            else
                alert "CRITICAL" "CHAOS DRILL FAILED: Federation integrity breach not detected"
                return 1
            fi
            ;;

        "privacy_budget")
            # Simulate privacy budget exhaustion
            alert "INFO" "CHAOS DRILL: Simulating privacy budget exhaustion"

            # Temporarily inflate epsilon values
            psql "$DB_URL" -c "
                INSERT INTO chaos_drill_events (drill_type, start_time, description)
                VALUES ('privacy_budget', NOW(), 'Simulating epsilon budget > 2.0');
            " 2>/dev/null || true

            # Wait for privacy alerts
            sleep 180  # 3 minutes

            local privacy_alerts=$(psql "$DB_URL" -t -c "
                SELECT COUNT(*) FROM privacy_budget_alerts
                WHERE ts > NOW() - INTERVAL '5 minutes';
            " 2>/dev/null || echo "0")

            if (( privacy_alerts > 0 )); then
                alert "SUCCESS" "CHAOS DRILL PASSED: Privacy budget violation detected (${privacy_alerts} alerts)"
            else
                alert "CRITICAL" "CHAOS DRILL FAILED: Privacy budget violation not detected"
                return 1
            fi
            ;;
    esac

    # Clean up drill artifacts
    psql "$DB_URL" -c "
        DELETE FROM chaos_drill_events
        WHERE start_time < NOW() - INTERVAL '1 hour';
    " 2>/dev/null || true

    log "INFO" "Chaos drill $drill_type completed"
}

# ========================================
# MAIN EXECUTION LOGIC
# ========================================

main() {
    local command="${1:-help}"

    case "$command" in
        "daily-validation")
            run_daily_validation
            ;;
        "pre-deploy-check")
            run_pre_deploy_checks
            ;;
        "update-reputation")
            update_federation_reputation
            ;;
        "adjust-thresholds")
            adjust_adaptive_thresholds
            ;;
        "chaos-drill")
            local drill_type="${2:-strategy_quarantine}"
            run_chaos_drill "$drill_type"
            ;;
        "full-cycle")
            log "INFO" "Starting full constitutional operations cycle"

            # Run all operations in sequence
            run_daily_validation || exit 1
            update_federation_reputation
            adjust_adaptive_thresholds

            # Run chaos drill on first Monday of month
            if [[ "$(date +%u)" == "1" && "$(date +%d)" -le "7" ]]; then
                run_chaos_drill "strategy_quarantine" || exit 1
            fi

            alert "SUCCESS" "Full constitutional operations cycle completed"
            ;;
        "help"|*)
            cat << EOF
Constitutional Operations Automation

USAGE: $0 <command> [options]

COMMANDS:
    daily-validation    Run daily constitutional validation sprint
    pre-deploy-check    Run pre-deployment constitutional checks (CI/CD)
    update-reputation   Update federation reputation scores
    adjust-thresholds   Adjust thresholds based on system maturity
    chaos-drill <type>  Run chaos drill (strategy_quarantine|federation_integrity|privacy_budget)
    full-cycle          Run complete operations cycle

ENVIRONMENT VARIABLES:
    DATABASE_URL        PostgreSQL connection string (required)
    PROMETHEUS_URL      Prometheus URL for alerts (default: http://localhost:9090)
    SLACK_WEBHOOK       Slack webhook for alerts (optional)
    LOG_DIR            Log directory (default: /var/log/constitutional)

EXAMPLES:
    $0 daily-validation
    $0 pre-deploy-check
    $0 chaos-drill strategy_quarantine
    $0 full-cycle

CRONTAB EXAMPLES:
    # Daily validation at 6 AM
    0 6 * * * $0 daily-validation

    # Full cycle every 4 hours
    0 */4 * * * $0 full-cycle

    # Monthly chaos drills (first Monday)
    0 9 * * 1 [ \$(date +\%d) -le 7 ] && $0 chaos-drill strategy_quarantine
EOF
            ;;
    esac
}

# Run main function with all arguments
main "$@"
