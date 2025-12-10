import tkinter as tk
from tkinter import ttk, messagebox
import platform
import random
from typing import Dict, Any, List

# --- Configuration Constants ---
SEVERITY_COLORS = {
    "Error": "#d32f2f", "Fatal": "#880e4f", "Warning": "#ef6c00", 
    "Justification": "#7b1fa2", "Message": "#1565c0"
}

# Determines the width of the Rule Name column (in characters)
# Adjust this if your rule names are very long
RULE_COLUMN_WIDTH = 50 

class WaverTopLevelWindow:
    def __init__(self, parent: tk.Tk, title: str = "Modal Window", data=None, on_submit=None):
        self.parent = parent
        self.title = title
        self.data = data if data else {}
        self.on_submit = on_submit
        self._window = None  
        self.rules_app = None 

    def show(self):
        if self._window is not None and self._window.winfo_exists():
            self._window.lift()
            self._window.focus_force()
            self._center_window()
            return

        self._window = tk.Toplevel(self.parent)
        self._window.title(self.title)
        # Wider window to accommodate the side-by-side columns comfortably
        self._window.geometry("1000x800") 
        
        self._window.transient(self.parent)
        self._window.grab_set()
        self._window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._setup_ui()
        self._center_window()
        self.parent.wait_window(self._window)

    def _setup_ui(self):
        self.waver_window_content = tk.Frame(self._window)
        self.waver_window_content.pack(fill=tk.BOTH, expand=True)

        self.rules_app = WaverRuelsFrame(
            self.waver_window_content, 
            data=self.data, 
            on_submit=self.on_submit
        )
        self.rules_app.pack(fill=tk.BOTH, expand=True)

        ctrl_frame = tk.Frame(self.waver_window_content, pady=10)
        ctrl_frame.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Button(ctrl_frame, text="Full Reload", 
                   command=lambda: self.rules_app.load_data(generate_mock_data())
                   ).pack(side=tk.LEFT, padx=5)

        ttk.Button(ctrl_frame, text="Submit Review", 
                   command=self.rules_app.submit
                   ).pack(side=tk.RIGHT, padx=5)

    def _center_window(self):
        self._window.update_idletasks()
        p_x = self.parent.winfo_rootx()
        p_y = self.parent.winfo_rooty()
        p_w = self.parent.winfo_width()
        p_h = self.parent.winfo_height()
        w = self._window.winfo_width()
        h = self._window.winfo_height()
        x = p_x + (p_w // 2) - (w // 2)
        y = p_y + (p_h // 2) - (h // 2)
        self._window.geometry(f"+{x}+{y}")

    def _on_close(self):
        confirm_win = tk.Toplevel(self._window)
        confirm_win.title("Confirm Exit")
        confirm_win.geometry("320x140")
        confirm_win.resizable(False, False)
        confirm_win.configure(bg="#f0f0f0")
        confirm_win.transient(self._window)
        confirm_win.grab_set()

        tk.Label(confirm_win, text="Do you want to close this window?", 
                 bg="#f0f0f0", font=("Segoe UI", 10)).pack(pady=(25, 20))

        btn_frame = tk.Frame(confirm_win, bg="#f0f0f0")
        btn_frame.pack(fill=tk.X, pady=10)

        self._confirm_result = False
        def on_yes():
            self._confirm_result = True
            confirm_win.destroy()
        def on_no():
            self._confirm_result = False
            confirm_win.destroy()

        ttk.Button(btn_frame, text="Yes", command=on_yes, width=10).pack(side=tk.LEFT, padx=20, expand=True)
        ttk.Button(btn_frame, text="No", command=on_no, width=10).pack(side=tk.RIGHT, padx=20, expand=True)

        self._window.update_idletasks()
        confirm_win.update_idletasks()
        p_x = self._window.winfo_rootx()
        p_y = self._window.winfo_rooty()
        p_w = self._window.winfo_width()
        p_h = self._window.winfo_height()
        c_w = confirm_win.winfo_reqwidth()
        c_h = confirm_win.winfo_reqheight()
        x = p_x + (p_w // 2) - (c_w // 2)
        y = p_y + (p_h // 2) - (c_h // 2)
        confirm_win.geometry(f"+{int(x)}+{int(y)}")
        
        self._window.wait_window(confirm_win)

        if self._confirm_result:
            self._window.grab_release()
            self._window.destroy()
            self._window = None

class WaverRuelsFrame(ttk.Frame):
    def __init__(self, master: tk.Widget, data: Dict[str, Any] = None, on_submit=None, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.data = data if data else {}
        self.on_submit_callback = on_submit
        self.vars = {} 
        self._setup_styles()
        self._setup_ui_structure()
        self.load_data(self.data)

    def _setup_styles(self) -> None:
        style = ttk.Style()
        style.layout("NoHover.TCheckbutton", style.layout("TCheckbutton"))
        style.configure("NoHover.TCheckbutton", background="white", font=("Segoe UI", 10))
        style.map("NoHover.TCheckbutton",
            background=[('active', 'white'), ('pressed', 'white'), ('!disabled', 'white')],
            indicatorbackground=[('active', 'white'), ('pressed', 'white')],
            foreground=[('active', 'black'), ('!disabled', 'black')]
        )

    def _setup_ui_structure(self) -> None:
        self._status_frame = tk.Frame(self, bg="#f8f9fa", height=40)
        self._status_frame.pack(fill=tk.X, side=tk.TOP)
        tk.Frame(self, bg="#e0e0e0", height=1).pack(fill=tk.X, side=tk.TOP)
        
        self._list_container = tk.Frame(self, bg="white")
        self._setup_scroll_area(self._list_container)
        self._list_container.pack(fill=tk.BOTH, expand=True)

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

    def load_data(self, new_data: Dict[str, Any]) -> None:
        self.data = new_data
        self.vars = {}
        for w in self._scroll_frame.winfo_children(): w.destroy()
        
        if not self.data:
            tk.Label(self._scroll_frame, text="No Data Loaded", bg="white").pack(pady=20)
            self._update_status_bar()
            return

        # --- HEADER ---
        header_frame = tk.Frame(self._scroll_frame, bg="#eee", pady=5, padx=10)
        header_frame.pack(fill=tk.X, anchor="nw") # Ensure it starts at left
        
        # 1. Spacer for the checkbox (approx width)
        tk.Label(header_frame, text=" ", width=4, bg="#eee").pack(side=tk.LEFT) 
        
        # 2. Rule Name Header (Matches RULE_COLUMN_WIDTH)
        tk.Label(header_frame, text="Rules", bg="#eee", width=RULE_COLUMN_WIDTH, anchor="w", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        # 3. Comment Header
        tk.Label(header_frame, text="Justification / Comments", bg="#eee", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=10)

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
        
        # Category Header
        cmd = lambda c=cat_name: self._on_parent_click(c)
        chk_parent = ttk.Checkbutton(cat_frame, text=cat_name, variable=parent_var, command=cmd, style="NoHover.TCheckbutton")
        chk_parent.pack(anchor="w")
        self._bind_universal_scroll(chk_parent)
        
        children_frame = tk.Frame(cat_frame, bg="white", padx=25)
        children_frame.pack(fill=tk.X, pady=(2,0))
        self._bind_universal_scroll(children_frame)
        
        for rule_name, details in rules.items():
            severity = details.get("Severty", "Message")
            existing_comment = details.get("comment", "")
            child_var = tk.BooleanVar(value=False)
            
            row = tk.Frame(children_frame, bg="white")
            row.pack(fill=tk.X, pady=4, anchor="w") # Anchor left
            self._bind_universal_scroll(row)
            
            # 1. Checkbox
            child_cmd = lambda c=cat_name, r=rule_name: self._on_child_click(c, r)
            chk = ttk.Checkbutton(row, variable=child_var, command=child_cmd, style="NoHover.TCheckbutton")
            chk.pack(side=tk.LEFT)
            self._bind_universal_scroll(chk)
            
            # 2. Rule Label (Fixed Width)
            fg_color = SEVERITY_COLORS.get(severity, "black")
            # Using width=RULE_COLUMN_WIDTH ensures the next element (Text) starts at the same spot every time
            lbl = tk.Label(row, text=f"{rule_name}", fg=fg_color, bg="white", 
                           font=("Segoe UI", 10), cursor="hand2",
                           width=RULE_COLUMN_WIDTH, anchor="w") # Fixed Width & Left Align
            lbl.pack(side=tk.LEFT, padx=5)
            lbl.bind("<Button-1>", lambda e, c=cat_name, r=rule_name: self._toggle_rule_via_label(c, r))
            self._bind_universal_scroll(lbl)
            
            # 3. Comment Box (Now packed LEFT immediately after Label)
            txt_comment = tk.Text(row, height=2, width=40, font=("Segoe UI", 9), 
                                  bd=1, relief="solid", highlightthickness=0)
            txt_comment.insert("1.0", existing_comment)
            txt_comment.config(state="disabled", bg="#f0f0f0", fg="#aaa")
            
            # Changed from side=RIGHT to side=LEFT
            txt_comment.pack(side=tk.LEFT, padx=(10, 0), expand=True, fill=tk.X) 
            self._bind_universal_scroll(txt_comment)

            # Store references
            child_vars[rule_name] = {
                'var': child_var, 
                'severity': severity, 
                'widget_comment': txt_comment
            }

        self.vars[cat_name] = {'var': parent_var, 'widget': chk_parent, 'base_name': cat_name, 'children': child_vars}
        self._update_category_text(cat_name)

    def _update_widget_state(self, cat_name: str, rule_name: str) -> None:
        rule_data = self.vars[cat_name]['children'][rule_name]
        is_checked = rule_data['var'].get()
        widget = rule_data['widget_comment']
        
        if is_checked:
            widget.config(state="normal", bg="white", fg="black")
        else:
            widget.config(state="disabled", bg="#f0f0f0", fg="#aaa")

    def _update_category_text(self, cat_name: str) -> None:
        cat_data = self.vars[cat_name]
        children = cat_data['children']
        total = len(children)
        selected = sum(1 for d in children.values() if d['var'].get())
        new_text = f"{cat_data['base_name']}   [{selected}/{total}]"
        cat_data['widget'].config(text=new_text)

    def _toggle_rule_via_label(self, cat_name: str, rule_name: str) -> None:
        target = self.vars[cat_name]['children'][rule_name]['var']
        target.set(not target.get())
        self._on_child_click(cat_name, rule_name)

    def _on_parent_click(self, cat_name: str) -> None:
        parent_state = self.vars[cat_name]['var'].get()
        for rule_name, rule_data in self.vars[cat_name]['children'].items():
            rule_data['var'].set(parent_state)
            self._update_widget_state(cat_name, rule_name)
        self._update_category_text(cat_name)
        self._update_status_bar()

    def _on_child_click(self, cat_name: str, rule_name: str = None) -> None:
        if rule_name:
            self._update_widget_state(cat_name, rule_name)
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
                is_selected = rule_name in target_rules
                rule_info['var'].set(is_selected)
                self._update_widget_state(cat_name, rule_name)
            any_checked = any(d['var'].get() for d in children.values())
            cat_data['var'].set(any_checked)
            self._update_category_text(cat_name)
        self._update_status_bar()

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
                fg_c = color if sel > 0 else "#aaa"
                bd_c = color if sel > 0 else "#e0e0e0"
                badge = tk.Frame(right_container, bg="white", padx=8, pady=3, highlightbackground=bd_c, highlightthickness=1)
                badge.pack(side=tk.LEFT, padx=5, pady=8)
                tk.Label(badge, text=sev.upper(), fg=fg_c, bg="white", font=("Segoe UI", 7, "bold")).pack(side=tk.LEFT)
                tk.Label(badge, text=f" {sel}/{tot}", fg="#333", bg="white", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

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

    def submit(self) -> None:
        result_data = {}
        for cat_name, rules in self.data.items():
            result_data[cat_name] = {}
            for rule_name, details in rules.items():
                new_details = details.copy()
                is_checked = False
                comment_text = ""
                if cat_name in self.vars and rule_name in self.vars[cat_name]['children']:
                    child_data = self.vars[cat_name]['children'][rule_name]
                    is_checked = child_data['var'].get()
                    comment_text = child_data['widget_comment'].get("1.0", tk.END).strip()
                new_details['checked'] = is_checked
                new_details['justification_comment'] = comment_text
                result_data[cat_name][rule_name] = new_details
        final_payload = {
            "RulesData": result_data
        }
        if self.on_submit_callback:
            self.on_submit_callback(final_payload)

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
    root.geometry("600x400")
    style = ttk.Style()
    style.theme_use("clam")
    mock_data = generate_mock_data()
    def on_submit(payload):
        print("--- SUBMITTED PAYLOAD ---")
        for cat, rules in payload["RulesData"].items():
            for rule, data in rules.items():
                if data['checked']:
                    print(f"[{cat}] {rule} | Comment: {data['justification_comment']}")
        messagebox.showinfo("Submitted", "Data submitted to console.")
    modal_app = WaverTopLevelWindow(root, title="My Popup", data=mock_data, on_submit=on_submit)
    def open_window():
        modal_app.show()
    tk.Label(root, text="Main Window (Root)", font=("Arial", 14, "bold")).pack(pady=50)
    ttk.Button(root, text="Open Modal Window", command=open_window).pack(pady=20)
    root.mainloop()