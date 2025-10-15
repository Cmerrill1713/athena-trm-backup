#!/usr/bin/env python3
"""
Predictive Drift Analytics for Constitutional Immune System
===========================================================

Advanced predictive analytics that forecasts governance drift before it occurs.
This module provides early warning capabilities to the constitutional immune system.

Key Features:
- Time series forecasting of governance metrics
- Anomaly prediction using statistical and ML models
- Early warning alerts for potential drift
- Predictive quarantine recommendations
- Trend analysis and pattern recognition

Usage:
    from scripts.predictive_drift_analytics import get_predictive_analytics_engine
    predictor = get_predictive_analytics_engine()
    forecast = predictor.forecast_governance_drift(hours_ahead=24)
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'AI-Projects', 'universal-ai-tools', 'src'))

from core.governance_drift_detection import (
    GovernanceDriftMetrics,
    DriftType,
    DriftSeverity
)

logger = logging.getLogger(__name__)

class PredictionModel(Enum):
    """Types of prediction models available."""
    LINEAR_TREND = "linear_trend"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    ISOLATION_FOREST = "isolation_forest"
    STATISTICAL_PROCESS_CONTROL = "statistical_process_control"

class PredictionConfidence(Enum):
    """Confidence levels for predictions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class DriftPrediction:
    """Represents a predicted governance drift event."""
    prediction_id: str
    predicted_drift_type: DriftType
    predicted_severity: DriftSeverity
    confidence_level: PredictionConfidence
    predicted_at: datetime
    time_to_occurence_hours: float
    forecasted_value: float
    baseline_value: float
    deviation_percentage: float
    contributing_factors: List[str]
    recommended_actions: List[str]
    model_used: PredictionModel
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PredictiveAnalyticsConfig:
    """Configuration for predictive drift analytics."""
    # Forecasting parameters
    forecast_horizon_hours: int = 24
    min_history_points: int = 100
    prediction_interval_minutes: int = 60  # How often to run predictions

    # Model parameters
    use_linear_trend: bool = True
    use_exponential_smoothing: bool = True
    use_isolation_forest: bool = True
    use_statistical_control: bool = True

    # Thresholds
    trend_alert_threshold: float = 0.1  # 10% trend deviation
    anomaly_score_threshold: float = -0.5  # Isolation Forest threshold
    control_limit_sigma: float = 3.0  # Standard deviations for control limits

    # Risk levels
    low_risk_hours: float = 24
    medium_risk_hours: float = 12
    high_risk_hours: float = 6
    critical_risk_hours: float = 2

