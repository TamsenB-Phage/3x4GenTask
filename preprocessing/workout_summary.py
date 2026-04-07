import pandas as pd
from pathlib import Path
import numpy as np
from preprocessing.route_matching import find_matched_routes

def summarize_from_tsvs(base_dir: str):
    """
    Crawls folder structure in ../out to build a master training log.
    """
    base_path = Path(base_dir)
    activity_folders = [f for f in base_path.iterdir() if f.is_dir() and f.name != "pauses"]
    
    summary_list = []
    print(f"Summarizing {len(activity_folders)} extracted activities...")

    for folder in activity_folders:
        session_file = folder / "session.tsv"
        record_file = folder / "record.tsv"
        
        if not session_file.exists():
            continue

        try:
            session_df = pd.read_csv(session_file, sep='\t')
            row = session_df.iloc[0]
            
            sport = row.get('sport_profile_name', row.get('sport', 'unknown'))
            sub_sport = row.get('sub_sport', 'generic')
            
            data = {
                "date": row.get('start_time'),
                "sport": sport,
                "sub_sport": sub_sport,
                "duration_min": round(row.get('total_elapsed_time', 0) / 60, 2),
                "avg_hr": row.get('avg_heart_rate'),
                "max_hr": row.get('max_heart_rate'),
                "folder": folder.name,
                "distance": row.get('total_distance', 0)
            }

            if record_file.exists():
                record_df = pd.read_csv(record_file, sep='\t')
                data["is_indoor"] = 'position_lat' not in record_df.columns

                if 'heart_rate' in record_df.columns:
                    valid_hr = record_df['heart_rate'][record_df['heart_rate'] > 0]
                    data["min_hr_manual"] = int(valid_hr.min()) if not valid_hr.empty else None
            
            summary_list.append(data)
        except Exception as e:
            print(f"Error processing folder {folder.name}: {e}")

    df = pd.DataFrame(summary_list)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        cols = ["date", "sport", "sub_sport", "is_indoor", "duration_min", "avg_hr", "max_hr", "min_hr_manual", "folder", "distance"]
        df = df[[c for c in cols if c in df.columns]]
    return df

def generate_route_report(summary_df, base_dir):
    """
    Wrapper for the H3 matching logic to identify repeating routes.
    """
    print("Matching routes based on spatial overlap...")
    route_report = find_matched_routes(summary_df, base_dir)
    if not route_report.empty:
        route_report = route_report.sort_values(['route_name', 'date'])
    return route_report