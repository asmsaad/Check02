import json
from typing import List, Dict, Callable, Any, Optional, Union, Literal

import tkinter as tk
from tkinter import ttk

from layouts.violation_viewer_layout import ViolationViewerLayoutFrame
from core.violation_filter import *
from views.table_menu import TableHeaderMenu, show_menu
from widgets.filter import ColumnFilter
from widgets.checkbox import ColoredCheckBox
from widgets.find import FindWidget

    







class ViolationTable:
    def __init__(self, layout):
        self.layout = layout
        self.left_column_frame = self.layout.body_left
        self.right_violations_columns_frame = self.layout.body_right
        self.macro_severity_frmae = self.layout.table_top_frame
        self.details_view = self.layout.details_view
        self.filter_section = self.layout.filter_right
        
        
        
        self.RULE_CATEGORY = rule_cat #! need  to be pass form backend
        
        # style = ttk.Style()
        
        
        # --- NEW: State Variables for Guard Clause ---
        self.v_scroll_enabled = True
        self.h_scroll_enabled = True   
        
        
        
        
        
        
        
        
        
        # --- 3a. LEFT PANE (Frozen Column) [Corner Display] ---
        self.left_column_frame.grid_rowconfigure(1, weight=1)
        self.left_column_frame.grid_columnconfigure(0, weight=1)
        #Header
        self.pins_header_canvas = tk.Canvas(self.left_column_frame,  bd=0, highlightthickness=0, height=62, )
        self.pins_header_canvas.grid(row=0, column=0, sticky="nsew")
        self.pins_header_frame = ttk.Frame(self.pins_header_canvas, style="ViolationTable.PinInfo.Header.TFrame")
        self.pins_header_canvas.create_window((0, 0), window=self.pins_header_frame, anchor="nw")
        #Body (Rows)
        self.pin_rows_canvas = tk.Canvas(self.left_column_frame, bd=0, highlightthickness=0,  )
        self.pin_rows_canvas.grid(row=1, column=0, sticky="nsew")
        self.pin_rows_frame = ttk.Frame(self.pin_rows_canvas, style="ViolationTable.PinInfo.Data.TFrame")
        self.pin_rows_canvas.create_window((0, 0), window=self.pin_rows_frame, anchor="nw")
        
    
        # --- 3b. RIGHT PANE (Scrolling Content) ---
        self.right_violations_columns_frame.grid_rowconfigure(1, weight=1)
        self.right_violations_columns_frame.grid_columnconfigure(0, weight=1)
        #Header
        self.violations_header_canvas = tk.Canvas(self.right_violations_columns_frame,  bd=0, highlightthickness=0 ,height=62 )
        self.violations_header_canvas.grid(row=0, column=0, sticky="nsew")
        self.violations_header_frame = ttk.Frame(self.violations_header_canvas, style="ViolationTable.Rules.Header.TFrame")
        self.violations_header_canvas.create_window((0, 0), window=self.violations_header_frame, anchor="nw")
        #Body (Rows)
        self.violations_rows_canvas = tk.Canvas(self.right_violations_columns_frame, bd=0, highlightthickness=0 )
        self.violations_rows_canvas.grid(row=1, column=0, sticky="nsew")
        self.violations_rows_frame = ttk.Frame(self.violations_rows_canvas, style="ViolationTable.Rules.Status.TFrame")
        self.violations_rows_canvas.create_window((0, 0), window=self.violations_rows_frame, anchor="nw")
        
        #----Hiden Rows
        # --- 2. Define the initial data ---
        # --- 1. Define the callback function ---
        action_button = ttk.Button(self.right_violations_columns_frame, text=":", width=0 , style="Tiny.TButton")
        action_button.grid(row=0, column=1, sticky="nsew", ipadx=0)
        
        # This frame is adjusting the left panel with the right panel, while one side has a scrollbar and the other does not.
        self.placeholder_v_scroll = ttk.Frame(self.left_column_frame, height=16, width=0 , style="ViolationTable.Placeholder.HScroll.TFrame")
        self.placeholder_v_scroll.grid(row=2, column=0, sticky="nsew")
        
        
        
        
        
        def on_find_change( state: Dict[str, Any]):
            """This function is passed to the widget and gets called on any change."""
            print("Find widget state changed:")
            print(f"  Text:   {state['text']}")
            print(f"  Case:   {state['CA']}")
            print(f"  Word:   {state['MW']}")
            print(f"  RegEx:  {state['RegEx']}")
            print("-" * 20)
            
            
        # ttk.Button(self.pins_header_canvas, text="Corner").pack(
        #     fill=tk.BOTH, expand=True, 
        # )
        

        find_frame = FindWidget(self.pins_header_frame, on_change_callback=on_find_change, style="TFrame")
        # find_frame.pack(side=tk.TOP, fill=tk.X)
        find_frame.grid(row=1, column=1, columnspan=100, sticky=tk.NSEW)
        # ttk.Button(self.pins_header_canvas, text="Pin").pack(
        #     fill=tk.BOTH, expand=True, 
        # )
        
        ttk.Button(self.pins_header_frame, text="Corner").grid(
            row=2, column=1 
        )
        
        
        
        
        
        
        # DATA_2 = {
        #     'NEW_catA': [{'rule': 'NewRuleA1', 'severity': 'Warning', 'col': 1, 'hide': True},
        #     {'rule': 'NewRuleA2', 'severity': 'Error', 'col': 2, 'hide': False}],
        #     'NEW_catB': [{'rule': 'NewRuleB1', 'severity': 'Fatal', 'col': 1, 'hide': True}]
        # }
        
        
        


        
        
        
        
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
        # menu = HiddenRulseRetriveMenu(
        #     parent_widget=action_button, 
        #     data_dict=initial_data, 
        #     on_change_callback=my_callback
        # )
        # #  menu.update_data(new_data)
        
        # #* Filter
        
        # # --- 1. Define the callback function ---
        # def print_selection_handler(selected_list: List[str]) -> None:
        #     """
        #     This is the function that will be called by the class
        #     every time the selection changes.
        #     """
        #     print("--- Selected Items ---")
        #     if not selected_list:
        #         print("None")
        #     else:
        #         for item in selected_list:
        #             print(f"- {item}")
        #     print("------------------------\n")


        # # --- 3. The Model Data ---
        # LOG_LEVELS = {
        #     "Error":   {"color": "#FF4136", "default": True},
        #     "Warning": {"color": "#FF851B", "default": True},
        #     "Fatal":   {"color": "#B10DC9", "default": False}
        # }

       
        
        # self.macro_name_frame = ttk.Frame(self.macro_severity_frmae, style="Tiny.TFrame")
        # self.macro_name_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # self.severity_filter_frame = ttk.Frame(self.macro_severity_frmae)
        # self.severity_filter_frame.pack(side=tk.LEFT)
        
        
        # macro_full_path = "/Users/Developer/Projects/Automation/dc_asdfk__asjdfkk.py"
        # macro_display_name = "dc_asdfk__asjdfkk"

        # macro_frame = MacroNameFrame(
        # self.macro_name_frame,
        # macro_name=macro_display_name,
        # macro_path=macro_full_path
        # )
        # macro_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,10))
    
        
        
        #  # --- 4. Instantiate the Class ---
        # # We create the checkbar, passing the root, data, and our handler
        # checkbar = ColoredCheckBox(
        #     parent=self.severity_filter_frame, 
        #     options_data=LOG_LEVELS, 
        #     on_change_callback=print_selection_handler
        # )
        # # Pack the checkbar frame itself
        # checkbar.pack(side=tk.RIGHT)
        
        
        def on_cut(text):
            print(f"Cut clicked by {text}")

        def on_copy(text):
            print(f"Copy clicked by {text}")

        def on_peast(text):
            print(f"Peast clicked by {text}")

        def on_delete(text):
            print(f"Delete clicked by {text}")
            
        def on_hide(hide_info):
            print(f"Request For Hide Col ", hide_info)
            if hide_info["pass_from"] == "header1":
                for index, column in enumerate(hide_info["header1"]):
                    if index == 0:
                        for each_widget in self.columnwise_cell_database[column]["header1"]:
                            each_widget.grid_forget()
                            self.columnwise_cell_database[column]["header1"][each_widget]["hide"] = True
                        
                    for each_widget in self.columnwise_cell_database[column]["header2"]:
                        each_widget.grid_forget()
                        self.columnwise_cell_database[column]["header2"][each_widget]["hide"] = True
                        
                    for each_widget in self.columnwise_cell_database[column]["body"]:
                        each_widget.grid_forget()
                        self.columnwise_cell_database[column]["body"][each_widget]["hide"] = True
                        
            if hide_info["pass_from"] == "header2":
                 for index, column in enumerate(hide_info["header2"]):
                    for each_widget in self.columnwise_cell_database[column]["header2"]:
                        each_widget.grid_forget()
                        self.columnwise_cell_database[column]["header2"][each_widget]["hide"] = True
                     
                    # count = 0   
                    # for column in hide_info["header1"]:
                    #     for each_widget in self.columnwise_cell_database[column]["header2"]:
                    #         if self.columnwise_cell_database[column]["header2"][each_widget]["hide"] == False:
                    #             count += 0
                    count = sum(1 for column in hide_info["header1"] for each_widget in self.columnwise_cell_database[column]["header2"] if self.columnwise_cell_database[column]["header2"][each_widget].get("hide") == False)
                                
                                
                    if count == 0:
                        for each_widget in self.columnwise_cell_database[hide_info["header1"][0]]["header1"]:
                            each_widget.grid_forget()
                            self.columnwise_cell_database[hide_info["header1"][0]]["header1"][each_widget]["hide"] = True
                        
                        
                    for each_widget in self.columnwise_cell_database[column]["body"]:
                        each_widget.grid_forget()
                        self.columnwise_cell_database[column]["body"][each_widget]["hide"] = True
                        
                    
                    
                    
                # {header1:[], header2:[], pass_from="header1"}

        menu_item_list = [
            {"menu_name": "Hide", "on_call": on_hide},
            # {"menu_name": "Cut", "on_call": on_cut},
            # {"menu_name": "Copy", "on_call": on_copy},
            # {"menu_name": "Peast", "on_call": on_peast},  # Spelled as requested
            # "separator",
            # {"menu_name": "Delete", "on_call": on_delete},
        ]
        
        self.header_menu = TableHeaderMenu(self.layout, menu_items=menu_item_list, tearoff=0)
        
        
        
        
        
        
        
        
        
        
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
    
    
    
    def update_details_view(self, details): 
        self.details_view.config(state="normal")
        self.details_view.delete("1.0", "end")
        # self.details_view.config(state="disabled")
        
        self.details_view.insert("1.0", details)
        self.details_view.see("1.0")
        self.details_view.config(state="disabled")
        
        print("=>", details)
    
    
    
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
            self.placeholder_v_scroll.grid()
            self.h_scroll_enabled = True # <-- MODIFIED
        else:
            self.h_scroll.grid_remove()
            self.placeholder_v_scroll.grid_remove()
            self.h_scroll_enabled = False # <-- MODIFIED
        
        
    def create_spreadsheet_content(self, rows, cols):
        # self.pin_rows_frame.grid_columnconfigure(0, minsize=100)
        
        
        
        
            
            # for each_rules in pin_data[each_pin]["rules"]:
        
        
        
        #! -------------
        self.pin_rows_frame
        self.violations_header_frame
        self.violations_rows_frame
        
        
        self.columnwise_cell_database = {}
        
        self.rules_column_info = {}
        self.volation_header_info = {}
        
        cat_row = 1
        rul_row = 2
        cat_col = 0
        rul_col = 0
        for each_cat in self.RULE_CATEGORY:
            cat_col += 1
            if each_cat not in self.volation_header_info:
                self.volation_header_info[each_cat] = {"rules":{}}
                
            self.volation_header_info[each_cat]["widget"] = ttk.Button(self.violations_header_frame, text=f"{each_cat}", style="Header.TButton")
            self.volation_header_info[each_cat]["widget"].grid(row=cat_row, column=cat_col, columnspan=len(self.RULE_CATEGORY[each_cat]), sticky="nsew")
            self.volation_header_info[each_cat]["grid"] = {"row":cat_row, "column":cat_col}
            self.bind_mouse_wheel(self.volation_header_info[each_cat]["widget"])
            col_list = [i for i in range(cat_col, cat_col + len(self.RULE_CATEGORY[each_cat]) )]# For hide columes under this cat
            
            self.volation_header_info[each_cat]["widget"].bind("<Button-3>", lambda e, m=self.header_menu, hide_info = {"header1":col_list, "header2":[], "pass_from":"header1"} : show_menu(e, m, hide_info))
            
            column = cat_col
            header_btn_widget = self.volation_header_info[each_cat]["widget"]
            # Storing Columnwize data to for hiding and unhiding data
            if column not in self.columnwise_cell_database:
                self.columnwise_cell_database[column] = {}
            if "header1" not in self.columnwise_cell_database[column]:
                self.columnwise_cell_database[column]["header1"] = {}
            if header_btn_widget not in self.columnwise_cell_database[column]["header1"]:
                self.columnwise_cell_database[column]["header1"][header_btn_widget] = {"row":1, "hide":False, "columnspan":len(self.RULE_CATEGORY[each_cat])}
            
            
            if len(self.RULE_CATEGORY[each_cat]) > 1:
                cat_col += len(self.RULE_CATEGORY[each_cat]) - 1
            
            
            for index, each_rule in enumerate(self.RULE_CATEGORY[each_cat]):
                rul_col += 1
                if each_rule['rule'] not in self.volation_header_info[each_cat]:
                    self.volation_header_info[each_cat]["rules"][each_rule['rule']] = {"widget":None}
                
                column = rul_col
                header_btn_widget = self.volation_header_info[each_cat]["rules"][each_rule['rule']]["widget"]
                
                header_btn_widget = ttk.Button(self.violations_header_frame, text=f"{each_rule['rule']}", style="Header.TButton" )
                header_btn_widget.grid(row=rul_row, column=rul_col, sticky="nsew")
                self.volation_header_info[each_cat]["rules"][each_rule['rule']]["grid"] = {"row":rul_row, "column":rul_col}
                self.rules_column_info[f"{each_cat}__{each_rule['rule']}"] = {"row":rul_row, "column":rul_col}                
                self.bind_mouse_wheel(header_btn_widget)
                header_btn_widget.bind("<Button-3>", lambda e, m=self.header_menu,  hide_info = {"header1":col_list, "header2":[column], "pass_from":"header2"} : show_menu(e, m, hide_info))
                
                # Storing Columnwize data to for hiding and unhiding data
                if column not in self.columnwise_cell_database:
                    self.columnwise_cell_database[column] = {}
                if "header2" not in self.columnwise_cell_database[column]:
                    self.columnwise_cell_database[column]["header2"] = {}
                if header_btn_widget not in self.columnwise_cell_database[column]["header2"]:
                    self.columnwise_cell_database[column]["header2"][header_btn_widget] = {"row":2, "hide":False, "columnspan":1}
                # update col
                self.RULE_CATEGORY[each_cat][index]["col"] = rul_col
                self.RULE_CATEGORY[each_cat][index]["hide"] = False
        
        
        
        
        
        all_rules = set(self.rules_column_info.keys())
        for each_pin in pin_data:
            available_keys = set(pin_data[each_pin]["rules"].keys())
            missing_rules = all_rules - available_keys
            print(missing_rules)
            for each_missing_rules in missing_rules:
                pin_data[each_pin]["rules"][each_missing_rules] = {"status":"missing"}
        
        
        
        
        
        
        btn_color = {
            "passed" : "Violation.Status.Passed.TButton",
            "failed" : "Violation.Status.Faield.TButton",
            "N/A" : "Violation.Status.N/A.TButton",
            "missing" : "Violation.Status.N/A.TButton",
        }
        
        
        
        
        self.pininfo_rows = {}
        
        pin_info_header_row = 1        
        pin_info_header_col = 0
        pin_info_body_row = 0
        pin_info_body_col = 1

        for each_pin in pin_data:
            pin_info_body_row += 1
            
            if each_pin not in self.pininfo_rows:
                self.pininfo_rows[each_pin] = {"rules":{}}
             
            #Left Frame   
            self.pininfo_rows[each_pin]["widget"] = ttk.Button(self.pin_rows_frame, text=f"{each_pin}", style="Header.TButton")
            self.pininfo_rows[each_pin]["widget"].grid(row=pin_info_body_row, column=pin_info_body_col,  sticky="nsew")
            self.pininfo_rows[each_pin]["grid"] = {"row":pin_info_body_row, "column":pin_info_body_col}
            self.bind_mouse_wheel(self.pininfo_rows[each_pin]["widget"])
            # print(self.pininfo_rows[each_pin]["grid"])
            
            #Right Frame
            for each_rules in pin_data[each_pin]["rules"]:       
                self.pininfo_rows[each_pin]["rules"]={each_rules:{"widget":None}}
                
                each_pin_individual_rules_info = pin_data[each_pin]["rules"][each_rules]
                status = each_pin_individual_rules_info["status"]
                status_details = each_pin_individual_rules_info["details"] if "details" in each_pin_individual_rules_info else "-"
                status_btn_widget = self.pininfo_rows[each_pin]["rules"][each_rules]["widget"]
                column = self.rules_column_info[each_rules]["column"] # For pacing each violation to its deseard rule colum
                
                status_btn_widget = ttk.Button(self.violations_rows_frame, text=f"{status}", style=btn_color[status], command=lambda details=status_details  : self.update_details_view(details))
                status_btn_widget.grid(row=pin_info_body_row, column=column ,  sticky="nsew")
                
                # Storing Columnwize data to for hiding and unhiding data
                if column not in self.columnwise_cell_database:
                    self.columnwise_cell_database[column] = {}
                if "body" not in self.columnwise_cell_database[column]:
                    self.columnwise_cell_database[column]["body"] = {}
                if status_btn_widget not in self.columnwise_cell_database[column]["body"]:
                    self.columnwise_cell_database[column]["body"][status_btn_widget] = {"row":pin_info_body_row, "hide":False, "columnspan":1}
                
                self.bind_mouse_wheel(status_btn_widget)
                # self.pininfo_rows[each_pin]["grid"] = {"row":pin_info_body_row, "column":pin_info_body_col}
                
        # print(self.rules_column_info)
        print(self.columnwise_cell_database)
        
        print()
        print()
        
        print(self.get_rules_with_visibility())
        
        #!--------
        self.rule_filter = ColumnFilter(self.filter_section, {}, on_update=self.handle_filter_update)
        self.rule_filter.pack(fill="both", expand=True)
        #!Update col into the filter
        self.rule_filter.update_data(self.RULE_CATEGORY)
        
        
        
        # for r in range(rows):
        #     header_btn = ttk.Button(self.pin_rows_frame, text=f"Row {r+1}", 
        #                             style="Header.TButton")
        #     header_btn.grid(row=r, column=0, sticky="nsew")
        #     # --- ADDED BINDING ---
        #     self.bind_mouse_wheel(header_btn)

        # for c in range(cols):
        #     col_name = chr(ord('A') + c)
        #     self.violations_header_frame.grid_columnconfigure(c, minsize=100)
        #     self.violations_rows_frame.grid_columnconfigure(c, minsize=100)
        #     header_btn = ttk.Button(self.violations_header_frame, text=f"Column {col_name}", 
        #                             style="Header.TButton")
        #     header_btn.grid(row=0, column=c, sticky="nsew")
        #     # --- ADDED BINDING ---
        #     self.bind_mouse_wheel(header_btn)

        # for r in range(rows):
        #     for c in range(cols):
        #         cell_btn = ttk.Button(self.violations_rows_frame, 
        #                               text=f"R{r+1}, C{c+1}", 
        #                               style="Cell.TButton")
        #         cell_btn.grid(row=r, column=c, sticky="nsew")
        #         # --- ADDED BINDING ---
        #         self.bind_mouse_wheel(cell_btn)
    


    #* Helper Fuction
    # Transform the dictionary
    def get_rules_with_visibility(self):
        result = {}
        for category, rules in self.RULE_CATEGORY.items():
            result[category] = []
            for i, rule_dict in enumerate(rules, 1):
                # Create a new dictionary with the existing rule and severity, and add col and hide
                new_rule = rule_dict.copy()
                new_rule['col'] = i  # Column number starting from 1
                new_rule['hide'] = True  # Always set to True as per your example
                result[category].append(new_rule)
        return result
    
    def handle_filter_update(self, data):
            """
            This function is passed to the class and will be
            triggered on any change.
            """
            print(data)
            detailed_result = self.get_hidden_non_hidden_col_lists(data)
            #Hide header1
            print(detailed_result["hidden_cat_cols"])
            for column in detailed_result["hidden_cat_cols"]:
                for each_widget in self.columnwise_cell_database[column]["header1"]:
                    each_widget.grid_forget()
                    self.columnwise_cell_database[column]["header1"][each_widget]["hide"] = True
                        
            #Hide header2 & Body            
            print(detailed_result["hidden_rule_cols"])
            for column in detailed_result["hidden_rule_cols"]:
                for each_widget in self.columnwise_cell_database[column]["header2"]:
                    each_widget.grid_forget()
                    self.columnwise_cell_database[column]["header2"][each_widget]["hide"] = True
                
                for each_widget in self.columnwise_cell_database[column]["body"]:
                    each_widget.grid_forget()
                    self.columnwise_cell_database[column]["body"][each_widget]["hide"] = True
                        
            
            
            
            #UnHide header1
            print(detailed_result["non_hidden_cat_cols"])
            for column in detailed_result["non_hidden_cat_cols"]:
                for each_widget in self.columnwise_cell_database[column]["header1"]:
                    each_widget.grid(row=self.columnwise_cell_database[column]["header1"][each_widget]["row"], column=column, columnspan=self.columnwise_cell_database[column]["header1"][each_widget]["columnspan"],  sticky="nsew")
                    self.columnwise_cell_database[column]["header1"][each_widget]["hide"] = False
                        
            #UnHide header2 & Body
            print(detailed_result["non_hidden_rule_cols"])      
            for column in detailed_result["non_hidden_rule_cols"]:
                for each_widget in self.columnwise_cell_database[column]["header2"]:
                    each_widget.grid(row=self.columnwise_cell_database[column]["header2"][each_widget]["row"], column=column, columnspan=self.columnwise_cell_database[column]["header2"][each_widget]["columnspan"],  sticky="nsew")
                    self.columnwise_cell_database[column]["header2"][each_widget]["hide"] = False
                
                for each_widget in self.columnwise_cell_database[column]["body"]:
                    each_widget.grid(row=self.columnwise_cell_database[column]["body"][each_widget]["row"], column=column, columnspan=self.columnwise_cell_database[column]["body"][each_widget]["columnspan"],  sticky="nsew")
                    self.columnwise_cell_database[column]["body"][each_widget]["hide"] = False      
            
           
            
            print("----")
            
    
    def get_hidden_non_hidden_col_lists(self, data):
        """
        Returns hidden and non-hidden column lists for rules and categories
        
        Args:
            data (dict): The rule data dictionary
            
        Returns:
            dict: Contains four lists of column numbers:
                - hidden_rule_cols: List of hidden rule column numbers
                - non_hidden_rule_cols: List of non-hidden rule column numbers 
                - hidden_cat_cols: List of hidden category lowest column numbers
                - non_hidden_cat_cols: List of non-hidden category lowest column numbers
        """
        
        hidden_rule_cols = []
        non_hidden_rule_cols = []
        hidden_cat_cols = []
        non_hidden_cat_cols = []
        
        for category, rules in data.items():
            # Calculate lowest col value among rules in this category
            cat_cols = [rule['col'] for rule in rules]
            lowest_col = min(cat_cols) if cat_cols else 0
            
            # Check if all rules in category are hidden
            all_hidden = all(rule['hide'] for rule in rules)
            
            # Add to appropriate category list
            if all_hidden:
                hidden_cat_cols.append(lowest_col)
            else:
                non_hidden_cat_cols.append(lowest_col)
            
            # Process individual rules - collect only column numbers
            for rule in rules:
                if rule['hide']:
                    hidden_rule_cols.append(rule['col'])
                else:
                    non_hidden_rule_cols.append(rule['col'])
        
        return {
            'hidden_rule_cols': hidden_rule_cols,
            'non_hidden_rule_cols': non_hidden_rule_cols,
            'hidden_cat_cols': hidden_cat_cols,
            'non_hidden_cat_cols': non_hidden_cat_cols
        }

    # # Test the detailed version
    # detailed_result = get_hidden_non_hidden_lists_detailed(DATA_1)
    # print("\nDetailed Results:")
    # print("Hidden Rules:", detailed_result['hidden_rules'])
    # print("Non-Hidden Rules:", detailed_result['non_hidden_rules'])
    # print("Hidden Categories:", detailed_result['hidden_cats'])
    # print("Non-Hidden Categories:", detailed_result['non_hidden_cats'])

    # # Test the detailed version
    # detailed_result = get_hidden_non_hidden_lists_detailed(DATA_1)
    # print("\nDetailed Results:")
    # print("Hidden Rules:", detailed_result['hidden_rules'])
    # print("Non-Hidden Rules:", detailed_result['non_hidden_rules'])
    # print("Hidden Categories:", detailed_result['hidden_cats'])
    # print("Non-Hidden Categories:", detailed_result['non_hidden_cats'])
       



