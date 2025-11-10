import tkinter as tk
from tkinter import ttk
import json
from typing import Dict, Callable, Any, Optional

class CheckbuttonMenu:
    """
    A class that creates a right-click, multi-select checkbutton popup menu
    for a given parent widget. It manages its state from a data dictionary
    and triggers an external callback function on any change.
    """
    
    def __init__(self, 
                 parent_widget: ttk.Widget, 
                 data_dict: Dict[str, Any], 
                 on_change_callback: Callable[[Dict[str, Any]], None]
                 ) -> None:
        """
        Initialize the CheckbuttonMenu.
        
        :param parent_widget: The widget to bind the right-click event to.
        :param data_dict: The initial data dictionary to build the menu from.
        :param on_change_callback: A function to call when data changes. 
                                 It will be passed the full, updated data_dict.
        """
        self.parent_widget: ttk.Widget = parent_widget
        self.data_dict: Dict[str, Any] = data_dict
        self.on_change_callback: Callable[[Dict[str, Any]], None] = on_change_callback
        
        # Internal state
        self.tk_vars: Dict[str, Any] = {}
        self.popup_window: Optional[tk.Toplevel] = None
        
        self._build_tk_vars()
        
        # Bind the right-click event to the parent widget
        self.parent_widget.bind("<Button-3>", self.show_popup)

    def update_data(self, new_data_dict: Dict[str, Any]) -> None:
        """
        Public method to load a new data_dict into the menu.
        """
        self.data_dict = new_data_dict
        self._build_tk_vars()
        print("--- Menu data updated ---")

    def _build_tk_vars(self) -> None:
        """
        Private: Clears and rebuilds the internal tk.BooleanVar dictionary
        based on the current self.data_dict.
        """
        self.tk_vars = {
            'master': tk.BooleanVar(),
            'categories': {}
        }
        
        all_true = True
        
        for cat_name, cat_data in self.data_dict.items():
            cat_var = tk.BooleanVar(value=cat_data.get('status', False))
            sub_vars = {}
            
            if not cat_data.get('status', False):
                all_true = False
            
            for sub_name, sub_status in cat_data.get('rules', {}).items():
                sub_var = tk.BooleanVar(value=sub_status)
                sub_vars[sub_name] = sub_var
                if not sub_status:
                    all_true = False
            
            self.tk_vars['categories'][cat_name] = {'var': cat_var, 'sub_vars': sub_vars}
        
        self.tk_vars['master'].set(all_true)

    # --- Controller Logic ---
    
    def _sync_and_trigger_callback(self) -> None:
        """
        Private: Reads all tk.BooleanVars, updates the self.data_dict,
        and then calls the external on_change_callback with the updated dict.
        """
        for cat_name, vars_data in self.tk_vars['categories'].items():
            if cat_name not in self.data_dict:
                self.data_dict[cat_name] = {'status': False, 'rules': {}}
                
            self.data_dict[cat_name]['status'] = vars_data['var'].get()
            
            for sub_name, sub_var in vars_data['sub_vars'].items():
                if 'rules' not in self.data_dict[cat_name]:
                    self.data_dict[cat_name]['rules'] = {}
                self.data_dict[cat_name]['rules'][sub_name] = sub_var.get()
        
        if self.on_change_callback:
            self.on_change_callback(self.data_dict)

    def _on_mark_all_toggle(self) -> None:
        """Called when the 'Mark all' checkbox is toggled."""
        new_state = self.tk_vars['master'].get()
        for cat_name, vars_data in self.tk_vars['categories'].items():
            vars_data['var'].set(new_state)
            for sub_var in vars_data['sub_vars'].values():
                sub_var.set(new_state)
        self._sync_and_trigger_callback()

    def _on_category_toggle(self, cat_name: str) -> None:
        """Called when a parent category checkbox is toggled."""
        new_state = self.tk_vars['categories'][cat_name]['var'].get()
        for sub_var in self.tk_vars['categories'][cat_name]['sub_vars'].values():
            sub_var.set(new_state)
        self._sync_and_trigger_callback()

    def _on_sub_category_toggle(self, cat_name: str) -> None:
        """Called when a sub-rule checkbox is toggled."""
        sub_vars = self.tk_vars['categories'][cat_name]['sub_vars'].values()
        is_any_sub_checked = any(var.get() for var in sub_vars)
        self.tk_vars['categories'][cat_name]['var'].set(is_any_sub_checked)
        self._sync_and_trigger_callback()

    # --- View & Popup Logic ---
    
    def _check_focus(self) -> None:
        """Checks if focus is still inside the popup. If not, closes it."""
        if not self.popup_window:
            return

        focused_widget = self.parent_widget.focus_get()
        
        # Check if the Toplevel itself is gone or if focus is outside
        try:
            if focused_widget is None or not str(focused_widget).startswith(str(self.popup_window)):
                self.popup_window.destroy()
                self.popup_window = None
        except tk.TclError:
            # This can happen if the window is already destroyed
            self.popup_window = None

    def _on_popup_focus_out(self, event: tk.Event) -> None:
        """When the Toplevel loses focus, wait 10ms then check."""
        self.parent_widget.after(10, self._check_focus)

    def show_popup(self, event: tk.Event) -> None:
        """Destroys any existing popup and creates a new one."""
        
        if self.popup_window:
            self.popup_window.destroy()
            self.popup_window = None
            
        widget = event.widget
        x = widget.winfo_rootx()
        y = widget.winfo_rooty()
        widget_height = widget.winfo_height()
        widget_width = widget.winfo_width()
        menu_y = y + widget_height
        
        self.popup_window = tk.Toplevel(self.parent_widget)
        self.popup_window.overrideredirect(True)

        menu_frame = ttk.Frame(self.popup_window, relief=tk.RAISED, borderwidth=1, style="TFrame")
        menu_frame.pack()

        cb_master = ttk.Checkbutton(
            menu_frame,
            text="Mark all checks visible",
            variable=self.tk_vars['master'],
            command=self._on_mark_all_toggle
        )
        cb_master.pack(anchor=tk.W, padx=5, pady=2)

        ttk.Separator(menu_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=2)

        for cat_name, vars_data in self.tk_vars['categories'].items():
            cb_cat = ttk.Checkbutton(
                menu_frame,
                text=f"{cat_name} (All)",
                variable=vars_data['var'],
                command=lambda c=cat_name: self._on_category_toggle(c)
            )
            cb_cat.pack(anchor=tk.W, padx=5, pady=2)
            
            for sub_name, sub_var in vars_data['sub_vars'].items():
                cb_sub = ttk.Checkbutton(
                    menu_frame,
                    text=f"  {sub_name}",
                    variable=sub_var,
                    command=lambda c=cat_name: self._on_sub_category_toggle(c)
                )
                cb_sub.pack(anchor=tk.W, padx=(20, 5), pady=2)
            
            ttk.Separator(menu_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=2)

        self.popup_window.update_idletasks()
        popup_width = self.popup_window.winfo_width()
        menu_x = (x + widget_width) - popup_width
        
        self.popup_window.geometry(f"+{menu_x}+{menu_y}")

        self.popup_window.bind("<FocusOut>", self._on_popup_focus_out)
        self.popup_window.focus_set()

