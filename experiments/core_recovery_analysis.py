import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.lines import Line2D

from scipy.signal import savgol_filter

from preprocessing.utils import get_power_column


# --------------------------------------------------
# Extraction: Global Pause Detection
# --------------------------------------------------
def analyze_global_pauses_capped(
    summary_df,
    base_dir,
    min_work_joules=50000,
    speed_threshold=0.3
):
    """
    Extracts pause segments across all activities and saves
    capped (60s) recovery snapshots.

    Returns:
        pause_summary (pd.DataFrame)
        pause_export_dir (Path)
    """
    base_path = Path(base_dir)
    pause_export_dir = base_path / "global_pauses_capped"
    pause_export_dir.mkdir(exist_ok=True)

    all_pauses = []

    for _, row in summary_df.iterrows():
        folder = str(row["folder"])
        record_path = base_path / folder / "record.tsv"

        if not record_path.exists():
            continue

        df = pd.read_csv(record_path, sep="\t")

        # --- Robust column handling ---
        if "heart_rate" not in df.columns:
            continue

        try:
            power_col = get_power_column(df)
        except ValueError:
            continue

        speed_col = "enhanced_speed" if "enhanced_speed" in df.columns else "speed"
        if speed_col not in df.columns:
            continue

        # --- Detect pauses ---
        df["is_paused"] = df[speed_col] < speed_threshold
        df["pause_group"] = (df["is_paused"] != df["is_paused"].shift()).cumsum()

        for p_id, pause_data in df[df["is_paused"]].groupby("pause_group"):
            if len(pause_data) < 10:
                continue

            start_power = pause_data[power_col].iloc[0]

            if pd.isna(start_power) or start_power < min_work_joules:
                continue

            # --- Trim to 60s ---
            pause_60 = pause_data.head(60).copy()

            file_name = f"pause_{folder}_{p_id}.tsv"
            pause_60.to_csv(pause_export_dir / file_name, sep="\t", index=False)

            all_pauses.append({
                "folder": folder,
                "pause_file": file_name,
                "power_at_start": start_power,
                "duration": len(pause_60),
                "hr_drop_60s": (
                    pause_60["heart_rate"].iloc[0]
                    - pause_60["heart_rate"].iloc[-1]
                )
            })

    return pd.DataFrame(all_pauses), pause_export_dir


# --------------------------------------------------
# Plot 1: Savitzky-Golay Recovery (Baseline)
# --------------------------------------------------
def plot_global_recovery_savgol(
    pause_summary,
    pause_dir,
    window_len=11,
    poly_order=2
):
    if pause_summary.empty:
        print("No pauses to plot.")
        return

    fig, ax = plt.subplots(figsize=(12, 8))  # ✅ explicit axes

    norm = plt.Normalize(
        pause_summary["power_at_start"].min(),
        pause_summary["power_at_start"].max()
    )
    colormap = cm.plasma

    all_series = []

    for _, row in pause_summary.iterrows():
        df = pd.read_csv(pause_dir / row["pause_file"], sep="\t")

        hr = df["heart_rate"].values

        if len(hr) > window_len:
            hr_smooth = savgol_filter(hr, window_len, poly_order)
        else:
            hr_smooth = hr

        x = np.arange(len(hr_smooth))
        color = colormap(norm(row["power_at_start"]))

        ax.plot(x, hr_smooth, color=color, alpha=0.35, linewidth=1.2)

        if len(hr_smooth) == 60:
            all_series.append(hr_smooth)

    # --- Global average ---
    if all_series:
        avg = np.mean(all_series, axis=0)
        ax.plot(
            np.arange(60),
            avg,
            color="black",
            linestyle="--",
            linewidth=3,
            label="Global Average"
        )

    # ✅ Proper colorbar attachment
    sm = cm.ScalarMappable(norm=norm, cmap=colormap)
    sm.set_array([])  # required for matplotlib
    fig.colorbar(sm, ax=ax, label="Accumulated Power (J)")

    ax.set_title("Heart Rate Recovery (Savitzky-Golay Smoothed)")
    ax.set_xlabel("Seconds")
    ax.set_ylabel("Heart Rate (bpm)")
    ax.legend()
    ax.grid(alpha=0.1)

    plt.show()


