import pandas as pd
from pathlib import Path
import numpy as np
from preprocessing.route_matching import find_matched_routes


def summarize_from_tsvs(base_dir: str) -> pd.DataFrame:
    """
    Build a master training summary from extracted activity folders.

    This function crawls a directory of activity exports (e.g. ../out),
    reads `session.tsv` and `record.tsv` files, and aggregates key
    training metrics into a single structured DataFrame.

    Each activity folder is expected to contain:
    - session.tsv (required): high-level session metadata
    - record.tsv (optional): time-series data for additional metrics

    Args:
        base_dir (str):
            Path to the root directory containing extracted activity folders.

    Returns:
        pd.DataFrame:
            A DataFrame containing one row per activity, sorted by date.
            Columns may include:
                - date (datetime): Activity start time
                - sport (str): Sport type (e.g. run, ride)
                - sub_sport (str): Sub-category of activity
                - is_indoor (bool): Whether the activity is indoors
                - duration_min (float): Duration in minutes
                - avg_hr (float): Average heart rate
                - max_hr (float): Maximum heart rate
                - min_hr_manual (int): Minimum observed HR from record data
                - folder (str): Source folder name
                - distance (float): Total distance

    Notes:
        - Activities without a session.tsv file are skipped.
        - Indoor detection is inferred from missing GPS coordinates.
        - Heart rate values <= 0 are treated as invalid.
        - The function is robust to missing columns and partial data.
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

                # Indoor activities typically lack GPS coordinates
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

        cols = [
            "date",
            "sport",
            "sub_sport",
            "is_indoor",
            "duration_min",
            "avg_hr",
            "max_hr",
            "min_hr_manual",
            "folder",
            "distance",
        ]

        df = df[[c for c in cols if c in df.columns]]

    return df


def generate_route_report(summary_df: pd.DataFrame, base_dir: str) -> pd.DataFrame:
    """
    Identify and group repeated routes based on spatial similarity.

    This function acts as a wrapper around the route matching logic,
    which uses spatial overlap (e.g. H3 indexing) to detect activities
    that follow similar routes.

    Args:
        summary_df (pd.DataFrame):
            Activity summary DataFrame produced by `summarize_from_tsvs`.
        base_dir (str):
            Path to the directory containing activity folders and record files.

    Returns:
        pd.DataFrame:
            A DataFrame of matched routes, typically including:
                - route_name (str): Identifier for grouped routes
                - date (datetime): Activity date
                - additional route-level metadata

            Returns an empty DataFrame if no matches are found.

    Notes:
        - Matching is based on spatial overlap, not exact path equality.
        - Results are sorted by route_name and date for readability.
        - Depends on `find_matched_routes` implementation.
    """
    print("Matching routes based on spatial overlap...")

    route_report = find_matched_routes(summary_df, base_dir)

    if not route_report.empty:
        route_report = route_report.sort_values(['route_name', 'date'])

    return route_report