# --- EXAMPLE USAGE ---

if __name__ == "__main__":
    
    root = tk.Tk()
    root.geometry("400x300")
    root.title("CheckbuttonMenu Class Example")

    # --- 1. Define the callback function ---
    def my_callback(updated_dict: Dict[str, Any]) -> None:
        """
        This function will be called by the class on any change.
        """
        print("--- CALLBACK TRIGGERED ---")
        print(json.dumps(updated_dict, indent=2))
        print("--------------------------\n")

    # --- 2. Define the initial data ---
    initial_data: Dict[str, Any] = {
        'cat1': {'status': True, 'rules': {'subCat1_1': True, 'subCat1_2': True}},
        'cat2': {'status': False, 'rules': {'subCat2_1': False, 'subCat2_2': True}}
    }
    
    # --- 3. Create the button to attach the menu to ---
    action_button = ttk.Button(root, text="Right-Click Me!")
    action_button.pack(pady=30, padx=50)

    # --- 4. Instantiate the class ---
    menu = CheckbuttonMenu(
        parent_widget=action_button, 
        data_dict=initial_data, 
        on_change_callback=my_callback
    )

    # --- 5. Example of updating the data ---
    new_data: Dict[str, Any] = {
        'files': {'status': True, 'rules': {'open': True, 'save': True, 'close': False}},
        'edit': {'status': True, 'rules': {'cut': True, 'copy': True, 'paste': True}}
    }

    update_button = ttk.Button(
        root, 
        text="Load New Data", 
        command=lambda: menu.update_data(new_data)
    )
    update_button.pack(pady=10)

    root.mainloop()