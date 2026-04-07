import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.signal import savgol_filter
from statsmodels.nonparametric.smoothers_lowess import lowess
from preprocessing import safe_savgol


def compute_lowess_trend(x, y, frac=0.08):
    mask = ~np.isnan(x) & ~np.isnan(y)

    if mask.sum() < 10:
        return y

    trend_vals = lowess(y[mask], x[mask], frac=frac, return_sorted=False)

    trend = np.full_like(y, np.nan)
    trend[mask] = trend_vals

    return trend


def zscore(x):
    return (x - np.nanmean(x)) / (np.nanstd(x) + 1e-6)


# -----------------------------
# Main plot
# -----------------------------
def plot_long_run_mechanics_hr(summary_tsv, base_out_dir):
    if not Path(summary_tsv).exists():
        raise FileNotFoundError("Summary file not found.")

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

    record_file = Path(base_out_dir) / str(longest_folder) / "record.tsv"

    if not record_file.exists():
        raise FileNotFoundError("Longest run record.tsv not found.")

    df = pd.read_csv(record_file, sep="\t")

    # -----------------------------
    # Required columns
    # -----------------------------
    required = [
        "accumulated_power",
        "vertical_ratio",
        "cadence",
        "heart_rate",
        "enhanced_speed",
        "enhanced_altitude",
    ]

    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    # -----------------------------
    # Clean data
    # -----------------------------
    df = df[
        (df["accumulated_power"] > 0) &
        (df["vertical_ratio"] > 0) & (df["vertical_ratio"] < 20) &
        (df["cadence"] > 60) & (df["cadence"] < 120) &
        (df["heart_rate"] > 60) &
        (df["enhanced_speed"] > 0)
    ].copy()

    if df.empty:
        raise ValueError("No valid long run data after filtering.")

    # -----------------------------
    # Unit conversions
    # -----------------------------
    df["cadence"] = df["cadence"] * 2.0
    df["speed_kmh"] = df["enhanced_speed"] * 3.6

    # -----------------------------
    # Smooth signals
    # -----------------------------
    df["vr_smooth"] = safe_savgol(df["vertical_ratio"], 101, 3)
    df["cad_smooth"] = safe_savgol(df["cadence"], 101, 3)
    df["hr_smooth"] = safe_savgol(df["heart_rate"], 101, 3)
    df["speed_smooth"] = safe_savgol(df["speed_kmh"], 101, 3)
    df["alt_smooth"] = safe_savgol(df["enhanced_altitude"], 101, 3)

    x = df["accumulated_power"].values

    # -----------------------------
    # Trends
    # -----------------------------
    df["vr_trend"] = compute_lowess_trend(x, df["vr_smooth"])
    df["cad_trend"] = compute_lowess_trend(x, df["cad_smooth"])
    df["hr_trend"] = compute_lowess_trend(x, df["hr_smooth"])
    df["speed_trend"] = compute_lowess_trend(x, df["speed_smooth"])

    # -----------------------------
    # Normalize altitude (visual only)
    # -----------------------------
    alt = df["alt_smooth"].values

    alt_norm = (alt - np.nanmin(alt)) / (np.nanmax(alt) - np.nanmin(alt) + 1e-6)

    speed_max = np.nanmax(df["speed_trend"])

    # scale so it's visible but not dominant
    df["alt_plot"] = alt_norm * speed_max * 1.0

    # -----------------------------
    # Breakdown score (mechanical only)
    # -----------------------------
    vr_z = zscore(df["vr_trend"])
    cad_z = zscore(df["cad_trend"])

    df["breakdown_score"] = vr_z - cad_z
    df["breakdown_score_smooth"] = safe_savgol(df["breakdown_score"], 151, 3)

    df["breakdown_flag"] = df["breakdown_score_smooth"] > 1.0

    # Detect zones
    zones = []
    in_zone = False
    start_idx = None

    for i, flag in enumerate(df["breakdown_flag"]):
        if flag and not in_zone:
            in_zone = True
            start_idx = i
        elif not flag and in_zone:
            zones.append((start_idx, i))
            in_zone = False

    if in_zone:
        zones.append((start_idx, len(df) - 1))

    zones = [(s, e) for s, e in zones if (e - s) > 200]

    # -----------------------------
    # Plot
    # -----------------------------
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.6, 0.4],
        specs=[[{"secondary_y": True}], [{"secondary_y": True}]],
    )

    # -----------------------------
    # TOP: Mechanics
    # -----------------------------
    fig.add_trace(
        go.Scatter(x=x, y=df["vr_trend"], name="VR Trend", line=dict(color="blue", width=3)),
        row=1, col=1, secondary_y=False
    )

    fig.add_trace(
        go.Scatter(x=x, y=df["cad_trend"], name="Cadence Trend", line=dict(color="magenta", width=3)),
        row=1, col=1, secondary_y=True
    )

    # -----------------------------
    # BOTTOM: Elevation (background area)
    # -----------------------------
    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["alt_plot"],
            name="Elevation profile",
            fill="tozeroy",
            line=dict(width=0),
            fillcolor="rgba(160,160,160,0.4)",
            hoverinfo="skip",
        ),
        row=2,
        col=1,
        secondary_y=True,
    )

    # -----------------------------
    # HR
    # -----------------------------
    fig.add_trace(
        go.Scatter(x=x, y=df["hr_smooth"], name="HR (smoothed)", line=dict(color="orange", width=2)),
        row=2, col=1, secondary_y=False
    )

    fig.add_trace(
        go.Scatter(x=x, y=df["hr_trend"], name="HR Trend", line=dict(color="red", dash="dash", width=3)),
        row=2, col=1, secondary_y=False
    )

    # -----------------------------
    # Speed trend
    # -----------------------------
    fig.add_trace(
        go.Scatter(
            x=x,
            y=df["speed_trend"],
            name="Speed Trend (km/h)",
            line=dict(color="rgba(120,120,120,0.7)", dash="dash", width=2),
        ),
        row=2,
        col=1,
        secondary_y=True,
    )

    # -----------------------------
    # Breakdown zones
    # -----------------------------
    for start, end in zones:
        fig.add_vrect(
            x0=df["accumulated_power"].iloc[start],
            x1=df["accumulated_power"].iloc[end],
            fillcolor="red",
            opacity=0.15,
            line_width=0,
            annotation_text="Breakdown",
            annotation_position="top left",
        )

    # -----------------------------
    # Layout
    # -----------------------------
    fig.update_layout(
        title=f"Longest Run Mechanics, Physiology & Terrain ({longest_run['distance']:.1f} km)",
        height=800,
        template="plotly_white",
        legend=dict(orientation="h"),
    )

    fig.update_xaxes(title="Accumulated Power (Joules)")

    fig.update_yaxes(title_text="Vertical Ratio (%)", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Cadence (spm)", row=1, col=1, secondary_y=True)

    fig.update_yaxes(title_text="Heart Rate (bpm)", row=2, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Speed (km/h)", row=2, col=1, secondary_y=True)

    return fig