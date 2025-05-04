import os
import shutil
import re

def get_files_info(folder_path):
    """
    Lists files in a folder, filters for numbered files (digits.extension),
    sorts them numerically, and determines max number and observed padding width.
    Returns a list of (number, filename) tuples, max number found, and common padding width.
    """
    files_info = []
    max_num = 0
    # We need padding per file potentially, but let's assume consistency and find the max
    # Better: find the padding of the file with the max number from the source folder
    observed_padding = 0
    file_extension = ""

    if os.path.isdir(folder_path):
        # Get all potential numbered files first to find max num and padding reliably
        potential_files = []
        for f in os.listdir(folder_path):
             if os.path.isfile(os.path.join(folder_path, f)):
                match = re.match(r'^(\d+)(\..+)$', f)
                if match:
                    num = int(match.group(1))
                    padding = len(match.group(1))
                    ext = match.group(2)
                    potential_files.append((num, f, padding, ext))

        # Sort by number to easily find the max num and its padding
        potential_files.sort(key=lambda x: x[0])

        if potential_files:
            # The last file in sorted list has the max number
            max_num = potential_files[-1][0]
            # Use the padding of the file with the max number from this source folder
            observed_padding = potential_files[-1][2]
            file_extension = potential_files[0][3] # Assume consistent extension

            # Return the list of (number, filename) for sorted files
            files_info = [(info[0], info[1]) for info in potential_files]


    # Sort based on the integer part of the filename just to be sure
    files_info.sort(key=lambda x: x[0])

    # Return sorted list of (number, filename), max number, observed padding, and common extension
    return files_info, max_num, observed_padding, file_extension

def get_min_padding_width_for_count(count):
    """Determines the minimum digits needed for zero-padding for a given count."""
    if count == 0:
        return 1 # Or 0, depending on desired output for empty folders
    return len(str(count))

# Define the source and target directories
source1_dir = 'ekran_goruntusu2'
source2_dir = 'ekran_goruntusu'
target_dir = 'merged_ekran_goruntusu'

# --- Create the target directory structure based on source1_dir ---
print(f"Creating target directory structure based on '{source1_dir}'...")
if os.path.exists(target_dir):
    # Optional: Remove existing target directory to start fresh if needed
    # print(f"Removing existing target directory: {target_dir}")
    # shutil.rmtree(target_dir)
    pass # Keep existing if you want to potentially merge into it
os.makedirs(target_dir, exist_ok=True)

# Walk through the source1 directory structure to create directories
for root, dirs, files in os.walk(source1_dir):
    # Calculate the relative path from source1_dir
    relative_path = os.path.relpath(root, source1_dir)
    # Construct the corresponding path in the target directory
    target_path = os.path.join(target_dir, relative_path)

    # Create the directory in the target path if it doesn't exist
    # os.walk provides directories first, so this should create them before processing files
    if not os.path.exists(target_path):
         os.makedirs(target_path)
         # print(f"Created directory: {target_path}") # Uncomment for verbose output


# --- Merge files into the target directory structure ---
print("Merging files...")

# Walk through the source1 directory structure again to process files
for root, dirs, files in os.walk(source1_dir):
    # Calculate the relative path
    relative_path = os.path.relpath(root, source1_dir)
    target_path = os.path.join(target_dir, relative_path)
    source2_path = os.path.join(source2_dir, relative_path)

    print(f"Processing folder: {relative_path}")

    # Get file info from source1 directory
    # files1_info is a list of (number, filename) tuples
    files1_info, max_source1_number, source1_padding_width, source1_ext = get_files_info(root)

    # Get file info from source2 directory if the corresponding directory exists
    files2_info = [] # list of (number, filename) tuples
    max_source2_number = 0
    source2_padding_width = 0 # Not directly used for naming in this logic
    source2_ext = ""

    if os.path.isdir(source2_path):
        files2_info, max_source2_number_unused, source2_padding_width_unused, source2_ext = get_files_info(source2_path)


    # --- Copy files from source1 with original names ---
    if files1_info:
        print(f"  Copying {len(files1_info)} files from source1...")
        for num, file in files1_info:
            source_file = os.path.join(root, file)
            target_file = os.path.join(target_path, file) # Copy with original name
            # Ensure target file doesn't exist before copying (should be true if target was empty)
            if not os.path.exists(target_file):
                 shutil.copy2(source_file, target_file)
                 # print(f"    Copied '{file}' from source1")
            # else:
                 # print(f"    Warning: Target file '{target_file}' already exists in target, skipping copy from source1.")


    # --- Copy and re-number files from source2 ---
    if files2_info:
        print(f"  Copying and re-numbering {len(files2_info)} files from source2...")
        # Determine the starting index for source2 files in the merged sequence
        start_index = max_source1_number + 1

        # Determine the final padding width for the new names from source2
        # Use source1's padding if files were present in source1, otherwise use padding needed for files2 count
        if source1_padding_width > 0:
             final_padding = source1_padding_width
        else:
             # If source1 had no numbered files, calculate padding based on the number of files from source2
             final_padding = get_min_padding_width_for_count(len(files2_info))

        # Determine the effective extension for the new files
        # Prefer source1 extension if files1 existed, otherwise use source2 extension
        effective_ext = source1_ext if source1_ext else source2_ext

        # Ensure we have an extension if possible
        if not effective_ext and files2_info:
             # Try to get extension from the first file in files2 if source1 had no numbered files
             match = re.match(r'^(\d+)(\..+)$', files2_info[0][1])
             if match:
                 effective_ext = match.group(2)


        file_index = start_index # Counter for source2 files in the merged sequence

        for num, file in files2_info:
            # Construct the new filename using the next index and determined padding/extension
            new_name = f"{file_index:0{final_padding}d}{effective_ext}"
            source_file = os.path.join(source2_path, file)
            target_file = os.path.join(target_path, new_name)

            # Check if the target file with the new name already exists (shouldn't if logic is right)
            if not os.path.exists(target_file):
                shutil.copy2(source_file, target_file)
                # print(f"    Copied '{file}' from source2 to '{new_name}'")
            else:
                print(f"  Warning: Target file '{target_file}' already exists during source2 copy, skipping.")

            file_index += 1
    elif files1_info:
        # Folder only had files in source1, they were copied with original names above
        print(f"  Only {len(files1_info)} files found in source1.")
    else:
         print("  No numbered files found in either source for this folder.")


print("\nMerging complete!")