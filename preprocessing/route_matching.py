import pandas as pd
from pathlib import Path
import h3

def get_route_fingerprint(record_path: Path, res: int = 8):
    """Generates a set of unique H3 cells for a given workout."""
    if not record_path.exists():
        return None
    
    df = pd.read_csv(record_path, sep='\t')
    
    # Ensure we have coordinates
    if 'position_lat' not in df.columns or 'position_long' not in df.columns:
        return None
        
    # Drop rows without GPS and convert to H3
    df = df.dropna(subset=['position_lat', 'position_long'])
    
    # Create the set of unique hexagons the workout passed through
    cells = {h3.latlng_to_cell(row['position_lat'], row['position_long'], res) 
             for _, row in df.iterrows()}
    return cells

def find_matched_routes(summary_df: pd.DataFrame, base_dir: str, similarity_threshold: float = 0.7):
    base_path = Path(base_dir)
    fingerprints = {}
    
    # 1. Load Fingerprints
    for idx, row in summary_df.iterrows():
        record_file = base_path / row['folder'] / "record.tsv"
        fp = get_route_fingerprint(record_file)
        if fp:
            fingerprints[row['folder']] = fp

    matched_data = []
    route_counter = 1
    processed_folders = set()

    for sport, group in summary_df.groupby('sport'):
        folders = group['folder'].tolist()
        
        for i, folder_a in enumerate(folders):
            if folder_a in processed_folders or folder_a not in fingerprints:
                continue
            
            current_route_members = [folder_a]
            fp_a = fingerprints[folder_a]
            
            for folder_b in folders[i+1:]:
                if folder_b in processed_folders or folder_b not in fingerprints:
                    continue
                
                intersection = len(fp_a.intersection(fingerprints[folder_b]))
                union = len(fp_a.union(fingerprints[folder_b]))
                similarity = intersection / union if union > 0 else 0
                
                if similarity >= similarity_threshold:
                    current_route_members.append(folder_b)
            
            if len(current_route_members) >= 2:
                for folder in current_route_members:
                    session_file = base_path / folder / "session.tsv"
                    sess_df = pd.read_csv(session_file, sep='\t')
                    s_row = sess_df.iloc[0]
                    
                    matched_data.append({
                        "route_name": f"Route {route_counter}",
                        "date": s_row.get('start_time'),
                        "activity_type": sport,
                        "distance": round(s_row.get('total_distance', 0), 2),
                        "folder": folder  # <--- This adds the file/folder name to your report
                    })
                    processed_folders.add(folder)
                route_counter += 1
                
    return pd.DataFrame(matched_data)