class PredictiveDriftAnalytics:
    """Predictive analytics engine for governance drift forecasting."""

    def __init__(self, config: Optional[PredictiveAnalyticsConfig] = None):
        self.config = config or PredictiveAnalyticsConfig()
        self.metrics_history: List[GovernanceDriftMetrics] = []
        self.prediction_history: List[DriftPrediction] = []
        self.models_trained = False

        # Initialize models
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )

        logger.info("🧠 Predictive drift analytics engine initialized")

    def add_metrics_sample(self, metrics: GovernanceDriftMetrics) -> None:
        """Add a new metrics sample to the history."""
        self.metrics_history.append(metrics)

        # Keep only recent history (30 days)
        cutoff = datetime.now() - timedelta(days=30)
        self.metrics_history = [
            m for m in self.metrics_history
            if m.timestamp > cutoff
        ]

        # Retrain models if we have enough data
        if len(self.metrics_history) >= self.config.min_history_points:
            self._train_models()

    def forecast_governance_drift(self, hours_ahead: int = 24) -> List[DriftPrediction]:
        """Forecast potential governance drift events."""
        if len(self.metrics_history) < self.config.min_history_points:
            logger.warning(f"Insufficient data for prediction. Need {self.config.min_history_points} points, have {len(self.metrics_history)}")
            return []

        predictions = []

        # Generate predictions from different models
        if self.config.use_linear_trend:
            trend_predictions = self._predict_linear_trend(hours_ahead)
            predictions.extend(trend_predictions)

        if self.config.use_exponential_smoothing:
            smoothing_predictions = self._predict_exponential_smoothing(hours_ahead)
            predictions.extend(smoothing_predictions)

        if self.config.use_isolation_forest and self.models_trained:
            anomaly_predictions = self._predict_anomalies(hours_ahead)
            predictions.extend(anomaly_predictions)

        if self.config.use_statistical_control:
            spc_predictions = self._predict_statistical_control(hours_ahead)
            predictions.extend(spc_predictions)

        # Filter and rank predictions
        predictions = self._filter_predictions(predictions)

        # Store predictions
        self.prediction_history.extend(predictions)

        return predictions

    def _train_models(self) -> None:
        """Train predictive models on historical data."""
        try:
            # Prepare data for training
            df = self._metrics_to_dataframe()

            if len(df) < self.config.min_history_points:
                return

            # Train Isolation Forest for anomaly detection
            features = ['violation_rate', 'policy_delta_score', 'behavioral_consistency_score', 'governance_score_avg']
            X = df[features].values

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train model
            self.isolation_forest.fit(X_scaled)

            self.models_trained = True
            logger.info("✅ Predictive models trained successfully")

        except Exception as e:
            logger.error(f"Failed to train predictive models: {e}")

    def _predict_linear_trend(self, hours_ahead: int) -> List[DriftPrediction]:
        """Predict drift using linear trend analysis."""
        predictions = []

        if len(self.metrics_history) < 10:
            return predictions

        try:
            df = self._metrics_to_dataframe()

            # Predict for each metric
            metrics_to_predict = [
                ('violation_rate', DriftType.VIOLATION_RATE_SPIKE),
                ('policy_delta_score', DriftType.POLICY_DELTA_DRIFT),
                ('behavioral_consistency_score', DriftType.BEHAVIORAL_SHIFT),
                ('governance_score_avg', DriftType.GOVERNANCE_SCORE_DEGRADATION)
            ]

            for metric_name, drift_type in metrics_to_predict:
                prediction = self._linear_trend_prediction(df, metric_name, drift_type, hours_ahead)
                if prediction:
                    predictions.append(prediction)

        except Exception as e:
            logger.error(f"Linear trend prediction failed: {e}")

        return predictions

    def _linear_trend_prediction(self, df: pd.DataFrame, metric_name: str, drift_type: DriftType, hours_ahead: int) -> Optional[DriftPrediction]:
        """Generate linear trend prediction for a specific metric."""
        try:
            # Fit linear regression
            X = np.arange(len(df)).reshape(-1, 1)
            y = df[metric_name].values

            model = LinearRegression()
            model.fit(X, y)

            # Predict future values
            future_points = int(hours_ahead / 2)  # Predict every 2 hours
            future_X = np.arange(len(df), len(df) + future_points).reshape(-1, 1)
            predictions = model.predict(future_X)

            # Check for concerning trends
            current_value = df[metric_name].iloc[-1]
            predicted_value = predictions[-1]  # Value at end of forecast horizon

            if metric_name == 'governance_score_avg':
                # For governance score, decreasing is bad
                deviation_pct = (current_value - predicted_value) / current_value if current_value > 0 else 0
                threshold_exceeded = deviation_pct > self.config.trend_alert_threshold
            else:
                # For other metrics, increasing is bad
                deviation_pct = (predicted_value - current_value) / max(current_value, 0.001)
                threshold_exceeded = deviation_pct > self.config.trend_alert_threshold

            if threshold_exceeded:
                confidence = self._calculate_trend_confidence(deviation_pct, hours_ahead)
                severity = self._calculate_risk_severity(hours_ahead, confidence)

                return DriftPrediction(
                    prediction_id=f"trend_{metric_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    predicted_drift_type=drift_type,
                    predicted_severity=severity,
                    confidence_level=confidence,
                    predicted_at=datetime.now(),
                    time_to_occurence_hours=hours_ahead,
                    forecasted_value=predicted_value,
                    baseline_value=current_value,
                    deviation_percentage=deviation_pct,
                    contributing_factors=[f"Linear trend in {metric_name}"],
                    recommended_actions=[
                        "Monitor trend closely",
                        "Consider preventive governance adjustments",
                        "Prepare quarantine procedures if trend continues"
                    ],
                    model_used=PredictionModel.LINEAR_TREND,
                    metadata={
                        "slope": model.coef_[0],
                        "intercept": model.intercept_,
                        "r_squared": model.score(X, y)
                    }
                )

        except Exception as e:
            logger.error(f"Linear trend prediction for {metric_name} failed: {e}")

        return None

    def _predict_exponential_smoothing(self, hours_ahead: int) -> List[DriftPrediction]:
        """Predict drift using exponential smoothing."""
        predictions = []

        if len(self.metrics_history) < 20:
            return predictions

        try:
            df = self._metrics_to_dataframe()

            # Simple exponential smoothing prediction
            metrics_to_predict = ['violation_rate', 'policy_delta_score']

            for metric_name in metrics_to_predict:
                series = df[metric_name]

                # Calculate exponential moving average
                ema = series.ewm(alpha=0.1).mean()

                # Predict next values
                current_ema = ema.iloc[-1]
                trend = (ema.iloc[-1] - ema.iloc[-10]) / 10  # Trend over last 10 points

                predicted_value = current_ema + (trend * (hours_ahead / 2))

                # Check for concerning predictions
                current_value = series.iloc[-1]

                if metric_name == 'violation_rate':
                    deviation_pct = (predicted_value - current_value) / max(current_value, 0.001)
                    if deviation_pct > self.config.trend_alert_threshold:
                        drift_type = DriftType.VIOLATION_RATE_SPIKE
                        severity = self._calculate_risk_severity(hours_ahead, PredictionConfidence.MEDIUM)

                        predictions.append(DriftPrediction(
                            prediction_id=f"smoothing_{metric_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            predicted_drift_type=drift_type,
                            predicted_severity=severity,
                            confidence_level=PredictionConfidence.MEDIUM,
                            predicted_at=datetime.now(),
                            time_to_occurence_hours=hours_ahead,
                            forecasted_value=predicted_value,
                            baseline_value=current_value,
                            deviation_percentage=deviation_pct,
                            contributing_factors=[f"Exponential smoothing trend in {metric_name}"],
                            recommended_actions=[
                                "Monitor violation patterns",
                                "Review recent strategy deployments",
                                "Consider proactive quarantine measures"
                            ],
                            model_used=PredictionModel.EXPONENTIAL_SMOOTHING,
                            metadata={"ema_alpha": 0.1, "trend": trend}
                        ))

        except Exception as e:
            logger.error(f"Exponential smoothing prediction failed: {e}")

        return predictions

    def _predict_anomalies(self, hours_ahead: int) -> List[DriftPrediction]:
        """Predict anomalies using isolation forest."""
        predictions = []

        if not self.models_trained or len(self.metrics_history) < self.config.min_history_points:
            return predictions

        try:
            # Get recent metrics for anomaly detection
            recent_metrics = self.metrics_history[-50:]  # Last 50 points

            # Prepare features
            features = []
            for metrics in recent_metrics:
                features.append([
                    metrics.violation_rate,
                    metrics.policy_delta_score,
                    metrics.behavioral_consistency_score,
                    metrics.governance_score_avg
                ])

            X = np.array(features)

            # Scale features
            X_scaled = self.scaler.transform(X)

            # Predict anomalies
            anomaly_scores = self.isolation_forest.decision_function(X_scaled)

            # Check if recent points are becoming anomalous
            recent_scores = anomaly_scores[-10:]  # Last 10 points
            avg_recent_score = np.mean(recent_scores)

            if avg_recent_score < self.config.anomaly_score_threshold:
                # Increasing anomaly trend detected
                severity = DriftSeverity.HIGH if avg_recent_score < -0.7 else DriftSeverity.MEDIUM

                predictions.append(DriftPrediction(
                    prediction_id=f"anomaly_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    predicted_drift_type=DriftType.BEHAVIORAL_SHIFT,
                    predicted_severity=severity,
                    confidence_level=PredictionConfidence.HIGH,
                    predicted_at=datetime.now(),
                    time_to_occurence_hours=hours_ahead * 0.5,  # Expected sooner
                    forecasted_value=avg_recent_score,
                    baseline_value=0.0,  # Normal baseline
                    deviation_percentage=abs(avg_recent_score),
                    contributing_factors=[
                        "Increasing anomaly scores across governance metrics",
                        "Behavioral patterns deviating from normal distribution"
                    ],
                    recommended_actions=[
                        "Immediate governance review required",
                        "Increase monitoring frequency",
                        "Prepare for potential quarantine activation"
                    ],
                    model_used=PredictionModel.ISOLATION_FOREST,
                    metadata={
                        "anomaly_score": avg_recent_score,
                        "threshold": self.config.anomaly_score_threshold,
                        "contamination_rate": 0.1
                    }
                ))

        except Exception as e:
            logger.error(f"Anomaly prediction failed: {e}")

        return predictions

    def _predict_statistical_control(self, hours_ahead: int) -> List[DriftPrediction]:
        """Predict drift using statistical process control."""
        predictions = []

        if len(self.metrics_history) < 30:
            return predictions

        try:
            df = self._metrics_to_dataframe()

            # Check each metric for control limit violations
            metrics_to_check = [
                ('violation_rate', DriftType.VIOLATION_RATE_SPIKE, 'increase'),
                ('policy_delta_score', DriftType.POLICY_DELTA_DRIFT, 'increase'),
                ('behavioral_consistency_score', DriftType.BEHAVIORAL_SHIFT, 'decrease'),
                ('governance_score_avg', DriftType.GOVERNANCE_SCORE_DEGRADATION, 'decrease')
            ]

            for metric_name, drift_type, direction in metrics_to_check:
                series = df[metric_name]

                # Calculate control limits
                mean = series.mean()
                std = series.std()

                upper_limit = mean + (self.config.control_limit_sigma * std)
                lower_limit = mean - (self.config.control_limit_sigma * std)

                # Check recent trend toward limits
                recent_values = series.tail(10)
                current_value = series.iloc[-1]

                if direction == 'increase':
                    # Check if trending toward upper limit
                    if current_value > (upper_limit * 0.8):  # Within 80% of limit
                        trend_direction = np.polyfit(range(len(recent_values)), recent_values, 1)[0]
                        if trend_direction > 0:  # Trending upward
                            predictions.append(self._create_spc_prediction(
                                metric_name, drift_type, current_value, upper_limit,
                                trend_direction, hours_ahead
                            ))
                else:  # decrease
                    # Check if trending toward lower limit
                    if current_value < (lower_limit * 1.2):  # Within 120% of limit (since lower)
                        trend_direction = np.polyfit(range(len(recent_values)), recent_values, 1)[0]
                        if trend_direction < 0:  # Trending downward
                            predictions.append(self._create_spc_prediction(
                                metric_name, drift_type, current_value, lower_limit,
                                trend_direction, hours_ahead
                            ))

        except Exception as e:
            logger.error(f"Statistical control prediction failed: {e}")

        return predictions

    def _create_spc_prediction(self, metric_name: str, drift_type: DriftType,
                             current_value: float, limit: float, trend: float,
                             hours_ahead: int) -> DriftPrediction:
        """Create a statistical process control prediction."""
        deviation_pct = abs(current_value - limit) / max(abs(limit), 0.001)

        severity = DriftSeverity.MEDIUM
        if deviation_pct > 0.5:
            severity = DriftSeverity.HIGH

        confidence = PredictionConfidence.MEDIUM
        if abs(trend) > 0.01:  # Strong trend
            confidence = PredictionConfidence.HIGH

        return DriftPrediction(
            prediction_id=f"spc_{metric_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            predicted_drift_type=drift_type,
            predicted_severity=severity,
            confidence_level=confidence,
            predicted_at=datetime.now(),
            time_to_occurence_hours=hours_ahead * 0.7,  # Expected relatively soon
            forecasted_value=limit,
            baseline_value=current_value,
            deviation_percentage=deviation_pct,
            contributing_factors=[
                f"Statistical process control limit approach in {metric_name}",
                f"Trend direction: {'increasing' if trend > 0 else 'decreasing'}"
            ],
            recommended_actions=[
                "Monitor control chart closely",
                "Investigate root causes of trend",
                "Consider process adjustments to prevent limit violation"
            ],
            model_used=PredictionModel.STATISTICAL_PROCESS_CONTROL,
            metadata={
                "control_limit": limit,
                "trend_slope": trend,
                "sigma_level": self.config.control_limit_sigma
            }
        )

    def _calculate_trend_confidence(self, deviation_pct: float, hours_ahead: float) -> PredictionConfidence:
        """Calculate confidence level for trend-based predictions."""
        if deviation_pct > 0.3 and hours_ahead < 12:
            return PredictionConfidence.CRITICAL
        elif deviation_pct > 0.2 and hours_ahead < 24:
            return PredictionConfidence.HIGH
        elif deviation_pct > 0.1:
            return PredictionConfidence.MEDIUM
        else:
            return PredictionConfidence.LOW

    def _calculate_risk_severity(self, hours_ahead: float, confidence: PredictionConfidence) -> DriftSeverity:
        """Calculate risk severity based on time to occurrence and confidence."""
        if hours_ahead <= self.config.critical_risk_hours or confidence == PredictionConfidence.CRITICAL:
            return DriftSeverity.CRITICAL
        elif hours_ahead <= self.config.high_risk_hours or confidence == PredictionConfidence.HIGH:
            return DriftSeverity.HIGH
        elif hours_ahead <= self.config.medium_risk_hours:
            return DriftSeverity.MEDIUM
        else:
            return DriftSeverity.LOW

    def _filter_predictions(self, predictions: List[DriftPrediction]) -> List[DriftPrediction]:
        """Filter and deduplicate predictions."""
        if not predictions:
            return predictions

        # Sort by severity and confidence
        predictions.sort(key=lambda p: (p.predicted_severity.value, p.confidence_level.value), reverse=True)

        # Remove duplicates by drift type (keep highest severity)
        seen_types = set()
        filtered = []

        for prediction in predictions:
            if prediction.predicted_drift_type not in seen_types:
                seen_types.add(prediction.predicted_drift_type)
                filtered.append(prediction)

        return filtered[:5]  # Return top 5 predictions

    def _metrics_to_dataframe(self) -> pd.DataFrame:
        """Convert metrics history to pandas DataFrame."""
        data = []
        for metrics in self.metrics_history:
            data.append({
                'timestamp': metrics.timestamp,
                'violation_rate': metrics.violation_rate,
                'policy_delta_score': metrics.policy_delta_score,
                'behavioral_consistency_score': metrics.behavioral_consistency_score,
                'governance_score_avg': metrics.governance_score_avg
            })

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp').sort_index()

        return df

    def get_prediction_statistics(self) -> Dict[str, Any]:
        """Get statistics about prediction performance."""
        if not self.prediction_history:
            return {"total_predictions": 0}

        recent_predictions = [
            p for p in self.prediction_history
            if p.predicted_at > datetime.now() - timedelta(days=7)
        ]

        return {
            "total_predictions": len(self.prediction_history),
            "recent_predictions": len(recent_predictions),
            "predictions_by_type": {
                drift_type.value: len([p for p in recent_predictions if p.predicted_drift_type == drift_type])
                for drift_type in DriftType
            },
            "predictions_by_severity": {
                severity.value: len([p for p in recent_predictions if p.predicted_severity == severity])
                for severity in DriftSeverity
            },
            "average_confidence": np.mean([p.confidence_level.value for p in recent_predictions]) if recent_predictions else 0
        }

