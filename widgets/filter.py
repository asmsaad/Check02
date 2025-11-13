import tkinter as tk
from tkinter import ttk
import pprint


try:
    from widgets.checkbox import ColoredCheckBox
except:
    from ..widgets.checkbox import ColoredCheckBox


class ScrolledFrame(ttk.Frame):
    """
    A pure-ttk scrollable frame that auto-hides its scrollbars
    and fixes flickering and child-scrolling issues.
    """

    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        self.canvas = tk.Canvas(
            self, borderwidth=0, background="#ffffff", highlightthickness=0
        )

        self.v_scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.h_scrollbar = ttk.Scrollbar(
            self, orient="horizontal", command=self.canvas.xview
        )

        self.scrollable_frame = ttk.Frame(self.canvas, style="CollumnFilter.Content.TFrame")

        self.canvas_frame_id = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )

        self.canvas.configure(
            yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set
        )

        self.v_scrollbar.pack(side="right", fill="y")
        self.h_scrollbar.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.bind_scrolling(self.canvas)
        self.bind_scrolling(self.scrollable_frame)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def bind_scrolling(self, widget):
        widget.bind("<MouseWheel>", self.on_mousewheel, add="+")
        widget.bind("<Button-4>", self.on_mousewheel, add="+")
        widget.bind("<Button-5>", self.on_mousewheel, add="+")

    def on_mousewheel(self, event):
        is_shift = (event.state & 0x1) != 0
        delta = 1 if (event.num == 5 or event.delta == -120) else -1

        if is_shift:
            self.canvas.xview_scroll(delta, "units")
        else:
            self.canvas.yview_scroll(delta, "units")


