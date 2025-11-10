import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

class SettingsManager:
    """Manages application settings and preferences"""
    
    def __init__(self):
        self.settings_file = Path.home() / ".tk_text_editor_settings.json"
        self.default_settings = {
            "theme": "clam",
            "font_family": "Consolas",
            "font_size": 12,
            "tab_width": 4,
            "line_numbers": True,
            "word_wrap": False,
            "recent_files": [],
            "window_geometry": "800x600",
            "dark_mode": False
        }
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from JSON file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    settings = self.default_settings.copy()
                    settings.update(loaded)
                    return settings
        except Exception:
            pass
        return self.default_settings.copy()
    
    def save_settings(self):
        """Save settings to JSON file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass
    
    def get(self, key: str, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        """Set a setting value"""
        self.settings[key] = value
        self.save_settings()
    
    def add_recent_file(self, filepath: str):
        """Add file to recent files list"""
        recent_files = self.get('recent_files', [])
        if filepath in recent_files:
            recent_files.remove(filepath)
        recent_files.insert(0, filepath)
        recent_files = recent_files[:10]  # Keep only 10 most recent
        self.set('recent_files', recent_files)


class LineNumberPanel(ttk.Frame):
    """Displays line numbers for the text editor"""
    
    def __init__(self, parent, text_widget):
        super().__init__(parent)
        self.text_widget = text_widget
        self.line_numbers = tk.Text(
            self, width=5, padx=3, takefocus=0, border=0,
            background='lightgray', foreground='darkblue',
            state='disabled', wrap='none'
        )
        self.line_numbers.pack(side='left', fill='y')
        
        # Bind to text changes and scrolling
        self.text_widget.bind('<<Modified>>', self._on_text_change)
        self.text_widget.bind('<Configure>', self._on_text_change)
        self.line_numbers.bind('<MouseWheel>', self._sync_scroll)
        
    def _on_text_change(self, event=None):
        """Update line numbers when text changes"""
        self.update_line_numbers()
        
    def update_line_numbers(self):
        """Update the displayed line numbers"""
        # Get current text content
        content = self.text_widget.get('1.0', 'end-1c')
        lines = content.count('\n') + 1
        
        # Generate line numbers
        line_numbers_text = '\n'.join(str(i) for i in range(1, lines + 1))
        
        # Update the line numbers widget
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', 'end')
        self.line_numbers.insert('1.0', line_numbers_text)
        self.line_numbers.config(state='disabled')
        
        # Sync scrolling
        self._sync_scroll()
    
    def _sync_scroll(self, event=None):
        """Sync scrolling between text widget and line numbers"""
        self.line_numbers.yview_moveto(self.text_widget.yview()[0])


class StatusBar(ttk.Frame):
    """Status bar displaying cursor position, zoom, and other info"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # Create status labels
        self.position_label = ttk.Label(self, text="Line: 1, Col: 1")
        self.position_label.pack(side='left', padx=5)
        
        self.zoom_label = ttk.Label(self, text="100%")
        self.zoom_label.pack(side='left', padx=5)
        
        self.encoding_label = ttk.Label(self, text="UTF-8")
        self.encoding_label.pack(side='left', padx=5)
        
        self.tab_label = ttk.Label(self, text="Tab: 4")
        self.tab_label.pack(side='left', padx=5)
        
        self.matches_label = ttk.Label(self, text="")
        self.matches_label.pack(side='right', padx=5)
    
    def update_position(self, line: int, col: int):
        """Update cursor position display"""
        self.position_label.config(text=f"Line: {line}, Col: {col}")
    
    def update_zoom(self, zoom_level: int):
        """Update zoom level display"""
        self.zoom_label.config(text=f"{zoom_level}%")
    
    def update_encoding(self, encoding: str):
        """Update encoding display"""
        self.encoding_label.config(text=encoding)
    
    def update_tab_width(self, width: int):
        """Update tab width display"""
        self.tab_label.config(text=f"Tab: {width}")
    
    def update_matches(self, current: int = 0, total: int = 0):
        """Update find matches display"""
        if total > 0:
            self.matches_label.config(text=f"Match: {current}/{total}")
        else:
            self.matches_label.config(text="")


