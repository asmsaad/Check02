import tkinter as tk
from tkinter import Menu, filedialog, Toplevel, Label, Entry
import os # Used for managing file paths

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter Menu Application")
        self.root.geometry("600x400")

        # Store the last browsed path
        self.last_browsed_path = os.path.expanduser("~") # Start at home directory

        # Create the main menu bar
        self.menubar = Menu(self.root)
        self.root.config(menu=self.menubar)

        # --- Create File Menu ---
        self.file_menu = Menu(self.menubar, tearoff=0)
        # The 'underline=0' part underlines the first character (index 0), which is 'F'
        self.menubar.add_cascade(label="File", menu=self.file_menu, underline=0) # F
        self.file_menu.add_command(label="Load", accelerator="Ctrl+L", command=self.load_file, underline=0) # L
        self.file_menu.add_command(label="Export", command=self.export_file, underline=0) # E

        # Bind the shortcut for Load
        self.root.bind("<Control-l>", self.load_file) # Use lowercase 'l'

        # --- Create Edit Menu ---
        self.edit_menu = Menu(self.menubar, tearoff=0)
        # 'underline=0' underlines the 'E'
        self.menubar.add_cascade(label="Edit", menu=self.edit_menu, underline=0) # E
        self.edit_menu.add_command(label="Copy", command=lambda: print("Clicked Copy"), underline=0) # C
        self.edit_menu.add_command(label="Paste", command=lambda: print("Clicked Paste"), underline=0) # P
        self.edit_menu.add_command(label="Cut", command=lambda: print("Clicked Cut"), underline=0) # u
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Preference", command=self.open_preference_window, underline=0) # P

        # --- Create View Menu ---
        self.view_menu = Menu(self.menubar, tearoff=0)
        # 'underline=0' underlines the 'V'
        self.menubar.add_cascade(label="View", menu=self.view_menu, underline=0) # V
        self.view_menu.add_command(label="Pin priority", command=lambda: print("Clicked Pin priority"), underline=0) # P
        self.view_menu.add_command(label="Category priority", command=lambda: print("Clicked Category priority"), underline=0) # C
        self.view_menu.add_command(label="Rule priority", command=lambda: print("Clicked Rule priority"), underline=0) # R
        self.view_menu.add_command(label="Tabular view", command=lambda: print("Clicked Tabular view"), underline=0) # T

        # --- Create Connection Menu ---
        self.connection_menu = Menu(self.menubar, tearoff=0)
        # 'underline=0' underlines the 'C'
        self.menubar.add_cascade(label="Connection", menu=self.connection_menu, underline=0) # C
        
        # Create a sub-menu for API Settings
        self.api_settings_menu = Menu(self.connection_menu, tearoff=0)
        self.connection_menu.add_cascade(label="API settings", menu=self.api_settings_menu, underline=0) # A
        
        # Add items to the sub-menu
        self.api_settings_menu.add_command(label="Setting 1", command=lambda: print("Clicked API Setting 1"), underline=8) # 1
        self.api_settings_menu.add_command(label="Setting 2", command=lambda: print("Clicked API Setting 2"), underline=8) # 2
        self.api_settings_menu.add_command(label="Setting 3", command=lambda: print("Clicked API Setting 3"), underline=8) # 3
        self.api_settings_menu.add_command(label="Setting 4", command=lambda: print("Clicked API Setting 4"), underline=8) # 4

        # --- Create Window Menu ---
        self.window_menu = Menu(self.menubar, tearoff=0)
        # 'underline=0' underlines the 'W'
        self.menubar.add_cascade(label="Window", menu=self.window_menu, underline=0) # W
        self.window_menu.add_command(label="Window settings", command=lambda: self.open_modal_window("Window settings"), underline=0) # W
        self.window_menu.add_command(label="Tab settings", command=lambda: self.open_modal_window("Tab settings"), underline=0) # T
        self.window_menu.add_separator()
        self.window_menu.add_command(label="Clear all tab", command=lambda: print("Clicked Clear all tab"), underline=0) # C
        self.window_menu.add_command(label="Close current tab", command=lambda: print("Clicked Close current tab"), underline=6) # c

        # --- Create Help Menu ---
        self.help_menu = Menu(self.menubar, tearoff=0)
        # 'underline=0' underlines the 'H'
        self.menubar.add_cascade(label="Help", menu=self.help_menu, underline=0) # H
        self.help_menu.add_command(label="Manual", command=lambda: print("Clicked Manual"), underline=0) # M
        self.help_menu.add_command(label="System info", command=lambda: print("Clicked System info"), underline=0) # S

        self.help_menu.add_command(label="What's new", command=lambda: print("Clicked What's new"), underline=0) # W
        self.help_menu.add_command(label="About", command=lambda: print("Clicked About"), underline=0) # A

    def load_file(self, event=None): # event=None allows it to be called by button or binding
        """
        Opens a file dialog to select a YAML file.
        Prints the selected file path and remembers the last directory.
        """
        filepath = filedialog.askopenfilename(
            initialdir=self.last_browsed_path,
            title="Select a YAML file",
            filetypes=(("YAML files", "*.yaml *.yml"), ("All files", "*.*"))
        )
        
        if filepath: # Check if a file was actually selected
            print(f"Selected file: {filepath}")
            # Update the last browsed path to the directory of the selected file
            self.last_browsed_path = os.path.dirname(filepath)
        else:
            print("File selection cancelled.")

    def export_file(self):
        """Prints a message when Export is clicked."""
        print("Clicking on Export")

    def open_modal_window(self, title):
        """
        Opens a generic modal (blocking) Toplevel window.
        """
        # Create the Toplevel window
        dialog = Toplevel(self.root)
        dialog.title(title)
        
        # Add some example content
        Label(dialog, text=f"This is the {title} window.").pack(padx=20, pady=10)
        Label(dialog, text="Some settings could go here.").pack(padx=20, pady=5)
        Entry(dialog).pack(padx=20, pady=5)
        
        # --- Make the dialog modal ---
        dialog.transient(self.root)  # Keep dialog on top
        dialog.grab_set()           # Direct all events to this dialog
        
        # Center the dialog
        self.center_window(dialog, 300, 150)

        self.root.wait_window(dialog)  # Wait until the dialog is closed

    def open_preference_window(self):
        """
        Opens the specific 'Preference' modal window.
        """
        # Create the Toplevel window
        dialog = Toplevel(self.root)
        dialog.title("Preferences")
        
        # Add some example entry fields
        Label(dialog, text="Setting 1:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        Entry(dialog).grid(row=0, column=1, padx=10, pady=5)
        
        Label(dialog, text="Setting 2:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        Entry(dialog).grid(row=1, column=1, padx=10, pady=5)

        # --- Make the dialog modal ---
        dialog.transient(self.root)  # Keep dialog on top
        dialog.grab_set()           # Direct all events to this dialog

        # Center the dialog
        self.center_window(dialog, 250, 100)
        
        self.root.wait_window(dialog)  # Wait until the dialog is closed

    def center_window(self, window, width, height):
        """
        Centers a Toplevel window on the root window.
        """
        # Ensure window size is calculated
        window.update_idletasks() 
        
        # Get root window position and size
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        # Calculate position for the dialog
        pos_x = root_x + (root_width // 2) - (width // 2)
        pos_y = root_y + (root_height // 2) - (height // 2)

        # Set the dialog's geometry
        window.geometry(f"{width}x{height}+{pos_x}+{pos_y}")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

