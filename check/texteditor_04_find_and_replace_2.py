import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, List, Any, Optional, Tuple, Union

# from dataclasses import dataclass # Removed

# --- Configuration Dataclasses ---



class TooltipConfig:
    """Configuration for tooltip appearance and behavior."""

    def __init__(
        self,
        background: str = "#FFFFFF",
        foreground: str = "#000000",
        font: Tuple[str, int] = ("Segoe UI", 9),
        delay: int = 500,
        justify: str = "left",
    ) -> None:
        self.background = background
        self.foreground = foreground
        self.font = font
        self.delay = delay
        self.justify = justify



class StyleConfig:
    """Configuration for widget styling."""

    def __init__(
        self,
        frame_bg: str = "#F3F3F3",
        entry_bg: str = "#FFFFFF",
        entry_fg: str = "#000000",
        entry_font: Tuple[str, int] = ("Segoe UI", 10),
        placeholder_color: str = "grey",
        border_color: str = "#CCCCCC",
    ) -> None:
        self.frame_bg = frame_bg
        self.entry_bg = entry_bg
        self.entry_fg = entry_fg
        self.entry_font = entry_font
        self.placeholder_color = placeholder_color
        self.border_color = border_color



class FindReplaceConfig:
    """Main configuration for FindReplace widget."""

    def __init__(
        self,
        style: Optional[StyleConfig] = None,
        tooltip: Optional[TooltipConfig] = None,
        default_show_replace: bool = False,
    ) -> None:
        # Use default instances if None is provided
        self.style = style if style is not None else StyleConfig()
        self.tooltip = tooltip if tooltip is not None else TooltipConfig()
        self.default_show_replace = default_show_replace


# --- Custom Class for Tooltips ---
class Tooltip:
    """
    Creates a tooltip for a given widget that appears below and right-aligned.
    """

    def __init__(self, widget: tk.Widget, text: str, config: TooltipConfig) -> None:
        self.widget = widget
        self.text = text
        self.config = config
        self.tip_window: Optional[tk.Toplevel] = None
        self.schedule_id: Optional[str] = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event: Optional[tk.Event] = None) -> None:
        """Schedule to show the tip after a delay."""
        self.schedule_id = self.widget.after(self.config.delay, self._create_tip_window)

    def _create_tip_window(self) -> None:
        """Create and position the tooltip window."""
        if self.tip_window or not self.text:
            return

        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx()
        y = y + self.widget.winfo_rooty() + self.widget.winfo_height()

        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)

        label = tk.Label(
            self.tip_window,
            text=self.text,
            justify=self.config.justify,
            background=self.config.background,
            foreground=self.config.foreground,
            relief="solid",
            borderwidth=1,
            font=self.config.font,
        )
        label.pack(ipadx=4, ipady=2)

        self.tip_window.update_idletasks()
        tip_width = self.tip_window.winfo_width()
        widget_width = self.widget.winfo_width()

        final_x = x + widget_width - tip_width
        self.tip_window.wm_geometry(f"+{int(final_x)}+{int(y)}")

    def hide_tip(self, event: Optional[tk.Event] = None) -> None:
        """Hide and destroy the tooltip."""
        if self.schedule_id:
            self.widget.after_cancel(self.schedule_id)
            self.schedule_id = None

        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


# --- Custom Class for Placeholder Entry ---
class PlaceholderEntry(tk.Entry):
    """
    An Entry widget that shows a placeholder text (watermark)
    when empty and not in focus.
    """

    def __init__(
        self, master: tk.Widget, placeholder: str, config: StyleConfig, **kwargs: Any
    ) -> None:
        super().__init__(master, **kwargs)
        self.placeholder: str = placeholder
        # Renamed attribute to avoid conflict with self.config() method
        self.style_config: StyleConfig = config
        self.default_fg: str = self["fg"]

        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self._put_placeholder()

    def _put_placeholder(self) -> None:
        """Insert the placeholder text if the entry is empty."""
        if self.get() == "":
            self.configure(fg=self.style_config.placeholder_color)
            self.insert(0, self.placeholder)

    def _on_focus_in(self, event: tk.Event) -> None:
        """Remove placeholder on focus."""
        if (
            self.get() == self.placeholder
            and self["fg"] == self.style_config.placeholder_color
        ):
            self.delete(0, tk.END)
            self.configure(fg=self.default_fg)

    def _on_focus_out(self, event: tk.Event) -> None:
        """Add placeholder if empty on focus out."""
        if self.get() == "":
            self._put_placeholder()


