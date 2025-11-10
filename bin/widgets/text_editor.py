#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyEdit: A Professional Text Editor

A modern and modular text editor application showcasing a 
clean interface, high performance, and robust functionality. 
Designed with an object-oriented architecture suitable for 
professional and commercial use.

Version: 1.0
Release Date: November 9, 2025
"""

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox, simpledialog, font
import os
import re
import json



# --- Configuration (Could be externalized to JSON) ---
DEFAULT_THEME = "light"
DEFAULT_FONT_FAMILY = "Consolas"
DEFAULT_FONT_SIZE = 11
DEFAULT_TAB_WIDTH = 4

# --- Main Application Class ---



class TextEditorWidget(ttk.Frame):
    """
    The main application class for the Tkinter Text Editor.
    
    This class is a self-contained ttk.Frame that manages the core 
    components (MenuBar, TextEditor, StatusBar) and handles application-level
    state and file operations.
    """
    
    def __init__(self, master, *args, **kwargs):
        """Initializes the main application frame."""
        super().__init__(master, *args, **kwargs)
        
        self.current_file_path = None
        self._is_modified = False
        self._find_dialog = None
        self._selection_job = None
        
        # --- Get the root window ---
        self.root = self.winfo_toplevel()
        
        # --- Window Setup ---
        #! self.root.title("Untitled - PyEdit")
        #! self.root.geometry("1000x700")
        
        # --- Style & Theme Setup ---
        self.style = ttk.Style(self)
        self._init_themes()
        
        # --- Font Configuration ---
        self.text_font = font.Font(
            family=DEFAULT_FONT_FAMILY, 
            size=DEFAULT_FONT_SIZE
        )
        self.current_font_size = DEFAULT_FONT_SIZE
        
        # --- UI Variables ---
        self.show_line_numbers = tk.BooleanVar(value=True)
        self.show_status_bar = tk.BooleanVar(value=True)
        self.word_wrap = tk.BooleanVar(value=False)
        self.current_theme = tk.StringVar(value=DEFAULT_THEME)
        self.current_tab_width = tk.IntVar(value=DEFAULT_TAB_WIDTH)
        
        # --- Create Main Components ---
        
        # 1. MenuBar
        # self.menu_bar = self._create_menu_bar()
        # # Attach the menu to the root window, not the frame
        #! self.root.config(menu=self.menu_bar)
        
        # 2. Status Bar (created before TextEditor for layout)
        # It now packs into 'self' (the TextEditorWidget frame)
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar.set_zoom(f"{int(self.current_font_size / DEFAULT_FONT_SIZE * 100)}%")
        self.status_bar.set_tab_width(f"Tabs: {self.current_tab_width.get()}")
        
        # 3. Main Editor Component
        # It also packs into 'self' (the TextEditorWidget frame)
        self.text_editor = TextEditor(self, font=self.text_font)
        self.text_editor.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # --- Initial Setup ---
        self._set_tab_width(self.current_tab_width.get())
        self._set_theme(self.current_theme.get())
        self._update_all_ui()
        
        # --- Event Bindings ---
        # Bind to the root window's close protocol
        #! self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # File Operations
        self.bind_event("<Control-n>", self._file_new)
        self.bind_event("<Control-o>", self._file_open)
        self.bind_event("<Control-s>", self._file_save)
        self.bind_event("<Control-Shift-S>", self._file_save_as)
        
        # Find/Replace
        self.bind_event("<Control-f>", self._show_find_dialog)
        self.bind_event("<Control-h>", self._show_find_dialog)
        
        # Navigation
        self.bind_event("<Control-g>", self._nav_go_to_line)
        
        # View
        self.bind_event("<Control-plus>", self._view_zoom_in)
        self.bind_event("<Control-equal>", self._view_zoom_in) # Ctrl+=
        self.bind_event("<Control-minus>", self._view_zoom_out)
        self.bind_event("<Control-0>", self._view_zoom_reset)
        
        # Listen for text modifications
        self.text_editor.text.bind("<<Modified>>", self._on_text_modified)
        
        # Bind selection change
        self.text_editor.text.bind("<<Selection>>", self._on_selection_change)

        # --- Pack 'self' (the TextEditorWidget frame) into its master ---
        # This makes the TextEditorWidget visible inside the frame 'a'
        #! self.pack(fill=tk.BOTH, expand=True)

    def bind_event(self, shortcut, command):
        """Helper to bind events to the root window."""
        # Bind to the root window to catch global shortcuts
        #! self.root.bind(shortcut, lambda e: (command(), "break")[1])
        ...
        
    def _init_themes(self):
        """Defines the color palettes for light and dark themes."""
        # --- Light Theme ---
        self.style.theme_create("light", parent="vista", settings={
            ".": {
                "configure": {"background": "#FFFFFF", "foreground": "#000000"}
            },
            # "TFrame": {
            #     "configure": {"background": "#FFFFFF"}
            # },
            # "StatusBar.TFrame": {
            #     "configure": {"background": "#F0F0F0"}
            # },
            # "TLabel": {
            #     "configure": {"background": "#F0F0F0"}
            # },
            # "LineNumberPanel.TFrame": {
            #     "configure": {"background": "#F0F0F0"}
            # },
            # "TButton": {
            #     "configure": {"background": "#E1E1E1"},
            #     "map": {"background": [("active", "#C0C0C0")]}
            # },
            # "TCheckbutton": {
            #     "configure": {"background": "#F0F0F0"}
            # },
            # "TEntry": {
            #     "configure": {"fieldbackground": "#FFFFFF", "foreground": "#000000"}
            # }
        })

        # --- Dark Theme ---
        dark_bg = "#2b2b2b"
        dark_fg = "#d3d3d3"
        dark_base = "#3c3c3c"
        dark_insert = "#FFFFFF"
        dark_select = "#4a6984"
        dark_line_bg = "#313335"

        self.style.theme_create("dark", parent="vista", settings={
            ".": {
                "configure": {"background": dark_bg, "foreground": dark_fg}
            },
            # "TFrame": {
            #     "configure": {"background": dark_bg}
            # },
            # "StatusBar.TFrame": {
            #     "configure": {"background": dark_base}
            # },
            # "TLabel": {
            #     "configure": {"background": dark_base, "foreground": dark_fg}
            # },
            # "LineNumberPanel.TFrame": {
            #     "configure": {"background": dark_line_bg}
            # },
            # "TButton": {
            #     "configure": {"background": dark_base, "foreground": dark_fg},
            #     "map": {"background": [("active", "#555555")]}
            # },
            # "TCheckbutton": {
            #     "configure": {"background": dark_bg, "foreground": dark_fg,
            #                   "indicatorcolor": dark_fg},
            #     "map": {"indicatorbackground": [("active", dark_base)]}
            # },
            # "TEntry": {
            #     "configure": {"fieldbackground": dark_base, "foreground": dark_fg,
            #                   "insertcolor": dark_insert}
            # },
            # "TMenu": {
            #     "configure": {"background": dark_base, "foreground": dark_fg}
            # },
            # "TMenuBar": {
            #     "configure": {"background": dark_base, "foreground": dark_fg}
            # }
        })
        
        self.style.theme_use(DEFAULT_THEME)

    def _set_theme(self, theme_name):
        """Applies the selected theme to all components."""
        self.style.theme_use(theme_name)
        self.current_theme.set(theme_name)
        
        if theme_name == "dark":
            # --- Dark Colors ---
            text_bg = "#2b2b2b"
            text_fg = "#d3d3d3"
            insert_bg = "#FFFFFF"
            select_bg = "#4a6984"
            line_bg = "#313335"
            line_fg = "#9C9C9C"
            current_line_bg = "#3c3c3c"
            find_match_bg = "#616161"
            
            # --- NEW TAGS ---
            selection_match_bg = "#404060" 
            current_find_match_bg = "#7a4a00" 
            
        else:
            # --- Light Colors ---
            text_bg = "#FFFFFF"
            text_fg = "#000000"
            insert_bg = "#000000"
            select_bg = "#B4D5FF"
            line_bg = "#F0F0F0"
            line_fg = "#6E6E6E"
            current_line_bg = "#E8F2FF"
            find_match_bg = "#FFFF00"
            
            # --- NEW TAGS ---
            selection_match_bg = "#DDEEFF" 
            current_find_match_bg = "#FFA33A" 
            
        # Configure Text Widget
        self.text_editor.text.config(
            background=text_bg,
            foreground=text_fg,
            insertbackground=insert_bg,
            selectbackground=select_bg,
            selectforeground=text_fg,
            wrap=tk.WORD if self.word_wrap.get() else tk.NONE
        )
        
        # Configure Text Tags
        self.text_editor.text.tag_config(
            "current_line", background=current_line_bg
        )
        self.text_editor.text.tag_config(
            "find_match", background=find_match_bg, foreground=text_fg
        )
        
        self.text_editor.text.tag_config(
            "selection_match", background=selection_match_bg
        )
        self.text_editor.text.tag_config(
            "current_find_match", background=current_find_match_bg
        )
        
        # Configure Line Numbers
        self.text_editor.line_numbers.config(
            background=line_bg
        )
        self.text_editor.line_numbers.set_colors(line_bg, line_fg)
        
        # Update UI
        self._update_all_ui()
    
    def _create_menu_bar(self):
        """Creates and returns the main application Menu."""
        # The menu's master is the root window
        menu_bar = tk.Menu(self.root)

        # --- File Menu ---
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self._file_new)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self._file_open)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self._file_save)
        file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self._file_save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # --- Edit Menu ---
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self._edit_undo)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self._edit_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=self._edit_cut)
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=self._edit_copy)
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=self._edit_paste)
        edit_menu.add_command(label="Select All", accelerator="Ctrl+A", command=self._edit_select_all)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find...", accelerator="Ctrl+F", command=self._show_find_dialog)
        edit_menu.add_command(label="Replace...", accelerator="Ctrl+H", command=self._show_find_dialog)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)

        # --- View Menu ---
        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_checkbutton(
            label="Show Line Numbers",
            variable=self.show_line_numbers,
            command=self._toggle_line_numbers
        )
        view_menu.add_checkbutton(
            label="Show Status Bar",
            variable=self.show_status_bar,
            command=self._toggle_status_bar
        )
        view_menu.add_checkbutton(
            label="Word Wrap",
            variable=self.word_wrap,
            command=self._toggle_word_wrap
        )
        view_menu.add_separator()
        
        # Zoom Sub-menu
        zoom_menu = tk.Menu(view_menu, tearoff=0)
        zoom_menu.add_command(label="Zoom In", accelerator="Ctrl++", command=self._view_zoom_in)
        zoom_menu.add_command(label="Zoom Out", accelerator="Ctrl+-", command=self._view_zoom_out)
        zoom_menu.add_command(label="Restore Default Zoom", accelerator="Ctrl+0", command=self._view_zoom_reset)
        view_menu.add_cascade(label="Zoom", menu=zoom_menu)
        
        # Tab Width Sub-menu
        tab_menu = tk.Menu(view_menu, tearoff=0)
        tab_menu.add_radiobutton(label="2 Spaces", value=2, variable=self.current_tab_width, command=self._on_tab_width_change)
        tab_menu.add_radiobutton(label="4 Spaces", value=4, variable=self.current_tab_width, command=self._on_tab_width_change)
        tab_menu.add_radiobutton(label="8 Spaces", value=8, variable=self.current_tab_width, command=self._on_tab_width_change)
        view_menu.add_cascade(label="Tab Width", menu=tab_menu)

        # Theme Sub-menu
        theme_menu = tk.Menu(view_menu, tearoff=0)
        theme_menu.add_radiobutton(label="Light", value="light", variable=self.current_theme, command=lambda: self._set_theme("light"))
        theme_menu.add_radiobutton(label="Dark", value="dark", variable=self.current_theme, command=lambda: self._set_theme("dark"))
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        
        menu_bar.add_cascade(label="View", menu=view_menu)

        # --- Navigation Menu ---
        nav_menu = tk.Menu(menu_bar, tearoff=0)
        nav_menu.add_command(label="Go To Line...", accelerator="Ctrl+G", command=self._nav_go_to_line)
        menu_bar.add_cascade(label="Navigation", menu=nav_menu)

        # --- Help Menu ---
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About PyEdit", command=self._help_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        return menu_bar

    # --- File Operations ---
    
    def _file_new(self):
        """Handles the 'New File' action."""
        if self._check_unsaved_changes() is False:
            return
            
        self.text_editor.text.delete("1.0", tk.END)
        self.current_file_path = None
        self._set_modified(False)
        self._update_all_ui()

    def _file_open(self):
        """Handles the 'Open File' action."""
        if self._check_unsaved_changes() is False:
            return
            
        filepath = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"), ("All Files", "*.*")]
        )
        
        if not filepath:
            return
            
        try:
            encoding = "utf-8"
            with open(filepath, "r", encoding=encoding) as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                encoding = "latin-1"
                with open(filepath, "r", encoding=encoding) as f:
                    content = f.read()
            except Exception as e:
                messagebox.showerror("Open Error", f"Failed to read file: {e}")
                return
        except Exception as e:
            messagebox.showerror("Open Error", f"Failed to open file: {e}")
            return
            
        self.text_editor.text.delete("1.0", tk.END)
        self.text_editor.text.insert("1.0", content)
        self.current_file_path = filepath
        self._set_modified(False)
        self.status_bar.set_encoding(encoding)
        self.text_editor.text.edit_reset() 
        self._update_all_ui()

    def _file_save(self):
        """Handles the 'Save File' action."""
        if not self.current_file_path:
            return self._file_save_as()
            
        try:
            content = self.text_editor.text.get("1.0", tk.END)
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self._set_modified(False)
            return True
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save file: {e}")
            return False

    def _file_save_as(self):
        """Handles the 'Save File As' action."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"), ("All Files", "*.*")]
        )
        
        if not filepath:
            return False
            
        self.current_file_path = filepath
        return self._file_save()

    def _check_unsaved_changes(self):
        """
        Checks for unsaved changes and prompts the user.
        """
        if not self._is_modified:
            return True
            
        filename = os.path.basename(self.current_file_path) if self.current_file_path else "Untitled"
        response = messagebox.askyesnocancel(
            "Unsaved Changes",
            f"Do you want to save changes to {filename}?"
        )
        
        if response is True:  # Yes
            return self._file_save()
        elif response is False: # No
            return True
        else:  # Cancel
            return False

    def _on_close(self):
        """Handles the application window close event."""
        if self._check_unsaved_changes():
            # Destroy the root window
            #! self.root.destroy()
            ...

    # --- Edit Operations ---

    def _edit_undo(self):
        self.text_editor.text.event_generate("<<Undo>>")

    def _edit_redo(self):
        self.text_editor.text.event_generate("<<Redo>>")

    def _edit_cut(self):
        self.text_editor.text.event_generate("<<Cut>>")

    def _edit_copy(self):
        self.text_editor.text.event_generate("<<Copy>>")

    def _edit_paste(self):
        self.text_editor.text.event_generate("<<Paste>>")

    def _edit_select_all(self):
        self.text_editor.text.event_generate("<<SelectAll>>")

    # --- Find & Replace ---

    def _show_find_dialog(self, event=None):
        """Shows the Find/Replace dialog window."""
        if self._find_dialog:
            self._find_dialog.deiconify()
            self._find_dialog.lift()
        else:
            # The master for the dialog is the root window
            self._find_dialog = FindReplaceDialog(self, self.text_editor.text)
            
        # Move focus to 'Find' entry
        self._find_dialog.find_entry.focus_set()
        
        try:
            selected_text = self.text_editor.text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self._find_dialog.find_var.set(selected_text)
                self._find_dialog.find_entry.select_range(0, tk.END)
        except tk.TclError:
            pass 

    # --- View Operations ---

    def _toggle_line_numbers(self):
        """Shows or hides the line number panel."""
        self.text_editor.toggle_line_numbers(self.show_line_numbers.get())
        
    def _toggle_status_bar(self):
        """Shows or hides the status bar."""
        if self.show_status_bar.get():
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        else:
            self.status_bar.pack_forget()
            
    def _toggle_word_wrap(self):
        """Toggles word wrap on the text widget."""
        if self.word_wrap.get():
            self.text_editor.text.config(wrap=tk.WORD)
        else:
            self.text_editor.text.config(wrap=tk.NONE)

    def _zoom(self, delta):
        """Increases or decreases the font size."""
        new_size = max(6, self.current_font_size + delta)
        self.current_font_size = new_size
        self.text_font.config(size=new_size)
        self.text_editor.line_numbers.set_font(self.text_font)
        self._set_tab_width(self.current_tab_width.get())
        self.status_bar.set_zoom(f"{int(self.current_font_size / DEFAULT_FONT_SIZE * 100)}%")
        self._update_all_ui()

    def _view_zoom_in(self):
        self._zoom(1)

    def _view_zoom_out(self):
        self._zoom(-1)
        
    def _view_zoom_reset(self):
        delta = DEFAULT_FONT_SIZE - self.current_font_size
        self._zoom(delta)
        
    def _on_tab_width_change(self):
        """Callback for when tab width is changed from the menu."""
        self._set_tab_width(self.current_tab_width.get())
        
    def _set_tab_width(self, width_in_spaces):
        """Configures the text widget to use pixel width for tabs."""
        tab_width_pixels = self.text_font.measure(' ' * width_in_spaces)
        self.text_editor.text.config(tabs=(tab_width_pixels,))
        self.status_bar.set_tab_width(f"Tabs: {width_in_spaces}")
        
    # --- Navigation Operations ---
    
    def _nav_go_to_line(self):
        """Shows a dialog to jump to a specific line number."""
        total_lines = int(self.text_editor.text.index(tk.END).split('.')[0]) - 1
        line_num = simpledialog.askinteger(
            "Go To Line",
            f"Enter line number (1-{total_lines}):",
            minvalue=1, maxvalue=total_lines
        )
        
        if line_num:
            target_index = f"{line_num}.0"
            self.text_editor.text.mark_set(tk.INSERT, target_index)
            self.text_editor.text.see(target_index)
            self.text_editor.text.focus_set()
            self._update_all_ui()

    # --- Help Operations ---

    def _help_about(self):
        """Shows the 'About' dialog."""
        messagebox.showinfo(
            "About PyEdit",
            "PyEdit v1.0\nA Professional Tkinter Text Editor\n"
            "Developed by Gemini (AI)"
        )

    # --- State & UI Management ---

    def _set_modified(self, modified_state):
        """Sets the modification state of the file."""
        if self._is_modified != modified_state:
            self._is_modified = modified_state
            self._update_title()

    def _update_title(self):
        """Updates the main window title with file name and modified status."""
        filename = "Untitled"
        if self.current_file_path:
            filename = os.path.basename(self.current_file_path)
            
        modified_marker = "*" if self._is_modified else ""
        # Update the root window's title
        #! self.root.title(f"{modified_marker}{filename} - PyEdit")

    def _on_text_modified(self, event=None):
        """Callback when the text widget content is modified."""
        try:
            if self.text_editor.text.edit_modified():
                self._set_modified(True)
        except tk.TclError:
            pass 
        
        self.text_editor.text.edit_modified(False)
        
        if self._find_dialog and self._find_dialog.winfo_viewable():
            self._find_dialog._highlight_all_matches()
        
        self._update_all_ui()

    def update_status_bar(self):
        """Updates the cursor position in the status bar."""
        try:
            line, col = self.text_editor.text.index(tk.INSERT).split('.')
            self.status_bar.set_cursor_pos(f"Ln: {line}, Col: {int(col) + 1}")
        except tk.TclError:
            pass 
            
    def _update_all_ui(self, event=None):
        """
        Calls all UI update functions.
        """
        self.update_status_bar()
        self.text_editor.highlight_current_line()
        self.text_editor.update_line_numbers()
        self._update_title()
        self._highlight_current_find_match()
        
    # --- Selection Highlighting Methods ---

    def _on_selection_change(self, event=None):
        """
        Schedules a highlight update when the text selection changes.
        """
        if self._selection_job:
            self.after_cancel(self._selection_job)
        self._selection_job = self.after(150, self._do_selection_highlight)

    def _do_selection_highlight(self):
        """
        Performs the actual highlighting of all instances of the selected text.
        """
        self.text_editor.text.tag_remove("selection_match", "1.0", tk.END)
        
        selected_text = ""
        try:
            selected_text = self.text_editor.text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            self.status_bar.set_match_count("")
            return

        if not selected_text or "\n" in selected_text or len(selected_text) > 100:
            self.status_bar.set_match_count("")
            return

        pattern = rf"\b{re.escape(selected_text)}\b"
        start_index = "1.0"
        count = 0
        
        try:
            sel_start = self.text_editor.text.index(tk.SEL_FIRST)
            sel_end = self.text_editor.text.index(tk.SEL_LAST)
        except tk.TclError:
            sel_start, sel_end = None, None

        while True:
            pos = self.text_editor.text.search(
                pattern, start_index, nocase=False, regexp=True, stopindex=tk.END
            )
            if not pos:
                break
            end_pos = f"{pos}+{len(selected_text)}c"
            
            if pos != sel_start and end_pos != sel_end:
                self.text_editor.text.tag_add("selection_match", pos, end_pos)
                count += 1
            
            start_index = end_pos

        if count > 0:
            self.status_bar.set_match_count(f"{count + 1} selection matches")
        else:
            self.status_bar.set_match_count("")

    # --- Current Find-Match Highlighting Method ---
    def _highlight_current_find_match(self, event=None):
        """
        Highlights the *specific* "find_match" (yellow) tag 
        that the insertion cursor is currently inside.
        """
        self.text_editor.text.tag_remove("current_find_match", "1.0", tk.END)

        try:
            tags_at_cursor = self.text_editor.text.tag_names(tk.INSERT)
        except tk.TclError:
            return 

        if "find_match" in tags_at_cursor:
            
            found_range = self.text_editor.text.tag_prevrange(
                "find_match", f"{tk.INSERT}+1c"
            )

            if found_range:
                range_start, range_end = found_range
                
                if self.text_editor.text.compare(tk.INSERT, ">=", range_start):
                
                    self.text_editor.text.tag_add("current_find_match", 
                                                 range_start, range_end)
                    
                    self.text_editor.text.tag_raise("current_find_match", "find_match")
                    try:
                        self.text_editor.text.tag_lower("current_find_match", "sel")
                    except tk.TclError:
                        pass
    
        
