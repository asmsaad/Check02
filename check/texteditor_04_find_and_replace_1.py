import tkinter as tk
from tkinter import font
from tkinter import ttk

# --- Custom Class for Tooltips (Shows below widget) ---
class Tooltip:
    """
    Creates a tooltip for a given widget that appears below and right-aligned.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        # Schedule to show the tip after a delay
        self.schedule_id = self.widget.after(500, self.create_tip_window)

    def create_tip_window(self):
        if self.tip_window or not self.text:
            return
            
        # Get widget position
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx()
        y = y + self.widget.winfo_rooty() + self.widget.winfo_height()

        # Create a toplevel window
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True) # No title bar
        
        # Light theme for tooltip
        label = tk.Label(self.tip_window, text=self.text, justify='left',
                         background="#FFFFFF", foreground="#000000",
                         relief='solid', borderwidth=1,
                         font=("Segoe UI", 9))
        label.pack(ipadx=4, ipady=2)
        
        # Calculate position to be right-aligned
        self.tip_window.update_idletasks() # Ensure size is calculated
        tip_width = self.tip_window.winfo_width()
        widget_width = self.widget.winfo_width()
        
        # Align right edge of tip with right edge of widget
        final_x = x + widget_width - tip_width
        
        self.tip_window.wm_geometry(f"+{int(final_x)}+{int(y)}")

    def hide_tip(self, event=None):
        # Cancel any scheduled tip
        if hasattr(self, 'schedule_id'):
            self.widget.after_cancel(self.schedule_id)
            
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# --- Custom Class for Placeholder Entry ---
class PlaceholderEntry(tk.Entry):
    """
    An Entry widget that shows a placeholder text (watermark)
    when empty and not in focus.
    """
    def __init__(self, master, placeholder, **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.default_fg = self['fg']
        self.placeholder_color = 'grey'

        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)
        self.put_placeholder()

    def put_placeholder(self):
        if self.get() == '':
            self.config(fg=self.placeholder_color)
            self.insert(0, self.placeholder)

    def on_focus_in(self, event):
        if self.get() == self.placeholder and self['fg'] == self.placeholder_color:
            self.delete(0, tk.END)
            self.config(fg=self.default_fg)

    def on_focus_out(self, event):
        if self.get() == '':
            self.put_placeholder()

# --- Main Application ---
class FindReplaceDemo:
    def __init__(self, root):
        self.root = root
        self.root.title("Main Window")
        self.root.geometry("800x600")
        
        # Main text area (for context)
        tk.Label(self.root, text="Press Ctrl+F or Ctrl+H").pack(pady=20)
        self.main_text = tk.Text(self.root)
        self.main_text.pack(fill='both', expand=True)
        
        # --- State Variables ---
        self.find_frame = None # Will be created on demand
        self.replace_visible = tk.BooleanVar(value=True)
        
        # --- NEW: State variables for toggle buttons ---
        self.match_case_var = tk.BooleanVar(value=False)
        self.whole_word_var = tk.BooleanVar(value=False)
        self.regex_var = tk.BooleanVar(value=False)
        
        # Setup styles
        self.setup_styles()

        # --- Bindings ---
        self.root.bind('<Control-f>', self.show_find)
        self.root.bind('<Control-h>', self.show_replace)
        self.root.bind('<Escape>', self.hide_frame)
        
    def setup_styles(self):
        """Configures all the ttk styles for the find widget."""
        s = ttk.Style()
        
        # --- Define Button Layout (to ensure bordercolor works) ---
        # s.element_create('Find.TButton.border', 'from', 'default')
        # s.layout('Find.TButton',
        #          [('Find.TButton.border', {'sticky': 'nswe', 'border': '1', 'children':
        #              [('Button.padding', {'sticky': 'nswe', 'children':
        #                  [('Button.label', {'sticky': 'nswe'})]
        #              })]
        #          })]
        # )
        
        # s.layout('Inactive.TButton', s.layout('Find.TButton'))
        # s.layout('Active.TButton', s.layout('Find.TButton'))

        # --- Base Style (used for non-toggles) ---
        # s.configure('Find.TButton', 
        #             background="#F0F0F0", 
        #             foreground="#000000", 
        #             relief='flat', 
        #             borderwidth=1,
        #             bordercolor="#FF0000")
        s.map('Find.TButton',
            # background=[('active', '#007ACC'), ('pressed', '#007ACC')],
            foreground=[('active', '#FFFFFF'), ('pressed', '#FFFFFF')],
            # bordercolor=[('active', '#007ACC'), ('pressed', '#007ACC')],
            # relief=[('pressed', 'flat'), ('!pressed', 'flat')]
        )
        
        
        
        
        # --- NEW: Style for INACTIVE toggle buttons ---
        # s.configure('Inactive.TButton',
        #             # background="#F0F0F0",
        #             # foreground="grey",  # Inactive text color
        #             # relief='flat',
        #             borderwidth=1,
        #             bordercolor="#FF0000")
        s.map('Inactive.TButton',
            # background=[('active', '#007ACC'), ('pressed', '#007ACC')],
            foreground=[('active', '#FFFFFF'), ('pressed', '#FFFFFF')],
            # bordercolor=[('active', '#007ACC'), ('pressed', '#007ACC')]
        )
        
        # --- NEW: Style for ACTIVE toggle buttons ---
        # s.configure('Active.TButton',
        #             # background="#E0E0E0",  # Slightly different bg for "on"
        #             # foreground="#000000",  # Active text color
        #             # relief='flat',
        #             borderwidth=1,
        #             bordercolor="#FF0751") # Active border
        s.map('Active.TButton',
            # background=[('active', '#007ACC'), ('pressed', '#007ACC')],
            foreground=[('active', '#FFFFFF'), ('pressed', '#FFFFFF')],
            # bordercolor=[('active', '#007ACC'), ('pressed', '#007ACC')]
        )


    def create_find_frame(self):
        if self.find_frame:
            return
            
        # Light theme background and border
        self.find_frame = tk.Frame(self.root, bg="#F3F3F3",
                                   highlightbackground="#CCCCCC", highlightthickness=1)
        
        # --- Configure Grid ---
        self.find_frame.columnconfigure(0, weight=0) # Toggle button
        self.find_frame.columnconfigure(1, weight=1) # Entries
        self.find_frame.columnconfigure(2, weight=0) # Actions
        
        # == Column 0: Toggle Button ==
        self.toggle_btn = ttk.Button(self.find_frame, text=">", width=3,
                                     command=self.toggle_replace_row, 
                                    #  style='Find.TButton'
                                     )
        self.toggle_btn.grid(row=0, column=0, rowspan=2, padx=5, pady=5, sticky='ns')

        # == Column 1: Find and Replace Entries ==
        
        # -- Row 0 (Find) --
        find_container = tk.Frame(self.find_frame, bg="#F00707")
        find_container.grid(row=0, column=1, padx=5, pady=(5, 5), sticky='ew')
        find_container.columnconfigure(0, weight=1)
        
        entry_font = ('Segoe UI', 10)
        self.find_entry = PlaceholderEntry(find_container, "Find",
                                           bg="#FFFFFF", fg="#000000",
                                           insertbackground="#000000", relief='flat',
                                        #    highlightcolor="#007ACC", highlightthickness=0,
                                           borderwidth=0,bd=0,
                                           highlightbackground="#CCCCCC", font=entry_font)
        self.find_entry.grid(row=0, column=0, sticky='ew', ipady=5)
        
        # --- NEW: Bind key release and enter key ---
        self.find_entry.bind("<KeyRelease>", self.on_find_key_release)
        self.find_entry.bind("<Return>", self.on_find_next)
        
        # --- MODIFIED: Store buttons and link to toggle functions ---
        self.btn_aa = ttk.Button(find_container, text="Aa", width=3,
                                 style='Inactive.TButton', 
                                 command=self.on_toggle_match_case)
        self.btn_aa.grid(row=0, column=1, padx=(5,2))
        Tooltip(self.btn_aa, "Match Case (Alt+C)")

        self.btn_ww = ttk.Button(find_container, text="Ww", width=3,
                                 style='Inactive.TButton', 
                                 command=self.on_toggle_whole_word)
        self.btn_ww.grid(row=0, column=2, padx=2)
        Tooltip(self.btn_ww, "Match Whole Word (Alt+W)")
        
        self.btn_re = ttk.Button(find_container, text=".*", width=3,
                                 style='Inactive.TButton', 
                                 command=self.on_toggle_regex)
        self.btn_re.grid(row=0, column=3, padx=2)
        Tooltip(self.btn_re, "Use Regular Expression (Alt+R)")

        # -- Row 1 (Replace) --
        self.replace_container = tk.Frame(self.find_frame, bg="#F00707")
        self.replace_container.grid(row=1, column=1, padx=5, pady=(5, 5), sticky='ew')
        self.replace_container.columnconfigure(0, weight=1)
        
        self.replace_entry = PlaceholderEntry(self.replace_container, "Replace",
                                              bg="#FFFFFF", fg="#000000",
                                              insertbackground="#000000", relief='flat',
                                            #   highlightcolor="#007ACC", highlightthickness=0,
                                              borderwidth=0,bd=0,
                                              highlightbackground="#CCCCCC", font=entry_font)
        self.replace_entry.grid(row=0, column=0, sticky='ew', ipady=5)
        
        # --- NEW: Bind enter key ---
        self.replace_entry.bind("<Return>", self.on_replace)
        
        # --- MODIFIED: Link buttons to functions ---
        btn_repl = ttk.Button(self.replace_container, text="Re", width=3,
                            #   style='Find.TButton', 
                              command=self.on_replace)
        btn_repl.grid(row=0, column=1, padx=(5, 2))
        Tooltip(btn_repl, "Replace")

        btn_repl_all = ttk.Button(self.replace_container, text="RA", width=3,
                                #   style='Find.TButton', 
                                  command=self.on_replace_all)
        btn_repl_all.grid(row=0, column=2, padx=2)
        Tooltip(btn_repl_all, "Replace All")


        # == Column 2: Action Buttons ==
        
        # -- Row 0 (Find Actions) --
        find_actions_container = tk.Frame(self.find_frame, bg="#F3F3F3")
        find_actions_container.grid(row=0, column=2, padx=5, pady=(5, 2), sticky='e')

        self.message_label = tk.Label(find_actions_container, text="No results",
                                      bg="#F3F3F3", fg="#555555")
        self.message_label.pack(side='left', padx=(0, 5))
        
        # --- MODIFIED: Link buttons to functions ---
        btn_f1 = ttk.Button(find_actions_container, text="↑", width=3,
                            # style='Find.TButton', 
                            command=self.on_find_previous)
        btn_f1.pack(side='left', padx=2)
        Tooltip(btn_f1, "Find Previous")
        
        btn_f2 = ttk.Button(find_actions_container, text="↓", width=3,
                            # style='Find.TButton', 
                            command=self.on_find_next)
        btn_f2.pack(side='left', padx=2)
        Tooltip(btn_f2, "Find Next")
        
        # --- Other buttons remain for layout ---
        btn_f3 = ttk.Button(find_actions_container, text="S1", width=3, 
                            # style='Find.TButton'
                            )
        btn_f3.pack(side='left', padx=(15,2))
        Tooltip(btn_f3, "Placeholder 1")
        btn_f4 = ttk.Button(find_actions_container, text="S2", width=3,
                            # style='Find.TButton'
                            )
        btn_f4.pack(side='left', padx=2)
        Tooltip(btn_f4, "Placeholder 2")
        btn_f5 = ttk.Button(find_actions_container, text="S3", width=3,
                            # style='Find.TButton'
                            )
        btn_f5.pack(side='left', padx=2)
        Tooltip(btn_f5, "Placeholder 3")

        # Set initial state
        self.toggle_replace_row(force_state=False) # Start collapsed

    def toggle_replace_row(self, force_state=None):
        if force_state is not None:
            self.replace_visible.set(force_state)
        else:
            self.replace_visible.set(not self.replace_visible.get())

        if self.replace_visible.get():
            self.replace_container.grid(row=1, column=1, padx=5, pady=(0, 5), sticky='ew')
            self.toggle_btn.config(text="v")
        else:
            self.replace_container.grid_remove()
            self.toggle_btn.config(text=">")

    def show_find(self, event=None):
        if not self.find_frame:
            self.create_find_frame()
            
        self.find_frame.place(rely=0.0, relx=1.0, x=-10, y=10, anchor='ne')
        self.find_frame.lift()
        
        self.toggle_replace_row(force_state=False)
        self.find_entry.focus_set()
        self.find_entry.select_range(0, 'end')

    def show_replace(self, event=None):
        if not self.find_frame:
            self.create_find_frame()

        self.find_frame.place(rely=0.0, relx=1.0, x=-10, y=10, anchor='ne')
        self.find_frame.lift()

        self.toggle_replace_row(force_state=True)
        self.replace_entry.focus_set()
        self.replace_entry.select_range(0, 'end')

    def hide_frame(self, event=None):
        if self.find_frame:
            self.find_frame.place_forget()
        self.main_text.focus_set()

    # --- NEW: Function Implementations ---

    def on_find_key_release(self, event):
        """Called every time a key is pressed in the Find Entry."""
        # Don't trigger on 'Enter', as that's handled separately
        if event.keysym == "Return":
            return
        print("this test is for serce for")
        # You would typically start your search logic here
        # E.g., self.find_all()

    def _update_toggle_button_style(self, button, variable):
        """Helper to update a toggle button's style based on its variable."""
        if variable.get():
            button.config(style='Active.TButton')
        else:
            button.config(style='Inactive.TButton')

    def on_toggle_match_case(self):
        """Called when the 'Match Case' button is clicked."""
        new_state = not self.match_case_var.get()
        self.match_case_var.set(new_state)
        print(f"Match Case: {new_state}")
        self._update_toggle_button_style(self.btn_aa, self.match_case_var)

    def on_toggle_whole_word(self):
        """Called when the 'Match Whole Word' button is clicked."""
        new_state = not self.whole_word_var.get()
        self.whole_word_var.set(new_state)
        print(f"Match Whole Word: {new_state}")
        self._update_toggle_button_style(self.btn_ww, self.whole_word_var)

    def on_toggle_regex(self):
        """Called when the 'Use Regular Expression' button is clicked."""
        new_state = not self.regex_var.get()
        self.regex_var.set(new_state)
        print(f"Regular Expression: {new_state}")
        self._update_toggle_button_style(self.btn_re, self.regex_var)

    def on_find_next(self, event=None):
        """Called by Find Next button or Enter in Find Entry."""
        print("Find Next function called")
        # Add find_next logic here
        return "break" # Prevents 'ding' sound if called by event

    def on_find_previous(self):
        """Called by Find Previous button."""
        print("Find Previous function called")
        # Add find_previous logic here
        
    def on_replace(self, event=None):
        """Called by Replace button or Enter in Replace Entry."""
        print("Replace function called")
        # Add replace_one logic here
        return "break" # Prevents 'ding' sound if called by event

    def on_replace_all(self):
        """Called by Replace All button."""
        print("Replace All function called")
        # Add replace_all logic here

# --- Main Application Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = FindReplaceDemo(root)
    root.mainloop()