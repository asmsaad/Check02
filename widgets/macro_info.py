import tkinter as tk
from tkinter import ttk, Menu
from typing import Dict, Any, Callable, Optional, Literal

# --- Type Alias for Tooltip Alignment ---
TooltipAlign = Literal[
    "bottom-left",
    "bottom-right",
    "bottom-middle",
    "top-left",
    "top-right",
    "top-middle",
    "left",
    "right",
]


# --- CustomTooltip Class (Unchanged) ---
class CustomTooltip:
    """A minimal, professional Tooltip implementation for modern Tkinter UIs."""

    def __init__(
        self,
        widget: tk.Widget,
        text: str,
        align_widget: tk.Widget,
        align: TooltipAlign = "bottom-left",
    ) -> None:
        self.widget = widget
        self.text = text
        self.align_widget = align_widget
        self.align: TooltipAlign = align
        self.tip_window: Optional[tk.Toplevel] = None

    def showtip(self, event: Optional[tk.Event] = None) -> None:
        if self.tip_window or not self.text:
            return

        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_attributes("-alpha", 0.0)

        label = ttk.Label(
            self.tip_window,
            text=self.text,
            justify=tk.LEFT,
            background="#FFFFE0",
            foreground="#333333",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Segoe UI", 9),
        )
        label.pack(ipadx=4, ipady=4)

        self.tip_window.update_idletasks()

        tip_w = self.tip_window.winfo_width()
        tip_h = self.tip_window.winfo_height()
        widget_x = self.align_widget.winfo_rootx()
        widget_y = self.align_widget.winfo_rooty()
        widget_w = self.align_widget.winfo_width()
        widget_h = self.align_widget.winfo_height()

        x, y = 0, 0
        match self.align:
            case "bottom-left":
                x = widget_x
                y = widget_y + widget_h + 2
            case "bottom-right":
                x = widget_x + widget_w - tip_w
                y = widget_y + widget_h + 2
            case "bottom-middle":
                x = widget_x + (widget_w // 2) - (tip_w // 2)
                y = widget_y + widget_h + 2
            case "top-left":
                x = widget_x
                y = widget_y - tip_h - 2
            case "top-right":
                x = widget_x + widget_w - tip_w
                y = widget_y - tip_h - 2
            case "top-middle":
                x = widget_x + (widget_w // 2) - (tip_w // 2)
                y = widget_y - tip_h - 2
            case "left":
                x = widget_x - tip_w - 2
                y = widget_y + (widget_h // 2) - (tip_h // 2)
            case "right":
                x = widget_x + widget_w + 2
                y = widget_y + (widget_h // 2) - (tip_h // 2)

        self.tip_window.wm_geometry(f"+{x}+{y}")
        self.tip_window.wm_attributes("-alpha", 1.0)

    def hidetip(self, event: Optional[tk.Event] = None) -> None:
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None

    def set_text(self, new_text: str) -> None:
        self.text = new_text


# --- Main Frame Widget (Fixed) ---
class MacroNameDisplayFrame(ttk.Frame):

    def __init__(
        self,
        master: tk.Widget,
        macro_data: Optional[Dict[str, str]],  # Changed to Optional
        tooltip_align: TooltipAlign = "bottom-left",
        **kwargs: Any,
    ) -> None:

        super().__init__(master, relief="flat", borderwidth=0, **kwargs)

        self.copy_button: Optional[ttk.Button] = None
        self._hide_id: Optional[str] = None
        self.is_disabled: bool = False  # Flag for disabled state

        # --- Internal State ---
        self.macro_data: Optional[Dict[str, str]] = {}
        self.macro_name: str = ""
        self.macro_path: str = ""
        self.tooltip: CustomTooltip
        self.tooltip_align: TooltipAlign = tooltip_align

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)

        self._create_widgets()
        self.update_macro(macro_data)

    def _create_widgets(self) -> None:
        style = ttk.Style(self.master)
        style.configure(
            "Copy.TButton",
            font=("Segoe UI", 7),
            foreground="#111111",
            padding=(0, 0, 0, 0),
            
        )
        # Style for disabled labels
        style.configure("Disabled.TLabel", foreground="#999999", font=("Segoe UI", 10))

        self.name_label = ttk.Label(
            self, text="Macro:", font=("Segoe UI", 10, "bold"), foreground="#4A4A4A"
        )
        self.name_label.pack(side=tk.LEFT, padx=(0, 5), )

        self.macro_name_frame: ttk.Frame = ttk.Frame(self, relief="flat", borderwidth=0)
        self.macro_name_frame.pack(side=tk.LEFT, fill="x", expand=True)  # Fill frame

        self.macro_display: ttk.Label = ttk.Label(
            self.macro_name_frame, text="", font=("Segoe UI", 10), foreground="#007ACC"
        )
        # Use grid for the label and button
        self.macro_display.grid(row=0, column=0, sticky="w", )

        self.copy_button = ttk.Button(
            self.macro_name_frame,
            text="⧉",
            command=self._copy_path,
            width=2,
            style="Copy.TButton",
            padding=(2, 0)
        )
        # Place button in grid, then hide it without forgetting its place
        self.copy_button.grid(row=0, column=1, sticky="w", padx=(4, 0))
        self.copy_button.grid_remove()

        self.tooltip = CustomTooltip(
            self.master,
            text="",
            align_widget=self.macro_display,
            align=self.tooltip_align,
        )

        # Bind Events
        self.macro_name_frame.bind("<Enter>", self._on_enter)
        self.macro_name_frame.bind("<Leave>", self._on_leave)
        self.macro_display.bind("<Enter>", self._on_enter)
        self.macro_display.bind("<Leave>", self._on_leave)

    def update_macro(self, macro_data: Optional[Dict[str, str]]) -> None:
        """Updates the display and tooltip with new macro data."""
        if not macro_data:
            self.macro_data = None
            self.macro_name = "N/A"
            self.macro_path = ""  # No path to copy
            self.is_disabled = True  # Set disabled flag
        else:
            self.macro_data = macro_data
            self.macro_name = list(macro_data.keys())[0]
            self.macro_path = list(macro_data.values())[0]
            self.is_disabled = False  # Clear disabled flag

        # Update the UI
        if self.is_disabled:
            self.macro_display.config(text=self.macro_name, style="Disabled.TLabel")
            self.name_label.config(style="Disabled.TLabel")  # Disable "Macro:" label
            self.tooltip.set_text("No macro loaded")
        else:
            self.macro_display.config(text=self.macro_name, style="TLabel")
            self.name_label.config(style="TLabel")  # Re-enable "Macro:" label
            self.tooltip.set_text(f"Full Location: {self.macro_path}")

    def _copy_path(self) -> None:
        """Copies the macro *path* and shows the tick mark."""
        # Do nothing if disabled or no path exists
        if self.is_disabled or not self.macro_path:
            return

        self.clipboard_clear()
        self.clipboard_append(self.macro_path)
        self.update()
        print(f"Copied to clipboard: {self.macro_path}")

        if self.copy_button and self.copy_button.winfo_ismapped():
            original_text = self.copy_button.cget("text")
            self.copy_button.config(text="✓", state=tk.DISABLED)
            self.master.after(
                800,
                lambda: self.copy_button
                and self.copy_button.config(text=original_text, state=tk.NORMAL),
            )

    def _on_enter(self, event: tk.Event) -> None:
        # If disabled, do not show tooltip or copy button
        if self.is_disabled:
            return

        if self._hide_id:
            self.master.after_cancel(self._hide_id)
        self.tooltip.showtip()
        self._show_copy_button()

    def _on_leave(self, event: tk.Event) -> None:
        # No check needed, these functions already handle it
        self._hide_copy_button_after_delay()
        self.tooltip.hidetip()

    def _show_copy_button(self) -> None:
        # Use grid() to show the button without causing flicker
        if self.copy_button and self.copy_button.winfo_ismapped() == 0:
            self.copy_button.grid()  # Re-show the button
            self.copy_button.bind("<Enter>", self._on_button_enter)
            self.copy_button.bind("<Leave>", self._on_button_leave)

    def _on_button_enter(self, event: tk.Event) -> None:
        if self._hide_id:
            self.master.after_cancel(self._hide_id)

    def _on_button_leave(self, event: tk.Event) -> None:
        self._hide_copy_button_after_delay()

    def _hide_copy_button_after_delay(self, event: Optional[tk.Event] = None) -> None:
        self._hide_id = self.master.after(50, self._remove_copy_button)

    def _remove_copy_button(self) -> None:
        # Use grid_remove() to hide without changing layout
        if self.copy_button and self.copy_button.winfo_ismapped():
            self.copy_button.grid_remove()


# --- Main Application Setup (Modified for Demo) ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Dynamic UI Example (Functional)")
    root.geometry("600x250")  # Made taller

    # --- Initial Data ---
    initial_macro_data = {
        "dc_asdfk__asjdfkk": "/Users/Developer/Projects/Automation/dc_asdfk__asjdfkk.py"
    }
    
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("MacroNameDisplayFrame.TFrame", background="red")
    style.configure("MacroNameDisplayFrame.TLabel", background="red")

    macro_frame = MacroNameDisplayFrame(
        root,
        # macro_data=initial_macro_data,
        macro_data=None,
        tooltip_align="bottom-left",
        style="MacroNameDisplayFrame.TFrame"
    )
    macro_frame.pack(pady=20, padx=20, fill="x")

    # --- Data for Update ---
    new_macro_data = {"new_macro_name_123": "C:/Windows/System32/new_macro_name_123.py"}

    # --- Button Frame ---
    button_frame = ttk.Frame(root, style="MacroNameDisplayFrame.TLabel")
    button_frame.pack(pady=10)

    def on_update_click():
        print("--- Updating Macro Data ---")
        macro_frame.update_macro(new_macro_data)

    def on_load_empty_click():
        print("--- Loading Empty Data ---")
        macro_frame.update_macro(None)  # Pass None to disable

    update_button = ttk.Button(
        button_frame, text="Update Macro Data", command=on_update_click
    )
    update_button.pack(side=tk.LEFT, padx=5)

    empty_button = ttk.Button(
        button_frame, text="Load Empty", command=on_load_empty_click
    )
    empty_button.pack(side=tk.LEFT, padx=5)

    ttk.Label(
        root,
        text="Hover over macro name for tooltip. Click Note: Hover is disabled when no macro is loaded.",
        font=("Segoe UI", 9, "italic"),
    ).pack(pady=5)

    root.mainloop()
