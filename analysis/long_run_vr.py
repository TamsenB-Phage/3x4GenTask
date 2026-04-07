import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
from scipy.signal import savgol_filter
from statsmodels.nonparametric.smoothers_lowess import lowess
from preprocessing import safe_savgol


def plot_longest_run_metric_interactive(summary_tsv, base_out_dir, metric="vertical_ratio"):
    if not Path(summary_tsv).exists():
        raise FileNotFoundError("Summary file not found.")

    # -----------------------------
    # Metric configuration
    # -----------------------------
    METRIC_CONFIG = {
        "vertical_ratio": {
            "col": "vertical_ratio",
            "label": "Vertical Ratio (%)",
            "title": "Running Efficiency Under Fatigue (Vertical Ratio)",
            "filter": lambda df: (df["vertical_ratio"] > 0) & (df["vertical_ratio"] < 20),
            "scale": 1.0,
            "reference_line": 7,
            "reference_label": "Elite VR (~7%)",
        },
        "cadence": {
            "col": "cadence",
            "label": "Cadence (spm)",
            "title": "Running Dynamics Under Fatigue (Cadence)",
            "filter": lambda df: (df["cadence"] > 60) & (df["cadence"] < 120),  # half cadence
            "scale": 2.0,  # convert to full cadence
            "reference_line": 170,
            "reference_label": "Typical endurance cadence (~170 spm)",
        },
    }

    if metric not in METRIC_CONFIG:
        raise ValueError(f"Unsupported metric: {metric}")

    cfg = METRIC_CONFIG[metric]
    col = cfg["col"]
    scale = cfg.get("scale", 1.0)

    # -----------------------------
    # Load summary
    # -----------------------------
    summary_df = pd.read_csv(summary_tsv, sep="\t")
    summary_df["date"] = pd.to_datetime(summary_df["date"])

    run_df = summary_df[
        summary_df["sport"].str.lower().str.contains("run", na=False)
    ].copy()

    run_df = run_df.dropna(subset=["distance"])

    if run_df.empty:
        raise ValueError("No running data found.")

    # -----------------------------
    # Longest run
    # -----------------------------
    longest_run = run_df.loc[run_df["distance"].idxmax()]
    longest_folder = longest_run["folder"]

    baseline_runs = run_df[run_df["date"] < longest_run["date"]]

    # -----------------------------
    # Power bins
    # -----------------------------
    bins = [0, 50_000, 100_000, 250_000, 500_000, 1_000_000, 2_000_000, 5_000_000]
    bin_labels = [(bins[i] + bins[i + 1]) / 2 for i in range(len(bins) - 1)]

    baseline_data = []

    # -----------------------------
    # Build baseline
    # -----------------------------
    for _, row in baseline_runs.iterrows():
        record_file = Path(base_out_dir) / str(row["folder"]) / "record.tsv"

        if not record_file.exists():
            continue

        df = pd.read_csv(record_file, sep="\t")

        if col not in df.columns or "accumulated_power" not in df.columns:
            continue

        df = df[cfg["filter"](df) & (df["accumulated_power"] > 0)].copy()

        if len(df) < 100:
            continue

        # ✅ APPLY SCALING
        df[col] = df[col] * scale

        df["power_bin"] = pd.cut(df["accumulated_power"], bins=bins, labels=bin_labels)

        baseline_data.append(df[["power_bin", col]])

    # ✅ SAFE fallback (no crash)
    if not baseline_data:
        print(f"No baseline data available for metric: {metric}")
        return go.Figure()

    baseline_df = pd.concat(baseline_data)

    # -----------------------------
    # Percentiles
    # -----------------------------
    stats = baseline_df.groupby("power_bin", observed=False)[col].agg(
        median="median",
        p5=lambda x: np.percentile(x, 5),
        p95=lambda x: np.percentile(x, 95),
    ).reset_index()

    stats["power_mid"] = stats["power_bin"].astype(float)

    stats["median_smooth"] = safe_savgol(stats["median"].values, 7, 2)
    stats["p5_smooth"] = safe_savgol(stats["p5"].values, 7, 2)
    stats["p95_smooth"] = safe_savgol(stats["p95"].values, 7, 2)

    # -----------------------------
    # Longest run
    # -----------------------------
    longest_file = Path(base_out_dir) / str(longest_folder) / "record.tsv"

    df_long = pd.read_csv(longest_file, sep="\t")

    df_long = df_long[cfg["filter"](df_long) & (df_long["accumulated_power"] > 0)].copy()

    if df_long.empty:
        print(f"No valid long-run data for metric: {metric}")
        return go.Figure()

    # ✅ APPLY SCALING
    df_long[col] = df_long[col] * scale

    df_long["smooth"] = safe_savgol(df_long[col].values, 101, 3)

    # -----------------------------
    # LOWESS trend
    # -----------------------------
    x = df_long["accumulated_power"].values
    y = df_long["smooth"].values

    mask = ~np.isnan(x) & ~np.isnan(y)

    if mask.sum() > 10:
        lowess_result = lowess(
            y[mask],
            x[mask],
            frac=0.08,
            return_sorted=False
        )

        trend = np.full_like(y, np.nan)
        trend[mask] = lowess_result
    else:
        trend = y  # fallback

    df_long["trend"] = trend

    # -----------------------------
    # Plot
    # -----------------------------
    fig = go.Figure()

    # Band
    fig.add_trace(go.Scatter(
        x=stats["power_mid"],
        y=stats["p95_smooth"],
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip",
    ))

    fig.add_trace(go.Scatter(
        x=stats["power_mid"],
        y=stats["p5_smooth"],
        fill="tonexty",
        name="Baseline (5–95 percentile)",
        line=dict(width=0),
        fillcolor="rgba(0, 150, 255, 0.2)",
    ))

    # Median
    fig.add_trace(go.Scatter(
        x=stats["power_mid"],
        y=stats["median_smooth"],
        name="Baseline median",
        line=dict(color="blue", width=3),
    ))

    # Long run
    fig.add_trace(go.Scatter(
        x=df_long["accumulated_power"],
        y=df_long["smooth"],
        name=f"Longest run ({longest_run['distance']:.1f} km)",
        line=dict(color="magenta", width=2),
    ))

    # Trend
    fig.add_trace(go.Scatter(
        x=df_long["accumulated_power"],
        y=df_long["trend"],
        name="Trend",
        line=dict(color="black", dash="dash", width=2),
    ))

    # Reference
    if cfg["reference_line"] is not None:
        fig.add_hline(
            y=cfg["reference_line"],
            line_dash="dash",
            line_color="gray",
            annotation_text=cfg["reference_label"],
        )

    # Layout
    fig.update_layout(
        title=cfg["title"],
        height=600,
        template="plotly_white",
        legend=dict(orientation="h"),
    )

    fig.update_xaxes(title="Accumulated Power (Joules)")
    fig.update_yaxes(title=cfg["label"])

    return fig
