"""tk_text_editor.py

A professional, modular Tkinter Text Editor inspired by Notepad++ features.
Single-file runnable example with OOP structure.

Main classes:
- MainApp
- EditorFrame
- FindReplaceDialog
- StatusBar
- LineNumberPanel
- MenuBar
- SettingsManager

Notes:
- Uses only tkinter and ttk (standard library).
- Settings persisted to JSON in user's home directory (~/.tk_text_editor_settings.json).
- Designed for clarity and extensibility (e.g. plugin/syntax hooks).

Run: python tk_text_editor.py

"""

from __future__ import annotations
import json
import os
import sys
import platform
import re
import codecs
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, List, Dict

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, simpledialog
except Exception as exc:  # pragma: no cover - fails only in unusual envs
    raise RuntimeError("tkinter is required to run this application") from exc

APP_NAME = "TkProEdit"
SETTINGS_FILENAME = os.path.join(Path.home(), f".{APP_NAME.lower()}_settings.json")


# ---------------------------- Settings Manager ---------------------------
class SettingsManager:
    """Persist and manage user settings.

    Settings stored as JSON in the user's home directory.
    """

    DEFAULTS = {
        "theme": "clam",
        "font_family": "Consolas" if platform.system() == "Windows" else "Courier",
        "font_size": 12,
        "tab_width": 4,
        "show_line_numbers": True,
        "wrap": False,
        "recent_files": [],
        "max_recent": 8,
        "highlight_current_line": True,
        "show_indent_guides": False,
    }

    def __init__(self, path: Optional[str] = None):
        self.path = path or SETTINGS_FILENAME
        self._data = dict(self.DEFAULTS)
        self.load()

    def load(self) -> None:
        """Load settings from JSON if available."""
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._data.update(data)
        except Exception:
            # robust: ignore malformed settings
            pass

    def save(self) -> None:
        """Save current settings to JSON."""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    def get(self, key: str):
        return self._data.get(key, self.DEFAULTS.get(key))

    def set(self, key: str, value) -> None:
        self._data[key] = value

    def add_recent(self, path: str) -> None:
        if not path:
            return
        recent: List[str] = self._data.get("recent_files", [])
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        recent = recent[: self._data.get("max_recent", 8)]
        self._data["recent_files"] = recent


# ---------------------------- Utility Helpers ---------------------------

def guess_encoding(path: str) -> str:
    """Try to guess file encoding; fallback to utf-8."""
    # naive but practical approach
    try:
        import chardet  # optional, not required

        with open(path, "rb") as f:
            raw = f.read(8192)
            result = chardet.detect(raw)
            if result and result.get("encoding"):
                return result["encoding"]
    except Exception:
        pass
    # fallback heuristics
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            with codecs.open(path, "r", encoding=enc) as f:
                f.read(2048)
            return enc
        except Exception:
            continue
    return "utf-8"


# ---------------------------- Line Number Panel -------------------------
class LineNumberPanel(ttk.Frame):
    """A panel that displays dynamic line numbers for a Text widget."""

    def __init__(self, master, text_widget: tk.Text, **kwargs):
        super().__init__(master, **kwargs)
        self.text = text_widget
        self.canvas = tk.Canvas(self, width=48, highlightthickness=0)
        self.canvas.pack(fill=tk.Y, expand=True, side=tk.RIGHT)
        self.text.bind("<<Change>>", self._on_change)
        self.text.bind("<Configure>", self._on_change)
        self.text.bind("<Motion>", self._on_change)
        self.redraw()

    def _on_change(self, *args):
        self.after_idle(self.redraw)

    def redraw(self):
        """Redraw line numbers. Efficient: only draw visible lines."""
        self.canvas.delete("all")
        i = self.text.index("@0,0")
        while True:
            dline = self.text.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            lineno = str(i).split(".")[0]
            self.canvas.create_text(44, y, anchor="ne", text=lineno, font=("Consolas", 10))
            i = self.text.index(f"{i}+1line")


