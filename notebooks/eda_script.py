"""
EDA Script for ESA Spacecraft Anomaly Detection Datasets
=========================================================
Analyzes: anomaly_types.csv, channels.csv, labels.csv, telecommands.csv
Outputs: summary statistics, distributions, and cross-table insights.
"""

import pandas as pd
import json
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "esa"

# ── Load all CSVs ───────────────────────────────────────────────────────────
anomaly_types = pd.read_csv(DATA_DIR / "anomaly_types.csv")
channels = pd.read_csv(DATA_DIR / "channels.csv")
labels = pd.read_csv(DATA_DIR / "labels.csv")
telecommands = pd.read_csv(DATA_DIR / "telecommands.csv")

# Parse timestamps in labels
labels["StartTime"] = pd.to_datetime(labels["StartTime"])
labels["EndTime"] = pd.to_datetime(labels["EndTime"])
labels["Duration"] = labels["EndTime"] - labels["StartTime"]
labels["DurationHours"] = labels["Duration"].dt.total_seconds() / 3600

print("=" * 80)
print("  ESA SPACECRAFT ANOMALY DETECTION — EXPLORATORY DATA ANALYSIS")
print("=" * 80)

# ============================================================================
# 1. ANOMALY_TYPES.CSV
# ============================================================================
print("\n" + "━" * 80)
print("  1. ANOMALY_TYPES.CSV")
print("━" * 80)
print(f"\nShape: {anomaly_types.shape}")
print(f"Columns: {list(anomaly_types.columns)}")
print(f"\nDtypes:\n{anomaly_types.dtypes}")
print(f"\nNull counts:\n{anomaly_types.isnull().sum()}")
print(f"\nFirst 5 rows:\n{anomaly_types.head()}")

print(f"\n--- Unique value counts per column ---")
for col in anomaly_types.columns:
    print(f"  {col}: {anomaly_types[col].nunique()} unique")

print(f"\n--- Category distribution ---")
print(anomaly_types["Category"].value_counts())

print(f"\n--- Class distribution (top 10) ---")
print(anomaly_types["Class"].value_counts().head(10))

print(f"\n--- Subclass distribution ---")
print(anomaly_types["Subclass"].value_counts())

print(f"\n--- Dimensionality distribution ---")
print(anomaly_types["Dimensionality"].value_counts())

print(f"\n--- Locality distribution ---")
print(anomaly_types["Locality"].value_counts())

print(f"\n--- Length distribution ---")
print(anomaly_types["Length"].value_counts())

print(f"\n--- Category × Dimensionality crosstab ---")
print(pd.crosstab(anomaly_types["Category"], anomaly_types["Dimensionality"], margins=True))

print(f"\n--- Category × Locality crosstab ---")
print(pd.crosstab(anomaly_types["Category"], anomaly_types["Locality"], margins=True))

print(f"\n--- Category × Length crosstab ---")
print(pd.crosstab(anomaly_types["Category"], anomaly_types["Length"], margins=True))

# Which classes are purely Anomaly vs Rare Event vs mixed?
class_cats = anomaly_types.groupby("Class")["Category"].apply(set).reset_index()
class_cats.columns = ["Class", "Categories"]
print(f"\n--- Classes with mixed categories ---")
mixed = class_cats[class_cats["Categories"].apply(len) > 1]
if len(mixed) > 0:
    print(mixed)
else:
    print("  No classes have mixed categories.")

pure = class_cats[class_cats["Categories"].apply(len) == 1]
pure["Category"] = pure["Categories"].apply(lambda x: list(x)[0])
print(f"\n--- Pure class → category mapping ---")
print(pure[["Class", "Category"]].to_string(index=False))

# ============================================================================
# 2. CHANNELS.CSV
# ============================================================================
print("\n" + "━" * 80)
print("  2. CHANNELS.CSV")
print("━" * 80)
print(f"\nShape: {channels.shape}")
print(f"Columns: {list(channels.columns)}")
print(f"\nDtypes:\n{channels.dtypes}")
print(f"\nNull counts:\n{channels.isnull().sum()}")
print(f"\nFirst 5 rows:\n{channels.head()}")

print(f"\n--- Unique value counts per column ---")
for col in channels.columns:
    print(f"  {col}: {channels[col].nunique()} unique")

print(f"\n--- Subsystem distribution ---")
print(channels["Subsystem"].value_counts())

