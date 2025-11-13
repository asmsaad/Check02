import tkinter as tk
from tkinter import ttk, Menu, messagebox, Listbox
from typing import Dict, Any, Optional, List, Union, Callable


class LinkDetailPopup(tk.Toplevel):
    """
    A minimal modal pop-up for showing detailed link information.
    Manages a single instance to prevent overlapping pop-ups.
    """

    _active_popup: Optional["LinkDetailPopup"] = None

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

        ttk.Label(
            self, text=title, font=("Segoe UI", 12, "bold"), padding=(10, 10)
        ).pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10)
        ttk.Label(
            self, text=content, font=("Segoe UI", 10), padding=(10, 10), justify=tk.LEFT
        ).pack(anchor="w")
        ttk.Button(self, text="Close", command=self.destroy).pack(pady=10)

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_window(self)


class CheckFilesPopup(tk.Toplevel):
    """
    A modal pop-up that displays a list of file paths in a Listbox.
    Prints the selected file path to the terminal on click.
    """

    _active_popup: Optional["CheckFilesPopup"] = None

    @classmethod
    def show_popup(
        cls, parent: tk.Tk | ttk.Frame, title: str, file_list: List[str]
    ) -> None:
        """Creates or shows a single instance of the file list popup."""
        if cls._active_popup and cls._active_popup.winfo_exists():
            cls._active_popup.destroy()

        new_popup = cls(parent, title, file_list)
        cls._active_popup = new_popup

    def __init__(
        self, parent: tk.Tk | ttk.Frame, title: str, file_list: List[str]
    ) -> None:
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.grab_set()

        # Center relative to parent
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        x = parent_x + (parent_width // 2) - 250
        y = parent_y + (parent_height // 2) - 150
        self.geometry(f"500x300+{x}+{y}")

        ttk.Label(
            self, text=title, font=("Segoe UI", 12, "bold"), padding=(10, 10)
        ).pack(anchor="w")
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10)

        # Frame for Listbox and Scrollbar
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(5, 0))

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.listbox = Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Segoe UI", 10),
            selectmode=tk.SINGLE,
            background="#FFFFFF",
            selectbackground="#0078D4",
            selectforeground="#FFFFFF",
            borderwidth=0,
            highlightthickness=0,
        )
        scrollbar.config(command=self.listbox.yview)

        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)

        # Populate the listbox
        if file_list:
            for item in file_list:
                self.listbox.insert(tk.END, item)
        else:
            self.listbox.insert(tk.END, "No files found.")
            self.listbox.config(state="disabled")

        # Bind the click event
        self.listbox.bind("<<ListboxSelect>>", self._on_item_select)

        ttk.Button(self, text="Close", command=self.destroy).pack(pady=10)

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_window(self)

    def _on_item_select(self, event: tk.Event) -> None:
        """Handles click events on the listbox."""
        try:
            selected_indices = self.listbox.curselection()
            if not selected_indices:
                return
            
            selected_path = self.listbox.get(selected_indices[0])
            print(f"Selected file: {selected_path}")
        except Exception as e:
            print(f"Error selecting item: {e}")


class WebLinkLabel(ttk.Label):
    """
    A ttk Label that looks and acts like a web link with hover effects.
    
    MODIFIED: Now accepts 'callback_data' to pass specific data
    to the callback, instead of just the label's text.
    """

    def __init__(
        self,
        master: tk.Widget,
        text: str,
        callback: Callable[[Any], None],
        callback_data: Any = None,  # <-- NEW: Data to pass to the callback
        **kwargs: Any,
    ) -> None:
        super().__init__(
            master, text=text, foreground="#0052CC", cursor="hand2", **kwargs
        )
        self.callback = callback
        self.callback_data = callback_data  # <-- NEW
        
        # Store original font to revert to
        self.original_font = kwargs.get("font", ("Segoe UI", 10, "normal"))
        if isinstance(self.original_font, str):
             # Simple parsing if font is a string; robust parsing is complex
             parts = self.original_font.split()
             name = parts[0]
             size = int(parts[1]) if len(parts) > 1 else 10
             style = parts[2] if len(parts) > 2 else "normal"
             self.original_font = (name, size, style)
        
        # Ensure 'normal' style is stored
        self.normal_font = (self.original_font[0], self.original_font[1], "normal")
        # Create underlined font
        self.underline_font = (self.original_font[0], self.original_font[1], "underline")

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _on_enter(self, event: tk.Event) -> None:
        self.config(font=self.underline_font)

    def _on_leave(self, event: tk.Event) -> None:
        self.config(font=self.normal_font)

    def _on_click(self, event: tk.Event) -> None:
        # <-- MODIFIED: Check if callback_data exists
        if self.callback_data is not None:
            self.callback(self.callback_data)
        else:
            self.callback(self.cget("text"))