class FindReplaceDialog(tk.Toplevel):
    """Find and Replace dialog with advanced options"""
    
    def __init__(self, parent, editor):
        super().__init__(parent)
        self.editor = editor
        self.title("Find and Replace")
        self.geometry("400x200")
        self.transient(parent)
        self.grab_set()
        
        self.matches = []
        self.current_match = 0
        self.search_flags = {
            'case_sensitive': False,
            'whole_word': False,
            'regex': False,
            'wrap_around': True
        }
        
        self._create_widgets()
        self._bind_events()
        
    def _create_widgets(self):
        """Create dialog widgets"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Find section
        ttk.Label(main_frame, text="Find:").grid(row=0, column=0, sticky='w', pady=2)
        self.find_entry = ttk.Entry(main_frame, width=30)
        self.find_entry.grid(row=0, column=1, columnspan=2, sticky='ew', pady=2, padx=(5,0))
        
        ttk.Label(main_frame, text="Replace:").grid(row=1, column=0, sticky='w', pady=2)
        self.replace_entry = ttk.Entry(main_frame, width=30)
        self.replace_entry.grid(row=1, column=1, columnspan=2, sticky='ew', pady=2, padx=(5,0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, sticky='ew', pady=10)
        
        self.find_next_btn = ttk.Button(button_frame, text="Find Next", command=self.find_next)
        self.find_next_btn.pack(side='left', padx=2)
        
        self.find_prev_btn = ttk.Button(button_frame, text="Find Previous", command=self.find_prev)
        self.find_prev_btn.pack(side='left', padx=2)
        
        self.replace_btn = ttk.Button(button_frame, text="Replace", command=self.replace)
        self.replace_btn.pack(side='left', padx=2)
        
        self.replace_all_btn = ttk.Button(button_frame, text="Replace All", command=self.replace_all)
        self.replace_all_btn.pack(side='left', padx=2)
        
        self.close_btn = ttk.Button(button_frame, text="Close", command=self.destroy)
        self.close_btn.pack(side='left', padx=2)
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options")
        options_frame.grid(row=3, column=0, columnspan=3, sticky='ew', pady=5)
        
        self.case_var = tk.BooleanVar()
        self.whole_word_var = tk.BooleanVar()
        self.regex_var = tk.BooleanVar()
        self.wrap_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Match Case", variable=self.case_var).pack(side='left', padx=5)
        ttk.Checkbutton(options_frame, text="Whole Word", variable=self.whole_word_var).pack(side='left', padx=5)
        ttk.Checkbutton(options_frame, text="Regex", variable=self.regex_var).pack(side='left', padx=5)
        ttk.Checkbutton(options_frame, text="Wrap Around", variable=self.wrap_var).pack(side='left', padx=5)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.grid(row=4, column=0, columnspan=3, sticky='w')
        
        main_frame.columnconfigure(1, weight=1)
        
    def _bind_events(self):
        """Bind keyboard events"""
        self.find_entry.bind('<KeyRelease>', self._on_find_change)
        self.bind('<Return>', lambda e: self.find_next())
        self.bind('<Escape>', lambda e: self.destroy())
        
    def _on_find_change(self, event=None):
        """Handle find text changes"""
        self.highlight_matches()
        
    def _get_search_pattern(self):
        """Get search pattern based on options"""
        pattern = self.find_entry.get()
        if not pattern:
            return None
            
        if not self.regex_var.get():
            pattern = re.escape(pattern)
            
        if self.whole_word_var.get():
            pattern = f'\\b{pattern}\\b'
            
        return pattern
    
    def highlight_matches(self):
        """Highlight all matches in the text"""
        pattern = self._get_search_pattern()
        if not pattern:
            self.editor.text_widget.tag_remove('search_highlight', '1.0', 'end')
            self.matches = []
            self.current_match = 0
            self.status_label.config(text="")
            return
            
        try:
            flags = 0 if self.case_var.get() else re.IGNORECASE
            content = self.editor.text_widget.get('1.0', 'end-1c')
            
            # Remove existing highlights
            self.editor.text_widget.tag_remove('search_highlight', '1.0', 'end')
            
            # Find all matches
            self.matches = list(re.finditer(pattern, content, flags))
            self.current_match = 0
            
            # Apply highlights
            for match in self.matches:
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.editor.text_widget.tag_add('search_highlight', start, end)
            
            # Configure highlight style
            self.editor.text_widget.tag_config('search_highlight', background='yellow')
            
            # Update status
            if self.matches:
                self.status_label.config(text=f"Found {len(self.matches)} matches")
                self._select_match(0)
            else:
                self.status_label.config(text="No matches found")
                
        except re.error as e:
            self.status_label.config(text=f"Regex error: {str(e)}")
    
    def _select_match(self, index: int):
        """Select and scroll to a specific match"""
        if not self.matches:
            return
            
        self.current_match = index % len(self.matches)
        match = self.matches[self.current_match]
        
        start = f"1.0+{match.start()}c"
        end = f"1.0+{match.end()}c"
        
        self.editor.text_widget.tag_remove('sel', '1.0', 'end')
        self.editor.text_widget.tag_add('sel', start, end)
        self.editor.text_widget.mark_set('insert', start)
        self.editor.text_widget.see(start)
        
        self.status_label.config(text=f"Match {self.current_match + 1} of {len(self.matches)}")
    
    def find_next(self):
        """Find next occurrence"""
        if not self.matches:
            self.highlight_matches()
            return
            
        self.current_match = (self.current_match + 1) % len(self.matches)
        self._select_match(self.current_match)
    
    def find_prev(self):
        """Find previous occurrence"""
        if not self.matches:
            self.highlight_matches()
            return
            
        self.current_match = (self.current_match - 1) % len(self.matches)
        self._select_match(self.current_match)
    
    def replace(self):
        """Replace current match"""
        if not self.matches or self.current_match >= len(self.matches):
            return
            
        replace_text = self.replace_entry.get()
        match = self.matches[self.current_match]
        
        start = f"1.0+{match.start()}c"
        end = f"1.0+{match.end()}c"
        
        self.editor.text_widget.delete(start, end)
        self.editor.text_widget.insert(start, replace_text)
        
        # Re-run search after replacement
        self.highlight_matches()
    
    def replace_all(self):
        """Replace all matches"""
        if not self.matches:
            return
            
        replace_text = self.replace_entry.get()
        replacements = 0
        
        # Replace from end to beginning to maintain positions
        for match in reversed(self.matches):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            
            self.editor.text_widget.delete(start, end)
            self.editor.text_widget.insert(start, replace_text)
            replacements += 1
        
        self.status_label.config(text=f"Replaced {replacements} occurrences")
        self.matches = []
        self.current_match = 0


class EditorFrame(ttk.Frame):
    """Main text editor frame with text widget and line numbers"""
    
    def __init__(self, parent, settings: SettingsManager):
        super().__init__(parent)
        self.settings = settings
        self.parent = parent
        self.current_file = None
        self.modified = False
        self.read_only = False
        self.zoom_level = 100
        
        self._create_widgets()
        self._bind_events()
        self._apply_settings()
        
    def _create_widgets(self):
        """Create editor widgets"""
        # Create paned window for resizable layout
        self.paned_window = ttk.PanedWindow(self, orient='horizontal')
        self.paned_window.pack(fill='both', expand=True)
        

        
        # Text widget
        text_frame = ttk.Frame(self.paned_window)
        self.text_widget = tk.Text(
            text_frame,
            wrap='none',
            undo=True,
            maxundo=-1,
            font=('Consolas', 12),
            selectbackground='lightblue',
            inactiveselectbackground='lightgray'
        )
        
        # Line numbers panel
        self.line_number_panel = LineNumberPanel(self.paned_window, self.text_widget)
        self.paned_window.add(self.line_number_panel)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.text_widget.yview)
        h_scrollbar = ttk.Scrollbar(text_frame, orient='horizontal', command=self.text_widget.xview)
        
        self.text_widget.configure(
            yscrollcommand=lambda f, l: self._on_text_scroll(f, l, v_scrollbar),
            xscrollcommand=h_scrollbar.set
        )
        
        # Pack widgets
        self.text_widget.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        
        self.paned_window.add(text_frame)
        
        # Connect line numbers to text widget
        self.line_number_panel.text_widget = self.text_widget
        
        # Configure tags
        self.text_widget.tag_configure('current_line', background='#e8f2ff')
        self.text_widget.tag_configure('search_highlight', background='yellow')
        
    def _bind_events(self):
        """Bind keyboard and mouse events"""
        # Text modification events
        self.text_widget.bind('<<Modified>>', self._on_modification)
        self.text_widget.bind('<KeyPress>', self._on_key_press)
        self.text_widget.bind('<Button-1>', self._on_click)
        
        # Cursor movement
        self.text_widget.bind('<KeyRelease>', self._update_cursor_position)
        self.text_widget.bind('<ButtonRelease-1>', self._update_cursor_position)
        
        # Zoom
        self.text_widget.bind('<Control-MouseWheel>', self._on_zoom)
        self.text_widget.bind('<Control-plus>', lambda e: self.zoom_in())
        self.text_widget.bind('<Control-minus>', lambda e: self.zoom_out())
        self.text_widget.bind('<Control-0>', lambda e: self.zoom_reset())
        
    def _apply_settings(self):
        """Apply current settings to editor"""
        font_size = self.settings.get('font_size', 12)
        font_family = self.settings.get('font_family', 'Consolas')
        tab_width = self.settings.get('tab_width', 4)
        
        # Calculate actual font size based on zoom
        actual_size = int(font_size * (self.zoom_level / 100))
        self.text_widget.config(font=(font_family, actual_size))
        
        # Configure tabs
        tab_spaces = ' ' * tab_width
        self.text_widget.config(tabs=(font_size * 2,))  # Approximate tab width
        
        # Update line numbers if enabled
        if self.settings.get('line_numbers', True):
            self.line_number_panel.pack(side='left', fill='y')
            self.line_number_panel.update_line_numbers()
        else:
            self.line_number_panel.pack_forget()
            
        # Word wrap
        wrap_mode = 'word' if self.settings.get('word_wrap', False) else 'none'
        self.text_widget.config(wrap=wrap_mode)
        
    def _on_text_scroll(self, first, last, scrollbar):
        """Handle text scrolling synchronization"""
        self.line_number_panel.line_numbers.yview_moveto(first)
        scrollbar.set(first, last)
        self._highlight_current_line()
        
    def _on_modification(self, event=None):
        """Handle text modification events"""
        if self.text_widget.edit_modified():
            self.modified = True
            self.text_widget.edit_modified(False)
            if hasattr(self.parent, 'update_title'):
                self.parent.update_title()
                
    def _on_key_press(self, event=None):
        """Handle key press events"""
        self._highlight_current_line()
        self._update_cursor_position()
        
    def _on_click(self, event=None):
        """Handle mouse click events"""
        self._highlight_current_line()
        self._update_cursor_position()
        
    def _on_zoom(self, event):
        """Handle zoom with mouse wheel"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def _highlight_current_line(self):
        """Highlight the current line"""
        self.text_widget.tag_remove('current_line', '1.0', 'end')
        
        current_line = self.text_widget.index('insert').split('.')[0]
        start = f"{current_line}.0"
        end = f"{current_line}.end"
        
        self.text_widget.tag_add('current_line', start, end)
    
    def _update_cursor_position(self, event=None):
        """Update cursor position in status bar"""
        if hasattr(self.parent, 'status_bar'):
            cursor_index = self.text_widget.index('insert')
            line, col = cursor_index.split('.')
            self.parent.status_bar.update_position(int(line), int(col) + 1)
    
    def zoom_in(self):
        """Zoom in text"""
        self.zoom_level = min(200, self.zoom_level + 10)
        self._apply_settings()
        if hasattr(self.parent, 'status_bar'):
            self.parent.status_bar.update_zoom(self.zoom_level)
    
    def zoom_out(self):
        """Zoom out text"""
        self.zoom_level = max(50, self.zoom_level - 10)
        self._apply_settings()
        if hasattr(self.parent, 'status_bar'):
            self.parent.status_bar.update_zoom(self.zoom_level)
    
    def zoom_reset(self):
        """Reset zoom to 100%"""
        self.zoom_level = 100
        self._apply_settings()
        if hasattr(self.parent, 'status_bar'):
            self.parent.status_bar.update_zoom(self.zoom_level)
    
    def get_text(self) -> str:
        """Get all text content"""
        return self.text_widget.get('1.0', 'end-1c')
    
    def set_text(self, text: str):
        """Set text content"""
        self.text_widget.delete('1.0', 'end')
        self.text_widget.insert('1.0', text)
        self.modified = False
        self.line_number_panel.update_line_numbers()
        self._highlight_current_line()
    
    def goto_line(self, line_number: int):
        """Go to specific line number"""
        max_line = int(self.text_widget.index('end-1c').split('.')[0])
        if 1 <= line_number <= max_line:
            self.text_widget.mark_set('insert', f"{line_number}.0")
            self.text_widget.see(f"{line_number}.0")
            self._highlight_current_line()
            self._update_cursor_position()
            return True
        return False


