#!/usr/bin/env python3
"""
Nightly Learning Effectiveness Report
Generates comprehensive analysis of learning system performance
"""

import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import Dict, Any
import json

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "dbname=universal_ai_tools user=postgres password=postgres host=athena-postgres port=5432")

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(DATABASE_URL)

def get_date_range(days: int = 7):
    """Get date range for analysis."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date

def get_bandit_performance(days: int = 7) -> Dict[str, Any]:
    """Analyze bandit prompt optimization performance."""
    start_date, end_date = get_date_range(days)

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Get variant performance
            cur.execute("""
                SELECT
                    bs.variant_name,
                    bs.trials,
                    bs.wins,
                    ROUND(bs.wins::numeric / NULLIF(bs.trials, 0), 3) as win_rate,
                    pv.template
                FROM bandit_stats bs
                JOIN prompt_variants pv ON pv.name = bs.variant_name
                WHERE pv.active = true
                ORDER BY win_rate DESC
            """)

            variants = [dict(row) for row in cur.fetchall()]

            # Get recent trends (last 24 hours)
            cur.execute("""
                SELECT
                    i.prompt_variant,
                    COUNT(*) as requests,
                    AVG(EXTRACT(epoch FROM (i.created_at - lag(i.created_at) OVER (ORDER BY i.created_at)))) as avg_time_between_requests
                FROM interactions i
                WHERE i.created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY i.prompt_variant
                ORDER BY requests DESC
            """)

            recent_trends = [dict(row) for row in cur.fetchall()]

            return {
                "variants": variants,
                "recent_trends": recent_trends,
                "analysis_period_days": days
            }

def get_evaluation_performance(days: int = 7) -> Dict[str, Any]:
    """Analyze LLM evaluation system performance."""
    start_date, end_date = get_date_range(days)

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Get daily evaluation averages
            cur.execute("""
                SELECT
                    DATE_TRUNC('day', ts) as day,
                    AVG(CASE WHEN metric = 'helpfulness' THEN score END) as helpfulness,
                    AVG(CASE WHEN metric = 'factuality' THEN score END) as factuality,
                    AVG(CASE WHEN metric = 'clarity' THEN score END) as clarity,
                    COUNT(DISTINCT interaction_id) as evaluated_interactions,
                    COUNT(*) as total_evaluations
                FROM eval_results
                WHERE ts >= %s AND ts <= %s
                GROUP BY DATE_TRUNC('day', ts)
                ORDER BY day DESC
            """, (start_date, end_date))

            daily_stats = [dict(row) for row in cur.fetchall()]

            # Get evaluation distribution by score ranges
            cur.execute("""
                SELECT
                    metric,
                    COUNT(CASE WHEN score >= 8 THEN 1 END) as excellent,
                    COUNT(CASE WHEN score >= 6 AND score < 8 THEN 1 END) as good,
                    COUNT(CASE WHEN score >= 4 AND score < 6 THEN 1 END) as average,
                    COUNT(CASE WHEN score < 4 THEN 1 END) as poor,
                    AVG(score) as avg_score,
                    COUNT(*) as total
                FROM eval_results
                WHERE ts >= %s AND ts <= %s
                GROUP BY metric
                ORDER BY metric
            """, (start_date, end_date))

            score_distribution = [dict(row) for row in cur.fetchall()]

            return {
                "daily_stats": daily_stats,
                "score_distribution": score_distribution,
                "analysis_period_days": days
            }

def get_learning_correlation(days: int = 7) -> Dict[str, Any]:
    """Analyze correlation between evaluation scores and bandit performance."""
    start_date, end_date = get_date_range(days)

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Get interactions with both evaluation and bandit data
            cur.execute("""
                SELECT
                    i.prompt_variant,
                    AVG(CASE WHEN er.metric = 'helpfulness' THEN er.score END) as avg_helpfulness,
                    AVG(CASE WHEN er.metric = 'factuality' THEN er.score END) as avg_factuality,
                    AVG(CASE WHEN er.metric = 'clarity' THEN er.score END) as avg_clarity,
                    COUNT(DISTINCT i.id) as interaction_count
                FROM interactions i
                LEFT JOIN eval_results er ON er.interaction_id = i.id
                WHERE i.created_at >= %s AND i.created_at <= %s
                GROUP BY i.prompt_variant
                HAVING COUNT(DISTINCT i.id) > 5  -- Minimum sample size
                ORDER BY avg_helpfulness DESC
            """, (start_date, end_date))

            variant_evaluation = [dict(row) for row in cur.fetchall()]

            # Get feedback patterns
            cur.execute("""
                SELECT
                    i.prompt_variant,
                    COUNT(CASE WHEN i.reward > 0 THEN 1 END) as positive_feedbacks,
                    COUNT(CASE WHEN i.reward < 0 THEN 1 END) as negative_feedbacks,
                    COUNT(CASE WHEN i.reward = 0 THEN 1 END) as neutral_feedbacks,
                    AVG(i.reward) as avg_reward
                FROM interactions i
                WHERE i.created_at >= %s AND i.created_at <= %s
                AND i.reward IS NOT NULL
                GROUP BY i.prompt_variant
                ORDER BY avg_reward DESC
            """, (start_date, end_date))

            feedback_patterns = [dict(row) for row in cur.fetchall()]

            # Get promotion system activity
            cur.execute("""
                SELECT
                    COUNT(*) as total_actions,
                    COUNT(CASE WHEN action_type = 'promote' THEN 1 END) as promotions,
                    COUNT(CASE WHEN action_type = 'demote' THEN 1 END) as demotions,
                    AVG(judge_score) as avg_promoted_score,
                    MAX(applied_at) as last_action_time
                FROM promotion_actions
                WHERE applied_at >= %s AND applied_at <= %s
            """, (start_date, end_date))

            promotion_activity = cur.fetchone()
            promotion_data = dict(promotion_activity) if promotion_activity else {}

            return {
                "variant_evaluation": variant_evaluation,
                "feedback_patterns": feedback_patterns,
                "promotion_activity": promotion_data,
                "analysis_period_days": days
            }

def generate_markdown_report(report_data: Dict[str, Any]) -> str:
    """Generate comprehensive Markdown report."""
    now = datetime.now()
    report_date = now.strftime("%Y-%m-%d")
    analysis_period = report_data.get("analysis_period_days", 7)

    report = f"""# 🧠 Learning Effectiveness Report - {report_date}

