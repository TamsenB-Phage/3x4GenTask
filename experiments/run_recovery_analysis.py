import pandas as pd
from pathlib import Path

from experiments.core_recovery_analysis import (
    analyze_global_pauses_capped,
    plot_global_recovery_savgol,
    plot_universal_stitched_recovery,
    plot_comrades_three_phase,
)


def run_recovery_analysis(
    summary_path: str,
    base_dir: str | None = None,
    comrades_date: str = "2025-06-08",
):
    """
    Runs the experimental recovery analysis pipeline.

    This pipeline focuses on three complementary views of recovery:

    1. Smoothed recovery curves (Savitzky-Golay)
       → Baseline recovery behaviour across all pauses

    2. Universal stitched recovery model
       → Approximate global heart rate decay across effort levels

    3. Comrades 3-phase comparison
       → Pre-race vs race-day vs post-race recovery dynamics

    Args:
        summary_path (str): Path to master workout summary TSV.
        base_dir (str | None): Directory containing processed activity folders.
                               If None, inferred from summary_path.
        comrades_date (str): Date of Comrades Marathon (YYYY-MM-DD).
    """

    print("\n=== Experimental Recovery Analysis ===")

    # -----------------------------
    # Resolve paths (CROSS-PLATFORM SAFE)
    # -----------------------------
    summary_path = Path(summary_path).resolve()

    if not summary_path.exists():
        raise FileNotFoundError(f"Summary file not found: {summary_path}")

    # Infer base_dir if not provided
    if base_dir is None:
        base_dir = summary_path.parent
    else:
        base_dir = Path(base_dir).resolve()

    print(f"Using summary file: {summary_path}")
    print(f"Using base directory: {base_dir}")

    # -----------------------------
    # Load summary
    # -----------------------------
    summary_df = pd.read_csv(summary_path, sep="\t")

    if summary_df.empty:
        print("Summary file is empty.")
        return

    # -----------------------------
    # Extract pauses
    # -----------------------------
    print("\n--- Extracting pauses ---")
    pause_df, pause_dir = analyze_global_pauses_capped(
        summary_df,
        base_dir,
        min_work_joules=50_000,
    )

    if pause_df.empty:
        print("No valid pauses found.")
        return

    print(f"Extracted {len(pause_df)} pauses.")
    print(f"Pause files saved to: {pause_dir}")

    # -----------------------------
    # 1. Smoothed recovery
    # -----------------------------
    print("\n--- Plot: Smoothed HR Recovery (Savgol) ---")
    plot_global_recovery_savgol(pause_df, pause_dir)

    # -----------------------------
    # 2. Universal stitched model
    # -----------------------------
    print("\n--- Plot: Universal Stitched Recovery ---")
    plot_universal_stitched_recovery(
        pause_df,
        pause_dir,
        work_range=(50_000, 4_000_000),
    )

    # -----------------------------
    # 3. Comrades phase comparison
    # -----------------------------
    print("\n--- Plot: Comrades 3-Phase Recovery ---")
    plot_comrades_three_phase(
        pause_df,
        pause_dir,
        comrades_date,
    )

    print("\n=== Recovery analysis complete ===")