# Global instance
_predictive_analytics_engine = None

def get_predictive_analytics_engine(config: Optional[PredictiveAnalyticsConfig] = None) -> PredictiveDriftAnalytics:
    """Get the global predictive analytics engine instance."""
    global _predictive_analytics_engine
    if _predictive_analytics_engine is None:
        _predictive_analytics_engine = PredictiveDriftAnalytics(config)
    return _predictive_analytics_engine

# Quick test function
def test_predictive_analytics():
    """Test the predictive analytics functionality."""
    print("🧠 Testing Predictive Drift Analytics")
    print("=" * 50)

    # Create engine
    engine = get_predictive_analytics_engine()

    # Add some sample data
    base_time = datetime.now() - timedelta(hours=200)

    for i in range(150):
        # Create slightly increasing violation rate trend
        violation_rate = 0.02 + (i * 0.0001) + np.random.normal(0, 0.005)

        metrics = GovernanceDriftMetrics(
            timestamp=base_time + timedelta(hours=i),
            violation_rate=max(0, min(1, violation_rate)),
            policy_delta_score=0.05 + np.random.normal(0, 0.01),
            behavioral_consistency_score=0.95 + np.random.normal(0, 0.02),
            governance_score_avg=0.88 + np.random.normal(0, 0.03)
        )
        engine.add_metrics_sample(metrics)

    # Generate predictions
    predictions = engine.forecast_governance_drift(hours_ahead=12)

    print(f"✅ Generated {len(predictions)} predictions")
    for pred in predictions[:3]:  # Show top 3
        print(f"   • {pred.predicted_drift_type.value}: {pred.predicted_severity.value} severity")
        print(f"     Confidence: {pred.confidence_level.value}")
        print(f"     Time to occurrence: {pred.time_to_occurence_hours:.1f} hours")
    # Show statistics
    stats = engine.get_prediction_statistics()
    print("\n📊 Prediction Statistics:")
    print(f"   Total predictions: {stats['total_predictions']}")
    print(f"   Average confidence: {stats.get('average_confidence', 0):.2f}")

    print("\n🎉 Predictive analytics test completed!")

if __name__ == "__main__":
    test_predictive_analytics()
