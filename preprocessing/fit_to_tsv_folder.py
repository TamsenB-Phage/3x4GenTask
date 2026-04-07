import pandas as pd
from garmin_fit_sdk import Decoder, Stream, Profile
from pathlib import Path
from typing import Union

def convert_semicircles_to_degrees(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes FIT coordinate columns to decimal degrees.

    Garmin stores latitude and longitude as 32-bit integers (semicircles).
    This function converts them to the standard decimal degrees used by 
    most mapping software.

    Args:
        df: A pandas DataFrame containing decoded FIT message data.

    Returns:
        pd.DataFrame: The DataFrame with 'position_lat' and 'position_long' 
            converted to float degrees, if those columns existed.
    """
    # Formula: degrees = semicircles * (180 / 2^31)
    factor = 180 / (2**31)
    
    # We check for these specific Garmin FIT SDK standard names
    target_cols = ['position_lat', 'position_long']
    
    for col in target_cols:
        if col in df.columns:
            # Convert to float first to ensure precision, then apply factor
            df[col] = df[col].astype(float) * factor
            
    return df

def fit_to_tsv_folder(fit_file_path: Union[str, Path], output_base_dir: str = "extracted_data") -> None:
    """Decodes a Garmin .FIT file and saves each message type as a TSV file.

    This function creates a subdirectory named after the FIT file and populates 
    it with Tab-Separated Value (TSV) files for every message type found 
    (e.g., record, lap, device_info). It also automatically handles the 
    conversion of semicircles to decimal degrees.

    Args:
        fit_file_path: The path to the source .fit file.
        output_base_dir: The root directory where extracted folders 
            will be created. Defaults to "extracted_data".

    Raises:
        FileNotFoundError: If the provided fit_file_path does not exist.
    """
    # 1. Setup paths
    fit_path = Path(fit_file_path)
    if not fit_path.exists():
        raise FileNotFoundError(f"FIT file not found at {fit_path}")

    folder_name = fit_path.stem
    output_dir = Path(output_base_dir) / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Setup SDK Decoder
    stream = Stream.from_file(str(fit_path))
    decoder = Decoder(stream)
    
    all_messages = {}
    msg_num_to_name = {v: k.lower() for k, v in Profile['mesg_num'].items()}

    def mesg_listener(mesg_num: int, message: dict) -> None:
        """Internal callback to collect messages by type during decoding."""
        msg_name = msg_num_to_name.get(mesg_num, f"unknown_{mesg_num}")
        if msg_name not in all_messages:
            all_messages[msg_name] = []
        all_messages[msg_name].append(message)

    # 3. Process the file
    print(f"Decoding {fit_path.name}...")
    _, errors = decoder.read(mesg_listener=mesg_listener)
    
    if errors:
        print(f"Warnings for {fit_path.name}: {errors}")

    # 4. Save each message type to its own TSV
    for msg_name, data_list in all_messages.items():
        df = pd.DataFrame(data_list)
        
        # Clean up column names (standardize spaces to underscores)
        df.columns = [str(c).replace(' ', '_') for c in df.columns]
        
        # Identify and convert coordinate columns if they exist
        df = convert_semicircles_to_degrees(df)
        
        tsv_name = f"{msg_name}.tsv"
        file_path = output_dir / tsv_name
        
        df.to_csv(file_path, sep='\t', index=False)
        
    print(f"Done! Data saved to: {output_dir}")

def main(input_dir: str = "../workouts", output_dir: str = "../out") -> None:
    """Batch processes all FIT files in a directory.

    Args:
        input_dir: Path to the folder containing .fit files.
        output_dir: Path to the folder where extracted data should be saved.
    """
    workout_folder = Path(input_dir)
    output_base_dir = Path(output_dir)
    
    # Validation
    if not workout_folder.exists():
        print(f"Error: The input folder '{workout_folder}' does not exist.")
        return

    # Create output base if it doesn't exist
    output_base_dir.mkdir(parents=True, exist_ok=True)
    
    # Gather files
    fit_files = list(workout_folder.glob("*.fit"))
    if not fit_files:
        print(f"No .fit files found in {workout_folder}")
        return

    print(f"Found {len(fit_files)} files. Starting conversion...")
    
    success_count = 0
    for fit_file in fit_files:
        try:
            # We call the conversion function for each file
            fit_to_tsv_folder(fit_file, str(output_base_dir))
            success_count += 1
        except Exception as e:
            # This prevents the whole script from crashing on one bad file
            print(f"  [ERROR] Could not process {fit_file.name}: {e}")

    print(f"\nProcessing complete!")
    print(f"Successfully converted {success_count} of {len(fit_files)} files.")

if __name__ == "__main__":
    main()