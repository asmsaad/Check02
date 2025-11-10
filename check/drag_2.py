
# This code allows you to make resizable sections smoothly.

import tkinter as tk
from tkinter import ttk

# Create main window
root = tk.Tk()
root.title("Built-in Resizable Panes")
root.geometry("600x300")

# Create PanedWindow with horizontal orientation
paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Create three resizable sections
frame1 = ttk.Frame(paned, relief="sunken", borderwidth=2)
frame2 = ttk.Frame(paned, relief="sunken", borderwidth=2)  
frame3 = ttk.Frame(paned, relief="sunken", borderwidth=2)
frame4 = ttk.Frame(paned, relief="sunken", borderwidth=2)

# Add some content to visualize each section
ttk.Label(frame1, text="Section 1", anchor="center", background="#e8f4fd").pack(fill="x", pady=0)
ttk.Label(frame2, text="Section 2", anchor="center", background="#f0f8f0").pack(fill="x", pady=0)
ttk.Label(frame3, text="Section 3", anchor="center", background="#fef8e8").pack(fill="x", pady=0)
ttk.Label(frame4, text="Section 4", anchor="center", background="#fea0e8").pack(fill="x", pady=0)

# Add frames to PanedWindow
paned.add(frame1, weight=1)
paned.add(frame2, weight=1)
paned.add(frame3, weight=1)
paned.add(frame4, weight=1)

# # Set initial sash positions (30%, 30%, 40%)
root.update()
width = paned.winfo_width()
if width > 0:
    paned.sashpos(0, int(width * 0.20))
    paned.sashpos(1, int(width * 0.40))
    paned.sashpos(2, int(width * 0.60))
    
    
    
    


class DraggablePanedWindow:
    def __init__(self, paned, frames):
        self.paned = paned
        self.frames = frames
        self.drag_data = {"frame": None, "index": None}
        
        self.setup_drag_bindings()
    
    def setup_drag_bindings(self):
        for i, frame in enumerate(self.frames):
            label = frame.winfo_children()[0]
            label.bind("<ButtonPress-1>", lambda e, idx=i: self.start_drag(e, idx))
            label.bind("<B1-Motion>", self.on_drag)
            label.bind("<ButtonRelease-1>", self.stop_drag)
    
    def start_drag(self, event, index):
        self.drag_data["frame"] = self.frames[index]
        self.drag_data["index"] = index
        print(f"Started dragging Section {index+1}")
    
    def on_drag(self, event):
        if self.drag_data["frame"] is None:
            return
        
        # Get mouse position relative to paned window
        x = event.widget.winfo_rootx() + event.x
        paned_x = self.paned.winfo_rootx()
        relative_x = x - paned_x
        paned_width = self.paned.winfo_width()
        
        if paned_width > 0:
            # Calculate which section we're hovering over
            section_width = paned_width / len(self.frames)
            hover_index = int(relative_x / section_width)
            hover_index = max(0, min(hover_index, len(self.frames) - 1))
            
            current_index = self.drag_data["index"]
            if current_index != hover_index:
                print(f"Swapping Section {current_index+1} with Section {hover_index+1}")
                self.swap_frames(current_index, hover_index)
                self.drag_data["index"] = hover_index
    
    def swap_frames(self, from_index, to_index):
        # Remove all frames
        for frame in self.frames:
            self.paned.remove(frame)
        
        # Swap in list
        self.frames[from_index], self.frames[to_index] = self.frames[to_index], self.frames[from_index]
        
        # Add back in new order
        for frame in self.frames:
            self.paned.add(frame)
    
    def stop_drag(self, event):
        self.drag_data = {"frame": None, "index": None}
        print("Drag ended")

# Usage
frames = [frame1, frame2, frame3, frame4]
drag_manager = DraggablePanedWindow(paned, frames)

    

root.mainloop()