from garmin_fit_sdk import Decoder, Stream, Profile
from pathlib import Path

def find_sleep_in_fit_files(folder_path: str):
    path_obj = Path(folder_path)
    fit_files = list(path_obj.glob("*.fit"))
    
    sleep_files = []

    # Map for checking file types
    # 9 = Health/Monitoring (where sleep usually lives)
    # 32 = Sleep (dedicated sleep files, rare but exist)
    target_file_types = [9, 32]

    print(f"Scanning {len(fit_files)} files for sleep data...")

    for file_path in fit_files:
        stream = Stream.from_file(str(file_path))
        decoder = Decoder(stream)
        
        is_sleep_file = False
        
        def mesg_listener(mesg_num, message):
            nonlocal is_sleep_file
            
            # 1. Check the File ID message (at the very start of the file)
            if mesg_num == Profile['mesg_num']['FILE_ID']:
                file_type = message.get('type')
                if file_type in target_file_types:
                    is_sleep_file = True

            # 2. Check for Sleep Level messages (Standard Sleep Data)
            if mesg_num == Profile['mesg_num']['SLEEP_LEVEL']:
                is_sleep_file = True

        # We only need to read a small part of the file to find the File ID
        # but decoder.read() is the safest way to ensure we hit the listener
        decoder.read(mesg_listener=mesg_listener)

        if is_sleep_file:
            sleep_files.append(file_path.name)
            print(f" [!] Found Sleep/Wellness data in: {file_path.name}")

    return sleep_files

# Execution
if __name__ == "__main__":
    workout_folder = Path("../workouts")
    sleep_results = find_sleep_in_fit_files(workout_folder)