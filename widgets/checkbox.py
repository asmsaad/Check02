import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, List, Any, Optional, Literal


class ColoredCheckBox(ttk.Frame):
    """
    A reusable Tkinter component that displays a horizontal row of
    checkbuttons, each with a colored circle and a label.

    Manages its own state and reports changes via a callback.
    """

    def __init__(
        self,
        parent: tk.Widget,
        options_data: Dict[str, Dict[str, Any]],
        on_change_callback: Optional[Callable[[List[str]], None]] = None,
    ) -> None:
        """
        Initializes the ColoredCheckBox widget.

        Args:
            parent: The parent widget (e.g., root, a frame).
            options_data: The dictionary defining the items.
                Format: {"ItemName": {"color": "#RRGGBB", "default": True/False}}
            on_change_callback: A function to call when the selection changes.
                It will be passed a list of selected item names.
        """
        super().__init__(parent)

        self.options_data: Dict[str, Dict[str, Any]] = options_data
        self.on_change_callback: Optional[Callable[[List[str]], None]] = (
            on_change_callback
        )
        self.tk_vars: Dict[str, tk.BooleanVar] = {}

        self._build_ui()
        self._trigger_callback()

    def _build_ui(self) -> None:
        """Private method to create all the internal widgets."""
        column_index = 0
        for item_name, data in self.options_data.items():
            # Create and place the widget for this item
            self._create_checkbox_item(item_name, data, column_index)
            column_index += 1

    def _create_checkbox_item(
        self, item_name: str, data: Dict[str, Any], column_index: int
    ) -> None:
        """
        Creates and places a single checkbox item in the specified column.
        This is refactored to allow adding items dynamically.
        """
        self.grid_columnconfigure(column_index, weight=0)

        # Create and store the variable
        item_var = tk.BooleanVar(value=data.get("default", False))
        self.tk_vars[item_name] = item_var

        toggle_handler = self._create_toggle_handler(item_var)

        # Create the widgets
        item_frame = ttk.Frame(self, )
        item_frame.grid(row=0, column=column_index, sticky="ew", padx=5)

        cb = ttk.Checkbutton(
            item_frame,
            variable=item_var,
            text="",
            command=self._trigger_callback,
        )
        cb.pack(side=tk.LEFT)

        circle_canvas = tk.Canvas(
            item_frame, width=15, height=15, bd=0, highlightthickness=0
        )
        circle_canvas.create_oval(
            2,
            2,
            13,
            13,
            fill=data.get("color", "#000000"),
            outline=data.get("color", "#000000"),
        )
        circle_canvas.pack(side=tk.LEFT, padx=(0, 5), pady=2)

        label = ttk.Label(item_frame, text=item_name)
        label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Make the circle and label clickable to toggle
        circle_canvas.bind("<Button-1>", toggle_handler)
        label.bind("<Button-1>", toggle_handler)

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
        selected_items: List[str] = [
            name for name, var in self.tk_vars.items() if var.get()
        ]

        if self.on_change_callback:
            self.on_change_callback(selected_items)

    def get_selected(self) -> List[str]:
        """Public method to get the current list of selected items."""
        return [name for name, var in self.tk_vars.items() if var.get()]

    def update_options(
        self,
        new_options_data: Dict[str, Dict[str, Any]],
        mode: Literal["replace", "merge"] = "replace",
    ) -> None:
        """
        Updates the component with a new set of options.

        Args:
            new_options_data: The new dictionary defining the items.
            mode: 'replace' (default) clears all old items.
                  'merge' adds new items while keeping existing ones and their state.
        """
        if mode == "replace":
            # 1. Clear all old widgets from this frame
            for widget in self.winfo_children():
                widget.destroy()

            # 2. Reset the internal state
            self.tk_vars = {}
            self.options_data = new_options_data

            # 3. Rebuild the UI with the new data
            self._build_ui()

        elif mode == "merge":
            has_new_items = False
            # Start new items at the end of the current grid
            column_index = len(self.options_data)

            for item_name, data in new_options_data.items():
                if item_name not in self.options_data:  # Only add if new
                    has_new_items = True
                    self.options_data[item_name] = data
                    self._create_checkbox_item(item_name, data, column_index)
                    column_index += 1

            if not has_new_items:
                return  # No changes, no need to fire callback

        # Fire the callback in both cases to show the new/full state
        self._trigger_callback()


if __name__ == "__main__":

    def print_selection_handler(selected_list: List[str]) -> None:
        """Callback function to print the new selection."""
        print("--- Selected Items ---")
        if not selected_list:
            print("None")
        else:
            for item in selected_list:
                print(f"- {item}")
        print("------------------------\n")

    root = tk.Tk()
    root.title("ColoredCheckBox Class Example")
    root.geometry("600x150")

    LOG_LEVELS = {
        "Error": {"color": "#FF4136", "default": True},
        "Warning": {"color": "#FF851B", "default": True},
        "Fatal": {"color": "#B10DC9", "default": False},
    }

    REPLACE_LEVELS = {
        "Info": {"color": "#7FDBFF", "default": True},
        "Debug": {"color": "#0074D9", "default": False},
    }

    MERGE_LEVELS = {
        "Critical": {"color": "#85144b", "default": True},
        "Verbose": {"color": "#aaaaaa", "default": False},
        "Error": {"color": "#000000", "default": False},  # This will be ignored
    }

    checkbar = ColoredCheckBox(
        parent=root, options_data=LOG_LEVELS, on_change_callback=print_selection_handler
    )
    checkbar.pack()

    button_frame = ttk.Frame(root)
    button_frame.pack(pady=10)

    replace_button = ttk.Button(
        button_frame,
        text="Replace with (Info, Debug)",
        command=lambda: checkbar.update_options(REPLACE_LEVELS, mode="replace"),
    )
    replace_button.pack(side=tk.LEFT, padx=5)

    merge_button = ttk.Button(
        button_frame,
        text="Merge (Critical, Verbose)",
        command=lambda: checkbar.update_options(MERGE_LEVELS, mode="merge"),
    )
    merge_button.pack(side=tk.LEFT, padx=5)

    root.config(bg="red")
    root.mainloop()
