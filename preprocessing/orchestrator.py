from pathlib import Path
from preprocessing.fit_to_tsv_folder import fit_to_tsv_folder
from preprocessing.workout_summary import summarize_from_tsvs, generate_route_report

def run_global_orchestration(workouts_dir="../workouts", out_dir="../out"):
    """Coordinates the generic end-to-end data pipeline for any Garmin activity.

    Args:
        workouts_dir (str): Path to raw .fit files.
        out_dir (str): Path for processed TSV output.

    Returns:
        tuple: (summary_df, route_report) resulting from the processed activities.
    """
    workouts_path = Path(workouts_dir)
    out_path = Path(out_dir)
    
    # 1. DECODE: FIT -> TSV
    print("--- Phase 1: Decoding FIT files ---")
    for fit_file in workouts_path.glob("*.fit"):
        fit_to_tsv_folder(str(fit_file), str(out_path))

    # 2. INDEX: Master Summary
    print("\n--- Phase 2: Building Master Summary ---")
    summary_df = summarize_from_tsvs(str(out_path))
    summary_df.to_csv(out_path / "master_workout_summary.tsv", sep='\t', index=False)

    # 3. SPATIAL: Match Routes
    print("\n--- Phase 3: Spatial Route Matching ---")
    route_report = generate_route_report(summary_df, str(out_path))
    route_report.to_csv(out_path / "matched_routes_analysis.tsv", sep='\t', index=False)

    return summary_df, route_report