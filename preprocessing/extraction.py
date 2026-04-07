import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
from pathlib import Path

def smooth_heart_rate(df, window_len=11, poly_order=2):
    """
    Applies Savitzky-Golay smoothing to the heart rate column.
    Preserves the shape of the 'peak' better than a rolling mean.
    """
    if 'heart_rate' not in df.columns:
        return df
    
    hr_raw = df['heart_rate'].values
    if len(hr_raw) > window_len:
        df['hr_smooth'] = savgol_filter(hr_raw, window_len, poly_order)
    else:
        df['hr_smooth'] = hr_raw
    return df

def extract_pause_snapshots(df, activity_id, output_dir, speed_threshold=0.3, min_work=50000):
    """
    Identifies pauses, trims them to 60s, and saves them as individual TSVs.
    Returns a list of metadata dictionaries for the summary.
    """
    pause_snapshots = []
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    power_col = 'accumulated_power' if 'accumulated_power' in df.columns else 'total_work'
    if 'heart_rate' not in df.columns or power_col not in df.columns:
        return []

    # Identify pause groups
    df['is_paused'] = df['enhanced_speed'] < speed_threshold
    df['p_grp'] = (df['is_paused'] != df['is_paused'].shift()).cumsum()
    
    for g_id, p_df in df[df['is_paused']].groupby('p_grp'):
        start_pow = p_df[power_col].iloc[0]
        
        # Filter: Must have enough data points and meet the work threshold
        if len(p_df) >= 15 and start_pow >= min_work:
            # Trim to 60s and smooth the specific slice
            snap_df = p_df.head(60).copy()
            snap_df = smooth_heart_rate(snap_df)
            
            file_name = f"pause_{activity_id}_{g_id}.tsv"
            snap_df.to_csv(output_path / file_name, sep='\t', index=False)
            
            pause_snapshots.append({
                'pause_file': file_name,
                'timestamp': snap_df['timestamp'].iloc[0],
                'power_at_start': start_pow,
                'hr_at_start': snap_df['hr_smooth'].iloc[0]
            })
            
    return pause_snapshots