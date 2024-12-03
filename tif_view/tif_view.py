import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np
import threading
import os
os.environ['DISPLAY'] = 'localhost:10.0'

class TiffPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("TIFF Player")
        
        # Initialize attributes
        self.running = False
        self.tiff_images = []
        self.current_frame = 0
        self.fps = 10
        self.min_clip = -65536  # Default to -2^16
        self.max_clip = 65536   # Default to 2^16
        self.average_frame = None
        
        # Create GUI elements
        self.left_canvas = tk.Canvas(root, width=400, height=600, bg="black")
        self.left_canvas.grid(row=0, column=0, sticky="nsew")
        
        self.right_canvas = tk.Canvas(root, width=400, height=600, bg="black")
        self.right_canvas.grid(row=0, column=1, sticky="nsew")
        
        self.control_frame = tk.Frame(root)
        self.control_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        self.open_button = tk.Button(self.control_frame, text="Open TIFF", command=self.open_tiff)
        self.open_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.play_button = tk.Button(self.control_frame, text="Play", command=self.play_movie, state=tk.DISABLED)
        self.play_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.stop_button = tk.Button(self.control_frame, text="Stop", command=self.stop_movie, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.fps_label = tk.Label(self.control_frame, text="FPS:")
        self.fps_label.pack(side=tk.LEFT, padx=5)
        
        self.fps_slider = tk.Scale(self.control_frame, from_=1, to=60, orient=tk.HORIZONTAL, command=self.set_fps)
        self.fps_slider.set(self.fps)
        self.fps_slider.pack(side=tk.LEFT, padx=5)
        
        self.scrollbar = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, command=self.scroll_frames)
        self.scrollbar.grid(row=2, column=0, columnspan=2, sticky="ew")
        
        self.clip_frame = tk.Frame(root)
        self.clip_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        
        self.min_clip_label = tk.Label(self.clip_frame, text="Min Clip:")
        self.min_clip_label.pack(side=tk.LEFT, padx=5)
        
        self.min_clip_slider = tk.Scale(self.clip_frame, from_=-65536, to=65536, orient=tk.HORIZONTAL, command=self.set_min_clip, resolution=100)
        self.min_clip_slider.set(self.min_clip)
        self.min_clip_slider.pack(side=tk.LEFT, padx=5)
        
        self.max_clip_label = tk.Label(self.clip_frame, text="Max Clip:")
        self.max_clip_label.pack(side=tk.LEFT, padx=5)
        
        self.max_clip_slider = tk.Scale(self.clip_frame, from_=-65536, to=65536, orient=tk.HORIZONTAL, command=self.set_max_clip, resolution=100)
        self.max_clip_slider.set(self.max_clip)
        self.max_clip_slider.pack(side=tk.LEFT, padx=5)

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)

    def validate_frame_index(self):
        """Ensure current_frame is within the valid range."""
        if not self.tiff_images:
            self.current_frame = 0
        else:
            self.current_frame = max(0, min(self.current_frame, len(self.tiff_images) - 1))

    def show_loading_box(self, message):
        self.loading_box = tk.Toplevel(self.root)
        self.loading_box.title("Please Wait")
        label = tk.Label(self.loading_box, text=message, padx=20, pady=20)
        label.pack()
        self.loading_box.update()

    def hide_loading_box(self):
        if hasattr(self, 'loading_box') and self.loading_box:
            self.loading_box.destroy()
            self.loading_box = None

    def open_tiff(self):
        file_path = filedialog.askopenfilename(filetypes=[("TIFF Files", "*.tif;*.tiff")])
        if not file_path:
            return
        
        self.show_loading_box("Loading TIFF file...")
        try:
            img = Image.open(file_path)
            self.tiff_images = []
            frames = []
            for i in range(img.n_frames):
                img.seek(i)
                frame = np.array(img, dtype=np.int32)  # Use int32 to support signed ranges
                frames.append(frame)
                self.tiff_images.append(frame)
            
            self.average_frame = np.mean(frames, axis=0).astype(np.int32)
            
            # Compute 5th and 95th percentiles for clipping
            all_pixels = np.concatenate([frame.flatten() for frame in frames])
            self.min_clip = int(np.percentile(all_pixels, 5))
            self.max_clip = int(np.percentile(all_pixels, 95))
            
            # Update sliders
            self.min_clip_slider.set(self.min_clip)
            self.max_clip_slider.set(self.max_clip)
            
            self.scrollbar.config(to=len(self.tiff_images) - 1)
            self.play_button.config(state=tk.NORMAL)
            self.current_frame = 0
            self.display_frame(self.current_frame)
            self.display_average_frame()
        except Exception as e:
            print(f"Error loading TIFF: {e}")
        finally:
            self.hide_loading_box()

    def play_movie(self):
        if not self.tiff_images:
            return

        self.running = True
        self.play_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        def play():
            while self.running:
                self.validate_frame_index()  # Ensure the index is valid
                self.display_frame(self.current_frame)
                self.current_frame = (self.current_frame + 1) % len(self.tiff_images)
                self.scrollbar.set(self.current_frame)

                self.root.after(int(1000 / self.fps))  # Adjust frame rate based on FPS

        threading.Thread(target=play, daemon=True).start()

    def stop_movie(self):
        self.running = False
        self.play_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def display_frame(self, frame_index):
        self.validate_frame_index()  # Ensure the index is valid
        if not self.tiff_images:
            return  # Exit if no frames are loaded
        frame = self.tiff_images[self.current_frame]
        frame = self.apply_clipping(frame)
        frame_image = ImageTk.PhotoImage(image=Image.fromarray(frame))
        
        if hasattr(self, 'left_canvas_image_id') and self.left_canvas_image_id:
            self.left_canvas.itemconfig(self.left_canvas_image_id, image=frame_image)
        else:
            self.left_canvas_image_id = self.left_canvas.create_image(0, 0, anchor=tk.NW, image=frame_image)
        
        self.left_canvas.image = frame_image

    def display_average_frame(self):
        if self.average_frame is None:
            return  # Exit if no average frame is computed

        # Debug: Print stats of the average frame before clipping
        print(f"Average frame min: {self.average_frame.min()}, max: {self.average_frame.max()}")
        
        avg_frame = self.apply_clipping(self.average_frame)
        avg_frame_image = ImageTk.PhotoImage(image=Image.fromarray(avg_frame))
        
        if hasattr(self, 'right_canvas_image_id') and self.right_canvas_image_id:
            self.right_canvas.itemconfig(self.right_canvas_image_id, image=avg_frame_image)
        else:
            self.right_canvas_image_id = self.right_canvas.create_image(0, 0, anchor=tk.NW, image=avg_frame_image)
        
        self.right_canvas.image = avg_frame_image

    def apply_clipping(self, frame):
        # Safeguard to avoid division by zero
        if self.max_clip == self.min_clip:
            return np.zeros_like(frame, dtype=np.uint8)

        # Apply clipping and normalize to [0, 255]
        frame = np.clip(frame, self.min_clip, self.max_clip)
        frame = ((frame - self.min_clip) / (self.max_clip - self.min_clip) * 255).astype(np.uint8)
        return frame

    def scroll_frames(self, value):
        self.current_frame = int(value)
        self.validate_frame_index()
        self.display_frame(self.current_frame)

    def set_fps(self, value):
        self.fps = int(value)

    def set_min_clip(self, value):
        self.min_clip = int(value)
        self.validate_frame_index()
        self.display_frame(self.current_frame)
        self.display_average_frame()

    def set_max_clip(self, value):
        self.max_clip = int(value)
        self.validate_frame_index()
        self.display_frame(self.current_frame)
        self.display_average_frame()

if __name__ == "__main__":
    root = tk.Tk()
    player = TiffPlayer(root)
    root.mainloop()
