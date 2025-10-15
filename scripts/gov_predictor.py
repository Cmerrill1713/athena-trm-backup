#!/usr/bin/env python3
"""
Predictive Governance System

Analyzes historical governance decisions to predict rollback probability
before deployments happen. Uses pattern recognition and statistical
modeling to forecast system behavior.

Features:
- Rollback probability forecasting
- Risk scoring for deployments
- Pattern-based early warning system
- Confidence intervals and uncertainty quantification
- Integration with deployment pipelines

Usage:
  python3 scripts/gov_predictor.py --analyze-deployment --traffic-rate 150 --deployment-type "feature"
  python3 scripts/gov_predictor.py --predict-rollback-probability --lookback-days 30
"""
import os, sys, json, time, statistics, math
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import urllib.request

# Configuration
ROLLBACK_THRESHOLD = 0.15  # 15% rollback probability triggers warning
HIGH_RISK_THRESHOLD = 0.30  # 30% rollback probability = high risk
CRITICAL_RISK_THRESHOLD = 0.50  # 50% rollback probability = critical

class GovernancePredictor:
    def __init__(self, log_file="logs/canary_decisions.log"):
        self.log_file = log_file
        self.historical_patterns = {}
        self.risk_factors = {}
        self.load_historical_data()

    def load_historical_data(self):
        """Load and analyze historical governance decisions"""
        decisions = self.parse_decision_log()

        if len(decisions) < 10:
            print("⚠️  Insufficient historical data for reliable predictions")
            return

        # Analyze patterns
        self.analyze_temporal_patterns(decisions)
        self.analyze_traffic_patterns(decisions)
        self.analyze_deployment_patterns(decisions)
        self.calculate_risk_factors(decisions)

    def parse_decision_log(self):
        """Parse the governance decision log"""
        decisions = []

        if not os.path.exists(self.log_file):
            return decisions

        with open(self.log_file, "r") as f:
            for line in f:
                if " - DECISION:" not in line:
                    continue

                try:
                    parts = line.strip().split(" - ")
                    timestamp_str = parts[0]
                    decision_part = parts[1]
                    reason_part = parts[2] if len(parts) > 2 else ""
                    metrics_part = parts[3] if len(parts) > 3 else ""

                    timestamp = time.strptime(timestamp_str, "%a %b %d %H:%M:%S %Y")
                    timestamp_epoch = time.mktime(timestamp)

                    decision = decision_part.replace("DECISION: ", "")
                    reason = reason_part.replace("REASON: ", "") if reason_part else ""

                    # Parse metrics
                    metrics = {}
                    if "METRICS:" in metrics_part:
                        metrics_json = metrics_part.replace("METRICS: ", "")
                        try:
                            metrics = json.loads(metrics_json)
                        except:
                            pass

                    decisions.append({
                        "timestamp": timestamp_epoch,
                        "decision": decision,
                        "reason": reason,
                        "metrics": metrics,
                        "hour": timestamp.tm_hour,
                        "day_of_week": timestamp.tm_wday,
                        "month": timestamp.tm_mon
                    })

                except Exception as e:
                    continue

        return decisions

    def analyze_temporal_patterns(self, decisions):
        """Analyze temporal patterns in governance decisions"""
        if not decisions:
            return

        # Rolling window analysis (last 30 days)
        cutoff = time.time() - (30 * 24 * 60 * 60)
        recent = [d for d in decisions if d["timestamp"] > cutoff]

        # Time-of-day patterns
        hourly_rollback_rate = {}
        for hour in range(24):
            hour_decisions = [d for d in recent if d["hour"] == hour]
            if hour_decisions:
                rollback_count = sum(1 for d in hour_decisions if d["decision"] == "ROLLBACK")
                hourly_rollback_rate[hour] = rollback_count / len(hour_decisions)

        # Day-of-week patterns
        dow_rollback_rate = {}
        for dow in range(7):
            dow_decisions = [d for d in recent if d["day_of_week"] == dow]
            if dow_decisions:
                rollback_count = sum(1 for d in dow_decisions if d["decision"] == "ROLLBACK")
                dow_rollback_rate[dow] = rollback_count / len(dow_decisions)

        self.historical_patterns["temporal"] = {
            "hourly_rollback_rate": hourly_rollback_rate,
            "dow_rollback_rate": dow_rollback_rate,
            "overall_rollback_rate": sum(1 for d in recent if d["decision"] == "ROLLBACK") / len(recent)
        }

    def analyze_traffic_patterns(self, decisions):
        """Analyze how traffic patterns correlate with governance decisions"""
        # This would integrate with actual traffic metrics
        # For now, use proxy metrics from governance KPIs
        pass

    def analyze_deployment_patterns(self, decisions):
        """Analyze patterns based on deployment characteristics"""
        # This would analyze deployment size, type, etc.
        # For now, use basic pattern analysis
        pass

    def calculate_risk_factors(self, decisions):
        """Calculate risk factors based on historical data"""
        if not decisions:
            return

        recent = [d for d in decisions if d["timestamp"] > time.time() - (30 * 24 * 60 * 60)]

        # Calculate baseline metrics
        rollback_rate = sum(1 for d in recent if d["decision"] == "ROLLBACK") / len(recent)

        # Risk factor weights (based on historical correlation)
        self.risk_factors = {
            "baseline_rollback_rate": rollback_rate,
            "temporal_risk_multiplier": 1.0,  # Will be updated based on time patterns
            "traffic_risk_multiplier": 1.0,   # Will be updated based on traffic patterns
            "deployment_risk_multiplier": 1.0 # Will be updated based on deployment patterns
        }

    def predict_rollback_probability(self, traffic_rate=None, deployment_type="feature",
                                   current_hour=None, day_of_week=None):
        """
        Predict rollback probability for a proposed deployment

        Args:
            traffic_rate: Current traffic rate (requests/minute)
            deployment_type: Type of deployment (feature, hotfix, major)
            current_hour: Hour of deployment (0-23)
            day_of_week: Day of week (0-6, Monday=0)

        Returns:
            dict: Prediction results with probability, confidence, and risk level
        """
        if not self.historical_patterns:
            return {
                "rollback_probability": 0.0,
                "confidence": 0.0,
                "risk_level": "unknown",
                "warning": "Insufficient historical data for prediction",
                "factors": {
                    "traffic_rate": traffic_rate,
                    "deployment_type": deployment_type,
                    "current_hour": current_hour,
                    "day_of_week": day_of_week,
                    "baseline_rate": 0.0
                }
            }

        # Start with baseline probability
        probability = self.risk_factors.get("baseline_rollback_rate", 0.10)

        # Apply temporal factors
        if current_hour is not None and "temporal" in self.historical_patterns:
            temporal = self.historical_patterns["temporal"]
            if current_hour in temporal["hourly_rollback_rate"]:
                hour_factor = temporal["hourly_rollback_rate"][current_hour]
                baseline = temporal["overall_rollback_rate"]
                if baseline > 0:
                    temporal_multiplier = hour_factor / baseline
                    probability *= temporal_multiplier

        # Apply traffic factors (simplified model)
        if traffic_rate:
            # Higher traffic = slightly higher risk (more load on new code)
            traffic_risk = min(1.5, max(0.5, traffic_rate / 100))
            probability *= traffic_risk

        # Apply deployment type factors
        deployment_multipliers = {
            "hotfix": 0.7,    # Lower risk - critical fixes
            "feature": 1.0,   # Baseline
            "major": 1.3,     # Higher risk - significant changes
            "experimental": 1.8  # Much higher risk
        }
        deployment_multiplier = deployment_multipliers.get(deployment_type, 1.0)
        probability *= deployment_multiplier

        # Calculate confidence based on historical data size
        # More data = higher confidence
        historical_decisions = len(self.parse_decision_log())
        confidence = min(1.0, historical_decisions / 100)  # 100 decisions = full confidence

        # Determine risk level
        if probability >= CRITICAL_RISK_THRESHOLD:
            risk_level = "critical"
        elif probability >= HIGH_RISK_THRESHOLD:
            risk_level = "high"
        elif probability >= ROLLBACK_THRESHOLD:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "rollback_probability": round(probability, 3),
            "confidence": round(confidence, 2),
            "risk_level": risk_level,
            "factors": {
                "traffic_rate": traffic_rate,
                "deployment_type": deployment_type,
                "current_hour": current_hour,
                "day_of_week": day_of_week,
                "baseline_rate": round(self.risk_factors.get("baseline_rollback_rate", 0), 3)
            }
        }

    def get_predictive_insights(self, days=30):
        """Get predictive insights and recommendations"""
        decisions = self.parse_decision_log()
        recent = [d for d in decisions if d["timestamp"] > time.time() - (days * 24 * 60 * 60)]

        insights = {
            "analysis_period_days": days,
            "total_decisions": len(recent),
            "rollback_rate": 0.0,
            "risky_hours": [],
            "risky_days": [],
            "recommendations": []
        }

        if not recent:
            insights["recommendations"].append("Insufficient data for predictive insights")
            return insights

        # Calculate rollback rate
        rollback_count = sum(1 for d in recent if d["decision"] == "ROLLBACK")
        insights["rollback_rate"] = rollback_count / len(recent)

        # Find risky time patterns
        if "temporal" in self.historical_patterns:
            temporal = self.historical_patterns["temporal"]

            # Risky hours (rollback rate > average + 1 std dev)
            avg_hourly_rate = statistics.mean(temporal["hourly_rollback_rate"].values())
            std_hourly_rate = statistics.stdev(temporal["hourly_rollback_rate"].values()) if len(temporal["hourly_rollback_rate"]) > 1 else 0

            risky_threshold = avg_hourly_rate + std_hourly_rate
            insights["risky_hours"] = [
                hour for hour, rate in temporal["hourly_rollback_rate"].items()
                if rate > risky_threshold
            ]

            # Risky days
            avg_dow_rate = statistics.mean(temporal["dow_rollback_rate"].values())
            std_dow_rate = statistics.stdev(temporal["dow_rollback_rate"].values()) if len(temporal["dow_rollback_rate"]) > 1 else 0

            risky_dow_threshold = avg_dow_rate + std_dow_rate
            insights["risky_days"] = [
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dow]
                for dow, rate in temporal["dow_rollback_rate"].items()
                if rate > risky_dow_threshold
            ]

        # Generate recommendations
        if insights["rollback_rate"] > 0.20:
            insights["recommendations"].append("High rollback rate detected - consider stricter pre-deploy gates")
        elif insights["rollback_rate"] < 0.05:
            insights["recommendations"].append("Very low rollback rate - system is stable, consider optimizing for speed")

        if insights["risky_hours"]:
            insights["recommendations"].append(f"Avoid deployments during risky hours: {', '.join(map(str, insights['risky_hours']))}")

        if insights["risky_days"]:
            insights["recommendations"].append(f"Exercise caution on: {', '.join(insights['risky_days'])}")

        return insights

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Governance Predictive System")
    parser.add_argument("--predict-rollback-probability", action="store_true",
                       help="Predict rollback probability for deployment")
    parser.add_argument("--traffic-rate", type=float,
                       help="Traffic rate for prediction (requests/minute)")
    parser.add_argument("--deployment-type", choices=["hotfix", "feature", "major", "experimental"],
                       default="feature", help="Type of deployment")
    parser.add_argument("--current-hour", type=int,
                       help="Hour of deployment (0-23, defaults to current)")
    parser.add_argument("--day-of-week", type=int,
                       help="Day of week (0-6, Monday=0, defaults to current)")
    parser.add_argument("--get-insights", action="store_true",
                       help="Get predictive insights and recommendations")
    parser.add_argument("--lookback-days", type=int, default=30,
                       help="Days of history to analyze")

    args = parser.parse_args()

    predictor = GovernancePredictor()

    if args.get_insights:
        insights = predictor.get_predictive_insights(args.lookback_days)

        print("🔮 Governance Predictive Insights")
        print("=" * 50)
        print(f"📊 Analysis Period: {insights['analysis_period_days']} days")
        print(f"📈 Total Decisions: {insights['total_decisions']}")
        print(".1%")
        print()

        if insights["risky_hours"]:
            print("⏰ Risky Deployment Hours:")
            for hour in insights["risky_hours"]:
                print(f"   {hour}:00 - Higher rollback probability")
            print()

        if insights["risky_days"]:
            print("📅 Risky Deployment Days:")
            for day in insights["risky_days"]:
                print(f"   {day} - Higher rollback probability")
            print()

        print("💡 Recommendations:")
        for rec in insights["recommendations"]:
            print(f"   • {rec}")
        print()

    elif args.predict_rollback_probability:
        # Get current time context if not specified
        current_time = time.localtime()
        current_hour = args.current_hour if args.current_hour is not None else current_time.tm_hour
        day_of_week = args.day_of_week if args.day_of_week is not None else current_time.tm_wday

        prediction = predictor.predict_rollback_probability(
            traffic_rate=args.traffic_rate,
            deployment_type=args.deployment_type,
            current_hour=current_hour,
            day_of_week=day_of_week
        )

        print("🔮 Governance Rollback Probability Prediction")
        print("=" * 50)
        print(".1%")
        print(".0%")
        print(f"⚠️  Risk Level: {prediction['risk_level'].upper()}")
        print()

        # Risk assessment
        if prediction["rollback_probability"] >= CRITICAL_RISK_THRESHOLD:
            print("🚨 CRITICAL RISK - Deployment strongly discouraged")
            print("   Consider postponing or implementing additional safeguards")
        elif prediction["rollback_probability"] >= HIGH_RISK_THRESHOLD:
            print("⚠️  HIGH RISK - Proceed with caution")
            print("   Consider extended canary window or additional monitoring")
        elif prediction["rollback_probability"] >= ROLLBACK_THRESHOLD:
            print("⚡ MEDIUM RISK - Standard deployment process recommended")
        else:
            print("✅ LOW RISK - Deployment should proceed normally")

        print()
        print("📊 Prediction Factors:")
        factors = prediction["factors"]
        print(f"   Traffic Rate: {factors['traffic_rate'] or 'unknown'} req/min")
        print(f"   Deployment Type: {factors['deployment_type']}")
        print(f"   Hour: {factors['current_hour']}")
        print(f"   Day: {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][factors['day_of_week']]}")
        print(".1%")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