def setup_styles() -> None:
    """Configures all custom ttk styles for the application."""
    style = ttk.Style()
    style.theme_use("clam")

    # style.configure("ViolationViewerLayoutFrame.TFrame", background="#2599c7")
    # style.configure(
    #     "Section.TFrame", background="#f9f9f9", borderwidth=1, relief="solid"
    # )
    # style.configure("Toolbar.TFrame", background="#e6e6e6")
    # style.configure("TLabel", background="#f9f9f9")

    # style.configure("ViolationDetails.TButton", padding=6)
    # style.map(
    #     "ViolationDetails.TButton",
    #     background=[("active", "#d9d9d9")],
    #     relief=[("pressed", "sunken"), ("!pressed", "raised")],
    # )
    
    
    
    # Style From ViolationTable
    style.configure("Tiny.TButton", padding=(3,6))  # (x, y)
    style.configure("Tiny.TFrame", background="#00eb33" )  # (x, y)
    
    style.configure( "ViolationTable.PinInfo.Header.TFrame", background="#b3ff3a", borderwidth=0, relief="solid" )
    style.configure( "ViolationTable.PinInfo.Data.TFrame", background="#ff6a6a", borderwidth=0, relief="solid" )
    style.configure( "ViolationTable.Rules.Header.TFrame", background="#7a9eff", borderwidth=0, relief="solid" )
    style.configure( "ViolationTable.Rules.Status.TFrame", background="#a800f7", borderwidth=0, relief="solid" )
       
    
    style.configure("Violation.Status.Passed.TButton", background="#6BC5A0", foreground="#0E2A20")
    style.configure("Violation.Status.Faield.TButton", background="#FF9E8C", foreground="#3D0E07")
    style.configure("Violation.Status.N/A.TButton", background="#AFC3D6", foreground="#1A242E")

    style.map("Violation.Status.Passed.TButton",
        background=[('disabled', '#DCE0E3'), ('pressed', 'hover', '#28A06E'), ('pressed', '#34B27E'), ('hover', '#5ABF91')],
        foreground=[('disabled', '#A6AFB8'), ('pressed', 'hover', '#E8FFF4'), ('pressed', '#FFFFFF'), ('hover', '#082018')]
    )
    style.map("Violation.Status.Faield.TButton",
        background=[('disabled', '#DCE0E3'), ('pressed', 'hover', '#E74B3C'), ('pressed', '#F35C4A'), ('hover', '#FF8A75')],
        foreground=[('disabled', '#A6AFB8'), ('pressed', 'hover', '#FFF3F1'), ('pressed', '#FFFFFF'), ('hover', '#2A0A05')]
    )
    style.map("Violation.Status.N/A.TButton",
        background=[('disabled', '#DCE0E3'), ('pressed', 'hover', '#6C88A1'), ('pressed', '#7E9AB3'), ('hover', '#A2B8CD')],
        foreground=[('disabled', '#A6AFB8'), ('pressed', 'hover', '#F0F6FA'), ('pressed', '#FFFFFF'), ('hover', '#141E26')]
    )
    
    
    #Style for ColumnFilter Class
    style.configure("CollumnFilter.Content.TFrame", background="#ffffff")
    style.configure("CollumnFilter.Filter.TFrame", background="#e0e0e0")   
    style.configure("CollumnFilter.Content.TCheckbutton", background="#ffffff")
    style.configure( "CollumnFilter.TLabelframe.Label", background="#e0e0e0", font=("Helvetica", 10, "bold") )



if __name__ == "__main__":
    root = tk.Tk()
    root.title("Violation Viewer Layout Demo")
    root.geometry("1000x600")

    # Set up the styles first
    setup_styles()

    # Create and pack the main widget
    violation_viewr_layout = ViolationViewerLayoutFrame(root)
    violation_viewr_layout.pack(expand=True, fill=tk.BOTH)
    ViolationTable(violation_viewr_layout)

    root.mainloop()
