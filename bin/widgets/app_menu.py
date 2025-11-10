import tkinter as tk
from tkinter import Menu, filedialog, messagebox, ttk
from typing import Dict, Any, Callable, Optional, List
import json
import os

# --- ⚙️ Professional Preferences Dialog (Kept for integration) ---

class PreferencesDialog(tk.Toplevel):
    """
    A minimal version of the modal Preferences dialog.
    """
    def __init__(self, parent_widget: ttk.Widget, data_dict: Dict[str, Any],
                 on_change_callback: Callable[[Dict[str, Any]], None]) -> None:
        super().__init__(parent_widget)
        self.transient(parent_widget)
        self.grab_set()
        self.title("Application Preferences")
        self.initial_data = data_dict.copy()
        self.on_change_callback = on_change_callback
        self.vars: Dict[str, tk.Variable] = {'api_timeout': tk.IntVar(value=data_dict.get('api_timeout', 30))}
        
        # Simple UI for demonstration
        ttk.Label(self, text="API Timeout (s):").pack(padx=10, pady=5)
        ttk.Entry(self, textvariable=self.vars['api_timeout']).pack(padx=10, pady=5)
        ttk.Button(self, text="OK", command=self.on_ok).pack(pady=10)
        self.wait_window(self)

    def on_ok(self) -> None:
        new_settings = {'api_timeout': self.vars['api_timeout'].get()}
        if new_settings != self.initial_data:
            self.on_change_callback(new_settings)
        self.destroy()

# --- 🚀 Main Application Class, accepting the root ---

