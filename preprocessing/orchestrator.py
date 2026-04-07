from pathlib import Path
from preprocessing.fit_to_tsv_folder import fit_to_tsv_folder
from preprocessing.workout_summary import summarize_from_tsvs, generate_route_report

REPO_DIR = Path(__file__).resolve().parents[1]   # repo/
PROJECT_ROOT = REPO_DIR.parent                  # folder containing repo/

DEFAULT_WORKOUTS_DIR = PROJECT_ROOT / "workouts"
DEFAULT_OUT_DIR = PROJECT_ROOT / "out"


def run_global_orchestration(
    workouts_dir: str | Path = None,
    out_dir: str | Path = None,
):
    """Coordinates the generic end-to-end data pipeline for Garmin activities.

    This pipeline:
        1. Decodes `.fit` files into structured TSV folders
        2. Builds a master training summary
        3. Performs spatial route matching

    Args:
        workouts_dir (str | Path, optional): Path to raw `.fit` files.
            Defaults to `<project_root>/workouts`.
        out_dir (str | Path, optional): Path for processed TSV outputs.
            Defaults to `<project_root>/out`.

    Returns:
        tuple:
            - pd.DataFrame: Summary of all activities
            - pd.DataFrame: Route matching report
    """

    # -----------------------------
    # Resolve paths safely
    # -----------------------------
    workouts_path = Path(workouts_dir) if workouts_dir else DEFAULT_WORKOUTS_DIR
    out_path = Path(out_dir) if out_dir else DEFAULT_OUT_DIR

    out_path.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # Phase 1: Decode FIT → TSV
    # -----------------------------
    print("--- Phase 1: Decoding FIT files ---")

    for fit_file in workouts_path.glob("*.fit"):
        fit_to_tsv_folder(str(fit_file), str(out_path))

    # -----------------------------
    # Phase 2: Build Master Summary
    # -----------------------------
    print("\n--- Phase 2: Building Master Summary ---")

    summary_df = summarize_from_tsvs(out_path)
    summary_df.to_csv(out_path / "master_workout_summary.tsv", sep="\t", index=False)

    # -----------------------------
    # Phase 3: Spatial Route Matching
    # -----------------------------
    print("\n--- Phase 3: Spatial Route Matching ---")

    route_report = generate_route_report(summary_df, out_path)
    route_report.to_csv(out_path / "matched_routes_analysis.tsv", sep="\t", index=False)

    return summary_df, route_report