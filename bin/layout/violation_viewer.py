import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

# from bin.widgets.text_editor import TextEditorWidget




class ViolationViewer:
    """A styled Tkinter layout component with toggleable and movable panel (bottom or right)."""

    def __init__(self, root):
        """Initialize the ViolationViewer layout."""
        # ---- Theme and Style ----
        self.style = ttk.Style()
        # self.style.theme_use("clam")  # 'clam' works well across platforms

        # General frame style
        self.style.configure("ViolationViewer.TFrame", background="#f5f5f5")

        # Custom section frames
        self.style.configure("Section.TFrame", background="#f9f9f9", borderwidth=1, relief="solid")
        self.style.configure("Toolbar.TFrame", background="#e6e6e6")

        # Buttons
        self.style.configure("ViolationDetails.TButton", padding=6)
        self.style.map("ViolationDetails.TButton",
                       background=[("active", "#d9d9d9")],
                       relief=[("pressed", "sunken"), ("!pressed", "raised")])

        # Text area
        self.style.configure("TLabel", background="#f9f9f9")

        # ---- Base Frame ----
        self.base_frame = ttk.Frame(root, style="ViolationViewer.TFrame")
        self.base_frame.pack(expand=True, fill=tk.BOTH)

        # ---- Panel State ----
        self.panel_visible = True
        self.panel_position = "bottom"  # Options: "bottom" or "right"

        # Initialize layout
        self._init_layout()

    def _init_layout(self):
        """Create and configure the main layout."""
        #
        self.table_top_frame = ttk.Frame(self.base_frame, style="Toolbar.TFrame")
        self.table_top_frame.pack(fill="x", side="top")
        # self.table_top_frame = tk.Frame(self.base_frame,height=20, background="red")
        # self.table_top_frame.pack(expand=True, fill=tk.X)
        
        # ---- PanedWindow Layout ----
        # Master (vertical) PanedWindow
        self.master_pane = ttk.PanedWindow(self.base_frame, orient="vertical")
        self.master_pane.pack(fill="both", expand=True)

        # Body PanedWindow
        self.body_pane = ttk.PanedWindow(self.master_pane, orient="horizontal")

        # Bottom panel (initially visible)
        self.bottom_pane = ttk.PanedWindow(self.master_pane, orient="horizontal")

        # Place panes into master
        self.master_pane.add(self.body_pane, weight=1)
        self.master_pane.add(self.bottom_pane, weight=0)

        # ---- Body Frames ----
        self.body_left = ttk.Frame(self.body_pane, width=200, style="Section.TFrame", padding=(3, 3))
        self.body_right = ttk.Frame(self.body_pane, width=800, style="Section.TFrame", padding=(3, 3))
        # Place panes into body
        self.body_pane.add(self.body_left)
        self.body_pane.add(self.body_right)
        
        
        # ---- Toolbar ----
        self.toolbar = ttk.Frame(self.base_frame, style="Toolbar.TFrame")
        self.toolbar.pack(fill="x", side="top")

        self.toggle_btn = ttk.Button(self.toolbar, text="Hide Panel", width=15, style="ViolationDetails.TButton", command=self.toggle_panel)
        self.toggle_btn.pack(side="left", padx=5, pady=5)

        self.move_btn = ttk.Button(self.toolbar, text="Move Panel Right", width=20, style="ViolationDetails.TButton", command=self.move_panel)
        self.move_btn.pack(side="left", padx=5, pady=5)



        # ---- Bottom Frame ----
        self.bottom_frame = ttk.Frame(self.bottom_pane, width=800, height=700, style="Section.TFrame")
        # Place panes into bottom(Text Viewer)
        self.bottom_pane.add(self.bottom_frame)

        # ---- Text View (ScrolledText) ----
        # self.bottom_frame.pack_propagate(False)
        self.b_ = tk.Frame(self.bottom_frame, background="red", height=100)
        self.b_.pack(fill="both", expand=True, padx=5, pady=5)
        # self.test_text = ScrolledText(self.bottom_frame, height=5, wrap="word", font=("Segoe UI", 10))
        # self.test_text.insert("1.0", "Bottom panel text area. Move or hide me to test layout.")
        # self.test_text.pack(fill="both", expand=True, padx=5, pady=5)
        # a = TextEditorWidget(self.b_ )
        # a.pack(fill="both", expand=True)
        

    def toggle_panel(self):
        """Show or hide the bottom/right panel."""
        if self.panel_visible:
            # self.b_.pack_forget() #!
            # self.base_frame.update() #!
            if self.panel_position == "bottom":
                self.master_pane.forget(self.bottom_pane)
            else:
                self.body_pane.forget(self.bottom_pane)

            self.toggle_btn.config(text="Show Panel")
            self.panel_visible = False
        else:
            # self.b_.pack(fill="both", expand=True, padx=5, pady=5) #!
            if self.panel_position == "bottom":
                self.master_pane.add(self.bottom_pane, weight=0)
            else:
                self.body_pane.add(self.bottom_pane, weight=0)

            self.toggle_btn.config(text="Hide Panel")
            self.panel_visible = True

    def move_panel(self):
        """Move panel between bottom and right positions."""
        if self.panel_position == "bottom":
            # Move to right
            self.master_pane.forget(self.bottom_pane)
            self.body_pane.add(self.bottom_pane, weight=0)
            #! self.body_pane.sashpos(1, int(self.body_pane.winfo_width() * 0.70))
            self.panel_position = "right"
            self.move_btn.config(text="Move Panel Bottom")
        else:
            # Move to bottom
            self.body_pane.forget(self.bottom_pane)
            self.master_pane.add(self.bottom_pane, weight=0)

            # Update geometry after adding
            self.master_pane.update()

            #!---
            # desired_bottom_height = 300
            # total_height = self.master_pane.winfo_height()
            # sash_position = total_height - desired_bottom_height
            # self.master_pane.sashpos(0, sash_position)

            self.panel_position = "bottom"
            self.move_btn.config(text="Move Panel Right")

        # Ensure panel is visible and update button text
        self.toggle_btn.config(text="Hide Panel")
        self.panel_visible = True


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Excel-like Layout with Movable Panel (Styled)")
    root.geometry("1000x600")

    viewer = ViolationViewer(root)

    root.update_idletasks()  # Ensure layout renders before showing
    root.mainloop()