# ---------------------------- Status Bar --------------------------------
class StatusBar(ttk.Frame):
    """StatusBar that shows cursor position, zoom, encoding and match info."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.cursor_var = tk.StringVar(value="Ln 1, Col 0")
        self.zoom_var = tk.StringVar(value="100%")
        self.enc_var = tk.StringVar(value="utf-8")
        self.match_var = tk.StringVar(value="")

        self.cursor_label = ttk.Label(self, textvariable=self.cursor_var, anchor="w")
        self.cursor_label.pack(side=tk.LEFT, padx=6)
        self.zoom_label = ttk.Label(self, textvariable=self.zoom_var)
        self.zoom_label.pack(side=tk.LEFT, padx=6)
        self.enc_label = ttk.Label(self, textvariable=self.enc_var)
        self.enc_label.pack(side=tk.LEFT, padx=6)
        self.match_label = ttk.Label(self, textvariable=self.match_var)
        self.match_label.pack(side=tk.RIGHT, padx=6)

    def update_cursor(self, line: int, col: int):
        self.cursor_var.set(f"Ln {line}, Col {col}")

    def set_zoom(self, percent: int):
        self.zoom_var.set(f"{percent}%")

    def set_encoding(self, enc: str):
        self.enc_var.set(enc)

    def set_match_info(self, current: int, total: int):
        if total == 0:
            self.match_var.set("")
        else:
            self.match_var.set(f"Match {current}/{total}")


# ---------------------------- Find / Replace -----------------------------
class FindReplaceDialog(tk.Toplevel):
    """Floating find/replace dialog with options and live highlight.

    Uses Text widget tags in the target editor to highlight matches.
    """

    def __init__(
        self,
        master,
        editor: 'EditorFrame',
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.title("Find & Replace")
        self.editor = editor
        self.transient(master)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.hide)

        # variables
        self.find_var = tk.StringVar()
        self.replace_var = tk.StringVar()
        self.match_case = tk.BooleanVar(value=False)
        self.match_whole = tk.BooleanVar(value=False)
        self.use_regex = tk.BooleanVar(value=False)
        self.wrap_around = tk.BooleanVar(value=True)
        self.include_whitespace_chars = tk.BooleanVar(value=True)

        # build UI
        frm = ttk.Frame(self)
        frm.pack(padx=8, pady=8, fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Find:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.find_var, width=40).grid(row=0, column=1, columnspan=3, sticky="we")

        ttk.Label(frm, text="Replace:").grid(row=1, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.replace_var, width=40).grid(row=1, column=1, columnspan=3, sticky="we")

        # options
        ttk.Checkbutton(frm, text="Match case", variable=self.match_case).grid(row=2, column=0)
        ttk.Checkbutton(frm, text="Whole word", variable=self.match_whole).grid(row=2, column=1)
        ttk.Checkbutton(frm, text="Regex", variable=self.use_regex).grid(row=2, column=2)
        ttk.Checkbutton(frm, text="Wrap", variable=self.wrap_around).grid(row=2, column=3)
        ttk.Checkbutton(frm, text="Include \n\t\r", variable=self.include_whitespace_chars).grid(row=3, column=0, columnspan=2)

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=4, column=0, columnspan=4, pady=(6, 0))
        ttk.Button(btn_frame, text="Find Next", command=self.find_next).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Find Prev", command=self.find_prev).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Replace", command=self.replace_one).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Replace All", command=self.replace_all).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Close", command=self.hide).pack(side=tk.LEFT, padx=3)

        # binds
        self.find_var.trace_add("write", lambda *a: self.highlight_all())
        self.bind("<Escape>", lambda e: self.hide())

        # internal
        self._matches: List[Tuple[str, str]] = []
        self._current_index = -1

    def show(self):
        self.deiconify()
        self.lift()
        self.find_var.set(self.editor.get_selection_or_word())
        self.highlight_all()

    def hide(self):
        self.withdraw()
        self.editor.clear_find_highlight()

    def _build_pattern(self, text: str) -> Tuple[str, int]:
        flags = 0
        if not self.match_case.get():
            flags |= re.IGNORECASE
        pattern = text
        if not self.include_whitespace_chars.get():
            # treat \n and \t as plain text instead of patterns
            pattern = pattern.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")
        if not self.use_regex.get():
            pattern = re.escape(pattern)
        if self.match_whole.get():
            pattern = r"\b" + pattern + r"\b"
        return pattern, flags

    def highlight_all(self):
        self.editor.clear_find_highlight()
        find_text = self.find_var.get()
        if not find_text:
            self.editor.statusbar.set_match_info(0, 0)
            return
        pattern, flags = self._build_pattern(find_text)
        try:
            regex = re.compile(pattern, flags)
        except re.error:
            # invalid regex
            self.editor.statusbar.set_match_info(0, 0)
            return
        text = self.editor.get_text()
        matches = list(regex.finditer(text))
        for m in matches:
            start = self.editor.index_to_text_index(m.start())
            end = self.editor.index_to_text_index(m.end())
            self.editor.highlight_range(start, end)
        self._matches = [(m.start(), m.end()) for m in matches]
        self._current_index = 0 if matches else -1
        self.editor.statusbar.set_match_info(self._current_index + 1 if self._current_index >= 0 else 0, len(matches))

    def find_next(self):
        if not self._matches:
            self.highlight_all()
            return
        self._current_index = (self._current_index + 1) % len(self._matches)
        s, e = self._matches[self._current_index]
        start = self.editor.index_to_text_index(s)
        end = self.editor.index_to_text_index(e)
        self.editor.select_range(start, end)
        self.editor.statusbar.set_match_info(self._current_index + 1, len(self._matches))
        self.editor.see_index(start)

    def find_prev(self):
        if not self._matches:
            self.highlight_all()
            return
        self._current_index = (self._current_index - 1) % len(self._matches)
        s, e = self._matches[self._current_index]
        start = self.editor.index_to_text_index(s)
        end = self.editor.index_to_text_index(e)
        self.editor.select_range(start, end)
        self.editor.statusbar.set_match_info(self._current_index + 1, len(self._matches))
        self.editor.see_index(start)

    def replace_one(self):
        if self._current_index < 0 or not self._matches:
            return
        s, e = self._matches[self._current_index]
        start = self.editor.index_to_text_index(s)
        end = self.editor.index_to_text_index(e)
        self.editor.replace_range(start, end, self.replace_var.get())
        self.highlight_all()

    def replace_all(self):
        find_text = self.find_var.get()
        if not find_text:
            return
        pattern, flags = self._build_pattern(find_text)
        try:
            regex = re.compile(pattern, flags)
        except re.error:
            messagebox.showerror("Invalid regex", "The search pattern is not a valid regular expression.")
            return
        text = self.editor.get_text()
        new_text, count = regex.subn(self.replace_var.get(), text)
        self.editor.replace_all(new_text)
        messagebox.showinfo("Replace All", f"{count} replacements made")
        self.highlight_all()


# ---------------------------- Editor Frame -------------------------------
class EditorFrame(ttk.Frame):
    """Core editor area containing a Text widget and helpers for tags and events."""

    def __init__(self, master, settings: SettingsManager, **kwargs):
        super().__init__(master, **kwargs)
        self.settings = settings
        self.font_family = settings.get("font_family")
        self.font_size = settings.get("font_size")

        # Scrollbar + Text
        self.yscroll = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.xscroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.text = tk.Text(
            self,
            wrap=tk.NONE if not settings.get("wrap") else tk.WORD,
            undo=True,
            autoseparators=True,
            maxundo=-1,
            yscrollcommand=self.yscroll.set,
            xscrollcommand=self.xscroll.set,
            font=(self.font_family, self.font_size),
            relief=tk.FLAT,
            insertwidth=2,
        )
        self.yscroll.config(command=self.text.yview)
        self.xscroll.config(command=self.text.xview)
        self.yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.xscroll.pack(side=tk.BOTTOM, fill=tk.X)

        # line numbers panel (optional)
        self.linenumber_panel = LineNumberPanel(self, self.text)
        if self.settings.get("show_line_numbers"):
            self.linenumber_panel.pack(side=tk.LEFT, fill=tk.Y)

        self.text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Tags
        self.text.tag_configure("current_line", background="#f2f2f2")
        self.text.tag_configure("find_match", background="#fff59d")

        # events
        self.text.bind("<Key>", self._on_key)
        self.text.bind("<Button-1>", lambda e: self.after_idle(self._update_cursor))
        self.text.bind("<Motion>", lambda e: self.after_idle(self._update_cursor))
        self.text.bind("<MouseWheel>", self._on_mousewheel)
        self.text.bind("<Control-MouseWheel>", self._on_ctrl_mousewheel)
        self.text.bind("<<Modified>>", self._on_modified)

        # custom virtual event for changes used by LineNumberPanel
        self.text.bind("<Any-KeyPress>", lambda e: self.text.event_generate("<<Change>>", when="tail"))

        # state
        self.filepath: Optional[str] = None
        self.encoding = "utf-8"
        self.dirty = False

        # statusbar reference added later
        self.statusbar: Optional[StatusBar] = None

        # find dialog
        self.find_dialog = FindReplaceDialog(self.master, self)

        # keybindings
        self._setup_bindings()

    # ------------------------- file & text helpers -------------------------
    def load_file(self, path: str):
        enc = guess_encoding(path)
        try:
            with codecs.open(path, "r", encoding=enc, errors="replace") as f:
                content = f.read()
            self.set_text(content)
            self.filepath = path
            self.encoding = enc
            self.dirty = False
            if self.statusbar:
                self.statusbar.set_encoding(enc)
            self.settings.add_recent(path)
            self.settings.save()
        except Exception as exc:
            messagebox.showerror("Open Error", f"Failed to open file:\n{exc}")

    def save_file(self, path: Optional[str] = None):
        path = path or self.filepath
        if not path:
            return False
        text = self.get_text()
        try:
            with codecs.open(path, "w", encoding=self.encoding or "utf-8") as f:
                f.write(text)
            self.filepath = path
            self.dirty = False
            self.settings.add_recent(path)
            self.settings.save()
            return True
        except Exception as exc:
            messagebox.showerror("Save Error", f"Failed to save file:\n{exc}")
            return False

    def get_text(self) -> str:
        return self.text.get("1.0", "end-1c")

    def set_text(self, data: str) -> None:
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, data)
        self.text.edit_reset()
        self._update_cursor()

    def replace_all(self, new_text: str) -> None:
        self.set_text(new_text)

    # ------------------------- selection helpers ---------------------------
    def get_selection_or_word(self) -> str:
        try:
            return self.text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            idx = self.text.index(tk.INSERT)
            word_start = self.text.index(f"{idx} wordstart")
            word_end = self.text.index(f"{idx} wordend")
            return self.text.get(word_start, word_end)

    def index_to_text_index(self, idx: int) -> str:
        """Convert absolute character offset to Tkinter index like '1.0'."""
        return self.text.index(f"1.0+{idx}c")

    def text_index_to_offset(self, index: str) -> int:
        """Convert Tkinter index to absolute character offset."""
        return int(self.text.index(index).split(".")[0]) * 0  # placeholder; prefer using search-based ops

    def replace_range(self, start: str, end: str, content: str):
        self.text.delete(start, end)
        self.text.insert(start, content)

    def select_range(self, start: str, end: str):
        self.text.tag_remove(tk.SEL, "1.0", tk.END)
        self.text.tag_add(tk.SEL, start, end)
        self.text.mark_set(tk.INSERT, end)
        self.text.see(start)

    # ------------------------- highlight helpers ---------------------------
    def highlight_range(self, start: str, end: str):
        self.text.tag_add("find_match", start, end)

    def clear_find_highlight(self):
        self.text.tag_remove("find_match", "1.0", tk.END)

    def clear_current_line_highlight(self):
        self.text.tag_remove("current_line", "1.0", tk.END)

    def highlight_current_line(self):
        if not self.settings.get("highlight_current_line"):
            return
        self.clear_current_line_highlight()
        idx = self.text.index(tk.INSERT)
        line = idx.split(".")[0]
        self.text.tag_add("current_line", f"{line}.0", f"{line}.end")

    # ------------------------- event handlers ------------------------------
    def _on_key(self, event):
        self.text.event_generate("<<Change>>", when="tail")
        self._update_cursor()

    def _on_modified(self, event=None):
        # Text widget sets modified flag; we use it to set dirty state
        try:
            modified = self.text.edit_modified()
            if modified:
                self.dirty = True
                self.text.edit_modified(False)
        except Exception:
            pass

    def _update_cursor(self):
        try:
            idx = self.text.index(tk.INSERT)
            line, col = map(int, idx.split("."))
            if self.statusbar:
                self.statusbar.update_cursor(line, col)
            self.highlight_current_line()
            # notify line number panel
            self.text.event_generate("<<Change>>", when="tail")
        except Exception:
            pass

    def _on_mousewheel(self, event):
        # default scrolling
        return

    def _on_ctrl_mousewheel(self, event):
        # zoom
        if event.delta > 0:
            self.zoom(1)
        else:
            self.zoom(-1)

    def zoom(self, delta_steps: int):
        self.font_size = max(6, self.font_size + delta_steps)
        self.text.config(font=(self.font_family, self.font_size))
        if self.statusbar:
            percent = int(100 * self.font_size / self.settings.get("font_size"))
            self.statusbar.set_zoom(percent)

    # ------------------------- bindings setup ------------------------------
    def _setup_bindings(self):
        # basic shortcuts
        self.text.bind("<Control-n>", lambda e: self.master.event_generate("<<NewFile>>"))
        self.text.bind("<Control-o>", lambda e: self.master.event_generate("<<OpenFile>>"))
        self.text.bind("<Control-s>", lambda e: self.master.event_generate("<<SaveFile>>"))
        self.text.bind("<Control-S>", lambda e: self.master.event_generate("<<SaveAsFile>>"))
        self.text.bind("<Control-f>", lambda e: self.master.event_generate("<<Find>>"))
        self.text.bind("<Control-h>", lambda e: self.master.event_generate("<<Replace>>"))
        self.text.bind("<Control-g>", lambda e: self.master.event_generate("<<GotoLine>>"))
        self.text.bind("<Control-z>", lambda e: self.text.edit_undo())
        self.text.bind("<Control-y>", lambda e: self.text.edit_redo())
        self.text.bind("<Control-a>", lambda e: self._select_all(e))
        self.text.bind("<Control-plus>", lambda e: (self.zoom(1), "break"))
        self.text.bind("<Control-minus>", lambda e: (self.zoom(-1), "break"))

    def _select_all(self, event):
        self.text.tag_add(tk.SEL, "1.0", tk.END)
        self.text.mark_set(tk.INSERT, "1.0")
        self.text.see(tk.INSERT)
        return "break"

    # ------------------------- external helpers ----------------------------
    def see_index(self, index: str):
        self.text.see(index)


# ---------------------------- Menu Bar ----------------------------------
class MenuBar(ttk.Frame):
    """Menu bar that creates File/Edit/View/Help menus and binds events to master."""

    def __init__(self, master, settings: SettingsManager, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.settings = settings
        self.menubar = tk.Menu(master)
        master.config(menu=self.menubar)
        self._build_menus()

    def _build_menus(self):
        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=lambda: self.master.event_generate("<<NewFile>>"))
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=lambda: self.master.event_generate("<<OpenFile>>"))
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=lambda: self.master.event_generate("<<SaveFile>>"))
        file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=lambda: self.master.event_generate("<<SaveAsFile>>"))
        file_menu.add_separator()
        # recent files
        recent = self.settings.get("recent_files") or []
        if recent:
            recent_menu = tk.Menu(file_menu, tearoff=0)
            for idx, p in enumerate(recent):
                recent_menu.add_command(label=f"{idx+1}. {os.path.basename(p)}", command=lambda path=p: self.master.event_generate("<<OpenRecent>>", when="tail") or self.master.event_generate("<<OpenPath>>", data=path))
            file_menu.add_cascade(label="Open Recent", menu=recent_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)
        self.menubar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=lambda: self.master.focus_get().event_generate("<Control-z>"))
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=lambda: self.master.focus_get().event_generate("<Control-y>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=lambda: self.master.focus_get().event_generate("<Control-x>"))
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=lambda: self.master.focus_get().event_generate("<Control-c>"))
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=lambda: self.master.focus_get().event_generate("<Control-v>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Find", accelerator="Ctrl+F", command=lambda: self.master.event_generate("<<Find>>"))
        edit_menu.add_command(label="Replace", accelerator="Ctrl+H", command=lambda: self.master.event_generate("<<Replace>>"))
        edit_menu.add_command(label="Go To Line...", accelerator="Ctrl+G", command=lambda: self.master.event_generate("<<GotoLine>>"))
        self.menubar.add_cascade(label="Edit", menu=edit_menu)

        # View menu
        view_menu = tk.Menu(self.menubar, tearoff=0)
        view_menu.add_checkbutton(label="Show Line Numbers", variable=tk.BooleanVar(value=self.settings.get("show_line_numbers")), command=self._toggle_line_numbers)
        view_menu.add_checkbutton(label="Word Wrap", variable=tk.BooleanVar(value=self.settings.get("wrap")), command=self._toggle_wrap)
        view_menu.add_separator()
        view_menu.add_command(label="Zoom In", accelerator="Ctrl++", command=lambda: self.master.event_generate("<<ZoomIn>>"))
        view_menu.add_command(label="Zoom Out", accelerator="Ctrl+-", command=lambda: self.master.event_generate("<<ZoomOut>>"))
        self.menubar.add_cascade(label="View", menu=view_menu)

        # Help
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._about)
        self.menubar.add_cascade(label="Help", menu=help_menu)

    def _toggle_line_numbers(self):
        current = not self.settings.get("show_line_numbers")
        self.settings.set("show_line_numbers", current)
        self.settings.save()
        self.master.event_generate("<<ToggleLineNumbers>>")

    def _toggle_wrap(self):
        current = not self.settings.get("wrap")
        self.settings.set("wrap", current)
        self.settings.save()
        self.master.event_generate("<<ToggleWrap>>")

    def _about(self):
        messagebox.showinfo(APP_NAME, f"{APP_NAME} - A professional Tkinter text editor\nBuilt with Tkinter & ttk")


# ---------------------------- Main Application --------------------------
class MainApp(tk.Tk):
    """Application entry point. Manages window, menus, frames, and interactions."""

    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1000x700")

        # settings
        self.settings = SettingsManager()
        self._setup_style()

        # build UI
        self.menubar = MenuBar(self, self.settings)

        self.paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # left: editor
        self.editor_container = ttk.Frame(self.paned)
        self.editor = EditorFrame(self.editor_container, self.settings)
        self.editor.pack(fill=tk.BOTH, expand=True)
        self.editor.statusbar = None  # set later
        self.paned.add(self.editor_container, weight=3)

        # right: optional document map or sidebar (placeholder)
        self.docmap = ttk.Frame(self.paned, width=240)
        ttk.Label(self.docmap, text="Document Map / Sidebar").pack(padx=8, pady=8)
        self.paned.add(self.docmap, weight=1)

        # status bar
        self.statusbar = StatusBar(self)
        self.editor.statusbar = self.statusbar
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

        # register events
        self.bind("<<NewFile>>", self.new_file)
        self.bind("<<OpenFile>>", self.open_file)
        self.bind("<<SaveFile>>", self.save_file)
        self.bind("<<SaveAsFile>>", self.save_as_file)
        self.bind("<<Find>>", lambda e: self.editor.find_dialog.show())
        self.bind("<<Replace>>", lambda e: self.editor.find_dialog.show())
        self.bind("<<GotoLine>>", self.goto_line)
        self.bind("<<ZoomIn>>", lambda e: self.editor.zoom(1))
        self.bind("<<ZoomOut>>", lambda e: self.editor.zoom(-1))
        self.bind("<<ToggleLineNumbers>>", self.toggle_line_numbers)
        self.bind("<<ToggleWrap>>", self.toggle_wrap)

        # init recent files
        self.opened_path: Optional[str] = None

        # update UI from settings
        if not self.settings.get("show_line_numbers"):
            self.editor.linenumber_panel.pack_forget()

        # set startup focus
        self.after(100, lambda: self.editor.text.focus_set())

    # -------------------------- style & appearance -----------------------
    def _setup_style(self):
        style = ttk.Style(self)
        theme = self.settings.get("theme")
        try:
            style.theme_use(theme)
        except Exception:
            # fallback to default
            pass

    # -------------------------- file operations --------------------------
    def new_file(self, event=None):
        if self._confirm_discard():
            self.editor.set_text("")
            self.editor.filepath = None
            self.title(f"{APP_NAME} - Untitled")

    def open_file(self, event=None):
        if not self._confirm_discard():
            return
        path = filedialog.askopenfilename()
        if not path:
            return
        self.editor.load_file(path)
        self.opened_path = path
        self.title(f"{APP_NAME} - {os.path.basename(path)}")

    def save_file(self, event=None):
        if not self.editor.filepath:
            return self.save_as_file()
        ok = self.editor.save_file(self.editor.filepath)
        if ok:
            self.title(f"{APP_NAME} - {os.path.basename(self.editor.filepath)}")

    def save_as_file(self, event=None):
        path = filedialog.asksaveasfilename(defaultextension=".txt")
        if not path:
            return
        ok = self.editor.save_file(path)
        if ok:
            self.title(f"{APP_NAME} - {os.path.basename(path)}")

    def _confirm_discard(self) -> bool:
        if self.editor.dirty:
            res = messagebox.askyesnocancel("Save changes?", "You have unsaved changes. Save now?")
            if res is None:
                return False
            if res:
                self.save_file()
        return True

    # -------------------------- misc commands ----------------------------
    def goto_line(self, event=None):
        ans = simpledialog.askinteger("Go To Line", "Line number:", minvalue=1)
        if ans is None:
            return
        try:
            self.editor.text.mark_set(tk.INSERT, f"{ans}.0")
            self.editor.text.see(tk.INSERT)
            self.editor._update_cursor()
        except Exception:
            pass

    def toggle_line_numbers(self, event=None):
        show = self.settings.get("show_line_numbers")
        if show:
            self.editor.linenumber_panel.pack(side=tk.LEFT, fill=tk.Y)
        else:
            self.editor.linenumber_panel.pack_forget()

    def toggle_wrap(self, event=None):
        new_wrap = tk.WORD if self.settings.get("wrap") else tk.NONE
        self.editor.text.config(wrap=new_wrap)


# ---------------------------- Application Entry ------------------------
def main():
    app = MainApp()
    app.mainloop()


if __name__ == "__main__":
    main()