class MacroMetaDataFrame(ttk.Frame):
    """Displays a 3-column, multi-row grid of macro run details."""

    def __init__(
        self, master: tk.Tk | ttk.Frame, data: Dict[str, Any], **kwargs: Any
    ) -> None:
        super().__init__(master, relief="flat", borderwidth=0, **kwargs)

        self.master_root = master.winfo_toplevel()
        self.data = data

        self._create_layout()

    def update_data(self, new_data: Dict[str, Any]) -> None:
        """
        NEW: Clears the frame and redraws all widgets with new data.
        """
        print("Updating frame with new data...")
        # Destroy all current child widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        # Set the new data
        self.data = new_data
        
        # Re-create the layout
        self._create_layout()

    def _link_callback(self, title: str, content: str) -> None:
        """Handles all link clicks by showing the modal popup."""
        LinkDetailPopup.show_popup(self.master_root, title, content)

    def _show_check_files_popup(self, title: str, file_list: List[str]) -> None:
        """
        NEW: Shows the modal popup with a list of files.
        """
        CheckFilesPopup.show_popup(self.master_root, title, file_list)

    def _get_data(
        self, key: str, default_value: Any = None
    ) -> Union[str, int, float, Dict, List]:
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
        meta_frame = ttk.Frame(self, style="MacroMetaDataFrame.TFrame")
        meta_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        meta_frame.columnconfigure((0, 2, 4), weight=0)
        meta_frame.columnconfigure((1, 3, 5), weight=1)

        # R1C1: Run By Link
        run_by = self._get_data("run_by", "Guest")
        ttk.Label(meta_frame, text="Run by:", style="MacroMetaDataFrame.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 5), pady=2
        )
        WebLinkLabel(
            meta_frame,
            text=run_by,
            callback=lambda t: self._link_callback("Run By User", f"User: {t}"),
            font=("Segoe UI", 10, "normal"),
            style="MacroMetaDataFrame.TLabel",
        ).grid(row=0, column=1, sticky="w", pady=2)

        # R2C1: Hostname
        hostname = self._get_data("host", "-")
        ttk.Label(meta_frame, text="Host:", style="MacroMetaDataFrame.TLabel").grid(
            row=1, column=0, sticky="w", padx=(0, 5), pady=2
        )
        ttk.Label(
            meta_frame,
            text=hostname,
            font=("Segoe UI", 10),
            style="MacroMetaDataFrame.TLabel",
        ).grid(row=1, column=1, sticky="w", pady=2)

        # R1C2: Tool Link
        tool_name = self._get_data("tool_name", "No Tool")
        ttk.Label(meta_frame, text="Tool:", style="MacroMetaDataFrame.TLabel").grid(
            row=0, column=2, sticky="w", padx=(0, 5), pady=2
        )
        WebLinkLabel(
            meta_frame,
            text=tool_name,
            callback=lambda t: self._link_callback("Tool Information", f"Tool: {t}"),
            font=("Segoe UI", 10, "normal"),
            style="MacroMetaDataFrame.TLabel",
        ).grid(row=0, column=3, sticky="w", pady=2)

        # R2C2: Version Link
        version = self._get_data("version", "-")
        ttk.Label(meta_frame, text="Version:", style="MacroMetaDataFrame.TLabel").grid(
            row=1, column=2, sticky="w", padx=(0, 5), pady=2
        )
        WebLinkLabel(
            meta_frame,
            text=version,
            callback=lambda t: self._link_callback("Version Info", f"Version: {t}"),
            font=("Segoe UI", 10, "normal"),
            style="MacroMetaDataFrame.TLabel",
        ).grid(row=1, column=3, sticky="w", pady=2)

        # R1C3: Start At
        start_at = self._get_data("start_time", "-(Utc)")
        ttk.Label(meta_frame, text="Start at:", style="MacroMetaDataFrame.TLabel").grid(
            row=0, column=4, sticky="w", padx=(0, 5), pady=2
        )
        ttk.Label(
            meta_frame,
            text=start_at,
            font=("Segoe UI", 10),
            style="MacroMetaDataFrame.TLabel",
        ).grid(row=0, column=5, sticky="w", pady=2)

        # R2C3: Duration
        duration = self._get_data("duration", "-")
        ttk.Label(meta_frame, text="Duration:", style="MacroMetaDataFrame.TLabel").grid(
            row=1, column=4, sticky="w", padx=(0, 5), pady=2
        )
        ttk.Label(
            meta_frame,
            text=duration,
            font=("Segoe UI", 10),
            style="MacroMetaDataFrame.TLabel",
        ).grid(row=1, column=5, sticky="w", pady=2)

    def _create_status_section(self) -> None:
        """
        Creates Column 2: Status Checks (White Background)
        
        MODIFIED: Now reads [is_valid, file_list] structure and
        links to the new CheckFilesPopup.
        """
        status_frame = ttk.Frame(
            self,
            style="MacroMetaDataFrame.InputFile.TFrame",
        )
        status_frame.grid(row=0, column=1, sticky="nsew", padx=15)
        status_frame.columnconfigure((0, 1), weight=1)

        checks = self._get_data("checks", {})
        # Using the longer list from your second (now removed) function
        check_names = ["Lef", "Libarty", "Verilog", "GDS", "hef"]

        for i, name in enumerate(check_names):
            # Fill row by row (standard grid layout)
            col = i // 2
            row = i % 2

            # MODIFIED: Default is [0, []]
            check_data = checks.get(name, [0, []])
            is_valid = check_data[0]
            file_list = check_data[1] if isinstance(check_data[1], list) else []
            count = len(file_list) # MODIFIED: Count is length of list

            mark = "✅" if is_valid else "❌"

            if count > 0:
                # Create a sub-frame to hold the composite label
                cell_frame = ttk.Frame(
                    status_frame, style="MacroMetaDataFrame.InputFile.TFrame"
                )
                cell_frame.grid(row=row, column=col, sticky="w", padx=5, pady=2)

                ttk.Label(
                    cell_frame,
                    text=f"{name}: {mark} (",
                    style="MacroMetaDataFrame.InputFile.TLabel",
                ).pack(side=tk.LEFT)

                # MODIFIED: Pass file_list as callback_data
                WebLinkLabel(
                    cell_frame,
                    text=str(count),
                    callback=lambda fl, n=name: self._show_check_files_popup(
                        f"{n} Files", fl
                    ),
                    callback_data=file_list, # <-- Pass the list
                    font=("Segoe UI", 10, "normal"),
                    style="MacroMetaDataFrame.InputFile.TLabel"
                ).pack(side=tk.LEFT)

                ttk.Label(
                    cell_frame, text=")", style="MacroMetaDataFrame.InputFile.TLabel"
                ).pack(side=tk.LEFT)
            else:
                # No count, just show status
                ttk.Label(
                    status_frame,
                    text=f"{name}: {mark}",
                    style="MacroMetaDataFrame.InputFile.TLabel",
                ).grid(row=row, column=col, sticky="w", padx=5, pady=2)

    def _create_link_section(self) -> None:
        """Creates Column 3: External Links"""
        link_frame = ttk.Frame(self, style="MacroMetaDataFrame.TFrame")
        link_frame.grid(row=0, column=2, sticky="nsew", padx=(15, 0))
        
        link_names = [
            "YAML Config",
            "Repo Link",
        ]
        links = self._get_data("links", {})

        for i, name in enumerate(link_names):
            key = name.lower().replace(" ", "_")
            url = links.get(key)

            if url and url != "-":
                WebLinkLabel(
                    link_frame,
                    text=name,
                    callback=lambda t, u=url: self._link_callback(
                        f"External Link: {t}", f"Simulated opening link for: {u}"
                    ),
                    font=("Segoe UI", 10, "normal"),
                    style="MacroMetaDataFrame.TLabel",
                ).pack(anchor="w", pady=2)
            else:
                ttk.Label(link_frame, text=f"{name}: -", foreground="#888888", style="MacroMetaDataFrame.TLabel").pack(
                    anchor="w", pady=2
                )


