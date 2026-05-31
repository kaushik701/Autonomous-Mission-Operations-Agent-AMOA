"""
ESA Anomaly Dataset loader — Mission 1 channels (10, 11, 14, 15).

Windowed: loads one channel pickle at a time (~50 MB RAM), slices by row.
Labels matched by timestamp overlap with anomaly time ranges.
"""
import zipfile
from pathlib import Path

import pandas as pd

ESA_DIR = Path("data/esa")
CHANNELS = [10, 11, 14, 15]


def load_labels() -> pd.DataFrame:
    """Load anomaly labels with parsed datetime columns."""
    df = pd.read_csv(ESA_DIR / "labels.csv")
    df["StartTime"] = pd.to_datetime(df["StartTime"])
    df["EndTime"] = pd.to_datetime(df["EndTime"])
    return df


def load_channel(channel: int) -> pd.DataFrame:
    """Load full channel pickle from its ZIP. Datetime index, one float32 column."""
    zip_path = ESA_DIR / f"channel_{channel}.zip"
    with zipfile.ZipFile(zip_path) as z:
        with z.open(f"channel_{channel}") as f:
            return pd.read_pickle(f)


def load_channel_window(
    channel: int,
    start_idx: int = 0,
    window_size: int = 1000,
) -> pd.DataFrame:
    """Load a contiguous window of rows from one channel by row index."""
    df = load_channel(channel)
    return df.iloc[start_idx: start_idx + window_size]


def _window_has_anomaly(
    window: pd.DataFrame,
    channel: int,
    labels: pd.DataFrame,
) -> int:
    """Return 1 if any timestamp in window falls within a labeled anomaly range."""
    channel_labels = labels[labels["Channel"] == f"channel_{channel}"]
    if channel_labels.empty:
        return 0
    ts = window.index
    for _, row in channel_labels.iterrows():
        start = row["StartTime"]
        end = row["EndTime"]
        # Channel pickles are tz-naive; labels CSV is tz-aware UTC. Normalize.
        if ts.tz is None and start.tzinfo is not None:
            start = start.tz_localize(None)
            end = end.tz_localize(None)
        if ((ts >= start) & (ts <= end)).any():
            return 1
    return 0


def load_windows_with_labels(
    channel: int,
    window_size: int = 1000,
    max_windows: int = 20,
) -> list[dict]:
    """Return windows of telemetry paired with anomaly labels.

    Each dict: {channel, start_idx, values: list[float], is_anomaly: 0|1}
    """
    labels = load_labels()
    df = load_channel(channel)
    windows = []
    for i in range(max_windows):
        start = i * window_size
        window = df.iloc[start: start + window_size]
        if window.empty:
            break
        is_anomaly = _window_has_anomaly(window, channel, labels)
        windows.append({
            "channel": channel,
            "start_idx": start,
            "values": window.iloc[:, 0].tolist(),
            "is_anomaly": is_anomaly,
        })
    return windows
