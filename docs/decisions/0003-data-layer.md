# ADR-0003: Data Layer Design — Windowed ESA Loading, diskcache, IsolationForest Baseline

**Date:** 2026-05-31
**Status:** Accepted
**Week:** W1

## Context

AMOA needs two data sources:

1. **Space-Track** — live TLE and CDM feeds via authenticated HTTP. Rate-limited
   (30 req/min, 300 req/hr). Auth cookie expires ~2 hours. Dev loop hits the same
   objects repeatedly.

2. **ESA Anomaly Benchmark** — Mission 1 telemetry for Health Guard evaluation.
   ~5.27 M rows per channel, 4 channels = ~12 GB total on disk. Each channel is
   a pandas pickle compressed inside a ZIP file.

Hardware constraint: 6 GB RAM Windows laptop. Cannot hold even one full channel
in memory alongside a running LangGraph + two LLM clients.

## Decision 1: Windowed ESA Loading

Load channels row-by-row in fixed-size windows (default 1 000 rows) rather than
reading full DataFrames into memory.

**Why:**
- Full channel load peaks at ~400 MB per pickle. Two channels + LangGraph +
  Gemini client = OOM on 6 GB with VS Code open.
- Window-level granularity matches how anomaly detection will work in production:
  Health Guard sees a rolling window, not the full mission timeline.
- Windowed loading keeps peak RAM under 80 MB per channel regardless of total
  dataset size.

**Trade-off accepted:** anomalies that straddle a window boundary are split
across two windows. Each window is labeled independently based on timestamp
overlap. A straddling anomaly gets label=1 in both windows, which slightly
inflates recall — acceptable for a baseline comparison.

**Alternative rejected:** downsample to every N-th row to reduce size. Rejected
because downsampling destroys high-frequency anomaly signatures (e.g. a 5-minute
spike would be invisible at 1-hour resolution).

## Decision 2: diskcache for Space-Track API Responses

Use `diskcache.Cache` to memoize Space-Track API responses (TLE, CDM) with a
2-hour TTL.

**Why:**
- Space-Track rate limits (30 req/min) are easy to hit during iterative dev.
  Every graph re-run re-fetches the same TLE for ISS.
- Auth cookie lifetime is ~2 hours; cache TTL matches this so stale entries
  never outlive a valid session.
- `diskcache` is zero-infrastructure: no Redis, no Docker, just a local
  directory. Stays within the 6 GB RAM / no-server constraint.
- Transparent: wrapping `fetch_tle()` and `fetch_cdms()` at the loader layer
  keeps the rest of the code unaware of caching.

**Trade-off accepted:** cache lives on disk, not in memory — slightly slower
than an in-process dict. Irrelevant at our call frequency (< 10 req/dev session).

**Alternative rejected:** `functools.lru_cache`. In-memory only, does not
survive process restart, and can't express per-entry TTL.

## Decision 3: IsolationForest as Anomaly Detection Baseline

Use scikit-learn `IsolationForest` as the baseline against which Health Guard
(Gemini 2.5 Flash) is evaluated.

**Why:**
- Unsupervised: no labeled training data required. IsolationForest fits on the
  same windows it predicts — mirrors the realistic deployment scenario where
  labeled anomalies are rare and arrive late.
- Fast: trains on 200 × 1 000-row windows in < 2 seconds on the laptop CPU.
  Low cost to re-run during development.
- Interpretable: anomaly score = average path length in isolation trees. Easy
  to explain in interviews without black-box hand-waving.
- Industry-standard baseline for multivariate time-series anomaly detection.

**Baseline results (W1):**

| Channel | Windows | Precision | Recall | F1    |
|---------|---------|-----------|--------|-------|
| 14      | 200     | 0.050     | 0.250  | 0.083 |
| 15      | 200     | 0.200     | 0.308  | 0.242 |

These scores set the floor Health Guard must exceed to justify LLM API cost.

**Gotcha discovered:** channels 10 and 11 carry zero anomaly labels in the ESA
benchmark. Running evaluation on them produces a degenerate all-zeros label
vector (F1=0 by construction). Evaluation restricted to channels 14 and 15.

**Second gotcha:** channel pickle indices are tz-naive; `labels.csv` timestamps
are tz-aware UTC. Comparison raises `TypeError` unless tz is stripped from label
timestamps before comparison. Fixed in `esa_loader._window_has_anomaly`.

**Alternative rejected:** LSTM autoencoder. Requires GPU or long CPU training
time; overkill for a W1 baseline. Deferred to W3 if IsolationForest proves
insufficient.

## Consequences

- `src/amoa/data/esa_loader.py` exposes `load_channel_window` and
  `load_windows_with_labels` as the only public API. Callers never read raw
  pickles directly.
- `src/amoa/baselines/isolation_forest.py` saves metrics to
  `src/amoa/eval/baseline_metrics.json` on every run — last run wins.
- diskcache directory is `.cache/spacetrack/` (git-ignored). Delete to force
  fresh API calls.
- 200 windows minimum required for meaningful ESA evaluation (first anomaly
  appears at window ~38 for channel 14).
