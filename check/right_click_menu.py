import tkinter as tk
from tkinter import ttk

# --- Main Application Setup ---
root = tk.Tk()
root.geometry("300x200")
root.title("Menu at Widget Example")

# --- The Menu ---
# We still use tearoff=0 to disable the "tear-off" feature.
context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="Cut", command=lambda: print("Cut clicked"))
context_menu.add_command(label="Copy", command=lambda: print("Copy clicked"))
context_menu.add_command(label="Paste", command=lambda: print("Paste clicked"))
context_menu.add_separator()
context_menu.add_command(label="Delete", command=lambda: print("Delete clicked"))


# --- The Event Handler ---
def show_menu_at_widget(event):
    """
    Displays the context menu aligned to the bottom-left
    of the widget that was clicked.
    """
    
    # Get the widget that triggered the event
    widget = event.widget

    # Get the widget's coordinates relative to the screen
    x = widget.winfo_rootx()
    y = widget.winfo_rooty()

    # Get the widget's height
    widget_height = widget.winfo_height()

    # Calculate the position for the menu:
    # x: aligned with the widget's left edge
    # y: placed just below the widget's bottom edge
    menu_x = x
    menu_y = y + widget_height

    try:
        # Post the menu at the calculated (x, y) screen coordinates
        context_menu.post(menu_x, menu_y)
    finally:
        # Release the grab to ensure proper menu behavior
        context_menu.grab_release()


# --- The Widget ---
action_button = tk.Button(root, text="Right-Click Me!", height=50)
action_button.pack(pady=50, padx=50) # Added more padding to see effect

# --- The Binding ---
# <Button-3> is the standard event for a right-mouse-click
action_button.bind("<Button-3>", show_menu_at_widget)

# Start the application
root.mainloop()