# --- Style Definitions ---
class AppStyles:
    """
    Holds all ttk styling configurations for the application.
    """

    def __init__(self, config: StyleConfig) -> None:
        self.style: ttk.Style = ttk.Style()
        # --- FIXED ---
        # Renamed self.config to self.style_data to avoid name conflict
        # with the child FindReplaceDemo class.
        self.style_data: StyleConfig = config

    def setup_styles(self) -> None:
        """Configures all the ttk styles for the find widget."""

        # --- FIXED --- (using self.style_data)
        self.style.configure(
            "FindOption.Normal.TButton",
            background=self.style_data.frame_bg,
            font=("Segoe UI", 10),
        )

        # --- FIXED --- (using self.style_data)
        self.style.configure(
            "FindOption.Inactive.TButton",
            background=self.style_data.entry_bg,
            font=("Segoe UI", 10),
        )

        # --- FIXED --- (using self.style_data)
        self.style.configure(
            "FindOption.Active.TButton",
            background=self.style_data.entry_bg,
            font=("Segoe UI", 10),
        )

        self.style.map(
            "FindOption.Inactive.TButton",
            foreground=[
                ("!active", "#9C9C9C"),
                ("active", "#0051FF"),
                ("pressed", "#0051FF"),
            ],
            bordercolor=[
                ("!active", "#FF0000"),
                ("active", "#FF0000"),
                ("pressed", "#FF0000"),
            ],
        )

        self.style.map(
            "FindOption.Active.TButton",
            foreground=[
                ("!active", "#0051FF"),
                ("active", "#9C9C9C"),
                ("pressed", "#9C9C9C"),
            ],
            bordercolor=[
                ("!active", "#0051FF"),
                ("active", "#9C9C9C"),
                ("pressed", "#9C9C9C"),
            ],
        )


