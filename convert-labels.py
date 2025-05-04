import os
import glob

def convert_labels(label_dir):
    # Dictionary to map text labels to numeric indices
    label_map = {
        'b1': 0,  # bina
    }
    
    # Get all text files in the label directory
    label_files = glob.glob(os.path.join(label_dir, '*.txt'))
    
    for file_path in label_files:
        # Read the current content
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Convert and write back
        with open(file_path, 'w') as f:
            for line in lines:
                parts = line.strip().split(' ')
                if parts[0] in label_map:
                    # Replace the text label with numeric index
                    parts[0] = str(label_map[parts[0]])
                    f.write(' '.join(parts) + '\n')
                else:
                    # Keep the line unchanged if label not found in map
                    f.write(line)
        
        print(f"Converted {file_path}")

# Example usage:
# Replace with the actual path to your label directories
train_labels_dir = './datasets/my-bina/labels/train'
val_labels_dir = './datasets/my-bina/labels/val'
test_labels_dir = './datasets/my-bina/labels/test'

# Convert labels in each directory
for directory in [train_labels_dir, val_labels_dir, test_labels_dir]:
    if os.path.exists(directory):
        print(f"Converting labels in {directory}...")
        convert_labels(directory)
    else:
        print(f"Directory {directory} not found, skipping.")

print("Label conversion complete!")