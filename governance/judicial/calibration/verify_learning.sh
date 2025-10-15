#!/usr/bin/env bash
# Verify Learning Loop - Check that autonomous learning is working

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Default DATABASE_URL
DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5433/athena_db}"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║          Learning Loop Verification                            ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check 1: Database connection
echo -e "${BLUE}[1/6]${NC} Checking database connection..."
if psql "$DATABASE_URL" -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "      ${GREEN}✅ Database accessible${NC}"
else
    echo -e "      ${RED}❌ Cannot connect to database${NC}"
    echo "      Set DATABASE_URL environment variable"
    exit 1
fi

# Check 2: Tables exist
echo -e "${BLUE}[2/6]${NC} Checking tables..."
TABLES=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('routing_outcomes', 'trm_training_runs', 'learned_patterns');")
if [ "$TABLES" -eq 3 ]; then
    echo -e "      ${GREEN}✅ All 3 tables exist${NC}"
else
    echo -e "      ${YELLOW}⚠️  Only $TABLES/3 tables found${NC}"
    echo "      Run: cd AI-Projects/universal-ai-tools && psql \$DATABASE_URL -f db/migrations/20251012_routing_outcomes.sql"
fi

# Check 3: Recent outcomes
echo -e "${BLUE}[3/6]${NC} Checking recent outcomes..."
RECENT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM routing_outcomes WHERE created_at > NOW() - INTERVAL '10 minutes';" | tr -d ' ')
if [ "$RECENT" -gt 0 ]; then
    echo -e "      ${GREEN}✅ $RECENT outcomes in last 10 minutes${NC}"
else
    echo -e "      ${YELLOW}ℹ️  No recent outcomes (system may be idle)${NC}"
fi

# Check 4: Total outcomes
echo -e "${BLUE}[4/6]${NC} Checking total outcomes..."
TOTAL=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM routing_outcomes;" | tr -d ' ')
echo -e "      ${GREEN}📊 $TOTAL total outcomes logged${NC}"

if [ "$TOTAL" -gt 1000 ]; then
    echo -e "      ${GREEN}✅ Sufficient data for training${NC}"
elif [ "$TOTAL" -gt 100 ]; then
    echo -e "      ${YELLOW}ℹ️  Getting there (1000+ recommended)${NC}"
else
    echo -e "      ${YELLOW}ℹ️  Accumulating data (need 100+ for training)${NC}"
fi

# Check 5: Success rate
echo -e "${BLUE}[5/6]${NC} Checking success rate..."
if [ "$TOTAL" -gt 0 ]; then
    SUCCESS_RATE=$(psql "$DATABASE_URL" -t -c "
        SELECT ROUND(100.0 * SUM(CASE WHEN success THEN 1 ELSE 0 END) / COUNT(*), 1)
        FROM routing_outcomes
        WHERE created_at > NOW() - INTERVAL '7 days';
    " | tr -d ' ')
    echo -e "      ${GREEN}📈 ${SUCCESS_RATE}% success rate (7 days)${NC}"
    
    if [ "${SUCCESS_RATE%.*}" -ge 90 ]; then
        echo -e "      ${GREEN}✅ Good success rate${NC}"
    elif [ "${SUCCESS_RATE%.*}" -ge 70 ]; then
        echo -e "      ${YELLOW}⚠️  Moderate success rate${NC}"
    else
        echo -e "      ${RED}⚠️  Low success rate - investigate${NC}"
    fi
fi

# Check 6: Training runs
echo -e "${BLUE}[6/6]${NC} Checking training runs..."
TRAINING_RUNS=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM trm_training_runs;" | tr -d ' ')
if [ "$TRAINING_RUNS" -gt 0 ]; then
    LAST_RUN=$(psql "$DATABASE_URL" -t -c "
        SELECT to_char(created_at, 'YYYY-MM-DD HH24:MI') 
        FROM trm_training_runs 
        ORDER BY created_at DESC LIMIT 1;
    " | xargs)
    echo -e "      ${GREEN}✅ $TRAINING_RUNS training runs${NC}"
    echo -e "      ${GREEN}   Last run: $LAST_RUN${NC}"
else
    echo -e "      ${YELLOW}ℹ️  No training runs yet${NC}"
    echo "      Run: make learn DAYS=7"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Learning Loop Verification Complete${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""

if [ "$TOTAL" -gt 100 ]; then
    echo "🎯 System Status: LEARNING ACTIVE"
    echo ""
    echo "📊 Stats by Model (last 7 days):"
    psql "$DATABASE_URL" -c "
        SELECT 
            selected_model,
            COUNT(*) as requests,
            ROUND(AVG(latency_ms)) as avg_latency_ms,
            ROUND(100.0 * SUM(CASE WHEN success THEN 1 ELSE 0 END) / COUNT(*), 1) as success_rate
        FROM routing_outcomes
        WHERE created_at > NOW() - INTERVAL '7 days'
        GROUP BY selected_model
        ORDER BY requests DESC
        LIMIT 10;
    "
else
    echo "🌱 System Status: ACCUMULATING DATA"
    echo ""
    echo "Next Steps:"
    echo "  1. Generate requests to accumulate outcomes"
    echo "  2. Wait for 100+ outcomes"
    echo "  3. Run: make learn DAYS=7"
fi

echo ""
echo "🔧 Commands:"
echo "   make learn DAYS=7        # Train + eval + promote"
echo "   make train               # Just train"
echo "   make eval                # Evaluate candidate"
echo ""

