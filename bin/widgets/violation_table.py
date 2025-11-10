import json
from typing import List, Dict, Callable, Any, Optional, Union, Literal

import tkinter as tk
from tkinter import ttk



from bin.layout.violation_viewer import ViolationViewer
from bin.widgets.violation_table_menu import HiddenRulseRetriveMenu
from bin.widgets.custom_widgets import ColoredCheckBox
from bin.widgets.macro_info import MacroNameFrame




class ViolationTable:
    def __init__(self, layout):
        self.layout = layout
        self.left_column_frame = self.layout.body_left
        self.right_violations_columns_frame = self.layout.body_right
        self.macro_severity_frmae = self.layout.table_top_frame
        
        style = ttk.Style()
        style.configure("Tiny.TButton", padding=(3,6))  # (x, y)
        style.configure("Tiny.TFrame", background="#00eb33" )  # (x, y)
        
        # --- NEW: State Variables for Guard Clause ---
        self.v_scroll_enabled = True
        self.h_scroll_enabled = True   
        
        # --- 3a. LEFT PANE (Frozen Column) [Corner Display] ---
        self.left_column_frame.grid_rowconfigure(1, weight=1)
        self.left_column_frame.grid_columnconfigure(0, weight=1)
        #Header
        self.pins_header_canvas = tk.Canvas(self.left_column_frame,height=35,  bd=0, highlightthickness=0)
        self.pins_header_canvas.grid(row=0, column=0, sticky="nsew")
        self.pins_header_frame = ttk.Frame(self.pins_header_canvas)
        self.pins_header_canvas.create_window((0, 0), window=self.pins_header_frame, anchor="nw")
        #Body (Rows)
        self.pin_rows_canvas = tk.Canvas(self.left_column_frame, bd=0, highlightthickness=0,  )
        self.pin_rows_canvas.grid(row=1, column=0, sticky="nsew")
        self.pin_rows_frame = ttk.Frame(self.pin_rows_canvas)
        self.pin_rows_canvas.create_window((0, 0), window=self.pin_rows_frame, anchor="nw")
        
    
        # --- 3b. RIGHT PANE (Scrolling Content) ---
        self.right_violations_columns_frame.grid_rowconfigure(1, weight=1)
        self.right_violations_columns_frame.grid_columnconfigure(0, weight=1)
        #Header
        self.violations_header_canvas = tk.Canvas(self.right_violations_columns_frame, height=35, bd=0, highlightthickness=0 , )
        self.violations_header_canvas.grid(row=0, column=0, sticky="nsew")
        self.violations_header_frame = ttk.Frame(self.violations_header_canvas)
        self.violations_header_canvas.create_window((0, 0), window=self.violations_header_frame, anchor="nw")
        #Body (Rows)
        self.violations_rows_canvas = tk.Canvas(self.right_violations_columns_frame, bd=0, highlightthickness=0,  )
        self.violations_rows_canvas.grid(row=1, column=0, sticky="nsew")
        self.violations_rows_frame = ttk.Frame(self.violations_rows_canvas)
        self.violations_rows_canvas.create_window((0, 0), window=self.violations_rows_frame, anchor="nw")
        
        #----Hiden Rows
        # --- 2. Define the initial data ---
        # --- 1. Define the callback function ---
        action_button = ttk.Button(self.right_violations_columns_frame, text=":", width=0 , style="Tiny.TButton")
        action_button.grid(row=0, column=1, sticky="e", ipadx=0)
        
        def my_callback(updated_dict: Dict[str, Any]) -> None:
            """
            This function will be called by the class on any change.
            """
            print("--- CALLBACK TRIGGERED ---")
            print(json.dumps(updated_dict, indent=2))
            print("--------------------------\n")
            
        initial_data: Dict[str, Any] = {
            'cat1': {'status': True, 'rules': {'subCat1_1': True, 'subCat1_2': True}},
            'cat2': {'status': False, 'rules': {'subCat2_1': False, 'subCat2_2': True}}
        }
        # --- 4. Instantiate the class ---
        menu = HiddenRulseRetriveMenu(
            parent_widget=action_button, 
            data_dict=initial_data, 
            on_change_callback=my_callback
        )
        #  menu.update_data(new_data)
        
        #* Filter
        
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


        # --- 3. The Model Data ---
        LOG_LEVELS = {
            "Error":   {"color": "#FF4136", "default": True},
            "Warning": {"color": "#FF851B", "default": True},
            "Fatal":   {"color": "#B10DC9", "default": False}
        }

       
        
        self.macro_name_frame = ttk.Frame(self.macro_severity_frmae, style="Tiny.TFrame")
        self.macro_name_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.severity_filter_frame = ttk.Frame(self.macro_severity_frmae)
        self.severity_filter_frame.pack(side=tk.LEFT)
        
        
        macro_full_path = "/Users/Developer/Projects/Automation/dc_asdfk__asjdfkk.py"
        macro_display_name = "dc_asdfk__asjdfkk"

        macro_frame = MacroNameFrame(
        self.macro_name_frame,
        macro_name=macro_display_name,
        macro_path=macro_full_path
        )
        macro_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,10))
    
        
        
         # --- 4. Instantiate the Class ---
        # We create the checkbar, passing the root, data, and our handler
        checkbar = ColoredCheckBox(
            parent=self.severity_filter_frame, 
            options_data=LOG_LEVELS, 
            on_change_callback=print_selection_handler
        )
        # Pack the checkbar frame itself
        checkbar.pack(side=tk.RIGHT)
        
        
        
        
        
        
        
        ttk.Frame(self.left_column_frame, height=16, width=0 , style="Tiny.TFrame").grid(row=2, column=0, sticky="nsew")
        
        ttk.Button(self.pins_header_canvas, text="Corner").pack(
            fill=tk.BOTH, expand=True, 
        )
        
        # ttk.Button(self.violations_header_canvas, text="Corner").pack(
        #      side=tk.RIGHT
        # )
        
        
        # --- 3c. SCROLLBARS (Inside Right Pane) ---
        self.v_scroll = ttk.Scrollbar(self.right_violations_columns_frame, orient=tk.VERTICAL, command=self.on_vertical_scroll)
        self.v_scroll.grid(row=1, column=1, sticky="ns")
        self.h_scroll = ttk.Scrollbar(self.right_violations_columns_frame, orient=tk.HORIZONTAL, command=self.on_horizontal_scroll)
        self.h_scroll.grid(row=2, column=0, sticky="ew")
        
        
         # --- 6. LINK SCROLLBARS ---
        self.pin_rows_canvas.configure(yscrollcommand=self.v_scroll.set)
        self.violations_rows_canvas.configure(yscrollcommand=self.v_scroll.set)
        self.violations_header_canvas.configure(xscrollcommand=self.h_scroll.set)
        self.violations_rows_canvas.configure(xscrollcommand=self.h_scroll.set)
        
        
        # --- 7. POPULATE SPREADSHEET ---
        self.create_spreadsheet_content(rows=10, cols=5)

        self.pin_rows_frame.bind("<Configure>", lambda event: self.pin_rows_canvas.configure(scrollregion=self.pin_rows_canvas.bbox("all")) )
        self.violations_header_frame.bind("<Configure>", lambda event: self.violations_header_canvas.configure(scrollregion=self.violations_header_canvas.bbox("all")) )
        self.violations_rows_frame.bind("<Configure>", lambda event: self.violations_rows_canvas.configure(scrollregion=self.violations_rows_canvas.bbox("all")) )
        
        self.violations_rows_canvas.bind("<Configure>", self._update_scrollbars)
        self.violations_header_canvas.bind("<Configure>", self._update_scrollbars)
        self.pin_rows_canvas.bind("<Configure>", self._update_scrollbars)

        # # self.row_header_frame.bind("<Configure>", self.on_row_header_frame_configure)
        # # self.header_frame.bind("<Configure>", self.on_header_frame_configure)
        # # self.content_frame.bind("<Configure>", self.on_content_frame_configure)
        # # self.pin_rows_canvas.configure(scrollregion=self.pin_rows_canvas.bbox("all"))
        # # self.violations_header_canvas.configure(scrollregion=self.violations_header_canvas.bbox("all"))
        # # self.violations_rows_canvas.configure(scrollregion=self.violations_rows_canvas.bbox("all"))
        
        # self.bind_mouse_wheel(self.pins_header_canvas, direction="VERTICAL")
        # self.bind_mouse_wheel(self.pin_rows_canvas, direction="VERTICAL")
        # self.bind_mouse_wheel(self.violations_header_canvas, direction="HORIZONTAL")
        # self.bind_mouse_wheel(self.violations_rows_canvas, direction="BOTH")
        
        
        # self.h_scroll.bind("<MouseWheel>", self.on_hscroll_mouse_wheel)
        # self.h_scroll.bind("<Button-4>", self.on_hscroll_mouse_wheel)
        # self.h_scroll.bind("<Button-5>", self.on_hscroll_mouse_wheel)
        
        # Bind scrolling to all 4 canvas quadrants
        self.bind_mouse_wheel(self.violations_rows_canvas)
        self.bind_mouse_wheel(self.pin_rows_canvas)
        self.bind_mouse_wheel(self.violations_header_canvas)
        self.bind_mouse_wheel(self.pins_header_canvas)
        
        # Bind wheel scroll to H-scroll bar
        self.h_scroll.bind("<MouseWheel>", self.on_hscroll_mouse_wheel)
        self.h_scroll.bind("<Button-4>", self.on_hscroll_mouse_wheel)
        self.h_scroll.bind("<Button-5>", self.on_hscroll_mouse_wheel)
        

        self.violations_rows_canvas.after(50, self._update_scrollbars)
    
    def bind_mouse_wheel(self, widget):
        """Binds vertical AND horizontal mouse wheel events."""
        # Vertical Scroll
        widget.bind("<MouseWheel>", self.on_mouse_wheel) # Windows
        widget.bind("<Button-4>", self.on_mouse_wheel)   # Linux (scroll up)
        widget.bind("<Button-5>", self.on_mouse_wheel)   # Linux (scroll down)
        
        # Horizontal Scroll
        widget.bind("<Shift-MouseWheel>", self.on_horizontal_mouse_wheel) # Windows
        widget.bind("<Shift-Button-4>", self.on_horizontal_mouse_wheel)   # Linux
        widget.bind("<Shift-Button-5>", self.on_horizontal_mouse_wheel)   # Linux 

    def on_mouse_wheel(self, event):
        """Handles vertical mouse wheel scrolling."""
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
        
        self.pin_rows_canvas.yview_scroll(units, "units")
        self.violations_rows_canvas.yview_scroll(units, "units")
        self.v_scroll.set(*self.violations_rows_canvas.yview())

    def on_horizontal_mouse_wheel(self, event):
        """Handles horizontal (Shift+MouseWheel) scrolling."""
        if event.num == 4:
            self.on_horizontal_virtual_scroll(-1)
        elif event.num == 5:
            self.on_horizontal_virtual_scroll(1)
        else:
            self.on_horizontal_virtual_scroll(int(-1 * (event.delta / 120)))

    def on_hscroll_mouse_wheel(self, event):
        """Handles mouse wheel scrolling when over the H-scrollbar."""
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
        
        self.violations_header_canvas.xview_scroll(units, "units")
        self.violations_rows_canvas.xview_scroll(units, "units")
        self.h_scroll.set(*self.violations_rows_canvas.xview())
    
    def on_vertical_scroll(self, *args):
        self.pin_rows_canvas.yview(*args)
        self.violations_rows_canvas.yview(*args)

    def on_horizontal_scroll(self, *args):
        self.violations_header_canvas.xview(*args)
        self.violations_rows_canvas.xview(*args)
        
    def _update_scrollbars(self, event=None):
        """
        Dynamically shows or hides scrollbars based on
        content size vs. canvas size.
        """
        # --- Vertical Scrollbar Check ---
        bbox = self.violations_rows_canvas.bbox("all")
        content_height = bbox[3] - bbox[1] if bbox else 0
        canvas_height = self.violations_rows_canvas.winfo_height()

        if content_height > canvas_height:
            self.v_scroll.grid()
            self.v_scroll_enabled = True # <-- MODIFIED
        else:
            self.v_scroll.grid_remove()
            self.v_scroll_enabled = False # <-- MODIFIED

        # --- Horizontal Scrollbar Check ---
        bbox = self.violations_rows_canvas.bbox("all")
        content_width = bbox[2] - bbox[0] if bbox else 0
        canvas_width = self.violations_rows_canvas.winfo_width()

        if content_width > canvas_width:
            self.h_scroll.grid()
            self.h_scroll_enabled = True # <-- MODIFIED
        else:
            self.h_scroll.grid_remove()
            self.h_scroll_enabled = False # <-- MODIFIED
        
        
    def create_spreadsheet_content(self, rows, cols):
        self.pin_rows_frame.grid_columnconfigure(0, minsize=100)
        for r in range(rows):
            header_btn = ttk.Button(self.pin_rows_frame, text=f"Row {r+1}", 
                                    style="Header.TButton")
            header_btn.grid(row=r, column=0, sticky="nsew")
            # --- ADDED BINDING ---
            self.bind_mouse_wheel(header_btn)

        for c in range(cols):
            col_name = chr(ord('A') + c)
            self.violations_header_frame.grid_columnconfigure(c, minsize=100)
            self.violations_rows_frame.grid_columnconfigure(c, minsize=100)
            header_btn = ttk.Button(self.violations_header_frame, text=f"Column {col_name}", 
                                    style="Header.TButton")
            header_btn.grid(row=0, column=c, sticky="nsew")
            # --- ADDED BINDING ---
            self.bind_mouse_wheel(header_btn)

        for r in range(rows):
            for c in range(cols):
                cell_btn = ttk.Button(self.violations_rows_frame, 
                                      text=f"R{r+1}, C{c+1}", 
                                      style="Cell.TButton")
                cell_btn.grid(row=r, column=c, sticky="nsew")
                # --- ADDED BINDING ---
                self.bind_mouse_wheel(cell_btn)
    


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Excel-like Layout with Movable Panel (Styled)")
    root.geometry("1000x600")

    viewer_layout = ViolationViewer(root)
    ViolationTable(viewer_layout)

    root.update_idletasks()  # Ensure layout renders before showing
    root.mainloop()
