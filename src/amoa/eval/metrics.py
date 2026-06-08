"""
Statistical comparison utilities.
Paired bootstrap CI on F1 difference (Health Guard vs IsolationForest baseline).
"""
import numpy as np
from scipy import stats


def paired_bootstrap_ci(
    scores_a: list[float],
    scores_b: list[float],
    n_resamples: int = 9999,
    confidence_level: float = 0.95,
) -> dict:
    """
    Compute paired bootstrap confidence interval on the difference
    between two sets of per-window scores (method_a - method_b).

    Returns dict with: mean_diff, ci_low, ci_high, excludes_zero
    """
    diffs = np.array(scores_a) - np.array(scores_b)

    result = stats.bootstrap(
        (diffs,),
        np.mean,
        n_resamples=n_resamples,
        confidence_level=confidence_level,
        method="percentile",
    )

    ci_low, ci_high = result.confidence_interval
    mean_diff = float(np.mean(diffs))

    return {
        "mean_diff": round(mean_diff, 4),
        "ci_low": round(float(ci_low), 4),
        "ci_high": round(float(ci_high), 4),
        "confidence_level": confidence_level,
        "excludes_zero": not (ci_low <= 0 <= ci_high),
    }