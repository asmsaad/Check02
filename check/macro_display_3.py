"""
A professional, multi-threaded Task Runner GUI application built with Tkinter.

This module provides a reusable TaskManager widget that displays a list of tasks,
supports advanced filtering (case-sensitive, whole word, regex), sorting,
and runs tasks in separate threads to keep the UI responsive.

This code is presented with documentation and type hints as requested,
without any modification to the original logic or structure.
"""

import tkinter as tk
from tkinter import ttk
import random
import time
import threading
import re
# Import types for annotation
from typing import List, Dict, Any, Optional

# 50 sample workout tasks for testing
WORKOUT_TASKS: List[str] = [
    "Push-ups",
    "Squats", "Plank", "Jumping Jacks", "Lunges", "Burpees", "Crunches",
    "Leg Raises", "Mountain Climbers", "High Knees", "Deadlifts", "Bench Press",
    "Overhead Press", "Barbell Rows", "Pull-ups", "Dips", "Bicep Curls",
    "Tricep Extensions", "Kettlebell Swings", "Box Jumps", "Wall Sits", "Russian Twists",
    "Flutter Kicks", "Glute Bridges", "Calf Raises", "Farmers Walk", "Battle Ropes",
    "Sled Push", "Tire Flip", "Man Makers", "Thrusters", "Clean and Jerk", "Snatch",
    "Handstand Push-ups", "Muscle-ups", "Pistol Squats", "Rope Climbs",
    "Double Unders", "Box Dips", "Inverted Rows", "Hanging Leg Raises",
    "Back Extensions", "Good Mornings", "Face Pulls", "Lateral Raises",
    "Front Raises", "Shrugs", "Side Planks", "Bird-dog", "Star Jumps"
]


# Define a constant for the row selection color
SELECTED_ROW_COLOR: str = "#e6e6e6"


class Tooltip:
    """
    A simple tooltip class for Tkinter widgets.
    
    Creates a small popup window when the mouse hovers over the widget.
    """

    def __init__(self, widget: tk.Misc, text: str) -> None:
        """
        Initialize the Tooltip.

        Args:
            widget: The Tkinter widget to bind the tooltip to.
            text: The text to display in the tooltip.
        """
        self.widget = widget
        self.text = text
        self.tooltip_window: Optional[tk.Toplevel] = None
        self.id: Optional[str] = None  # To store the 'after' job ID
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event: Optional[tk.Event] = None) -> None:
        """Callback for when the mouse enters the widget."""
        self.schedule()

    def leave(self, event: Optional[tk.Event] = None) -> None:
        """Callback for when the mouse leaves the widget."""
        self.unschedule()
        self.hidetip()

    def schedule(self) -> None:
        """Schedules the tooltip to appear after a delay."""
        self.unschedule()
        self.id = self.widget.after(500, self.showtip)  # 500ms delay

    def unschedule(self) -> None:
        """Cancels a pending scheduled tooltip."""
        id = getattr(self, 'id', None)
        if id:
            self.widget.after_cancel(id)

    def showtip(self) -> None:
        """Creates and displays the actual tooltip window."""
        if self.tooltip_window:
            return
        # Get widget position and calculate tooltip position
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        # Create a Toplevel window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # No window decorations
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Add the label with text
        label = tk.Label(self.tooltip_window, text=self.text,
                         background="#ffffe0", relief="solid",
                         borderwidth=1, font=("tahoma", "8", "normal"))
        label.pack()

    def hidetip(self) -> None:
        """Destroys the tooltip window."""
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()


