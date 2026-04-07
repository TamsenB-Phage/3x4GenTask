import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from pathlib import Path

def plot_by_route_position(route_df, route_id, base_dir, metric='heart_rate'):
    """
    Plots metrics for all activities in a specific route stretched by distance.
    """
    activities = route_df[route_df['route_name'] == route_id]
    plt.figure(figsize=(12, 5))
    
    for _, row in activities.iterrows():
        record_path = Path(base_dir) / str(row.folder) / "record.tsv"
        df = pd.read_csv(record_path, sep='\t').dropna(subset=['position_lat', 'heart_rate'])
        
        # Distance deltas for 'Stretched' X-Axis
        lat = np.radians(df['position_lat'])
        lon = np.radians(df['position_long'])
        dlat = lat.diff()
        dlon = lon.diff()
        a = np.sin(dlat/2)**2 + np.cos(lat.shift()) * np.cos(lat) * np.sin(dlon/2)**2
        df['cum_dist'] = (2 * 6371000 * np.arcsin(np.sqrt(a))).fillna(0).cumsum()
        
        plt.plot(df['cum_dist'], df[metric], label=f"{row['date']} ({row['folder']})", alpha=0.8)

    plt.title(f"Spatial {metric} Analysis: {route_id}")
    plt.xlabel("Distance along route (meters)")
    plt.ylabel(f"{metric}")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

def plot_route_metric_comparison(route_report, base_dir, route_name, x_axis_col='distance', y_axis_col='accumulated_power'):
    """
    Compares arbitrary metrics (Power, Speed, HR) across the same route over time.
    """
    base_path = Path(base_dir)
    route_group = route_report[route_report['route_name'] == route_name]
    
    plt.figure(figsize=(12, 6))
    for _, row in route_group.iterrows():
        record_file = base_path / str(row.folder) / "record.tsv"
        if not record_file.exists(): continue
        df = pd.read_csv(record_file, sep='\t')
        if x_axis_col in df.columns and y_axis_col in df.columns:
            plot_df = df.dropna(subset=[x_axis_col, y_axis_col])
            plt.plot(plot_df[x_axis_col], plot_df[y_axis_col], label=f"{row['date']}", alpha=0.8)
    
    plt.title(f"{y_axis_col.title()} vs {x_axis_col.title()}: {route_name}")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.show()

def plot_pause_recovery_curves(pause_summary_df, pause_folder_path, route_name):
    """
    Visualizes recovery snapshots colored by fatigue (Accumulated Power).
    """
    path = Path(pause_folder_path) / route_name.replace(" ", "_")
    if not path.exists(): return

    plt.figure(figsize=(10, 6))
    norm = plt.Normalize(pause_summary_df['accumulated_power_start'].min(), 
                         pause_summary_df['accumulated_power_start'].max())
    colormap = cm.get_cmap('cool')

    for _, row in pause_summary_df.iterrows():
        pause_file = path / row['pause_file']
        if not pause_file.exists(): continue
        df = pd.read_csv(pause_file, sep='\t')
        plt.plot(range(len(df)), df['heart_rate'], color=colormap(norm(row['accumulated_power_start'])), alpha=0.7)

    sm = plt.cm.ScalarMappable(cmap=colormap, norm=norm)
    plt.colorbar(sm, ax=plt.gca(), label='Accumulated Power (Joules)')
    plt.title(f"Heart Rate Recovery Curves: {route_name}")
    plt.show()