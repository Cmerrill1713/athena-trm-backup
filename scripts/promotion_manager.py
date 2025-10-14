#!/usr/bin/env python3
"""
Promotion System Management and Manual Overrides

Provides administrative controls for the auto-promotion system:
- Manual promotion/demotion of variants
- Override promotion rules
- View promotion history and analytics
- Emergency controls

Usage:
    python3 scripts/promotion_manager.py status          # View current status
    python3 scripts/promotion_manager.py promote v1      # Manually promote variant
    python3 scripts/promotion_manager.py demote v2       # Manually demote variant
    python3 scripts/promotion_manager.py rules           # View/edit promotion rules
    python3 scripts/promotion_manager.py history         # View promotion history
"""

import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "dbname=universal_ai_tools user=postgres password=postgres host=athena-postgres port=5432")

class PromotionManager:
    def __init__(self):
        self.db_conn = None

    def get_db_connection(self):
        """Get database connection."""
        if not self.db_conn:
            self.db_conn = psycopg2.connect(DATABASE_URL)
        return self.db_conn

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive promotion system status."""
        status = {
            'rules': {},
            'variants': {},
            'recent_actions': [],
            'system_health': {}
        }

        with self.get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get current rules
                cur.execute("SELECT * FROM promotion_rules WHERE rule_name = 'default'")
                rules = cur.fetchone()
                status['rules'] = dict(rules) if rules else {}

                # Get variant status
                cur.execute("""
                    SELECT
                        pv.name,
                        pv.active,
                        COALESCE(bs.trials, 0) as trials,
                        COALESCE(bs.wins, 0) as wins,
                        ROUND(COALESCE(bs.wins::numeric / NULLIF(bs.trials, 0), 0), 3) as win_rate,
                        COUNT(er.id) as eval_count,
                        AVG(CASE WHEN er.metric = 'helpfulness' THEN er.score END) as helpfulness,
                        AVG(CASE WHEN er.metric = 'factuality' THEN er.score END) as factuality,
                        AVG(CASE WHEN er.metric = 'clarity' THEN er.score END) as clarity
                    FROM prompt_variants pv
                    LEFT JOIN bandit_stats bs ON bs.variant_name = pv.name
                    LEFT JOIN eval_results er ON er.interaction_id IN (
                        SELECT id FROM interactions WHERE created_at >= NOW() - INTERVAL '24 hours'
                    )
                    GROUP BY pv.name, pv.active, bs.trials, bs.wins
                """)

                variants = [dict(row) for row in cur.fetchall()]
                status['variants'] = {v['name']: v for v in variants}

                # Get recent actions (last 7 days)
                cur.execute("""
                    SELECT * FROM promotion_actions
                    WHERE applied_at >= NOW() - INTERVAL '7 days'
                    ORDER BY applied_at DESC
                    LIMIT 20
                """)

                status['recent_actions'] = [dict(row) for row in cur.fetchall()]

                # System health metrics
                cur.execute("""
                    SELECT
                        COUNT(CASE WHEN applied_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as actions_24h,
                        COUNT(CASE WHEN applied_at >= NOW() - INTERVAL '7 days' THEN 1 END) as actions_7d,
                        AVG(CASE WHEN applied_at >= NOW() - INTERVAL '24 hours' THEN judge_score END) as avg_score_24h
                    FROM promotion_actions
                    WHERE applied_at >= NOW() - INTERVAL '7 days'
                """)

                health = cur.fetchone()
                status['system_health'] = dict(health) if health else {}

        return status

    def manual_promotion_action(self, variant_name: str, action: str, reason: str = "Manual override") -> bool:
        """Perform manual promotion/demotion action."""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get current traffic estimate (simplified)
                    current_traffic = 20.0  # Default assumption

                    # Calculate target traffic based on action
                    if action == 'promote':
                        target_traffic = min(current_traffic + 10, 50)  # +10% manual promotion
                    elif action == 'demote':
                        target_traffic = max(current_traffic - 10, 5)   # -10% manual demotion
                    else:
                        logger.error(f"Invalid action: {action}")
                        return False

                    # Get current evaluation score
                    cur.execute("""
                        SELECT
                            AVG(CASE WHEN metric = 'helpfulness' THEN score END) +
                            AVG(CASE WHEN metric = 'factuality' THEN score END) +
                            AVG(CASE WHEN metric = 'clarity' THEN score END)
                        FROM eval_results er
                        JOIN interactions i ON i.id = er.interaction_id
                        WHERE i.prompt_variant = %s AND i.created_at >= NOW() - INTERVAL '24 hours'
                    """, (variant_name,))

                    avg_score = cur.fetchone()[0] or 5.0

                    # Count evaluations
                    cur.execute("""
                        SELECT COUNT(*) FROM eval_results er
                        JOIN interactions i ON i.id = er.interaction_id
                        WHERE i.prompt_variant = %s AND i.created_at >= NOW() - INTERVAL '24 hours'
                    """, (variant_name,))

                    eval_count = cur.fetchone()[0] or 0

                    # Record the manual action
                    cur.execute("""
                        INSERT INTO promotion_actions (
                            variant_name, action_type, reason, old_traffic_pct, new_traffic_pct,
                            judge_score, eval_count, applied_at, applied_by
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        variant_name, action, reason, current_traffic, target_traffic,
                        avg_score, eval_count, datetime.now(), 'manual_override'
                    ))

                conn.commit()

            logger.info(f"MANUAL {action.upper()}: {variant_name} ({current_traffic:.1f}% → {target_traffic:.1f}%) - {reason}")
            return True

        except Exception as e:
            logger.error(f"Manual action failed: {e}")
            return False

    def update_rules(self, rule_updates: Dict[str, Any]) -> bool:
        """Update promotion rules."""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Build update query
                    set_parts = []
                    values = []
                    for key, value in rule_updates.items():
                        if key != 'rule_name':  # Don't update primary key
                            set_parts.append(f"{key} = %s")
                            values.append(value)

                    if not set_parts:
                        logger.warning("No valid rule updates provided")
                        return False

                    query = f"""
                        UPDATE promotion_rules
                        SET {', '.join(set_parts)}, updated_at = %s
                        WHERE rule_name = 'default'
                    """
                    values.append(datetime.now())

                    cur.execute(query, values)

                    if cur.rowcount == 0:
                        logger.warning("No rules updated - rule 'default' may not exist")
                        return False

                conn.commit()

            logger.info(f"Updated promotion rules: {rule_updates}")
            return True

        except Exception as e:
            logger.error(f"Rule update failed: {e}")
            return False

    def show_status(self):
        """Display comprehensive system status."""
        status = self.get_system_status()

        print("🚀 Promotion System Status")
        print("=" * 50)

        # Rules
        print("\n📋 Current Rules:")
        rules = status.get('rules', {})
        if rules:
            for key, value in rules.items():
                if key not in ['rule_name', 'updated_at']:
                    print(f"  {key}: {value}")
        else:
            print("  No rules configured")

        # Variant status
        print("\n🎯 Variant Performance (24h):")
        variants = status.get('variants', {})
        if variants:
            print("<30"            print("-" * 80)
            for name, data in sorted(variants.items(), key=lambda x: x[1].get('overall_score', 0), reverse=True):
                active = "✅" if data.get('active') else "❌"
                trials = data.get('trials', 0)
                win_rate = data.get('win_rate', 0)
                evals = data.get('eval_count', 0)
                helpfulness = data.get('helpfulness', 0)
                factuality = data.get('factuality', 0)
                clarity = data.get('clarity', 0)
                overall = (helpfulness + factuality + clarity) / 3 if (helpfulness + factuality + clarity) > 0 else 0

                print("<30")
        else:
            print("  No variant data available")

        # Recent actions
        print("\n🔄 Recent Actions (7 days):")
        actions = status.get('recent_actions', [])
        if actions:
            for action in actions[:10]:  # Show last 10
                ts = action['applied_at'].strftime("%m-%d %H:%M")
                print(f"  {ts}: {action['action_type']} {action['variant_name']} "
                      f"({action['old_traffic_pct']:.1f}% → {action['new_traffic_pct']:.1f}%)")
        else:
            print("  No recent actions")

        # System health
        print("\n💚 System Health:")
        health = status.get('system_health', {})
        if health:
            actions_24h = health.get('actions_24h', 0)
            actions_7d = health.get('actions_7d', 0)
            avg_score = health.get('avg_score_24h', 0)
            print(f"  Actions (24h): {actions_24h}")
            print(f"  Actions (7d): {actions_7d}")
            print(".2f"        else:
            print("  No health data available")

def main():
    parser = argparse.ArgumentParser(description='Promotion System Management')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Status command
    subparsers.add_parser('status', help='Show system status')

    # Manual action commands
    promote_parser = subparsers.add_parser('promote', help='Manually promote a variant')
    promote_parser.add_argument('variant', help='Variant name to promote')
    promote_parser.add_argument('--reason', default='Manual override', help='Reason for promotion')

    demote_parser = subparsers.add_parser('demote', help='Manually demote a variant')
    demote_parser.add_argument('variant', help='Variant name to demote')
    demote_parser.add_argument('--reason', default='Manual override', help='Reason for demotion')

    # Rules command
    rules_parser = subparsers.add_parser('rules', help='View/edit promotion rules')
    rules_parser.add_argument('--update', nargs='*', help='Update rules (key=value pairs)')

    # History command
    subparsers.add_parser('history', help='Show promotion history')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = PromotionManager()

    if args.command == 'status':
        manager.show_status()

    elif args.command == 'promote':
        success = manager.manual_promotion_action(args.variant, 'promote', args.reason)
        print("✅ Promotion successful" if success else "❌ Promotion failed")

    elif args.command == 'demote':
        success = manager.manual_promotion_action(args.variant, 'demote', args.reason)
        print("✅ Demotion successful" if success else "❌ Demotion failed")

    elif args.command == 'rules':
        if args.update:
            # Parse key=value pairs
            updates = {}
            for update in args.update:
                if '=' in update:
                    key, value = update.split('=', 1)
                    # Try to parse as number or boolean
                    if value.isdigit():
                        value = int(value)
                    elif value.lower() in ('true', 'false'):
                        value = value.lower() == 'true'
                    elif '.' in value and value.replace('.', '').isdigit():
                        value = float(value)
                    updates[key] = value

            success = manager.update_rules(updates)
            print("✅ Rules updated" if success else "❌ Rules update failed")
        else:
            status = manager.get_system_status()
            rules = status.get('rules', {})
            print("Current Promotion Rules:")
            for key, value in rules.items():
                if key not in ['rule_name', 'updated_at']:
                    print(f"  {key}: {value}")

    elif args.command == 'history':
        status = manager.get_system_status()
        actions = status.get('recent_actions', [])
        print("Promotion History (Recent 20 actions):")
        print("-" * 80)
        for action in actions:
            ts = action['applied_at'].strftime("%Y-%m-%d %H:%M:%S")
            print("<15")

if __name__ == "__main__":
    main()
