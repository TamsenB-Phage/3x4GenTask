import pandas as pd
import numpy as np
from pathlib import Path

def calculate_universal_offsets(pause_list, fallback_decay=1.0):
    """
    Sorts pauses by starting HR and calculates synthetic time offsets 
    to bridge gaps between different effort levels.
    """
    # Sort descending: Highest HR establishes the t=0 anchor
    pause_list.sort(key=lambda x: x['hr_series'][0], reverse=True)
    
    hr_to_time = {}
    aligned_data = []

    for i, pause in enumerate(pause_list):
        hr_vals = pause['hr_series']
        start_hr = int(hr_vals[0])
        
        if i == 0:
            offset = 0
        else:
            if start_hr in hr_to_time:
                offset = hr_to_time[start_hr]
            else:
                # Gap-Bridging: Find closest higher HR anchor
                existing_hrs = np.array(list(hr_to_time.keys()))
                higher_hrs = existing_hrs[existing_hrs > start_hr]
                
                if len(higher_hrs) > 0:
                    anchor_hr = higher_hrs.min()
                    offset = hr_to_time[anchor_hr] + (anchor_hr - start_hr) / fallback_decay
                else:
                    offset = 0

        # Update the master map with this curve's timeline
        for t, hr in enumerate(hr_vals):
            synth_t = t + offset
            hr_int = int(hr)
            if hr_int not in hr_to_time or synth_t < hr_to_time[hr_int]:
                hr_to_time[hr_int] = synth_t
        
        pause['offset'] = offset
        aligned_data.append(pause)

    return aligned_data

def categorize_comrades_phases(pause_summary, comrades_date_str):
    """
    Labels data as Pre-Comrades, The Race, or Post-Comrades based on UTC timestamp.
    """
    comrades_dt = pd.to_datetime(comrades_date_str).tz_localize('UTC')
    comrades_date_only = comrades_dt.date()
    
    def get_phase(ts_str):
        ts = pd.to_datetime(ts_str)
        if ts.date() == comrades_date_only:
            return 'The Race'
        return 'Post-Comrades' if ts > comrades_dt else 'Pre-Comrades'

    pause_summary['phase'] = pause_summary['timestamp'].apply(get_phase)
    return pause_summary