class ColumnFilter(ttk.Frame):
    """
    A hierarchical rule filtering widget.
    This class is now a self-contained ttk.Frame.
    It triggers an external 'on_update' callback with the data dict.
    """

    def __init__(self, master, data, on_update=None,  *args, **kwargs, ):
        super().__init__(master, *args, **kwargs)
        self.data = data
        self.on_update_callback = on_update  # Store the external callback
        self.style = ttk.Style(self)

        self.severity_colors = {
            "Warning": "#E67E22",
            "Error": "#E74C3C",
            "Fatal": "#8E44AD",
        }

        self._create_dynamic_styles()

        self.data_vars = {}
        self.category_vars = {}
        self.severity_vars = {}
        self.filter_scope_var = tk.StringVar(value="all")

        self.total_rule_count = 0
        self.visible_rule_count = 0

        self.initialize_vars()
        self.build_ui()
        self.rebuild_rule_list()  # Initial build

    def _create_dynamic_styles(self):
        """Creates severity-specific styles."""
        self.style.configure(
            "CollumnFilter.Content.TCheckbutton", background="#ffffff", foreground="black"
        )
        for severity, color in self.severity_colors.items():
            style_name = f"{severity}.CollumnFilter.Content.TCheckbutton"
            self.style.configure(style_name, background="#ffffff", foreground=color)

    def initialize_vars(self):
        """Create and link all the tk.BooleanVars to the input data."""
        severities = set()
        for cat_name, rules in self.data.items():
            self.data_vars[cat_name] = {}
            any_rule_checked = False
            for rule in rules:
                self.total_rule_count += 1
                rule_name = rule["rule"]
                severities.add(rule["severity"])

                is_checked = not rule["hide"]
                if is_checked:
                    any_rule_checked = True

                var = tk.BooleanVar(value=is_checked)
                var.trace_add(
                    "write", lambda *args, c=cat_name: self.on_rule_toggled(c)
                )
                self.data_vars[cat_name][rule_name] = var

            cat_var = tk.BooleanVar(value=any_rule_checked)
            cat_var.trace_add(
                "write", lambda *args, c=cat_name: self.on_category_toggled(c)
            )
            self.category_vars[cat_name] = cat_var

        for severity in sorted(list(severities)):
            var = tk.BooleanVar(value=True)
            var.trace_add("write", self.on_filter_changed)
            self.severity_vars[severity] = var

        self.filter_scope_var.trace_add("write", self.on_filter_changed)

    def build_ui(self):
        """Create the main GUI layout."""
        
        
        
        
        filter_frame = ttk.Frame(self, style="CollumnFilter.Filter.TFrame")
        filter_frame.pack(anchor=tk.W)
        
        
        

       
        LOG_LEVELS = {
            "Error": {"color": "#FF4136", "default": True},
            "Warning": {"color": "#FF851B", "default": True},
            "Fatal": {"color": "#B10DC9", "default": False},
        }
        
        
            

        

        
        severtiy_group = ttk.Frame(
            filter_frame, 
            style="CollumnFilter.Filter.TFrame",
            # text="Severtiy"
        )
        severtiy_group.grid(row=1, column=1, sticky=tk.NSEW)    
        self.severtiy_filter_cb = ColoredCheckBox(
            parent=severtiy_group,
            options_data=LOG_LEVELS,
            on_change_callback=self.print_selection_handler,
        )
        self.severtiy_filter_cb.grid(row=1, column=1, sticky=tk.NSEW)
        
        
        
            

        scope_group = ttk.Frame(
            filter_frame,
            style="CollumnFilter.Filter.TFrame",
            # text="Scope"
            padding=(5,0)
        )
        # scope_group = ttk.Labelframe(filter_frame, text="Filter Scope")
        scope_group.grid(row=2, column=1, sticky=tk.NSEW, )

        ttk.Radiobutton(
            scope_group, text="All Rules", variable=self.filter_scope_var, value="all"
        ).pack(anchor="w", side=tk.LEFT)
        ttk.Radiobutton(
            scope_group,
            text="Selected Rules",
            variable=self.filter_scope_var,
            value="selected",
        ).pack(anchor="w", side=tk.LEFT)

        self.status_label = ttk.Label(filter_frame, text="Status...")
        self.status_label.grid(row=3, column=1, sticky=tk.NSEW)



        self.status_bar = ttk.Frame(self, padding=(50, 5), relief="sunken", style="CollumnFilter.Filter.TFrame")
        self.status_bar.pack()

        self.scrolled_frame = ScrolledFrame(self)
        self.scrolled_frame.pack(fill="both", expand=True, side="top")
        self.scrolled_frame.scrollable_frame.config(padding=10)
        
    
    def print_selection_handler(self, selected_list) -> None:
            """Callback function to print the new selection."""
   
            for severity, var in self.severity_vars.items():
            
                if severity in selected_list:
                    self.severity_vars[severity].set(True)
                else:
                    self.severity_vars[severity].set(False)
                
            # print("------------------------\n")

    def rebuild_rule_list(self, *args):
        """Clears and redraws the entire rule list based on current filters."""
        for widget in self.scrolled_frame.scrollable_frame.winfo_children():
            widget.destroy()

        self.visible_rule_count = 0
        active_scope = self.filter_scope_var.get()
        active_severities = {s for s, v in self.severity_vars.items() if v.get()}

        self.untrace_all_vars()

        try:
            for cat_name, rules in self.data.items():
                rules_to_draw = []
                for rule in rules:
                    rule_var = self.data_vars[cat_name][rule["rule"]]
                    is_checked = rule_var.get()
                    passes_severity = rule["severity"] in active_severities

                    if active_scope == "all":
                        if passes_severity:
                            rules_to_draw.append(rule)
                    elif active_scope == "selected":
                        if passes_severity and is_checked:
                            rules_to_draw.append(rule)

                if rules_to_draw:
                    cat_var = self.category_vars[cat_name]
                    any_visible_checked = any(
                        self.data_vars[cat_name][r["rule"]].get() for r in rules_to_draw
                    )
                    cat_var.set(any_visible_checked)

                    cat_check = ttk.Checkbutton(
                        self.scrolled_frame.scrollable_frame,
                        text=cat_name,
                        variable=cat_var,
                        style="CollumnFilter.Content.TCheckbutton",
                    )
                    cat_check.pack(anchor="w", fill="x")
                    self.scrolled_frame.bind_scrolling(cat_check)

                    for rule in rules_to_draw:
                        self.visible_rule_count += 1
                        rule_name = rule["rule"]
                        rule_var = self.data_vars[cat_name][rule_name]
                        severity = rule["severity"]

                        style_name = (
                            f"{severity}.CollumnFilter.Content.TCheckbutton"
                            if severity in self.severity_colors
                            else "CollumnFilter.Content.TCheckbutton"
                        )

                        rule_check = ttk.Checkbutton(
                            self.scrolled_frame.scrollable_frame,
                            text=rule_name,
                            variable=rule_var,
                            style=style_name,
                        )
                        rule_check.pack(anchor="w", fill="x", padx=(20, 0))
                        self.scrolled_frame.bind_scrolling(rule_check)
        finally:
            self.trace_all_vars()

        self.update_status_label()
        self._trigger_update()  # Call the update function

    def on_category_toggled(self, cat_name):
        """Called when a category checkbox is clicked."""
        new_state = self.category_vars[cat_name].get()
        self.untrace_rule_vars(cat_name)
        visible_rule_names = self.get_visible_rule_names(cat_name)

        for rule_name, rule_var in self.data_vars[cat_name].items():
            if rule_name in visible_rule_names:
                rule_var.set(new_state)

        self.trace_rule_vars(cat_name)
        self._trigger_update()

    def on_rule_toggled(self, cat_name):
        """Called when a rule checkbox is clicked."""
        self.untrace_cat_var(cat_name)
        any_checked = any(var.get() for var in self.data_vars[cat_name].values())
        self.category_vars[cat_name].set(any_checked)
        self.trace_cat_var(cat_name)

        if self.filter_scope_var.get() == "selected":
            self.rebuild_rule_list()
        else:
            self._trigger_update()

    def on_filter_changed(self, *args):
        self.rebuild_rule_list()

    def get_visible_rule_names(self, cat_name):
        visible_names = set()
        active_scope = self.filter_scope_var.get()
        active_severities = {s for s, v in self.severity_vars.items() if v.get()}

        for rule in self.data[cat_name]:
            rule_var = self.data_vars[cat_name][rule["rule"]]
            is_checked = rule_var.get()
            passes_severity = rule["severity"] in active_severities

            if (active_scope == "all" and passes_severity) or (
                active_scope == "selected" and passes_severity and is_checked
            ):
                visible_names.add(rule["rule"])
        return visible_names

    # --- Callback Tracing Helpers ---
    def untrace_all_vars(self):
        for var in self.category_vars.values():
            if var.trace_info():
                var.trace_remove("write", var.trace_info()[0][1])
        for rules in self.data_vars.values():
            for var in rules.values():
                if var.trace_info():
                    var.trace_remove("write", var.trace_info()[0][1])

    def trace_all_vars(self):
        for cat_name, var in self.category_vars.items():
            var.trace_add("write", lambda *a, c=cat_name: self.on_category_toggled(c))
        for cat_name, rules in self.data_vars.items():
            for rule_name, var in rules.items():
                var.trace_add("write", lambda *a, c=cat_name: self.on_rule_toggled(c))

    def untrace_rule_vars(self, cat_name):
        for var in self.data_vars[cat_name].values():
            if var.trace_info():
                var.trace_remove("write", var.trace_info()[0][1])

    def trace_rule_vars(self, cat_name):
        for rule_name, var in self.data_vars[cat_name].items():
            var.trace_add("write", lambda *a, c=cat_name: self.on_rule_toggled(c))

    def untrace_cat_var(self, cat_name):
        var = self.category_vars[cat_name]
        if var.trace_info():
            var.trace_remove("write", var.trace_info()[0][1])

    def trace_cat_var(self, cat_name):
        var = self.category_vars[cat_name]
        var.trace_add("write", lambda *a, c=cat_name: self.on_category_toggled(c))

    # --- Output Functions ---
    def update_status_label(self):
        self.status_label.config(
            text=f"Showing {self.visible_rule_count} of {self.total_rule_count} rules"
        )

    def _trigger_update(self):
        """Builds the dict, prints it, and triggers the external callback."""
        updated_dict = {}
        for cat_name, rules in self.data.items():
            updated_dict[cat_name] = []
            for rule in rules:
                rule_name = rule["rule"]
                is_checked = self.data_vars[cat_name][rule_name].get()
                new_rule = rule.copy()
                new_rule["hide"] = not is_checked
                updated_dict[cat_name].append(new_rule)

        # print("\n--- [ColumnFilter] UPDATED DATA DICT ---")
        # # pprint.pprint(updated_dict)
        # print("-------------------------------------------\n")

        # Trigger the external callback
        if self.on_update_callback:
            self.on_update_callback(updated_dict)

    # --- PUBLIC METHOD ---
    def update_data(self, new_data):
        """Public method to load a new data dictionary into the filter."""
        print("--- [ColumnFilter] LOADING NEW DATA ---")
        self.data = new_data

        # Clear all old variables
        self.untrace_all_vars()
        self.data_vars.clear()
        self.category_vars.clear()
        self.severity_vars.clear()

        # Reset counts
        self.total_rule_count = 0
        self.visible_rule_count = 0

        # Re-initialize and rebuild
        self.initialize_vars()
        self.rebuild_rule_list()


