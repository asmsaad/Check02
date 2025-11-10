import tkinter as tk
from tkinter import ttk

class FrozenSpreadsheet(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Frozen Panes & Guarded Scroll")
        self.geometry("800x700")

        # --- State Variables for Toggling ---
        self.bottom_pane_position = "bottom"  # 'bottom' or 'right'
        self.bottom_pane_visible = True
        
        # --- NEW: State Variables for Guard Clause ---
        self.v_scroll_enabled = True
        self.h_scroll_enabled = True

        # --- STYLE CONFIGURATION ---
        style = ttk.Style()
        style.configure("Header.TButton", background="#f0f0f0", relief="groove")
        style.configure("Cell.TButton", relief="flat")
        style.configure(
            "Bottom.TFrame",
            background="#34495e"  # Dark blue-gray
        )
        # --- END OF STYLE CONFIGURATION ---

        # --- 1. Main Vertical PanedWindow ---
        self.main_paned_window = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.main_paned_window.pack(fill=tk.BOTH, expand=True)

        # --- 2. Top Container Frame for Spreadsheet ---
        self.spreadsheet_container = ttk.Frame(self.main_paned_window)
        
        # --- 3. Horizontal PanedWindow (for spreadsheet) ---
        self.horizontal_paned_window = ttk.PanedWindow(self.spreadsheet_container, orient=tk.HORIZONTAL)
        self.horizontal_paned_window.pack(fill=tk.BOTH, expand=True) 

        # --- 3a. LEFT PANE (Frozen Column) ---
        self.left_pane = ttk.Frame(self.horizontal_paned_window, width=100)
        self.left_pane.grid_rowconfigure(1, weight=1)
        self.left_pane.grid_columnconfigure(0, weight=1)
        
        self.corner_frame = ttk.Frame(self.left_pane, height=30, width=100)
        self.corner_frame.grid(row=0, column=0, sticky="nsew")
        ttk.Button(self.corner_frame, text="Corner").pack(
            fill=tk.BOTH, expand=True, padx=1, pady=1
        )
        self.row_header_canvas = tk.Canvas(self.left_pane, bd=0, highlightthickness=0)
        self.row_header_canvas.grid(row=1, column=0, sticky="nsew")
        self.row_header_frame = ttk.Frame(self.row_header_canvas)
        self.row_header_canvas.create_window((0, 0), window=self.row_header_frame, anchor="nw")

        # --- 3b. RIGHT PANE (Scrolling Content) ---
        self.right_pane = ttk.Frame(self.horizontal_paned_window)
        self.right_pane.grid_rowconfigure(1, weight=1)
        self.right_pane.grid_columnconfigure(0, weight=1)
        self.header_canvas = tk.Canvas(self.right_pane, height=30, bd=0, highlightthickness=0)
        self.header_canvas.grid(row=0, column=0, sticky="nsew")
        self.header_frame = ttk.Frame(self.header_canvas)
        self.header_canvas.create_window((0, 0), window=self.header_frame, anchor="nw")
        self.content_canvas = tk.Canvas(self.right_pane, bd=0, highlightthickness=0)
        self.content_canvas.grid(row=1, column=0, sticky="nsew")
        self.content_frame = ttk.Frame(self.content_canvas)
        self.content_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.horizontal_paned_window.add(self.left_pane, weight=0)
        self.horizontal_paned_window.add(self.right_pane, weight=1)

        # --- 3c. SCROLLBARS (Inside Right Pane) ---
        self.v_scroll = ttk.Scrollbar(self.right_pane, orient=tk.VERTICAL, 
                                      command=self.on_vertical_scroll)
        self.v_scroll.grid(row=1, column=1, sticky="ns")
        
        self.h_scroll = ttk.Scrollbar(self.right_pane, orient=tk.HORIZONTAL, 
                                      command=self.on_horizontal_scroll)
        self.h_scroll.grid(row=2, column=0, sticky="ew")

        # --- 4. Bottom Container Frame (for buttons & log) ---
        self.bottom_container = ttk.Frame(self.main_paned_window)
        self.bottom_container.grid_rowconfigure(0, weight=0) 
        self.bottom_container.grid_rowconfigure(1, weight=1) 
        self.bottom_container.grid_columnconfigure(0, weight=1)
        
        self.bottom_frame = ttk.Frame(self.bottom_container, style="Bottom.TFrame", height=40)
        self.bottom_frame.grid(row=0, column=0, sticky="ew")
        self.bottom_frame.grid_propagate(False) 

        self.action1_button = ttk.Button(self.bottom_frame, 
                                         text="Move to Right", 
                                         command=self.toggle_bottom_pane_position)
        self.action1_button.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.action2_button = ttk.Button(self.bottom_frame, 
                                         text="Hide Pane", 
                                         command=self.toggle_bottom_pane_visibility)
        self.action2_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(self.bottom_frame, text="Export...").pack(side=tk.RIGHT, padx=10, pady=5)

        self.log_frame = ttk.Frame(self.bottom_container)
        self.log_frame.grid(row=1, column=0, sticky="nsew")
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.text_area = tk.Text(self.log_frame, height=5, wrap="word")
        self.text_scroll = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, 
                                         command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=self.text_scroll.set)
        self.text_area.grid(row=0, column=0, sticky="nsew")
        self.text_scroll.grid(row=0, column=1, sticky="ns")
        self.text_area.insert(tk.END, "Application log initialized...\n")
        
        # --- 5. ADD PANES TO MAIN VERTICAL PANEWINDOW ---
        self.main_paned_window.add(self.spreadsheet_container, weight=1) 
        self.main_paned_window.add(self.bottom_container, weight=0)

        # --- 6. LINK SCROLLBARS ---
        self.row_header_canvas.configure(yscrollcommand=self.v_scroll.set)
        self.content_canvas.configure(yscrollcommand=self.v_scroll.set)
        self.header_canvas.configure(xscrollcommand=self.h_scroll.set)
        self.content_canvas.configure(xscrollcommand=self.h_scroll.set)

        # --- 7. POPULATE SPREADSHEET ---
        self.create_spreadsheet_content(rows=10, cols=5) # Start with few rows/cols

        # --- 8. BINDINGS ---
        self.row_header_frame.bind("<Configure>", self.on_row_header_frame_configure)
        self.header_frame.bind("<Configure>", self.on_header_frame_configure)
        self.content_frame.bind("<Configure>", self.on_content_frame_configure)
        
        self.content_canvas.bind("<Configure>", self._update_scrollbars)
        self.header_canvas.bind("<Configure>", self._update_scrollbars)
        self.row_header_canvas.bind("<Configure>", self._update_scrollbars)

        self.bind_mouse_wheel(self.content_canvas)
        self.bind_mouse_wheel(self.row_header_canvas)
        self.bind_mouse_wheel(self.header_canvas)
        self.bind_mouse_wheel(self.corner_frame)
        
        self.h_scroll.bind("<MouseWheel>", self.on_hscroll_mouse_wheel)
        self.h_scroll.bind("<Button-4>", self.on_hscroll_mouse_wheel)
        self.h_scroll.bind("<Button-5>", self.on_hscroll_mouse_wheel)

        styles_to_bind = ["Header.TButton", "Cell.TButton"]
        for style_name in styles_to_bind:
            self.bind_class(style_name, "<MouseWheel>", self.on_mouse_wheel)
            self.bind_class(style_name, "<Button-4>", self.on_mouse_wheel)
            self.bind_class(style_name, "<Button-5>", self.on_mouse_wheel)
            self.bind_class(style_name, "<Shift-MouseWheel>", self.on_horizontal_mouse_wheel)
            self.bind_class(style_name, "<Shift-Button-4>", self.on_horizontal_mouse_wheel)
            self.bind_class(style_name, "<Shift-Button-5>", self.on_horizontal_mouse_wheel)

        self.after(50, self._update_scrollbars)


    # --- Action Button Callbacks (Unchanged) ---
    
    def toggle_bottom_pane_position(self):
        if not self.bottom_pane_visible:
            return
        self.main_paned_window.forget(self.spreadsheet_container)
        self.main_paned_window.forget(self.bottom_container)
        if self.bottom_pane_position == "bottom":
            self.main_paned_window.configure(orient=tk.HORIZONTAL)
            self.main_paned_window.add(self.spreadsheet_container, weight=1)
            self.main_paned_window.add(self.bottom_container, weight=0)
            self.bottom_pane_position = "right"
            self.action1_button.configure(text="Move to Bottom")
        elif self.bottom_pane_position == "right":
            self.main_paned_window.configure(orient=tk.VERTICAL)
            self.main_paned_window.add(self.spreadsheet_container, weight=1)
            self.main_paned_window.add(self.bottom_container, weight=0)
            self.bottom_pane_position = "bottom"
            self.action1_button.configure(text="Move to Right")

    def toggle_bottom_pane_visibility(self):
        if self.bottom_pane_visible:
            self.main_paned_window.forget(self.bottom_container)
            self.bottom_pane_visible = False
            self.action2_button.configure(text="Show Pane")
            self.action1_button.configure(state=tk.DISABLED)
        else:
            if self.bottom_pane_position == "bottom":
                self.main_paned_window.add(self.bottom_container, weight=0)
            elif self.bottom_pane_position == "right":
                self.main_paned_window.add(self.bottom_container, weight=0)
            self.bottom_pane_visible = True
            self.action2_button.configure(text="Hide Pane")
            self.action1_button.configure(state=tk.NORMAL)


    # --- Content Creation (Unchanged) ---
    
    def create_spreadsheet_content(self, rows, cols):
        for w in self.row_header_frame.winfo_children(): w.destroy()
        for w in self.header_frame.winfo_children(): w.destroy()
        for w in self.content_frame.winfo_children(): w.destroy()
        self.row_header_frame.grid_columnconfigure(0, minsize=100)
        for r in range(rows):
            header_btn = ttk.Button(self.row_header_frame, text=f"Row {r+1}", 
                                    style="Header.TButton")
            header_btn.grid(row=r, column=0, sticky="nsew")
        for c in range(cols):
            col_name = chr(ord('A') + c)
            self.header_frame.grid_columnconfigure(c, minsize=100)
            self.content_frame.grid_columnconfigure(c, minsize=100)
            header_btn = ttk.Button(self.header_frame, text=f"Column {col_name}", 
                                    style="Header.TButton")
            header_btn.grid(row=0, column=c, sticky="nsew")
        for r in range(rows):
            for c in range(cols):
                cell_btn = ttk.Button(self.content_frame, 
                                      text=f"R{r+1}, C{c+1}", 
                                      style="Cell.TButton")
                cell_btn.grid(row=r, column=c, sticky="nsew")

    # --- Scroll Handlers (MODIFIED) ---

    def _update_scrollbars(self, event=None):
        """
        Dynamically shows or hides scrollbars based on
        content size vs. canvas size.
        """
        # --- Vertical Scrollbar Check ---
        bbox = self.content_canvas.bbox("all")
        content_height = bbox[3] - bbox[1] if bbox else 0
        canvas_height = self.content_canvas.winfo_height()

        if content_height > canvas_height:
            self.v_scroll.grid()
            self.v_scroll_enabled = True # <-- MODIFIED
        else:
            self.v_scroll.grid_remove()
            self.v_scroll_enabled = False # <-- MODIFIED

        # --- Horizontal Scrollbar Check ---
        bbox = self.content_canvas.bbox("all")
        content_width = bbox[2] - bbox[0] if bbox else 0
        canvas_width = self.content_canvas.winfo_width()

        if content_width > canvas_width:
            self.h_scroll.grid()
            self.h_scroll_enabled = True # <-- MODIFIED
        else:
            self.h_scroll.grid_remove()
            self.h_scroll_enabled = False # <-- MODIFIED


    def on_vertical_scroll(self, *args):
        self.row_header_canvas.yview(*args)
        self.content_canvas.yview(*args)

    def on_horizontal_scroll(self, *args):
        self.header_canvas.xview(*args)
        self.content_canvas.xview(*args)

    def on_row_header_frame_configure(self, event):
        self.row_header_canvas.configure(scrollregion=self.row_header_canvas.bbox("all"))
        self._update_scrollbars()

    def on_header_frame_configure(self, event):
        self.header_canvas.configure(scrollregion=self.header_canvas.bbox("all"))
        self._update_scrollbars()

    def on_content_frame_configure(self, event):
        self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
        self._update_scrollbars()

    # --- Mouse Wheel Handlers ---

    def bind_mouse_wheel(self, widget):
        widget.bind("<MouseWheel>", self.on_mouse_wheel) 
        widget.bind("<Button-4>", self.on_mouse_wheel)   
        widget.bind("<Button-5>", self.on_mouse_wheel)   
        widget.bind("<Shift-MouseWheel>", self.on_horizontal_mouse_wheel) 
        widget.bind("<Shift-Button-4>", self.on_horizontal_mouse_wheel)   
        widget.bind("<Shift-Button-5>", self.on_horizontal_mouse_wheel)   

    def on_mouse_wheel(self, event):
        if event.num == 4:
            self.on_virtual_scroll(-1)
        elif event.num == 5:
            self.on_virtual_scroll(1)
        else:
            self.on_virtual_scroll(int(-1 * (event.delta / 120)))

    def on_virtual_scroll(self, units):
        """Scrolls the vertical canvases by a number of units."""
        # --- NEW: Guard Clause ---
        if not self.v_scroll_enabled:
            return
            
        self.row_header_canvas.yview_scroll(units, "units")
        self.content_canvas.yview_scroll(units, "units")
        self.v_scroll.set(*self.content_canvas.yview())

    def on_horizontal_mouse_wheel(self, event):
        if event.num == 4:
            self.on_horizontal_virtual_scroll(-1)
        elif event.num == 5:
            self.on_horizontal_virtual_scroll(1)
        else:
            self.on_horizontal_virtual_scroll(int(-1 * (event.delta / 120)))

    def on_horizontal_virtual_scroll(self, units):
        """Scrolls the horizontal canvases by a number of units."""
        # --- NEW: Guard Clause ---
        if not self.h_scroll_enabled:
            return
            
        self.header_canvas.xview_scroll(units, "units")
        self.content_canvas.xview_scroll(units, "units")
        self.h_scroll.set(*self.content_canvas.xview())

    def on_hscroll_mouse_wheel(self, event):
        # We don't need a guard here, because this function
        # just calls the one that *has* the guard.
        if event.num == 4:
            self.on_horizontal_virtual_scroll(-1)
        elif event.num == 5:
            self.on_horizontal_virtual_scroll(1)
        else:
            self.on_horizontal_virtual_scroll(int(-1 * (event.delta / 120)))


if __name__ == "__main__":
    app = FrozenSpreadsheet()
    app.mainloop()