import tkinter as tk
from tkinter import ttk, Menu 
from typing import Dict, Any, Callable, Optional 

# --- CustomTooltip Class (Restored with Type Hinting) ---
class CustomTooltip:
    """A minimal, professional Tooltip implementation for modern Tkinter UIs."""
    def __init__(self, widget: tk.Widget, text: str, align_widget: tk.Widget) -> None:
        self.widget = widget
        self.text = text
        self.align_widget = align_widget
        self.tip_window: Optional[tk.Toplevel] = None

    def showtip(self, event=None) -> None:
        if self.tip_window or not self.text:
            return
        x = self.align_widget.winfo_rootx()
        y = self.align_widget.winfo_rooty() + self.align_widget.winfo_height() + 2 

        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(self.tip_window, text=self.text, justify=tk.LEFT,
                          background="#FFFFE0", 
                          foreground="#333333",
                          relief=tk.SOLID, borderwidth=1,
                          font=("Segoe UI", 9))
        label.pack(ipadx=4, ipady=4)

    def hidetip(self, event=None) -> None:
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None

# --- Main Frame Widget (Fixed and Complete) ---
class MacroNameFrame(ttk.Frame):
    
    def __init__(self, 
                 master: tk.Tk | ttk.Frame, 
                 macro_name: str, 
                 macro_path: str, 
                 **kwargs: Any) -> None:
        
        # 🔑 FIX: Explicitly remove borders from the main frame
        super().__init__(master,  relief='flat', borderwidth=0, **kwargs)
        
        self.macro_name: str = macro_name
        self.macro_path: str = macro_path
        self.copy_button: Optional[ttk.Button] = None
        self._hide_id: Optional[str] = None
        
        self.columnconfigure(0, weight=0) 
        self.columnconfigure(1, weight=1) 
        self.columnconfigure(2, weight=0)
        
        self._create_widgets()
        
    def _create_widgets(self) -> None:
        style = ttk.Style(self.master)
        style.configure("Copy.TButton", font=("Segoe UI", 9), foreground="#111111", padding=(0,0,0,0))
        
        # Static Label
        self.name_label = ttk.Label(self, text="Macro:", font=("Segoe UI", 10, "bold"), foreground="#4A4A4A")
        self.name_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Nested frame (also flat/borderless)
        self.macro_name_frame: ttk.Frame = ttk.Frame(self, relief='flat', borderwidth=0)
        self.macro_name_frame.pack(side=tk.LEFT)
        
        # Macro Name Display
        self.macro_display: ttk.Label = ttk.Label(self.macro_name_frame, text=self.macro_name, 
                                       font=("Segoe UI", 10), foreground="#007ACC")
        self.macro_display.pack(side=tk.LEFT, padx=(0, 0))
        
        # Copy button (initially hidden)
        self.copy_button = ttk.Button(self.macro_name_frame, text="⧉", command=self._copy_name, 
                                      width=1, style="Copy.TButton")
        
        # Tooltip Setup
        self.tooltip: CustomTooltip = CustomTooltip(
            self.master, 
            text=f"Full Location: {self.macro_path}", 
            align_widget=self.macro_display
        )
        
        # Bind Events
        self.macro_name_frame.bind("<Enter>", self._on_enter)
        self.macro_name_frame.bind("<Leave>", self._on_leave)
        self.macro_display.bind("<Enter>", self._on_enter)
        self.macro_display.bind("<Leave>", self._on_leave)
        
    def _on_enter(self, event: tk.Event) -> None:
        if self._hide_id:
             self.master.after_cancel(self._hide_id)
        self.tooltip.showtip()
        self._show_copy_button()

    def _on_leave(self, event: tk.Event) -> None:
        self._hide_copy_button_after_delay()
        self.tooltip.hidetip()
        
    def _show_copy_button(self) -> None:
        if self.copy_button and self.copy_button.winfo_ismapped() == 0:
            self.copy_button.pack(side=tk.LEFT, ipadx=4) 
            self.copy_button.bind("<Enter>", self._on_button_enter)
            self.copy_button.bind("<Leave>", self._on_button_leave)
            
    def _on_button_enter(self, event: tk.Event) -> None:
        if self._hide_id:
            self.master.after_cancel(self._hide_id)

    def _on_button_leave(self, event: tk.Event) -> None:
        self._hide_copy_button_after_delay()

    def _hide_copy_button_after_delay(self, event: Optional[tk.Event] = None) -> None:
        self._hide_id = self.master.after(50, self._remove_copy_button)
        
    def _remove_copy_button(self) -> None:
        if self.copy_button and self.copy_button.winfo_ismapped():
            self.copy_button.pack_forget()

    def _copy_name(self) -> None:
        """Copies the macro name (the text) and shows the tick mark."""
        self.clipboard_clear()
        self.clipboard_append(self.macro_name)
        self.update() 
        print(f"Copied to clipboard: {self.macro_name}")
        
        # 🟢 RESTORED: Visual feedback (tick mark)
        if self.copy_button and self.copy_button.winfo_ismapped():
            original_text = self.copy_button.cget("text")
            self.copy_button.config(text="✓", state=tk.DISABLED) # Show tick mark
            # Schedule a function to revert the button state after 800ms
            self.master.after(800, 
                              lambda: self.copy_button and self.copy_button.config(text=original_text, state=tk.NORMAL))