class TaskManager(ttk.Frame):
    """
    A comprehensive task management widget.

    This widget provides a scrollable list of tasks with features like
    sorting, filtering (text, case, whole word, regex), and asynchronous
    task execution with visual feedback.
    """

    def __init__(self, master: tk.Misc) -> None:
        """
        Initializes the TaskManager frame.

        Args:
            master: The parent widget.
        """
        super().__init__(master, padding="10")
        self.master = master

        # --- State Variables ---
        self.master_task_list: List[str] = sorted(WORKOUT_TASKS)  # The full, unfiltered list
        self.task_widgets: List[Dict[str, Any]] = []  # Holds dicts of widgets for each task
        self.sort_order: str = "asc"  # Current sort order
        self.filter_cs: tk.BooleanVar = tk.BooleanVar(value=False)  # Case-Sensitive
        self.filter_regex: tk.BooleanVar = tk.BooleanVar(value=False)  # Regex
        self.filter_mhw: tk.BooleanVar = tk.BooleanVar(value=False)  # Match Whole Word
        self.selected_row_data: Optional[Dict[str, Any]] = None  # Holds the task_data dict of the selected row
        self.run_animation_job: Dict[Any, str] = {}  # To manage "Running..." animations
        self.canvas_window: Optional[int] = None  # ID for the canvas window item
        self.visible_tasks: List[Dict[str, Any]] = []  # To store the currently visible/filtered tasks
        self._updating_layout: bool = False  # Add this flag

        self._setup_styles()

        # --- Main Layout ---
        self.grid_rowconfigure(2, weight=1)  # Make row 2 (task list) expandable
        self.grid_columnconfigure(0, weight=1)  # Make col 0 (main col) expandable

        self._create_header_controls()
        self._create_status_bar()
        self._create_task_list_area()

        self._populate_tasks()  # Create all task widgets
        self._update_task_list()  # Filter and display them

    def _setup_styles(self) -> None:
        """Initializes all ttk styles used by the widget."""
        self.style = ttk.Style()

        # Get host window background color
        try:
            default_bg = self.master.cget('background')
        except tk.TclError:
            default_bg = "#f0f0f0"  # A sensible fallback

        self.header_bg_active = "#f0f0f0"  # A sensible fallback

        # Style for toggle buttons (active/inactive)
        self.style.configure("Toggle.TButton", padding=5, font=('tahoma', 8))
        self.style.configure("Sort.TButton", padding=5, font=('tahoma', 8))
        self.style.configure("RunAll.TButton", padding=5, font=('tahoma', 8))
        self.style.configure("Run.TButton", padding=5, font=('tahoma', 8))  
        self.style.configure("Filter.TEntry", padding=5, font=('tahoma', 8))

        self.style.map("Toggle.TButton",
                       foreground=[('!active', 'disabled', 'gray'), ('active', 'black'), ('disabled', 'gray')],
                       background=[('active', self.header_bg_active), ('!active', self.header_bg_active)])
            
        # --- FIXED: Create unique styles without the 'style' parameter conflict ---
        
        # Create new styles by copying configuration from Toggle.TButton
        base_config = self.style.configure("Toggle.TButton")

        # Apply the same configuration to our new styles without the problematic parameter
        self.style.configure("CS.Toggle.TButton", **base_config)
        self.style.configure("MHW.Toggle.TButton", **base_config)
        self.style.configure("Regex.Toggle.TButton", **base_config)
        self.style.configure("RunAll.TButton", **base_config)
        self.style.configure("Sort.TButton", **base_config)
        self.style.configure("Row.TWidgets", **base_config)

        # Copy the style mapping as well
        toggle_map = self.style.map("Toggle.TButton")
        self.style.map("CS.Toggle.TButton", **toggle_map)
        self.style.map("MHW.Toggle.TButton", **toggle_map)
        self.style.map("Regex.Toggle.TButton", **toggle_map)
        self.style.map("RunAll.TButton", **toggle_map)
        self.style.map("Sort.TButton", **toggle_map)
        self.style.map("Row.TWidgets", **toggle_map)

        # Style for selected row
        self.style.configure("Selected.TFrame", background=SELECTED_ROW_COLOR)
        self.style.configure("Normal.TFrame", background='white')

        # Style for separators in rows
        self.style.configure("Row.TSeparator", background="#d0d0d0")
        self.style.configure("Selected.TSeparator", background=SELECTED_ROW_COLOR)  # Hide in selection

        # Style for the Text widget to look like a readonly Entry
        self.style.configure("Task.TText", relief="flat", padding=2,
                             background=default_bg,
                             font=('segoe ui', 10))

        # Separator for Col 1
        self.style.configure("Col1.TSeparator", background="#d0d0d0")
        self.style.configure("Header.TFrame", background=self.header_bg_active)
        self.style.configure("Status.TFrame", background="#ffffff")
        self.style.configure("Status.TLabel", background="#ffffff", foreground="#d1cece")

    def _create_header_controls(self) -> None:
        """Creates the top header frame with sort, filter, and run-all buttons."""
        self.header_frame = ttk.Frame(self, style="Header.TFrame", padding=(2, 2))
        self.header_frame.grid(row=0, column=0, sticky="ew")

        # Configure grid columns for alignment
        self.header_frame.grid_columnconfigure(0, weight=1, minsize=100)  # Col 1: Sort
        self.header_frame.grid_columnconfigure(1, weight=4)  # Col 2: Filter
        self.header_frame.grid_columnconfigure(2, weight=1, minsize=100)  # Col 3: Run All

        # --- Column 1: Sort ---
        col1_frame = ttk.Frame(self.header_frame, style="Header.TFrame")
        col1_frame.pack(side="left", anchor='w')
        self.sort_button = ttk.Button(col1_frame, text="AZ↓", style="Sort.TButton", width=3, command=self._on_sort_toggle)
        self.sort_button.pack(side='left', anchor='w')
        Tooltip(self.sort_button, "Toggle sort order (Ascending/Descending)")

        col1_sep = ttk.Separator(col1_frame, orient="vertical", style="Row.TSeparator")
        col1_sep.pack(side='left', fill='y', padx=(10, 10))

        # --- Column 2: Filter ---
        col2_frame = ttk.Frame(self.header_frame, style="Header.TFrame")
        col2_frame.pack(side="left", expand=True, fill="x", anchor='w')
        col2_frame.grid_columnconfigure(0, weight=1)

        filter_entry_frame = ttk.Frame(col2_frame, style="Header.TFrame")
        filter_entry_frame.grid(row=0, column=0, sticky="ew")

        self.filter_icon = ttk.Label(filter_entry_frame, text="🔍", style="CS.Toggle.TButton", width=2)
        self.filter_icon.pack(side="left")

        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(filter_entry_frame, textvariable=self.filter_var, style="Filter.TEntry")
        self.filter_entry.pack(side="left", fill="x", expand=True)
        # Add a trace to the variable, so any change calls _on_filter_change
        self.filter_var.trace_add("write", lambda *args: self._on_filter_change())

        # --- Toggle Button Color Logic ---
        toggle_frame = ttk.Frame(filter_entry_frame, style="Header.TFrame")
        toggle_frame.pack(side="right")

        self.clear_button = ttk.Button(toggle_frame, text="X", style="CS.Toggle.TButton", width=2, command=self._on_clear_filter)
        self.clear_button.pack(side="left", padx=(0, 5))
        Tooltip(self.clear_button, "Clear filter text")

        # 2. Add traces to the variables
        self.filter_cs.trace_add("write", lambda *args: self._update_toggle_colors())
        self.filter_mhw.trace_add("write", lambda *args: self._update_toggle_colors())
        self.filter_regex.trace_add("write", lambda *args: self._update_toggle_colors())

        # 3. Create buttons with their new, unique styles
        self.cs_button = ttk.Checkbutton(toggle_frame, text="Aa", style="CS.Toggle.TButton", variable=self.filter_cs, width=2, command=self._on_filter_change)
        self.cs_button.pack(side="left")
        Tooltip(self.cs_button, "Toggle Case Sensitive search")

        self.mhw_button = ttk.Checkbutton(toggle_frame, text="a̲b̲", style="MHW.Toggle.TButton", variable=self.filter_mhw, width=2, command=self._on_filter_change)
        self.mhw_button.pack(side="left")
        Tooltip(self.mhw_button, "Toggle Match Whole Word only")

        self.regex_button = ttk.Checkbutton(toggle_frame, text=".*", style="Regex.Toggle.TButton", variable=self.filter_regex, width=2, command=self._on_filter_change)
        self.regex_button.pack(side="left")
        Tooltip(self.regex_button, "Toggle regular expression search")

        # --- Column 3: Run All ---
        col3_frame = ttk.Frame(self.header_frame, style="Header.TFrame")
        col3_frame.pack(side="left", anchor='w')
        col3_sep = ttk.Separator(col3_frame, orient="vertical", style="Row.TSeparator")
        col3_sep.pack(side='left', fill='y', padx=(10, 10))

        self.run_all_button = ttk.Button(col3_frame, text="Run All", style="RunAll.TButton", width=10, command=self._run_all_visible, )
        self.run_all_button.pack(side='left', anchor='e', padx=(0, 10))
        Tooltip(self.run_all_button, "Run all tasks currently visible in the list")

        ttk.Button(col3_frame, text="", style="RunAll.TButton", width=0).pack(side='left', anchor='e', )

        # 4. Update colors initially
        self._update_toggle_colors()

    def _update_toggle_colors(self) -> None:
        """Update the foreground colors of toggle buttons based on their state"""
        # Update CS button color
        cs_color = "green" if self.filter_cs.get() else "black"
        self.style.configure("CS.Toggle.TButton", foreground=cs_color)

        # Update MHW button color  
        mhw_color = "green" if self.filter_mhw.get() else "black"
        self.style.configure("MHW.Toggle.TButton", foreground=mhw_color)

        # Update Regex button color
        regex_color = "green" if self.filter_regex.get() else "black"
        self.style.configure("Regex.Toggle.TButton", foreground=regex_color)

    def _create_status_bar(self) -> None:
        """Creates the status bar label (e.g., "Displaying 10 results...")"""
        status_frame = ttk.Frame(self, style="Status.TFrame")
        status_frame.grid(row=1, column=0, sticky="ew")

        self.status_label = ttk.Label(status_frame, text="Displaying 0 results out of 0", style="Status.TLabel", anchor="w", justify="center")
        self.status_label.pack()

    def _create_task_list_area(self) -> None:
        """Creates the scrollable canvas area for displaying task rows."""
        # This frame will hold the canvas and scrollbar
        canvas_frame = tk.Frame(self)
        canvas_frame.grid(row=2, column=0, sticky="nsew")
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # The canvas widget that allows scrolling
        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0, background="white")
        # The scrollbar, linked to the canvas
        self.scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # A placeholder to maintain layout width when scrollbar is hidden
        self.scrollbar_placeholder = ttk.Button(canvas_frame, text="", style="RunAll.TButton", width=0, state='disabled')

        # Grid layout for canvas/scrollbar
        self.scrollbar_placeholder.grid(row=0, column=1, sticky="ns")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # This is the frame *inside* the canvas that will hold all task rows
        self.task_list_frame = ttk.Frame(self.canvas, style="Normal.TFrame")

        # Create the window ONCE and store its ID
        # This tells the canvas to manage the 'task_list_frame'
        self.canvas_window = self.canvas.create_window((0, 0), window=self.task_list_frame, anchor="nw")

        # "NO DATA" placeholder
        self.no_data_label = ttk.Label(self.task_list_frame, text="NO DATA AVAILABLE", font=("tahoma", 14, "bold"), foreground="gray")

        # "Loading..." placeholder
        self.loading_label = ttk.Label(self.task_list_frame, text="Loading tasks...", font=("tahoma", 14, "bold"), foreground="gray")

        # Consolidated layout logic
        # Bind to both canvas and frame resizes to call the same function
        self.task_list_frame.bind("<Configure>", lambda e: self._refresh_canvas_layout())
        self.canvas.bind("<Configure>", lambda e: self._refresh_canvas_layout())

        # --- Mousewheel Binding ---
        self.master.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.master.bind_all("<Button-4>", self._on_mousewheel, add="+")  # Linux
        self.master.bind_all("<Button-5>", self._on_mousewheel, add="+")  # Linux

        # --- Keyboard Navigation Binding ---
        # Bind to 'bind_all' to catch keys regardless of which widget has focus
        self.master.bind_all("<Up>", self._on_key_up, add="+")
        self.master.bind_all("<Down>", self._on_key_down, add="+")

    def _refresh_canvas_layout(self, event: Optional[tk.Event] = None) -> None:
        """
        Consolidated function to update canvas scroll region and inner frame width.
        Only enable scrolling when content is taller than the canvas.
        
        Args:
            event: The configure event (optional).
        """
        self.master.update_idletasks()  # Ensure all widget sizes are calculated

        # 1. Update inner frame width to match canvas width
        if self.canvas_window:
            self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width())

        # 2. Update scroll region but only enable scrolling when needed
        content_bbox = self.canvas.bbox("all")  # Get bounding box of all content
        canvas_height = self.canvas.winfo_height()

        if content_bbox:
            content_height = content_bbox[3] - content_bbox[1]  # Total height of content

            # Only enable scrolling if content is taller than canvas
            if content_height > canvas_height:
                # Only update if scrollregion actually changed
                current_scrollregion = self.canvas.cget('scrollregion')
                new_scrollregion = ' '.join(str(x) for x in content_bbox)
                if current_scrollregion != new_scrollregion:
                    self.canvas.configure(scrollregion=content_bbox)
                
                # Show scrollbar, hide placeholder
                self.scrollbar_placeholder.grid_remove()
                self.scrollbar.grid()

                # --- Mousewheel Binding ---
                self.master.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
                self.master.bind_all("<Button-4>", self._on_mousewheel, add="+")  # Linux
                self.master.bind_all("<Button-5>", self._on_mousewheel, add="+")  # Linux

            else:
                # Content is shorter than canvas, disable scrolling
                # Only disable if currently enabled
                if self.scrollbar.winfo_ismapped():
                    self.scrollbar.grid_remove()
                    self.canvas.yview_moveto(0)  # Scroll to top
                    self.scrollbar_placeholder.grid()  # Show placeholder
                    
                    # --- Mousewheel Binding ---
                    self.master.unbind_all("<MouseWheel>")
                    self.master.unbind_all("<Button-4>")  # Linux
                    self.master.unbind_all("<Button-5>")  # Linux

    def _on_mousewheel(self, event: tk.Event) -> None:
        """
        Handles mouse wheel scrolling events for the canvas.

        Args:
            event: The mouse wheel event.
        """
        # Check if the widget is a child of the canvas
        widget = event.widget
        is_child = False
        while widget:
            if widget == self.canvas:
                is_child = True
                break
            widget = getattr(widget, 'master', None)

        if not is_child:
            return

        # Platform-specific scrolling
        if event.num == 4:  # Linux scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.yview_scroll(1, "units")
        else:  # Windows/macOS
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def _populate_tasks(self) -> None:
        """
        Creates all task row widgets *once* and stores them in self.task_widgets.
        
        This is an optimization. Rows are not destroyed, just hidden/shown
        using pack_forget() and pack().
        """
        self.task_widgets = []
        normal_bg = self.style.lookup("Normal.TFrame", "background")

        for task_name in self.master_task_list:
            # Create the main frame for the row
            row_frame = ttk.Frame(self.task_list_frame, style="Normal.TFrame", padding=(2, 2))

            # --- Configure Grid for this row ---
            # This grid is *inside* the row_frame, but we use .pack() to place widgets
            row_frame.grid_columnconfigure(0, weight=0, minsize=100)  # Col 1
            row_frame.grid_columnconfigure(1, weight=0)  # Sep 1
            row_frame.grid_columnconfigure(2, weight=1)  # Col 2 (expandable)
            row_frame.grid_columnconfigure(3, weight=0)  # Sep 2
            row_frame.grid_columnconfigure(4, weight=0, minsize=100)  # Col 3

            # --- Separators (Borders) ---
            sep1 = ttk.Separator(row_frame, orient="vertical", style="Row.TSeparator")
            sep2 = ttk.Separator(row_frame, orient="vertical", style="Row.TSeparator")

            # --- Column 1: Spacing & Separator ---
            col1_frame = ttk.Frame(row_frame, style="Normal.TFrame")
            ttk.Frame(col1_frame, style="Normal.TFrame", width=0).pack(side="left", padx=18)

            # --- Column 2: Task Name (Text widget) ---
            col2_frame = ttk.Frame(row_frame, style="Normal.TFrame")

            # Use a Text widget for rich formatting (highlighting)
            task_text = tk.Text(col2_frame, height=1, relief="flat",
                                background=normal_bg,
                                width=len(task_name),
                                font=('segoe ui', 10), wrap="none")
            task_text.insert("1.0", task_name)
            task_text.tag_configure("highlight", background="yellow")
            task_text.configure(state="disabled")  # Make it read-only
            task_text.pack(anchor="w")

            # --- Column 3: Run Button ---
            col3_frame_ = ttk.Frame(row_frame, style="Normal.TFrame")

            run_button = ttk.Button(col3_frame_, text="Run", width=11, style="Run.TButton")
            run_button.pack(side="right", padx=(2, 10))

            # --- Place all columns using .pack() for horizontal layout ---
            col1_frame.pack(side="left", anchor="w")
            sep1.pack(side='left', fill='y', padx=(10, 10))
            col2_frame.pack(side="left", anchor="w", expand=True, fill='x')
            sep2.pack(side='left', fill='y', padx=(10, 10))
            col3_frame_.pack(side="right", anchor="e", )

            # --- Store widget data ---
            task_data: Dict[str, Any] = {
                "task_name": task_name,
                "row_frame": row_frame,
                "task_text": task_text,
                "run_button": run_button,
                "is_running": False,
                # Store all widgets that need styling on selection
                "style_widgets": [row_frame, col1_frame, col2_frame, col3_frame_, sep1, sep2]
            }

            # --- Bindings ---
            # Set the command for the run button
            run_button.configure(command=lambda t=task_data: self._run_task(t))

            # Row selection binding
            # Bind all widgets in the row to the same click handler
            widgets_to_bind = [row_frame, col1_frame, col2_frame, col3_frame_, task_text, sep1, sep2, run_button]
            for w in widgets_to_bind:
                w.bind("<Button-1>", lambda e, t=task_data: self._on_row_click(e, t))

            self.task_widgets.append(task_data)

    def _set_row_style(self, task_data: Dict[str, Any], style_name: str) -> None:
        """
        Helper function to apply a style to all widgets in a row.

        Args:
            task_data: The task data dictionary for the row.
            style_name: The name of the ttk.Style (e.g., "Normal.TFrame").
        """
        try:
            bg_color = self.style.lookup(style_name, "background")
        except tk.TclError:
            # Fallback if style/lookup fails
            bg_color = SELECTED_ROW_COLOR if "Selected" in style_name else self.master.cget('background')

        # Apply style to all ttk widgets
        for widget in task_data['style_widgets']:
            widget.configure(style=style_name)

        # Manually set background for non-ttk Text widget
        task_data['task_text'].configure(background=bg_color)

        # Special handling for separators
        sep_style = "Selected.TSeparator" if "Selected" in style_name else "Row.TSeparator"
        for widget in task_data['style_widgets']:
            if isinstance(widget, ttk.Separator):
                widget.configure(style=sep_style)

    def _on_row_click(self, event: Optional[tk.Event], task_data: Dict[str, Any]) -> None:
        """
        Handles the selection of a task row.

        Args:
            event: The click event (can be None if called programmatically).
            task_data: The task data dictionary for the clicked row.
        """
        # If the clicked row is already selected, do nothing
        if self.selected_row_data == task_data:
            return

        # Deselect the *old* row, if one was selected
        if self.selected_row_data:
            self._set_row_style(self.selected_row_data, "Normal.TFrame")

        # Select the *new* row
        self._set_row_style(task_data, "Selected.TFrame")
        self.selected_row_data = task_data  # Store the newly selected row

        print(f"Selected row: {task_data['task_name']}")

    def _update_task_list(self) -> None:
        """
        The core filtering, sorting, and display logic.
        
        Filters the master list, sorts the result, and then uses
        pack_forget() and pack() to display only the matching rows.
        """
        filter_text = self.filter_var.get()
        use_cs = self.filter_cs.get()
        use_mhw = self.filter_mhw.get()
        use_regex = self.filter_regex.get()

        # --- 1. Forget all current rows & labels ---
        # This hides all rows without destroying them
        for task_data in self.task_widgets:
            task_data['row_frame'].pack_forget()  # Use pack_forget, not grid_forget
        self.no_data_label.pack_forget()

        # --- Show "Loading..." label ---
        self.loading_label.pack(pady=50)
        # Force Tkinter to redraw the UI *now*
        self.master.update_idletasks()

        # --- 2. Filter tasks (This is the "slow" part) ---
        filtered_tasks: List[Dict[str, Any]] = []
        flags = 0 if use_cs else re.IGNORECASE

        for task_data in self.task_widgets:
            task_name = task_data['task_name']
            match = False
            if not filter_text:
                match = True  # Show all if filter is empty
            else:
                try:
                    if use_regex:
                        if re.search(filter_text, task_name, flags):
                            match = True
                    elif use_mhw:
                        # Match whole word
                        pattern = r'\b' + re.escape(filter_text) + r'\b'
                        if re.search(pattern, task_name, flags):
                            match = True
                    else:
                        # Standard substring search
                        if filter_text in task_name or (not use_cs and filter_text.lower() in task_name.lower()):
                            match = True
                except re.error:
                    pass  # Ignore invalid regex

            if match:
                filtered_tasks.append(task_data)

        # --- 3. Sort tasks ---
        if self.sort_order == "asc":
            filtered_tasks.sort(key=lambda x: x['task_name'])
        else:
            filtered_tasks.sort(key=lambda x: x['task_name'], reverse=True)

        # --- 4. Hide "Loading..." label ---
        self.loading_label.pack_forget()

        # --- SAVE VISIBLE TASKS ---
        self.visible_tasks = filtered_tasks  # Store for navigation/run all
        # --- End ---

        # --- 5. Display tasks ---
        if not filtered_tasks:
            # Show "NO DATA" if list is empty
            self.no_data_label.pack(pady=50)
        else:
            # Pack the filtered and sorted rows back into the frame
            for task_data in filtered_tasks:
                # Use pack here to stack the grid-based rows vertically
                task_data['row_frame'].pack(fill="x", expand=True)
                # Apply text highlighting for the filter
                self._highlight_text(task_data['task_text'], task_data['task_name'], filter_text, use_cs, use_regex, use_mhw)

        # --- 6. Update status ---
        self.status_label.config(text=f"Displaying {len(filtered_tasks)} results out of {len(self.master_task_list)}")

        # --- Refresh canvas scrolling immediately ---
        self._refresh_canvas_layout()

    def _highlight_text(self, text_widget: tk.Text, full_text: str, filter_text: str, use_cs: bool, use_regex: bool, use_mhw: bool) -> None:
        """
        Applies a 'highlight' tag to the filter match within the task name.

        Args:
            text_widget: The tk.Text widget to modify.
            full_text: The complete, unmodified task name.
            filter_text: The text to search for.
            use_cs: Case-sensitive flag.
            use_regex: Regex flag.
            use_mhw: Match whole word flag.
        """
        text_widget.configure(state="normal")  # Enable writing
        text_widget.delete("1.0", "end")
        text_widget.insert("1.0", full_text)
        text_widget.tag_remove("highlight", "1.0", "end")  # Clear old highlights

        if not filter_text:
            text_widget.configure(state="disabled")  # Disable writing
            return

        flags = 0 if use_cs else re.IGNORECASE
        pattern = filter_text

        if not use_regex:
            pattern = re.escape(filter_text)  # Escape special chars
            if use_mhw:
                pattern = r'\b' + pattern + r'\b'  # Add word boundaries

        try:
            # Find all matches and add the tag
            for match in re.finditer(pattern, full_text, flags):
                start, end = match.span()
                start_index = f"1.{start}"
                end_index = f"1.{end}"
                text_widget.tag_add("highlight", start_index, end_index)
        except re.error:
            pass  # Ignore invalid regex
            
        text_widget.configure(state="disabled")  # Disable writing

    def _on_filter_change(self, *args) -> None:
        """Callback for when the filter text or options change."""
        # We call _update_task_list directly
        self._update_task_list()

    def _on_clear_filter(self) -> None:
        """Callback for the 'X' button to clear the filter."""
        self.filter_var.set("")
        # _update_task_list() is already called by the filter_var trace

    def _on_sort_toggle(self) -> None:
        """Callback for the sort button (AZ/ZA)."""
        if self.sort_order == "asc":
            self.sort_order = "desc"
            self.sort_button.config(text="ZA↑")
        else:
            self.sort_order = "asc"
            self.sort_button.config(text="AZ↓")
        self._update_task_list()  # Re-sort and update the view

    def _run_task(self, task_data: Dict[str, Any]) -> None:
        """
        Starts the execution of a single task.
        
        Disables the button, starts the animation, and launches the
        worker thread.

        Args:
            task_data: The task data dictionary for the row.
        """
        if task_data['is_running']:
            return  # Don't run if already running
            
        task_data['is_running'] = True
        button = task_data['run_button']
        button.config(text="Running.", state="disabled")
        
        self._animate_run(button)  # Start animation
        
        # Run the actual work in a separate thread
        thread = threading.Thread(target=self._task_worker, args=(task_data,), daemon=True)
        thread.start()

    def _animate_run(self, button: ttk.Button, state: int = 0) -> None:
        """
        Recursively animates the "Running..." text on a button.

        Args:
            button: The button to animate.
            state: The current animation frame (0, 1, or 2).
        """
        if not button.instate(['disabled']):
            return  # Stop animation if button is re-enabled
            
        states = ["Running.  ", "Running.. ", "Running..."]
        try:
            button.config(text=states[state])
            next_state = (state + 1) % len(states)
            # Schedule the next frame
            self.run_animation_job[button] = self.master.after(300, self._animate_run, button, next_state)
        except tk.TclError:
            # Widget was destroyed, stop animation
            pass

    def _task_worker(self, task_data: Dict[str, Any]) -> None:
        """
        This runs in a separate thread.
        Never touch Tkinter widgets directly from here.
        
        Args:
            task_data: The task's data dictionary.
        """
        task_name = task_data['task_name']
        print(f"Task Started: {task_name}")
        
        # Simulate a long-running task
        sleep_time = random.uniform(1.5, 5.0)
        time.sleep(sleep_time)
        
        print(f"Task Finished: {task_name}")

        # Schedule the completion callback to run on the *main GUI thread*
        self.master.after(0, self._on_task_complete, task_data)

    def _on_task_complete(self, task_data: Dict[str, Any]) -> None:
        """
        This runs back on the main GUI thread.
        It's safe to update widgets here.
        
        Args:
            task_data: The task's data dictionary.
        """
        task_data['is_running'] = False
        button = task_data['run_button']
        
        # Stop the animation job
        job = self.run_animation_job.pop(button, None)
        if job:
            self.master.after_cancel(job)
        
        # Check if button still exists before configuring
        if button.winfo_exists():
            button.config(text="Run", state="normal")  # Reset button

    def _run_all_visible(self) -> None:
        """Runs all tasks that are currently visible in the filtered list."""
        print("--- Running all visible tasks ---")
        
        # Get the list of visible tasks (this is faster than checking ismapped())
        visible_tasks_list = self.visible_tasks
        
        if not visible_tasks_list:
            print("No visible tasks to run.")
            return

        for task_data in visible_tasks_list:
            self._run_task(task_data)  # Start each task

    def _is_focus_in_list(self, widget: tk.Misc) -> bool:
        """
        Helper function to check if the currently focused widget is
        a child of the main task list canvas.
        
        Args:
            widget: The widget to check (usually self.master.focus_get()).

        Returns:
            True if the widget is inside the canvas, False otherwise.
        """
        current = widget
        while current:
            if current == self.canvas:
                # Yes, the focused widget is inside our canvas
                return True
            if current == self:
                # We've hit the main app frame, so we're not in the list
                return False
            # Move up the widget hierarchy
            current = getattr(current, 'master', None)
        return False

    def _on_key_up(self, event: tk.Event) -> Optional[str]:
        """
        Handles the 'Up' arrow key press.
        Only navigates if the mouse is currently hovering over the task list.
        
        Args:
            event: The key press event.

        Returns:
            "break" to stop event propagation if handled, else None.
        """
        try:
            # 1. Get the widget currently under the mouse pointer
            x = self.master.winfo_pointerx()
            y = self.master.winfo_pointery()
            widget_under_mouse = self.master.winfo_containing(x, y)
        except (tk.TclError, AttributeError):
            # This can fail if the pointer isn't over the window
            return

        # 2. Check if that widget is part of our scrollable list
        if widget_under_mouse and self._is_widget_in_list(widget_under_mouse):

            # 3. If yes, move selection
            if str(self.task_list_frame) in str(widget_under_mouse):
                self._move_selection(-1)  # -1 for "Up"
                return "break"  # Stop event from propagating
        return None  # Explicitly return None if not handled

    def _on_key_down(self, event: tk.Event) -> Optional[str]:
        """
        Handles the 'Down' arrow key press.
        Only navigates if the mouse is currently hovering over the task list.
        
        Args:
            event: The key press event.

        Returns:
            "break" to stop event propagation if handled, else None.
        """
        try:
            # 1. Get the widget currently under the mouse pointer
            x = self.master.winfo_pointerx()
            y = self.master.winfo_pointery()
            widget_under_mouse = self.master.winfo_containing(x, y)
        except (tk.TclError, AttributeError):
            # This can fail if the pointer isn't over the window
            return

        print('---DOWN\t\t>>', widget_under_mouse, '\n\t\t  ', self.task_list_frame, '\n\t\t  ', True if str(self.task_list_frame) in str(widget_under_mouse) else False)

        # 2. Check if that widget is part of our scrollable list
        if widget_under_mouse and self._is_widget_in_list(widget_under_mouse):

            # 3. If yes, move selection
            if str(self.task_list_frame) in str(widget_under_mouse):
                self._move_selection(1)  # 1 for "Down"
                return "break"  # Stop event from propagating
        return None  # Explicitly return None if not handled

    def _is_widget_in_list(self, widget: tk.Misc) -> bool:
        """
        Checks if a given widget is the task_list_frame itself
        or one of its children (i.e., inside the scrollable area).

        This is a robust replacement for checking widget path strings.
        
        Args:
            widget: The widget to check.

        Returns:
            True if the widget is a descendant of self.task_list_frame.
        """
        current = widget
        while current:
            # Check if we've found the task list frame
            if current == self.task_list_frame:
                return True
            # Check if we've gone "too high" (up to the main app)
            if current == self:
                return False
            # Move one level up in the widget hierarchy
            try:
                current = current.master
            except AttributeError:
                # Reached the top (like 'root')
                return False
        return False

    def _move_selection(self, direction: int) -> None:
        """
        Moves the row selection up or down in the visible list.

        Args:
            direction: -1 for Up, 1 for Down.
        """
        visible_list = self.visible_tasks
        if not visible_list:
            return  # Nothing to select

        current_selection = self.selected_row_data
        
        if current_selection is None:
            # No selection, so select the first (if Down) or last (if Up)
            new_selection = visible_list[0] if direction == 1 else visible_list[-1]
        else:
            try:
                # Find current index in the *visible* list
                current_index = visible_list.index(current_selection)
                new_index = current_index + direction
                
                # NEW NON-WRAPPING LOGIC:
                if new_index < 0:
                    # We are at the top (index 0) and pressed Up. Do nothing.
                    return
                if new_index >= len(visible_list):
                    # We are at the bottom and pressed Down. Do nothing.
                    return
                # --- End of Modification ---

                new_selection = visible_list[new_index]

            except ValueError:
                # Selected item is no longer visible (e.g., list was filtered)
                # Default to selecting the first or last item
                new_selection = visible_list[0] if direction == 1 else visible_list[-1]

        # Trigger the click/selection logic
        self._on_row_click(None, new_selection)

        # --- Correct ".see()" logic for a Canvas ---
        
        # Ensure all widget geometry is up-to-date before we read it
        self.master.update_idletasks()

        try:
            # 1. Get Viewport geometry
            canvas_height = self.canvas.winfo_height()
            top_fraction, bottom_fraction = self.canvas.yview()

            # 2. Get total scrollable content height
            list_height = self.task_list_frame.winfo_height()
            if list_height == 0:
                return  # Nothing to scroll

            # 3. Calculate current viewport in pixels
            viewport_top_y = top_fraction * list_height
            viewport_bottom_y = viewport_top_y + canvas_height

            # 4. Get Widget geometry (relative to the list_frame)
            widget_top = new_selection['row_frame'].winfo_y()
            widget_height = new_selection['row_frame'].winfo_height()
            widget_bottom = widget_top + widget_height

            # 5. Check the three conditions

            if widget_top < viewport_top_y:
                # --- CONDITION 1: WIDGET IS ABOVE VIEWPORT ---
                # Scroll to show the top of the widget at the top of the view
                fraction = widget_top / list_height
                self.canvas.yview_moveto(fraction)

            elif widget_bottom > viewport_bottom_y:
                # --- CONDITION 2: WIDGET IS BELOW VIEWPORT ---
                # Scroll to show the bottom of the widget at the bottom of the view
                new_viewport_top_y = widget_bottom - canvas_height
                new_viewport_top_y = max(0, new_viewport_top_y)
                fraction = new_viewport_top_y / list_height
                self.canvas.yview_moveto(fraction)
                
        except (tk.TclError, AttributeError, ZeroDivisionError):
            # This can fail if the window is being resized or has no height.
            pass
        # --- End of .see() logic ---
        
# --- Main application entry point ---
if __name__ == "__main__":
    """
    Main entry point for the application.
    Creates the root window and the TaskManager instance.
    """
    root = tk.Tk()
    root.title("Professional Task Runner")
    root.geometry("500x600")

    # This test_Frame is not strictly necessary but was in the original
    test_Frame = tk.Frame(root, border=3, padx=20, pady=20)
    test_Frame.pack()

    app = TaskManager(master=test_Frame)
    app.pack(expand=True, fill="both")
    
    root.mainloop()