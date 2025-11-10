import tkinter as tk
from tkinter import font
import re # Import regular expressions for search

class ProTextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Pro Text Editor")
        self.root.geometry("900x700") # Made window larger

        # --- Text State Variables ---
        self.wrap_var = tk.BooleanVar(value=True)
        self.show_lines_var = tk.BooleanVar(value=True)
        
        # --- Clipboard Variables ---
        self.clipboard_history = []
        self.history_window = None 

        # --- Find/Replace State Variables ---
        self.find_var = tk.StringVar()
        self.replace_var = tk.StringVar()
        self.match_case_var = tk.BooleanVar(value=False)
        self.wrap_search_var = tk.BooleanVar(value=True)
        self.whole_word_var = tk.BooleanVar(value=False)
        self.search_mode_var = tk.StringVar(value="Normal") # Modes: "Normal", "RegEx"
        self.highlight_all_var = tk.BooleanVar(value=True) 
        
        # --- Search Tracking Variables ---
        self.search_results = [] # Stores (start, end) tuples of matches
        self.current_search_index = -1 # Tracks which match we're on
        self.auto_search_id = None # For debouncing auto-search

        # --- Create Main UI Components ---
        self.create_toolbar()
        self.create_find_toolbar() 
        self.create_menu()
        
        # --- Main Editor & Status Bar ---
        self.create_editor_area()
        self.create_status_bar() 

        # --- Configure Initial State ---
        self.set_edit_mode() 
        self.toggle_wrap()      
        self.update_line_numbers()
        self.update_cursor_pos() 
        self.highlight_current_line()
        
        # --- Bind Events ---
        self.text_widget.bind("<<Modified>>", self.on_text_modified)
        self.text_widget.bind("<MouseWheel>", self.on_scroll)
        self.text_widget.bind("<Button-4>", self.on_scroll)
        self.text_widget.bind("<Button-5>", self.on_scroll)
        
        self.text_widget.bind("<KeyRelease>", self.on_key_or_click)
        self.text_widget.bind("<ButtonRelease-1>", self.on_key_or_click)
        
        # Auto-search when typing in find box
        self.find_var.trace_add("write", self.schedule_auto_search)
        self.highlight_all_var.trace_add("write", self.on_highlight_toggle)


    def create_toolbar(self):
        """Creates the top toolbar with action buttons."""
        self.toolbar_frame = tk.Frame(self.root, relief=tk.RAISED, bd=2)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.edit_btn = tk.Button(self.toolbar_frame, text="Edit Mode", command=self.set_edit_mode)
        self.edit_btn.pack(side=tk.LEFT, padx=2, pady=5)
        self.readonly_btn = tk.Button(self.toolbar_frame, text="Read-Only Mode", command=self.set_readonly_mode)
        self.readonly_btn.pack(side=tk.LEFT, padx=2, pady=5)
        self.undo_btn = tk.Button(self.toolbar_frame, text="Undo", command=self.undo_text)
        self.undo_btn.pack(side=tk.LEFT, padx=2, pady=5)
        self.redo_btn = tk.Button(self.toolbar_frame, text="Redo", command=self.redo_text)
        self.redo_btn.pack(side=tk.LEFT, padx=2, pady=5)
        self.cut_btn = tk.Button(self.toolbar_frame, text="Cut", command=self.cut_text)
        self.cut_btn.pack(side=tk.LEFT, padx=2, pady=5)
        self.copy_btn = tk.Button(self.toolbar_frame, text="Copy", command=self.copy_text)
        self.copy_btn.pack(side=tk.LEFT, padx=2, pady=5)
        self.paste_btn = tk.Button(self.toolbar_frame, text="Paste", command=self.paste_text)
        self.paste_btn.pack(side=tk.LEFT, padx=2, pady=5)
        self.clip_history_btn = tk.Button(self.toolbar_frame, text="Clipboard", command=self.show_clipboard_history)
        self.clip_history_btn.pack(side=tk.LEFT, padx=2, pady=5)
        self.clear_clip_btn = tk.Button(self.toolbar_frame, text="Clear Clipboard", command=self.clear_clipboard)
        self.clear_clip_btn.pack(side=tk.LEFT, padx=2, pady=5)


    def create_find_toolbar(self):
        """MODIFIED: Creates the Find/Replace toolbar without Find All button."""
        self.find_frame = tk.Frame(self.root, bd=1, relief=tk.SUNKEN)
        self.find_frame.pack(side=tk.TOP, fill=tk.X, padx=2, pady=1)

        # --- Column 0: Labels ---
        tk.Label(self.find_frame, text="Find:").grid(row=0, column=0, padx=5, sticky='w')
        tk.Label(self.find_frame, text="Replace:").grid(row=1, column=0, padx=5, sticky='w')

        # --- Column 1: Entries ---
        find_entry = tk.Entry(self.find_frame, textvariable=self.find_var, width=30)
        find_entry.grid(row=0, column=1, padx=5, pady=2, sticky='we')
        
        # --- Store reference to replace_entry ---
        self.replace_entry_widget = tk.Entry(self.find_frame, textvariable=self.replace_var, width=30)
        self.replace_entry_widget.grid(row=1, column=1, padx=5, pady=2, sticky='we')
        
        # --- Bind Enter keys ---
        find_entry.bind("<Return>", lambda e: self.find_next())  # Enter in find = find next
        self.replace_entry_widget.bind("<Return>", self.on_replace_enter) 

        # --- Column 2: Find Buttons ---
        find_btn_frame = tk.Frame(self.find_frame)
        find_btn_frame.grid(row=0, column=2, padx=5, sticky='we')
        tk.Button(find_btn_frame, text="Find Next", command=self.find_next).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(find_btn_frame, text="Find Prev", command=self.find_previous).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # --- REMOVED: Find All Button ---
        
        # --- Column 3: Replace Buttons ---
        replace_btn_frame = tk.Frame(self.find_frame)
        replace_btn_frame.grid(row=1, column=2, columnspan=2, padx=5, pady=2, sticky='we')
        tk.Button(replace_btn_frame, text="Replace", command=self.replace_one).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(replace_btn_frame, text="Replace Prev", command=self.replace_and_find_previous).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Button(replace_btn_frame, text="Replace All", command=self.replace_all).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)


        # --- Column 4: Checkboxes ---
        options_frame = tk.Frame(self.find_frame)
        options_frame.grid(row=0, column=4, rowspan=2, padx=5, sticky='ns')
        
        tk.Checkbutton(options_frame, text="Match Case", variable=self.match_case_var, command=self.invalidate_search).pack(anchor='w')
        tk.Checkbutton(options_frame, text="Wrap Around", variable=self.wrap_search_var).pack(anchor='w')
        tk.Checkbutton(options_frame, text="Match Whole Word", variable=self.whole_word_var, command=self.invalidate_search).pack(anchor='w')
        tk.Checkbutton(options_frame, text="Highlight All", variable=self.highlight_all_var).pack(anchor='w')


        # --- Column 5: Mode Radios ---
        mode_frame = tk.Frame(self.find_frame)
        mode_frame.grid(row=0, column=5, rowspan=2, padx=5, sticky='ns')
        tk.Label(mode_frame, text="Mode:").pack(anchor='w')
        tk.Radiobutton(mode_frame, text="Normal", variable=self.search_mode_var, value="Normal", command=self.invalidate_search).pack(anchor='w')
        tk.Radiobutton(mode_frame, text="RegEx", variable=self.search_mode_var, value="RegEx", command=self.invalidate_search).pack(anchor='w')
        
        # Allow column 1 (entries) to stretch
        self.find_frame.grid_columnconfigure(1, weight=1)

    def create_menu(self):
        """Creates the main application menu bar."""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        self.pref_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Preferences", menu=self.pref_menu)
        self.pref_menu.add_checkbutton(label="Wrap Lines", variable=self.wrap_var, command=self.toggle_wrap)
        self.pref_menu.add_checkbutton(label="Show Line Numbers", variable=self.show_lines_var, command=self.toggle_line_numbers)

    def create_editor_area(self):
        """Creates the frame holding the line numbers and text widget."""
        self.editor_frame = tk.Frame(self.root)
        self.editor_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True) 

        self.scrollbar = tk.Scrollbar(self.editor_frame, orient=tk.VERTICAL)
        
        self.line_numbers = tk.Text(
            self.editor_frame, width=4, padx=5, bd=0, fg="#6b6b6b",
            state=tk.DISABLED, wrap=tk.NONE, yscrollcommand=self.on_line_scroll
        )
        self.line_numbers.config(bg="#f0f0f0") 
        self.line_numbers.tag_configure("odd", background="#e0e0e0")
        self.line_numbers.tag_configure("even", background="#f0f0e0")
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        self.text_widget = tk.Text(
            self.editor_frame, wrap=tk.WORD, undo=True,
            yscrollcommand=self.on_text_scroll
        )
        
        self.text_widget.tag_configure("match", background="yellow", foreground="black")
        self.text_widget.tag_configure("current_match", background="orange", foreground="black")
        
        self.text_widget.tag_configure("current_line", background="#e8f2fe") 
        self.text_widget.tag_lower("current_line") 
        
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar.config(command=self.on_scrollbar)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        default_font = font.Font(family="Courier New", size=11)
        default_font_bold = font.Font(family="Courier New", size=11, weight="bold") 
        
        self.text_widget.config(font=default_font)
        self.line_numbers.config(font=default_font)
        
        self.line_numbers.tag_configure("active_line", background="#e8f2fe", font=default_font_bold, foreground="black")

        
        sample_text = ('''"This is a professional Tkinter text editor.\n\n"
                       "New Features:\n"
                       "* Undo / Redo buttons\n"
                       * "Alternating line number colors\n"
                       * "Clipboard History (button on toolbar)\n\n"
                       "Try cutting and copying different snippets of \n"
                       "text, then click the 'Clipboard' button to \n"
                       "see the history and paste from it.\n"
                       "---
                       NEW: Find and Replace!\n"
                       "Try searching for 'text' or 'button'.\n"
                       "Use 'Find Next' to cycle through them.\n"
                       "The status bar at the bottom will show your cursor position and search results."
                       ''')
        
        self.text_widget.insert(1.0, sample_text)
        self.text_widget.edit_modified(False)

    def create_status_bar(self):
        """Creates the bottom status ribbon."""
        self.status_bar = tk.Frame(self.root, relief=tk.SUNKEN, bd=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_message_label = tk.Label(self.status_bar, text="", anchor='w')
        self.status_message_label.pack(side=tk.LEFT, padx=5)

        self.cursor_pos_label = tk.Label(self.status_bar, text="Ln 1, Col 1", anchor='e')
        self.cursor_pos_label.pack(side=tk.RIGHT, padx=5)

    # --- NEW: Auto-search with debouncing ---
    def schedule_auto_search(self, *args):
        """Schedule auto-search with debouncing to prevent lag."""
        if self.auto_search_id:
            self.root.after_cancel(self.auto_search_id)
        self.auto_search_id = self.root.after(300, self.auto_search)
        
    def auto_search(self):
        """Perform search without moving cursor."""
        if self.find_var.get():
            # Store current cursor position
            current_pos = self.text_widget.index(tk.INSERT)
            
            # Perform search and highlight
            self.find_all(keep_cursor=True)
            
            # Restore cursor position
            self.text_widget.mark_set(tk.INSERT, current_pos)
            self.highlight_current_line()

    # --- Status Bar and Event Handlers ---

    def set_status_message(self, msg):
        self.status_message_label.config(text=msg)

    def clear_status_message(self):
        self.status_message_label.config(text="")

    def update_cursor_pos(self, event=None):
        line, col = self.text_widget.index(tk.INSERT).split('.')
        self.cursor_pos_label.config(text=f"Ln {line}, Col {int(col) + 1}")
        
    def on_key_or_click(self, event=None):
        self.update_cursor_pos()
        self.highlight_current_line()
            
        if event and event.type == tk.EventType.KeyRelease:
            if "matches found" in self.status_message_label.cget("text"):
                 self.clear_status_message()
                 
    def highlight_current_line(self, event=None):
        """Highlights the line where the cursor is in both widgets."""
        self.text_widget.tag_remove("current_line", "1.0", tk.END)
        
        self.line_numbers.config(state=tk.NORMAL)
        self.line_numbers.tag_remove("active_line", "1.0", tk.END)
        self.line_numbers.config(state=tk.DISABLED)

        try:
            line_start = self.text_widget.index(f"{tk.INSERT} linestart")
            line_end = self.text_widget.index(f"{tk.INSERT} lineend +1c") 
            self.text_widget.tag_add("current_line", line_start, line_end)

            line_num_str = line_start.split('.')[0] 
            
            self.line_numbers.config(state=tk.NORMAL)
            self.line_numbers.tag_add("active_line", f"{line_num_str}.0", f"{line_num_str}.end")
            self.line_numbers.config(state=tk.DISABLED)
            
        except tk.TclError:
            pass 
            
    # --- Search Invalidation ---
    
    def invalidate_search(self, *args):
        self.search_results = []
        self.current_search_index = -1
        self.clear_highlights()
        
    def on_highlight_toggle(self, *args):
        """Applies or clears highlights when the toggle is clicked."""
        if self.highlight_all_var.get():
            self.find_all(keep_cursor=True)
        else:
            self.clear_highlights()
            
    def on_replace_enter(self, event=None):
        """Handles pressing Enter in the replace box."""
        if self.find_var.get() and self.replace_var.get():
            self.replace_one()
        # Refocus the entry widget without selecting all
        self.replace_entry_widget.focus_set()
        self.replace_entry_widget.selection_clear()
        self.replace_entry_widget.icursor(tk.END)
        return "break" # Prevents the default "ding" sound
        
    def clear_highlights(self):
        self.text_widget.tag_remove("match", "1.0", tk.END)
        self.text_widget.tag_remove("current_match", "1.0", tk.END)

    # --- Find and Replace Core Logic ---

    def _perform_search(self, find_term, start_index="1.0"):
        if not find_term:
            return []

        nocase = not self.match_case_var.get()
        regexp = self.search_mode_var.get() == "RegEx"
        whole_word = self.whole_word_var.get()
        
        if whole_word and not regexp:
            find_term = r"\b" + re.escape(find_term) + r"\b"
            regexp = True
        
        results = []
        current_pos = start_index
        while True:
            count_var = tk.StringVar()
            start_pos = self.text_widget.search(
                find_term,
                current_pos,
                stopindex=tk.END,
                nocase=nocase,
                regexp=regexp,
                count=count_var
            )
            
            if not start_pos:
                break 
            
            match_length = int(count_var.get())
            if match_length == 0:
                break 

            end_pos = f"{start_pos} + {match_length}c"
            results.append((start_pos, end_pos))
            
            current_pos = end_pos
            
        return results

    def find_all(self, keep_cursor=False):
        """
        Finds all matches, updates count, and conditionally highlights.
        If keep_cursor is True, doesn't move cursor.
        """
        self.clear_highlights()
        find_term = self.find_var.get()
        
        if not find_term:
            self.set_status_message("")
            self.search_results = []
            self.current_search_index = -1
            return

        # 1. Always perform the search to get results
        self.search_results = self._perform_search(find_term)
        
        if not self.search_results:
            self.set_status_message("No matches found.")
            return

        # 2. Always update the status message with the count
        self.set_status_message(f"{len(self.search_results)} matches found.")
        
        # 3. Conditionally apply highlights
        if self.highlight_all_var.get():
            for start, end in self.search_results:
                self.text_widget.tag_add("match", start, end)
            
        self.current_search_index = -1 # Reset index

    def find_next(self):
        """Finds and highlights the next match."""
        if not self.search_results:
            # If no search results, perform search first
            self.find_all(keep_cursor=True)
            if not self.search_results:
                return 

        # Clear old "current" tag but preserve yellow highlights
        if self.current_search_index > -1:
            try:
                old_start, old_end = self.search_results[self.current_search_index]
                self.text_widget.tag_remove("current_match", old_start, old_end)
                # Re-apply the yellow tag if highlighting is on
                if self.highlight_all_var.get():
                    self.text_widget.tag_add("match", old_start, old_end)
            except (IndexError, tk.TclError):
                pass
            
        self.current_search_index += 1
        
        if self.current_search_index >= len(self.search_results):
            if self.wrap_search_var.get():
                self.current_search_index = 0
                self.set_status_message("Wrapped search to top.")
            else:
                self.current_search_index = len(self.search_results) - 1
                self.set_status_message("End of search reached.")
                return
        
        start, end = self.search_results[self.current_search_index]
        # Remove yellow tag before adding orange to avoid overlap
        if self.highlight_all_var.get():
            self.text_widget.tag_remove("match", start, end)
        self.text_widget.tag_add("current_match", start, end)
        
        self.text_widget.see(start)
        self.text_widget.tag_add(tk.SEL, start, end)
        self.text_widget.focus_set()
        
        self.highlight_current_line() 
        self.set_status_message(f"Match {self.current_search_index + 1} of {len(self.search_results)}")

    def find_previous(self):
        """Finds and highlights the previous match."""
        if not self.search_results:
            self.find_all(keep_cursor=True)
            if not self.search_results:
                return 

        # Clear old "current" tag but preserve yellow highlights
        if self.current_search_index > -1:
            try:
                old_start, old_end = self.search_results[self.current_search_index]
                self.text_widget.tag_remove("current_match", old_start, old_end)
                # Re-apply the yellow tag if highlighting is on
                if self.highlight_all_var.get():
                    self.text_widget.tag_add("match", old_start, old_end)
            except (IndexError, tk.TclError):
                pass
            
        self.current_search_index -= 1
        
        if self.current_search_index < 0:
            if self.wrap_search_var.get():
                self.current_search_index = len(self.search_results) - 1
                self.set_status_message("Wrapped search to end.")
            else:
                self.current_search_index = 0
                self.set_status_message("Start of search reached.")
                return

        start, end = self.search_results[self.current_search_index]
        # Remove yellow tag before adding orange to avoid overlap
        if self.highlight_all_var.get():
            self.text_widget.tag_remove("match", start, end)
        self.text_widget.tag_add("current_match", start, end)
        
        self.text_widget.see(start)
        self.text_widget.tag_add(tk.SEL, start, end)
        self.text_widget.focus_set()
        
        self.highlight_current_line() 
        self.set_status_message(f"Match {self.current_search_index + 1} of {len(self.search_results)}")

    def replace_one(self):
        """Replaces the currently selected match and finds the next one."""
        find_term = self.find_var.get()
        replace_term = self.replace_var.get()
        
        if not find_term or not replace_term:
            self.set_status_message("Need both find and replace terms.")
            return
            
        # If we have a current match selected, replace it
        if self.current_search_index >= 0 and self.search_results:
            try:
                start, end = self.search_results[self.current_search_index]
                
                # Replace the text
                self.text_widget.delete(start, end)
                self.text_widget.insert(start, replace_term)
                
                # Invalidate search since text changed
                self.invalidate_search()
                self.find_all(keep_cursor=True)
                
                # If we still have matches, find the next one
                if self.search_results:
                    # Start from current position to find next match
                    current_pos = self.text_widget.index(tk.INSERT)
                    self.find_next_from_position(current_pos)
                else:
                    self.set_status_message("No more matches found.")
                    
            except (IndexError, tk.TclError) as e:
                self.set_status_message("Replace failed. Finding next...")
                self.find_next()
        else:
            # No current selection, find first match from cursor
            self.find_next_from_position(self.text_widget.index(tk.INSERT))

    def find_next_from_position(self, start_pos):
        """Find next match from given position."""
        if not self.search_results:
            return
            
        # Find first match at or after start position
        next_index = -1
        for i, (match_start, match_end) in enumerate(self.search_results):
            if self.text_widget.compare(match_start, ">=", start_pos):
                next_index = i
                break
                
        if next_index != -1:
            self.current_search_index = next_index - 1  # Will be incremented in find_next
            self.find_next()
        elif self.wrap_search_var.get():
            self.current_search_index = -1  # Wrap to beginning
            self.find_next()
        else:
            self.set_status_message("No more matches after current position.")

    def replace_and_find_previous(self):
        """Replaces the currently selected text and finds the PREVIOUS match."""
        find_term = self.find_var.get()
        replace_term = self.replace_var.get()
        
        if not find_term or not replace_term:
            self.set_status_message("Need both find and replace terms.")
            return
            
        if self.current_search_index >= 0 and self.search_results:
            try:
                start, end = self.search_results[self.current_search_index]
                
                # Replace the text
                self.text_widget.delete(start, end)
                self.text_widget.insert(start, replace_term)
                
                # Invalidate search since text changed
                self.invalidate_search()
                self.find_all(keep_cursor=True)
                
                # Find previous match
                if self.search_results:
                    current_pos = self.text_widget.index(tk.INSERT)
                    self.find_previous_from_position(current_pos)
                else:
                    self.set_status_message("No more matches found.")
                    
            except (IndexError, tk.TclError):
                self.set_status_message("Replace failed. Finding previous...")
                self.find_previous()
        else:
            self.find_previous()

    def find_previous_from_position(self, start_pos):
        """Find previous match from given position."""
        if not self.search_results:
            return
            
        # Find last match before start position
        prev_index = -1
        for i, (match_start, match_end) in reversed(list(enumerate(self.search_results))):
            if self.text_widget.compare(match_start, "<", start_pos):
                prev_index = i
                break
                
        if prev_index != -1:
            self.current_search_index = prev_index + 1  # Will be decremented in find_previous
            self.find_previous()
        elif self.wrap_search_var.get():
            self.current_search_index = len(self.search_results)  # Wrap to end
            self.find_previous()
        else:
            self.set_status_message("No more matches before current position.")

    def replace_all(self):
        """Replaces all occurrences in the document."""
        find_term = self.find_var.get()
        replace_term = self.replace_var.get()
        
        if not find_term:
            return
            
        matches = self._perform_search(find_term)
        
        if not matches:
            self.set_status_message("No matches found to replace.")
            return
            
        self.invalidate_search() 
        
        for start, end in reversed(matches):
            self.text_widget.delete(start, end)
            self.text_widget.insert(start, replace_term)
            
        self.set_status_message(f"{len(matches)} results replaced.")
        
        # Re-run find_all to update cache
        self.find_all(keep_cursor=True)

    # --- Standard Editor Functions ---
    
    def set_edit_mode(self):
        self.text_widget.config(state=tk.NORMAL)
        self.edit_btn.config(relief=tk.SUNKEN)
        self.readonly_btn.config(relief=tk.RAISED)

    def set_readonly_mode(self):
        self.text_widget.config(state=tk.DISABLED)
        self.edit_btn.config(relief=tk.RAISED)
        self.readonly_btn.config(relief=tk.SUNKEN)

    def undo_text(self):
        try:
            self.text_widget.edit_undo()
        except tk.TclError: pass 
        self.highlight_current_line() 

    def redo_text(self):
        try:
            self.text_widget.edit_redo()
        except tk.TclError: pass 
        self.highlight_current_line() 

    def _add_to_clipboard_history(self):
        try:
            selected_text = self.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text and selected_text not in self.clipboard_history:
                self.clipboard_history.insert(0, selected_text)
                if len(self.clipboard_history) > 10:
                    self.clipboard_history.pop()
        except tk.TclError: pass 

    def cut_text(self):
        self._add_to_clipboard_history() 
        self.text_widget.event_generate("<<Cut>>")
        self.highlight_current_line() 

    def copy_text(self):
        self._add_to_clipboard_history() 
        self.text_widget.event_generate("<<Copy>>")

    def paste_text(self):
        self.text_widget.event_generate("<<Paste>>")
        self.highlight_current_line() 
        
    def clear_clipboard(self):
        self.root.clipboard_clear()
        
    def show_clipboard_history(self):
        if self.history_window and self.history_window.winfo_exists():
            self.history_window.lift()
            return
        if not self.clipboard_history: return

        self.history_window = tk.Toplevel(self.root)
        self.history_window.title("Clipboard History")
        self.history_window.geometry("300x350")
        self.history_window.transient(self.root)
        self.history_window.grab_set()

        listbox = tk.Listbox(self.history_window, font=("Arial", 10))
        listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        for item in self.clipboard_history:
            preview = item.replace("\n", " ").strip()[:50] + "..."
            listbox.insert(tk.END, preview)
        
        listbox.bind("<<ListboxSelect>>", self.on_history_select)

    def on_history_select(self, event):
        widget = event.widget
        try:
            idx = widget.curselection()[0]
            text_to_paste = self.clipboard_history[idx]
            self.text_widget.insert(tk.INSERT, text_to_paste)
            self.highlight_current_line() 
            self.history_window.destroy()
            self.history_window = None
        except IndexError: pass 

    def toggle_wrap(self):
        self.text_widget.config(wrap=tk.WORD if self.wrap_var.get() else tk.NONE)
        self.update_line_numbers()

    def toggle_line_numbers(self):
        if self.show_lines_var.get():
            self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
            self.update_line_numbers()
        else:
            self.line_numbers.pack_forget()

    # --- FIXED: Line Number and Scrolling Logic for Wrap Lines ---

    def on_text_modified(self, event=None):
        self.invalidate_search() 
        self.update_line_numbers()
        self.text_widget.edit_modified(False)

    def update_line_numbers(self):
        """FIXED: Counts logical lines only, ignoring visual wrap lines."""
        if not self.show_lines_var.get(): 
            return
        
        # Get current cursor line before update
        current_line = self.text_widget.index(tk.INSERT).split('.')[0]
        
        # Get actual logical line count (ignores visual wraps)
        line_count = int(self.text_widget.index('end-1c').split('.')[0])

        self.line_numbers.config(state=tk.NORMAL)
        self.line_numbers.delete(1.0, tk.END)
        
        # Only insert numbers for logical lines
        for i in range(1, line_count + 1):
            tag = "odd" if i % 2 != 0 else "even"
            self.line_numbers.insert(tk.END, f"{i}\n", (tag,))
        
        # Highlight active line in line numbers
        try:
            self.line_numbers.tag_add("active_line", f"{current_line}.0", f"{current_line}.end")
        except tk.TclError:
            pass 
        
        self.line_numbers.config(state=tk.DISABLED)
        self.on_scroll() 

    def on_scroll(self, event=None):
        self.root.after(1, self.sync_scroll)

    def sync_scroll(self):
        scroll_pos = self.text_widget.yview()
        self.line_numbers.yview_moveto(scroll_pos[0])

    def on_text_scroll(self, first, last):
        self.scrollbar.set(first, last)
        self.line_numbers.yview_moveto(first)

    def on_line_scroll(self, first, last):
        self.scrollbar.set(first, last)
        self.text_widget.yview_moveto(first)
        
    def on_scrollbar(self, *args):
        self.text_widget.yview(*args)
        self.line_numbers.yview(*args)

# --- Main Application Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ProTextEditor(root)
    root.mainloop()