# --- Main Application Setup ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Dynamic UI Example (Functional)")
    root.geometry("480x150")

    macro_full_path = "/Users/Developer/Projects/Automation/dc_asdfk__asjdfkk.py"
    macro_display_name = "dc_asdfk__asjdfkk"
    
    macro_frame = MacroNameFrame(
        root,
        macro_name=macro_display_name,
        macro_path=macro_full_path
    )
    macro_frame.pack(pady=20, padx=20, fill='x')

    ttk.Label(root, text="Click the button for the copy action and visual feedback.", 
              font=("Segoe UI", 9, "italic")).pack(pady=10)

    root.mainloop()




import tkinter as tk
from tkinter import ttk, Menu, messagebox
from typing import Dict, Any, Optional, List, Union, Callable

# --- 1. Pop-up Dialog Class (Handles Link Clicks) ---

class LinkDetailPopup(tk.Toplevel):
    """
    A minimal modal pop-up for showing detailed link information.
    Manages a single instance to prevent overlapping pop-ups.
    """
    
    _active_popup: Optional['LinkDetailPopup'] = None

    @classmethod
    def show_popup(cls, parent: tk.Tk | ttk.Frame, title: str, content: str) -> None:
        """Creates or shows a single instance of the popup, destroying the previous one."""
        if cls._active_popup and cls._active_popup.winfo_exists():
            cls._active_popup.destroy()
            
        new_popup = cls(parent, title, content)
        cls._active_popup = new_popup

    def __init__(self, parent: tk.Tk | ttk.Frame, title: str, content: str) -> None:
        super().__init__(parent)
        self.transient(parent)
        self.title(f"Details: {title}")
        self.grab_set()
        
        # Calculate center position relative to the main window
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        x = parent_x + (parent_width // 2) - 200
        y = parent_y + (parent_height // 2) - 100
        self.geometry(f"400x200+{x}+{y}")

        ttk.Label(self, text=title, font=('Segoe UI', 12, 'bold'), padding=(10, 10)).pack(anchor='w')
        ttk.Separator(self, orient='horizontal').pack(fill='x', padx=10)
        ttk.Label(self, text=content, font=('Segoe UI', 10), padding=(10, 10), justify=tk.LEFT).pack(anchor='w')
        ttk.Button(self, text="Close", command=self.destroy).pack(pady=10)
        
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_window(self)

# --- 2. Link Helper Class (Creates underlined labels) ---

class WebLinkLabel(ttk.Label):
    """A ttk Label that looks and acts like a web link with hover effects."""
    def __init__(self, master: tk.Widget, text: str, callback: Callable[[Any], None], **kwargs: Any) -> None:
        super().__init__(master, text=text, foreground='#0052CC', cursor="hand2", **kwargs)
        self.callback = callback
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _on_enter(self, event: tk.Event) -> None:
        self.config(font=('Segoe UI', 10, 'underline'))

    def _on_leave(self, event: tk.Event) -> None:
        self.config(font=('Segoe UI', 10, 'normal'))
        
    def _on_click(self, event: tk.Event) -> None:
        self.callback(self.cget('text'))

# --- 3. Macro Details Frame (Main Application) ---

class MacroMetaDataFrame(ttk.Frame):
    """Displays a 3-column, multi-row grid of macro run details."""
    
    def __init__(self, master: tk.Tk | ttk.Frame, data: Dict[str, Any], **kwargs: Any) -> None:
        super().__init__(master,  relief='flat', borderwidth=0, **kwargs)
        
        self.master_root = master.winfo_toplevel()
        self.data = data
        self._setup_style()
        self._create_layout()

    def _setup_style(self) -> None:
        """Sets up custom styles for a clean, borderless appearance."""
        style = ttk.Style(self.master_root)
        style.configure('White.TFrame', background='white', borderwidth=0)
        style.configure('White.TLabel', background='white')

    def _link_callback(self, title: str, content: str) -> None:
        """Handles all link clicks by showing the modal popup."""
        LinkDetailPopup.show_popup(self.master_root, title, content)

    def _get_data(self, key: str, default_value: Any = None) -> Union[str, int, float, Dict, List]:
        """Utility to safely retrieve data or return a placeholder."""
        if self.data is None or self.data.get(key) is None:
            return "-" if default_value is None else default_value
        return self.data[key]

    def _create_layout(self) -> None:
        """Creates the three main columns using grid."""
        self.columnconfigure(0, weight=3) 
        self.columnconfigure(1, weight=1) 
        self.columnconfigure(2, weight=1) 
        
        self._create_metadata_section()
        self._create_status_section()
        self._create_link_section()

    def _create_metadata_section(self) -> None:
        """Creates Column 1: Metadata (Nested 3x2 Grid)"""
        meta_frame = ttk.Frame(self,)
        meta_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 15))
        meta_frame.columnconfigure((0, 2, 4), weight=0) # Static labels
        meta_frame.columnconfigure((1, 3, 5), weight=1) # Dynamic data
        
        # 🔑 FIX: The following line was removed to stop rows from expanding
        # meta_frame.rowconfigure((0, 1), weight=1) 
        
        # R1C1: Run By Link
        run_by = self._get_data('run_by', 'Guest')
        ttk.Label(meta_frame, text="Run by:").grid(row=0, column=0, sticky='w', padx=(0, 5), pady=2) # Added small pady
        WebLinkLabel(meta_frame, text=run_by, 
                     callback=lambda t: self._link_callback("Run By User", f"User: {t}"),
                     font=('Segoe UI', 10, 'normal')).grid(row=0, column=1, sticky='w', pady=2)
        
        # R2C1: Hostname
        hostname = self._get_data('host', '-')
        ttk.Label(meta_frame, text="Host:").grid(row=1, column=0, sticky='w', padx=(0, 5), pady=2)
        ttk.Label(meta_frame, text=hostname, font=('Segoe UI', 10)).grid(row=1, column=1, sticky='w', pady=2)

        # R1C2: Tool Link
        tool_name = self._get_data('tool_name', 'No Tool')
        ttk.Label(meta_frame, text="Tool:").grid(row=0, column=2, sticky='w', padx=(0, 5), pady=2)
        WebLinkLabel(meta_frame, text=tool_name, 
                     callback=lambda t: self._link_callback("Tool Information", f"Tool: {t}"),
                     font=('Segoe UI', 10, 'normal')).grid(row=0, column=3, sticky='w', pady=2)

        # R2C2: Version Link
        version = self._get_data('version', '-')
        ttk.Label(meta_frame, text="Version:").grid(row=1, column=2, sticky='w', padx=(0, 5), pady=2)
        WebLinkLabel(meta_frame, text=version, 
                     callback=lambda t: self._link_callback("Version Info", f"Version: {t}"),
                     font=('Segoe UI', 10, 'normal')).grid(row=1, column=3, sticky='w', pady=2)

        # R1C3: Start At
        start_at = self._get_data('start_time', '-(Utc)')
        ttk.Label(meta_frame, text="Start at:").grid(row=0, column=4, sticky='w', padx=(0, 5), pady=2)
        ttk.Label(meta_frame, text=start_at, font=('Segoe UI', 10)).grid(row=0, column=5, sticky='w', pady=2)

        # R2C3: Duration
        duration = self._get_data('duration', '-')
        ttk.Label(meta_frame, text="Duration:").grid(row=1, column=4, sticky='w', padx=(0, 5), pady=2)
        ttk.Label(meta_frame, text=duration, font=('Segoe UI', 10)).grid(row=1, column=5, sticky='w', pady=2)

    def _create_status_section(self) -> None:
        """Creates Column 2: Status Checks (White Background)"""
        status_frame = ttk.Frame(self, style='White.TFrame',)
        status_frame.grid(row=0, column=1, sticky='nsew', padx=15)
        status_frame.columnconfigure((0, 1), weight=1)
        
        # 🔑 FIX: The following line was removed to stop rows from expanding
        # status_frame.rowconfigure((0, 1), weight=1)
        
        checks = self._get_data('checks', {})
        check_names = ["Lef", "Libarty", "Verilog", "GDS"]
        
        for i, name in enumerate(check_names):
            row = i // 2
            col = i % 2
            
            check_data = checks.get(name, [0, 0])
            count = check_data[1]
            is_valid = check_data[0]
            
            mark = "✔️" if is_valid else "❌" # Using Unicode characters
            
            if count > 0:
                cell_frame = ttk.Frame(status_frame, style='White.TFrame')
                cell_frame.grid(row=row, column=col, sticky='w', padx=5, pady=2)
                
                ttk.Label(cell_frame, text=f"{name}: {mark} (", style='White.TLabel').pack(side=tk.LEFT)
                
                WebLinkLabel(cell_frame, text=str(count), 
                             callback=lambda t, n=name: self._link_callback(f"{n} Issues", f"Found {t} issues for {n}."),
                             font=('Segoe UI', 10, 'normal')).pack(side=tk.LEFT)
                
                ttk.Label(cell_frame, text=")", style='White.TLabel').pack(side=tk.LEFT)
            else:
                ttk.Label(status_frame, text=f"{name}: {mark}", style='White.TLabel').grid(row=row, column=col, sticky='w', padx=5, pady=2)

    def _create_link_section(self) -> None:
        """Creates Column 3: External Links"""
        link_frame = ttk.Frame(self, )
        link_frame.grid(row=0, column=2, sticky='nsew', padx=(15, 0))
        link_names = ["YAML Config", "Repo Link", "Pin Info"]
        links = self._get_data('links', {})
        
        for i, name in enumerate(link_names):
            key = name.lower().replace(" ", "_")
            url = links.get(key)
            
            if url and url != "-":
                WebLinkLabel(link_frame, text=name, 
                             callback=lambda t, u=url: self._link_callback(f"External Link: {t}", f"Simulated opening link for: {u}"),
                             font=('Segoe UI', 10, 'normal')).pack(anchor='w', pady=2)
            else:
                ttk.Label(link_frame, text=f"{name}: -", foreground='#888888').pack(anchor='w', pady=2)

    def _create_status_section(self) -> None:
        """Creates Column 2: Status Checks (White Background)"""
        status_frame = ttk.Frame(self, style='White.TFrame', )
        status_frame.grid(row=0, column=1, sticky='nsew', padx=15)
        status_frame.columnconfigure((0, 1), weight=1)
        #! status_frame.rowconfigure((0, 1), weight=1)
        
        checks = self._get_data('checks', {})
        check_names = ["Lef", "Libarty", "Verilog", "GDS"]
        
        for i, name in enumerate(check_names):
            row = i // 2
            col = i % 2
            
            check_data = checks.get(name, [0, 0])
            count = check_data[1]
            is_valid = check_data[0]
            
            mark = "✅" if is_valid else "❌" # Using Unicode characters
            
            if count > 0:
                cell_frame = ttk.Frame(status_frame, style='White.TFrame')
                cell_frame.grid(row=row, column=col, sticky='w', padx=5, pady=2)
                
                ttk.Label(cell_frame, text=f"{name}: {mark} (", style='White.TLabel').pack(side=tk.LEFT)
                
                WebLinkLabel(cell_frame, text=str(count), 
                             callback=lambda t, n=name: self._link_callback(f"{n} Issues", f"Found {t} issues for {n}."),
                             font=('Segoe UI', 10, 'normal')).pack(side=tk.LEFT)
                
                ttk.Label(cell_frame, text=")", style='White.TLabel').pack(side=tk.LEFT)
            else:
                ttk.Label(status_frame, text=f"{name}: {mark}", style='White.TLabel').grid(row=row, column=col, sticky='w', padx=5, pady=2)

    # def _create_link_section(self) -> None:
    #     """Creates Column 3: External Links"""
    #     link_frame = ttk.Frame(self, padding="10")
    #     link_frame.grid(row=0, column=2, sticky='nsew', padx=(15, 0))
    #     link_names = ["YAML Config", "Repo Link", "Pin Info"]
    #     links = self._get_data('links', {})
        
    #     for i, name in enumerate(link_names):
    #         key = name.lower().replace(" ", "_")
    #         url = links.get(key)
            
    #         if url and url != "-":
    #             WebLinkLabel(link_frame, text=name, 
    #                          callback=lambda t, u=url: self._link_callback(f"External Link: {t}", f"Simulated opening link for: {u}"),
    #                          font=('Segoe UI', 10, 'normal')).pack(anchor='w', pady=2)
    #         else:
    #             ttk.Label(link_frame, text=f"{name}: -", foreground='#888888').pack(anchor='w', pady=2)