**Analysis Period:** Last {analysis_period} days
**Generated:** {now.strftime("%Y-%m-%d %H:%M:%S")}

---

## 🤖 Bandit Prompt Optimization Performance

### Variant Leaderboard
| Variant | Trials | Wins | Win Rate | Status |
|---------|--------|------|----------|--------|
"""

    for variant in report_data["bandit_performance"]["variants"]:
        status = "🏆 Best" if variant == report_data["bandit_performance"]["variants"][0] else "Active"
        report += f"""| {variant['variant_name']} | {variant['trials']} | {variant['wins']} | {variant['win_rate']:.3f} | {status} |
"""

    report += "\n### Recent Traffic Trends (24h)\n"
    report += "| Variant | Requests | Avg Time Between |\n"
    report += "|---------|----------|------------------|\n"

    for trend in report_data["bandit_performance"]["recent_trends"]:
        avg_time = f"{trend['avg_time_between_requests']:.1f}s" if trend['avg_time_between_requests'] else "N/A"
        report += f"| {trend['prompt_variant']} | {trend['requests']} | {avg_time} |\n"

    report += "\n---\n\n## 🧠 LLM Evaluation System Performance\n\n"

    # Evaluation daily stats
    if report_data["evaluation_performance"]["daily_stats"]:
        report += "### Daily Evaluation Averages\n"
        report += "| Date | Helpfulness | Factuality | Clarity | Evaluations |\n"
        report += "|------|-------------|------------|---------|-------------|\n"

        for day_stat in report_data["evaluation_performance"]["daily_stats"][:7]:  # Last 7 days
            date_str = day_stat['day'].strftime("%Y-%m-%d")
            helpful = ".1f" if day_stat['helpfulness'] else "N/A"
            factual = ".1f" if day_stat['factuality'] else "N/A"
            clear = ".1f" if day_stat['clarity'] else "N/A"
            report += f"| {date_str} | {helpful} | {factual} | {clear} | {day_stat['evaluated_interactions']} |\n"

    # Score distribution
    if report_data["evaluation_performance"]["score_distribution"]:
        report += "\n### Score Distribution by Metric\n"
        for metric_data in report_data["evaluation_performance"]["score_distribution"]:
            report += f"\n#### {metric_data['metric'].title()}\n"
            report += f"- **Average Score:** {metric_data['avg_score']:.2f}/10\n"
            report += f"- **Excellent (8-10):** {metric_data['excellent']} responses\n"
            report += f"- **Good (6-8):** {metric_data['good']} responses\n"
            report += f"- **Average (4-6):** {metric_data['average']} responses\n"
            report += f"- **Poor (<4):** {metric_data['poor']} responses\n"

    report += "\n---\n\n## 🔗 Learning System Correlation\n\n"

    # Variant evaluation correlation
    if report_data["learning_correlation"]["variant_evaluation"]:
        report += "### Evaluation Scores by Variant\n"
        report += "| Variant | Helpfulness | Factuality | Clarity | Interactions |\n"
        report += "|---------|-------------|------------|---------|--------------|\n"

        for variant_eval in report_data["learning_correlation"]["variant_evaluation"]:
            report += f"| {variant_eval['prompt_variant']} | {variant_eval['avg_helpfulness']:.2f} | {variant_eval['avg_factuality']:.2f} | {variant_eval['avg_clarity']:.2f} | {variant_eval['interaction_count']} |\n"

    # Feedback patterns
    if report_data["learning_correlation"]["feedback_patterns"]:
        report += "\n### Feedback Patterns by Variant\n"
        report += "| Variant | 👍 Positive | 👎 Negative | 😐 Neutral | Avg Reward |\n"
        report += "|---------|------------|-------------|-----------|------------|\n"

        for feedback in report_data["learning_correlation"]["feedback_patterns"]:
            report += f"| {feedback['prompt_variant']} | {feedback['positive_feedbacks']} | {feedback['negative_feedbacks']} | {feedback['neutral_feedbacks']} | {feedback['avg_reward']:.3f} |\n"

    # Promotion system activity
    promotion_data = report_data["learning_correlation"].get("promotion_activity", {})
    if promotion_data:
        report += "\n### Auto-Promotion System Activity\n"
        total_actions = promotion_data.get('total_actions', 0)
        promotions = promotion_data.get('promotions', 0)
        demotions = promotion_data.get('demotions', 0)
        avg_score = promotion_data.get('avg_promoted_score', 0)
        last_action = promotion_data.get('last_action_time')

        report += f"- **Total Actions:** {total_actions}\n"
        report += f"- **Promotions:** {promotions}\n"
        report += f"- **Demotions:** {demotions}\n"
        report += ".2f"
        if last_action:
            report += f"- **Last Action:** {last_action.strftime('%Y-%m-%d %H:%M:%S')}\n"

    report += "\n---\n\n## 📊 Key Insights & Recommendations\n\n"

    # Generate insights based on data
    insights = []

    # Bandit insights
    if report_data["bandit_performance"]["variants"]:
        best_variant = report_data["bandit_performance"]["variants"][0]
        if best_variant["trials"] > 10:
            win_rate = best_variant["win_rate"]
            if win_rate > 0.6:
                insights.append(f"✅ **Strong performer:** {best_variant['variant_name']} has {win_rate:.1%} win rate - consider making it default")
            elif win_rate < 0.3:
                insights.append(f"⚠️ **Underperformer:** {best_variant['variant_name']} has only {win_rate:.1%} win rate - review or deactivate")

    # Evaluation insights
    if report_data["evaluation_performance"]["score_distribution"]:
        for metric_data in report_data["evaluation_performance"]["score_distribution"]:
            avg_score = metric_data['avg_score']
            if avg_score < 5:
                insights.append(f"⚠️ **Quality concern:** {metric_data['metric']} scores averaging {avg_score:.1f}/10 - investigate responses")
            elif avg_score > 7:
                insights.append(f"✅ **Quality strength:** {metric_data['metric']} scores averaging {avg_score:.1f}/10 - excellent performance")

    # Correlation insights
    if report_data["learning_correlation"]["variant_evaluation"]:
        top_eval = report_data["learning_correlation"]["variant_evaluation"][0]
        if top_eval["avg_helpfulness"] > 7:
            insights.append(f"🎯 **Evaluation leader:** {top_eval['prompt_variant']} scores {top_eval['avg_helpfulness']:.1f}/10 helpfulness")
        elif top_eval["avg_helpfulness"] < 5:
            insights.append(f"⚠️ **Evaluation concern:** Best variant only {top_eval['avg_helpfulness']:.1f}/10 helpfulness - review prompt quality")

    if not insights:
        insights.append("📊 System operating within normal parameters - continue monitoring")

    for insight in insights:
        report += f"- {insight}\n"

    report += "\n---\n\n## 🎯 Action Items\n\n"

    # Generate action items based on data
    actions = []

    # Check for variants that need attention
    bandit_data = report_data["bandit_performance"]
    if len(bandit_data["variants"]) > 1:
        win_rates = [v["win_rate"] for v in bandit_data["variants"]]
        if max(win_rates) - min(win_rates) > 0.3:  # Significant difference
            actions.append("📈 **Optimize variants:** Large performance gap between variants - consider promoting winner or investigating underperformers")

    # Check evaluation coverage
    eval_data = report_data["evaluation_performance"]
    if eval_data["daily_stats"] and len(eval_data["daily_stats"]) > 0:
        recent_day = eval_data["daily_stats"][0]
        if recent_day["evaluated_interactions"] < 10:  # Low evaluation volume
            actions.append("🔍 **Increase evaluation coverage:** Only evaluating ~10 interactions/day - consider enabling evaluation for more traffic")

    # Check feedback correlation
    correlation_data = report_data["learning_correlation"]
    if correlation_data["variant_evaluation"] and correlation_data["feedback_patterns"]:
        # Look for mismatches between evaluation and feedback
        eval_leader = correlation_data["variant_evaluation"][0]["prompt_variant"]
        feedback_leader = correlation_data["feedback_patterns"][0]["prompt_variant"] if correlation_data["feedback_patterns"] else None

        if feedback_leader and eval_leader != feedback_leader:
            actions.append(f"🤔 **Investigate discrepancy:** Evaluation favors {eval_leader} but feedback favors {feedback_leader} - check for evaluation bias")

    if not actions:
        actions.append("✅ **System healthy:** No immediate action items - continue monitoring performance")

    for action in actions:
        report += f"- {action}\n"

    report += "\n---\n\n*Report generated automatically by learning system analysis*"

    return report

def main():
    """Generate and save nightly learning report."""
    try:
        print("🔍 Generating nightly learning effectiveness report...")

        # Gather all data
        report_data = {
            "bandit_performance": get_bandit_performance(),
            "evaluation_performance": get_evaluation_performance(),
            "learning_correlation": get_learning_correlation()
        }

        # Generate Markdown report
        report_md = generate_markdown_report(report_data)

        # Save report
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)

        report_date = datetime.now().strftime("%Y-%m-%d")
        report_file = f"{reports_dir}/learning_report_{report_date}.md"

        with open(report_file, 'w') as f:
            f.write(report_md)

        print(f"✅ Report saved to: {report_file}")

        # Also save JSON data for programmatic access
        json_file = f"{reports_dir}/learning_data_{report_date}.json"
        with open(json_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"✅ Data saved to: {json_file}")

    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
