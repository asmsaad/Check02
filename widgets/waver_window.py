import tkinter as tk
from tkinter import ttk, messagebox
import platform
from typing import Dict, Any, List

# --- Configuration Constants ---
SEVERITY_COLORS = {
    "Error": "#d32f2f",         # Red
    "Fatal": "#880e4f",         # Dark Magenta
    "Warning": "#ef6c00",       # Dark Orange
    "Justification": "#7b1fa2", # Purple
    "Message": "#1565c0"        # Blue
}

class RuleSelectorFrame(ttk.Frame):
    """
    Advanced Rule Manager.
    - Resizable Text Area (PanedWindow).
    - Real-time Category Counts (e.g., "Cat [1/3]").
    - Static styling (No hover effects).
    """

    def __init__(self, master: tk.Widget, data: Dict[str, Any] = None, on_submit=None, **kwargs) -> None:
        super().__init__(master, **kwargs)
        
        self.data = data if data else {}
        self.on_submit_callback = on_submit
        self.vars = {} 
        
        self._setup_styles()
        self._setup_ui_structure()
        self.load_data(self.data)

    def _setup_styles(self) -> None:
        """
        Configures styles to remove hover effects (No visual change on active state).
        """
        style = ttk.Style()
        
        # 1. Checkbutton: Force white background on 'active' (hover) state
        style.layout("NoHover.TCheckbutton", style.layout("TCheckbutton")) # Copy layout
        style.configure("NoHover.TCheckbutton", background="white", font=("Segoe UI", 10))
        
        # Map states to ensure no color change on hover/press
        style.map("NoHover.TCheckbutton",
            background=[('active', 'white'), ('pressed', 'white'), ('!disabled', 'white')],
            indicatorbackground=[('active', 'white'), ('pressed', 'white')],
            foreground=[('active', 'black'), ('!disabled', 'black')]
        )
        
        # 2. PanedWindow Sash (Handle) Styling
        style.configure("Sash", sashthickness=4, sashrelief="raised")

    # ----------------------------------------------------------------
    # UI Structure (PanedWindow Implementation)
    # ----------------------------------------------------------------

    def _setup_ui_structure(self) -> None:
        # 1. Fixed Top Status Bar
        self._status_frame = tk.Frame(self, bg="#f8f9fa", height=40)
        self._status_frame.pack(fill=tk.X, side=tk.TOP)
        tk.Frame(self, bg="#e0e0e0", height=1).pack(fill=tk.X, side=tk.TOP) # Divider line
        
        # 2. Paned Window (Holds List + Footer)
        self._paned_window = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self._paned_window.pack(fill=tk.BOTH, expand=True)

        # --- PANE 1: Scrollable List ---
        self._list_container = tk.Frame(self._paned_window, bg="white")
        self._setup_scroll_area(self._list_container)
        self._paned_window.add(self._list_container, weight=4) # List takes 4 parts space

        # --- PANE 2: Footer (Text Area) ---
        self._footer_container = tk.Frame(self._paned_window, bg="#f0f0f0")
        self._setup_footer(self._footer_container)
        self._paned_window.add(self._footer_container, weight=1) # Footer takes 1 part space

    def _setup_scroll_area(self, parent):
        self._canvas = tk.Canvas(parent, highlightthickness=0, bg="white")
        self._scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self._canvas.yview)
        self._scroll_frame = ttk.Frame(self._canvas) 

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        
        self._canvas_window = self._canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")

        self._scroll_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._bind_universal_scroll(self._canvas)
        self._bind_universal_scroll(self._scroll_frame)

    def _setup_footer(self, parent):
        # Inner frame for padding
        inner = tk.Frame(parent, bg="#f0f0f0", padx=15, pady=10)
        inner.pack(fill=tk.BOTH, expand=True)

        # Drag Handle Hint
        tk.Label(inner, text="::: Drag above to resize :::", bg="#f0f0f0", fg="#aaa", font=("Arial", 6)).pack(anchor="n")

        lbl = tk.Label(inner, text="Justification / Comments", bg="#f0f0f0", fg="#555", font=("Segoe UI", 9, "bold"))
        lbl.pack(anchor="w")
        
        # Text area fills the remaining space in the Pane
        self.text_area = tk.Text(inner, height=5, font=("Segoe UI", 10), relief="flat", bd=1, highlightbackground="#ccc", highlightthickness=1)
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        btn_frame = tk.Frame(inner, bg="#f0f0f0")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Submit Review", command=self.submit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)

    # ----------------------------------------------------------------
    # Data & Rendering
    # ----------------------------------------------------------------

    def load_data(self, new_data: Dict[str, Any]) -> None:
        self.data = new_data
        self.vars = {}
        
        for w in self._scroll_frame.winfo_children(): w.destroy()
        
        if not self.data:
            tk.Label(self._scroll_frame, text="No Data Loaded", bg="white").pack(pady=20)
            self._update_status_bar()
            return

        for cat_name, rules in self.data.items():
            self._build_category_block(cat_name, rules)

        self._update_status_bar()
        self._scroll_frame.update_idletasks()
        self._update_scroll_state()

    def _build_category_block(self, cat_name: str, rules: Dict[str, Any]) -> None:
        cat_frame = tk.Frame(self._scroll_frame, bg="white", pady=8, padx=10)
        cat_frame.pack(fill=tk.X, anchor="nw")
        self._bind_universal_scroll(cat_frame)

        parent_var = tk.BooleanVar(value=False)
        child_vars = {}

        # Parent Checkbox
        cmd = lambda c=cat_name: self._on_parent_click(c)
        chk_parent = ttk.Checkbutton(
            cat_frame, 
            text=cat_name, # Initial text, will be updated immediately
            variable=parent_var, 
            command=cmd, 
            style="NoHover.TCheckbutton"
        )
        chk_parent.pack(anchor="w")
        self._bind_universal_scroll(chk_parent)

        children_frame = tk.Frame(cat_frame, bg="white", padx=25)
        children_frame.pack(fill=tk.X, pady=(2,0))
        self._bind_universal_scroll(children_frame)

        for rule_name, details in rules.items():
            severity = details.get("Severty", "Message")
            child_var = tk.BooleanVar(value=False)
            child_vars[rule_name] = {'var': child_var, 'severity': severity}
            
            row = tk.Frame(children_frame, bg="white")
            row.pack(fill=tk.X, pady=2)
            self._bind_universal_scroll(row)

            child_cmd = lambda c=cat_name: self._on_child_click(c)
            chk = ttk.Checkbutton(
                row, 
                variable=child_var, 
                command=child_cmd, 
                style="NoHover.TCheckbutton"
            )
            chk.pack(side=tk.LEFT)
            self._bind_universal_scroll(chk)

            fg_color = SEVERITY_COLORS.get(severity, "black")
            lbl = tk.Label(
                row, 
                text=f"{rule_name}", 
                fg=fg_color, 
                bg="white", 
                font=("Segoe UI", 10),
                cursor="hand2"
            )
            lbl.pack(side=tk.LEFT, padx=5)
            
            lbl.bind("<Button-1>", lambda e, c=cat_name, r=rule_name: self._toggle_rule_via_label(c, r))
            # Remove hover binding logic (no activebackground set, so standard behavior applies)
            self._bind_universal_scroll(lbl)

        # Store widget reference so we can update text later
        self.vars[cat_name] = {
            'var': parent_var, 
            'widget': chk_parent, 
            'base_name': cat_name,
            'children': child_vars
        }
        
        # Trigger initial text update (e.g., "Cat [0/3]")
        self._update_category_text(cat_name)

    # ----------------------------------------------------------------
    # Logic: Selection, Hierarchy & Dynamic Text
    # ----------------------------------------------------------------

    def _update_category_text(self, cat_name: str) -> None:
        """Updates the Category Checkbutton text with counts."""
        cat_data = self.vars[cat_name]
        children = cat_data['children']
        
        total = len(children)
        selected = sum(1 for d in children.values() if d['var'].get())
        
        # Format: "CategoryName [X/Y Selected]"
        new_text = f"{cat_data['base_name']}   [{selected}/{total}]"
        cat_data['widget'].config(text=new_text)
        #cat_data['widget'].configure( font=("Segoe UI", 11, 'bold'))

    def _toggle_rule_via_label(self, cat_name: str, rule_name: str) -> None:
        target = self.vars[cat_name]['children'][rule_name]['var']
        target.set(not target.get())
        self._on_child_click(cat_name)

    def _on_parent_click(self, cat_name: str) -> None:
        parent_state = self.vars[cat_name]['var'].get()
        for rule_data in self.vars[cat_name]['children'].values():
            rule_data['var'].set(parent_state)
        
        self._update_category_text(cat_name)
        self._update_status_bar()

    def _on_child_click(self, cat_name: str) -> None:
        children = self.vars[cat_name]['children']
        parent_var = self.vars[cat_name]['var']
        
        any_checked = any(d['var'].get() for d in children.values())
        parent_var.set(any_checked)
        
        self._update_category_text(cat_name)
        self._update_status_bar()

    def update_selections_only(self, selection_map: Dict[str, List[str]]) -> None:
        for cat_name, cat_data in self.vars.items():
            target_rules = selection_map.get(cat_name, [])
            children = cat_data['children']
            for rule_name, rule_info in children.items():
                rule_info['var'].set(rule_name in target_rules)
            
            # Sync Logic
            any_checked = any(d['var'].get() for d in children.values())
            cat_data['var'].set(any_checked)
            self._update_category_text(cat_name)
            
        self._update_status_bar()

    # ----------------------------------------------------------------
    # Simsum Status Bar
    # ----------------------------------------------------------------

    def _update_status_bar(self) -> None:
        for w in self._status_frame.winfo_children(): w.destroy()

        stats = {} 
        total_selected = 0
        total_rules = 0

        for cat in self.vars.values():
            for rule in cat['children'].values():
                sev = rule['severity']
                if sev not in stats: stats[sev] = {"total": 0, "selected": 0}
                
                stats[sev]["total"] += 1
                total_rules += 1
                
                if rule['var'].get():
                    stats[sev]["selected"] += 1
                    total_selected += 1

        left_container = tk.Frame(self._status_frame, bg="#f8f9fa", padx=10, pady=5)
        left_container.pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(left_container, text="TOTAL SELECTED", fg="#999", bg="#f8f9fa", font=("Segoe UI", 7, "bold")).pack(anchor="w")
        tk.Label(left_container, text=f"{total_selected} / {total_rules}", fg="#333", bg="#f8f9fa", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        right_container = tk.Frame(self._status_frame, bg="#f8f9fa", padx=10)
        right_container.pack(side=tk.RIGHT, fill=tk.Y)

        priority_order = ["Fatal", "Error", "Warning", "Justification", "Message"]
        for sev in priority_order:
            if sev in stats and stats[sev]["total"] > 0:
                sel = stats[sev]["selected"]
                tot = stats[sev]["total"]
                color = SEVERITY_COLORS.get(sev, "#333")
                
                bg_c = "#f8f9fa"
                fg_c = color if sel > 0 else "#aaa"
                bd_c = color if sel > 0 else "#e0e0e0"
                
                badge = tk.Frame(right_container, bg="white", padx=8, pady=3, highlightbackground=bd_c, highlightthickness=1)
                badge.pack(side=tk.LEFT, padx=5, pady=8)
                tk.Label(badge, text=sev.upper(), fg=fg_c, bg="white", font=("Segoe UI", 7, "bold")).pack(side=tk.LEFT)
                tk.Label(badge, text=f" {sel}/{tot}", fg="#333", bg="white", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

    # ----------------------------------------------------------------
    # Scrolling
    # ----------------------------------------------------------------
    def _on_frame_configure(self, event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._update_scroll_state()

    def _on_canvas_configure(self, event=None):
        self._canvas.itemconfig(self._canvas_window, width=event.width)
        self._update_scroll_state()

    def _update_scroll_state(self):
        req_h = self._scroll_frame.winfo_reqheight()
        vis_h = self._canvas.winfo_height()
        if vis_h < 5: return
        if req_h > vis_h: self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else: self._scrollbar.pack_forget(); self._canvas.yview_moveto(0)

    def _on_mousewheel(self, event):
        if not self._scrollbar.winfo_ismapped(): return
        if platform.system() in ['Windows', 'Darwin']: self._canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        elif event.num == 4: self._canvas.yview_scroll(-1, "units")
        elif event.num == 5: self._canvas.yview_scroll(1, "units")

    def _bind_universal_scroll(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)
        widget.bind("<Button-4>", self._on_mousewheel)
        widget.bind("<Button-5>", self._on_mousewheel)

    # ----------------------------------------------------------------
    # Submit / Cancel
    # ----------------------------------------------------------------
    def submit(self) -> None:
        result_data = {}
        for cat_name, rules in self.data.items():
            result_data[cat_name] = {}
            for rule_name, details in rules.items():
                new_details = details.copy()
                is_checked = False
                if cat_name in self.vars and rule_name in self.vars[cat_name]['children']:
                    is_checked = self.vars[cat_name]['children'][rule_name]['var'].get()
                new_details['checked'] = is_checked
                result_data[cat_name][rule_name] = new_details

        final_payload = {
            "RulesData": result_data,
            "Justification": self.text_area.get("1.0", tk.END).strip()
        }
        if self.on_submit_callback: self.on_submit_callback(final_payload)

    def cancel(self) -> None:
        if messagebox.askyesno("Discard", "Discard changes?"):
            self.load_data(self.data)

# ----------------------------------------------------------------
# Driver Code
# ----------------------------------------------------------------
import random

def generate_mock_data():
    cats = ["Cat1_Design", "Cat2_Elec", "Cat3_Timing"]
    data = {}
    for cat in cats:
        rules = {}
        for i in range(random.randint(2, 5)):
            rules[f"{cat}_Rule_{i+1}"] = {"Severty": random.choice(["Error", "Warning", "Fatal"])}
        data[cat] = rules
    return data

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Rule Review Manager")
    root.geometry("700x800")
    
    # Calm Theme
    style = ttk.Style()
    style.theme_use("clam")

    mock_data = generate_mock_data()
    
    def on_submit(payload):
        print(payload)
        messagebox.showinfo("Submitted", "Data submitted to console.")

    app = RuleSelectorFrame(root, data=mock_data, on_submit=on_submit)
    app.pack(fill=tk.BOTH, expand=True)

    # Control Frame
    ctrl_frame = tk.Frame(root, pady=10)
    ctrl_frame.pack(side=tk.BOTTOM)

    # 1. RESTORED: Totally Update Data (Destroys and Reloads)
    ttk.Button(ctrl_frame, text="Full Reload (New Data)", 
               command=lambda: app.load_data(generate_mock_data())).pack(side=tk.LEFT, padx=5)

    # 2. Update Selection Only (Preserves Widgets)
    def update_selection_demo():
        # Select just the first rule of the first category
        cat = list(mock_data.keys())[0]
        rule = list(mock_data[cat].keys())[0]
        app.update_selections_only({cat: [rule]})
        
    ttk.Button(ctrl_frame, text="Update Selection Only", 
               command=update_selection_demo).pack(side=tk.LEFT, padx=5)

    root.mainloop()