# --- Main Application Controller ---
class FindReplaceDemo(AppStyles):
    """
    Main application class for the Find/Replace demo.
    This class manages the find/replace logic and pop-up frame.
    """

    def __init__(
        self,
        parent: tk.Widget,
        text_widget: tk.Text,
        config: FindReplaceConfig,
        on_find_callback: Optional[
            Callable[["FindReplaceDemo", str, Dict[str, bool]], None]
        ] = None,
        on_replace_callback: Optional[
            Callable[["FindReplaceDemo", str, str, Dict[str, bool]], None]
        ] = None,
        on_options_change: Optional[
            Callable[["FindReplaceDemo", Dict[str, bool]], None]
        ] = None,
    ) -> None:

        # Initialize AppStyles with configuration
        # This correctly calls AppStyles.__init__(config.style)
        # The parent's self.style_data is now correctly set.
        super().__init__(config.style)

        self.parent: tk.Widget = parent
        self.text_widget: tk.Text = text_widget
        # This self.config (a FindReplaceConfig) no longer conflicts
        # with the parent's self.style_data.
        self.config: FindReplaceConfig = config

        # Callback functions
        self.on_find_callback: Optional[Callable] = on_find_callback
        self.on_replace_callback: Optional[Callable] = on_replace_callback
        self.on_options_change: Optional[Callable] = on_options_change

        # --- State Variables ---
        self.find_frame: Optional[tk.Frame] = None
        self.replace_visible: tk.BooleanVar = tk.BooleanVar(
            value=config.default_show_replace
        )
        self.match_case_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.whole_word_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.regex_var: tk.BooleanVar = tk.BooleanVar(value=False)

        # Widget references
        self.find_entry: Optional[PlaceholderEntry] = None
        self.replace_entry: Optional[PlaceholderEntry] = None
        self.match_case_button: Optional[ttk.Button] = None
        self.whole_word_button: Optional[ttk.Button] = None
        self.regex_button: Optional[ttk.Button] = None
        self.results_label: Optional[tk.Label] = None
        self.toggle_replace_button: Optional[ttk.Button] = None
        self.find_prev_button: Optional[ttk.Button] = None
        self.find_next_button: Optional[ttk.Button] = None
        self.replace_button: Optional[ttk.Button] = None
        self.replace_all_button: Optional[ttk.Button] = None

        # Frame containers
        self._frame_containers: Dict[str, tk.Widget] = {}

        # Setup styles and initialize
        # This call now works because self.setup_styles() (in the parent)
        # will use self.style_data, which exists and is correct.
        self.setup_styles()
        self._setup_bindings()

    def _setup_bindings(self) -> None:
        """Configure all application bindings."""
        self.parent.bind("<Control-f>", self.show_find)
        self.parent.bind("<Control-h>", self.show_replace)
        self.parent.bind("<Escape>", self.hide_frame)

    def _layout_init(self) -> None:
        """
        Initialize the main layout structure and create all widget containers.
        This method only sets up the frame structure, not individual widgets.
        """
        if self.find_frame:
            return

        # === MAIN CONTAINER FRAME ===
        self.find_frame = tk.Frame(
            self.parent,
            bg=self.config.style.frame_bg,
            highlightbackground=self.config.style.border_color,
            highlightthickness=1,
        )

        # === CONFIGURE MAIN GRID LAYOUT ===
        self.find_frame.columnconfigure(0, weight=0, minsize=40)  # Toggle column
        self.find_frame.columnconfigure(1, weight=1)  # Inputs column
        self.find_frame.columnconfigure(2, weight=0, minsize=120)  # Actions column

        self.find_frame.rowconfigure(0, weight=0)  # Find row
        self.find_frame.rowconfigure(1, weight=0)  # Replace row

        # === CREATE ALL FRAME CONTAINERS ===
        self._create_frame_containers()

        # === CREATE ALL WIDGETS ===
        self._create_widgets()

        # === LAYOUT ALL WIDGETS ===
        self._layout_widgets()

    def _create_frame_containers(self) -> None:
        """Create all frame containers for organizing widgets."""

        self._frame_containers["toggle_frame"] = tk.Frame(
            self.find_frame, bg=self.config.style.frame_bg
        )

        self._frame_containers["input_main_frame"] = tk.Frame(
            self.find_frame, bg=self.config.style.frame_bg
        )

        self._frame_containers["find_input_frame"] = tk.Frame(
            self._frame_containers["input_main_frame"], bg=self.config.style.entry_bg
        )

        self._frame_containers["replace_input_frame"] = tk.Frame(
            self._frame_containers["input_main_frame"], bg=self.config.style.entry_bg
        )

        self._frame_containers["options_frame"] = tk.Frame(
            self._frame_containers["find_input_frame"], bg=self.config.style.entry_bg
        )

        self._frame_containers["actions_main_frame"] = tk.Frame(
            self.find_frame, bg=self.config.style.frame_bg
        )

        self._frame_containers["find_actions_frame"] = tk.Frame(
            self._frame_containers["actions_main_frame"], bg=self.config.style.frame_bg
        )

        self._frame_containers["replace_actions_frame"] = tk.Frame(
            self._frame_containers["actions_main_frame"], bg=self.config.style.frame_bg
        )

        self._frame_containers["status_frame"] = tk.Frame(
            self._frame_containers["find_actions_frame"], bg=self.config.style.frame_bg
        )

    def _create_widgets(self) -> None:
        """Create all widget instances."""

        self.toggle_replace_button = ttk.Button(
            self._frame_containers["toggle_frame"],
            text=">",
            width=3,
            command=self._toggle_replace_row,
        )

        self.find_entry = PlaceholderEntry(
            self._frame_containers["find_input_frame"],
            "Find",
            config=self.config.style,
            bg=self.config.style.entry_bg,
            fg=self.config.style.entry_fg,
            insertbackground=self.config.style.entry_fg,
            relief="flat",
            borderwidth=0,
            bd=0,
            highlightbackground=self.config.style.border_color,
            font=self.config.style.entry_font,
        )

        self.match_case_button = ttk.Button(
            self._frame_containers["options_frame"],
            text="Aa",
            width=2,
            style="FindOption.Inactive.TButton",
            command=self._on_toggle_match_case,
        )

        self.whole_word_button = ttk.Button(
            self._frame_containers["options_frame"],
            text="a̲b̲",
            width=2,
            style="FindOption.Inactive.TButton",
            command=self._on_toggle_whole_word,
        )

        self.regex_button = ttk.Button(
            self._frame_containers["options_frame"],
            text=".*",
            width=2,
            style="FindOption.Inactive.TButton",
            command=self._on_toggle_regex,
        )

        self.replace_entry = PlaceholderEntry(
            self._frame_containers["replace_input_frame"],
            "Replace",
            config=self.config.style,
            bg=self.config.style.entry_bg,
            fg=self.config.style.entry_fg,
            insertbackground=self.config.style.entry_fg,
            relief="flat",
            borderwidth=0,
            bd=0,
            highlightbackground=self.config.style.border_color,
            font=self.config.style.entry_font,
        )

        self.results_label = tk.Label(
            self._frame_containers["status_frame"],
            text="No results",
            bg=self.config.style.frame_bg,
            fg="#555555",
        )

        self.find_prev_button = ttk.Button(
            self._frame_containers["find_actions_frame"],
            text="↑",
            width=2,
            style="FindOption.Normal.TButton",
            command=self._on_find_previous,
        )

        self.find_next_button = ttk.Button(
            self._frame_containers["find_actions_frame"],
            text="↓",
            width=2,
            style="FindOption.Normal.TButton",
            command=self._on_find_next,
        )

        self.replace_button = ttk.Button(
            self._frame_containers["replace_actions_frame"],
            text="Re",
            width=2,
            style="FindOption.Normal.TButton",
            command=self._on_replace,
        )

        self.replace_all_button = ttk.Button(
            self._frame_containers["replace_actions_frame"],
            text="RA",
            width=2,
            style="FindOption.Normal.TButton",
            command=self._on_replace_all,
        )

        self._setup_tooltips()

    def _setup_tooltips(self) -> None:
        """Configure all tooltips for widgets."""
        Tooltip(self.match_case_button, "Match Case (Alt+C)", self.config.tooltip)
        Tooltip(self.whole_word_button, "Match Whole Word (Alt+W)", self.config.tooltip)
        Tooltip(
            self.regex_button, "Use Regular Expression (Alt+R)", self.config.tooltip
        )
        Tooltip(self.find_prev_button, "Find Previous", self.config.tooltip)
        Tooltip(self.find_next_button, "Find Next", self.config.tooltip)
        Tooltip(self.replace_button, "Replace", self.config.tooltip)
        Tooltip(self.replace_all_button, "Replace All", self.config.tooltip)

    def _layout_widgets(self) -> None:
        """Arrange all widgets in their respective containers."""

        self._frame_containers["toggle_frame"].grid(
            row=0, column=0, rowspan=2, padx=5, pady=5, sticky="ns"
        )
        self.toggle_replace_button.pack(fill="both", expand=True)

        # Fixed layout bug: Added rowspan=2
        self._frame_containers["input_main_frame"].grid(
            row=0, column=1, rowspan=2, padx=5, pady=5, sticky="ewns"
        )
        self._frame_containers["input_main_frame"].columnconfigure(0, weight=1)

        self._frame_containers["find_input_frame"].grid(
            row=0, column=0, sticky="ew", pady=(0, 2)
        )
        self._frame_containers["find_input_frame"].columnconfigure(0, weight=1)

        self.find_entry.grid(row=0, column=0, sticky="ew", ipady=4, padx=(5, 0))

        self._frame_containers["options_frame"].grid(
            row=0, column=1, padx=5, sticky="e"
        )
        self.match_case_button.grid(row=0, column=0, padx=2, ipadx=2)
        self.whole_word_button.grid(row=0, column=1, padx=2, ipadx=2)
        self.regex_button.grid(row=0, column=2, padx=2, ipadx=2)

        self._frame_containers["replace_input_frame"].grid(
            row=1, column=0, sticky="ew", pady=(2, 0)
        )
        self._frame_containers["replace_input_frame"].columnconfigure(0, weight=1)
        self.replace_entry.grid(row=0, column=0, sticky="ew", ipady=4, padx=(5, 0))

        # Fixed layout bug: Added rowspan=2
        self._frame_containers["actions_main_frame"].grid(
            row=0, column=2, rowspan=2, padx=5, pady=5, sticky="ns"
        )

        self._frame_containers["find_actions_frame"].pack(fill="x", expand=True)

        self._frame_containers["status_frame"].pack(side="left", fill="x", expand=True)
        self.results_label.pack(side="left", padx=(0, 5))

        self.find_prev_button.pack(side="left", padx=2, ipadx=2)
        self.find_next_button.pack(side="left", padx=2, ipadx=2)

        self._frame_containers["replace_actions_frame"].pack(
            fill="x", expand=True, pady=(2, 0)
        )
        self.replace_button.pack(side="left", ipadx=2)
        self.replace_all_button.pack(side="left", ipadx=2, padx=5)

        self._setup_widget_bindings()

        self._toggle_replace_row(force_state=self.config.default_show_replace)

    def _setup_widget_bindings(self) -> None:
        """Configure bindings for interactive widgets."""
        self.find_entry.bind("<KeyRelease>", self._on_find_key_release)
        self.find_entry.bind("<Return>", self._on_find_next)
        self.replace_entry.bind("<Return>", self._on_replace)

    def _toggle_replace_row(self, force_state: Optional[bool] = None) -> None:
        """Show or hide the Replace entry and buttons."""
        if force_state is not None:
            self.replace_visible.set(force_state)
        else:
            self.replace_visible.set(not self.replace_visible.get())

        if self.replace_visible.get():
            self._frame_containers["replace_input_frame"].grid(
                row=1, column=0, sticky="ew", pady=(2, 0)
            )
            self._frame_containers["replace_actions_frame"].pack(
                fill="x", expand=True, pady=(2, 0)
            )
            self.toggle_replace_button.config(text="▼")
        else:
            self._frame_containers["replace_input_frame"].grid_remove()
            self._frame_containers["replace_actions_frame"].pack_forget()
            self.toggle_replace_button.config(text="▶")

    def show_find(self, event: Optional[tk.Event] = None) -> None:
        """Show the find widget, focused on the Find entry."""
        if not self.find_frame:
            self._layout_init()

        self.find_frame.place(rely=0.0, relx=1.0, x=-10, y=10, anchor="ne")
        self.find_frame.lift()

        self._toggle_replace_row(force_state=False)
        self.find_entry.focus_set()
        self.find_entry.select_range(0, "end")

    def show_replace(self, event: Optional[tk.Event] = None) -> None:
        """Show the find widget, focused on the Replace entry."""
        if not self.find_frame:
            self._layout_init()

        self.find_frame.place(rely=0.0, relx=1.0, x=-10, y=10, anchor="ne")
        self.find_frame.lift()

        self._toggle_replace_row(force_state=True)
        self.replace_entry.focus_set()
        self.replace_entry.select_range(0, "end")

    def hide_frame(self, event: Optional[tk.Event] = None) -> None:
        """Hide the find widget and return focus to the main text area."""
        if self.find_frame:
            self.find_frame.place_forget()
        self.text_widget.focus_set()

    # --- Event Handlers ---
    def _on_find_key_release(self, event: tk.Event) -> None:
        """Called every time a key is pressed in the Find Entry."""
        if event.keysym == "Return":
            return

        if self.on_find_callback:
            search_options = self._get_search_options()
            self.on_find_callback(self, self.find_entry.get(), search_options)

    def _on_toggle_match_case(self) -> None:
        """Called when the 'Match Case' button is clicked."""
        new_state = not self.match_case_var.get()
        self.match_case_var.set(new_state)
        self._update_toggle_button_style(self.match_case_button, self.match_case_var)

        if self.on_options_change:
            self.on_options_change(self, self._get_search_options())

    def _on_toggle_whole_word(self) -> None:
        """Called when the 'Match Whole Word' button is clicked."""
        new_state = not self.whole_word_var.get()
        self.whole_word_var.set(new_state)
        self._update_toggle_button_style(self.whole_word_button, self.whole_word_var)

        if self.on_options_change:
            self.on_options_change(self, self._get_search_options())

    def _on_toggle_regex(self) -> None:
        """Called when the 'Use Regular Expression' button is clicked."""
        new_state = not self.regex_var.get()
        self.regex_var.set(new_state)
        self._update_toggle_button_style(self.regex_button, self.regex_var)

        if self.on_options_change:
            self.on_options_change(self, self._get_search_options())

    def _on_find_next(self, event: Optional[tk.Event] = None) -> str:
        """Called by Find Next button or Enter in Find Entry."""
        if self.on_find_callback:
            search_options = self._get_search_options()
            self.on_find_callback(self, self.find_entry.get(), search_options)
        return "break"

    def _on_find_previous(self) -> None:
        """Called by Find Previous button."""
        if self.on_find_callback:
            search_options = self._get_search_options()
            self.on_find_callback(self, self.find_entry.get(), search_options)

    def _on_replace(self, event: Optional[tk.Event] = None) -> str:
        """Called by Replace button or Enter in Replace Entry."""
        if self.on_replace_callback:
            search_options = self._get_search_options()
            self.on_replace_callback(
                self, self.find_entry.get(), self.replace_entry.get(), search_options
            )
        return "break"

    def _on_replace_all(self) -> None:
        """Called by Replace All button."""
        if self.on_replace_callback:
            search_options = self._get_search_options()
            self.on_replace_callback(
                self, self.find_entry.get(), self.replace_entry.get(), search_options
            )

    def _update_toggle_button_style(
        self, button: ttk.Button, variable: tk.BooleanVar
    ) -> None:
        """Helper to update a toggle button's style based on its variable."""
        if not button:
            return
        if variable.get():
            button.config(style="FindOption.Active.TButton")
        else:
            button.config(style="FindOption.Inactive.TButton")

    def _get_search_options(self) -> Dict[str, bool]:
        """Get current search options as a dictionary."""
        return {
            "match_case": self.match_case_var.get(),
            "whole_word": self.whole_word_var.get(),
            "regex": self.regex_var.get(),
        }

    def update_results_label(self, results_text: str) -> None:
        """Update the results label with new text."""
        if self.results_label:
            self.results_label.config(text=results_text)


