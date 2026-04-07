import pandas as pd
from pathlib import Path
from preprocessing.extraction import extract_pause_snapshots
from analysis.pause_stitching import calculate_universal_offsets, categorize_comrades_phases

def run_comrades_analysis(summary_df, out_dir="../out", comrades_date="2025-06-08"):
    """Specialized recovery analysis for the Comrades Marathon event.

    Args:
        summary_df (pd.DataFrame): The output from the global orchestrator.
        out_dir (str): Path to processed activity folders.
        comrades_date (str): Event date to define Pre/Race/Post phases.

    Returns:
        list[dict]: Aligned recovery curves with synthetic offsets and phase tags.
    """
    out_path = Path(out_dir)
    pauses_dir = out_path / "pauses"
    all_pause_metadata = []

    # 1. EXTRACTION: Slice recovery windows
    print("\n--- Phase 4: Extracting Recovery Snapshots (Comrades Spec) ---")
    for _, row in summary_df.iterrows():
        record_path = out_path / row['folder'] / "record.tsv"
        if record_path.exists():
            df = pd.read_csv(record_path, sep='\t')
            snaps = extract_pause_snapshots(df, row['folder'], pauses_dir)
            all_pause_metadata.extend(snaps)

    # 2. ANALYSIS: Stitching & Phasing
    if not all_pause_metadata:
        print("No recovery snapshots found.")
        return None

    print("\n--- Phase 5: Stitching & Phasing Analysis ---")
    pause_summary = pd.DataFrame(all_pause_metadata)
    pause_summary = categorize_comrades_phases(pause_summary, comrades_date)
    
    processed_pauses = []
    for _, row in pause_summary.iterrows():
        p_path = pauses_dir / row['pause_file']
        if p_path.exists():
            p_df = pd.read_csv(p_path, sep='\t')
            processed_pauses.append({
                'hr_series': p_df['hr_smooth'].values,
                'phase': row['phase'],
                'timestamp': row['timestamp'],
                'pause_file': row['pause_file'],
                'power': row['power_at_start']
            })
            
    return calculate_universal_offsets(processed_pauses)