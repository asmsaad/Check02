import tkinter as tk
from tkinter import ttk, messagebox

class WaverTopLevelWindow:
    """
    A reusable Modal Window class.
    - Blocks interaction with the main window while open.
    - Centers itself over the parent window.
    - Handles closing with a confirmation dialog.
    - Prevents multiple instances (lifts existing one if clicked again).
    """

    def __init__(self, parent: tk.Tk, title: str = "Modal Window"):
        self.parent = parent
        self.title = title
        self._window = None  # Keep track of the window instance

    def show(self):
        """Displays the window. If already open, brings it to front."""
        
        # 1. Check if window already exists
        if self._window is not None and self._window.winfo_exists():
            self._window.lift()  # Bring to top
            self._window.focus_force() # Force focus
            self._center_window() # Re-center just in case parent moved
            return

        # 2. Create new Toplevel
        self._window = tk.Toplevel(self.parent)
        self._window.title(self.title)
        
        # 3. OS Compatibility & Modal Behavior setup
        self._window.transient(self.parent) # Tell OS this belongs to parent (keeps it on top)
        self._window.grab_set()             # MAKE MODAL: Disables interaction with parent
        
        # 4. Handle the "X" button click
        self._window.protocol("WM_DELETE_WINDOW", self._on_close)

        # 5. Add content (Example)
        self._setup_ui()

        # 6. Center relative to parent
        self._center_window()
        
        # 7. Wait for window to close before running code after .show() (Optional, but good for logic)
        self.parent.wait_window(self._window)

    def _setup_ui(self):
        """Internal method to build the window content."""
        frame = tk.Frame(self._window, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="This is a modal window.\nYou cannot click the main window.", font=("Segoe UI", 10)).pack(pady=10)
        ttk.Button(frame, text="Close", command=self._on_close).pack(pady=10)

    def _center_window(self):
        """Calculates center position relative to the parent window."""
        self._window.update_idletasks() # Ensure geometry is calculated
        
        # Get Parent dimensions and position
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Get Self dimensions
        width = self._window.winfo_width()
        height = self._window.winfo_height()

        # Calculate position
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)

        # Apply geometry
        self._window.geometry(f"+{x}+{y}")

    def _on_close(self):
        """Handles the closing confirmation."""
        # Note: We use parent=self._window so the popup appears over the modal, not the root
        confirm = messagebox.askyesno("Confirm Exit", "Do you want to close this window?", parent=self._window)
        
        if confirm:
            self._window.grab_release() # Release the lock on main window
            self._window.destroy()      # Destroy the toplevel
            self._window = None         # Reset instance tracker

# ----------------------------------------------------------------
# Driver Code
# ----------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Main Application")
    root.geometry("600x400")

    # Initialize the class (does not show window yet)
    modal_app = WaverTopLevelWindow(root, title="My Popup")
    #modal_app._window

    def open_window():
        print("Button Clicked: Attempting to open modal...")
        modal_app.show()
        print("Modal Closed. Main window is workable again.")

    # Main UI
    tk.Label(root, text="Main Window (Root)", font=("Arial", 14, "bold")).pack(pady=50)
    
    btn = ttk.Button(root, text="Open Modal Window", command=open_window)
    btn.pack(pady=20)

    root.mainloop()