# --- Event Handler Functions ---
def handle_find_callback(
    app_instance: FindReplaceDemo, search_text: str, options: Dict[str, bool]
) -> None:
    """Handle find operations."""
    print(f"Find: '{search_text}' with options: {options}")
    app_instance.update_results_label(f"Found: {search_text}")


def handle_replace_callback(
    app_instance: FindReplaceDemo,
    search_text: str,
    replace_text: str,
    options: Dict[str, bool],
) -> None:
    """Handle replace operations."""
    print(f"Replace: '{search_text}' with '{replace_text}', options: {options}")


def handle_options_change(
    app_instance: FindReplaceDemo, options: Dict[str, bool]
) -> None:
    """Handle search options changes."""
    print(f"Options changed: {options}")


# --- Main Application Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Professional Find/Replace Demo")
    root.geometry("800x600")

    # Create main widgets
    tk.Label(root, text="Press Ctrl+F (Find) or Ctrl+H (Replace)").pack(pady=10)
    main_text = tk.Text(root)
    main_text.pack(fill="both", expand=True, padx=10, pady=10)

    # Create configuration
    # This now works correctly
    app_config = FindReplaceConfig(default_show_replace=False)

    # Create the controller instance with dependency injection
    app = FindReplaceDemo(
        parent=root,
        text_widget=main_text,
        config=app_config,
        on_find_callback=handle_find_callback,
        on_replace_callback=handle_replace_callback,
        on_options_change=handle_options_change,
    )

    root.mainloop()
