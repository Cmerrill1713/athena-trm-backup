#!/bin/bash

# =============================================================================
# PRODUCTION VALIDATION SUITE EXECUTOR
# =============================================================================
#
# Runs the complete production validation suite for the Constitutional AI Framework.
#
# Usage: ./scripts/run_production_validation.sh
#
# Requirements:
# - PostgreSQL client (psql) configured with database connection
# - Prometheus alert configuration loaded (see monitoring/alerts/production_safety_alerts.yml)
#
# Output: Comprehensive validation report with pass/fail status for each component
#
# =============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATION_SQL="${SCRIPT_DIR}/production_validation_suite.sql"
ALERTS_YAML="${SCRIPT_DIR}/../monitoring/alerts/production_safety_alerts.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================================${NC}"
}

# Pre-flight checks
check_dependencies() {
    log_header "DEPENDENCY CHECKS"

    # Check psql
    if ! command -v psql &> /dev/null; then
        log_error "psql command not found. Please install PostgreSQL client."
        exit 1
    fi
    log_success "psql found: $(psql --version)"

    # Check validation SQL file
    if [[ ! -f "$VALIDATION_SQL" ]]; then
        log_error "Validation SQL file not found: $VALIDATION_SQL"
        exit 1
    fi
    log_success "Validation SQL file found"

    # Check alerts YAML file
    if [[ ! -f "$ALERTS_YAML" ]]; then
        log_warning "Alerts YAML file not found: $ALERTS_YAML"
        log_warning "Prometheus alerts validation will be skipped"
    else
        log_success "Alerts YAML file found"
    fi
}

# Validate Prometheus alerts configuration
validate_alerts() {
    log_header "PROMETHEUS ALERTS VALIDATION"

    if [[ ! -f "$ALERTS_YAML" ]]; then
        log_warning "Skipping alerts validation - file not found"
        return
    fi

    # Basic YAML syntax check
    if command -v yamllint &> /dev/null; then
        if yamllint "$ALERTS_YAML" > /dev/null 2>&1; then
            log_success "Alerts YAML syntax is valid"
        else
            log_error "Alerts YAML has syntax errors"
            yamllint "$ALERTS_YAML"
            return 1
        fi
    else
        log_warning "yamllint not found - skipping YAML validation"
    fi

    # Check for required alert rules
    local required_alerts=(
        "RouterP95Latency"
        "JudgeHelpfulnessDrop"
        "StrategyImbalance"
        "RAGRerankOverFiltering"
        "ConstitutionalViolationRate"
    )

    local missing_alerts=()
    for alert in "${required_alerts[@]}"; do
        if ! grep -q "alert: $alert" "$ALERTS_YAML"; then
            missing_alerts+=("$alert")
        fi
    done

    if [[ ${#missing_alerts[@]} -eq 0 ]]; then
        log_success "All required safety alerts defined"
    else
        log_error "Missing required alerts: ${missing_alerts[*]}"
        return 1
    fi
}

# Run SQL validation suite
run_sql_validation() {
    log_header "SQL VALIDATION SUITE EXECUTION"

    log_info "Running comprehensive SQL validation suite..."
    log_info "This may take 2-5 minutes depending on data volume..."

    # Run the validation SQL and capture output
    local sql_output
    if ! sql_output=$(psql -f "$VALIDATION_SQL" 2>&1); then
        log_error "SQL validation failed to execute"
        echo "$sql_output"
        return 1
    fi

    # Extract the final summary
    local summary_line
    summary_line=$(echo "$sql_output" | grep "PRODUCTION_VALIDATION_SUMMARY" | head -1)

    if [[ -z "$summary_line" ]]; then
        log_error "Could not find validation summary in output"
        echo "$sql_output"
        return 1
    fi

    # Parse the summary
    local total_checks pass_rate readiness
    total_checks=$(echo "$summary_line" | sed 's/.*| \([0-9]*\) |/\1/' | awk '{print $1}')
    pass_rate=$(echo "$summary_line" | sed 's/.*| \([0-9.]*\) |.*|/\1/' | awk '{print $1}')
    readiness=$(echo "$summary_line" | sed 's/.*| \([^|]*\)$/\1/' | sed 's/^ *//')

    echo "$sql_output"

    log_header "VALIDATION RESULTS SUMMARY"
    echo "Total Checks: $total_checks"
    echo "Pass Rate: $pass_rate%"
    echo "Readiness: $readiness"

    # Determine overall status
    local pass_rate_num
    pass_rate_num=$(echo "$pass_rate" | awk '{print int($1)}')

    if [[ $pass_rate_num -eq 100 ]]; then
        log_success "🎉 ALL CHECKS PASSED - SYSTEM IS PRODUCTION READY!"
        return 0
    elif [[ $pass_rate_num -ge 80 ]]; then
        log_success "✅ MOSTLY READY - Minor issues to address before production"
        return 0
    elif [[ $pass_rate_num -ge 60 ]]; then
        log_warning "⚠️ NEEDS WORK - Significant issues require attention"
        return 1
    else
        log_error "❌ NOT READY - Major validation failures detected"
        return 1
    fi
}

# Generate detailed report
generate_report() {
    local exit_code=$1
    local report_file="${SCRIPT_DIR}/validation_report_$(date +%Y%m%d_%H%M%S).txt"

    log_header "GENERATING DETAILED REPORT"

    {
        echo "Constitutional AI Framework - Production Validation Report"
        echo "Generated: $(date)"
        echo "Exit Code: $exit_code"
        echo ""
        echo "Dependencies:"
        echo "- psql: $(psql --version 2>/dev/null || echo 'Not found')"
        echo "- yamllint: $(yamllint --version 2>/dev/null || echo 'Not found')"
        echo ""
        echo "Files Checked:"
        echo "- Validation SQL: $([[ -f "$VALIDATION_SQL" ]] && echo 'Found' || echo 'Missing')"
        echo "- Alerts YAML: $([[ -f "$ALERTS_YAML" ]] && echo 'Found' || echo 'Missing')"
        echo ""
        echo "For full validation output, see terminal output above."
        echo ""
        echo "Next Steps:"
        if [[ $exit_code -eq 0 ]]; then
            echo "✅ System appears ready for production deployment"
            echo "   - Review any warnings in the output"
            echo "   - Ensure alerts are loaded in Prometheus"
            echo "   - Run chaos drills regularly"
        else
            echo "❌ Issues detected - review validation output for details"
            echo "   - Address failing checks before production deployment"
            echo "   - Re-run validation after fixes"
        fi
    } > "$report_file"

    log_success "Detailed report saved to: $report_file"
}

# Main execution
main() {
    log_header "CONSTITUTIONAL AI FRAMEWORK - PRODUCTION VALIDATION SUITE"

    local start_time
    start_time=$(date +%s)

    # Run validation steps
    check_dependencies
    validate_alerts
    run_sql_validation
    local exit_code=$?

    generate_report $exit_code

    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_header "VALIDATION COMPLETE"
    log_info "Total execution time: ${duration}s"

    if [[ $exit_code -eq 0 ]]; then
        log_success "Validation suite completed successfully!"
    else
        log_error "Validation suite completed with failures. See output above for details."
    fi

    return $exit_code
}

# Run main function
main "$@"
