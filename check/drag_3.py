import tkinter as tk
from tkinter import ttk

# -------------------------------
# Main Application Window
# -------------------------------
root = tk.Tk()
root.title("Tkinter Excel-like Grid Prototype")
root.geometry("800x400")

# -------------------------------
# Scrollbars
# -------------------------------
v_scroll = tk.Scrollbar(root, orient=tk.VERTICAL)
v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

h_scroll = tk.Scrollbar(root, orient=tk.HORIZONTAL)
h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

# -------------------------------
# Top PanedWindow: Header
# -------------------------------
header_pane = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
header_pane.pack(side=tk.TOP, fill=tk.X)

# Frozen Header
header_left_canvas = tk.Canvas(header_pane, width=150, height=30, bg="lightgray")
header_left_frame = tk.Frame(header_left_canvas, bg="lightgray")
header_left_canvas.create_window((0, 0), window=header_left_frame, anchor="nw")
header_pane.add(header_left_canvas, weight=0)

# Scrollable Header
header_right_canvas = tk.Canvas(header_pane, height=30, bg="lightblue")
header_right_frame = tk.Frame(header_right_canvas, bg="lightblue")
header_right_canvas.create_window((0, 0), window=header_right_frame, anchor="nw")
header_pane.add(header_right_canvas, weight=1)

# -------------------------------
# Bottom PanedWindow: Body
# -------------------------------
body_pane = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
body_pane.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Frozen Columns
body_left_canvas = tk.Canvas(body_pane, width=150, bg="lightgray", yscrollcommand=v_scroll.set)
body_left_frame = tk.Frame(body_left_canvas, bg="lightgray")
body_left_canvas.create_window((0, 0), window=body_left_frame, anchor="nw")
body_pane.add(body_left_canvas, weight=0)

# Scrollable Columns
body_right_canvas = tk.Canvas(body_pane, bg="white", yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
body_right_frame = tk.Frame(body_right_canvas, bg="white")
body_right_canvas.create_window((0, 0), window=body_right_frame, anchor="nw")
body_pane.add(body_right_canvas, weight=1)









# -------------------------------
# Fill header with buttons
# -------------------------------
for i in range(3):
    tk.Button(header_left_frame, text=f"Frozen {i+1}", width=15).grid(row=0, column=i, padx=1, pady=1)

for i in range(10):
    tk.Button(header_right_frame, text=f"Col {i+1}", width=15).grid(row=0, column=i, padx=1, pady=1)

# Fill body with buttons
for r in range(30):
    for c in range(3):
        tk.Button(body_left_frame, text=f"L{r+1},{c+1}", width=15).grid(row=r, column=c, padx=1, pady=1)
    for c in range(10):
        tk.Button(body_right_frame, text=f"R{r+1},{c+1}", width=15).grid(row=r, column=c, padx=1, pady=1)
        

# -------------------------------
# Update scroll regions
# -------------------------------
def update_scroll_regions(event=None):
    body_left_canvas.configure(scrollregion=body_left_canvas.bbox("all"))
    body_right_canvas.configure(scrollregion=body_right_canvas.bbox("all"))
    header_right_canvas.configure(scrollregion=header_right_canvas.bbox("all"))

body_left_frame.bind("<Configure>", update_scroll_regions)
body_right_frame.bind("<Configure>", update_scroll_regions)
header_right_frame.bind("<Configure>", update_scroll_regions)

# -------------------------------
# Synchronize scrolling
# -------------------------------
def on_vertical_scroll(*args):
    body_left_canvas.yview(*args)
    body_right_canvas.yview(*args)

v_scroll.config(command=on_vertical_scroll)

def on_horizontal_scroll(*args):
    body_right_canvas.xview(*args)
    header_right_canvas.xview(*args)

h_scroll.config(command=on_horizontal_scroll)

# Sync vertical scrolling with mouse wheel
def _on_mousewheel(event):
    delta = int(-1*(event.delta/120))
    body_left_canvas.yview_scroll(delta, "units")
    body_right_canvas.yview_scroll(delta, "units")
    return "break"





# -------------------------------
# Synchronize PanedWindow sash
# -------------------------------

def sync_sash_from_header(event=None):
    """Sync body pane sash when header pane is dragged"""
    body_pane.sashpos(0, header_pane.sashpos(0))


def sync_sash_from_body(event=None):
    """Sync header pane sash when body pane is dragged"""
    header_pane.sashpos(0, body_pane.sashpos(0))


# Bind dragging events
header_pane.bind("<B1-Motion>", sync_sash_from_header)
body_pane.bind("<B1-Motion>", sync_sash_from_body)




body_left_canvas.bind_all("<MouseWheel>", _on_mousewheel)
body_right_canvas.bind_all("<MouseWheel>", _on_mousewheel)

# -------------------------------
# Run App
# -------------------------------
root.mainloop()
