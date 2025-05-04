import os
import shutil
import random
import math

# Add this line to see the current directory (debugging purposes, can remove later)
print("Current working directory:", os.getcwd())

# Define source directories
# 'ekran_goruntusu' klasörünün altında doğrudan 'images' ve 'labels' olduğunu varsayarak yolları güncelledik.
source_base_dir = './ekran_goruntusu' # Scriptiniz CollectAI içinde ise bu yol doğru olmalı.
source_images_dir = os.path.join(source_base_dir, 'images') # b1 klasörünü kaldırdık
source_labels_dir = os.path.join(source_base_dir, 'labels') # b1 klasörünü kaldırdık

# Define destination base directory
destination_base_dir = 'datasets/my-bina'

# Define split ratios (70/15/15 as you desired)
train_ratio = 0.7
val_ratio = 0.3
test_ratio = 0

# Ensure ratios sum to 1 (or very close due to floating point precision)
if not (abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6):
    print("Warning: Split ratios do not sum to 1. Adjusting test ratio.")
    test_ratio = 1.0 - train_ratio - val_ratio

# Create destination directories
def create_dirs(base_dir):
    os.makedirs(os.path.join(base_dir, 'images', 'train'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'images', 'val'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'images', 'test'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'labels', 'train'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'labels', 'val'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'labels', 'test'), exist_ok=True)

create_dirs(destination_base_dir)

# Get list of image files and extract base names
try:
    # List files in the updated source image directory
    image_files = [f for f in os.listdir(source_images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff'))] # Yaygın görsel formatlarını ekledik
    base_names = [os.path.splitext(f)[0] for f in image_files]
except FileNotFoundError:
    print(f"Error: Source directory not found: {source_images_dir}")
    print("Please ensure the 'ekran_goruntusu/images' folder exists relative to the script location.")
    exit() # Scripti durdur

# Optional: Verify that each image has a corresponding label
missing_labels = [name for name in base_names if not os.path.exists(os.path.join(source_labels_dir, name + '.txt'))]
if missing_labels:
    print(f"Warning: The following base names are missing corresponding label (.txt) files: {missing_labels}")
    # Skipping files without matching labels
    base_names = [name for name in base_names if name not in missing_labels]

if not base_names:
    print("No matching image and label files found. Exiting.")
    exit()

# Shuffle the base names
random.shuffle(base_names)

# Calculate split sizes using the improved distribution method
total_files = len(base_names)

# Calculate train count
train_count = math.floor(total_files * train_ratio)

# Calculate remaining files after train split
remaining_files = total_files - train_count

# Calculate val and test counts from remaining files
val_test_ratio_sum = val_ratio + test_ratio
if val_test_ratio_sum == 0:
     val_count = 0
     test_count = remaining_files
elif remaining_files == 0:
     val_count = 0
     test_count = 0
else:
    # Calculate val count from remaining files based on its proportion of the remaining
    val_count = math.floor(remaining_files * (val_ratio / val_test_ratio_sum))
    test_count = remaining_files - val_count # Test gets the rest


# Ensure the counts add up to total_files (should be guaranteed by the calculation logic)
if train_count + val_count + test_count != total_files:
     print("Warning: File counts do not sum up, adjusting test count.")
     test_count = total_files - train_count - val_count


print(f"Total files found: {total_files}")
print(f"Train set size: {train_count}")
print(f"Validation set size: {val_count}")
print(f"Test set size: {test_count}")

# Split base names
train_files = base_names[:train_count]
val_files = base_names[train_count : train_count + val_count]
test_files = base_names[train_count + val_count :]

# Function to copy files
def copy_files(file_list, data_type, split_type):
    """
    Copies files from source to destination.

    Args:
        file_list (list): List of base filenames.
        data_type (str): 'images' or 'labels'.
        split_type (str): 'train', 'val', or 'test'.
    """
    source_dir = source_images_dir if data_type == 'images' else source_labels_dir
    dest_dir = os.path.join(destination_base_dir, data_type, split_type)
    # Belirli bir uzantı yerine, base_name'e uygun uzantıyı bulmaya çalışalım (sadece görüntüler için geçerli)
    # Etiketler için uzantı her zaman '.txt'
    extension = '.txt' if data_type == 'labels' else None # Görseller için uzantıyı henüz bilmiyoruz

    # Ensure destination directory exists
    os.makedirs(dest_dir, exist_ok=True)

    for base_name in file_list:
        if data_type == 'images':
            # Find the correct image extension by checking files in the source images directory
            found_extension = None
            for img_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']: # Kontrol edilecek yaygın uzantılar
                 potential_source_path = os.path.join(source_dir, base_name + img_ext)
                 if os.path.exists(potential_source_path):
                     source_path = potential_source_path
                     extension = img_ext
                     found_extension = True
                     break
            if not found_extension:
                 print(f"Error: Image file not found with common extensions for base name: {base_name}")
                 continue # Bu dosyayı atla
        else: # data_type == 'labels'
             source_path = os.path.join(source_dir, base_name + '.txt')
             extension = '.txt'


        destination_path = os.path.join(dest_dir, base_name + extension)
        try:
            shutil.copy2(source_path, destination_path)
        except FileNotFoundError:
            print(f"Error: Source file not found - {source_path}")
        except Exception as e:
            print(f"Error copying file {source_path} to {destination_path}: {e}")


# Copy files to their respective directories
print("Copying train files...")
copy_files(train_files, 'images', 'train')
copy_files(train_files, 'labels', 'train')

print("Copying validation files...")
copy_files(val_files, 'images', 'val')
copy_files(val_files, 'labels', 'val')

print("Copying test files...")
copy_files(test_files, 'images', 'test')
copy_files(test_files, 'labels', 'test')

print("\nFile splitting and copying complete!")
print(f"Dataset created in: {destination_base_dir}")

# Print final counts in destination folders (Optional verification)
print("\nVerifying counts in destination folders:")
try:
    print(f"Train Images: {len(os.listdir(os.path.join(destination_base_dir, 'images', 'train')))}")
    print(f"Val Images: {len(os.listdir(os.path.join(destination_base_dir, 'images', 'val')))}")
    print(f"Test Images: {len(os.listdir(os.path.join(destination_base_dir, 'images', 'test')))}")
    print(f"Train Labels: {len(os.listdir(os.path.join(destination_base_dir, 'labels', 'train')))}")
    print(f"Val Labels: {len(os.listdir(os.path.join(destination_base_dir, 'labels', 'val')))}")
    print(f"Test Labels: {len(os.listdir(os.path.join(destination_base_dir, 'labels', 'test')))}")
except FileNotFoundError:
    print("Error: Destination directories not found during verification.")