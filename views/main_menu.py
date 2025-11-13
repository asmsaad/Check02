import tkinter as tk
from tkinter import Menu, filedialog, messagebox, ttk
from typing import Dict, Any, Callable, Optional, List
import json
import os

# ---  Preferences Dialog (Unchanged) ---

class PreferencesDialog(tk.Toplevel):
    """A modal dialog for setting application preferences."""
    
    def __init__(self, parent_widget: tk.Widget, data_dict: Dict[str, Any],
                 on_change_callback: Callable[[Dict[str, Any]], None]) -> None:
        super().__init__(parent_widget)
        self.transient(parent_widget)
        self.grab_set()
        self.title("Application Preferences")
        self.geometry(self._center_geometry(parent_widget))
        
        self.initial_data = data_dict.copy()
        self.on_change_callback = on_change_callback
        self.vars: Dict[str, tk.Variable] = {
            'api_timeout': tk.IntVar(value=data_dict.get('api_timeout', 30))
        }
        
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="API Timeout (s):").pack(padx=10, pady=5)
        ttk.Entry(main_frame, textvariable=self.vars['api_timeout']).pack(padx=10, pady=5)
        ttk.Button(main_frame, text="OK", command=self.on_ok).pack(pady=10)
        
        self.wait_window(self)

    def on_ok(self) -> None:
        """Saves settings and closes the dialog."""
        new_settings = {'api_timeout': self.vars['api_timeout'].get()}
        if new_settings != self.initial_data:
            self.on_change_callback(new_settings)
        self.destroy()

    def _center_geometry(self, parent: tk.Widget) -> str:
        """Calculates geometry to center this Toplevel on its parent."""
        parent.update_idletasks()
        parent_x, parent_y = parent.winfo_rootx(), parent.winfo_rooty()
        parent_w, parent_h = parent.winfo_width(), parent.winfo_height()
        
        self.update_idletasks()
        width, height = 300, 150
        self.geometry(f"{width}x{height}")

        x = parent_x + (parent_w // 2) - (width // 2)
        y = parent_y + (parent_h // 2) - (height // 2)
        return f"{width}x{height}+{x}+{y}"


# ---  Main Application Menu Class (Name Changed) ---

class PinCheckScoreboardAppMenu(tk.Menu):
    """
    Manages the main application menu bar (formerly AppMenu).
    
    This class IS a tk.Menu, designed to be attached to the root window.
    It receives callbacks to execute for all menu actions and
    binds its own global accelerators.
    """
    def __init__(
        self, 
        master: tk.Tk, 
        callbacks: Dict[str, Callable],
        initial_history: Optional[List[str]] = None
    ):
        """
        Initializes the menu system.
        """
        super().__init__(master)
        
        self.master = master 
        self.callbacks = callbacks

        # --- State Variables ---
        self.current_file: Optional[str] = None
        self.max_recent_files = 10
        self.recent_files: List[str] = initial_history or []
        self.app_settings: Dict[str, Any] = {"api_timeout": 30}
        
        # --- Tkinter Variables ---
        self.show_details_panel_var = tk.BooleanVar(value=True)
        self.api_collected_var = tk.BooleanVar(value=False)
        self.current_theme = tk.StringVar(value="Light")
        
        self._build_menus()
        self._update_history_menu()
        
    def _build_menus(self):
        """Creates all sub-menus and attaches them to self (the menubar)."""

        # --- File Menu ---
        file_menu = Menu(self, tearoff=0)
        self.add_cascade(label="File", menu=file_menu, underline=0) # F
        self._create_file_menu(file_menu)

        # --- Edit Menu ---
        # edit_menu = Menu(self, tearoff=0)
        # self.add_cascade(label="Edit", menu=edit_menu, underline=0) # E
        # edit_menu.add_command(label="Preferences", command=self._wrap_callback('on_preferences_open'), underline=0) # P

        # --- View Menu ---
        view_menu = Menu(self, tearoff=0)
        self.add_cascade(label="View", menu=view_menu, underline=0) # V
        self._create_view_menu(view_menu)

        # --- Connection Menu ---
        # connection_menu = Menu(self, tearoff=0)
        # self.add_cascade(label="Connection", menu=connection_menu, underline=0) # C
        # self._create_connection_menu(connection_menu)

        # --- Run Menu ---
        run_menu = Menu(self, tearoff=0)
        self.add_cascade(label="Run", menu=run_menu, underline=0) # R
        self._create_run_menu(run_menu)

        # --- Window Menu ---
        # window_menu = Menu(self, tearoff=0)
        # self.add_cascade(label="Window", menu=window_menu, underline=0) # W
        # self._create_window_menu(window_menu)
        
        # --- Help Menu ---
        help_menu = Menu(self, tearoff=0)
        self.add_cascade(label="Help", menu=help_menu, underline=0) # H
        self._create_help_menu(help_menu)

    # --- Menu Creation Helpers (with underline) ---
    
    def _create_file_menu(self, menu: Menu):
        """Builds the 'File' menu."""
        menu.add_command(label="Load YAML...", command=self.load_yaml_file, accelerator="Ctrl+O", underline=0) # L
        menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S", underline=0) # S
        menu.add_command(label="Save As...", command=self.save_file_as, accelerator="Ctrl+Shift+S", underline=5) # A
        menu.add_separator()
        
        self.history_menu = Menu(menu, tearoff=0)
        self.history_menu.config(postcommand=self._wrap_callback('on_history_open', self.recent_files))
        
        menu.add_cascade(label="History", menu=self.history_menu, accelerator="Ctrl+H", underline=0) # H
        menu.add_separator()
        menu.add_command(label="Export...", command=self._wrap_callback('on_export'), underline=0) # E

    def _create_view_menu(self, menu: Menu):
        """Builds the 'View' menu."""
        menu.add_checkbutton(label="Show Details Panel", command=self.toggle_details_panel, variable=self.show_details_panel_var, underline=0) # S
        # menu.add_separator()
        # menu.add_command(label="Heatmap View", command=self._wrap_callback('on_view_select', "heatmap"), underline=0) # H
        # menu.add_command(label="Tabular View", command=self._wrap_callback('on_view_select', "tabular"), underline=0) # T

    # def _create_connection_menu(self, menu: Menu):
    #     """Builds the 'Connection' menu."""
    #     menu.add_checkbutton(label="API Collected", command=self.toggle_api_collected, variable=self.api_collected_var, underline=0) # A
    #     menu.add_command(label="API Connection", command=self._wrap_callback('on_api_connect'), underline=4) # C

    def _create_run_menu(self, menu: Menu):
        """Builds the 'Run' menu."""
        menu.add_command(label="Run", accelerator="F5", command=self._wrap_callback('on_run'), underline=0) # R
        menu.add_command(label="Run with Edit", accelerator="Shift+F5", command=self._wrap_callback('on_run_edit'), underline=5) # w

    # def _create_window_menu(self, menu: Menu):
    #     """Builds the 'Window' menu."""
    #     menu.add_command(label="Window Settings", command=self._wrap_callback('on_window_settings'), underline=0) # W
    #     theme_menu = Menu(menu, tearoff=0)
    #     menu.add_cascade(label="Theme", menu=theme_menu, underline=0) # T
    #     theme_menu.add_radiobutton(label="Light", variable=self.current_theme, value="Light", command=self.change_theme, underline=0) # L
    #     theme_menu.add_radiobutton(label="Dark", variable=self.current_theme, value="Dark", command=self.change_theme, underline=0) # D

    def _create_help_menu(self, menu: Menu):
        """Builds the 'Help' menu."""
        menu.add_command(label="Manual", command=self.show_manual, underline=0) # M
        menu.add_separator()
        menu.add_command(label="System Info", command=self.show_system_info, underline=0) # S
        menu.add_command(label="What's New", command=self.show_whats_new, underline=0) # W
        menu.add_command(label="About", command=self.show_about, underline=0) # A

    # --- Accelerator Binding Method ---
    
    def bind_global_accelerators(self):
        """Binds all global keyboard accelerators to the root window."""
        root = self.winfo_toplevel() 
        
        root.bind('<F5>', lambda e: self._wrap_callback('on_run')())
        root.bind('<Shift-F5>', lambda e: self._wrap_callback('on_run_edit')())
        root.bind('<Control-o>', lambda e: self.load_yaml_file())
        root.bind('<Control-O>', lambda e: self.load_yaml_file())
        root.bind('<Control-s>', lambda e: self.save_file())
        root.bind('<Control-S>', lambda e: self.save_file())
        root.bind('<Control-Shift-S>', lambda e: self.save_file_as())
        root.bind('<Control-h>', lambda e: self._wrap_callback('on_history_open', self.recent_files)())
        root.bind('<Control-H>', lambda e: self._wrap_callback('on_history_open', self.recent_files)())

    # --- Action Handlers (Unchanged) ---
    
    def _wrap_callback(self, callback_name: str, *args: Any) -> Callable:
        """Safely retrieves a callback from the dict and wraps it."""
        callback = self.callbacks.get(callback_name, lambda *a: None)
        return lambda: callback(*args)

    def load_yaml_file(self):
        """Handles the 'Load YAML' file dialog and action."""
        file_path = filedialog.askopenfilename(
            parent=self.master, 
            defaultextension=".yaml", 
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if file_path:
            self.current_file = file_path
            self._wrap_callback('on_file_open', file_path)()
            self._add_to_history(file_path)

    def save_file(self):
        """Handles the 'Save' action."""
        if self.current_file:
            self._wrap_callback('on_file_save', self.current_file)()
        else:
            self.save_file_as()

    def save_file_as(self):
        """Handles the 'Save As' file dialog and action."""
        file_path = filedialog.asksaveasfilename(
            parent=self.master,
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if file_path:
            self.current_file = file_path
            self._wrap_callback('on_file_save_as', file_path)()
            self._add_to_history(file_path)

    def _add_to_history(self, file_path: str):
        """Adds a file path to the top of the recent files list."""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:self.max_recent_files]
        self._update_history_menu()
        self._wrap_callback('on_history_update', self.recent_files)()
            
    def _update_history_menu(self):
        """Rebuilds the 'History' menu from the recent_files list."""
        self.history_menu.delete(0, "end")
        
        if not self.recent_files:
            self.history_menu.add_command(label="(No recent files)", state="disabled")
            return

        for path in self.recent_files:
            cmd = lambda p=path: self._wrap_callback('on_history_select', p)()
            self.history_menu.add_command(label=path, command=cmd)
            
        self.history_menu.add_separator()
        self.history_menu.add_command(label="Clear History", command=self._clear_history)

    def _clear_history(self):
        """Clears all items from the recent files list."""
        self.recent_files.clear()
        self._update_history_menu()
        self._wrap_callback('on_history_update', self.recent_files)()

    # --- Dialog Handlers (Help window position logic updated) ---
    
    def show_preferences(self):
        """Opens the modal PreferencesDialog."""
        self._wrap_callback('on_preferences_open')()
        PreferencesDialog(
            parent_widget=self.master,
            data_dict=self.app_settings,
            on_change_callback=self.update_settings_callback
        )

    def update_settings_callback(self, new_settings: Dict[str, Any]):
        """Callback from the dialog to update internal settings."""
        self.app_settings.update(new_settings)
        self._wrap_callback('on_preferences_update', new_settings)()

    def _create_modal_help_window(self, title: str):
        """Helper function to create a modal Toplevel window."""
        self.master.update_idletasks()
        parent_x, parent_y = self.master.winfo_rootx(), self.master.winfo_rooty()
        parent_w, parent_h = self.master.winfo_width(), self.master.winfo_height()
        
        width, height = 300, 150
        
        # Horizontally center
        x = parent_x + (parent_w // 2) - (width // 2)
        
        # --- MODIFIED: Vertically center, then shift up 20% of parent height ---
        vertical_center = parent_y + (parent_h // 2)
        dialog_offset = (height // 2)
        parent_up_shift = int(parent_h * 0.20) # 20% shift
        
        y = vertical_center - dialog_offset - parent_up_shift
        # --- End Modification ---
        
        top = tk.Toplevel(self.master)
        top.title(title)
        top.geometry(f"{width}x{height}+{x}+{y}")
        top.transient(self.master) 
        top.grab_set()             
        
        ttk.Label(top, text=f"This is the '{title}' window.", padding=20).pack(expand=True)
        ttk.Button(top, text="Close", command=top.destroy).pack(pady=10)
        
        top.wait_window()

    def show_manual(self): self._create_modal_help_window("Manual")
    def show_system_info(self): self._create_modal_help_window("System Info")
    def show_whats_new(self): self._create_modal_help_window("What's New")
    def show_about(self): self._create_modal_help_window("About")

    # --- Simple Toggle/Command Wrappers (Unchanged) ---
    
    def toggle_details_panel(self):
        val = self.show_details_panel_var.get()
        self._wrap_callback('on_view_toggle', "details_panel", val)()

    def toggle_api_collected(self):
        val = self.api_collected_var.get()
        self._wrap_callback('on_api_toggle', val)()
    
    def change_theme(self):
        val = self.current_theme.get()
        self._wrap_callback('on_theme_change', val)()




if __name__ == "__main__":   
    
    
    HISTORY_FILE = "app_history.json"

    def load_history() -> List[str]:
        """Loads the recent files list from a JSON file."""
        if not os.path.exists(HISTORY_FILE):
            return []
        try:
            with open(HISTORY_FILE, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"Error loading history: {e}")
            return []

    def save_history(file_list: List[str]):
        """Saves the recent files list to a JSON file."""
        try:
            with open(HISTORY_FILE, 'w') as f:
                json.dump(file_list, f, indent=2)
            print(f"History saved to {HISTORY_FILE}")
        except Exception as e:
            print(f"Error saving history: {e}")


    def handle_file_open(path: str):
        print(f"CALLBACK: Opening file: {path}")
        root.title(f"Data Analysis Suite - {os.path.basename(path)}")
        
    def handle_file_save(path: str):
        print(f"CALLBACK: Saving file: {path}")
        
    def handle_file_save_as(path: str):
        print(f"CALLBACK: Saving new file: {path}")
        root.title(f"Data Analysis Suite - {os.path.basename(path)}")

    def handle_history_open(file_list: List[str]):
        print(f"CALLBACK: History menu opened. Current list: {file_list}")

    def handle_history_select(path: str):
        print(f"CALLBACK: History item selected: {path}")
        handle_file_open(path)

    def handle_run():
        print("CALLBACK: Executing 'Run' (F5)")
        
    def handle_run_edit():
        print("CALLBACK: Executing 'Run with Edit' (Shift+F5)")
        
    def handle_preferences_open():
        print("CALLBACK: Opening Preferences dialog...")
        
    def handle_preferences_update(settings: Dict[str, Any]):
        print(f"CALLBACK: Settings updated: {settings}")

    def handle_view_toggle(panel: str, is_visible: bool):
        print(f"CALLBACK: View '{panel}' toggled to: {is_visible}")
        
    def handle_view_select(view_name: str):
        print(f"CALLBACK: View switched to: {view_name}")

    def handle_api_toggle(is_collected: bool):
        print(f"CALLBACK: API Collected toggled to: {is_collected}")
        
    def handle_api_connect():
        print("CALLBACK: Attempting API connection...")
        
    def handle_theme_change(theme_name: str):
        print(f"CALLBACK: Theme changed to: {theme_name}")

    

    app_callbacks = {
        'on_file_open': handle_file_open,
        'on_file_save': handle_file_save,
        'on_file_save_as': handle_file_save_as,
        'on_history_update': save_history,
        'on_history_open': handle_history_open,
        'on_history_select': handle_history_select,
        'on_run': handle_run,
        'on_run_edit': handle_run_edit,
        'on_preferences_open': handle_preferences_open,
        'on_preferences_update': handle_preferences_update,
        'on_view_toggle': handle_view_toggle,
        'on_view_select': handle_view_select,
        'on_api_toggle': handle_api_toggle,
        'on_api_connect': handle_api_connect,
        'on_theme_change': handle_theme_change,
        'on_export': lambda: print("CALLBACK: Exporting data..."),
        'on_window_settings': lambda: print("CALLBACK: Opening window settings..."),
    }
    
    
    root = tk.Tk()
    root.title("PinCheckScoreboardAppMenu Menu check")
    root.geometry("800x600")

    initial_history = load_history()
    app_menu = PinCheckScoreboardAppMenu( master=root, callbacks={}, initial_history=initial_history )    
    # app_menu = PinCheckScoreboardAppMenu( master=root, callbacks=app_callbacks, initial_history=initial_history )    
    root.config(menu=app_menu) # Attach the menu to the root window
    app_menu.bind_global_accelerators() # Call the binding method
    

    
    root.mainloop()