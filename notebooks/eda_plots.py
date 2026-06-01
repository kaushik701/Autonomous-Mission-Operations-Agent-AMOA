"""
EDA Plots Generator for ESA Spacecraft Anomaly Detection Datasets
=================================================================
Loads: anomaly_types.csv, channels.csv, labels.csv, telecommands.csv
Generates: Six premium space-themed high-DPI exploratory visualizations.
Saves: PNG plots inside notebooks/plots/
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set paths
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "esa"
PLOTS_DIR = Path(__file__).resolve().parent / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Styling Constants (Premium Dark Space Theme) ─────────────────────────────
BG_COLOR = "#0B0F19"          # Very deep space navy
AXIS_BG_COLOR = "#111827"     # Dark card background
GRID_COLOR = "#1F2937"        # Subtle gridlines
TEXT_COLOR = "#E5E7EB"        # Cool grey text
ACCENT_BLUE = "#38BDF8"       # Electric Blue
ACCENT_PINK = "#F43F5E"       # Hot Pink
ACCENT_PURPLE = "#A855F7"     # Purple
ACCENT_GREEN = "#10B981"      # Emerald Green
ACCENT_ORANGE = "#F97316"     # Orange

PALETTE_CATEGORIES = {
    "Anomaly": ACCENT_PINK,
    "Rare Event": ACCENT_BLUE,
    "Communication Gap": ACCENT_GREEN
}
PALETTE_SUBSYSTEMS = [ACCENT_BLUE, ACCENT_PURPLE, ACCENT_ORANGE, ACCENT_GREEN, ACCENT_PINK, "#EAB308"]

# Configure Matplotlib styles
plt.rcParams.update({
    "figure.facecolor": BG_COLOR,
    "axes.facecolor": AXIS_BG_COLOR,
    "axes.edgecolor": GRID_COLOR,
    "axes.grid": True,
    "grid.color": GRID_COLOR,
    "grid.linestyle": "--",
    "grid.alpha": 0.5,
    "text.color": TEXT_COLOR,
    "axes.labelcolor": TEXT_COLOR,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "figure.titlesize": 16,
    "figure.titleweight": "bold"
})

def load_data():
    """Loads all CSV files and applies initial preprocessing."""
    print("Loading datasets...")
    anomaly_types = pd.read_csv(DATA_DIR / "anomaly_types.csv")
    channels = pd.read_csv(DATA_DIR / "channels.csv")
    labels = pd.read_csv(DATA_DIR / "labels.csv")
    telecommands = pd.read_csv(DATA_DIR / "telecommands.csv")
    
    # Parse timestamps
    labels["StartTime"] = pd.to_datetime(labels["StartTime"])
    labels["EndTime"] = pd.to_datetime(labels["EndTime"])
    labels["Duration"] = labels["EndTime"] - labels["StartTime"]
    labels["DurationHours"] = labels["Duration"].dt.total_seconds() / 3600.0
    
    if "Timestamp" in telecommands.columns:
        telecommands["Timestamp"] = pd.to_datetime(telecommands["Timestamp"])
        
    return anomaly_types, channels, labels, telecommands

def plot_anomaly_distribution(anomaly_types):
    """Plot 1: Anomaly Class and Category Distribution."""
    print("Generating Plot 1: Anomaly Distribution...")
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    
    # Sort and count
    class_counts = anomaly_types.groupby(["Class", "Category"]).size().reset_index(name="Count")
    class_counts = class_counts.sort_values(by="Count", ascending=True)
    
    sns.barplot(
        data=class_counts,
        y="Class",
        x="Count",
        hue="Category",
        palette=PALETTE_CATEGORIES,
        dodge=False,
        ax=ax,
        edgecolor=BG_COLOR,
        linewidth=1
    )
    
    ax.set_title("Spacecraft Anomaly Distribution by Class and Category", pad=15)
    ax.set_xlabel("Number of Occurrences", labelpad=10)
    ax.set_ylabel("Anomaly Class", labelpad=10)
    ax.legend(title="Category", facecolor=AXIS_BG_COLOR, edgecolor=GRID_COLOR, loc="lower right")
    
    # Add values on the bar edges
    for container in ax.containers:
        ax.bar_label(container, fmt="%d", padding=5, color=TEXT_COLOR, fontsize=9)
        
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "anomaly_distribution.png", facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    print("  Saved: anomaly_distribution.png")

def plot_anomaly_durations(labels, anomaly_types):
    """Plot 2: Anomaly Duration Distribution (Log Scale)."""
    print("Generating Plot 2: Anomaly Durations...")
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    
    # Merge label rows with categories
    merged = labels.merge(anomaly_types, on="ID", how="left")
    
    # We use a small epsilon to avoid log(0) issues for zero durations
    epsilon = 0.01
    merged["LogDurationHours"] = np.log10(merged["DurationHours"].clip(lower=epsilon))
    
    # Kernel Density Estimation with elegant fill
    for cat, color in PALETTE_CATEGORIES.items():
        subset = merged[merged["Category"] == cat]
        if len(subset) > 0:
            sns.kdeplot(
                data=subset,
                x="LogDurationHours",
                fill=True,
                color=color,
                label=cat,
                alpha=0.3,
                linewidth=2,
                ax=ax
            )
            
    ax.set_title("Distribution of Flagged Anomaly Durations (Log Scale)", pad=15)
    ax.set_xlabel("Duration in Hours (Log10 Scale)", labelpad=10)
    ax.set_ylabel("Density", labelpad=10)
    
    # Customize the X-axis labels to show actual hours instead of raw logs
    log_ticks = [-2, -1, 0, 1, 2, 3]
    hour_labels = ["0.01h", "0.1h", "1h", "10h", "100h", "1000h"]
    ax.set_xticks(log_ticks)
    ax.set_xticklabels(hour_labels)
    
    ax.legend(title="Category", facecolor=AXIS_BG_COLOR, edgecolor=GRID_COLOR)
    
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "anomaly_durations.png", facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    print("  Saved: anomaly_durations.png")

def plot_subsystem_vulnerability(labels, channels):
    """Plot 3: Subsystem Vulnerability Map."""
    print("Generating Plot 3: Subsystem Vulnerability...")
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    
    # Merge labels with channel subsystems
    merged = labels.merge(channels, on="Channel", how="left")
    
    # Calculate counts and durations per subsystem
    subsys_stats = merged.groupby("Subsystem").agg(
        Anomalies=("ID", "nunique"),
        TotalFlaggedChannels=("Channel", "count")
    ).reset_index()
    subsys_stats = subsys_stats.sort_values(by="TotalFlaggedChannels", ascending=False)
    
    # Horizontal bar plot
    sns.barplot(
        data=subsys_stats,
        y="Subsystem",
        x="TotalFlaggedChannels",
        palette=PALETTE_SUBSYSTEMS,
        ax=ax,
        edgecolor=BG_COLOR,
        linewidth=1
    )
    
    ax.set_title("Vulnerability Map: Flagged Channels by Spacecraft Subsystem", pad=15)
    ax.set_xlabel("Total Flagged Channel Instances", labelpad=10)
    ax.set_ylabel("Subsystem", labelpad=10)
    
    # Add labels on bars
    for container in ax.containers:
        ax.bar_label(container, fmt="%d", padding=5, color=TEXT_COLOR, fontsize=9)
        
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "subsystem_vulnerability.png", facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    print("  Saved: subsystem_vulnerability.png")

def plot_temporal_trends(labels):
    """Plot 4: Anomaly Occurrences Over Time (Timeline)."""
    print("Generating Plot 4: Temporal Trends...")
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    
    # Extract year-month for plotting
    labels_copy = labels.copy()
    labels_copy["YearMonth"] = labels_copy["StartTime"].dt.to_period("M")
    
    # Unique anomalies (by ID) per month
    monthly_trends = labels_copy.groupby("YearMonth").agg(
        UniqueAnomalies=("ID", "nunique"),
        ChannelFlaggedEvents=("Channel", "count")
    ).reset_index()
    
    # Convert Period to timestamp for plotting compatibility
    monthly_trends["PlotTime"] = monthly_trends["YearMonth"].dt.to_timestamp()
    
    # Area chart with gradient vibe
    ax.fill_between(
        monthly_trends["PlotTime"],
        monthly_trends["ChannelFlaggedEvents"],
        color=ACCENT_BLUE,
        alpha=0.15,
        label="Total Flagged Channels"
    )
    
    sns.lineplot(
        data=monthly_trends,
        x="PlotTime",
        y="ChannelFlaggedEvents",
        color=ACCENT_BLUE,
        linewidth=2.5,
        marker="o",
        markersize=6,
        label="Channel Flagged Instances",
        ax=ax
    )
    
    # Plot unique anomalies on secondary y-axis
    ax2 = ax.twinx()
    sns.lineplot(
        data=monthly_trends,
        x="PlotTime",
        y="UniqueAnomalies",
        color=ACCENT_PINK,
        linewidth=2,
        marker="s",
        markersize=6,
        label="Unique Anomaly Cases",
        ax=ax2
    )
    
    # Secondary Y style
    ax2.grid(False)
    ax2.set_ylabel("Unique Anomaly IDs", color=ACCENT_PINK, labelpad=10, fontweight="bold")
    ax2.tick_params(axis="y", labelcolor=ACCENT_PINK)
    
    ax.set_title("Timeline: Anomaly Flagging Activity Over Spacecraft Mission", pad=15)
    ax.set_xlabel("Time", labelpad=10)
    ax.set_ylabel("Flagged Channels Count", color=ACCENT_BLUE, labelpad=10, fontweight="bold")
    ax.tick_params(axis="y", labelcolor=ACCENT_BLUE)
    
    # Combine legends
    lines, labels_l = ax.get_legend_handles_labels()
    lines2, labels_r = ax2.get_legend_handles_labels()
    ax.get_legend().remove()
    ax2.legend(lines + lines2, labels_l + labels_r, loc="upper left", facecolor=AXIS_BG_COLOR, edgecolor=GRID_COLOR)
    
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "temporal_trends.png", facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    print("  Saved: temporal_trends.png")

def plot_telecommand_priorities(telecommands):
    """Plot 5: Telecommand Priority Breakdown (Donut Chart)."""
    print("Generating Plot 5: Telecommand Priorities...")
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    
    priority_counts = telecommands["Priority"].value_counts().sort_index()
    
    labels_list = [f"Priority {idx}" for idx in priority_counts.index]
    colors = [ACCENT_BLUE, ACCENT_PURPLE, ACCENT_ORANGE, ACCENT_PINK, ACCENT_GREEN][:len(priority_counts)]
    
    # Wedge custom styling
    wedges, texts, autotexts = ax.pie(
        priority_counts,
        labels=labels_list,
        colors=colors,
        autopct="%1.1f%%",
        startangle=140,
        pctdistance=0.80,
        textprops=dict(color=TEXT_COLOR, fontsize=10),
        wedgeprops=dict(width=0.4, edgecolor=BG_COLOR, linewidth=3)
    )
    
    # Make percentages bold
    for autotext in autotexts:
        autotext.set_fontweight("bold")
        autotext.set_color(TEXT_COLOR)
        
    ax.set_title("Telecommand Volume Breakdown by Priority Level", pad=20)
    
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "telecommand_priorities.png", facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    print("  Saved: telecommand_priorities.png")

def plot_anomaly_characteristics_heatmap(anomaly_types):
    """Plot 6: Cross-tab Heatmaps for Anomaly Characteristics."""
    print("Generating Plot 6: Characteristic Heatmaps...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)
    
    # 1. Category x Dimensionality
    crosstab_dim = pd.crosstab(anomaly_types["Category"], anomaly_types["Dimensionality"])
    sns.heatmap(
        crosstab_dim,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=True,
        ax=ax1,
        annot_kws={"size": 11, "weight": "bold"},
        edgecolor=GRID_COLOR,
        linewidths=1
    )
    ax1.set_title("Anomaly Category vs Dimensionality", pad=15)
    ax1.set_ylabel("Category", labelpad=10)
    ax1.set_xlabel("Dimensionality", labelpad=10)
    
    # 2. Category x Locality
    crosstab_loc = pd.crosstab(anomaly_types["Category"], anomaly_types["Locality"])
    sns.heatmap(
        crosstab_loc,
        annot=True,
        fmt="d",
        cmap="Purples",
        cbar=True,
        ax=ax2,
        annot_kws={"size": 11, "weight": "bold"},
        edgecolor=GRID_COLOR,
        linewidths=1
    )
    ax2.set_title("Anomaly Category vs Locality", pad=15)
    ax2.set_ylabel("")
    ax2.set_xlabel("Locality", labelpad=10)
    
    # Color bar styling
    for ax in [ax1, ax2]:
        cbar = ax.collections[0].colorbar
        cbar.ax.yaxis.set_tick_params(color=TEXT_COLOR)
        plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color=TEXT_COLOR)
        
    plt.suptitle("Spacecraft Anomaly Attribute Cross-Tabulation Analysis", y=0.98)
    plt.tight_layout()
    fig.savefig(PLOTS_DIR / "anomaly_characteristics_heatmap.png", facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    print("  Saved: anomaly_characteristics_heatmap.png")

def main():
    print("=" * 80)
    print("  ESA SPACECRAFT ANOMALY DETECTION — EXPLORATORY DATA VISUALIZATION")
    print("=" * 80)
    
    # Load
    anomaly_types, channels, labels, telecommands = load_data()
    
    # Plot
    plot_anomaly_distribution(anomaly_types)
    plot_anomaly_durations(labels, anomaly_types)
    plot_subsystem_vulnerability(labels, channels)
    plot_temporal_trends(labels)
    plot_telecommand_priorities(telecommands)
    plot_anomaly_characteristics_heatmap(anomaly_types)
    
    print("\n" + "=" * 80)
    print(f"  EDA PLOTS GENERATED SUCCESSFULLY! Saved in: {PLOTS_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    main()
