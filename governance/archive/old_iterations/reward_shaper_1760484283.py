"""
Advanced Reward Shaping with Human + Judge Blending
==================================================

Implements precise reward calculation blending human feedback with judge scores,
including drift correction and confidence weighting.

Key Features:
- Human feedback mapping: {-1,0,+1} → [0,1]
- Judge score normalization: [1,10] → [-1,1] → [0,1]
- Confidence-weighted blending (0.9 human + 0.25 judge)
- Drift correction with rolling z-score normalization
- Fallback handling for missing signals
"""

import json
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class JudgeScores:
    """Normalized judge scores for helpfulness, factuality, clarity."""
    helpfulness: float  # [1,10] raw
    factuality: float   # [1,10] raw
    clarity: float      # [1,10] raw

    def normalize(self) -> Tuple[float, float, float]:
        """
        Normalize judge scores from [1,10] to [-1,1].

        j_k = (s_k - 5.5) / 4.5 → j_k ∈ [-1,1]
        """
        def norm_score(score: float) -> float:
            return (score - 5.5) / 4.5

        return (
            norm_score(self.helpfulness),
            norm_score(self.factuality),
            norm_score(self.clarity)
        )

@dataclass
class FeedbackSignal:
    """Combined feedback signal with human and judge components."""
    human_feedback: Optional[int] = None  # -1, 0, or +1
    judge_scores: Optional[JudgeScores] = None
    timestamp: datetime = None
    domain: str = "general"  # For drift correction per domain

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class RewardShaper:
    """
    Advanced reward shaper with human + judge blending and drift correction.

    Implements:
    - Human feedback mapping: h ∈ {-1,0,+1} → h' = (h+1)/2 ∈ [0,1]
    - Judge aggregation: mean of normalized dimensions → [0,1]
    - Confidence-weighted blending: 0.9 * human + 0.25 * judge
    - Drift correction with rolling z-score per domain
    """

    def __init__(self,
                 human_weight: float = 0.9,
                 judge_weight: float = 0.25,
                 drift_window_days: int = 7,
                 drift_clip_sigma: float = 2.0):
        self.human_weight = human_weight
        self.judge_weight = judge_weight
        self.drift_window_days = drift_window_days
        self.drift_clip_sigma = drift_clip_sigma

        # Rolling statistics for drift correction per domain
        self.domain_stats: Dict[str, deque] = {}
        self.max_window_size = drift_window_days * 24 * 60 * 60  # Convert to seconds

    def shape_reward(self, feedback: FeedbackSignal) -> float:
        """
        Shape reward from human + judge feedback with drift correction.

        Algorithm:
        1. Process human feedback: h ∈ {-1,0,+1} → h' = (h+1)/2 ∈ [0,1]
        2. Process judge scores: normalize → aggregate → map to [0,1]
        3. Apply drift correction to judge scores
        4. Weight and blend: r = clip(0.9*h' + 0.25*j'', 0, 1)
        5. Fallback handling for missing signals
        """
        human_reward = self._process_human_feedback(feedback.human_feedback)
        judge_reward = self._process_judge_feedback(feedback.judge_scores, feedback.domain)

        # Confidence weighting with cap at 1.0
        total_weight = self.human_weight + self.judge_weight
        if total_weight > 1.0:
            human_weight_norm = self.human_weight / total_weight
            judge_weight_norm = self.judge_weight / total_weight
        else:
            human_weight_norm = self.human_weight
            judge_weight_norm = self.judge_weight

        # Blend rewards
        if human_reward is not None and judge_reward is not None:
            blended = human_weight_norm * human_reward + judge_weight_norm * judge_reward
        elif human_reward is not None:
            blended = human_reward  # Fallback to human only
        elif judge_reward is not None:
            blended = judge_reward  # Fallback to judge only
        else:
            blended = 0.5  # Neutral fallback

        # Clip to [0,1]
        final_reward = np.clip(blended, 0.0, 1.0)

        logger.debug(f"Shaped reward: human={human_reward:.3f}, judge={judge_reward:.3f}, final={final_reward:.3f}")

        # Update drift correction statistics
        if judge_reward is not None:
            self._update_domain_stats(feedback.domain, judge_reward, feedback.timestamp)

        return final_reward

    def _process_human_feedback(self, human: Optional[int]) -> Optional[float]:
        """Process human feedback: {-1,0,+1} → [0,1]."""
        if human is None:
            return None

        if human not in [-1, 0, 1]:
            logger.warning(f"Invalid human feedback: {human}, expected -1, 0, or 1")
            return None

        # h' = (h + 1) / 2
        return (human + 1.0) / 2.0

    def _process_judge_feedback(self, judge: Optional[JudgeScores], domain: str) -> Optional[float]:
        """Process judge feedback with drift correction."""
        if judge is None:
            return None

        # Normalize individual dimensions: [1,10] → [-1,1]
        help_norm, fact_norm, clar_norm = judge.normalize()

        # Aggregate: mean of normalized dimensions
        judge_aggregate = (help_norm + fact_norm + clar_norm) / 3.0

        # Apply drift correction
        judge_corrected = self._apply_drift_correction(judge_aggregate, domain)

        # Map to [0,1]: j'' = (j' + 1) / 2
        judge_reward = (judge_corrected + 1.0) / 2.0

        return np.clip(judge_reward, 0.0, 1.0)

    def _apply_drift_correction(self, judge_score: float, domain: str) -> float:
        """
        Apply drift correction using rolling z-score normalization.

        Maintain rolling mean/std per domain, z-score new judges and clip to [-2,2].
        """
        if domain not in self.domain_stats:
            self.domain_stats[domain] = deque(maxlen=self.max_window_size)

        # Get historical scores for this domain (within time window)
        recent_scores = []
        cutoff_time = datetime.now() - timedelta(days=self.drift_window_days)

        for score, timestamp in self.domain_stats[domain]:
            if timestamp > cutoff_time:
                recent_scores.append(score)

        if len(recent_scores) < 10:  # Need minimum samples for stable statistics
            corrected = judge_score  # No correction if insufficient history
        else:
            mean_score = np.mean(recent_scores)
            std_score = np.std(recent_scores)

            if std_score > 0:
                # Z-score normalization
                z_score = (judge_score - mean_score) / std_score
                # Clip to [-2, 2] sigma
                z_score_clipped = np.clip(z_score, -self.drift_clip_sigma, self.drift_clip_sigma)
                # Convert back to original scale
                corrected = z_score_clipped * std_score + mean_score
            else:
                corrected = judge_score

        # Store this score for future drift correction
        self.domain_stats[domain].append((judge_score, datetime.now()))

        return corrected

    def _update_domain_stats(self, domain: str, score: float, timestamp: datetime):
        """Update rolling statistics for drift correction."""
        if domain not in self.domain_stats:
            self.domain_stats[domain] = deque(maxlen=self.max_window_size)

        self.domain_stats[domain].append((score, timestamp))

        # Clean old entries
        cutoff_time = datetime.now() - timedelta(days=self.drift_window_days)
        while self.domain_stats[domain] and self.domain_stats[domain][0][1] < cutoff_time:
            self.domain_stats[domain].popleft()

    def get_domain_stats(self, domain: str) -> Dict:
        """Get drift correction statistics for a domain."""
        if domain not in self.domain_stats:
            return {'samples': 0, 'mean': 0.0, 'std': 0.0}

        scores = [score for score, _ in self.domain_stats[domain]]
        if not scores:
            return {'samples': 0, 'mean': 0.0, 'std': 0.0}

        return {
            'samples': len(scores),
            'mean': float(np.mean(scores)),
            'std': float(np.std(scores)),
            'min': float(np.min(scores)),
            'max': float(np.max(scores))
        }

    def get_all_domain_stats(self) -> Dict[str, Dict]:
        """Get drift correction statistics for all domains."""
        return {domain: self.get_domain_stats(domain) for domain in self.domain_stats}

    def save_state(self, filepath: str):
        """Save reward shaper state to JSON file."""
        # Convert deques to lists for serialization
        domain_stats_serializable = {}
        for domain, scores_deque in self.domain_stats.items():
            domain_stats_serializable[domain] = list(scores_deque)

        state = {
            'config': {
                'human_weight': self.human_weight,
                'judge_weight': self.judge_weight,
                'drift_window_days': self.drift_window_days,
                'drift_clip_sigma': self.drift_clip_sigma
            },
            'domain_stats': domain_stats_serializable
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)

    def load_state(self, filepath: str):
        """Load reward shaper state from JSON file."""
        with open(filepath, 'r') as f:
            state = json.load(f)

        # Load configuration
        config = state.get('config', {})
        self.human_weight = config.get('human_weight', 0.9)
        self.judge_weight = config.get('judge_weight', 0.25)
        self.drift_window_days = config.get('drift_window_days', 7)
        self.drift_clip_sigma = config.get('drift_clip_sigma', 2.0)

        # Load domain statistics
        for domain, scores_list in state.get('domain_stats', {}).items():
            self.domain_stats[domain] = deque(scores_list, maxlen=self.max_window_size)

        logger.info(f"Loaded reward shaper state with {len(self.domain_stats)} domains")


# Global reward shaper instance
_shaper = None

def get_reward_shaper() -> RewardShaper:
    """Get or create global reward shaper instance."""
    global _shaper
    if _shaper is None:
        _shaper = RewardShaper()
    return _shaper