print(f"\n--- Physical Unit distribution ---")
print(channels["Physical Unit"].value_counts())

print(f"\n--- Group distribution ---")
print(channels["Group"].value_counts().sort_index())

print(f"\n--- Target distribution ---")
print(channels["Target"].value_counts())

print(f"\n--- Subsystem × Target crosstab ---")
print(pd.crosstab(channels["Subsystem"], channels["Target"], margins=True))

print(f"\n--- Subsystem × Physical Unit crosstab ---")
print(pd.crosstab(channels["Subsystem"], channels["Physical Unit"], margins=True))

# Channels per group
print(f"\n--- Channels per Group ---")
print(channels.groupby("Group")["Channel"].apply(list).to_string())

# ============================================================================
# 3. LABELS.CSV
# ============================================================================
print("\n" + "━" * 80)
print("  3. LABELS.CSV")
print("━" * 80)
print(f"\nShape: {labels.shape}")
print(f"Columns: {list(labels.columns)}")
print(f"\nDtypes:\n{labels.dtypes}")
print(f"\nNull counts:\n{labels.isnull().sum()}")
print(f"\nFirst 5 rows:\n{labels.head()}")

print(f"\n--- Unique value counts per column ---")
for col in ["ID", "Channel"]:
    print(f"  {col}: {labels[col].nunique()} unique")

print(f"\n--- Anomaly ID counts (top 15) — how many channel-label rows per anomaly ---")
id_counts = labels["ID"].value_counts()
print(id_counts.head(15))
print(f"\n  Mean channels per anomaly: {id_counts.mean():.1f}")
print(f"  Median channels per anomaly: {id_counts.median():.1f}")
print(f"  Min: {id_counts.min()}, Max: {id_counts.max()}")

print(f"\n--- Channel involvement frequency (top 15) — how often is each channel flagged ---")
ch_counts = labels["Channel"].value_counts()
print(ch_counts.head(15))
print(f"\n  Mean anomalies per channel: {ch_counts.mean():.1f}")
print(f"  Channels never flagged: {set(channels['Channel']) - set(labels['Channel'])}")

print(f"\n--- Temporal coverage ---")
print(f"  Earliest StartTime: {labels['StartTime'].min()}")
print(f"  Latest EndTime:     {labels['EndTime'].max()}")
print(f"  Time span:          {labels['EndTime'].max() - labels['StartTime'].min()}")

print(f"\n--- Duration statistics (hours) ---")
print(labels["DurationHours"].describe())

# Zero or negative durations
zero_dur = labels[labels["DurationHours"] <= 0]
print(f"\n  Rows with zero/negative duration: {len(zero_dur)}")
if len(zero_dur) > 0:
    print(zero_dur[["ID", "Channel", "StartTime", "EndTime"]].head(10))

# Duration by anomaly (aggregate per ID)
anom_dur = labels.groupby("ID").agg(
    n_channels=("Channel", "nunique"),
    min_start=("StartTime", "min"),
    max_end=("EndTime", "max"),
    mean_duration_h=("DurationHours", "mean"),
    max_duration_h=("DurationHours", "max"),
    n_label_rows=("Channel", "count"),
).reset_index()
anom_dur["overall_span_h"] = (anom_dur["max_end"] - anom_dur["min_start"]).dt.total_seconds() / 3600

print(f"\n--- Per-anomaly summary (top 10 by span) ---")
print(anom_dur.sort_values("overall_span_h", ascending=False).head(10).to_string(index=False))

print(f"\n--- Per-anomaly summary statistics ---")
print(anom_dur[["n_channels", "n_label_rows", "mean_duration_h", "overall_span_h"]].describe())

# Temporal distribution — year
labels["Year"] = labels["StartTime"].dt.year
print(f"\n--- Anomalies per year (by label rows) ---")
print(labels["Year"].value_counts().sort_index())

# Unique anomalies per year
year_anom = labels.groupby("Year")["ID"].nunique()
print(f"\n--- Unique anomaly IDs per year ---")
print(year_anom.sort_index())

# ============================================================================
# 4. TELECOMMANDS.CSV
# ============================================================================
print("\n" + "━" * 80)
print("  4. TELECOMMANDS.CSV")
print("━" * 80)
print(f"\nShape: {telecommands.shape}")
print(f"Columns: {list(telecommands.columns)}")
print(f"\nDtypes:\n{telecommands.dtypes}")
print(f"\nNull counts:\n{telecommands.isnull().sum()}")
print(f"\nFirst 5 rows:\n{telecommands.head()}")