# --------------------------------------------------
# Plot 2: Universal Stitched Recovery
# --------------------------------------------------
def plot_universal_stitched_recovery(
    pause_summary,
    pause_dir,
    work_range=(50000, 4000000)
):
    """
    Creates a stitched universal recovery curve using gap-bridging.
    """
    min_work, max_work = work_range

    pauses = []

    for _, row in pause_summary.iterrows():
        if not (min_work <= row["power_at_start"] <= max_work):
            continue

        df = pd.read_csv(pause_dir / row["pause_file"], sep="\t")

        pauses.append({
            "hr_series": df["heart_rate"].head(60).values,
            "power": row["power_at_start"]
        })

    if not pauses:
        print("No pauses in selected work range.")
        return

    pauses.sort(key=lambda x: x["hr_series"][0], reverse=True)

    # ✅ Create explicit axes
    fig, ax = plt.subplots(figsize=(12, 8))

    norm = plt.Normalize(min_work, max_work)
    colormap = cm.plasma

    hr_to_time = {}
    FALLBACK_DECAY = 1.0

    for i, pause in enumerate(pauses):
        hr = pause["hr_series"]

        hr_smooth = (
            savgol_filter(hr, 11, 2) if len(hr) > 11 else hr
        )

        start_hr = int(hr_smooth[0])

        if i == 0:
            offset = 0
        else:
            if start_hr in hr_to_time:
                offset = hr_to_time[start_hr]
            else:
                existing = np.array(list(hr_to_time.keys()))
                higher = existing[existing > start_hr]

                if len(higher) > 0:
                    anchor = higher.min()
                    offset = hr_to_time[anchor] + (anchor - start_hr) / FALLBACK_DECAY
                else:
                    offset = 0

        x = np.arange(len(hr_smooth)) + offset

        ax.plot(
            x,
            hr_smooth,
            color=colormap(norm(pause["power"])),
            alpha=0.3
        )

        # Update HR → synthetic time map
        for t, h in enumerate(hr_smooth):
            synth_t = t + offset
            h_int = int(h)

            if h_int not in hr_to_time or synth_t < hr_to_time[h_int]:
                hr_to_time[h_int] = synth_t

    # ✅ Proper colorbar
    sm = cm.ScalarMappable(norm=norm, cmap=colormap)
    sm.set_array([])
    fig.colorbar(sm, ax=ax, label="Accumulated Power (J)")

    ax.set_title("Universal Stitched Recovery Curve")
    ax.set_xlabel("Synthetic Seconds")
    ax.set_ylabel("Heart Rate (bpm)")
    ax.grid(alpha=0.15)

    plt.show()


# --------------------------------------------------
# Plot 3: Comrades 3-Phase Analysis
# --------------------------------------------------
def plot_comrades_three_phase(
    pause_summary,
    pause_dir,
    comrades_date_str,
    work_range=(50000, 4000000)
):
    """
    Plots recovery curves split into:
    - Pre-Comrades
    - Race Day
    - Post-Comrades
    """
    comrades_dt = pd.to_datetime(comrades_date_str).tz_localize("UTC")
    race_day = comrades_dt.date()

    min_work, max_work = work_range

    pauses = []

    for _, row in pause_summary.iterrows():
        if not (min_work <= row["power_at_start"] <= max_work):
            continue

        df = pd.read_csv(pause_dir / row["pause_file"], sep="\t")

        ts = pd.to_datetime(df["timestamp"].iloc[0])

        if ts.date() == race_day:
            phase = "Race"
        elif ts > comrades_dt:
            phase = "Post"
        else:
            phase = "Pre"

        pauses.append({
            "hr_series": df["heart_rate"].head(60).values,
            "power": row["power_at_start"],
            "phase": phase
        })

    if not pauses:
        return

    pauses.sort(key=lambda x: x["hr_series"][0], reverse=True)

    colors = {
        "Pre": "#00CED1",   # Cyan
        "Race": "#FF00FF",  # Magenta
        "Post": "#FF8C00"   # Orange
    }

    plt.figure(figsize=(14, 8))

    hr_to_time = {}
    FALLBACK_DECAY = 1.0

    for i, pause in enumerate(pauses):
        hr = pause["hr_series"]
        hr_smooth = savgol_filter(hr, 11, 2) if len(hr) > 11 else hr

        start_hr = int(hr_smooth[0])

        if i == 0:
            offset = 0
        else:
            if start_hr in hr_to_time:
                offset = hr_to_time[start_hr]
            else:
                existing = np.array(list(hr_to_time.keys()))
                higher = existing[existing > start_hr]

                if len(higher) > 0:
                    anchor = higher.min()
                    offset = hr_to_time[anchor] + (anchor - start_hr) / FALLBACK_DECAY
                else:
                    offset = 0

        x = np.arange(len(hr_smooth)) + offset

        plt.plot(
            x,
            hr_smooth,
            color=colors[pause["phase"]],
            alpha=0.35,
            linewidth=1.5
        )

        for t, h in enumerate(hr_smooth):
            synth_t = t + offset
            h_int = int(h)

            if h_int not in hr_to_time or synth_t < hr_to_time[h_int]:
                hr_to_time[h_int] = synth_t

    # -----------------------------
    # Legend (NEW)
    # -----------------------------
    legend_elements = [
        Line2D([0], [0], color=colors["Pre"], lw=3, label="Pre-Comrades (Training)"),
        Line2D([0], [0], color=colors["Race"], lw=3, label="Race Day"),
        Line2D([0], [0], color=colors["Post"], lw=3, label="Post-Comrades (Recovery)")
    ]

    plt.legend(
        handles=legend_elements,
        loc="upper right",
        frameon=True
    )

    # -----------------------------
    # Labels & layout
    # -----------------------------
    plt.title("Comrades 3-Phase Recovery Analysis")
    plt.xlabel("Synthetic Seconds")
    plt.ylabel("Heart Rate (bpm)")
    plt.grid(alpha=0.15)

    plt.show()