if __name__ == "__main__":

    # MODIFIED: sample_data uses the new 'checks' format
    sample_data = {
        "run_by": "jdoe",
        "host": "lab-server-12",
        "tool_name": "MyToolSuite 4.2",
        "version": "v1.2.345-gHjK",
        "start_time": "10:12:35 10 Oct 2025 (Utc)",
        "duration": "96.95s",
        "checks": {
            "Lef": [1, []],
            "Libarty": [0, ["/path/to/libs/lib1.db", "/path/to/libs/lib2.db"]],
            "Verilog": [
                1,
                ["/project/src/top.v", "/project/src/sub1.v", "/project/src/sub2.v"],
            ],
            "GDS": [0, []],
            "hef": [1, ["/data/run/final.hef"]]
        },
        "links": {
            "yaml_config": "s3://bucket/config.yaml",
            "repo_link": "https://git.corp/project/macro",
            "pin_info": None,
        },
    }

    # NEW: Data for the update_data method
    new_sample_data = {
        "run_by": "a.smith",
        "host": "prod-server-01",
        "tool_name": "MyToolSuite 5.0",
        "version": "v2.0.0-release",
        "start_time": "14:30:00 11 Nov 2025 (Utc)",
        "duration": "120.5s",
        "checks": {
            "Lef": [1, ["/new/path/lef.lef"]],
            "Libarty": [1, ["/new/path/libs/lib_prod.db"]],
            "Verilog": [1, ["/new/src/top_final.v"]],
            "GDS": [1, []],
            "hef": [0, ["/new/run/final.hef", "/new/run/extra.hef"]]
        },
        "links": {
            "yaml_config": "s3://prod-bucket/config_prod.yaml",
            "repo_link": None, # Test a missing link
        },
    }


    root = tk.Tk()
    root.title("Macro Details (Professional UI)")
    root.geometry("1000x300") # Made taller for the new button

    style = ttk.Style(root)
    style.theme_use("clam")

    # Define the styles used by the class
    # style.configure("MacroMetaDataFrame.TFrame", background="#d8d8d8")
    # style.configure("MacroMetaDataFrame.TLabel", background="#d8d8d8")
    # style.configure(
    #     "MacroMetaDataFrame.InputFile.TFrame", background="#ebebeb", borderwidth=0
    # )
    # style.configure("MacroMetaDataFrame.InputFile.TLabel", background="#ebebeb")
    
    
    style.configure("MacroMetaDataFrame.TFrame", background="#d8d8d8")
    style.configure("MacroMetaDataFrame.TLabel", background="#d8d8d8")
    style.configure( "MacroMetaDataFrame.InputFile.TFrame", background="#ebebeb", borderwidth=0)
    style.configure("MacroMetaDataFrame.InputFile.TLabel", background="#ebebeb")

    # --- Main Frame ---
    main_frame = ttk.Frame(root, padding=5, )
    main_frame.pack(fill="x", anchor="n")
    macro_details_frame = MacroMetaDataFrame(main_frame, data=sample_data)
    macro_details_frame.pack(fill="x", anchor="n")

    ttk.Label(
        main_frame,
        text="Click any blue underlined text or number to trigger a pop-up.",
        font=("Segoe UI", 9, "italic"),
    ).pack(pady=10)

    # NEW: Button to test the update_data method
    ttk.Button(
        main_frame,
        text="Update Data (Test)",
        command=lambda: macro_details_frame.update_data(new_sample_data)
    ).pack(pady=10)


    root.mainloop()