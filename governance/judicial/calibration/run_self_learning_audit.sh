#!/bin/bash

# =============================================================================
# SELF-LEARNING CAPABILITY AUDIT & GAP ANALYSIS
# =============================================================================
#
# Comprehensive audit of all self-learning capabilities in the Constitutional AI Framework
# with automatic gap analysis and implementation recommendations.
#
# Usage:
#   ./scripts/run_self_learning_audit.sh [cursor|local_agent]
#
# Options:
#   cursor        - Generate prompt for Cursor agent
#   local_agent   - Generate prompt for local AI agent
#   (no arg)      - Run complete audit with gap analysis
#
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUDIT_PROMPT="${SCRIPT_DIR}/self_learning_audit_prompt.txt"
GAP_ANALYSIS="${SCRIPT_DIR}/self_learning_gap_analysis.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}$(printf '%.0s=' {1..80})${NC}"
}

show_prompt() {
    local agent_type="$1"
    log_header "SELF-LEARNING CAPABILITY AUDIT PROMPT"

    case "$agent_type" in
        "cursor")
            echo -e "${CYAN}Copy this prompt into Cursor's chat:${NC}"
            echo ""
            cat "$AUDIT_PROMPT"
            echo ""
            echo -e "${YELLOW}After Cursor responds with the audit results, run:${NC}"
            echo -e "${CYAN}  ./scripts/run_self_learning_audit.sh analyze < audit_results.txt${NC}"
            ;;

        "local_agent")
            echo -e "${CYAN}Use this prompt with your local AI agent:${NC}"
            echo ""
            cat "$AUDIT_PROMPT"
            echo ""
            echo -e "${YELLOW}Then save the response and run:${NC}"
            echo -e "${CYAN}  cat agent_response.txt | ./scripts/run_self_learning_audit.sh analyze${NC}"
            ;;

        *)
            log_error "Invalid agent type. Use 'cursor' or 'local_agent'"
            exit 1
            ;;
    esac
}

run_gap_analysis() {
    log_header "GAP ANALYSIS EXECUTION"

    log_info "Reading audit results from stdin..."
    log_info "Running comprehensive gap analysis..."

    # Run the gap analysis script
    if python3 "$GAP_ANALYSIS"; then
        log_success "Gap analysis completed successfully"
    else
        local exit_code=$?
        log_error "Gap analysis failed with exit code $exit_code"

        if [[ $exit_code -eq 1 ]]; then
            log_warning "Critical gaps detected - review the analysis above"
        fi

        exit $exit_code
    fi
}

show_usage() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

Commands:
    cursor          Show prompt for Cursor agent
    local_agent     Show prompt for local AI agent
    analyze         Run gap analysis on audit results (expects input via stdin or file)

Options:
    -h, --help      Show this help message

Examples:
    # Show prompt for Cursor
    $0 cursor

    # Show prompt for local agent
    $0 local_agent

    # Analyze audit results from file
    $0 analyze < audit_results.txt

    # Analyze audit results piped from another command
    cat audit_results.txt | $0 analyze

EOF
}

main() {
    case "${1:-}" in
        "cursor")
            show_prompt "cursor"
            ;;

        "local_agent")
            show_prompt "local_agent"
            ;;

        "analyze")
            run_gap_analysis
            ;;

        "-h"|"--help"|"")
            show_usage
            ;;

        *)
            log_error "Unknown command: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