class AppMenu:
    """
    The main application logic and UI manager, which accepts a tk.Tk root instance.
    """
    def __init__(self, master: tk.Tk):
        """
        Initializes the application, setting up state and the UI on the provided master.
        
        Args:
            master: The root tk.Tk window instance.
        """
        self.master = master


        # --- 🛠️ Application State Variables ---
        self.max_recent_files = 5
        self.recent_files: List[str] = [
            "/home/user/data/config1.yaml", "/home/user/data/project2.json", 
            "/mnt/share/logs/log_b.txt", "/var/tmp/temp_c.dat", 
            "/home/user/data/report_d.csv"
        ]
        
        # Application Settings (managed via dialog)
        self.app_settings: Dict[str, Any] = {"api_timeout": 30}
        
        # Tkinter variables for toggled menu items
        self.show_details_panel_var = tk.BooleanVar(value=True)
        self.api_collected_var = tk.BooleanVar(value=False)
        self.current_theme = tk.StringVar(value="Light")
        
        # Set up UI components
        self.create_menu_bar()
        self.bind_accelerators()
        
    def create_menu_bar(self):
        """Creates the main menu bar and all sub-menus on the master window."""
        menubar = Menu(self.master)
        self.master.config(menu=menubar) # Attaches the menu to the external root

        # --- File Menu ---
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        self._create_file_menu(file_menu)

        # --- Edit Menu ---
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Preferences", command=self.show_preferences)

        # --- View Menu ---
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        self._create_view_menu(view_menu)

        # --- Connection Menu ---
        connection_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Connection", menu=connection_menu)
        self._create_connection_menu(connection_menu)

        # --- Run Menu ---
        run_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Run", menu=run_menu)
        self._create_run_menu(run_menu)

        # --- Window Menu ---
        window_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Window", menu=window_menu)
        self._create_window_menu(window_menu)
        
        # --- Help Menu ---
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        self._create_help_menu(help_menu)

    # --- Menu Creation Helpers (Only showing one for brevity) ---
    
    def _create_file_menu(self, menu):
        menu.add_command(label="Load YAML...", command=self.load_yaml_file)
        menu.add_command(label="Save", command=self.save_file)
        menu.add_command(label="Save As...", command=self.save_file_as)
        menu.add_separator()
        self.history_menu = Menu(menu, tearoff=0)
        menu.add_cascade(label="History", menu=self.history_menu)
        self._update_history_menu()
        menu.add_separator()
        menu.add_command(label="Export...", command=self.export_data)

    def _create_view_menu(self, menu):
        menu.add_checkbutton(label="Show Details Panel", command=self.toggle_details_panel,
                             variable=self.show_details_panel_var)
        menu.add_separator()
        menu.add_command(label="Heatmap View", command=self.view_heatmap)
        menu.add_command(label="Tabular View", command=self.view_tabular)

    def _create_connection_menu(self, menu):
        menu.add_checkbutton(label="API Collected", command=self.toggle_api_collected,
                             variable=self.api_collected_var)
        menu.add_command(label="API Connection", command=self.connect_api)

    def _create_run_menu(self, menu):
        menu.add_command(label="Run", accelerator="F5", command=self.run_app)
        menu.add_command(label="Run with Edit", accelerator="Shift+F5", command=self.run_with_edit)

    def _create_window_menu(self, menu):
        menu.add_command(label="Window Settings", command=self.window_settings)
        theme_menu = Menu(menu, tearoff=0)
        menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_radiobutton(label="Light", variable=self.current_theme, value="Light", command=self.change_theme)
        theme_menu.add_radiobutton(label="Dark", variable=self.current_theme, value="Dark", command=self.change_theme)

    def _create_help_menu(self, menu):
        menu.add_command(label="Manual", command=self.show_manual)
        menu.add_separator()
        menu.add_command(label="System Info", command=self.show_system_info)
        menu.add_command(label="What's New", command=self.show_whats_new)
        menu.add_command(label="About", command=self.show_about)
    
    # --- Action Handlers ---
    
    def show_preferences(self):
        """Opens the modal PreferencesDialog, passing the root as the parent."""
        print("Edit -> Preferences: Opening settings dialog...")
        # Since the master is a tk.Tk, we can pass it directly as the parent widget.
        PreferencesDialog(
            parent_widget=self.master,
            data_dict=self.app_settings,
            on_change_callback=self.update_settings_callback
        )

    def update_settings_callback(self, new_settings: Dict[str, Any]) -> None:
        """Callback to update settings."""
        print(f"✅ Settings updated via callback: {new_settings}")
        self.app_settings.update(new_settings)
        
    def load_yaml_file(self):
        file_path = filedialog.askopenfilename(defaultextension=".yaml", filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
        if file_path:
            print(f"File -> Load YAML: Selected path: {file_path}")
            self._add_to_history(file_path)

    def _add_to_history(self, file_path):
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:self.max_recent_files]
        self._update_history_menu()
            
    def _update_history_menu(self):
        # Implementation for updating history menu
        pass
        
    # --- Placeholder Methods (showing toggles and commands) ---
    def bind_accelerators(self): self.master.bind('<F5>', lambda e: self.run_app())
    def save_file(self): print("File -> Save: Saving...")
    def save_file_as(self): print("File -> Save As: Opening save dialog...")
    def export_data(self): print("File -> Export: Exporting...")
    def toggle_details_panel(self): print(f"View -> Show Details Panel: {self.show_details_panel_var.get()}")
    def view_heatmap(self): print("View -> Heatmap View: Switching...")
    def view_tabular(self): print("View -> Tabular View: Switching...")
    def toggle_api_collected(self): print(f"Connection -> API Collected: {self.api_collected_var.get()}")
    def connect_api(self): print("Connection -> API Connection: Attempting...")
    def run_app(self): print("Run -> Run (F5): Starting process...")
    def run_with_edit(self): print("Run -> Run with Edit (Shift+F5): Starting debug process...")
    def window_settings(self): print("Window -> Window Settings: Opening dialog...")
    def change_theme(self): print(f"Window -> Theme: Changing theme to {self.current_theme.get()}")
    def show_manual(self): print("Help -> Manual: Opening documentation...")
    def show_system_info(self): print("Help -> System Info: Showing details...")
    def show_whats_new(self): print("Help -> What's New: Showing release notes.")
    def show_about(self): print("Help -> About: Showing application credits.")


if __name__ == "__main__":
    # --- Execute root=Tk() in the main block ---
    root = tk.Tk()
    
    # Pass the root to the application manager
    app = AppMenu(root)
    
    root.title("Data Analysis Suite (Tkinter)")
    root.geometry("800x600")
        
    # Start the event loop on the root
    root.mainloop()