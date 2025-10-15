"""
Canary Statistical Evaluation

Uses Wilson score intervals to determine if canary is statistically
significantly different from control. Prevents false rollbacks due to
random variance.

Key insight: Raw delta can be misleading with small sample sizes.
Need both magnitude (>3-5%) AND statistical significance (p<0.05).
"""

import math
from typing import Tuple


def wilson_score_interval(
    successes: int,
    trials: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate Wilson score confidence interval for success rate

    More accurate than normal approximation for small samples.

    Args:
        successes: Number of successes
        trials: Total number of trials
        confidence: Confidence level (default: 0.95 for 95%)

    Returns:
        (lower_bound, upper_bound) for success rate

    Reference: https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
    """
    if trials == 0:
        return (0.0, 0.0)

    # Z-score for confidence level
    # 0.95 → 1.96, 0.99 → 2.58
    z = {
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576
    }.get(confidence, 1.96)

    p = successes / trials
    denominator = 1 + z**2 / trials
    centre = (p + z**2 / (2 * trials)) / denominator
    margin = z * math.sqrt(p * (1 - p) / trials + z**2 / (4 * trials**2)) / denominator

    lower = max(0.0, centre - margin)
    upper = min(1.0, centre + margin)

    return (lower, upper)


def is_significantly_different(
    canary_successes: int,
    canary_trials: int,
    control_successes: int,
    control_trials: int,
    min_delta: float = 0.03,  # 3% minimum difference
    confidence: float = 0.95
) -> Tuple[bool, float, str]:
    """
    Check if canary is significantly different from control

    Uses Wilson score intervals. Canary is significantly worse if:
    - Canary upper bound < Control lower bound (non-overlapping)
    - AND absolute delta > min_delta

    Args:
        canary_successes: Canary successes
        canary_trials: Canary trials
        control_successes: Control successes
        control_trials: Control trials
        min_delta: Minimum meaningful difference (default: 3%)
        confidence: Confidence level (default: 95%)

    Returns:
        (is_significantly_worse, delta, explanation)
    """
    if canary_trials < 10 or control_trials < 10:
        return (False, 0.0, "Insufficient sample size (need 10+ trials each)")

    canary_rate = canary_successes / canary_trials
    control_rate = control_successes / control_trials
    delta = canary_rate - control_rate

    # Get confidence intervals
    canary_lower, canary_upper = wilson_score_interval(canary_successes, canary_trials, confidence)
    control_lower, control_upper = wilson_score_interval(control_successes, control_trials, confidence)

    # Check if intervals overlap
    intervals_overlap = not (canary_upper < control_lower or control_upper < canary_lower)

    # Significantly worse if:
    # 1. Canary upper bound < control lower bound (non-overlapping, canary clearly worse)
    # 2. AND absolute delta > min_delta
    is_sig_worse = (
        canary_upper < control_lower and
        abs(delta) > min_delta
    )

    # Build explanation
    if is_sig_worse:
        explanation = (
            f"Canary is significantly worse: {canary_rate:.1%} vs {control_rate:.1%} "
            f"(delta: {delta:+.1%}, p<{1-confidence:.2f})"
        )
    elif abs(delta) > min_delta and not intervals_overlap:
        if delta < 0:
            explanation = f"Canary appears worse but not statistically significant yet (delta: {delta:+.1%})"
        else:
            explanation = f"Canary appears better: {canary_rate:.1%} vs {control_rate:.1%} (delta: {delta:+.1%})"
    elif abs(delta) > min_delta:
        explanation = f"Delta is {delta:+.1%} but intervals overlap (not significant)"
    else:
        explanation = f"Canary and control are equivalent (delta: {delta:+.1%} < {min_delta:.1%})"

    return (is_sig_worse, delta, explanation)


def should_rollback_canary(
    canary_successes: int,
    canary_trials: int,
    control_successes: int,
    control_trials: int,
    min_delta: float = 0.05,      # 5% minimum to trigger rollback
    min_duration_minutes: int = 10,  # Must be true for 10+ min
    confidence: float = 0.95
) -> Tuple[bool, str]:
    """
    Determine if canary should be rolled back

    Safety criteria (ALL must be true):
    - Statistical significance (p<0.05)
    - Delta magnitude > min_delta (5%)
    - Sufficient sample sizes (10+ each)

    Args:
        canary_successes: Canary successes
        canary_trials: Canary trials
        control_successes: Control successes
        control_trials: Control trials
        min_delta: Minimum delta to care about (default: 5%)
        min_duration_minutes: How long condition must persist
        confidence: Confidence level

    Returns:
        (should_rollback, reason)
    """
    # Check sample sizes
    if canary_trials < 20 or control_trials < 20:
        return (False, f"Insufficient data: canary={canary_trials}, control={control_trials} (need 20+ each)")

    # Check statistical significance
    is_worse, delta, explanation = is_significantly_different(
        canary_successes, canary_trials,
        control_successes, control_trials,
        min_delta=min_delta,
        confidence=confidence
    )

    if is_worse:
        canary_rate = canary_successes / canary_trials
        control_rate = control_successes / control_trials

        reason = (
            f"ROLLBACK RECOMMENDED: {explanation}\n"
            f"  Canary: {canary_successes}/{canary_trials} = {canary_rate:.1%}\n"
            f"  Control: {control_successes}/{control_trials} = {control_rate:.1%}\n"
            f"  Delta: {delta:+.1%} (threshold: >{min_delta:.1%})\n"
            f"  Confidence: {confidence:.0%}"
        )
        return (True, reason)
    else:
        return (False, explanation)


# Example usage in alerts or auto-rollback script:
if __name__ == "__main__":
    # Test case: Canary clearly worse
    print("Test 1: Canary significantly worse")
    should_rollback, reason = should_rollback_canary(
        canary_successes=85, canary_trials=100,
        control_successes=95, control_trials=100
    )
    print(f"Rollback: {should_rollback}")
    print(f"Reason: {reason}\n")

    # Test case: Not enough data
    print("Test 2: Insufficient sample size")
    should_rollback, reason = should_rollback_canary(
        canary_successes=8, canary_trials=10,
        control_successes=9, control_trials=10
    )
    print(f"Rollback: {should_rollback}")
    print(f"Reason: {reason}\n")

    # Test case: Difference not significant
    print("Test 3: Difference within noise")
    should_rollback, reason = should_rollback_canary(
        canary_successes=94, canary_trials=100,
        control_successes=96, control_trials=100
    )
    print(f"Rollback: {should_rollback}")
    print(f"Reason: {reason}\n")
