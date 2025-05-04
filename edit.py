import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk
import os
import shutil
import cv2
import numpy as np
from PIL import Image, ImageTk
import re
import json

class YOLOAnnotationEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO Annotation Editor v1.0")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # State variables
        self.current_image_path = None
        self.current_label_path = None
        self.images_list = []
        self.current_image_index = -1
        self.annotations = []  # List of dicts: {'class_id': str, 'x_center': float, 'y_center': float, 'width': float, 'height': float}
        self.selected_annotation_index = -1
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.class_colors = {}  # Will be populated with random colors for each class
        self.zoom_level = 1.0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.panning = False
        self.class_mapping = {}  # Maps class_id to class_name
        self.config_file = "annotation_editor_config.json"
        
        # Load class mapping and configuration
        self.load_config()
        
        # Create main layout
        self.create_layout()
        
        # Bind events
        self.bind_events()
        
    def load_config(self):
        """Load configuration if exists, otherwise create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.class_mapping = config.get('class_mapping', {})
                    # Convert keys from string to int if they were numeric
                    self.class_mapping = {int(k) if k.isdigit() else k: v for k, v in self.class_mapping.items()}
            except Exception as e:
                messagebox.showwarning("Config Load Error", f"Failed to load configuration: {str(e)}")
                self.class_mapping = {}
        else:
            # Default mappings (modify as needed)
            self.class_mapping = {
                "0": "Class_0",
                "1": "Class_1",
                "2": "Class_2",
                # Add more defaults as needed
            }
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'class_mapping': self.class_mapping}, f, indent=2)
        except Exception as e:
            messagebox.showwarning("Config Save Error", f"Failed to save configuration: {str(e)}")
    
    def create_layout(self):
        """Create the main UI layout"""
        # Create a main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top toolbar
        self.toolbar = tk.Frame(self.main_frame, bd=1, relief=tk.RAISED)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Toolbar buttons
        btn_open = tk.Button(self.toolbar, text="Open Folder", command=self.open_folder)
        btn_open.pack(side=tk.LEFT, padx=2, pady=2)
        
        btn_save = tk.Button(self.toolbar, text="Save", command=self.save_annotations)
        btn_save.pack(side=tk.LEFT, padx=2, pady=2)
        
        btn_prev = tk.Button(self.toolbar, text="Previous", command=self.prev_image)
        btn_prev.pack(side=tk.LEFT, padx=2, pady=2)
        
        btn_next = tk.Button(self.toolbar, text="Next", command=self.next_image)
        btn_next.pack(side=tk.LEFT, padx=2, pady=2)
        
        btn_add = tk.Button(self.toolbar, text="Add Annotation", command=self.start_new_annotation)
        btn_add.pack(side=tk.LEFT, padx=2, pady=2)
        
        btn_delete = tk.Button(self.toolbar, text="Delete Selected", command=self.delete_selected_annotation)
        btn_delete.pack(side=tk.LEFT, padx=2, pady=2)
        
        btn_class_mapping = tk.Button(self.toolbar, text="Class Mapping", command=self.edit_class_mapping)
        btn_class_mapping.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Image navigation toolbar
        self.nav_frame = tk.Frame(self.main_frame)
        self.nav_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        self.image_counter_label = tk.Label(self.nav_frame, text="Image: 0/0")
        self.image_counter_label.pack(side=tk.LEFT, padx=5)
        
        self.image_path_label = tk.Label(self.nav_frame, text="No image loaded")
        self.image_path_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Zoom controls
        zoom_frame = tk.Frame(self.nav_frame)
        zoom_frame.pack(side=tk.RIGHT, padx=5)
        
        btn_zoom_in = tk.Button(zoom_frame, text="+", command=self.zoom_in, width=2)
        btn_zoom_in.pack(side=tk.LEFT, padx=2)
        
        self.zoom_label = tk.Label(zoom_frame, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=2)
        
        btn_zoom_out = tk.Button(zoom_frame, text="-", command=self.zoom_out, width=2)
        btn_zoom_out.pack(side=tk.LEFT, padx=2)
        
        btn_reset_view = tk.Button(zoom_frame, text="Reset View", command=self.reset_view)
        btn_reset_view.pack(side=tk.LEFT, padx=2)
        
        # Main content area with the canvas and sidebar
        self.content_frame = tk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for image display
        self.canvas_frame = tk.Frame(self.content_frame, bd=1, relief=tk.SUNKEN)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas with scrollbars
        self.canvas = tk.Canvas(self.canvas_frame, bg='gray', cursor="crosshair")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Sidebar for annotations list
        self.sidebar_frame = tk.Frame(self.content_frame, width=250)
        self.sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        self.sidebar_frame.pack_propagate(False)  # Prevent the frame from shrinking
        
        # Annotations list with scrollbar
        self.annotations_list_label = tk.Label(self.sidebar_frame, text="Annotations:")
        self.annotations_list_label.pack(side=tk.TOP, anchor=tk.W, pady=(0, 5))
        
        annotations_frame = tk.Frame(self.sidebar_frame)
        annotations_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.annotations_listbox = tk.Listbox(annotations_frame, exportselection=0)
        self.annotations_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(annotations_frame, orient=tk.VERTICAL, command=self.annotations_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.annotations_listbox.config(yscrollcommand=scrollbar.set)
        
        # Bind listbox selection
        self.annotations_listbox.bind('<<ListboxSelect>>', self.on_annotation_select)
        
        # Status bar
        self.status_bar = tk.Label(self.main_frame, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def bind_events(self):
        """Bind events to the canvas and root"""
        # Canvas event bindings
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Right click for context menu
        self.canvas.bind("<ButtonPress-3>", self.show_context_menu)
        
        # Middle button (scroll wheel) for panning
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.pan)
        self.canvas.bind("<ButtonRelease-2>", self.end_pan)
        
        # Mouse wheel for zooming
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mousewheel)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mousewheel)    # Linux scroll down
        
        # Keyboard shortcuts
        self.root.bind("<Left>", lambda e: self.prev_image())
        self.root.bind("<Right>", lambda e: self.next_image())
        self.root.bind("<Delete>", lambda e: self.delete_selected_annotation())
        self.root.bind("<Control-s>", lambda e: self.save_annotations())
        self.root.bind("<Control-o>", lambda e: self.open_folder())
        self.root.bind("<Control-n>", lambda e: self.start_new_annotation())
        self.root.bind("<Escape>", lambda e: self.cancel_new_annotation())
    
    def open_folder(self):
        """Open a folder containing images and labels"""
        folder_path = filedialog.askdirectory(title="Select Dataset Folder")
        if not folder_path:
            return
        
        # Look for images folder
        images_folder = os.path.join(folder_path, "images")
        if not os.path.exists(images_folder):
            # If no 'images' subfolder, assume all images are in the selected folder
            images_folder = folder_path
        
        # Look for labels folder
        labels_folder = os.path.join(folder_path, "labels")
        if not os.path.exists(labels_folder):
            # If no 'labels' subfolder, assume it's in the parent directory
            parent_dir = os.path.dirname(folder_path)
            potential_labels_folder = os.path.join(parent_dir, "labels")
            if os.path.exists(potential_labels_folder):
                labels_folder = potential_labels_folder
            else:
                # As a last resort, assume labels are in the same folder as images
                labels_folder = images_folder
        
        # Get all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        self.images_list = []
        
        for root, _, files in os.walk(images_folder):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    self.images_list.append(os.path.join(root, file))
        
        if not self.images_list:
            messagebox.showinfo("No Images", f"No images found in {images_folder}")
            return
        
        self.images_list.sort()
        self.current_image_index = 0
        
        # Store the labels folder
        self.labels_folder = labels_folder
        
        # Load the first image
        self.load_image(self.images_list[0])
    
    def load_image(self, image_path):
        """Load an image and its annotations"""
        if not os.path.exists(image_path):
            messagebox.showerror("Error", f"Image not found: {image_path}")
            return
        
        # Reset view parameters
        self.reset_view()
        
        # Update image path
        self.current_image_path = image_path
        
        # Determine label path
        filename = os.path.basename(image_path)
        basename = os.path.splitext(filename)[0]
        self.current_label_path = os.path.join(self.labels_folder, f"{basename}.txt")
        
        # Update UI
        self.image_path_label.config(text=image_path)
        self.image_counter_label.config(text=f"Image: {self.current_image_index+1}/{len(self.images_list)}")
        
        # Load the image
        try:
            # Use cv2 to load the image for better performance
            cv_image = cv2.imread(image_path)
            self.original_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            self.image_height, self.image_width = self.original_image.shape[:2]
            
            # Create a PIL Image
            self.pil_image = Image.fromarray(self.original_image)
            self.photo_image = ImageTk.PhotoImage(self.pil_image)
            
            # Clear canvas and display image
            self.canvas.delete("all")
            self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)
            
            # Configure canvas scrolling
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
            
            # Load annotations
            self.load_annotations()
            
            # Update status
            self.status_bar.config(text=f"Loaded {filename} ({self.image_width}x{self.image_height})")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
    
    def load_annotations(self):
        """Load YOLO format annotations for the current image"""
        self.annotations = []
        self.selected_annotation_index = -1
        
        # Clear annotations listbox
        self.annotations_listbox.delete(0, tk.END)
        
        if not os.path.exists(self.current_label_path):
            self.status_bar.config(text=f"No label file found. Will create new file when saved.")
            self.update_canvas()
            return
        
        try:
            with open(self.current_label_path, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split()
                if len(parts) < 5:
                    continue
                
                class_id = parts[0]
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                
                # Ensure values are within range [0, 1]
                x_center = max(0, min(1, x_center))
                y_center = max(0, min(1, y_center))
                width = max(0, min(1, width))
                height = max(0, min(1, height))
                
                self.annotations.append({
                    'class_id': class_id,
                    'x_center': x_center,
                    'y_center': y_center,
                    'width': width,
                    'height': height
                })
            
            # Update the annotations listbox
            self.update_annotations_listbox()
            
            # Update canvas
            self.update_canvas()
            
            self.status_bar.config(text=f"Loaded {len(self.annotations)} annotations from {os.path.basename(self.current_label_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load annotations: {str(e)}")
    
    def update_annotations_listbox(self):
        """Update the annotations listbox with current annotations"""
        self.annotations_listbox.delete(0, tk.END)
        
        for i, annotation in enumerate(self.annotations):
            class_id = annotation['class_id']
            class_name = self.class_mapping.get(class_id, class_id)
            x_center = annotation['x_center']
            y_center = annotation['y_center']
            width = annotation['width']
            height = annotation['height']
            
            # Calculate absolute coordinates for better display
            abs_width = int(width * self.image_width)
            abs_height = int(height * self.image_height)
            
            self.annotations_listbox.insert(tk.END, f"{class_name} ({abs_width}x{abs_height})")
            
            # Set background color for the annotation in the listbox
            color = self.get_class_color(class_id)
            hex_color = "#{:02x}{:02x}{:02x}".format(*color)
            self.annotations_listbox.itemconfig(i, bg=hex_color)
    
    def update_canvas(self):
        """Update the canvas with current annotations"""
        # Clear all annotation objects on canvas
        self.canvas.delete("annotation")
        
        if not hasattr(self, 'original_image'):
            return
        
        # Apply zoom
        display_width = int(self.image_width * self.zoom_level)
        display_height = int(self.image_height * self.zoom_level)
        
        # Resize the image
        if self.zoom_level != 1.0:
            resized_image = self.pil_image.resize((display_width, display_height), Image.LANCZOS)
            self.photo_image = ImageTk.PhotoImage(resized_image)
            self.canvas.itemconfig(self.canvas_image, image=self.photo_image)
        else:
            self.photo_image = ImageTk.PhotoImage(self.pil_image)
            self.canvas.itemconfig(self.canvas_image, image=self.photo_image)
        
        # Update canvas size
        self.canvas.coords(self.canvas_image, self.pan_offset_x, self.pan_offset_y)
        self.canvas.config(scrollregion=(0, 0, display_width + self.pan_offset_x, display_height + self.pan_offset_y))
        
        # Update zoom label
        self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
        
        # Draw annotations
        for i, annotation in enumerate(self.annotations):
            class_id = annotation['class_id']
            x_center = annotation['x_center'] * self.image_width * self.zoom_level
            y_center = annotation['y_center'] * self.image_height * self.zoom_level
            width = annotation['width'] * self.image_width * self.zoom_level
            height = annotation['height'] * self.image_height * self.zoom_level
            
            # Calculate absolute coordinates
            x1 = x_center - width/2 + self.pan_offset_x
            y1 = y_center - height/2 + self.pan_offset_y
            x2 = x_center + width/2 + self.pan_offset_x
            y2 = y_center + height/2 + self.pan_offset_y
            
            # Get color for this class
            color = self.get_class_color(class_id)
            hex_color = "#{:02x}{:02x}{:02x}".format(*color)
            
            # Draw rectangle
            outline_width = 3 if i == self.selected_annotation_index else 2
            rectangle_id = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=hex_color,
                width=outline_width,
                tags=("annotation", f"box_{i}")
            )
            
            # Get class label (name or ID)
            class_label = self.class_mapping.get(class_id, class_id)
            
            # Draw label background
            text_bg = self.canvas.create_rectangle(
                x1, y1 - 20, x1 + len(class_label) * 8, y1,
                fill=hex_color,
                outline="",
                tags=("annotation", f"label_bg_{i}")
            )
            
            # Draw label text
            text_id = self.canvas.create_text(
                x1 + 5, y1 - 10,
                text=class_label,
                fill="white",
                anchor=tk.W,
                tags=("annotation", f"text_{i}")
            )
    
    def get_class_color(self, class_id):
        """Get a consistent color for a class ID"""
        if class_id not in self.class_colors:
            # Generate a random color, but make it bright enough
            r = (hash(str(class_id) + "r") % 200) + 50
            g = (hash(str(class_id) + "g") % 200) + 50
            b = (hash(str(class_id) + "b") % 200) + 50
            self.class_colors[class_id] = (r, g, b)
        
        return self.class_colors[class_id]
    
    def on_annotation_select(self, event):
        """Handle selection of an annotation in the listbox"""
        if not self.annotations_listbox.curselection():
            self.selected_annotation_index = -1
            self.update_canvas()
            return
        
        self.selected_annotation_index = self.annotations_listbox.curselection()[0]
        
        # Update canvas to highlight selected annotation
        self.update_canvas()
        
        # Show some details in status bar
        if 0 <= self.selected_annotation_index < len(self.annotations):
            annotation = self.annotations[self.selected_annotation_index]
            class_id = annotation['class_id']
            class_name = self.class_mapping.get(class_id, class_id)
            self.status_bar.config(text=f"Selected: {class_name} (ID: {class_id})")
    
    def on_canvas_click(self, event):
        """Handle click on canvas"""
        if not hasattr(self, 'original_image'):
            return
        
        # Convert event coordinates to image coordinates, accounting for zoom and pan
        image_x = (event.x - self.pan_offset_x) / self.zoom_level
        image_y = (event.y - self.pan_offset_y) / self.zoom_level
        
        # Check if click is inside the image
        if not (0 <= image_x < self.image_width and 0 <= image_y < self.image_height):
            return
        
        # Check if click is on an existing annotation
        clicked_annotation = self.find_annotation_at_point(image_x, image_y)
        
        if clicked_annotation is not None:
            # Select this annotation
            self.selected_annotation_index = clicked_annotation
            self.annotations_listbox.selection_clear(0, tk.END)
            self.annotations_listbox.selection_set(clicked_annotation)
            self.annotations_listbox.see(clicked_annotation)
            
            # Start dragging
            self.dragging = True
            self.drag_start_x = image_x
            self.drag_start_y = image_y
            
            # Update canvas to highlight selected annotation
            self.update_canvas()
        else:
            # If in new annotation mode, start drawing a new annotation
            if hasattr(self, 'new_annotation_in_progress') and self.new_annotation_in_progress:
                self.new_annotation_start_x = image_x / self.image_width
                self.new_annotation_start_y = image_y / self.image_height
                self.dragging = True
    
    def on_canvas_drag(self, event):
        """Handle drag on canvas"""
        if not hasattr(self, 'original_image') or not self.dragging:
            return
        
        # Convert event coordinates to image coordinates, accounting for zoom and pan
        image_x = (event.x - self.pan_offset_x) / self.zoom_level
        image_y = (event.y - self.pan_offset_y) / self.zoom_level
        
        # Constrain to image boundaries
        image_x = max(0, min(self.image_width, image_x))
        image_y = max(0, min(self.image_height, image_y))
        
        if hasattr(self, 'new_annotation_in_progress') and self.new_annotation_in_progress:
            # Drawing a new annotation
            curr_x = image_x / self.image_width
            curr_y = image_y / self.image_height
            
            # Calculate rectangle coordinates
            x1 = min(self.new_annotation_start_x, curr_x)
            y1 = min(self.new_annotation_start_y, curr_y)
            x2 = max(self.new_annotation_start_x, curr_x)
            y2 = max(self.new_annotation_start_y, curr_y)
            
            # Update or create the preview rectangle
            if hasattr(self, 'preview_rect') and self.preview_rect:
                # Calculate screen coordinates
                screen_x1 = x1 * self.image_width * self.zoom_level + self.pan_offset_x
                screen_y1 = y1 * self.image_height * self.zoom_level + self.pan_offset_y
                screen_x2 = x2 * self.image_width * self.zoom_level + self.pan_offset_x
                screen_y2 = y2 * self.image_height * self.zoom_level + self.pan_offset_y
                
                self.canvas.coords(self.preview_rect, screen_x1, screen_y1, screen_x2, screen_y2)
            else:
                # Calculate screen coordinates
                screen_x1 = x1 * self.image_width * self.zoom_level + self.pan_offset_x
                screen_y1 = y1 * self.image_height * self.zoom_level + self.pan_offset_y
                screen_x2 = x2 * self.image_width * self.zoom_level + self.pan_offset_x
                screen_y2 = y2 * self.image_height * self.zoom_level + self.pan_offset_y
                
                self.preview_rect = self.canvas.create_rectangle(
                    screen_x1, screen_y1, screen_x2, screen_y2,
                    outline="yellow",
                    width=2,
                    dash=(5, 5),
                    tags="preview"
                )
        elif self.selected_annotation_index >= 0:
            # Moving an existing annotation
            dx = (image_x - self.drag_start_x) / self.image_width
            dy = (image_y - self.drag_start_y) / self.image_height
            
            annotation = self.annotations[self.selected_annotation_index]
            
            # Update center position
            new_x_center = annotation['x_center'] + dx
            new_y_center = annotation['y_center'] + dy
            
            # Ensure annotation stays within image bounds
            half_width = annotation['width'] / 2
            half_height = annotation['height'] / 2
            
            new_x_center = max(half_width, min(1 - half_width, new_x_center))
            new_y_center = max(half_height, min(1 - half_height, new_y_center))
            
            annotation['x_center'] = new_x_center
            annotation['y_center'] = new_y_center
            
            # Update drag start point
            self.drag_start_x = image_x
            self.drag_start_y = image_y
            
            # Update canvas
            self.update_canvas()
    
    def on_canvas_release(self, event):
        """Handle release on canvas"""
        if not self.dragging:
            return
        
        self.dragging = False
        
        if hasattr(self, 'new_annotation_in_progress') and self.new_annotation_in_progress:
            # Finalize new annotation
            if hasattr(self, 'preview_rect') and self.preview_rect:
                # Get coordinates from preview rectangle
                coords = self.canvas.coords(self.preview_rect)
                
                if len(coords) == 4:
                    # Convert screen coordinates to normalized coordinates
                    x1 = (coords[0] - self.pan_offset_x) / (self.zoom_level * self.image_width)
                    y1 = (coords[1] - self.pan_offset_y) / (self.zoom_level * self.image_height)
                    x2 = (coords[2] - self.pan_offset_x) / (self.zoom_level * self.image_width)
                    y2 = (coords[3] - self.pan_offset_y) / (self.zoom_level * self.image_height)
                    
                    # Ensure values are within [0, 1]
                    x1 = max(0, min(1, x1))
                    y1 = max(0, min(1, y1))
                    x2 = max(0, min(1, x2))
                    y2 = max(0, min(1, y2))
                    
                    width = x2 - x1
                    height = y2 - y1
                    x_center = x1 + width/2
                    y_center = y1 + height/2
                    
                    # Check for minimum size
                    if width > 0.01 and height > 0.01:
                        # Choose class
                        class_id = self.prompt_for_class()
                        
                        if class_id is not None:
                            # Add the new annotation
                            self.annotations.append({
                                'class_id': class_id,
                                'x_center': x_center,
                                'y_center': y_center,
                                'width': width,
                                'height': height
                            })
                            
                            # Update UI
                            self.update_annotations_listbox()
                            self.selected_annotation_index = len(self.annotations) - 1
                            self.annotations_listbox.selection_clear(0, tk.END)
                            self.annotations_listbox.selection_set(self.selected_annotation_index)
                            self.annotations_listbox.see(self.selected_annotation_index)
                
                # Clean up
                self.canvas.delete("preview")
                self.preview_rect = None
                self.new_annotation_in_progress = False
                
                # Update canvas
                self.update_canvas()
    
    def prompt_for_class(self):
        """Prompt user to select a class for the annotation"""
        # Get available classes
        class_options = list(set(self.class_mapping.keys()))
        
        # Create a dialog for class selection
        class_dialog = tk.Toplevel(self.root)
        class_dialog.title("Select Class")
        class_dialog.geometry("300x400")
        class_dialog.transient(self.root)
        class_dialog.grab_set()
        
        # Add a search/filter entry
        filter_frame = tk.Frame(class_dialog)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        filter_label = tk.Label(filter_frame, text="Filter:")
        filter_label.pack(side=tk.LEFT)
        
        filter_var = tk.StringVar()
        filter_entry = tk.Entry(filter_frame, textvariable=filter_var)
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Create the listbox with classes
        class_frame = tk.Frame(class_dialog)
        class_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(class_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        class_listbox = tk.Listbox(class_frame, yscrollcommand=scrollbar.set, exportselection=0)
        class_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=class_listbox.yview)
        
        # Populate the listbox
        all_classes = sorted(class_options)
        for class_id in all_classes:
            class_name = self.class_mapping.get(class_id, class_id)
            class_listbox.insert(tk.END, f"{class_id}: {class_name}")
            
            # Set background color
            color = self.get_class_color(class_id)
            hex_color = "#{:02x}{:02x}{:02x}".format(*color)
            idx = class_listbox.size() - 1
            class_listbox.itemconfig(idx, bg=hex_color)
        
        # Add new class button
        add_class_button = tk.Button(class_dialog, text="Add New Class", 
                                     command=lambda: self.add_new_class(class_dialog, class_listbox))
        add_class_button.pack(padx=5, pady=5)
        
        # OK/Cancel buttons
        button_frame = tk.Frame(class_dialog)
        button_frame.pack(fill=tk.X, pady=5)
        
        cancel_button = tk.Button(button_frame, text="Cancel", 
                                 command=lambda: class_dialog.destroy())
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
        ok_button = tk.Button(button_frame, text="OK", 
                             command=lambda: self.on_class_select(class_dialog, class_listbox))
        ok_button.pack(side=tk.RIGHT, padx=5)
        
        # Filter function
        def filter_classes(*args):
            filter_text = filter_var.get().lower()
            class_listbox.delete(0, tk.END)
            
            for class_id in all_classes:
                class_name = self.class_mapping.get(class_id, class_id)
                combined = f"{class_id}: {class_name}".lower()
                
                if filter_text in combined:
                    class_listbox.insert(tk.END, f"{class_id}: {class_name}")
                    
                    # Set background color
                    color = self.get_class_color(class_id)
                    hex_color = "#{:02x}{:02x}{:02x}".format(*color)
                    idx = class_listbox.size() - 1
                    class_listbox.itemconfig(idx, bg=hex_color)
        
        filter_var.trace("w", filter_classes)
        
        # Double-click to select
        class_listbox.bind("<Double-1>", lambda e: self.on_class_select(class_dialog, class_listbox))
        
        # Center the dialog
        class_dialog.update_idletasks()
        width = class_dialog.winfo_width()
        height = class_dialog.winfo_height()
        x = (class_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (class_dialog.winfo_screenheight() // 2) - (height // 2)
        class_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Set focus on the filter entry
        filter_entry.focus_set()
        
        # Store the selected class
        self.selected_class_id = None
        
        # Wait for dialog to close
        class_dialog.wait_window()
        
        return self.selected_class_id
    
    def on_class_select(self, dialog, listbox):
        """Handle class selection"""
        if not listbox.curselection():
            return
        
        selected_item = listbox.get(listbox.curselection()[0])
        class_id = selected_item.split(":")[0].strip()
        
        self.selected_class_id = class_id
        dialog.destroy()
    
    def add_new_class(self, parent_dialog, class_listbox):
        """Add a new class to the class mapping"""
        add_dialog = tk.Toplevel(parent_dialog)
        add_dialog.title("Add New Class")
        add_dialog.transient(parent_dialog)
        add_dialog.grab_set()
        
        # Class ID frame
        id_frame = tk.Frame(add_dialog)
        id_frame.pack(fill=tk.X, padx=10, pady=5)
        
        id_label = tk.Label(id_frame, text="Class ID:")
        id_label.pack(side=tk.LEFT)
        
        id_entry = tk.Entry(id_frame)
        id_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Class name frame
        name_frame = tk.Frame(add_dialog)
        name_frame.pack(fill=tk.X, padx=10, pady=5)
        
        name_label = tk.Label(name_frame, text="Class Name:")
        name_label.pack(side=tk.LEFT)
        
        name_entry = tk.Entry(name_frame)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Buttons
        button_frame = tk.Frame(add_dialog)
        button_frame.pack(fill=tk.X, pady=10)
        
        cancel_button = tk.Button(button_frame, text="Cancel", 
                                 command=lambda: add_dialog.destroy())
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
        def on_add():
            class_id = id_entry.get().strip()
            class_name = name_entry.get().strip()
            
            if not class_id or not class_name:
                messagebox.showwarning("Warning", "Class ID and Name cannot be empty", parent=add_dialog)
                return
            
            # Add to mapping
            self.class_mapping[class_id] = class_name
            
            # Update listbox
            class_listbox.insert(tk.END, f"{class_id}: {class_name}")
            
            # Set background color
            color = self.get_class_color(class_id)
            hex_color = "#{:02x}{:02x}{:02x}".format(*color)
            idx = class_listbox.size() - 1
            class_listbox.itemconfig(idx, bg=hex_color)
            
            # Save config
            self.save_config()
            
            # Close dialog
            add_dialog.destroy()
        
        add_button = tk.Button(button_frame, text="Add", command=on_add)
        add_button.pack(side=tk.RIGHT, padx=5)
        
        # Center the dialog
        add_dialog.update_idletasks()
        width = add_dialog.winfo_width()
        height = add_dialog.winfo_height()
        x = (add_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (add_dialog.winfo_screenheight() // 2) - (height // 2)
        add_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Set focus on the ID entry
        id_entry.focus_set()
        
    def find_annotation_at_point(self, x, y):
        """Find if a point is inside an annotation"""
        for i, annotation in enumerate(self.annotations):
            x_center = annotation['x_center'] * self.image_width
            y_center = annotation['y_center'] * self.image_height
            width = annotation['width'] * self.image_width
            height = annotation['height'] * self.image_height
            
            x1 = x_center - width/2
            y1 = y_center - height/2
            x2 = x_center + width/2
            y2 = y_center + height/2
            
            if x1 <= x <= x2 and y1 <= y <= y2:
                return i
        
        return None
    
    def start_new_annotation(self):
        """Start creating a new annotation"""
        if not hasattr(self, 'original_image'):
            messagebox.showinfo("No Image", "Please open an image first")
            return
        
        self.new_annotation_in_progress = True
        self.status_bar.config(text="Drawing new annotation. Click and drag to create a bounding box.")
    
    def cancel_new_annotation(self):
        """Cancel creating a new annotation"""
        if hasattr(self, 'new_annotation_in_progress') and self.new_annotation_in_progress:
            self.new_annotation_in_progress = False
            
            if hasattr(self, 'preview_rect') and self.preview_rect:
                self.canvas.delete(self.preview_rect)
                self.preview_rect = None
            
            self.status_bar.config(text="New annotation cancelled")
    
    def delete_selected_annotation(self):
        """Delete the selected annotation"""
        if self.selected_annotation_index < 0 or self.selected_annotation_index >= len(self.annotations):
            return
        
        # Delete the annotation
        del self.annotations[self.selected_annotation_index]
        
        # Update UI
        self.update_annotations_listbox()
        self.selected_annotation_index = -1
        self.update_canvas()
        
        self.status_bar.config(text="Annotation deleted")
    
    def save_annotations(self):
        """Save annotations to the YOLO format file"""
        if not self.current_label_path:
            messagebox.showinfo("No Label", "No label file path available")
            return
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.current_label_path), exist_ok=True)
            
            with open(self.current_label_path, 'w') as f:
                for annotation in self.annotations:
                    class_id = annotation['class_id']
                    x_center = annotation['x_center']
                    y_center = annotation['y_center']
                    width = annotation['width']
                    height = annotation['height']
                    
                    # Ensure values are within range [0, 1]
                    x_center = max(0, min(1, x_center))
                    y_center = max(0, min(1, y_center))
                    width = max(0, min(1, width))
                    height = max(0, min(1, height))
                    
                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
            
            self.status_bar.config(text=f"Saved {len(self.annotations)} annotations to {os.path.basename(self.current_label_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save annotations: {str(e)}")
    
    def prev_image(self):
        """Load the previous image in the list"""
        if not self.images_list or self.current_image_index <= 0:
            return
        
        # Save current annotations
        self.save_annotations()
        
        # Load previous image
        self.current_image_index -= 1
        self.load_image(self.images_list[self.current_image_index])
    
    def next_image(self):
        """Load the next image in the list"""
        if not self.images_list or self.current_image_index >= len(self.images_list) - 1:
            return
        
        # Save current annotations
        self.save_annotations()
        
        # Load next image
        self.current_image_index += 1
        self.load_image(self.images_list[self.current_image_index])
    
    def edit_class_mapping(self):
        """Edit the class mapping"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Class Mapping")
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create a frame for the treeview
        tree_frame = tk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create scrollbar
        scrollbar = tk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create treeview
        columns = ("Class ID", "Class Name")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=tree.yview)
        
        # Define headings
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        # Populate treeview
        for class_id, class_name in sorted(self.class_mapping.items()):
            tree.insert("", tk.END, values=(class_id, class_name))
        
        # Buttons frame
        button_frame = tk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Add button
        def add_class():
            add_dialog = tk.Toplevel(dialog)
            add_dialog.title("Add Class")
            add_dialog.transient(dialog)
            add_dialog.grab_set()
            
            # Create input fields
            input_frame = tk.Frame(add_dialog)
            input_frame.pack(padx=10, pady=10)
            
            tk.Label(input_frame, text="Class ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
            id_entry = tk.Entry(input_frame)
            id_entry.grid(row=0, column=1, padx=5, pady=5)
            
            tk.Label(input_frame, text="Class Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
            name_entry = tk.Entry(input_frame)
            name_entry.grid(row=1, column=1, padx=5, pady=5)
            
            # Button frame
            btn_frame = tk.Frame(add_dialog)
            btn_frame.pack(pady=10)
            
            def on_add():
                class_id = id_entry.get().strip()
                class_name = name_entry.get().strip()
                
                if not class_id or not class_name:
                    messagebox.showwarning("Warning", "Class ID and Name cannot be empty", parent=add_dialog)
                    return
                
                # Add to mapping
                self.class_mapping[class_id] = class_name
                
                # Update treeview
                tree.insert("", tk.END, values=(class_id, class_name))
                
                # Save config
                self.save_config()
                
                # Close dialog
                add_dialog.destroy()
            
            tk.Button(btn_frame, text="Add", command=on_add).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="Cancel", command=add_dialog.destroy).pack(side=tk.LEFT, padx=5)
            
            # Center dialog
            add_dialog.update_idletasks()
            width = add_dialog.winfo_width()
            height = add_dialog.winfo_height()
            x = (add_dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (add_dialog.winfo_screenheight() // 2) - (height // 2)
            add_dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            id_entry.focus_set()
        
        tk.Button(button_frame, text="Add", command=add_class).pack(side=tk.LEFT, padx=5)
        
        # Edit button
        def edit_class():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo("Selection", "Please select a class to edit", parent=dialog)
                return
            
            # Get current values
            item = tree.item(selected[0])
            class_id, class_name = item['values']
            
            # Create edit dialog
            edit_dialog = tk.Toplevel(dialog)
            edit_dialog.title("Edit Class")
            edit_dialog.transient(dialog)
            edit_dialog.grab_set()
            
            # Create input fields
            input_frame = tk.Frame(edit_dialog)
            input_frame.pack(padx=10, pady=10)
            
            tk.Label(input_frame, text="Class ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
            id_entry = tk.Entry(input_frame)
            id_entry.insert(0, class_id)
            id_entry.config(state="readonly")  # ID cannot be changed
            id_entry.grid(row=0, column=1, padx=5, pady=5)
            
            tk.Label(input_frame, text="Class Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
            name_entry = tk.Entry(input_frame)
            name_entry.insert(0, class_name)
            name_entry.grid(row=1, column=1, padx=5, pady=5)
            
            # Button frame
            btn_frame = tk.Frame(edit_dialog)
            btn_frame.pack(pady=10)
            
            def on_edit():
                new_name = name_entry.get().strip()
                
                if not new_name:
                    messagebox.showwarning("Warning", "Class Name cannot be empty", parent=edit_dialog)
                    return
                
                # Update mapping
                self.class_mapping[class_id] = new_name
                
                # Update treeview
                tree.item(selected[0], values=(class_id, new_name))
                
                # Update annotations listbox if needed
                self.update_annotations_listbox()
                
                # Save config
                self.save_config()
                
                # Close dialog
                edit_dialog.destroy()
            
            tk.Button(btn_frame, text="Save", command=on_edit).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="Cancel", command=edit_dialog.destroy).pack(side=tk.LEFT, padx=5)
            
            # Center dialog
            edit_dialog.update_idletasks()
            width = edit_dialog.winfo_width()
            height = edit_dialog.winfo_height()
            x = (edit_dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (edit_dialog.winfo_screenheight() // 2) - (height // 2)
            edit_dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            name_entry.focus_set()
        
        tk.Button(button_frame, text="Edit", command=edit_class).pack(side=tk.LEFT, padx=5)
        
        # Delete button
        def delete_class():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo("Selection", "Please select a class to delete", parent=dialog)
                return
            
            # Get class ID
            item = tree.item(selected[0])
            class_id = item['values'][0]
            
            # Confirm deletion
            if messagebox.askyesno("Confirm", f"Are you sure you want to delete class '{class_id}'?", parent=dialog):
                # Delete from mapping
                if class_id in self.class_mapping:
                    del self.class_mapping[class_id]
                
                # Remove from treeview
                tree.delete(selected[0])
                
                # Save config
                self.save_config()
        
        tk.Button(button_frame, text="Delete", command=delete_class).pack(side=tk.LEFT, padx=5)
        
        # Import/Export buttons
        def import_classes():
            file_path = filedialog.askopenfilename(
                title="Import Class Mapping",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
                parent=dialog
            )
            
            if not file_path:
                return
            
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                if 'class_mapping' in data:
                    self.class_mapping = data['class_mapping']
                    
                    # Convert keys from string to int if they were numeric
                    self.class_mapping = {int(k) if k.isdigit() else k: v for k, v in self.class_mapping.items()}
                    
                    # Clear and repopulate treeview
                    for item in tree.get_children():
                        tree.delete(item)
                        
                    for class_id, class_name in sorted(self.class_mapping.items()):
                        tree.insert("", tk.END, values=(class_id, class_name))
                    
                    # Save config
                    self.save_config()
                    
                    messagebox.showinfo("Import", "Class mapping imported successfully", parent=dialog)
                else:
                    messagebox.showwarning("Import", "Invalid file format", parent=dialog)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import: {str(e)}", parent=dialog)
        
        def export_classes():
            file_path = filedialog.asksaveasfilename(
                title="Export Class Mapping",
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
                parent=dialog
            )
            
            if not file_path:
                return
            
            try:
                with open(file_path, 'w') as f:
                    json.dump({'class_mapping': self.class_mapping}, f, indent=2)
                    
                messagebox.showinfo("Export", "Class mapping exported successfully", parent=dialog)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}", parent=dialog)
        
        import_export_frame = tk.Frame(dialog)
        import_export_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(import_export_frame, text="Import", command=import_classes).pack(side=tk.LEFT, padx=5)
        tk.Button(import_export_frame, text="Export", command=export_classes).pack(side=tk.LEFT, padx=5)
        
        # Close button
        tk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
        
        # Center dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def show_context_menu(self, event):
        """Show context menu on right click"""
        if not hasattr(self, 'original_image'):
            return
        
        # Convert event coordinates to image coordinates
        image_x = (event.x - self.pan_offset_x) / self.zoom_level
        image_y = (event.y - self.pan_offset_y) / self.zoom_level
        
        # Check if right-click is on an annotation
        annotation_idx = self.find_annotation_at_point(image_x, image_y)
        
        # Create context menu
        context_menu = tk.Menu(self.root, tearoff=0)
        
        if annotation_idx is not None:
            # Select this annotation
            self.selected_annotation_index = annotation_idx
            self.annotations_listbox.selection_clear(0, tk.END)
            self.annotations_listbox.selection_set(annotation_idx)
            self.annotations_listbox.see(annotation_idx)
            self.update_canvas()
            
            # Menu for annotation
            annotation = self.annotations[annotation_idx]
            class_id = annotation['class_id']
            class_name = self.class_mapping.get(class_id, class_id)
            
            context_menu.add_command(label=f"Annotation: {class_name}", state=tk.DISABLED)
            context_menu.add_separator()
            
            # Change class
            context_menu.add_command(label="Change Class", 
                                    command=lambda: self.change_annotation_class(annotation_idx))
            
            # Delete annotation
            context_menu.add_command(label="Delete Annotation", 
                                    command=lambda: self.delete_selected_annotation())
        else:
            # Menu for canvas
            context_menu.add_command(label="Add Annotation", 
                                    command=lambda: self.start_new_annotation())
            
            context_menu.add_separator()
            
            # Zoom options
            context_menu.add_command(label="Zoom In", command=self.zoom_in)
            context_menu.add_command(label="Zoom Out", command=self.zoom_out)
            context_menu.add_command(label="Reset View", command=self.reset_view)
        
        # Display context menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def change_annotation_class(self, annotation_idx):
        """Change the class of an annotation"""
        if annotation_idx < 0 or annotation_idx >= len(self.annotations):
            return
        
        # Get current class
        annotation = self.annotations[annotation_idx]
        current_class_id = annotation['class_id']
        
        # Prompt for new class
        new_class_id = self.prompt_for_class()
        
        if new_class_id is not None and new_class_id != current_class_id:
            # Update annotation
            annotation['class_id'] = new_class_id
            
            # Update UI
            self.update_annotations_listbox()
            self.update_canvas()
            
            self.status_bar.config(text=f"Changed annotation class from {current_class_id} to {new_class_id}")
    
    def start_pan(self, event):
        """Start panning the image"""
        self.panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
    
    def pan(self, event):
        """Pan the image"""
        if not self.panning:
            return
        
        # Calculate the distance moved
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        
        # Update the pan offset
        self.pan_offset_x += dx
        self.pan_offset_y += dy
        
        # Update the pan start position
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        
        # Update the canvas
        self.update_canvas()
    
    def end_pan(self, event):
        """End panning the image"""
        self.panning = False
    
    def on_mousewheel(self, event):
        """Handle mousewheel event for zooming"""
        if not hasattr(self, 'original_image'):
            return
        
        # Determine scroll direction
        if event.num == 4 or event.delta > 0:  # Scroll up
            self.zoom_in()
        elif event.num == 5 or event.delta < 0:  # Scroll down
            self.zoom_out()
    
    def zoom_in(self):
        """Zoom in on the image"""
        if not hasattr(self, 'original_image'):
            return
        
        self.zoom_level = min(5.0, self.zoom_level * 1.2)
        self.update_canvas()
    
    def zoom_out(self):
        """Zoom out from the image"""
        if not hasattr(self, 'original_image'):
            return
        
        self.zoom_level = max(0.1, self.zoom_level / 1.2)
        self.update_canvas()
    
    def reset_view(self):
        """Reset the view to default"""
        if not hasattr(self, 'original_image'):
            return
        
        self.zoom_level = 1.0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.update_canvas()

def main():
    root = tk.Tk()
    app = YOLOAnnotationEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()