import tkinter as tk
from tkinter import ttk
from typing import Dict, Literal, List, Tuple, Any
import platform,os








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

        headers = [self.data.get("Ruel Name", "Rule"), "Compare Source", "Path"]
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

class DetailsViolationAnalysisFrame(ttk.Frame):
    """
    A production-ready Tkinter component with 'Details' and 'Analysis' tabs.
    Features robust state management (Hide/Show/Disable/Enable).
    """

    def __init__(self, master: tk.Widget, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        
        # Internal State tracking
        self._notebook: ttk.Notebook
        self._details_tab: ttk.Frame
        self._analysis_tab: ttk.Frame
        self._text_area: tk.Text
        self._btn_container: ttk.Frame
        
        self._setup_ui()
        self._initialize_state()

    def _setup_ui(self) -> None:
        """Constructs the notebook and tab layout."""
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill=tk.BOTH, expand=True)

        # --- Tab 1: Details ---
        self._details_tab = ttk.Frame(self._notebook)
        self._notebook.add(self._details_tab, text="Details")

        self._text_area = tk.Text(self._details_tab, wrap=tk.WORD, height=10, padx=5, pady=5)
        text_scroll = ttk.Scrollbar(self._details_tab, orient=tk.VERTICAL, command=self._text_area.yview)
        self._text_area.configure(yscrollcommand=text_scroll.set)
        
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- Tab 2: Analysis ---
        self._analysis_tab = ttk.Frame(self._notebook)
        self._notebook.add(self._analysis_tab, text="Analysis")

        self._btn_container = ttk.Frame(self._analysis_tab)
        self._btn_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
               
        self.analysis_tab = ViolationAnalysisTabFrame(self._btn_container, data={})
        self.analysis_tab.pack(fill=tk.BOTH, expand=True)

    def _initialize_state(self) -> None:
        """Sets initial state: Tab 1 active, Tab 2 disabled."""
        self._notebook.select(self._details_tab)
        self._notebook.tab(self._analysis_tab, state="disabled")

    # ----------------------------------------------------------------
    # Public API Methods
    # ----------------------------------------------------------------

    def update_details_text(self, content: str) -> None:
        """Updates the text area content safely."""
        self._text_area.config(state=tk.NORMAL)
        self._text_area.delete("1.0", tk.END)
        self._text_area.insert("1.0", content)

    def update_analysis_tab_content(self, analysis_tab_data: Dict[str, str]) -> None:
        """
        Regenerates buttons in the Analysis tab from a dictionary.
        Format: { "ButtonLabel": "ActionDescription" }
        """
        self.analysis_tab.update_data(analysis_tab_data)


    def set_active_tab(self, tab_name: Literal["details", "analysis"]) -> None:
        """Focuses a specific tab programmatically."""
        if tab_name == "details":
            self._notebook.select(self._details_tab)
        elif tab_name == "analysis":
            # Validations to prevent TclErrors
            if not self._is_analysis_visible():
                print("Error: Cannot focus Analysis tab (It is hidden).")
                return
            
            # Ensure it's enabled before selecting
            self._notebook.tab(self._analysis_tab, state="normal")
            self._notebook.select(self._analysis_tab)

    def disable_analysis_tab(self) -> None:
        """
        Disables the Analysis tab (grayed out) and forces focus to Details.
        """
        if not self._is_analysis_visible():
            print("Warning: Analysis tab is hidden, cannot disable state.")
            return

        # 1. Force focus to Details tab immediately
        self._notebook.select(self._details_tab)
        
        # 2. Set Analysis state to disabled
        self._notebook.tab(self._analysis_tab, state="disabled")

    def toggle_analysis_visibility(self, show: bool) -> None:
        """
        Completely Hides or Shows the Analysis tab.
        """
        is_currently_visible = self._is_analysis_visible()

        if show and not is_currently_visible:
            # Add it back to the notebook
            self._notebook.add(self._analysis_tab, text="Analysis")
            # Default to normal state when showing
            self._notebook.tab(self._analysis_tab, state="normal")
        
        elif not show and is_currently_visible:
            # If we are hiding the currently active tab, switch focus first
            if self._notebook.select() == str(self._analysis_tab):
                self._notebook.select(self._details_tab)
            
            # Hide removes it from view but keeps the object
            self._notebook.forget(self._analysis_tab)

    # ----------------------------------------------------------------
    # Helper Methods (Private)
    # ----------------------------------------------------------------
    
    def _is_analysis_visible(self) -> bool:
        """
        Checks if Analysis tab is currently in the Notebook's tab list.
        Critical Fix: compare str(widget) against the list of tab IDs.
        """
        # self._notebook.tabs() returns a tuple of string identifiers
        return str(self._analysis_tab) in self._notebook.tabs()





















