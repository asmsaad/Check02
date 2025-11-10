import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, Callable, List

# --- Utility Class: Tooltip (Full ttk) ---

class Tooltip:
    """Creates a ttk-styled tooltip for a given widget."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget: tk.Widget = widget
        self.text: str = text
        self.tip_window: Optional[tk.Toplevel] = None
        self.schedule_id: Optional[str] = None
        
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event: Optional[tk.Event] = None) -> None:
        self.schedule_id = self.widget.after(500, self.create_tip_window)

    def create_tip_window(self) -> None:
        if self.tip_window or not self.text:
            return
            
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx()
        y = y + self.widget.winfo_rooty() + self.widget.winfo_height()

        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        
        # Use a dedicated style for the tooltip
        style = ttk.Style(self.tip_window)
        style.configure(
            "Tooltip.TLabel",
            background="#FFFFE0", # Light yellow
            foreground="#333333", # Dark text
            relief='solid',
            borderwidth=1,
            font=("Segoe UI", 9),
            padding=(4, 2)
        )
        
        label = ttk.Label(self.tip_window, text=self.text, 
                          justify='left', style="Tooltip.TLabel")
        label.pack()
        
        self.tip_window.update_idletasks()
        tip_width = self.tip_window.winfo_width()
        widget_width = self.widget.winfo_width()
        final_x = x + widget_width - tip_width
        
        self.tip_window.wm_geometry(f"+{int(final_x)}+{int(y)}")

    def hide_tip(self, event: Optional[tk.Event] = None) -> None:
        if self.schedule_id:
            self.widget.after_cancel(self.schedule_id)
            self.schedule_id = None
            
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# --- Utility Class: PlaceholderEntry (Full ttk) ---

class PlaceholderEntry(ttk.Entry):
    """
    A ttk.Entry widget that shows a placeholder text (watermark)
    when empty and not in focus, using ttk.Style.
    """
    def __init__(self, master: tk.Widget, placeholder: str, **kwargs: Any) -> None:
        
        self.normal_style: str = kwargs.get("style", "TEntry")
        self.placeholder_style: str = f"Placeholder.{self.normal_style}"
        self.placeholder: str = placeholder
        self.placeholder_color: str = 'grey'

        style = ttk.Style(master)
        style.configure(self.placeholder_style, foreground=self.placeholder_color)
        
        kwargs["style"] = self.placeholder_style
        
        super().__init__(master, **kwargs)
        self.insert(0, self.placeholder)
        
        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)

    def on_focus_in(self, event: tk.Event) -> None:
        if self.cget("style") == self.placeholder_style:
            self.delete(0, tk.END)
            self.configure(style=self.normal_style)

    def on_focus_out(self, event: tk.Event) -> None:
        if self.get() == '':
            self.insert(0, self.placeholder)
            self.configure(style=self.placeholder_style)

# --- Architecture Class: AppStyles (Light Theme) ---

class AppStyles:
    """
    Mixin class for defining all ttk styles for the application.
    Implements a clean, light theme for the Find/Replace widget.
    """
    def __init__(self) -> None:
        self.style = ttk.Style()
        self._define_styles()

    def _define_styles(self) -> None:
        """Defines all custom ttk styles."""
        
        # --- Frame Styles (Light) ---
        self.style.configure(
            "Find.TFrame", 
            background="#F0F0F0", 
            borderwidth=1, 
            relief='solid',
            bordercolor="#D0D0D0"
        )
        self.style.configure(
            "EntryContainer.TFrame", 
            background="#FFFFFF",
            borderwidth=1,
            relief='solid',
            bordercolor="#C0C0C0"
        )
        self.style.configure(
            "Actions.TFrame", 
            background="#F0F0F0" # Match main frame
        )
        
        # --- Action Button Style ---
        self.style.configure(
            'Find.TButton', 
            relief='flat', 
            background="#E1E1E1", 
            foreground="#333333",
            padding=5,
        )
        # self.style.map('Find.TButton',
        #     background=[('active', '#0078D4'), ('!disabled', 'white')],
        #     foreground=[('active', 'white')]
        # )
        
        # --- Toggle Button Style (Checkbutton as Button) ---
        self.style.configure(
            'Toggle.TButton',
            relief='flat',
            padding=5,
            background="#FFFFFF",
            indicatordiameter=-1 # Hide the checkbutton indicator
        )
        self.style.map('Toggle.TButton',
            # Change text color based on 'selected' state
            foreground=[
                ('!selected', 'grey'),  # Inactive
                ('selected', 'black')   # Active
            ],
            # Visual feedback on hover/press
            background=[
                ('pressed', '#C6C6C6'),
                ('active', '#E1E1E1')
            ]
        )
        
        # --- Entry Style ---
        self.style.configure(
            "Find.TEntry",
            fieldbackground="#FFFFFF",
            foreground="#333333",
            insertcolor="black",
            borderwidth=0,
            relief='flat',
            padding=5,
        )
        
        # --- Label Style ---
        self.style.configure(
            "Message.TLabel",
            background="#F0F0F0", # Match main frame
            foreground="grey"
        )

# --- Main Application (Converted to ttk and decoupled) ---

class FindReplaceDemo(AppStyles):
    
    def __init__(self, 
                 root: tk.Tk,
                 # --- Callbacks ---
                 on_find_changed: Callable[[str], None],
                 on_match_case_toggled: Callable[[bool], None],
                 on_whole_word_toggled: Callable[[bool], None],
                 on_regex_toggled: Callable[[bool], None],
                 on_find_next: Callable[[], None],
                 on_find_prev: Callable[[], None],
                 on_replace: Callable[[], None],
                 on_replace_all: Callable[[], None]
                 ) -> None:
        
        self.root: tk.Tk = root
        super().__init__() # Initializes self.style
        
        # --- Store Callbacks ---
        self.on_find_changed_callback = on_find_changed
        self.on_match_case_toggled_callback = on_match_case_toggled
        self.on_whole_word_toggled_callback = on_whole_word_toggled
        self.on_regex_toggled_callback = on_regex_toggled
        self.on_find_next_callback = on_find_next
        self.on_find_prev_callback = on_find_prev
        self.on_replace_callback = on_replace
        self.on_replace_all_callback = on_replace_all
        
        # --- Main text area ---
        ttk.Label(self.root, text="Press Ctrl+F or Ctrl+H").pack(pady=20)
        self.main_text = tk.Text(self.root)
        self.main_text.pack(fill='both', expand=True)
        
        # --- Frame & State ---
        self.master_frame: Optional[ttk.Frame] = None
        self.replace_visible: tk.BooleanVar = tk.BooleanVar(value=True)
        
        # --- Toggle Button State Variables ---
        self.match_case_var = tk.BooleanVar(value=False)
        self.whole_word_var = tk.BooleanVar(value=False)
        self.regex_var = tk.BooleanVar(value=False)

        # --- Bindings ---
        self.root.bind('<Control-f>', self.show_find)
        self.root.bind('<Control-h>', self.show_replace)
        self.root.bind('<Escape>', self.hide_frame)

    def _init_layout(self) -> None:
        """Creates the find/replace frame and all its child widgets."""
        if self.master_frame:
            return
            
     
        # ----------------- MASTER ------------------    
        self.master_frame = ttk.Frame(self.root, style="Find.TFrame")
        
        self.master_frame.columnconfigure(0, weight=0) 
        self.master_frame.columnconfigure(1, weight=1) 
        self.master_frame.columnconfigure(2, weight=0) 
        
        
        
        
        # ------------------ COL-1 ------------------ [ Toggle Button ]
        self.toggle_btn = ttk.Button(self.master_frame, text="❯", width=2, command=self.toggle_replace_row, style='Find.TButton')
        self.toggle_btn.grid(row=0, column=0, rowspan=2, padx=5, pady=5, sticky='ns')
        
        
        # ------------------ COL-2 ------------------ [ Find and Replace Entry (3 Selection Btn)]
        # --------------- COL-2  ROW-1 -------------- [Find and 3selection Btn]
        self.find_tools_frame = ttk.Frame(self.master_frame, style="EntryContainer.TFrame")
        self.find_tools_frame.grid(row=0, column=1, padx=5, pady=(5, 2), sticky='ew')
        self.find_tools_frame.columnconfigure(0, weight=1)
        # --------------- COL-2  ROW-1 -------------- [Replace Btn]
        self.replace_tools_frame = ttk.Frame(self.master_frame, style="EntryContainer.TFrame")
        self.replace_tools_frame.grid(row=1, column=1, columnspan=2, padx=5, pady=(0, 5), sticky='ew')
        self.replace_tools_frame.columnconfigure(0, weight=1)
                
                
        # ------------------ COL-3 ------------------ [ Additional Action Btns]
        # --------------- COL-3  ROW-1 -------------- [Select next , previous Btns, select to hilite btns]
        self.message_label = ttk.Label(self.master_frame, text="No result found", style="Message.TLabel")
        self.message_label.grid(row=0, column=2, padx=5, pady=(5, 2), sticky='ew')
        
        
        # ------------------ COL-4 ------------------ [ Additional Action Btns]
        # --------------- COL-4  ROW-1 -------------- [Select next , previous Btns, select to hilite btns]
        actions_container = ttk.Frame(self.master_frame, style="EntryContainer.TFrame")
        actions_container.grid(row=0, column=3, padx=5, pady=(0, 5), sticky='ew')
        # --------------- COL-4  ROW-2 -------------- [Replace Next , Replace All Btns, ]

        
        
        
        
        

        # ------------- FIND TOOLS FRAME ------------
        # self.find_entry = PlaceholderEntry(self.find_tools_frame, "Find", style="Find.TEntry")
        # self.find_entry.grid(row=0, column=0, sticky='ew', ipady=5, padx=(5,0))
        
        btn_aa = ttk.Checkbutton(self.find_tools_frame, text="Aa", width=3, style='Toggle.TButton', variable=self.match_case_var, command=lambda: self.on_match_case_toggled_callback(self.match_case_var.get()))
        btn_aa.grid(row=0, column=1, padx=(5,2))
        Tooltip(btn_aa, "Match Case (Alt+C)")

        btn_ww = ttk.Checkbutton(self.find_tools_frame, text="Ww", width=3, style='Toggle.TButton', variable=self.whole_word_var, command=lambda: self.on_whole_word_toggled_callback(self.whole_word_var.get()))
        btn_ww.grid(row=0, column=2, padx=2)
        Tooltip(btn_ww, "Match Whole Word (Alt+W)")

        btn_re = ttk.Checkbutton(self.find_tools_frame, text=".*", width=3, style='Toggle.TButton', variable=self.regex_var, command=lambda: self.on_regex_toggled_callback(self.regex_var.get()))
        btn_re.grid(row=0, column=3, padx=2)
        Tooltip(btn_re, "Use Regular Expression (Alt+R)")

        
      
        # ----------- REPLACE TOOLS FRAME -----------
        # self.replace_entry = PlaceholderEntry(self.replace_tools_frame, "Replace",  style="Find.TEntry")
        # self.replace_entry.grid(row=0, column=0, sticky='ew', ipady=5, padx=(5,0))
        
        # btn_repl = ttk.Button(self.replace_tools_frame, text="Re", width=3, style='Toggle.TButton', command=self.on_replace_callback)
        # btn_repl.grid(row=0, column=1, padx=(5,2))
        # Tooltip(btn_repl, "Replace")
        
        # btn_repl_all = ttk.Button(self.replace_tools_frame, text="RA", width=3, style='Toggle.TButton', command=self.on_replace_all_callback)
        # btn_repl_all.pack(padx=2, side=tk.LEFT)#grid(row=0, column=2, padx=2)
        # Tooltip(btn_repl_all, "Replace All")
        
        # Store replace actions container for toggling
        # self.replace_actions_container = self.replace_entry
        self.toggle_replace_row(force_state=False)

        
        
        
        
        
       
        # --- ACTION CONTROL AND RESULT VIEW FRAME --- 
 
        
        btn_f1 = ttk.Button(actions_container, text="F<", width=3, style='Toggle.TButton', command=self.on_find_prev_callback)
        btn_f1.pack(side='left', padx=2)
        Tooltip(btn_f1, "Find Previous")
        
        btn_f2 = ttk.Button(actions_container, text="F>", width=3, style='Toggle.TButton', command=self.on_find_next_callback)
        btn_f2.pack(side='left', padx=2)
        Tooltip(btn_f2, "Find Next")
        
        btn_f5 = ttk.Button(actions_container, text="X", width=3, style='Toggle.TButton', command=self.hide_frame)
        btn_f5.pack(side='left', padx=2)
        Tooltip(btn_f5, "Close (Esc)")

        
        
        
               


        # ---------------- BIND KEYS ----------------
        # Find
        # self.find_entry.bind("<KeyRelease>", lambda e: self.on_find_changed_callback(self.find_entry.get()))
        # self.find_entry.bind("<Return>", lambda e: self.on_find_next_callback())
        # Replace
        self.replace_entry.bind("<Return>",  lambda e: self.on_replace_callback())
        

        # --- Toggle Buttons (Checkbuttons) ---
        

        # -- Row 1 (Replace) --
    
        
    
        
        # --- Bind Enter ---
        

        # == Column 2: Action Buttons ==
        
        

        # self.message_label = ttk.Label(actions_container, text="", style="Message.TLabel")
        # self.message_label.pack(side='top', padx=(0, 5))
        
        # # --- NEW LAYOUT: Sub-frames for buttons ---
        # find_actions = ttk.Frame(actions_container, style="Actions.TFrame")
        # find_actions.pack(side='top')
        
        # replace_actions = ttk.Frame(actions_container, style="Actions.TFrame")
        # replace_actions.pack(side='top', pady=(2,0))
        
        
        
        
        
        
        

        # -- Find Actions --
        # btn_f1 = ttk.Button(find_actions, text="F<", width=3, 
        #                     style='Find.TButton', command=self.on_find_prev_callback)
        # btn_f1.pack(side='left', padx=2)
        # Tooltip(btn_f1, "Find Previous")
        
        # btn_f2 = ttk.Button(find_actions, text="F>", width=3, 
        #                     style='Find.TButton', command=self.on_find_next_callback)
        # btn_f2.pack(side='left', padx=2)
        # Tooltip(btn_f2, "Find Next")

        # btn_f5 = ttk.Button(find_actions, text="X", width=3, 
        #                     style='Find.TButton', command=self.hide_frame)
        # btn_f5.pack(side='left', padx=2)
        # Tooltip(btn_f5, "Close (Esc)")
        
        
        
        

        # # -- Replace Actions (now in the same column) --
        # btn_repl = ttk.Button(replace_actions, text="Re", width=3, 
        #                       style='Find.TButton', command=self.on_replace_callback)
        # btn_repl.pack(side='left', padx=2)
        # Tooltip(btn_repl, "Replace")

        # btn_repl_all = ttk.Button(replace_actions, text="RA", width=3, 
        #                           style='Find.TButton', command=self.on_replace_all_callback)
        # btn_repl_all.pack(side='left', padx=2)
        # Tooltip(btn_repl_all, "Replace All")
        
        # # --- Store replace actions container for toggling ---
        # self.replace_actions_container = replace_actions
        
        # self.toggle_replace_row(force_state=False)
        
        
        
        
        
        

    def toggle_replace_row(self, force_state: Optional[bool] = None) -> None:
        """Shows or hides the 'Replace' row widgets."""
        if force_state is not None:
            self.replace_visible.set(force_state)
        else:
            self.replace_visible.set(not self.replace_visible.get())

        if self.replace_visible.get():
            self.replace_tools_frame.grid(row=1, column=1, padx=5, pady=(0, 5), sticky='ew')
            self.replace_actions_container.pack(side='top', pady=(2,0))
            self.toggle_btn.config(text="v")
        else:
            self.replace_tools_frame.grid_remove()
            self.replace_actions_container.pack_forget()
            self.toggle_btn.config(text="❯")

    def show_find(self, event: Optional[tk.Event] = None) -> None:
        if not self.master_frame:
            self._init_layout()
        self.master_frame.place(rely=0.0, relx=1.0, x=-10, y=10, anchor='ne')
        self.master_frame.lift()
        self.toggle_replace_row(force_state=False)
        self.find_entry.focus_set()
        self.find_entry.select_range(0, 'end')

    def show_replace(self, event: Optional[tk.Event] = None) -> None:
        if not self.master_frame:
            self._init_layout()
        self.master_frame.place(rely=0.0, relx=1.0, x=-10, y=10, anchor='ne')
        self.master_frame.lift()
        self.toggle_replace_row(force_state=True)
        self.replace_entry.focus_set()
        self.replace_entry.select_range(0, 'end')

    def hide_frame(self, event: Optional[tk.Event] = None) -> None:
        if self.master_frame:
            self.master_frame.place_forget()
        self.main_text.focus_set()

# --- Main Application Execution ---
if __name__ == "__main__":
    
    root = tk.Tk()
    root.geometry("800x600")

    # --- 1. Define All Callback Functions ---
    # These functions just print, demonstrating the decoupling.
    
    def handle_find_change(text: str):
        print(f"Find text changed to: '{text}'")
        # In a real app, you would start searching here.
        
    def handle_match_case(is_active: bool):
        print(f"Match Case toggled to: {is_active}")
        
    def handle_whole_word(is_active: bool):
        print(f"Match Whole Word toggled to: {is_active}")
        
    def handle_regex(is_active: bool):
        print(f"Regex toggled to: {is_active}")
        
    def handle_find_next():
        print("--- ACTION: Find Next ---")
        
    def handle_find_prev():
        print("--- ACTION: Find Previous ---")
        
    def handle_replace():
        print("--- ACTION: Replace ---")
        
    def handle_replace_all():
        print("--- ACTION: Replace All ---")

    # --- 2. Instantiate the Class, Passing Callbacks ---
    app = FindReplaceDemo(
        root,
        on_find_changed=handle_find_change,
        on_match_case_toggled=handle_match_case,
        on_whole_word_toggled=handle_whole_word,
        on_regex_toggled=handle_regex,
        on_find_next=handle_find_next,
        on_find_prev=handle_find_prev,
        on_replace=handle_replace,
        on_replace_all=handle_replace_all
    )
    
    root.mainloop()