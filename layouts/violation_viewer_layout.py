import tkinter as tk
from tkinter import ttk
from typing import Literal
from tkinter import scrolledtext

# Type alias for self-documenting code
PanelPosition = Literal["bottom", "right"]


class ViolationViewerLayoutFrame(ttk.Frame):
    """A styled Tkinter layout component with toggleable and movable panel."""

    def __init__(self, root: tk.Widget) -> None:
        """Initialize the ViolationViewerLayoutFrame layout."""
        super().__init__(root, style="ViolationViewerLayoutFrame.TFrame")

        # Panel State
        self.panel_visible: bool = True
        self.panel_position: PanelPosition = "bottom"

        # Initialize layout
        self._init_layout()

    def _init_layout(self) -> None:
        """Create and configure the main layout."""

        # --- Top Frames ---
        self.table_top_frame = ttk.Frame(self, style="Toolbar.TFrame")
        self.table_top_frame.pack(fill="x", side="top")
        # ttk.Button(self.table_top_frame,text="text").pack()

        # --- PanedWindow Layout (must be packed last) ---
        self.master_pane = ttk.PanedWindow(self, orient="vertical")
        self.master_pane.pack(fill="both", expand=True)

        # --- PanedWindow Children ---
        self.body_pane = ttk.PanedWindow(self.master_pane, orient="horizontal")
        self.bottom_pane = ttk.PanedWindow(self.master_pane, orient="horizontal")

        self.master_pane.add(self.body_pane, weight=1)
        self.master_pane.add(self.bottom_pane, weight=0)

        # --- Body Frames ---
        self.body_left = ttk.Frame(
            self.body_pane, width=200, style="Section.TFrame", padding=(3, 3)
        )
        self.body_right = ttk.Frame(
            self.body_pane, width=550, style="Section.TFrame", padding=(3, 3)
        )
        
        self.filter_right = ttk.Frame(
            self.body_pane, width=200, style="Section.TFrame", padding=(3, 3)
        )
        
        self.body_pane.add(self.body_left)
        self.body_pane.add(self.body_right)
        self.body_pane.add(self.filter_right)

        # --- Bottom Frame ---
        self.bottom_frame = ttk.Frame(
            self.bottom_pane, style="Section.TFrame",
            
        )
        self.bottom_pane.add(self.bottom_frame)

        # # --- Dummy Content ---
        self.details_view = scrolledtext.ScrolledText(self.bottom_frame, heigh=10)
        self.details_view.pack(fill="both", expand=True)
        # self.b_ = tk.Frame(self.bottom_frame, background="red", height=100)
        # self.b_.pack(fill="both", expand=True, padx=5, pady=5)

        self.toolbar = ttk.Frame(self, style="Toolbar.TFrame")
        self.toolbar.pack(fill="x", side="top")

        # --- Toolbar Widgets ---
        self.toggle_btn = ttk.Button(
            self.toolbar,
            text="Hide Panel",
            width=15,
            style="ViolationDetails.TButton",
            command=self.toggle_panel,
        )
        self.toggle_btn.pack(side="left", padx=5, pady=5)

        self.move_btn = ttk.Button(
            self.toolbar,
            text="Move Panel Right",
            width=20,
            style="ViolationDetails.TButton",
            command=self.move_panel,
        )
        self.move_btn.pack(side="left", padx=5, pady=5)

    def toggle_panel(self) -> None:
        """Show or hide the bottom/right panel."""
        if self.panel_visible:
            if self.panel_position == "bottom":
                self.master_pane.forget(self.bottom_pane)
            else:
                self.body_pane.forget(self.bottom_pane)
            self.toggle_btn.config(text="Show Panel")
            self.panel_visible = False
        else:
            if self.panel_position == "bottom":
                self.master_pane.add(self.bottom_pane, weight=0)
            else:
                self.body_pane.add(self.bottom_pane, weight=0)
            self.toggle_btn.config(text="Hide Panel")
            self.panel_visible = True

    def move_panel(self) -> None:
        """Move panel between bottom and right positions."""
        if self.panel_position == "bottom":
            # Move to right
            self.master_pane.forget(self.bottom_pane)
            self.body_pane.add(self.bottom_pane, weight=0)
            self.panel_position = "right"
            self.move_btn.config(text="Move Panel Bottom")
        else:
            # Move to bottom
            self.body_pane.forget(self.bottom_pane)
            self.master_pane.add(self.bottom_pane, weight=0)
            self.master_pane.update()
            self.panel_position = "bottom"
            self.move_btn.config(text="Move Panel Right")

        self.toggle_btn.config(text="Hide Panel")
        self.panel_visible = True


def setup_styles() -> None:
    """Configures all custom ttk styles for the application."""
    style = ttk.Style()
    style.theme_use("clam")

    style.configure("ViolationViewerLayoutFrame.TFrame", background="#f5f5f5")
    style.configure(
        "Section.TFrame", background="#f9f9f9", borderwidth=1, relief="solid"
    )
    style.configure("Toolbar.TFrame", background="#e6e6e6")
    style.configure("TLabel", background="#f9f9f9")

    style.configure("ViolationDetails.TButton", padding=6)
    style.map(
        "ViolationDetails.TButton",
        background=[("active", "#d9d9d9")],
        relief=[("pressed", "sunken"), ("!pressed", "raised")],
    )


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Violation Viewer Layout Demo")
    root.geometry("1000x600")

    # Set up the styles first
    setup_styles()

    # Create and pack the main widget
    viewer = ViolationViewerLayoutFrame(root)
    viewer.pack(expand=True, fill=tk.BOTH)

    root.mainloop()