class MenuBar:
    """Handles application menus"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.menu_bar = tk.Menu(parent)
        parent.config(menu=self.menu_bar)
        
        self._create_menus()
    
    def _create_menus(self):
        """Create all application menus"""
        self._create_file_menu()
        self._create_edit_menu()
        self._create_view_menu()
        self._create_help_menu()
    
    def _create_file_menu(self):
        """Create File menu"""
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        file_menu.add_command(label="New", command=self.app.file_new, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.app.file_open, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.app.file_save, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.app.file_save_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        
        # Recent files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        self._update_recent_files()
        
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.app.quit)
        
        # Bind accelerators
        self.parent.bind_all('<Control-n>', lambda e: self.app.file_new())
        self.parent.bind_all('<Control-o>', lambda e: self.app.file_open())
        self.parent.bind_all('<Control-s>', lambda e: self.app.file_save())
        self.parent.bind_all('<Control-Shift-S>', lambda e: self.app.file_save_as())
    
    def _create_edit_menu(self):
        """Create Edit menu"""
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        edit_menu.add_command(label="Undo", command=self.app.edit_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.app.edit_redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.app.edit_cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.app.edit_copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.app.edit_paste, accelerator="Ctrl+V")
        edit_menu.add_command(label="Select All", command=self.app.edit_select_all, accelerator="Ctrl+A")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find", command=self.app.edit_find, accelerator="Ctrl+F")
        edit_menu.add_command(label="Replace", command=self.app.edit_replace, accelerator="Ctrl+H")
        edit_menu.add_command(label="Go To Line", command=self.app.edit_goto_line, accelerator="Ctrl+G")
        
        # Bind accelerators
        self.parent.bind_all('<Control-z>', lambda e: self.app.edit_undo())
        self.parent.bind_all('<Control-y>', lambda e: self.app.edit_redo())
        self.parent.bind_all('<Control-x>', lambda e: self.app.edit_cut())
        self.parent.bind_all('<Control-c>', lambda e: self.app.edit_copy())
        self.parent.bind_all('<Control-v>', lambda e: self.app.edit_paste())
        self.parent.bind_all('<Control-a>', lambda e: self.app.edit_select_all())
        self.parent.bind_all('<Control-f>', lambda e: self.app.edit_find())
        self.parent.bind_all('<Control-h>', lambda e: self.app.edit_replace())
        self.parent.bind_all('<Control-g>', lambda e: self.app.edit_goto_line())
    
    def _create_view_menu(self):
        """Create View menu"""
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        
        self.line_numbers_var = tk.BooleanVar(value=True)
        self.word_wrap_var = tk.BooleanVar()
        
        view_menu.add_checkbutton(label="Line Numbers", variable=self.line_numbers_var, 
                                 command=self.app.toggle_line_numbers)
        view_menu.add_checkbutton(label="Word Wrap", variable=self.word_wrap_var,
                                 command=self.app.toggle_word_wrap)
        view_menu.add_separator()
        view_menu.add_command(label="Zoom In", command=self.app.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.app.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Reset Zoom", command=self.app.zoom_reset, accelerator="Ctrl+0")
        
        # Bind accelerators
        self.parent.bind_all('<Control-plus>', lambda e: self.app.zoom_in())
        self.parent.bind_all('<Control-minus>', lambda e: self.app.zoom_out())
        self.parent.bind_all('<Control-0>', lambda e: self.app.zoom_reset())
    
    def _create_help_menu(self):
        """Create Help menu"""
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        
        help_menu.add_command(label="About", command=self.app.show_about)
    
    def _update_recent_files(self):
        """Update recent files menu"""
        self.recent_menu.delete(0, 'end')
        recent_files = self.app.settings.get('recent_files', [])
        
        if not recent_files:
            self.recent_menu.add_command(label="No recent files", state='disabled')
        else:
            for filepath in recent_files:
                # Show only filename in menu but store full path
                filename = os.path.basename(filepath)
                self.recent_menu.add_command(
                    label=filename,
                    command=lambda f=filepath: self.app.open_recent_file(f)
                )
    
    def update_view_menu(self):
        """Update view menu checkboxes"""
        self.line_numbers_var.set(self.app.settings.get('line_numbers', True))
        self.word_wrap_var.set(self.app.settings.get('word_wrap', False))


class MainApp(tk.Tk):
    """Main application class"""
    
    def __init__(self):
        super().__init__()
        
        self.settings = SettingsManager()
        self.title("Tkinter Text Editor")
        self.geometry(self.settings.get('window_geometry', '800x600'))
        
        # Initialize components
        self._setup_ui()
        self._apply_theme()
        
        # Set up window protocol
        self.protocol("WM_DELETE_WINDOW", self.quit)
        
        # Update title
        self.update_title()
    
    def _setup_ui(self):
        """Set up user interface"""
        # Create menu bar
        self.menu_bar = MenuBar(self, self)
        
        # Create main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True)
        
        # Create editor
        self.editor = EditorFrame(main_frame, self.settings)
        self.editor.pack(fill='both', expand=True)
        
        # Create status bar
        self.status_bar = StatusBar(main_frame)
        self.status_bar.pack(side='bottom', fill='x')
        
        # Update status bar with initial settings
        self.status_bar.update_tab_width(self.settings.get('tab_width', 4))
        self.status_bar.update_zoom(self.editor.zoom_level)
        
        # Update menu checkboxes
        self.menu_bar.update_view_menu()
    
    def _apply_theme(self):
        """Apply current theme"""
        style = ttk.Style()
        theme = self.settings.get('theme', 'clam')
        
        try:
            style.theme_use(theme)
        except tk.TclError:
            style.theme_use('clam')
    
    def update_title(self):
        """Update window title with current file and modification status"""
        title = "Tkinter Text Editor"
        if self.editor.current_file:
            filename = os.path.basename(self.editor.current_file)
            title = f"{filename} - {title}"
        if self.editor.modified:
            title = f"*{title}"
        self.title(title)
    
    def file_new(self):
        """Create new file"""
        if self.editor.modified:
            if not self._confirm_unsaved_changes():
                return
        
        self.editor.set_text("")
        self.editor.current_file = None
        self.editor.modified = False
        self.update_title()
    
    def file_open(self, filename=None):
        """Open file"""
        if self.editor.modified:
            if not self._confirm_unsaved_changes():
                return
        
        if not filename:
            filename = filedialog.askopenfilename(
                title="Open File",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("Python files", "*.py"),
                    ("All files", "*.*")
                ]
            )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                self.editor.set_text(content)
                self.editor.current_file = filename
                self.editor.modified = False
                self.settings.add_recent_file(filename)
                self.menu_bar._update_recent_files()
                self.update_title()
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {str(e)}")
    
    def file_save(self):
        """Save file"""
        if not self.editor.current_file:
            return self.file_save_as()
        
        try:
            with open(self.editor.current_file, 'w', encoding='utf-8') as file:
                file.write(self.editor.get_text())
            
            self.editor.modified = False
            self.update_title()
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {str(e)}")
            return False
    
    def file_save_as(self):
        """Save file as new name"""
        filename = filedialog.asksaveasfilename(
            title="Save File As",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Python files", "*.py"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.editor.current_file = filename
            self.settings.add_recent_file(filename)
            self.menu_bar._update_recent_files()
            return self.file_save()
        return False
    
    def open_recent_file(self, filename):
        """Open recent file from menu"""
        self.file_open(filename)
    
    def edit_undo(self):
        """Undo last action"""
        try:
            self.editor.text_widget.edit_undo()
        except tk.TclError:
            pass
    
    def edit_redo(self):
        """Redo last action"""
        try:
            self.editor.text_widget.edit_redo()
        except tk.TclError:
            pass
    
    def edit_cut(self):
        """Cut selected text"""
        try:
            self.editor.text_widget.event_generate("<<Cut>>")
        except tk.TclError:
            pass
    
    def edit_copy(self):
        """Copy selected text"""
        try:
            self.editor.text_widget.event_generate("<<Copy>>")
        except tk.TclError:
            pass
    
    def edit_paste(self):
        """Paste text from clipboard"""
        try:
            self.editor.text_widget.event_generate("<<Paste>>")
        except tk.TclError:
            pass
    
    def edit_select_all(self):
        """Select all text"""
        self.editor.text_widget.tag_add('sel', '1.0', 'end')
    
    def edit_find(self):
        """Open find dialog"""
        FindReplaceDialog(self, self.editor)
    
    def edit_replace(self):
        """Open replace dialog"""
        FindReplaceDialog(self, self.editor)
    
    def edit_goto_line(self):
        """Go to specific line"""
        line_str = tk.simpledialog.askstring("Go To Line", "Enter line number:")
        if line_str and line_str.isdigit():
            line_num = int(line_str)
            if not self.editor.goto_line(line_num):
                messagebox.showwarning("Go To Line", f"Line {line_num} is out of range")
    
    def toggle_line_numbers(self):
        """Toggle line numbers visibility"""
        current = self.settings.get('line_numbers', True)
        self.settings.set('line_numbers', not current)
        self.editor._apply_settings()
        self.menu_bar.update_view_menu()
    
    def toggle_word_wrap(self):
        """Toggle word wrap"""
        current = self.settings.get('word_wrap', False)
        self.settings.set('word_wrap', not current)
        self.editor._apply_settings()
        self.menu_bar.update_view_menu()
    
    def zoom_in(self):
        """Zoom in"""
        self.editor.zoom_in()
    
    def zoom_out(self):
        """Zoom out"""
        self.editor.zoom_out()
    
    def zoom_reset(self):
        """Reset zoom"""
        self.editor.zoom_reset()
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Tkinter Text Editor",
            "Professional Tkinter Text Editor\n\n"
            "Built with Python and Tkinter\n"
            "Features: Syntax highlighting, Find/Replace, Multiple themes, and more!"
        )
    
    def _confirm_unsaved_changes(self) -> bool:
        """Confirm if user wants to save unsaved changes"""
        if not self.editor.modified:
            return True
        
        result = messagebox.askyesnocancel(
            "Unsaved Changes",
            "Do you want to save changes before closing?"
        )
        
        if result is None:  # Cancel
            return False
        elif result:  # Yes
            return self.file_save()
        else:  # No
            return True
    
    def quit(self):
        """Quit application"""
        if self.editor.modified:
            if not self._confirm_unsaved_changes():
                return
        
        # Save window geometry
        self.settings.set('window_geometry', self.geometry())
        self.settings.save_settings()
        
        self.destroy()


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()