# ----------------------------------------------------------------
# Driver Code
# ----------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Professional Notebook Manager")
    root.geometry("600x450")

    # 1. APPLY CLAM THEME (Requested)
    style = ttk.Style()
    style.theme_use("clam")

    details_vilolation_frame = DetailsViolationAnalysisFrame(root)
    details_vilolation_frame.pack(fill=tk.BOTH, expand=True)

    # --- External Controls ---
    control_panel = ttk.LabelFrame(root, text="External Controller")
    control_panel.pack(fill=tk.X, padx=10, pady=10)
    
    
    
    
    # Short valid data (Scrollbar should HIDE)
    valid_data_short = {
        "Ruel Name": "P_CEMISMATC",
        "message": "Critical Error: The pin direction defined in the CSV spec does not match the implementation.",
        "per_view": {
            "/path/specs.csv": "Output",  
            "/path/block_a.lef": "Input", # Mismatch
            "/path/block_b.lef": "Output"
        }
    }

    # Long valid data (Scrollbar should SHOW)
    valid_data_long = {
        "Ruel Name": "P_CEMISMATC",
        "message": "This list is long to demonstrate the dynamic scrollbar appearing.",
        "per_view": {f"/path/file_{i}.lef": ("Input" if i%2==0 else "Output") for i in range(25)}
    }
    valid_data_long["per_view"]["/path/spec.csv"] = "Input"
    
    
    
    

    # Callback Functions
    def load_data_and_focus():
        data = {
            "Calculate Metrics": "Calculating...", 
            "Generate PDF": "PDF Created",
            "Email Logs": "Email Sent"
        }
        # Ensure it's visible first
        details_vilolation_frame.toggle_analysis_visibility(True)
        details_vilolation_frame.update_analysis_tab_content(valid_data_long)
        details_vilolation_frame.set_active_tab("analysis")

    def disable_analysis():
        details_vilolation_frame.disable_analysis_tab()

    def hide_analysis():
        details_vilolation_frame.toggle_analysis_visibility(False)

    def show_analysis():
        details_vilolation_frame.toggle_analysis_visibility(True)
        
    
    
      
    # Callbacks
    def load_empty():
        details_vilolation_frame.update_analysis_tab_content({}) # Green

    def load_invalid():
        details_vilolation_frame.update_analysis_tab_content({"error_code": 500, "garbage": "true"}) # Orange

    def load_valid():
        details_vilolation_frame.update_analysis_tab_content(valid_data_short) # Red (Short - No Scroll)

    def load_long():
        details_vilolation_frame.update_analysis_tab_content(valid_data_long) # Red (Long - With Scroll)

    
        
        

    # Layout Grid for Controls
    ttk.Button(control_panel, text="Load Data & Focus Analysis", command=load_data_and_focus).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    ttk.Button(control_panel, text="Disable Analysis & Focus Details", command=disable_analysis).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    ttk.Button(control_panel, text="Hide Analysis Tab", command=hide_analysis).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
    ttk.Button(control_panel, text="Show Analysis Tab", command=show_analysis).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
    
   
   
   
   
    # Analysis Tab Buttons
    ttk.Button(control_panel, text="1. Load Empty (Green)", command=load_empty).grid(row=3, column=0, padx=5, pady=5, sticky="ew")
    ttk.Button(control_panel, text="2. Load Invalid (Orange)", command=load_invalid).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
    ttk.Button(control_panel, text="3. Load Valid Violation (Red)", command=load_valid).grid(row=3, column=2, padx=5, pady=5, sticky="ew")
    ttk.Button(control_panel, text="4. Load Long Data (Test Scroll)", command=load_long).grid(row=3, column=3, padx=5, pady=5, sticky="ew")

    # Column configuration for resizing
    control_panel.columnconfigure(0, weight=1)
    control_panel.columnconfigure(1, weight=1)

    root.mainloop()