# --- 4. Main Application Setup ---

if __name__ == "__main__":
    
    # Data Definition (Only contains keys needed by MacroMetaDataFrame)
    sample_data = {
        'run_by': 'jdoe',
        'host': 'lab-server-12',
        'tool_name': 'MyToolSuite 4.2',
        'version': 'v1.2.345-gHjK',
        'start_time': '10:12:35 10 Oct 2025 (Utc)',
        'duration': '96.95s',
        'checks': {
            'Lef': [1, 0],      
            'Libarty': [0, 15], 
            'Verilog': [1, 100],
            'GDS': [0, 0]       
        },
        'links': {
            'yaml_config': 's3://bucket/config.yaml',
            'repo_link': 'https://git.corp/project/macro',
            'pin_info': None
        }
    }

    root = tk.Tk()
    root.title("Macro Details (Professional UI)")
    root.geometry("1000x250") # Adjusted geometry
    
    # Call MacroMetaDataFrame, which is the only main component
    macro_details_frame = MacroMetaDataFrame(root, data=sample_data)
    macro_details_frame.pack(pady=10, padx=20, fill='x', anchor='n')
    
    ttk.Label(root, text="Click any blue underlined text or number to trigger the modal pop-up.", 
              font=("Segoe UI", 9, "italic")).pack(pady=10)

    root.mainloop()

