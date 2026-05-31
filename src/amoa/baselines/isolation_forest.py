"""
IsolationForest baseline for telemetry anomaly detection.
Trained and evaluated on ESA Mission 1 windowed data.
"""
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import f1_score, precision_score, recall_score

from amoa.data.esa_loader import load_windows_with_labels

METRICS_PATH = Path("src/amoa/eval/baseline_metrics.json")


def train_and_eval(
    channel: int,
    window_size: int = 1000,
    max_windows: int = 20,
    contamination: float = 0.1,
) -> dict:
    """
    Train IsolationForest and return evaluation metrics.
    Saves metrics to eval/baseline_metrics.json.
    """
    windows = load_windows_with_labels(channel, window_size, max_windows)
    if not windows:
        raise ValueError(f"No windows loaded for channel {channel}")

    X = np.array([np.array(w["values"]).flatten() for w in windows])
    y_true = np.array([w["is_anomaly"] for w in windows])

    model = IsolationForest(contamination=contamination, random_state=42)
    raw_preds = model.fit_predict(X)
    y_pred = (raw_preds == -1).astype(int)

    metrics = {
        "method": "isolation_forest",
        "channel": channel,
        "n_windows": len(windows),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 4),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
        "contamination": contamination,
    }

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_PATH.open("w") as f:
        json.dump(metrics, f, indent=2)

    return metrics


if __name__ == "__main__":
    import re
    import sys

    arg = sys.argv[1] if len(sys.argv) > 1 else "data/esa/channel_10.zip"
    match = re.search(r"channel_(\d+)", Path(arg).stem)
    if not match:
        print(f"ERROR: cannot parse channel number from {arg!r}", file=sys.stderr)
        print("Expected path like data/esa/channel_10.zip", file=sys.stderr)
        sys.exit(1)
    channel = int(match.group(1))
    metrics = train_and_eval(channel)
    print(json.dumps(metrics, indent=2))