if __name__ == "__main__":
    # --- 1. Define the external callback function ---
    def handle_filter_update(data):
        """
        This function is passed to the class and will be
        triggered on any change.
        """
        print(">>> EXTERNAL CALLBACK TRIGGERED <<<")
        # You could now, for example, save this to a file
        # or send it to another part of your application.
        pprint.pprint(data)  # (optional, already printed by the class)
        print(">>> END EXTERNAL CALLBACK <<<")

    # --- 2. Define the data ---
    DATA_1 = {
        "cat1": [
            {"rule": "ruleC1R1", "severity": "Warning", "col": 1, "hide": True},
            {"rule": "ruleC1R2", "severity": "Warning", "col": 2, "hide": True},
        ],
        "cat2": [
            {"rule": "ruleC2R1", "severity": "Error", "col": 1, "hide": True},
            {"rule": "ruleC2R2", "severity": "Fatal", "col": 2, "hide": True},
        ],
        "cat3": [
            {"rule": "ruleC3R1", "severity": "Fatal", "col": 1, "hide": True},
            {"rule": "ruleC3R2", "severity": "Warning", "col": 2, "hide": True},
            {"rule": "ruleC3R3", "severity": "Error", "col": 3, "hide": True},
        ],
        # ... (rest of your data) ...
        "cat4": [{"rule": "ruleC4R1", "severity": "Error", "col": 1, "hide": True}],
        "cat5": [
            {"rule": "ruleC5R1", "severity": "Warning", "col": 1, "hide": True},
            {"rule": "ruleC5R2", "severity": "Fatal", "col": 2, "hide": True},
        ],
    }

    # A smaller, different data set for testing the update method
    DATA_2 = {
        "NEW_catA": [
            {"rule": "NewRuleA1", "severity": "Warning", "col": 1, "hide": True},
            {"rule": "NewRuleA2", "severity": "Error", "col": 2, "hide": False},
        ],
        "NEW_catB": [
            {"rule": "NewRuleB1", "severity": "Fatal", "col": 1, "hide": True}
        ],
    }

    # --- 3. Setup the Root Window and Styles ---
    root = tk.Tk()
    root.title("Column Filter Application")
    root.geometry("500x700")

    style = ttk.Style(root)
    style.theme_use("clam")
    
    style.configure("CollumnFilter.Content.TFrame", background="#ffffff")
    style.configure("CollumnFilter.Filter.TFrame", background="#e0e0e0")   
    style.configure("CollumnFilter.Content.TCheckbutton", background="#ffffff")
    style.configure(
        "CollumnFilter.TLabelframe.Label", background="#e0e0e0", font=("Helvetica", 10, "bold")
    )

    # --- 4. Create the Main App Frame ---
    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill="both", expand=True)

    # --- 5. Load the ColumnFilter widget ---
    filter_app = ColumnFilter(main_frame, DATA_1, on_update=handle_filter_update)
    filter_app.pack(fill="both", expand=True)

    # --- 6. Add a button to test the update_data method ---
    update_button = ttk.Button(
        main_frame,
        text="Load New Data (DATA_2)",
        command=lambda: filter_app.update_data(DATA_2),
    )
    update_button.pack(side="bottom", fill="x", pady=(10, 0))

    root.mainloop()
