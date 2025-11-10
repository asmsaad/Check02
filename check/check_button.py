import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Toggle Button Example")

# Use 'clam' theme so colors are visible
style = ttk.Style()
# style.theme_use('clam')

# Track toggle state
is_selected = tk.BooleanVar(value=False)

# Configure two styles: selected and unselected
style.configure("Normal.TButton",  foreground="black",relief="sunken")
style.configure("Selected.TButton",  foreground="blue", relief="raised")

def toggle():
    if is_selected.get():
        # Currently selected → unselect
        button.config(style="Normal.TButton")
        is_selected.set(False)
    else:
        # Currently unselected → select
        button.config(style="Selected.TButton")
        is_selected.set(True)
    # if is_selected.get():
    #     button.config(relief="sunken")
    # else:
    #     button.config(relief="raised")


# Create the button
button = ttk.Button(root, text="Toggle Me", style="Normal.TButton", command=toggle)
button.pack(padx=20, pady=20)

root.mainloop()
