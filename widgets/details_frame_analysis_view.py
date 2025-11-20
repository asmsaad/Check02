import tkinter as tk
from tkinter import ttk
import os
import platform
from typing import Dict, Any, List, Tuple

class ViolationAnalysisTabFrame(ttk.Frame):
    """
    ViolationAnalysisTabFrame displays mismatch data in a tabular format.

    Features:
    - Generates color-coded indicators for different violation types.
    - Handles warnings when data mismatches occur.
    - Gracefully handles empty or missing violation data by showing a "no violation found" message.
    """

    def __init__(self, master: tk.Widget, data: Dict[str, Any] = None, **kwargs) -> None:
        super().__init__(master, **kwargs)
        
        self.data = data if data is not None else {}
        
        # Constants
        self.MAIN_BG = "#dcdad5" 
        self.FONTS = {
            "ui": ("Segoe UI", 11),
            "header": ("Segoe UI", 10, "bold"),
            "path": ("Consolas", 11),
            "msg_title": ("Helvetica", 11, "bold")
        }
        
        self._setup_styles()

        # 1. Setup Scrollable Infrastructure
        self._canvas = tk.Canvas(self, highlightthickness=0, bg=self.MAIN_BG)
        self._scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._scroll_frame = ttk.Frame(self._canvas)

        self._setup_scroll_logic()
        
        # 2. Render
        self.refresh_ui()

    def update_data(self, new_data: Dict[str, Any]) -> None:
        """Updates the content and recalculates scrollbar visibility."""
        self.data = new_data
        self.refresh_ui()

    def refresh_ui(self) -> None:
        # Clear old widgets
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()

        # Render based on state
        if not self.data:
            # Case 1: Empty (Green)
            self._build_status_banner("✔ NO VIOLATIONS FOUND", "No Rule violation detected.", 
                                      "#e8f5e9", "#2e7d32", "#1b5e20")
        elif not self._is_valid_structure():
            # Case 2: Invalid Structure (Orange)
            self._build_status_banner("⚠ DATA STRUCTURE ERROR", "Unstructured data detected.", 
                                      "#fff3e0", "#ef6c00", "#e65100")
        else:
            # Case 3: Valid Violation (Red)
            self._build_status_banner("⚠ RULE VIOLATION DETECTED", self.data.get("message", ""), 
                                      "#ffebee", "#c62828", "#8b0000")
            self._build_data_table()
        
        # Force layout update to check scrollbar need
        self._scroll_frame.update_idletasks()
        self._update_scroll_state()

    def _setup_styles(self) -> None:
        style = ttk.Style()
        style.configure("GridHeader.TButton", font=self.FONTS["header"], foreground="black")

    def _setup_scroll_logic(self) -> None:
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._scroll_frame, anchor="nw"
        )

        # Bind configure events to handle dynamic resizing
        self._scroll_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Universal Scroll Bindings
        self._bind_scroll_events(self._canvas)
        self._bind_scroll_events(self._scroll_frame)

    # ------------------------------------------------------------------
    # DYNAMIC SCROLL LOGIC
    # ------------------------------------------------------------------

    def _on_frame_configure(self, event=None):
        """Called when inner content size changes."""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._update_scroll_state()

    def _on_canvas_configure(self, event=None):
        """Called when main window resizes."""
        self._canvas.itemconfig(self._canvas_window, width=event.width)
        self._update_scroll_state()

    def _update_scroll_state(self):
        """Shows scrollbar ONLY if content is taller than viewport."""
        req_height = self._scroll_frame.winfo_reqheight()
        visible_height = self._canvas.winfo_height()

        if visible_height < 5: return 

        if req_height > visible_height:
            self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self._scrollbar.pack_forget()
            self._canvas.yview_moveto(0)

    def _on_mousewheel(self, event):
        """Scrolls only if scrollbar is visible."""
        if not self._scrollbar.winfo_ismapped():
            return

        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            self._canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        elif event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")

    def _bind_scroll_events(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)
        widget.bind("<Button-4>", self._on_mousewheel)
        widget.bind("<Button-5>", self._on_mousewheel)

    # ------------------------------------------------------------------
    # DATA PROCESSING & RENDER
    # ------------------------------------------------------------------

    def _is_valid_structure(self) -> bool:
        if not isinstance(self.data, dict): return False
        if "per_view" not in self.data or not isinstance(self.data["per_view"], dict): return False
        return True

    def _build_status_banner(self, title, message, bg_color, fg_color, border_color):
        container = tk.Frame(self._scroll_frame, bg=bg_color, padx=15, pady=15, 
                             highlightbackground=border_color, highlightthickness=2)
        container.pack(fill=tk.X, padx=10, pady=(10, 20))
        self._bind_scroll_events(container)

        lbl_title = tk.Label(container, text=title, font=self.FONTS["msg_title"], 
                             bg=bg_color, fg=fg_color)
        lbl_title.pack(anchor="w")
        self._bind_scroll_events(lbl_title)

        lbl_msg = tk.Label(container, text=message, font=self.FONTS["ui"], 
                           bg=bg_color, fg="#333333", wraplength=600, justify="left")
        lbl_msg.pack(anchor="w", pady=(5, 0))
        self._bind_scroll_events(lbl_msg)

    def _process_data(self) -> List[Tuple[str, str, str]]:
        raw_per_view = self.data.get("per_view", {})
        csv_row = None
        other_rows = []
        for path, direction in raw_per_view.items():
            _, ext_with_dot = os.path.splitext(path)
            ext = ext_with_dot.lstrip(".").lower()
            row_data = (direction, ext, path)
            if ext == 'csv': csv_row = row_data
            else: other_rows.append(row_data)
        
        final = [csv_row] if csv_row else []
        final.extend(other_rows)
        return final

    def _build_data_table(self) -> None:
        table_frame = tk.Frame(self._scroll_frame, bg=self.MAIN_BG)
        table_frame.pack(fill=tk.X, padx=10, pady=10)
        self._bind_scroll_events(table_frame)

        table_frame.columnconfigure(0, weight=1)
        table_frame.columnconfigure(1, weight=1)
        table_frame.columnconfigure(2, weight=4) 

        headers = [self.data.get("Ruel Name", "Rule"), "File Type", "File Path"]
        for col_idx, text in enumerate(headers):
            btn = ttk.Button(table_frame, text=text, style="GridHeader.TButton", state="normal")
            btn.grid(row=0, column=col_idx, sticky="ew", padx=1, pady=1)
            self._bind_scroll_events(btn)

        sorted_data = self._process_data()
        if not sorted_data: return
        ref_dir = sorted_data[0][0]

        for row_idx, (direction, f_type, f_path) in enumerate(sorted_data, start=1):
            is_mismatch = (direction != ref_dir)
            bg, fg = ("#ffcdd2", "#b71c1c") if is_mismatch else (self.MAIN_BG, "black")

            def create_cell(txt, col, bg, fg, font_fam, is_bold=False, just="left", cap=False):
                font_cfg = (font_fam, 11, "bold" if is_bold else "normal")
                entry = tk.Entry(table_frame, bg=bg, fg=fg, font=font_cfg, relief="sunken", 
                                 bd=1, justify=just, highlightthickness=0)
                entry.insert(0, str(txt).upper() if cap else str(txt))
                entry.configure(state="readonly")
                entry.grid(row=row_idx, column=col, sticky="ew", padx=1, pady=1, ipady=5)
                self._bind_scroll_events(entry)

            create_cell(direction, 0, bg, fg, "Segoe UI", is_bold=False, just="center")
            create_cell(f_type, 1, self.MAIN_BG, "black", "Segoe UI", just="center", cap=True)
            create_cell(f_path, 2, self.MAIN_BG, "black", "Consolas")