# --- Text Editor Frame ---

class TextEditor(ttk.Frame):
    """
    A frame containing the core text editor components:
    - LineNumberPanel (Canvas)
    - Text (tk.Text)
    - Vertical Scrollbar (ttk.Scrollbar)
    """
    
    def __init__(self, master, font, *args, **kwargs):
        """Initializes the TextEditor frame."""
        super().__init__(master, *args, **kwargs)
        self.master = master
        
        # --- Create Widgets ---
        self.v_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        
        
        self.text = tk.Text(
            self,
            undo=True,
            maxundo=-1,
            autoseparators=True,
            font=font,
            bd=0,
            highlightthickness=0,
            yscrollcommand=self._on_text_scroll,
            xscrollcommand=self.h_scroll.set,
            wrap=tk.NONE,
            padx=5,
            pady=2
        )
        
        self.line_numbers = LineNumberPanel(self, width=45, font=font)
        
        # --- Configure Scrollbar ---
        self.v_scroll.config(command=self._on_scrollbar_yview)
        self.h_scroll.config(command=self.text.xview)
        
        
        # --- Layout ---
        # self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        # self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        # self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # Make the main text column (1) and row (0) expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.line_numbers.grid(row=0, column=0, sticky="ns")
        self.text.grid(row=0, column=1, sticky="nsew")
        self.v_scroll.grid(row=0, column=2, sticky="ns")
        self.h_scroll.grid(row=1, column=1, sticky="ew")
        
        # --- Event Bindings ---
        self.text.bind("<KeyRelease>", self.master._update_all_ui)
        self.text.bind("<ButtonRelease-1>", self.master._update_all_ui)
        self.text.bind("<Configure>", self.master._update_all_ui)
        self.text.bind("<MouseWheel>", self._on_mouse_wheel)
        self.text.bind("<Control-MouseWheel>", self._on_ctrl_mouse_wheel)
        self.text.bind("<Shift-MouseWheel>", self._on_shift_mouse_wheel)

        self._line_update_job = None

    def _on_text_scroll(self, first, last):
        """Handles scrolling of the text widget."""
        self.v_scroll.set(first, last)
        self.line_numbers.yview_moveto(first)
        self.master._update_all_ui()

    def _on_scrollbar_yview(self, *args):
        """Handles scrolling of the vertical scrollbar."""
        self.text.yview(*args)
        
        
    def _on_mouse_wheel(self, event):
        """Handles standard mouse wheel scrolling."""
        # On Windows/macOS, event.delta is +/- 120
        # On Linux, event.num is 4 or 5
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = -1 * (event.delta // 120)
            
        self.text.yview_scroll(delta, "units")
        # self.line_numbers.yview_scroll(delta, "units")
        return "break" # Prevents default scroll
    
    def _on_shift_mouse_wheel(self, event):
        """Handles horizontal scrolling with Shift+MouseWheel."""
        # On Windows/macOS, event.delta is +/- 120
        # On Linux, event.num is 4 or 5
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = -1 * (event.delta // 120)
            
        self.text.xview_scroll(delta, "units")
        return "break" # Prevents default scroll
        
    def _on_ctrl_mouse_wheel(self, event):
        """Handles zoom-in/out via Ctrl+MouseWheel."""
        if event.delta > 0:
            self.master._view_zoom_in()
        else:
            self.master._view_zoom_out()
        return "break" # Prevents default scroll action
    


    def highlight_current_line(self):
            """Applies a tag to highlight the line with the insertion cursor."""
            self.text.tag_remove("current_line", "1.0", tk.END)
            
            # Add the tag to the new line
            self.text.tag_add("current_line", "insert linestart", "insert lineend+1c")
            
            # --- THIS IS THE FIX ---
            # Lower the tag's priority so the 'sel' (selection) tag
            # will be drawn on top of it, making selection visible.
            try:
                self.text.tag_lower("current_line", "sel")
            except tk.TclError:
                # This can happen if the 'sel' tag doesn't exist yet
                pass

    def update_line_numbers(self):
        """
        Schedules a redraw of the line number panel.
        Uses `after` to "debounce" redraws during rapid typing.
        """
        if self._line_update_job:
            self.after_cancel(self._line_update_job)
        
        self._line_update_job = self.after(50, self.line_numbers.redraw)

    def toggle_line_numbers(self, show):
        """Shows or hides the line number panel."""
        if show:
            self.line_numbers.grid(row=0, column=0, sticky="ns")
        else:
            self.line_numbers.grid_forget()

# --- Line Number Panel ---

class LineNumberPanel(tk.Canvas):
    """
    A custom widget (Canvas) to display line numbers that
    scroll in sync with the main Text widget.
    """
    
    def __init__(self, master, font, *args, **kwargs):
        """Initializes the LineNumberPanel."""
        super().__init__(master, *args, **kwargs)
        self.text_widget = master.text
        self._font = font
        self._bg_color = "#F0F0F0"
        self._fg_color = "#6E6E6E"
        self.config(width=45, bd=0, highlightthickness=0)

    def set_font(self, font):
        """Sets the font for the line numbers."""
        self._font = font
        self.redraw()
        
    def set_colors(self, bg, fg):
        """Sets the background and foreground colors."""
        self._bg_color = bg
        self._fg_color = fg
        self.config(background=bg)
        self.redraw()

    def redraw(self, *args):
        """
        Redraws the line numbers. This is the core logic.
        
        It calculates which lines are visible in the text widget
        and draws the corresponding numbers on the canvas.
        """
        self.delete("all")
        
        try:
            # Get the index of the first visible line
            first_line_index = self.text_widget.index("@0,0")
            
            # Get the y-position of the first visible line
            dline = self.text_widget.dlineinfo(first_line_index)
            if dline is None:
                return # No text
            
            y_pos = dline[1]
            line_num_str = first_line_index.split('.')[0]
            
            # Loop as long as lines are visible
            while True:
                # Get line info (x, y, width, height, baseline)
                dline = self.text_widget.dlineinfo(f"{line_num_str}.0")
                
                if dline is None:
                    break # Reached end of visible area
                    
                y = dline[1]
                
                # Check if line is outside the visible canvas area
                if y > self.winfo_height():
                    break
                    
                # Draw the line number
                self.create_text(
                    40,  # x-position (right-aligned)
                    y,
                    anchor="ne",
                    text=line_num_str,
                    fill=self._fg_color,
                    font=self._font
                )
                
                # Move to the next line
                line_num_str = str(int(line_num_str) + 1)
                
        except tk.TclError:
            pass # Error (e.g., widget destroyed)

# --- Status Bar ---

class StatusBar(ttk.Frame):
    """
    The application status bar, displaying cursor position,
    zoom level, encoding, and other info.
    """
    
    def __init__(self, master, *args, **kwargs):
        """Initializes the StatusBar."""
        super().__init__(master, style="StatusBar.TFrame", *args, **kwargs)
        
        # --- Left Side ---
        self.left_frame = ttk.Frame(self, style="StatusBar.TFrame")
        self.left_frame.pack(side=tk.LEFT, padx=5)
        
        self.cursor_pos_label = ttk.Label(self.left_frame, text="Ln: 1, Col: 1")
        self.cursor_pos_label.pack(side=tk.LEFT, padx=10)
        
        self.match_count_label = ttk.Label(self.left_frame, text="")
        self.match_count_label.pack(side=tk.LEFT, padx=10)
        
        # --- Right Side ---
        self.right_frame = ttk.Frame(self, style="StatusBar.TFrame")
        self.right_frame.pack(side=tk.RIGHT, padx=5)
        
        self.tab_width_label = ttk.Label(self.right_frame, text="Tabs: 4")
        self.tab_width_label.pack(side=tk.RIGHT, padx=10)
        
        self.zoom_label = ttk.Label(self.right_frame, text="100%")
        self.zoom_label.pack(side=tk.RIGHT, padx=10)
        
        self.encoding_label = ttk.Label(self.right_frame, text="UTF-8")
        self.encoding_label.pack(side=tk.RIGHT, padx=10)

    def set_cursor_pos(self, text):
        self.cursor_pos_label.config(text=text)

    def set_zoom(self, text):
        self.zoom_label.config(text=text)
        
    def set_encoding(self, text):
        self.encoding_label.config(text=text)

    def set_tab_width(self, text):
        self.tab_width_label.config(text=text)
        
    def set_match_count(self, text):
        self.match_count_label.config(text=text)
        
# --- Find/Replace Dialog ---

class FindReplaceDialog(tk.Toplevel):
    """
    A floating dialog window for Find and Replace operations.
    Communicates directly with the Text widget.
    """
    
    def __init__(self, master, text_widget, *args, **kwargs):
        """Initializes the Find/Replace dialog."""
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.text_widget = text_widget
        
        self.title("Find / Replace")
        self.transient(master)
        self.resizable(False, False)
        
        # --- STATE VARIABLES ---
        self.match_list = [] # Stores (start, end) of all matches
        self.current_match_index = -1 # 0-based index of current match
        
        # --- Variables ---
        self.find_var = tk.StringVar()
        self.replace_var = tk.StringVar()
        self.match_case = tk.BooleanVar()
        self.whole_word = tk.BooleanVar()
        self.regex = tk.BooleanVar()
        self.wrap_around = tk.BooleanVar(value=True)
        
        # --- Main Frame ---
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Input Fields ---
        find_frame = ttk.Frame(main_frame)
        find_frame.grid(row=0, column=0, sticky="ew", pady=5)
        ttk.Label(find_frame, text="Find:", width=10).pack(side=tk.LEFT)
        self.find_entry = ttk.Entry(find_frame, textvariable=self.find_var)
        self.find_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.find_entry.bind("<Return>", self._on_find_entry_return)
        
        replace_frame = ttk.Frame(main_frame)
        replace_frame.grid(row=1, column=0, sticky="ew", pady=5)
        ttk.Label(replace_frame, text="Replace:", width=10).pack(side=tk.LEFT)
        self.replace_entry = ttk.Entry(replace_frame, textvariable=self.replace_var)
        self.replace_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # --- Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=1, rowspan=2, sticky="ns", padx=(10, 0))
        
        ttk.Button(button_frame, text="Find Next", command=self._find_next).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Find Previous", command=self._find_prev).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Replace", command=self._replace).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Replace All", command=self._replace_all).pack(fill=tk.X, pady=2)
        
        # --- Options ---
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        
        ttk.Checkbutton(options_frame, text="Match Case", variable=self.match_case, command=self._highlight_all_matches).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(options_frame, text="Whole Word", variable=self.whole_word, command=self._highlight_all_matches).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(options_frame, text="Regex", variable=self.regex, command=self._highlight_all_matches).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(options_frame, text="Wrap Around", variable=self.wrap_around, command=self._highlight_all_matches).pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=5, padx=5)
        
        # --- Bindings ---
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.find_var.trace_add("write", self._highlight_all_matches)
        self.find_var.trace_add("write", self._on_find_text_changed)
        
        # Initial highlighting
        self._highlight_all_matches()

    def _on_close(self):
        """Hides the window and clears highlights on close."""
        self.text_widget.tag_remove("find_match", "1.0", tk.END)
        self.master.status_bar.set_match_count("")
        self.master._find_dialog = None # Allow to be garbage collected
        self.destroy()

    def _search(self, pattern, start_index, backwards=False, wrap=False):
        """
        Core search logic for the text widget.
        Returns (start_pos, end_pos) or (None, None).
        """
        is_regex = self.regex.get()
        is_nocase = not self.match_case.get()
        is_whole_word = self.whole_word.get()
        
        if is_whole_word and not is_regex:
            pattern = rf"\b{re.escape(pattern)}\b"
            is_regex = True
            
        count_var = tk.IntVar()
        
        while True:
            pos = self.text_widget.search(
                pattern,
                start_index,
                backwards=backwards,
                nocase=is_nocase,
                regexp=is_regex,
                count=count_var,
                stopindex="1.0" if backwards else tk.END
            )
            
            if not pos:
                if wrap and self.wrap_around.get():
                    start_index = tk.END if backwards else "1.0"
                    wrap = False # Only wrap once
                    continue
                else:
                    return None, None
            
            # search() returns the start index
            # count_var.get() gives the length of the match
            end_pos = f"{pos}+{count_var.get()}c"
            return pos, end_pos

    def _find_next(self, wrap=True):
        """Finds the next occurrence of the search term."""
        pattern = self.find_var.get()
        if not pattern:
            return
            
        start_index = self.text_widget.index(tk.INSERT)
        start_pos, end_pos = self._search(
            pattern,
            f"{start_index}+1c",  # Start search 1 char *after* the cursor
            wrap=wrap
        )
        
        if start_pos and end_pos:
            self._select_match(start_pos, end_pos)
        else:
            messagebox.showinfo("Not Found", "No more matches found.", parent=self)
    
    def _on_find_entry_return(self, event=None):
        """Handles pressing Enter in the Find box."""
        self._find_next()
        # This manually gives focus back to the find entry box.
        self.find_entry.focus_set()
        return "break" # Prevents the default "ding" sound
    
    def _find_prev(self):
        """Finds the previous occurrence of the search term."""
        pattern = self.find_var.get()
        if not pattern:
            return
            
        start_pos, end_pos = self._search(
            pattern,
            self.text_widget.index(tk.INSERT),
            backwards=True,
            wrap=True
        )
        
        if start_pos and end_pos:
            self._select_match(start_pos, end_pos)
        else:
            messagebox.showinfo("Not Found", "No more matches found.", parent=self)

    def _replace(self):
        """Replaces the currently selected match and finds the next."""
        try:
            sel_start = self.text_widget.index(tk.SEL_FIRST)
            sel_end = self.text_widget.index(tk.SEL_LAST)
            selected_text = self.text_widget.get(sel_start, sel_end)
        except tk.TclError:
            # No selection, just find next
            self._find_next()
            return

        find_pattern = self.find_var.get()
        replace_text = self.replace_var.get()
        
        matches = False
        if self.regex.get():
            matches = True 
        elif self.match_case.get():
            matches = (selected_text == find_pattern)
        else:
            matches = (selected_text.lower() == find_pattern.lower())
            
        if matches:
            # --- THIS IS THE NEW, FIXED LOGIC ---
            
            self.text_widget.delete(sel_start, sel_end)
            self.text_widget.insert(sel_start, replace_text)
            
            # Get the position *after* the replacement
            new_cursor_pos = self.text_widget.index(tk.INSERT)
            
            # Re-run the search on the entire document, as all
            # match indices are now invalid. This rebuilds self.match_list.
            self._highlight_all_matches()
            
            # Restore the cursor to its correct spot
            self.text_widget.mark_set(tk.INSERT, new_cursor_pos)
            
            # Now, find the next valid match from our new position
            self.text_widget.focus_set()
            self._find_next(wrap=False)
            
            # --- END OF NEW LOGIC ---
        else:
            # No match, just find the next one from the cursor
            self._find_next()

    def _replace_all(self):
        """Replaces all occurrences in the document."""
        find_pattern = self.find_var.get()
        replace_text = self.replace_var.get()
        
        if not find_pattern:
            return
            
        content = self.text_widget.get("1.0", tk.END)
        count = 0
        
        try:
            if self.regex.get():
                flags = 0
                if not self.match_case.get():
                    flags = re.IGNORECASE
                new_content, count = re.subn(find_pattern, replace_text, content, flags=flags)
            
            else:
                pattern_to_search = find_pattern
                if self.whole_word.get():
                    pattern_to_search = rf"\b{re.escape(find_pattern)}\b"
                
                flags = 0
                if not self.match_case.get():
                    flags = re.IGNORECASE
                    
                new_content, count = re.subn(pattern_to_search, replace_text, content, flags=flags)

        except re.error as e:
            messagebox.showerror("Regex Error", f"Invalid regular expression: {e}", parent=self)
            return

        if count > 0:
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", new_content)
            self.master._on_text_modified() # Trigger modified flag
            
        # --- THIS IS THE NEW MESSAGE LOGIC ---
        message = f"{count} replacements made."
        messagebox.showinfo(
            "Replace All",
            message,
            parent=self
        )
        
        # Also update our status labels
        self.master.status_bar.set_match_count(message)
        self.status_label.config(text=message, foreground="green") # Use 'green' for success
        # --- END OF NEW LOGIC ---
        
        self._highlight_all_matches() # Re-highlight

    def _highlight_all_matches(self, *args):
        """
        Applies 'find_match' tag to all results and builds the match list.
        """
        
        #This clears the special cursor-hover highlight
        # to prevent a stale highlight from remaining.
        self.text_widget.tag_remove("current_find_match", "1.0", tk.END)
        
        
        self.text_widget.tag_remove("find_match", "1.0", tk.END)
        
        # Explicitly lower the 'find_match' tag priority below 'sel'.
        # This ensures 'sel' (the blue selection) always draws on top.
        try:
            self.text_widget.tag_lower("find_match", "sel")
        except tk.TclError:
            pass # 'sel' tag might not exist yet, which is fine
        
        
        # --- MODIFIED LOGIC ---
        self.match_list.clear()
        self.current_match_index = -1
        
        pattern = self.find_var.get()
        if not pattern:
            self._update_match_status() # Clears the labels
            return
            
        start_index = "1.0"
        count = 0
        while True:
            start_pos, end_pos = self._search(
                pattern, start_index, wrap=False
            )
            
            if not start_pos:
                break
                
            self.text_widget.tag_add("find_match", start_pos, end_pos)
            
            # --- ADD THIS ---
            # Add the found match (start, end) to our list
            self.match_list.append((start_pos, end_pos))
            # --- END ---
            
            count += 1
            start_index = end_pos
            
        # Call the new status updater instead of the old status bar
        self._update_match_status()

    def _select_match(self, start_pos, end_pos):
        """Selects a found match and brings it into view."""
        self.text_widget.tag_remove(tk.SEL, "1.0", tk.END)
        self.text_widget.tag_add(tk.SEL, start_pos, end_pos)
        self.text_widget.mark_set(tk.INSERT, start_pos)
        self.text_widget.see(start_pos)
        self.text_widget.focus_set()
        self.master._update_all_ui()
        
        # Find the index of this match in our list
        try:
            self.current_match_index = self.match_list.index((start_pos, end_pos))
        except ValueError:
            self.current_match_index = -1 # Should not happen
            
        # Manually force the TextEditorWidget to update its UI (for current-match)
        self.master._update_all_ui()
        
        # Now that we have a new index, update the "X of Y" labels
        self._update_match_status()
      
    def _on_find_text_changed(self, *args):
        """Callback for when the find text entry changes."""
        self._highlight_all_matches()
        
    def _update_match_status(self):
        """
        Updates the "X of Y matches" status label in the dialog
        and in the main application status bar.
        """
        total_matches = len(self.match_list)
        pattern = self.find_var.get()

        # --- Handle "No Result" ---
        if total_matches == 0:
            if pattern:
                # Only show "No results" if user has typed something
                message = "No results found"
                # Configure the local label to be red
                self.status_label.config(text=message, foreground="red")
                self.master.status_bar.set_match_count(message)
            else:
                # Clear all messages if find box is empty
                self.status_label.config(text="", foreground="")
                self.master.status_bar.set_match_count("")
            return

        # --- Handle "X of Y" ---
        # Reset color from red (if it was)
        self.status_label.config(foreground="")
        
        if self.current_match_index == -1:
            # No specific match is *selected*, just show total
            message = f"{total_matches} matches"
        else:
            # A match is selected (e.g., "5 of 10")
            # We add 1 for a 1-based display
            message = f"{self.current_match_index + 1} of {total_matches} matches"

        # Update both labels
        self.status_label.config(text=message)
        self.master.status_bar.set_match_count(message)


# --- Application Entry Point ---
if __name__ == "__main__":
    root = tk.Tk()
    
    a = ttk.Frame(root)
    a.pack(fill=tk.BOTH, expand=True)
    
    TextEditorWidget(a)
    
    # test_canvas = tk.Canvas(root, bd=0, highlightthickness=0,  )
    # test_canvas.pack(fill=tk.BOTH, expand=True)
    # test_frame = ttk.Frame(test_canvas)
    # test_canvas.create_window((0, 0), window=test_frame, anchor="nw")
    # TextEditorWidget(test_frame)
    # FindReplaceDemo(parent=test_canvas)
    
    root.mainloop()