print(f"\n--- Priority distribution ---")
print(telecommands["Priority"].value_counts().sort_index())

pct = telecommands["Priority"].value_counts(normalize=True).sort_index() * 100
print(f"\n--- Priority distribution (%) ---")
for p, v in pct.items():
    print(f"  Priority {p}: {v:.1f}%")

# ============================================================================
# 5. CROSS-TABLE ANALYSIS: labels ↔ anomaly_types
# ============================================================================
print("\n" + "━" * 80)
print("  5. CROSS-TABLE: LABELS ↔ ANOMALY TYPES")
print("━" * 80)

# Merge labels with anomaly_types on ID
labels_enriched = labels.merge(anomaly_types, on="ID", how="left")

print(f"\n--- Label rows per Category ---")
print(labels_enriched["Category"].value_counts())

print(f"\n--- Label rows per Class (top 10) ---")
print(labels_enriched["Class"].value_counts().head(10))

print(f"\n--- Mean duration (hours) per Category ---")
print(labels_enriched.groupby("Category")["DurationHours"].mean())

print(f"\n--- Mean duration (hours) per Dimensionality ---")
dim_dur = labels_enriched.groupby("Dimensionality")["DurationHours"].agg(["mean", "median", "count"])
print(dim_dur)

print(f"\n--- Mean channels-per-anomaly by Category ---")
ch_per_anom = labels_enriched.groupby(["ID", "Category"])["Channel"].nunique().reset_index()
print(ch_per_anom.groupby("Category")["Channel"].mean())

# ============================================================================
# 6. CROSS-TABLE: labels ↔ channels
# ============================================================================
print("\n" + "━" * 80)
print("  6. CROSS-TABLE: LABELS ↔ CHANNELS")
print("━" * 80)

labels_ch = labels.merge(channels, on="Channel", how="left")

print(f"\n--- Label rows per Subsystem ---")
print(labels_ch["Subsystem"].value_counts())

print(f"\n--- Label rows per Physical Unit ---")
print(labels_ch["Physical Unit"].value_counts())

print(f"\n--- Label rows: Target YES vs NO ---")
print(labels_ch["Target"].value_counts())

print(f"\n--- Mean duration by Subsystem ---")
print(labels_ch.groupby("Subsystem")["DurationHours"].agg(["mean", "median", "count"]))

print(f"\n--- Mean duration by Target ---")
print(labels_ch.groupby("Target")["DurationHours"].agg(["mean", "median", "count"]))

# ============================================================================
# 7. DATA QUALITY & STRUCTURAL SUMMARY
# ============================================================================
print("\n" + "━" * 80)
print("  7. DATA QUALITY & STRUCTURAL SUMMARY")
print("━" * 80)

# Check which anomaly IDs in labels are not in anomaly_types and vice versa
label_ids = set(labels["ID"].unique())
atype_ids = set(anomaly_types["ID"].unique())
print(f"\n  Anomaly IDs in labels:        {len(label_ids)}")
print(f"  Anomaly IDs in anomaly_types: {len(atype_ids)}")
print(f"  IDs in labels but NOT in anomaly_types: {label_ids - atype_ids}")
print(f"  IDs in anomaly_types but NOT in labels: {atype_ids - label_ids}")

# Check which channels in labels are not in channels.csv
label_chs = set(labels["Channel"].unique())
ch_chs = set(channels["Channel"].unique())
print(f"\n  Channels in labels:       {len(label_chs)}")
print(f"  Channels in channels.csv: {len(ch_chs)}")
print(f"  In labels but NOT in channels.csv: {label_chs - ch_chs}")
print(f"  In channels.csv but NOT in labels: {ch_chs - label_chs}")

# Communication gaps (no dimensionality/locality/length)
comm_gaps = anomaly_types[anomaly_types["Category"] == "Communication Gap"]
print(f"\n  Communication Gap anomalies: {len(comm_gaps)}")
if len(comm_gaps) > 0:
    print(comm_gaps[["ID", "Class", "Category"]].to_string(index=False))

print("\n" + "=" * 80)
print("  EDA COMPLETE")
print("=" * 80)