# ----------------------------------------------------------------
# Driver Code
# ----------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Rule Verification System")
    root.geometry("1000x600")
    style = ttk.Style()
    style.theme_use("clam")
    
    # --- 1. Define Data Sets ---
    
    # Short valid data (Scrollbar should HIDE)
    valid_data_short = {
        "Ruel Name": "Pin Direction Check",
        "message": "Critical Error: The pin direction defined in the CSV spec does not match the implementation.",
        "per_view": {
            "/path/specs.csv": "Output",  
            "/path/block_a.lef": "Input", # Mismatch
            "/path/block_b.lef": "Output"
        }
    }

    # Long valid data (Scrollbar should SHOW)
    valid_data_long = {
        "Ruel Name": "Scroll Test",
        "message": "This list is long to demonstrate the dynamic scrollbar appearing.",
        "per_view": {f"/path/file_{i}.lef": ("Input" if i%2==0 else "Output") for i in range(25)}
    }
    valid_data_long["per_view"]["/path/spec.csv"] = "Input"

    # --- 2. Initialize App ---
    app = ViolationAnalysisTabFrame(root, data=valid_data_short)
    app.pack(fill=tk.BOTH, expand=True)

    # --- 3. Control Panel ---
    control_panel = tk.Frame(root, bg="#333", pady=10)
    control_panel.pack(fill=tk.X, side=tk.BOTTOM)

    # Callbacks
    def load_empty():
        app.update_data({}) # Green

    def load_invalid():
        app.update_data({"error_code": 500, "garbage": "true"}) # Orange

    def load_valid():
        app.update_data(valid_data_short) # Red (Short - No Scroll)

    def load_long():
        app.update_data(valid_data_long) # Red (Long - With Scroll)

    # Buttons
    ttk.Button(control_panel, text="1. Load Empty (Green)", command=load_empty).pack(side=tk.LEFT, padx=10)
    ttk.Button(control_panel, text="2. Load Invalid (Orange)", command=load_invalid).pack(side=tk.LEFT, padx=10)
    ttk.Button(control_panel, text="3. Load Valid Violation (Red)", command=load_valid).pack(side=tk.LEFT, padx=10)
    ttk.Button(control_panel, text="4. Load Long Data (Test Scroll)", command=load_long).pack(side=tk.LEFT, padx=10)

    root.mainloop()