import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, List, Any, Optional

class ColoredCheckBox(ttk.Frame):
    """
    A reusable Tkinter component that displays a horizontal row of
    checkbuttons, each with a colored circle and a label.
    It manages its own state and reports changes via a callback.
    """

    def __init__(self, 
                 parent: tk.Widget, 
                 options_data: Dict[str, Dict[str, Any]],
                 on_change_callback: Optional[Callable[[List[str]], None]] = None
                 ) -> None:
        """
        Initializes the ColoredCheckBox widget.
        
        :param parent: The parent widget (e.g., root, a frame).
        :param options_data: The dictionary defining the items.
               Format: {"ItemName": {"color": "#RRGGBB", "default": True/False}}
        :param on_change_callback: A function to call when the selection changes.
                                 It will be passed a list of selected item names.
        """
        # Initialize the parent ttk.Frame
        super().__init__(parent, padding=10)
        
        # Store configuration
        self.options_data: Dict[str, Dict[str, Any]] = options_data
        self.on_change_callback: Optional[Callable[[List[str]], None]] = on_change_callback
        
        # Internal model to hold the widget's state
        self.tk_vars: Dict[str, tk.BooleanVar] = {}

        # Build the UI
        self._build_ui()
        
        # Trigger the initial callback to report the default state
        self._trigger_callback()

    def _build_ui(self) -> None:
        """Private method to create all the internal widgets."""
        
        column_index = 0
        for item_name, data in self.options_data.items():
            
            # --- A. Configure Grid ---
            # The class *is* the main_frame, so we configure its grid.
            # weight=0 packs them closely together as in your example.
            self.grid_columnconfigure(column_index, weight=0)

            # --- B. Create Model Variable ---
            item_var = tk.BooleanVar(value=data.get('default', False))
            self.tk_vars[item_name] = item_var

            # --- C. Create Controller (Click Handler) ---
            toggle_handler = self._create_toggle_handler(item_var)

            # --- D. Create View (Composite Widget) ---
            
            # 1. Container frame for this one item
            item_frame = ttk.Frame(self, style="TFrame")
            item_frame.grid(row=0, column=column_index, sticky="ew", padx=5)

            # 2. The Checkbutton (no text)
            cb = ttk.Checkbutton(
                item_frame,
                variable=item_var,
                text="",
                command=self._trigger_callback # Handles clicks on the box
            )
            cb.pack(side=tk.LEFT)

            # 3. The colored circle
            circle_canvas = tk.Canvas(
                item_frame, 
                width=15, height=15, 
                bd=0, highlightthickness=0
            )
            circle_canvas.create_oval(
                2, 2, 13, 13, 
                fill=data.get("color", "#000000"), 
                outline=data.get("color", "#000000")
            )
            circle_canvas.pack(side=tk.LEFT, padx=(0, 5), pady=2)
            
            # 4. The Label
            label = ttk.Label(item_frame, text=item_name)
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # --- E. Bindings ---
            # Make the circle and label clickable
            circle_canvas.bind("<Button-1>", toggle_handler)
            label.bind("<Button-1>", toggle_handler)
            
            column_index += 1

    def _create_toggle_handler(self, var: tk.BooleanVar) -> Callable[..., None]:
        """Creates a closure to toggle the given BooleanVar and fire callback."""
        def handler(event: Optional[tk.Event] = None) -> None:
            var.set(not var.get())
            self._trigger_callback()
        return handler

    def _trigger_callback(self) -> None:
        """
        Builds a list of selected items and calls the external
        on_change_callback function with that list.
        """
        selected_items: List[str] = []
        for item_name, var in self.tk_vars.items():
            if var.get():
                selected_items.append(item_name)
        
        # Only call the callback if it was provided
        if self.on_change_callback:
            self.on_change_callback(selected_items)

    def get_selected(self) -> List[str]:
        """Public method to get the current list of selected items."""
        return [name for name, var in self.tk_vars.items() if var.get()]

# --- EXAMPLE USAGE ---

if __name__ == "__main__":

    # --- 1. Define the callback function ---
    def print_selection_handler(selected_list: List[str]) -> None:
        """
        This is the function that will be called by the class
        every time the selection changes.
        """
        print("--- Selected Items ---")
        if not selected_list:
            print("None")
        else:
            for item in selected_list:
                print(f"- {item}")
        print("------------------------\n")

    # --- 2. Main Application Setup ---
    root = tk.Tk()
    root.title("ColoredCheckBox Class Example")
    root.geometry("400x100")

    # --- 3. The Model Data ---
    LOG_LEVELS = {
        "Error":   {"color": "#FF4136", "default": True},
        "Warning": {"color": "#FF851B", "default": True},
        "Fatal":   {"color": "#B10DC9", "default": False}
    }

    # --- 4. Instantiate the Class ---
    # We create the checkbar, passing the root, data, and our handler
    checkbar = ColoredCheckBox(
        parent=root, 
        options_data=LOG_LEVELS, 
        on_change_callback=print_selection_handler
    )
    # Pack the checkbar frame itself
    checkbar.pack(fill=tk.X, expand=True, anchor=tk.N)

    # --- 5. Run the Application ---
    root.mainloop()