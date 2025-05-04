# YOLO Data Collection & Processing Toolkit

A comprehensive toolkit for collecting, annotating, and preparing custom datasets for YOLO object detection models.

## Overview

This toolkit provides a complete workflow for:
1. **Screen Capture & Annotation** - Capture regions of your screen and annotate objects with YOLO-compatible labels
2. **Dataset Management** - Split, merge, and organize your custom datasets
3. **Label Conversion** - Convert between text and numeric labels

## Installation

### Prerequisites
- Python 3.8 or higher
- Conda package manager

### Setup
1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/yolo-data-collection.git
   cd yolo-data-collection
   ```

2. Create the conda environment from the provided YAML file:
   ```bash
   conda env create -f environment.yaml
   ```

3. Activate the environment:
   ```bash
   conda activate yolo-data-collection
   ```

## Annotation Editor (`edit.py`)

The Annotation Editor provides a graphical interface for viewing and editing YOLO format annotations.

```bash
python edit.py
```

### Key Features:
- **Open and browse** existing datasets with forward/backward navigation
- **View annotations** visualized on the images with colored bounding boxes
- **Add new annotations** by drawing bounding boxes directly on the image
- **Edit existing annotations** by dragging them or changing their class
- **Delete annotations** that are incorrect or no longer needed
- **Zoom and pan** for detailed work on high-resolution images
- **Class management** with custom color coding and class mapping editing

### Keyboard Shortcuts:
- **Left/Right Arrow**: Navigate between images
- **Delete**: Remove the selected annotation
- **Ctrl+S**: Save annotations
- **Ctrl+O**: Open a dataset folder
- **Ctrl+N**: Start a new annotation
- **Escape**: Cancel new annotation

### Mouse Controls:
- **Left-click and drag**: Draw or move annotations
- **Right-click**: Open context menu for additional options
- **Middle-click and drag**: Pan the image
- **Mouse wheel**: Zoom in/out

### Screen Capture & Annotation Tool (`collect.py`)

This GUI tool allows you to capture regions of your screen and annotate objects for YOLO training.

```bash
python collect.py
```

#### Key Controls:
- **W**: Enter target selection mode (capture a screen region)
- **S**: Confirm and save the selected region
- **A**: Select an annotation class/folder
- **Z**: Undo the last annotation
- **ESC**: Exit the program

#### Workflow:
1. Press **W** to capture a screen region
2. Select the region with your mouse and press **S** to confirm
3. Press **A** to select an annotation class
4. Draw bounding boxes around objects by clicking and dragging
5. Each annotation is automatically saved with YOLO format labels

### Dataset Splitting (`split.py`)

Split your collected data into training, validation, and test sets.

```bash
python split.py
```

This script:
- Creates a standard YOLO dataset structure
- Randomly splits images and labels into train/val/test sets (default: 70%/30%/0%)
- Maintains image-label pairs during splitting

### Merging Datasets (`merge.py`)

Merge data from multiple collection sessions.

```bash
python merge.py
```

The script combines data from `ekran_goruntusu` and `ekran_goruntusu2` directories into a merged dataset while maintaining proper file numbering.

### Converting Labels (`convert-labels.py`)

Convert text-based class labels to numeric indices as required by YOLO.

```bash
python convert-labels.py
```

Edit the label mapping in the script to define your classes:
```python
label_map = {
    'b1': 0,  # building
    'car': 1,
    # Add more class mappings as needed
}
```

## Directory Structure

After running the tools, your workspace will have this structure:

```
yolo-data-collection/
├── ekran_goruntusu/        # Screen capture output
│   ├── images/             # Captured screen regions
│   ├── labels/             # YOLO format labels
│   └── [class_folders]/    # Annotated object crops by class
├── datasets/
│   └── my-bina/            # Processed dataset
│       ├── images/
│       │   ├── train/
│       │   ├── val/
│       │   └── test/
│       └── labels/
│           ├── train/
│           ├── val/
│           └── test/
├── merged_ekran_goruntusu/ # (Optional) Merged datasets
├── collect.py
├── split.py
├── merge.py
├── convert-labels.py
└── environment.yaml
```

## Tips for Effective Data Collection

1. **Screen Resolution**: The tool works with any screen resolution but performs best on moderate to high-resolution displays
2. **Class Naming**: Use short, lowercase names without spaces for annotation classes
3. **Consistent Annotations**: Try to be consistent with bounding box sizes and positions
4. **Balanced Classes**: Collect a balanced number of samples for each class
5. **Diverse Samples**: Capture objects from various angles, lighting conditions, and backgrounds
6. **Background Variation**: Include a variety of backgrounds to improve model generalization

## Customization

### Modifying Split Ratios
Edit `split.py` to change the dataset split ratios:
```python
train_ratio = 0.7  # 70% training
val_ratio = 0.3    # 30% validation
test_ratio = 0     # 0% test
```

### Changing Output Directories
Modify the directory paths in each script to customize your workflow.

## Troubleshooting

### Common Issues

1. **Tkinter Not Found**: Install tkinter via conda: `conda install -c conda-forge tk`
2. **PyAutoGUI Permissions**: Some systems require additional permissions for screen capture
   - On macOS: Grant screen recording permissions in System Preferences > Security & Privacy
   - On Windows: Run the script as administrator if having permission issues
3. **Path Not Found Errors**: Ensure all referenced directories exist before running the scripts

## License

This toolkit is provided under the MIT License. See LICENSE file for details.

## Acknowledgements

This toolkit was created to streamline the process of collecting custom datasets for YOLO object detection models.