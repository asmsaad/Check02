import tkinter as tk
from tkinter import ttk
import threading
import time
import random
from typing import Callable

class SpecLoaderUI(ttk.Frame):
    """
    Professional Async Loader.
    - Frame Padding: 20px (as requested).
    - Height Matching: Entry & Combobox match Button height.
    - Disabled widgets look enabled (White BG).
    - External Macro Update capability.
    """

    def __init__(self, master: tk.Widget, on_macro_load: Callable[[str], None], **kwargs):
        # UPDATED: Added padding=20 to the super().__init__ call
        # This creates the 20px "border/spacing" inside the frame around all widgets
        super().__init__(master, padding=20, **kwargs)
        
        self.on_macro_load = on_macro_load
        
        # Configuration
        self.PLACEHOLDER_SPEC = "Enter Spec Path..."
        self.PLACEHOLDER_MACRO = "Search Macro..."
        
        self.all_macro_data = [
            "Macro_Design_Check_v1", "Macro_Design_Check_v2", 
            "Macro_Elec_Rule_A", "Macro_Elec_Rule_B",
            "Macro_Timing_Signoff", "Macro_Phy_Ver_LVS",
            "Macro_Phy_Ver_DRC", "Macro_Antenna_Fix",
        ]
        
        self.loading = False
        
        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        
        # 1. Minimal Text Styles
        style.configure("Compact.TLabel", font=("Segoe UI", 9), padding=0)
        style.configure("Error.Compact.TLabel", foreground="#d32f2f", font=("Segoe UI", 8), padding=0)
        style.configure("Success.Compact.TLabel", foreground="#2e7d32", font=("Segoe UI", 8), padding=0)
        style.configure("Normal.Compact.TLabel", foreground="#555555", font=("Segoe UI", 8), padding=0)

        # 2. Custom Entry/Combo Style: Force WHITE background when disabled
        style.map("Flat.TEntry",
            fieldbackground=[("disabled", "white"), ("readonly", "white")],
            foreground=[("disabled", "black"), ("readonly", "black")]
        )
        style.map("Flat.TCombobox",
            fieldbackground=[("disabled", "white"), ("readonly", "white")],
            foreground=[("disabled", "black"), ("readonly", "black")]
        )

    def _build_ui(self):
        # Grid Weights: Col 0 grows, Col 1 fixed
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        # --- ROW 0: Spec Input & Load Button ---
        self.ent_spec = ttk.Entry(self, style="Flat.TEntry", foreground="grey")
        self.ent_spec.insert(0, self.PLACEHOLDER_SPEC)
        
        # ipady=4 matches button height
        self.ent_spec.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=0, ipady=4)
        
        self.ent_spec.bind("<FocusIn>", lambda e: self._on_focus_in(self.ent_spec, self.PLACEHOLDER_SPEC))
        self.ent_spec.bind("<FocusOut>", lambda e: self._on_focus_out(self.ent_spec, self.PLACEHOLDER_SPEC))

        self.btn_load = ttk.Button(self, text="Load", command=self._start_loading_process, width=12)
        self.btn_load.grid(row=0, column=1, sticky="ew", padx=0, pady=0)

        # --- ROW 1: Status Message ---
        self.lbl_status = ttk.Label(self, text="", style="Normal.Compact.TLabel")
        self.lbl_status.grid(row=1, column=0, columnspan=2, sticky="w", padx=2, pady=(2, 2))

        # --- ROW 2: Macro Search & Run Button ---
        self.combo_var = tk.StringVar()
        self.cmb_macros = ttk.Combobox(self, textvariable=self.combo_var, state="disabled", style="Flat.TCombobox", foreground="grey")
        self.cmb_macros.set(self.PLACEHOLDER_MACRO)
        
        # ipady=4 matches button height
        self.cmb_macros.grid(row=2, column=0, sticky="ew", padx=(0, 5), pady=0, ipady=4)

        self.cmb_macros.bind("<FocusIn>", lambda e: self._on_focus_in_combo(self.cmb_macros, self.PLACEHOLDER_MACRO))
        self.cmb_macros.bind("<FocusOut>", lambda e: self._on_focus_out_combo(self.cmb_macros, self.PLACEHOLDER_MACRO))
        self.cmb_macros.bind("<KeyRelease>", self._on_combo_keyrelease)
        self.cmb_macros.bind("<<ComboboxSelected>>", self._on_macro_selected)

        self.btn_run_macro = ttk.Button(self, text="Load Macro", state="disabled", width=12, command=self._trigger_macro_load)
        self.btn_run_macro.grid(row=2, column=1, sticky="ew", padx=0, pady=0)

    # ----------------------------------------------------------------
    # API: External Update
    # ----------------------------------------------------------------

    def set_active_macro(self, macro_name: str):
        """Sets the macro from an external source."""
        if self.ent_spec.get() == self.PLACEHOLDER_SPEC:
            self.ent_spec.delete(0, tk.END)
            self.ent_spec.insert(0, "External_Spec_Source")
            self.ent_spec.config(foreground="black")
        
        self.ent_spec.config(state="disabled")
        self.lbl_status.config(text="Macro pre-selected.", style="Normal.Compact.TLabel")
        self.btn_load.config(state="normal", text="Load Another Spec")
        
        self.cmb_macros.config(state="normal")
        self.cmb_macros.config(foreground="black")
        self.combo_var.set(macro_name)
        
        self.btn_run_macro.config(state="normal")

    # ----------------------------------------------------------------
    # Logic: Placeholders
    # ----------------------------------------------------------------
    def _on_focus_in(self, widget, placeholder):
        if widget.get() == placeholder:
            widget.delete(0, tk.END)
            widget.config(foreground='black')

    def _on_focus_out(self, widget, placeholder):
        if not widget.get():
            widget.insert(0, placeholder)
            widget.config(foreground='grey')

    def _on_focus_in_combo(self, widget, placeholder):
        if widget.get() == placeholder:
            widget.set('')
            widget.config(foreground='black')

    def _on_focus_out_combo(self, widget, placeholder):
        if not widget.get():
            widget.set(placeholder)
            widget.config(foreground='grey')

    # ----------------------------------------------------------------
    # Logic: Loading Process
    # ----------------------------------------------------------------
    def _start_loading_process(self):
        if self.btn_load.cget("text") == "Load Another Spec":
            self._reset_ui()
            return

        curr_text = self.ent_spec.get()
        if not curr_text or curr_text == self.PLACEHOLDER_SPEC:
            self.lbl_status.config(text="Error: Enter path.", style="Error.Compact.TLabel")
            return

        self.ent_spec.config(state="disabled")
        self.btn_load.config(state="disabled")
        self.lbl_status.config(text="", style="Normal.Compact.TLabel")
        
        self.loading = True
        self._animate_loading_text(0)
        threading.Thread(target=self._backend_worker, daemon=True).start()

    def _animate_loading_text(self, step):
        if not self.loading: return
        dots = "." * (step % 4)
        self.btn_load.config(text=f"Loading{dots}")
        self.after(300, lambda: self._animate_loading_text(step + 1))

    def _backend_worker(self):
        try:
            time.sleep(1.5)
            if random.random() < 0.2: raise Exception("Timeout.")
            self.after(0, self._on_load_success)
        except Exception as e:
            self.after(0, lambda: self._on_load_fail(str(e)))

    def _on_load_fail(self, error_msg):
        self.loading = False
        self.btn_load.config(text="Load", state="normal")
        self.ent_spec.config(state="normal")
        self.lbl_status.config(text=f"Err: {error_msg}", style="Error.Compact.TLabel")

    def _on_load_success(self):
        self.loading = False
        self.btn_load.config(text="Done")
        self.lbl_status.config(text="Loaded.", style="Success.Compact.TLabel")
        self.after(1500, self._finalize_success_state)

    def _finalize_success_state(self):
        self.lbl_status.config(text="Select macro.", style="Normal.Compact.TLabel")
        self.btn_load.config(text="Load Another Spec", state="normal")
        
        self.cmb_macros.config(state="normal")
        self.cmb_macros['values'] = self.all_macro_data
        self.cmb_macros.focus_set()
        self._on_focus_in_combo(self.cmb_macros, self.PLACEHOLDER_MACRO)
        
        try: self.tk.call('ttk::combobox::Post', self.cmb_macros)
        except: pass

    def _reset_ui(self):
        self.ent_spec.config(state="normal")
        self.ent_spec.delete(0, tk.END)
        self._on_focus_out(self.ent_spec, self.PLACEHOLDER_SPEC)
        
        self.btn_load.config(text="Load")
        self.lbl_status.config(text="")
        
        self.combo_var.set("")
        self.cmb_macros.config(state="disabled", values=[])
        self._on_focus_out_combo(self.cmb_macros, self.PLACEHOLDER_MACRO)
        self.btn_run_macro.config(state="disabled")

    # ----------------------------------------------------------------
    # Logic: Search
    # ----------------------------------------------------------------
    def _on_combo_keyrelease(self, event):
        if event.keysym in ['Up', 'Down', 'Return', 'Tab', 'Escape', 'Left', 'Right']: return
        typed = self.combo_var.get().lower()
        
        if typed == '' or typed == self.PLACEHOLDER_MACRO.lower():
            self.cmb_macros['values'] = self.all_macro_data
        else:
            filtered = [item for item in self.all_macro_data if typed in item.lower()]
            self.cmb_macros['values'] = filtered
            if filtered:
                try: self.tk.call('ttk::combobox::Post', self.cmb_macros)
                except tk.TclError: pass

    def _on_macro_selected(self, event):
        val = self.combo_var.get()
        if val and val != self.PLACEHOLDER_MACRO:
            self.btn_run_macro.config(state="normal")

    def _trigger_macro_load(self):
        selected_macro = self.combo_var.get()
        if self.on_macro_load and selected_macro != self.PLACEHOLDER_MACRO:
            self.on_macro_load(selected_macro)

# ----------------------------------------------------------------
# Driver Code
# ----------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Padded Loader")
    root.geometry("550x200") # Adjusted for padding
    
    style = ttk.Style()
    style.theme_use("clam")
    
    def my_callback(val): print(f"Exec: {val}")

    # Note: No padding in pack(), because padding is now internal to the frame (20px)
    app = SpecLoaderUI(root, on_macro_load=my_callback)
    app.pack(fill=tk.X, anchor="n")

    def test_external_update():
        app.set_active_macro("External_Macro_X")

    ttk.Button(root, text="Simulate External Update", command=test_external_update).pack(pady=10)

    root.mainloop()