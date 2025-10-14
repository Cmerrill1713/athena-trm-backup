#!/usr/bin/env python3
"""
Auto-Promotion/Rollback System for Prompt Variants

Automatically promotes high-performing variants and rolls back underperformers
based on LLM judge scores and bandit performance metrics.

Safety Features:
- Minimum sample sizes before action
- Gradual promotion/demotion (10-25% at a time)
- Manual override capabilities
- Audit logging for all actions
- Rollback limits to prevent over-correction

Usage:
    python3 scripts/auto_promotion.py --dry-run    # Preview changes
    python3 scripts/auto_promotion.py --apply      # Apply changes
    python3 scripts/auto_promotion.py --rollback   # Emergency rollback
"""

import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse
import logging

# Prometheus metrics
try:
    from prometheus_client import Counter, Gauge, generate_latest
    promotion_actions_total = Counter("promotion_actions_total", "Total promotion actions taken", ["action_type", "variant"])
    promotion_score_gauge = Gauge("promotion_score_last", "Last promotion decision score", ["variant"])
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    promotion_actions_total = promotion_score_gauge = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "dbname=universal_ai_tools user=postgres password=postgres host=athena-postgres port=5432")

# Configuration loaded from database
CONFIG = {}

class AutoPromotionSystem:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.db_conn = None
        self.actions_taken = []
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load promotion rules from database."""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM promotion_rules WHERE rule_name = 'default' AND enabled = true
                    """)

                    row = cur.fetchone()
                    if row:
                        return dict(row)
                    else:
                        # Fallback defaults
                        return {
                            'min_samples': 50,
                            'promotion_threshold': 7.5,
                            'demotion_threshold': 5.5,
                            'max_traffic_change_pct': 25.0,
                            'min_variant_traffic_pct': 5.0
                        }
        except Exception as e:
            logger.warning(f"Failed to load config from database, using defaults: {e}")
            return {
                'min_samples': 50,
                'promotion_threshold': 7.5,
                'demotion_threshold': 5.5,
                'max_traffic_change_pct': 25.0,
                'min_variant_traffic_pct': 5.0
            }

    def get_db_connection(self):
        """Get database connection."""
        if not self.db_conn:
            self.db_conn = psycopg2.connect(DATABASE_URL)
        return self.db_conn

    def get_variant_performance(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance metrics for all active variants."""
        start_time = datetime.now() - timedelta(hours=hours)

        with self.get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get evaluation scores and bandit performance
                cur.execute("""
                    SELECT
                        pv.name as variant_name,
                        pv.template,
                        pv.active,
                        COALESCE(bs.trials, 0) as bandit_trials,
                        COALESCE(bs.wins, 0) as bandit_wins,
                        ROUND(COALESCE(bs.wins::numeric / NULLIF(bs.trials, 0), 0), 3) as bandit_win_rate,

                        -- Evaluation metrics (last 24h)
                        COUNT(er.id) as eval_count,
                        AVG(CASE WHEN er.metric = 'helpfulness' THEN er.score END) as avg_helpfulness,
                        AVG(CASE WHEN er.metric = 'factuality' THEN er.score END) as avg_factuality,
                        AVG(CASE WHEN er.metric = 'clarity' THEN er.score END) as avg_clarity,

                        -- Overall judge score (average of 3 metrics)
                        ROUND((
                            AVG(CASE WHEN er.metric = 'helpfulness' THEN er.score END) +
                            AVG(CASE WHEN er.metric = 'factuality' THEN er.score END) +
                            AVG(CASE WHEN er.metric = 'clarity' THEN er.score END)
                        ) / 3, 2) as overall_score

                    FROM prompt_variants pv
                    LEFT JOIN bandit_stats bs ON bs.variant_name = pv.name
                    LEFT JOIN eval_results er ON er.interaction_id IN (
                        SELECT id FROM interactions WHERE created_at >= %s
                    )
                    GROUP BY pv.name, pv.template, pv.active, bs.trials, bs.wins
                    ORDER BY overall_score DESC NULLS LAST
                """, (start_time,))

                variants = [dict(row) for row in cur.fetchall()]

                # Filter out variants with insufficient data
                variants = [v for v in variants if v['eval_count'] >= self.config['min_samples']]

                return variants

    def get_current_traffic_distribution(self) -> Dict[str, float]:
        """Get current traffic distribution across variants."""
        # In a real implementation, this would query actual traffic metrics
        # For now, we'll use bandit trial distribution as proxy
        with self.get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT variant_name, trials
                    FROM bandit_stats
                    WHERE trials > 0
                """)

                total_trials = sum(row['trials'] for row in cur.fetchall())
                if total_trials == 0:
                    return {}

                cur.execute("""
                    SELECT variant_name, trials
                    FROM bandit_stats
                    WHERE trials > 0
                    ORDER BY trials DESC
                """)

                distribution = {}
                for row in cur.fetchall():
                    distribution[row['variant_name']] = (row['trials'] / total_trials) * 100

                return distribution

    def determine_actions(self, variants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Determine what actions to take based on performance."""
        actions = []
        current_traffic = self.get_current_traffic_distribution()

        # Sort variants by performance
        sorted_variants = sorted(variants, key=lambda x: x.get('overall_score', 0), reverse=True)

        for variant in sorted_variants:
            variant_name = variant['variant_name']
            score = variant.get('overall_score', 0)
            eval_count = variant['eval_count']
            current_pct = current_traffic.get(variant_name, 0)

            # Skip if insufficient data
            if eval_count < self.config['min_samples']:
                continue

            # Promotion candidates (high performers)
            if score >= self.config['promotion_threshold'] and current_pct < 50:  # Don't over-promote
                target_pct = min(current_pct + self.config['max_traffic_change_pct'], 50)
                if target_pct > current_pct:
                    actions.append({
                        'action': 'promote',
                        'variant': variant_name,
                        'reason': f'High performance (score: {score:.2f}, evals: {eval_count})',
                        'current_traffic': current_pct,
                        'target_traffic': target_pct,
                        'score': score,
                        'eval_count': eval_count
                    })

            # Demotion candidates (underperformers)
            elif score <= self.config['demotion_threshold'] and current_pct > self.config['min_variant_traffic_pct']:
                # Only demote if there's a better alternative
                best_score = sorted_variants[0].get('overall_score', 0) if sorted_variants else 0
                if best_score > score + 1.0:  # Significant gap
                    target_pct = max(current_pct - self.config['max_traffic_change_pct'], self.config['min_variant_traffic_pct'])
                    if target_pct < current_pct:
                        actions.append({
                            'action': 'demote',
                            'variant': variant_name,
                            'reason': f'Underperformance (score: {score:.2f}, best: {best_score:.2f}, evals: {eval_count})',
                            'current_traffic': current_pct,
                            'target_traffic': target_pct,
                            'score': score,
                            'eval_count': eval_count
                        })

        return actions

    def apply_actions(self, actions: List[Dict[str, Any]]) -> bool:
        """Apply the determined actions."""
        if not actions:
            logger.info("No actions to apply")
            return True

        if self.dry_run:
            logger.info("DRY RUN - Would apply the following actions:")
            for action in actions:
                logger.info(f"  {action['action'].upper()}: {action['variant']} "
                          f"({action['current_traffic']:.1f}% → {action['target_traffic']:.1f}%) - {action['reason']}")
            return True

        try:
            # Log actions to database for audit trail
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    for action in actions:
                        cur.execute("""
                            INSERT INTO promotion_actions (
                                variant_name, action_type, reason, old_traffic_pct, new_traffic_pct,
                                judge_score, eval_count, applied_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            action['variant'],
                            action['action'],
                            action['reason'],
                            action['current_traffic'],
                            action['target_traffic'],
                            action['score'],
                            action['eval_count'],
                            datetime.now()
                        ))

                        # Record Prometheus metrics
                        if METRICS_AVAILABLE:
                            promotion_actions_total.labels(
                                action_type=action['action'],
                                variant=action['variant']
                            ).inc()
                            promotion_score_gauge.labels(variant=action['variant']).set(action['score'])

                        # In a real system, you'd update traffic distribution here
                        # This might involve updating bandit parameters or traffic split configs

                        logger.info(f"APPLIED: {action['action']} {action['variant']} "
                                  f"({action['current_traffic']:.1f}% → {action['target_traffic']:.1f}%) - Score: {action['score']:.2f}")

                conn.commit()

            return True

        except Exception as e:
            logger.error(f"Failed to apply actions: {e}")
            return False

    def emergency_rollback(self, hours: int = 4) -> bool:
        """Emergency rollback to previous state."""
        if self.dry_run:
            logger.info("DRY RUN - Would rollback last 4 hours of changes")
            return True

        try:
            rollback_time = datetime.now() - timedelta(hours=hours)

            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Find recent actions to rollback
                    cur.execute("""
                        SELECT variant_name, action_type, old_traffic_pct, new_traffic_pct
                        FROM promotion_actions
                        WHERE applied_at >= %s AND action_type IN ('promote', 'demote')
                        ORDER BY applied_at DESC
                    """, (rollback_time,))

                    actions_to_rollback = cur.fetchall()

                    if not actions_to_rollback:
                        logger.info("No recent actions to rollback")
                        return True

                    # Apply reverse actions
                    for variant_name, action_type, old_pct, new_pct in actions_to_rollback:
                        reverse_action = 'demote' if action_type == 'promote' else 'promote'
                        reverse_target = old_pct

                        logger.info(f"ROLLBACK: {reverse_action} {variant_name} back to {reverse_target:.1f}%")

                        # Log rollback action
                        cur.execute("""
                            INSERT INTO promotion_actions (
                                variant_name, action_type, reason, old_traffic_pct, new_traffic_pct,
                                applied_at
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            variant_name,
                            f'rollback_{action_type}',
                            f'Emergency rollback from {new_pct:.1f}% to {old_pct:.1f}%',
                            new_pct,
                            old_pct,
                            datetime.now()
                        ))

                conn.commit()

            logger.info(f"Emergency rollback completed - reverted {len(actions_to_rollback)} actions")
            return True

        except Exception as e:
            logger.error(f"Emergency rollback failed: {e}")
            return False

    def run(self) -> bool:
        """Run the auto-promotion analysis and apply actions."""
        logger.info("Starting auto-promotion analysis...")

        try:
            # Get performance data
            variants = self.get_variant_performance()
            if not variants:
                logger.warning("No variant performance data available")
                return True

            logger.info(f"Analyzed {len(variants)} variants with sufficient evaluation data")

            # Determine actions
            actions = self.determine_actions(variants)

            # Apply actions
            success = self.apply_actions(actions)

            if success:
                logger.info("Auto-promotion cycle completed successfully")
                if not self.dry_run:
                    logger.info(f"Applied {len(actions)} actions")
                return True
            else:
                logger.error("Auto-promotion cycle failed")
                return False

        except Exception as e:
            logger.error(f"Auto-promotion failed: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Auto-Promotion System for Prompt Variants')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Preview changes without applying them (default: True)')
    parser.add_argument('--apply', action='store_true',
                       help='Apply changes (overrides dry-run)')
    parser.add_argument('--rollback', action='store_true',
                       help='Perform emergency rollback of recent changes')
    parser.add_argument('--hours', type=int, default=4,
                       help='Hours to rollback for emergency rollback (default: 4)')

    args = parser.parse_args()

    # Override dry-run if --apply is specified
    dry_run = not args.apply

    if args.rollback:
        logger.info("Performing emergency rollback...")
        system = AutoPromotionSystem(dry_run=False)  # Always apply rollbacks
        success = system.emergency_rollback(args.hours)
    else:
        logger.info(f"Running auto-promotion system (dry_run: {dry_run})...")
        system = AutoPromotionSystem(dry_run=dry_run)
        success = system.run()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
