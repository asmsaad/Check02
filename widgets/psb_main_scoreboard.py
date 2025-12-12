"""
Module containing ScoreboardApp extracted from the monolithic script for incremental refactor.
This file mirrors the original class while keeping a small sys.path preamble so it
can be imported during staged migration.
"""
import sys
import pathlib
# BIN_DIR should point to the repository `bin` directory (four levels up from gui file)
BIN_DIR = str(pathlib.Path(__file__).resolve().parents[4] / "bin")
# Ensure repo lib paths are available when importing this module standalone
sys.path.append(BIN_DIR + "/../lib/python")
sys.path.append(BIN_DIR + "/../lib/python/Util")

import os
import sys as _sys
import threading
import io
import csv
import math
import json
# Use Python 3.11 native hints; avoid importing from `typing` where possible.
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from collections import defaultdict
from typing import Any, Dict, List, Callable, Tuple, Optional

# PIL imports for rotated header image generation
try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
except ImportError:
    Image = ImageDraw = ImageFont = ImageTk = None

from memphys_pin_check_scoreboard.gui.psb_details_bottom import DetailsBottom
from memphys_pin_check_scoreboard.gui.psb_soft_frame import SoftFrame
from memphys_pin_check_scoreboard.gui.psb_waiver_forms import WaiverTopLevelWindow, WaiverRulesFrame
from memphys_pin_check_scoreboard.gui.tooltips import Tooltip
from memphys_pin_check_scoreboard.gui.psb_violations_analysis_tab import ViolationAnalysisTabFrame
from memphys_pin_check_scoreboard.psb_settings_and_config import load_settings, save_settings
from memphys_pin_check_scoreboard import (
    SOFT_LIGHT,
    SOFT_DARK,
    PINCHECK_SCOREBOARD_CONFIG,
    MEMPHYS_PIN_CHECK_CONFIG,
    MEMPHYS_RULE_SHORT_MAP,
)
from memphys_pin_check_scoreboard.gui.models import (
    RuleDef,
    Violation,
    PinRecord,
    RunMetadata,
    RunData,
)
from memphys_pin_check_scoreboard.io import load_yaml_to_rundata
from memphys_pin_check_scoreboard.gui.psb_load_macro_notebook import LoadMacroNotebook
from memphys_pin_check_scoreboard.gui.psb_rule_manager import RuleManager
from memphys_pin_check_scoreboard.pincheck_scoreboard_run_editor import RunEditor
from memphys_pin_check_scoreboard.psb_settings_and_config import load_scoreboard_config as _load_scoreboard_config_full
from memphys_pin_check_scoreboard.psb_utils import CellLevel, choose_level



class TableManager:
    """Encapsulates Treeview, header canvas and overlay badge pooling.

    This class was extracted from ScoreboardApp._build_table to isolate table
    creation and related operations while preserving behaviour. It expects an
    application instance `app` which continues to own shared state and callback
    methods; TableManager will set `app.tree` and `app.header_canvas` so the
    rest of the application continues to work unchanged.
    """

    def __init__(self, app, parent):
        self.app = app
        self.parent = parent

    def build(self):
        """
        Build the Treeview table and the header canvas.
        
        The `header_canvas` sits above the `Treeview` and is used to draw
        category bands and rotated column labels. The Treeview columns for
        rule cells are intentionally narrow — the human-readable labels are
        rendered on the canvas instead.
        """
        base_cols = ["PIN", "DIR", "TYPE"]
        # Category header band
        # Make header canvas taller so rotated labels can render vertically
        self.app.header_canvas = tk.Canvas(
            parent,
            height=self.app._header_height,
            background="#d4d4d4",
            highlightthickness=0,
            bd=0,
        )
        self.app.header_canvas.grid(row=0, column=0, sticky="ew", padx=(2, 2), pady=(0, 0))
        parent.grid_columnconfigure(0, weight=1)
        self.app.tree = ttk.Treeview(
            parent, columns=base_cols, show="headings", selectmode="browse"
        )
        
        for c in base_cols:
            w = 240 if c == "PIN" else 100
            self.app.tree.heading(c, text=c)
            self.app.tree.column(
                c,
                width=w,
                anchor="center",
                stretch="no",
            )
        # store scrollbars to coordinate overlay refresh
        self.app.ysb = ttk.Scrollbar(
            parent, orient="vertical", command=self.app._on_yscroll
        )  # was: self.app.tree.yview
        self.app.xsb = ttk.Scrollbar(parent, orient="horizontal", command=self.app._on_xscroll)
        # y/x scrollcommand wrapper ensures overlay refresh when view changes
        self.app.tree.configure(
            yscrollcommand=self.app._on_tree_yscroll, xscrollcommand=self.app._tree_xscroll
        )
        self.app.tree.grid(row=2, column=0, sticky="nsew", padx=(2, 2), pady=(2, 2))
        
        # Vertical scrollbar stays to the right of the tree, fills vertically
        self.app.ysb.grid(row=2, column=1, sticky="ns", padx=(0, 2), pady=(2, 2))
        
        # Horizontal scrollbar should span the full width under the tree
        self.app.xsb.grid(row=3, column=0, sticky="ew", padx=(2, 2), pady=(0, 2))
        
        # Allow row 2 (the tree row) to grow; you already have this line
        parent.grid_rowconfigure(2, weight=1)
        self.app._retag_tree_colors()
        self.app.tree.bind("<ButtonRelease-1>", self.app._on_cell_click)
        self.app.tree.bind("<Button-3>", self.app._show_context_menu)
        
        # Also refresh overlays on tree resizing
        self.app.tree.bind(
            "<Configure>",
            lambda e: (self.app._redraw_group_header(), self.app._schedule_badge_refresh()),
        )
        self.app.header_canvas.bind("<Configure>", lambda e: self.app._redraw_group_header())
        self.app.header_canvas.bind("<Button-3>", self.app._on_header_right_click)
        self.app.tree.bind("<MouseWheel>", lambda e: self.app._schedule_badge_refresh())
        self.app.tree.bind("<Button-4>", lambda e: self.app._schedule_badge_refresh())
        self.app.tree.bind("<Button-5>", lambda e: self.app._schedule_badge_refresh())
        self.app.ctx = tk.Menu(self, tearoff=False)
        self.app.ctx.add_command(
            label="Copy Pin/Entity Name", command=lambda: self.app._ctx_copy("pin")
        )
        self.app.ctx.add_command(
            label="Copy Cell Messages", command=lambda: self.app._ctx_copy("messages")
        )
        self.app.ctx.add_separator()
        self.app.ctx.add_command(
            label="Open Evidence (if path)", command=self.app._ctx_open_evidence
        )
        self.app.ctx.add_separator()
        self.app.ctx.add_command(
            label="Export This Row to CSV…", command=self.app._ctx_export_row
        )
        
        
        def _open_waiver_window(self) -> None:
        """
        Build real waiver data from the loaded run and open/refresh the Waiver window.
        - If no YAML is loaded, inform the user.
        - If the window is already created and showing, refresh its content.
        - Otherwise inject data and show it.
        """
        if not self.app._rundata:
            try:
                messagebox.showinfo("Waiver", "Load a YAML first.")
            except Exception:
                pass
            return
        
        try:
            real_data = self.app._build_waiver_data()
        except Exception as exc:
            try:
                messagebox.showerror("Waiver", f"Failed to build waiver data:\n{exc}")
            except Exception:
                pass
            return
        
        # If window exists and is visible, refresh its frame content
        try:
            if getattr(self.app.waiver_window, "_window", None) is not None and self.app.waiver_window._window.winfo_exists():
                # live refresh
                if getattr(self.app.waiver_window, "rules_app", None):
                    self.app.waiver_window.rules_app.load_data(real_data)
                    # center to parent after refresh for good UX
                    try:
                        self.app.waiver_window._center_window()
                    except Exception:
                        pass
                    return
        except Exception:
            pass
        
        # Inject new data and open
        try:
            self.app.waiver_window.data = real_data
            self.app.waiver_window.show()
        except Exception:
            # As a fallback, recreate WaiverTopLevelWindow and open
            try:
                self.app.waiver_window = WaiverTopLevelWindow(self, title="Rules waiver", data=real_data, on_submit=on_submit_waiver)
                self.app.waiver_window.show()
            except Exception as exc2:
                try:
                    messagebox.showerror("Waiver", f"Unable to open Waiver window:\n{exc2}")
                except Exception:
                    pass
        
        # --- ADD: map pincheck severities to Waiver UI tokens ---


# =======================
# Main Scoreboard Window
# =======================

from enum import Enum

# Resource locations (computed relative to repo layout)
RESOURCE_DIR = BIN_DIR + "/../resources"
SCOREBOARD_CONFIG_FILE = RESOURCE_DIR + "/memphys_scoreboard_config.yml"
SCOREBOARD_LOGO_ICON = RESOURCE_DIR + "/pincheck_scoreboard/heatmap32x32.png"

STATUS_GLYPH = {
    CellLevel.PASS_: "✔",  # tick mark
    CellLevel.FAIL: "✖",  # cross mark
    CellLevel.WARN: "!",  # exclamation for warning
    CellLevel.NA: "✔",  # dash for N/A
}
SEVERITY_ORDER = {"ERROR": 3, "WARNING": 2, "INFO": 1, None: 0}

class ScoreboardApp(tk.Tk):
    """
    Main application window for the Pincheck Scoreboard.

    Responsibilities:
        - Present a columnar scoreboard of rules vs pins with compact cells showing
            pass/warn/fail markers.
        - Provide filters (search, severity, pin type) and persist UI settings.
        - Allow toggling visibility of categories and individual rules.
        - Render rotated rule headers to allow tightly packed columns.
        - Offer per-row details, CSV export, and evidence file opening.

    Implementation notes:
        - Uses a `header_canvas` to draw category bands and rotated rule labels
            so the underlying `ttk.Treeview` columns can be narrow.
        - Caches generated header images in `_col_heading_imgs` to avoid GC.
        - Settings persist via `save_settings` and are loaded with `load_settings`.
    """

    def __init__(self):
        super().__init__()
        self.title("Pin Check Scoreboard")
        self.cfg = load_settings()
        # Ensure expected keys exist with safe defaults to avoid KeyError
        vf = self.cfg.setdefault("view_filters", {})
        vf.setdefault("search", "")
        vf.setdefault("severity", "ALL")
        vf.setdefault("pin_type", "ALL")
        vf.setdefault("case_sensitive", False)
        vf.setdefault("only_violated", False)

        rg = self.cfg.setdefault("rule_groups", {})
        rg.setdefault("order", [])
        rg.setdefault("visible", {})
        rg.setdefault("rules_visible", {})
        self._apply_rule_label_overrides()
        geom = self.cfg.get("window_settings", {}).get("geometry")
        # Header canvas height (user adjustable)
        self._header_height = int(
            self.cfg.get("ui_settings", {}).get("header_height", 84)
        )
        self.geometry(geom if isinstance(geom, str) and "x" in geom else "1320x780")
        self.minsize(1100, 680)
        self.iconphoto(True, tk.PhotoImage(file=SCOREBOARD_LOGO_ICON, master=self))

        # Fonts (responsive; compact mode will shrink them)
        self._font_family = (
            "Sans Regular" if sys.platform.startswith("win") else "DejaVu Sans"
        )

        self._size_base = 9  # was 10
        self._size_small = 8  # was 9
        self._size_bold = 10  # was 11
        self._size_heading = 8  # was 9

        self._compact = False
        # When True the Analysis Tab is showing a rule-specific/custom view
        # and should not be overwritten by the automatic summary population.
        self._analysis_custom_view_active = False
        # State
        self._rundata: RunData | None = None
        self._viol_by_pin_by_rule: dict[str, dict[str, list[Violation]]] = {}
        self._last_yaml_path: str | None = None
        self._known_pins: set[str] = set()
        self._filter_text = tk.StringVar(value=self.cfg["view_filters"]["search"])
        self._filter_sev = tk.StringVar(value=self.cfg["view_filters"]["severity"])
        self._filter_type = tk.StringVar(value=self.cfg["view_filters"]["pin_type"])
        self._filter_case = tk.BooleanVar(
            value=self.cfg["view_filters"]["case_sensitive"]
        )
        self._filter_only_viol = tk.BooleanVar(
            value=self.cfg["view_filters"]["only_violated"]
        )
        self._group_order: list[str] = list(self.cfg["rule_groups"]["order"])
        self._group_visible: dict[str, bool] = dict(self.cfg["rule_groups"]["visible"])
        self._rule_visible_overlay_by_cat: dict[str, dict[str, bool]] = {}
        # NEW: rule-level visibility (category -> {rule_id: bool})
        self._rule_visible_by_cat: dict[str, dict[str, bool]] = dict(
            (self.cfg["rule_groups"].get("rules_visible") or {})
        )
        self._pin_types: set[str] = set()
        self._search_entry: ttk.Entry | None = None
        self._rules_by_cat: dict[str, list[str]] = {}
        self._col_pairs: list[tuple[str, str]] = []
        self._xscroll_first = 0.0
        self._xscroll_last = 1.0
        self._col_total_width = 0
        self._last_header_signature = None
        # NEW: caches for per-cell levels and overlay badge widgets
        # Use `object` instead of `typing.Any` to avoid typing import.
        self._cell_cache: dict[str, dict[str, dict[str, object]]] = {}
        self._badge_widgets: dict[tuple[str, str], tk.Label] = {}
        # NEW: Debounce + pooling
        self._badge_refresh_after: str | None = None
        self._badge_pool: list[tk.Label] = []
        self._badge_font = None  # will be set in _apply_theme()
        # NEW: Toggle for overlays (fast mode if off)
        self._cell_color_overlays = tk.BooleanVar(value=True)

        self.only_columes_to_show_by_click_only_violation = {}
        
        def _get_on_submit_waiver():
            # Prefer a globally-defined on_submit_waiver (kept in bin during
            # staged migration). Fall back to a simple logger to allow the
            # app to be constructed for testing.
            try:
                return globals().get("on_submit_waiver")
            except Exception:
                return None

        on_submit_cb = _get_on_submit_waiver() or (lambda payload: print("[psb_main_scoreboard] waiver submitted"))

        self.waiver_window = WaiverTopLevelWindow(
            self,
            title="Rules waiver",
            data={},  # real data will be built on-demand
            on_submit=on_submit_cb,
        )

        self._apply_theme()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._apply_theme()
        # Responsive: debounce resize to keep content inside borders and shrink fonts if needed
        self._resize_after = None
        self.bind("<Configure>", self._on_root_resize)
        # ---------- THEME ENGINE ----------

        # Auto-load the most recent report (if available) to populate the scoreboard on startup
        try:
            recent = self.cfg.get("recent_reports", [])
            if recent:
                candidate = recent[0]
                if isinstance(candidate, str) and os.path.isfile(candidate):
                    # Load silently; UI will show any errors
                    try:
                        self._load_yaml_path(candidate)
                    except Exception:
                        pass
        except Exception:
            pass

    def _tk_font(self, size=None, weight="normal"):
        """
        Build a Tk font tuple (family, size, weight) using the app's preferred font.

        This helper centralizes font creation so all widgets can use a consistent
        typeface and scale. It returns the plain Tk-compatible tuple, which is
        accepted by ttk styles and Tk widget `font=` configurations.

        Args:
            size (int | None): The point size for the font. When None, the method
                uses `self._size_base`, which adjusts in responsive mode.
            weight (str): Either "normal" or "bold". Any other value is passed
                through (Tk treats non-empty strings as weight tokens).

        Returns:
            tuple: (family, size, weight_token)
                - family: `self._font_family` (e.g., "DejaVu Sans" or "Sans Regular")
                - size:   the provided `size` or the app's `self._size_base`
                - weight_token: "" when weight == "normal", or the weight string otherwise.
                  (Tk interprets empty string as "normal".)
        """
        font_family = self._font_family
        font_size = size if size is not None else self._size_base
        weight_token = "" if weight == "normal" else weight
        return (font_family, font_size, weight_token)

    def _apply_theme(self, mode: str | None = None):
        if mode is not None:
            self.cfg.setdefault("ui_settings", {})["theme"] = mode
            save_settings(self.cfg)
        theme_name = (self.cfg.get("ui_settings", {}) or {}).get("theme", "LIGHT").upper()
        self._theme_mode = theme_name
        self.colors = SOFT_DARK if theme_name == "DARK" else SOFT_LIGHT
        self.configure(bg=self.colors["surface"])
        # cache badge font (used a lot) — use smaller for less churn
        self._badge_font = self._tk_font(self._size_small, weight="bold")
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        c = self.colors
        # ---- Base & Card styles

        # style.configure("TFrame", background=c["surface"])
        style.configure("Referance.TButton", background="#fcf3cf", foreground="#654321", font=("Consolas", 8, "bold") )
        style.configure("ViolationAnalysisTabFrame.TFrame", background="#d4d4d4")
        style.configure("DetailsBottom.TLabel", background="#d4d4d4")
        style.configure("DetailsBottom.TPanedwindow", background="#d4d4d4")
        style.configure(
            "TLabel",
            font=self._tk_font(self._size_base),
        )
        style.configure(
            "Card.TLabel",
            font=self._tk_font(self._size_base),
        )
        style.configure(
            "Card.Muted.TLabel",
            background=c["panel"],
            foreground=c["muted"],
            font=self._tk_font(self._size_small),
        )

        style.configure("Card.TPanedwindow", background="#d4d4d4")

        style.configure(
            "Accent.TButton",
            padding=(10, 6),
            font=self._tk_font(self._size_base),
            background=c["accent"],
            foreground="#FFFFFF",
            borderwidth=1,
            relief="solid",
            bordercolor=c["border_button_hover"],
        )
        style.map(
            "Accent.TButton",
            background=[("active", c["accent_hover"])],
            bordercolor=[("focus", c["focus"]), ("active", c["border_button_hover"])],
            foreground=[("disabled", "#D0D5E5")],
        ) 
        style.map(
            "Referance.TButton",
            background=[("active", "#fcf3cf"), ("pressed", "#fcf3cf")],
            foreground=[("active", "#654321"), ("pressed", "#654321")],
        )
        # Outlined (secondary)
        style.configure(
            "Outlined.TButton",
            padding=(10, 6),
            font=self._tk_font(self._size_base),
            background=c["panel"],
            foreground=c["text"],
            borderwidth=1,
            relief="solid",
            bordercolor=c["border_button"],
        )
        style.map(
            "Outlined.TButton",
            background=[("active", c["panel"])],
            bordercolor=[("active", c["border_button_hover"]), ("focus", c["focus"])],
        )
        # ---- Treeview
        style.configure(
            "Treeview",
            fieldbackground="#d4d4d4",
        )
        # style.configure("Treeview", bordercolor="#FF0000")
        # style.configure("Treeview.Heading", bordercolor="#FF0000")
        style.map(
            "Treeview",
            background=[("selected", c["selection"])],
            foreground=[("selected", c["on_selection"])],
            bordercolor=[
                ("focus", "red"),
                ("!focus", "green"),
            ],
        )
        style.configure(
            "Treeview.Heading",
            borderwidth=1,
            relief="solid",
        )

        style.configure(
            "Status.TLabel",
            background=c["surface"],
            foreground=c["muted"],
            font=self._tk_font(self._size_small),
        )

        # SAD STYLE
        BASE_BG = "#dcdad5"
        HOVER_TEXT = "#0078d7"  # Bright Blue

        style.configure(
            "Filter.TCheckbutton",
            background=BASE_BG,
            foreground="black",
            font=("Segoe UI", 9),
            # padding=2
        )
        style.configure("StyleSad.TFrame", background="#dcdad5")
        style.configure("StyleSad.TLabelFrame", background="#dcdad5", padding=(3, 3))

        style.map(
            "Filter.TCheckbutton",
            # 1. Lock Background (No change on hover)
            background=[("active", BASE_BG), ("!disabled", BASE_BG)],
            # 2. Change Text Color on Hover
            foreground=[("active", HOVER_TEXT), ("!disabled", "black")],
            # 3. Optional: Lock Indicator Background (The box itself)
            indicatorbackground=[("active", BASE_BG), ("pressed", BASE_BG)],
        )

        # Retheme cards/canvases
        for name in ("head_card", "filters_card", "table_card", "details_card"):
            if hasattr(self, name):
                getattr(self, name).retheme(
                    c["panel"], c["shadow_light"], c["shadow_dark"]
                )
        if hasattr(self, "_main_container"):
            self._main_container.configure(bg=c["surface"])
        if hasattr(self, "header_canvas"):
            self.header_canvas.configure(background=c["band_bg"])
        # Repaint content
        if hasattr(self, "status"):
            self.status.configure(style="Status.TLabel")
        if hasattr(self, "tree"):
            self._retag_tree_colors()
        if hasattr(self, "_paint_badges"):
            self._paint_badges()
        if hasattr(self, "detail") and hasattr(self.detail, "apply_colors"):
            self.detail.apply_colors(c)
        # Refresh per-cell overlays after theme changes (if enabled)
        if hasattr(self, "_refresh_cell_badges") and self._cell_color_overlays.get():
            self.after_idle(self._refresh_cell_badges)

    def _apply_rule_label_overrides(self) -> None:
        """
        Apply rule_label_overrides from self.cfg to MEMPHYS_RULE_SHORT_MAP
        and refresh the UI (columns + header).
        """
        try:
            overrides = (self.cfg or {}).get("rule_label_overrides", {}) or {}
            if isinstance(overrides, dict):
                for rid, new_short in overrides.items():
                    if (
                        isinstance(rid, str)
                        and isinstance(new_short, str)
                        and new_short.strip()
                    ):
                        MEMPHYS_RULE_SHORT_MAP[rid] = new_short.strip()
            # Rebuild header images & columns to use new labels
            if hasattr(self, "_rebuild_table_columns"):
                self._rebuild_table_columns()
            if hasattr(self, "_refresh_table"):
                self._refresh_table()
            if hasattr(self, "_redraw_group_header"):
                self._redraw_group_header()
        except Exception:
            pass

    def _toggle_theme(self):
        """
        Toggle the UI theme between LIGHT and DARK, then refresh visuals.

        This switches self._theme_mode to the opposite theme by calling
        `_apply_theme()` with the new mode, re-draws the custom header band,
        and refreshes the table so styles, row tags, and overlay badges are
        updated to match the new palette.

        Args:
            None

        Returns:
            None
        """
        # Decide the next theme based on current mode (no change to external behavior).
        next_mode = "DARK" if self._theme_mode != "DARK" else "LIGHT"

        # Apply theme, then repaint header and refresh table visuals.
        self._apply_theme(next_mode)
        self._redraw_group_header()
        self._refresh_table()

    def _retag_tree_colors(self):
        """
        (Re)configure Treeview row and severity tags using the current theme palette.

        This method applies background/foreground colors to commonly used tags:
            - Alternating row tags: "row_even", "row_odd" (gridline effect)
            - Severity tags: "FAIL", "WARN", "PASS" (row highlighting)
            - Group header tag: "group_header" (synthetic header row for 'Other Violations')

        It is safe to call multiple times (e.g., after a theme change or when the
        Treeview is recreated). The function returns early if the Treeview hasn't
        been built yet.

        Args:
            None

        Returns:
            None

        Side Effects:
            - Mutates tag styling on `self.tree` via `tag_configure`.

        Notes:
            - Tag names are part of the UI contract across the app; do not rename them
              unless you update all usages (row insertion, status badges, etc.).
        """
        # Use a descriptive alias for the active color palette.
        palette = self.colors

        # If the tree isn't available yet, there's nothing to retag.
        if not hasattr(self, "tree"):
            return

        # Alternating row tags to simulate gridlines; header already has a border.
        self.tree.tag_configure(
            "row_even", background=palette["row_even"], foreground=palette["text"]
        )
        self.tree.tag_configure(
            "row_odd", background=palette["row_odd"], foreground=palette["text"]
        )

        # Severity-driven row highlighting tags.
        self.tree.tag_configure(
            "FAIL", background=palette["error_bg"], foreground=palette["error_fg"]
        )
        self.tree.tag_configure(
            "WARN", background=palette["warn_bg"], foreground=palette["warn_fg"]
        )
        self.tree.tag_configure(
            "PASS", background=palette["pass_bg"], foreground=palette["pass_fg"]
        )

        # Synthetic header row (used for "Other Violations" group).
        self.tree.tag_configure(
            "group_header", background=palette["panel"], foreground=palette["text"]
        )

    def _on_root_resize(self, event):
        """
        Handle top-level window resize events to keep the UI responsive.

        This callback is bound to the root window's `<Configure>` event. It records
        the latest window dimensions, triggers responsive layout adjustments, and
        repaints the custom group header band so its background/rounded corners
        stay aligned with the new size.

        Args:
            event: A Tkinter event object for `<Configure>`. Common fields used:
                - event.width   (int): New root window width.
                - event.height  (int): New root window height.
                - event.widget  (Tk):  The widget that was configured (root).

        Returns:
            None
        """
        # Make the event intent explicit without altering logic.
        new_width = event.width
        new_height = event.height

        # Persist the latest root geometry for downstream layout calculations.
        self._root_w = new_width
        self._root_h = new_height

        # Recompute responsive metrics and repaint the group header band.
        self._apply_responsive()
        self._redraw_group_header()

    def _apply_main_split_initial_position(self) -> None:
        """
        Set the initial sash position for the main vertical split.
        Uses a saved pixel value from settings when available; otherwise
        approximates your original 58% table / 40% details split.
        """
        try:
            pos = int((self.cfg.get("ui_settings", {}) or {}).get("main_split", -1))
        except Exception:
            pos = -1

        try:
            if hasattr(self, "_main_split"):
                if pos >= 0:
                    # Use saved pixel value (Tk will clamp if needed)
                    self._main_split.sashpos(0, pos)
                else:
                    # Default close to old relheight=0.58 for the table card
                    total = (
                        self._main_split.winfo_height()
                        or self._main_container.winfo_height()
                    )
                    if total and total > 80:
                        default_pos = int(total * 0.70)
                        self._main_split.sashpos(0, default_pos)
        except Exception:
            # Ignore early geometry/layout races without crashing
            pass

    def _persist_main_split(self) -> None:
        """
        Read the current sash pixel position and persist it in user settings.
        Called on sash release; also used by _on_close for redundancy.
        """
        try:
            if hasattr(self, "_main_split"):
                pos = int(self._main_split.sashpos(0))
                self.cfg.setdefault("ui_settings", {})["main_split"] = pos
                save_settings(self.cfg)
        except Exception:
            pass

    # ---------- Header handle (resize) ----------
    def _on_header_handle_press(self, event):
        """
        Begin a header-height drag interaction (mouse button press on the handle).

        This handler captures two pieces of state that will be used by the
        drag-motion handler (`_on_header_handle_drag`) to compute the new
        header height while dragging:

            - `_drag_start_y`:   The screen Y coordinate (in pixels) of the
                                 mouse at the moment the user pressed down.
            - `_start_height`:   The header canvas height at drag start.

        Both values are stored on the handle widget (`self._header_handle`)
        to keep the transient drag state colocated with the UI element.

        Args:
            event: Tkinter event object. Only `event.y_root` is used.

        Returns:
            None
        """
        try:
            # Record the absolute screen Y position at press time.
            self._header_handle._drag_start_y = event.y_root

            # Record the header height at the start of the drag; fall back to the
            # remembered target height if the canvas isn't fully realized yet.
            current_header_px = int(
                self.header_canvas.winfo_height() or self._header_height
            )
            self._header_handle._start_height = current_header_px
            print('++'*20)
        except Exception:
            # Defensive: ignore transient layout issues during press.
            pass

    def _on_header_handle_drag(self, event):
        """
        Update the header canvas height while the user drags the resize handle.

        This handler computes the vertical delta (in screen pixels) from the
        initial press point recorded in `_on_header_handle_press`, adds it to
        the starting header height, clamps to a sensible minimum, and applies
        the new height to the header canvas. It then triggers a header redraw.

        Drag state used:
            - `self._header_handle._drag_start_y`: screen Y at drag start
            - `self._header_handle._start_height`: header height at drag start

        Args:
            event: Tkinter event object. Uses `event.y_root` to measure vertical movement.

        Returns:
            None
        """
        try:
            # Read drag baseline and current Y from the event & stored state.
            start_y_screen = getattr(self._header_handle, "_drag_start_y", event.y_root)
            start_header_height_px = int(
                getattr(self._header_handle, "_start_height", self._header_height)
            )

            # Vertical delta in screen coordinates since press.
            delta_y_px = event.y_root - start_y_screen

            # Compute and clamp the new header height.
            new_height_px = max(36, int(start_header_height_px + delta_y_px))

            # Persist and apply to the header canvas.
            self._header_height = new_height_px
            self.header_canvas.configure(height=self._header_height)

            # Redraw category header to reflect the new geometry.
            self._redraw_group_header()
        except Exception:
            # Defensive: ignore transient geometry/layout issues during drag.
            pass

    def _on_header_handle_release(self, event):
        """
        Finalize a header-height drag interaction (mouse button release on the handle).

        This handler persists the current header height to the user settings so
        subsequent launches (or theme toggles) restore the chosen height. No geometry
        changes are performed here—the height is assumed to have been updated during
        `_on_header_handle_drag`.

        Args:
            event: Tkinter event object (not used beyond signaling release).

        Returns:
            None
        """
        try:
            # Persist the chosen header height into the UI settings.
            current_height_px = int(self._header_height)
            self.cfg.setdefault("ui_settings", {})["header_height"] = current_height_px
            save_settings(self.cfg)
        except Exception:
            # Non-fatal: ignore persistence errors to keep UI responsive.
            pass

    def _auto_fit_header(self):
        """
        Auto-fit header height to accommodate the tallest rotated label or
        the longest fallback stacked label based on current font metrics.
        """
        try:
            # Find the longest label among visible columns
            for _, _, col_w in self._measure_columns():
                pass
            longest = 0
            for cat, rid in getattr(self, "_col_pairs", []):
                short = MEMPHYS_RULE_SHORT_MAP.get(rid, rid)
                longest = max(longest, len(short))

            # Simple heuristic: base height + per-char increment
            base = 40
            per_char = 8
            new_h = min(240, max(48, base + longest * per_char))
            self._header_height = int(new_h)
            self.header_canvas.configure(height=self._header_height)
            self._redraw_group_header()
            # Persist immediately
            self.cfg.setdefault("ui_settings", {})["header_height"] = int(
                self._header_height
            )
            save_settings(self.cfg)
        except Exception:
            pass

    def _apply_responsive(self):
        """
        Adjust font sizes and UI layout when the window is small/large, then repaint.

        - Toggles `self._compact` based on current width/height.
        - Updates size tokens (`_size_base/_small/_bold/_heading`) accordingly.
        - Re-applies theme/styles and redraws the group header.
        - Updates head-section wrapping where available.
        """
        window_width = max(1, self.winfo_width())
        window_height = max(1, self.winfo_height())
        should_compact = window_width < 1200 or window_height < 720

        if should_compact != self._compact:
            self._compact = should_compact

            # Compact vs. regular font scale
            if should_compact:
                self._size_base, self._size_small, self._size_bold, self._size_heading = (
                    8,
                    7,
                    9,
                    7,
                )
            else:
                self._size_base, self._size_small, self._size_bold, self._size_heading = (
                    9,
                    8,
                    10,
                    8,
                )

            # Re-apply theme + dependent styles and redraw header
            self._apply_theme()
            self._redraw_group_header()

        # Ensure head text wrapping follows container width (defensive)
        if hasattr(self, "_head_responsive"):
            try:
                self._head_responsive()
            except Exception:
                pass

    # ---------- UI BUILD ----------
    def _build_ui(self):
        """
        Build and layout the main UI widgets.

        This method constructs the menu bar, header card, filters card, the
        main split (table + details) and registers keyboard shortcuts. It
        should be called once during initialization.
        """
        # Build UI in logical sections: top, middle (left/right panes), bottom
        self._build_menu()

        # Top frame (menu area) — keep menu attached to root, reserve top bar
        self._top_frame = tk.Frame(
            self,
        )
        self._top_frame.pack(side="top", fill="x")

        # Middle frame holds a horizontal PanedWindow with left/right panes
        self._middle_frame = tk.Frame(self, bg=self.colors.get("surface"))
        self._middle_frame.pack(side="top", fill="both", expand=True)
        self._paned = tk.PanedWindow(
            self._middle_frame, orient="horizontal", background="#aaaaaa"
        )
        self._paned.pack(fill="both", expand=True)
        self._left_pane = tk.Frame(
            self._paned,
        )
        self._right_pane = tk.Frame(self._paned, bg="#d4d4d4")
        self._paned.add(self._left_pane, minsize=350)
        self._paned.add(self._right_pane)

        # Bottom frame contains status and any lower controls
        self._bottom_frame = tk.Frame(self, bg=self.colors.get("surface"))
        self._bottom_frame.pack(side="bottom", fill="x")

        # Build sections into the panes
        self._build_head_section()
        self._build_filter_section()
        self._build_table_section()
        self._build_details_section()
        self._build_bottom_section()

        def _update_pan_window_dispaly_area_():
            self._paned.sash_place(0, 350, 0)

        self._middle_frame.after(250, _update_pan_window_dispaly_area_)

    # ---- UI section builders (refactored from _build_ui) ----

    def _build_head_section(self):
        """
        Construct the top “Head” card in the left pane: load button, run/tool/design rows,
        severity badges, and responsive text wrapping hook.
        """
        # Choose container: the left pane or its stacked holder
        container = getattr(self, "_left_pane", self)
        container.config(background="#dcdad5")

        # Ensure a top-anchored stack for head+filters so they remain at the top
        if not hasattr(self, "_left_stack"):
            self._left_stack = ttk.Frame(container, style="StyleSad.TFrame")
            self._left_stack.pack(side="top", fill="x", anchor="n")
        container = self._left_stack
        head_content = container
        style = ttk.Style(head_content)
        style.theme_use("clam")
        # style.configure("Style5.TFrame", background="#dcdad5")
        left_section_frame = ttk.Frame(head_content, style="StyleSad.TFrame")
        left_section_frame.pack(fill=tk.BOTH, expand=True, anchor="ne")
        # Project Load Section
        macro_load_frame = ttk.LabelFrame(left_section_frame, padding=(5, 5))
        macro_load_frame.pack(fill=tk.BOTH, expand=True, anchor="ne", padx=10)
        macro_load_type_nb = LoadMacroNotebook(
            macro_load_frame,
            style="StyleSad.TFrame",
            load_yaml_btn_callback=self._open_yaml,
        )
        macro_load_type_nb.pack(expand=True, fill=tk.X, anchor="ne")
        
        
        # --- NEW: Reload YAML button on the left sidebar ---
        reload_btn = ttk.Button(
            macro_load_frame,
            text="Reload YAML",
            width=12,
            style="Outlined.TButton",   # existing style in your theme
            command=self._reload_yaml
        )
        reload_btn.pack(fill=tk.X, pady=(6, 0))

        # Optional: tooltip for UX consistency
        try:
            Tooltip(reload_btn, "Reload the last opened YAML (F5)")
        except Exception:
            pass


        badges_row = ttk.LabelFrame(left_section_frame, padding=(5, 5))
        badges_row.pack(fill=tk.BOTH, anchor="n", expand=True, padx=10)

        # Filter
        self.filter_loaded_macro_frame = ttk.LabelFrame(
            left_section_frame, padding=(5, 5)
        )
        self.filter_loaded_macro_frame.pack(
            fill=tk.BOTH, expand=True, anchor="ne", padx=10
        )

        # Rule Filter
        self.rule_filter_frame = ttk.LabelFrame(left_section_frame, padding=(5, 5))
        self.rule_filter_frame.pack(fill=tk.BOTH, expand=True, anchor="ne", padx=10)

        # --- Rules section header (left: label, right: Select All) ---
        rules_header_frame = ttk.Frame(self.rule_filter_frame)
        rules_header_frame.pack(fill=tk.BOTH, pady=(0, 4))

        # Left: "Rules" label
        tk.Label(
            rules_header_frame,
            text="Rules",
            font=("Segoe UI", 10, "normal"),
            bg="#dcdad5",
            fg="#333",
            justify="left",
        ).pack(side="left", anchor="w")

        # Right: Select All checkbox
        self._select_all_var = tk.BooleanVar(value=True)
        select_all_CB = ttk.Checkbutton(
            rules_header_frame,
            text="Select All",
            variable=self._select_all_var,
            command=self._on_select_all_toggle,  # <-- we implement this next
            style="Filter.TCheckbutton",
        )
        select_all_CB.pack(side="right", anchor="e")

        self.rule_manager = RuleManager(self.rule_filter_frame)
        self.rule_manager.pass_update_table_args(
            self._group_visible,
            self._rule_visible_by_cat,
            self._refresh_table,
            self._filter_only_viol,
        )
        select_all_CB["command"] = lambda: self.rule_manager.make_all_select(
            self._select_all_var
        )

        self._open_group_manager(self.rule_filter_frame)

        # Meta rows: Run By / Tool / Design
        meta_container = ttk.Frame(head_content, style="Card.TFrame")

        # Run by
        run_row = ttk.Frame(meta_container, style="Card.TFrame")
        run_row.pack(side="top", fill="x", padx=0, pady=(0, 2))
        self.lbl_run_by_key = ttk.Label(
            run_row, text="Run by:", style="Card.Muted.TLabel"
        )
        self.lbl_run_by_val = ttk.Label(run_row, text="-", style="Card.TLabel")
        self.lbl_run_by_key.pack(side="left")
        self.lbl_run_by_val.pack(side="left", padx=(6, 0))

        # Tool
        tool_row = ttk.Frame(meta_container, style="Card.TFrame")
        tool_row.pack(side="top", fill="x", padx=0, pady=(0, 2))
        self.lbl_tool_key = ttk.Label(tool_row, text="Tool:", style="Card.Muted.TLabel")
        self.lbl_tool_val = ttk.Label(tool_row, text="-", style="Card.TLabel")
        self.lbl_tool_key.pack(side="left")
        self.lbl_tool_val.pack(side="left", padx=(6, 0))

        # Design
        design_row = ttk.Frame(meta_container, style="Card.TFrame")
        design_row.pack(side="top", fill="x", padx=0, pady=(0, 2))
        self.lbl_design_key = ttk.Label(
            design_row, text="Design:", style="Card.Muted.TLabel"
        )
        self.lbl_design_val = ttk.Label(design_row, text="-", style="Card.TLabel")
        self.lbl_design_key.pack(side="left")
        self.lbl_design_val.pack(side="left", padx=(6, 0))

        self.badge_err = tk.Label(
            badges_row, text="ERR: 0", padx=10, pady=4, bd=0, highlightthickness=0
        )
        self.badge_warn = tk.Label(
            badges_row, text="WARN: 0", padx=10, pady=4, bd=0, highlightthickness=0
        )
        self.badge_info = tk.Label(
            badges_row, text="INFO: 0", padx=10, pady=4, bd=0, highlightthickness=0
        )
        self.badge_err.pack(side="left", padx=(0, 8), expand=True, fill=tk.X)
        self.badge_warn.pack(side="left", padx=(0, 8), expand=True, fill=tk.X)
        self.badge_info.pack(side="left", padx=(0,), expand=True, fill=tk.X)

    def _build_filter_section(self):
        """
        Build the Filters card in the left pane: search box, filter toggles,
        severity and pin-type comboboxes, plus actions (Select Violations, Export CSV).
        """
        tk.Label(
            self.filter_loaded_macro_frame,
            text="Filter",
            font=("Segoe UI", 10, "normal"),
            bg="#dcdad5",
            fg="#333",
            justify="left",
        ).pack(anchor="w")

        search_entry = ttk.Entry(
            self.filter_loaded_macro_frame, textvariable=self._filter_text
        )
        search_entry.pack(ipady=4, expand=True, fill=tk.X)
        search_entry.bind("<KeyRelease>", lambda e: self._refresh_table())
        self._search_entry = search_entry
        Tooltip(search_entry, "Filter by pin or entity (Ctrl+F)")
        self.add_placeholder_to(search_entry, "Search on pin name")
        options_row = ttk.Frame(self.filter_loaded_macro_frame, style="StyleSad.TFrame")
        options_row.pack(side="top", fill="x", padx=2, pady=(0, 4))

        # Then update the checkbox command:
        ttk.Checkbutton(
            options_row,
            text="Only Rows and Columns with Violations",
            variable=self._filter_only_viol,
            command=self._on_only_violated_toggle,
            style="Filter.TCheckbutton",
        ).pack(side=tk.LEFT, anchor="w", pady=(0, 5))

        # --- Row 3: Severity selector ---
        severity_row = ttk.Frame(self.filter_loaded_macro_frame, style="StyleSad.TFrame")
        severity_row.pack(side="top", fill="x", pady=(0, 4))
        tk.Label(
            severity_row,
            text="Severity ",
            font=("Segoe UI", 10, "normal"),
            width=9,
            justify="left",
            bg="#dcdad5",
            fg="#333",
        ).pack(side="left", padx=0)

        severity_combo = ttk.Combobox(
            severity_row,
            textvariable=self._filter_sev,
            values=["ALL", "ERROR", "WARNING", "INFO"],
            width=12,
            state="readonly",
            style="Flat.SpecLoaderFrame.TCombobox",
        )
        severity_combo.pack(side="left", ipady=4, expand=True, fill=tk.X)
        severity_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_table())

        # --- Row 4: Pin type selector ---
        pin_type_row = ttk.Frame(self.filter_loaded_macro_frame, style="StyleSad.TFrame")
        pin_type_row.pack(side="top", fill="x", pady=(0, 6))
        tk.Label(
            pin_type_row,
            text="Pin Type ",
            font=("Segoe UI", 10, "normal"),
            width=9,
            justify=tk.LEFT,
            bg="#dcdad5",
            fg="#333",
        ).pack(side="left", padx=0)

        self.cb_type = ttk.Combobox(
            pin_type_row,
            textvariable=self._filter_type,
            values=["ALL"],
            width=16,
            state="readonly",
            style="Flat.SpecLoaderFrame.TCombobox",
        )
        self.cb_type.pack(
            side="left",
            ipady=4,
            expand=True,
            fill=tk.X,
        )
        self.cb_type.bind("<<ComboboxSelected>>", lambda e: self._refresh_table())

    def _on_only_violated_toggle(self):
        self._refresh_table()
        self._update_rules_filter_ui()
        self.rule_manager.disable_enable_rules(
            self.only_columes_to_show_by_click_only_violation
        )
    
        
    def add_placeholder_to(
        self,
        widget: ttk.Entry,
        placeholder_text: str,
        color_placeholder="grey",
        color_normal="black",
    ):
        """
        Adds a professional placeholder behavior to a ttk.Entry widget and
        tracks whether the placeholder is currently displayed.
        """

        # Track placeholder state on the widget (used by _get_search_query)
        widget._pc_placeholder_text = placeholder_text
        widget._pc_is_placeholder = False  # flips to True when placeholder is inserted

        def on_focus_in(event):
            """Remove placeholder when user clicks to type."""
            current_text = widget.get()
            current_color = str(widget.cget("foreground"))
            if current_text == placeholder_text and current_color == color_placeholder and getattr(widget, "_pc_is_placeholder", False):
                widget.delete(0, tk.END)
                widget.configure(foreground=color_normal)
                widget._pc_is_placeholder = False

        def on_focus_out(event):
            """Restore placeholder if left empty."""
            if not widget.get():
                widget.delete(0, tk.END)
                widget.insert(0, placeholder_text)
                widget.configure(foreground=color_placeholder)
                widget._pc_is_placeholder = True
            else:
                widget.configure(foreground=color_normal)
                widget._pc_is_placeholder = False

        # Bind events
        widget.bind("<FocusIn>", on_focus_in)
        widget.bind("<FocusOut>", on_focus_out)

        # Initialize placeholder immediately if the entry starts empty
        try:
            if not widget.get():
                on_focus_out(None)
            else:
                widget.configure(foreground=color_normal)
                widget._pc_is_placeholder = False
        except Exception:
            pass

    
    def _get_search_query(self) -> str:
        """
        Return the effective search query, treating placeholder text as 'no query'.
        Falls back to the StringVar value if the entry is not available.
        """
        try:
            if self._search_entry is not None:
                # Ignore the placeholder as a real query
                if getattr(self._search_entry, "_pc_is_placeholder", False):
                    return ""
                return (self._search_entry.get() or "").strip()
        except Exception:
            pass

        # Fallback to StringVar; guard against placeholder being saved there
        try:
            val = (self._filter_text.get() or "").strip()
            placeholder = getattr(self._search_entry, "_pc_placeholder_text", None)
            if placeholder and val == placeholder:
                return ""
            return val
        except Exception:
            return ""


    
    def _build_table_section(self):
        """
        Build the right-side main area: Soft-UI table card (Treeview + header canvas)
        and details card, lay them out, and initialize the table widgets.
        """
        # Choose container: the right pane or root fallback
        container = getattr(self, "_right_pane", self)
        container.config(background="#d4d4d4")

        self._loading_yaml_frame = tk.Frame(container)
        # self._loading_yaml_frame.pack(expand=True, fill=tk.BOTH, )

        self._loading_center_frame = tk.Frame(self._loading_yaml_frame, )
        self._loading_center_frame.pack(expand=True, anchor="center", padx=(0, 100))

        self._loading_progressbar = ttk.Progressbar(self._loading_center_frame, orient="horizontal", length=
                        400, mode="indeterminate")
        self._loading_progressbar.pack()
        tk.Label(
            self._loading_center_frame,
            text="Loading selected YAML file",
            font=("Segoe UI", 10, "normal"),
            fg="#333",
            justify="center",
        ).pack()

        



        # #Start
        # self._main_container.pack_forget()
        # self._loading_yaml_frame.pack(expand=True, fill=tk.BOTH, )
        # self._loading_progressbar.start(100)

        # #Stop
        # self._loading_progressbar.stop()
        # self._loading_yaml_frame.pack_forget()
        # self._main_container.pack(fill="both", expand=True, padx=8, pady=(8, 8))


        self._empty_main_frame = tk.Frame(container)
        self._empty_main_frame.pack(expand=True, fill=tk.BOTH)
        lbl_header = tk.Label(
            self._empty_main_frame,
            text="Pick a YAML to see the violations \nor\nLoad a project and select any macro form the left panel",
            font=("Segoe UI", 10, "normal"),
            fg="#333",
            justify="center",
        )
        lbl_header.pack(expand=True, anchor="center", padx=(0, 20))

        # Outer container for table + details cards
        self._main_container = tk.Frame(container, bg="#d4d4d4")

        # NEW: vertical paned window that will hold the two cards with a draggable sash
        self._main_split = ttk.Panedwindow(
            self._main_container, orient="vertical", style="Card.TPanedwindow"
        )
        self._main_split.pack(fill="both", expand=True)

        # Soft-UI cards
        self.table_card = SoftFrame(
            self._main_container,
            bg="#d4d4d4",
            light="#d4d4d4",
            dark=self.colors["shadow_dark"],
            radius=0,
            pad=0,
        )
        self.details_card = SoftFrame(
            self._main_container,
            bg="#d4d4d4",
            light="#d4d4d4",
            dark=self.colors["shadow_dark"],
            radius=0,
            pad=0,
        )

        # Set relative grow weights via paneconfigure (this is the ttk way)
        try:
            self._main_split.paneconfigure(self.table_card, weight=7)
            self._main_split.paneconfigure(self.details_card, weight=3)
        except Exception:
            # Some Tk builds may ignore weight; safe to swallow
            pass

        # Build the Treeview table inside the table card
        self._build_table(self.table_card.content)
        # After the UI is laid out, restore the saved sash position or apply default
        self.after_idle(self._apply_main_split_initial_position)

        # Persist sash position as soon as the user finishes dragging
        self._main_split.bind("<ButtonRelease-1>", lambda e: self._persist_main_split())

        self._main_split.add(self.table_card)
        self._main_split.add(self.details_card)

        def _update_pan_window_dispaly_area():
            self._main_split.update_idletasks()
            total_height = self._main_split.winfo_height()
            self._main_split.sashpos(0, int(total_height * 0.70))
            # self._main_split.sashpos(0, 700)

        def _update_pan_window_dispaly_area_event(e):
            _update_pan_window_dispaly_area()

        self._main_container.after(250, _update_pan_window_dispaly_area)
        self._main_container.bind("<Configure>", _update_pan_window_dispaly_area_event)

    def _build_details_section(self):
        """
        Build the bottom details area as a Notebook with two tabs:
        - Details (rich text panel for per-pin/per-rule info)
        - Analysis Tab (table view for analyzer-driven summaries)
        """
        # Notebook container
        self._details_notebook = ttk.Notebook(
            self.details_card.content, style="Details.TNotebook"
        )
        self._details_notebook.pack(fill="both", expand=True)

        # --- Tab 1: Details view (styled panel) ---
        # self.analysis_tab

        # --- Tab 2: Analysis Tab (placeholder table) ---
        self.analysis_tab_ = ttk.Frame(self._details_notebook)
        self.analysis_tab_.pack(fill="both", expand=True)

        # Add tab to notebook
        self._details_notebook.add(self.analysis_tab_, text="Analysis")

        self.analysis_tab = ViolationAnalysisTabFrame(self.analysis_tab_, data={})
        self.analysis_tab.pack(fill=tk.BOTH, expand=True)
        # self.analysis_tab.update_file_open_command(self.cfg["file_viewer_cmd"])

        self.detail = DetailsBottom(
            self.analysis_tab.details_section_frame,
            font_family=self._font_family,
            colors=self.colors,
            _focus_analysis_tab=self._focus_analysis_tab,
            update_analysis_tab_content=self.update_analysis_tab_content,
        )
        self.detail.pack(fill="both", expand=True)
        self.analysis_tab.update_mouse_scroll()

        # Bind notebook tab changes to populate the Analysis Tab on demand
        try:
            self._details_notebook.bind(
                "<<NotebookTabChanged>>", self._on_details_tab_changed
            )
        except Exception:
            # Defensive: ignore binding issues on older Tk builds
            pass

    def _focus_analysis_tab(self):
        self._details_notebook.select(self.analysis_tab_)

    def update_analysis_tab_content(self, valid_data_short):
        self.analysis_tab.update_data(valid_data_short)

    def _on_details_tab_changed(self, event=None):
        """
        When the Details notebook switches to the Analysis tab, populate it
        with the analyzer summary (unless a custom analysis view is active).
        """
        try:
            notebook = getattr(self, "_details_notebook", None)
            if notebook is None:
                return

            selected_index = notebook.index(notebook.select())
            # Analysis Tab is index 1
            if selected_index == 1:
                # Do not overwrite custom analysis views (rule-specific)
                if getattr(self, "_analysis_custom_view_active", False):
                    return

        except Exception:
            # Defensive: ignore transient notebook state/layout issues
            pass

    def _populate_analysis_tree(self, data: dict):
        """Fill `self.analysis_tree` with rows from analyzer output.

        Expected `data` format: { 'rules': [ {rule_id, category, total, errors, warnings, info} ],
        'categories': [ {category, total_violations, rules: [...] } ] }
        """
        try:
            tree = getattr(self, "analysis_tree", None)
            if tree is None:
                return
            # Clear existing rows
            tree.delete(*tree.get_children())
            # Populate a simple view: rule_id | category | total | errors | warnings | info
            # Reconfigure columns to hold full data
            cols = ("rule_id", "category", "total", "errors", "warnings", "info")
            tree.config(columns=cols)
            for c in cols:
                tree.heading(c, text=c.replace("_", " ").title())
                if c == "rule_id":
                    tree.column(c, width=220, anchor="w")
                elif c == "category":
                    tree.column(c, width=140, anchor="w")
                else:
                    tree.column(c, width=80, anchor="center")

            for r in data.get("rules", []):
                tree.insert(
                    "",
                    "end",
                    values=(
                        r.get("rule_id"),
                        r.get("category"),
                        r.get("total"),
                        r.get("errors"),
                        r.get("warnings"),
                        r.get("info"),
                    ),
                )
        except Exception:
            pass

    def _build_bottom_section(self):
        """
        Build the bottom status bar (Ready/Loaded messages) and wire global shortcuts.
        """
        # Choose container: the bottom frame created in _build_ui (fallback to root)
        container = getattr(self, "_bottom_frame", self)

        # Status label
        self.status = ttk.Label(
            container,
            text="Ready — Load a YAML.",
            anchor="w",
            style="Status.TLabel",
        )
        self.status.pack(fill="x", padx=12, pady=(4, 4))

        # Paint severity badges (ERR/WARN/INFO) to match theme
        self._paint_badges()

        # Keyboard shortcuts
        self.bind_all("<Control-o>", lambda e: self._open_yaml())
        self.bind_all("<Control-f>", lambda e: self._focus_search())
        self.bind_all("<F5>", lambda e: self._reload_yaml())

        # Periodic header poller (keeps category bands/labels in sync)
        self.after(200, self._header_poller)

    def _paint_badges(self):
        """
        Style the ERR/WARN/INFO count badges to match the current theme.
        """
        # Ensure badge widgets exist before styling
        if not (
            hasattr(self, "badge_err")
            and hasattr(self, "badge_warn")
            and hasattr(self, "badge_info")
        ):
            return

        palette = self.colors
        badge_font = self._tk_font(self._size_small)

        # Apply themed backgrounds/foregrounds
        self.badge_err.configure(
            bg=palette["badge_err"], fg=palette["badge_text_light"], font=badge_font
        )
        self.badge_warn.configure(
            bg=palette["badge_warn"], fg=palette["badge_text_dark"], font=badge_font
        )
        self.badge_info.configure(
            bg=palette["badge_info"], fg=palette["badge_text_dark"], font=badge_font
        )


    

    def _build_menu(self):
        """
        Create the main menu bar: File (open/reload/export), Re Run (RunEditor),
        View (filters/legend/unhide), and Help (About), plus the Recent submenu.
        """
        # Root menubar
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # --- File menu ---
        m_file = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="File", menu=m_file)

        m_file.add_command(
            label="Open YAML…", accelerator="Ctrl+O", command=self._open_yaml
        )
        m_file.add_command(
            label="Reload YAML", accelerator="F5", command=self._reload_yaml
        )

        # Recent submenu
        recent_menu = tk.Menu(m_file, tearoff=False)
        m_file.add_cascade(label="Open Recent", menu=recent_menu)
        self._menu_recent = recent_menu

        # m_file.add_separator()
        # m_file.add_command(label="Export CSV…", command=self._export_csv)

        m_file.add_separator()
        m_file.add_command(label="Exit", command=self._on_close)

        # --- Re Run menu ---
        m_rerun = tk.Menu(menubar, tearoff=False)
        menubar.add_command(label="Re Run", command=self._open_run_editor)
        menubar.add_command(label="Waiver", command=self._open_waiver_window)
        menubar.add_command(label="Settings", command=self._open_settings_rename_headers)

        # --- Help menu ---
        m_help = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Help", menu=m_help)
        m_help.add_command(
            label="About",
            command=lambda: messagebox.showinfo(
                "About", "Pincheck Scoreboard — YAML-driven (Tk)\nPython 3.x"
            ),
        )

        # Populate the Recent submenu from settings
        self._refresh_recent_menu()

    # ---------- TABLE + Category band ----------

    def _build_table(self, parent):
        """Thin wrapper: delegate table creation to TableManager to keep the
        original public API while isolating implementation details in a single
        class for easier testing and maintenance."""
        self.table_manager = TableManager(self, parent)
        self.table_manager.build()

    def _severity_to_waiver_token(self, sev: str) -> str:
        """
        Map pincheck severity strings to WaiverRuelsFrame expected badges.
        Input: 'ERROR' | 'WARNING' | 'INFO' (case-insensitive), optionally 'FATAL'.
        Output: 'Error' | 'Warning' | 'Message' | 'Fatal'
        """
        s = (sev or "").strip().upper()
        if s == "FATAL":
            return "Fatal"
        if s == "ERROR":
            return "Error"
        if s == "WARNING":
            return "Warning"
        # Default for INFO/unknown
        return "Message"

    def _worst_severity(self, severities):
        """
        Return the worst severity among given tokens using pincheck ranking:
        ERROR > WARNING > INFO. Accepts mixed case and unknowns.
        """
        rank = {"ERROR": 3, "WARNING": 2, "INFO": 1}
        worst = 0
        for s in severities or []:
            worst = max(worst, rank.get((s or "").upper(), 0))
        if worst >= 3:
            return "ERROR"
        if worst >= 2:
            return "WARNING"
        if worst >= 1:
            return "INFO"
        return "INFO"  # default to INFO when nothing known

    # --- ADD: build Waiver data including all catalog rules ---
    def _build_waiver_data(self) -> dict:
        """
        Build the nested dict WaiverRuelsFrame expects:
        {
        "<Category>": {
            "<RuleID>": { "Severty": "<Error|Warning|Message|Fatal>", "comment": "" },
            ...
        },
        ...
        }
        Rules: include ALL rules from the catalog; if the run has violations
        for a rule, upgrade the severity to the worst seen for that rule.
        """
        if not self._rundata:
            return {}

        # 1) Group violations per rule_id to compute worst severity if present
        from collections import defaultdict
        viol_by_rule = defaultdict(list)
        for v in self._rundata.violations:
            # Guard against missing rule_id
            rid = v.rule_id or ""
            if rid:
                viol_by_rule[rid].append(v)

        # 2) Compose category -> rules dict using the catalog
        out: dict = {}
        for rid, rdef in self._rundata.rule_catalog.items():
            category = (rdef.category or "META").strip() or "META"
            # Worst severity from actual violations if any, else catalog default
            if viol_by_rule.get(rid):
                worst = self._worst_severity([v.severity for v in viol_by_rule[rid]])
                waiver_sev = self._severity_to_waiver_token(worst)
            else:
                waiver_sev = self._severity_to_waiver_token(rdef.severity)

            out.setdefault(category, {})
            out[category][rid] = {
                "Severty": waiver_sev,   # NOTE: intentional misspelling to match UI
                "comment": ""            # user will type in the waiver window
            }

        # 3) Edge-case: violations for rule_ids not present in catalog
        #     (ensure they also appear, using violation category/severity)
        for rid, vlist in viol_by_rule.items():
            if rid in self._rundata.rule_catalog:
                continue
            # pick category from first violation, fallback META
            cat = (vlist[0].category or "META").strip() or "META"
            worst = self._worst_severity([v.severity for v in vlist])
            waiver_sev = self._severity_to_waiver_token(worst)
            out.setdefault(cat, {})
            out[cat][rid] = {"Severty": waiver_sev, "comment": ""}

        return out


    def _preferred_viewer_cmd(self) -> str:
        """
        Return the configured file viewer command/path as a raw string.
        Defaults to 'gedit' for continuity when missing.
        """
        try:
            raw = (self.cfg or {}).get("file_viewer_cmd", "gedit")
        except Exception:
            raw = "gedit"
        return (str(raw) or "gedit").strip()

    def _is_terminal_editor(self, cmd_token: str) -> bool:
        """
        Heuristic: treat these as terminal editors that should run inside a terminal emulator.
        """
        base = os.path.basename(cmd_token).lower()
        return base in {"nano", "vim", "vi", "less", "emacs", "nvim"}

    def _open_with_preferred_viewer(self, target_path: str) -> None:
        """
        Open a file using the command/path the user specified in settings.

        Rules:
        - If the command contains a space-separated program and args, we append the file path as the last arg.
        - If the command looks like a terminal editor (nano, vim, etc.), run via terminal emulator:
                x-terminal-emulator -e <cmd ...> <file>
            (override terminal via env PINCHECK_TERMINAL)
        - Otherwise, run the command directly: <cmd ...> <file>
        - If the command contains a `{file}` token, we expand it and DO NOT append the file at the end.

        Everything runs in a background thread; errors are shown to the user.
        """

        def _worker():
            try:
                raw_cmd = self._preferred_viewer_cmd()
                if not raw_cmd:
                    raw_cmd = "xdg-open"

                # If the user provides a {file} placeholder, expand it literally and run as shell
                if "{file}" in raw_cmd:
                    cmd_str = raw_cmd.replace("{file}", shlex.quote(target_path))
                    # Use repository helper; fallback to os.system if needed
                    try:
                        Misc.run_system_cmd(cmd_str, capture_output=False)  # type: ignore[attr-defined]
                    except Exception:
                        os.system(cmd_str)
                    return

                # Tokenize the command into args
                try:
                    base_cmd_parts = shlex.split(raw_cmd)
                except Exception:
                    base_cmd_parts = [raw_cmd]

                # Decide terminal vs GUI
                if base_cmd_parts and self._is_terminal_editor(base_cmd_parts[0]):
                    term = os.environ.get("PINCHECK_TERMINAL", "x-terminal-emulator")
                    cmd = [term, "-e"] + base_cmd_parts + [target_path]
                else:
                    cmd = base_cmd_parts + [target_path]

                # Execute without capturing output
                Misc.run_system_cmd(cmd, capture_output=False)  # type: ignore[attr-defined]
            except Exception as exc:
                try:
                    messagebox.showerror(
                        "Open File", f"Failed to open '{target_path}':\n{exc}"
                    )
                except Exception:
                    pass

        threading.Thread(target=_worker, daemon=True).start()

    def _open_settings_rename_headers(self) -> None:
        """
        Settings window:
        • Top section: File viewer command/path (Entry field)
        • Below: Rename Table Header (grouped by Category; existing functionality)
        """
        # --- Load rule catalog (unchanged) ---
        try:
            catalog = list((MEMPHYS_PIN_CHECK_CONFIG.get("rule_catalog") or []))
        except Exception:
            catalog = []
        if not catalog:
            # Quietly return if no catalog yet
            return

        # Build category -> rules mapping (unchanged)
        rules_by_cat: dict[str, list[dict]] = {}
        for r in catalog:
            cat = r.get("category") or "META"
            rules_by_cat.setdefault(cat, []).append(r)
        for cat in list(rules_by_cat.keys()):
            rules_by_cat[cat].sort(key=lambda rr: str(rr.get("rule_id") or "").lower())

        # Determine display order: prefer known group order; append new categories
        group_order = list(getattr(self, "_group_order", [])) or []
        remaining = [c for c in sorted(rules_by_cat.keys()) if c not in group_order]
        ordered_categories = group_order + remaining

        # --- Build Toplevel window (renamed to Settings) ---
        win = tk.Toplevel(self)
        win.title("Settings")
        try:
            win.configure(bg=self.colors.get("surface", "#f0f0f0"))
        except Exception:
            pass
        win.geometry("720x640")
        win.transient(self)

        def _close_window():
            try:
                try:
                    win.grab_release()
                except Exception:
                    pass
                win.destroy()
            except Exception:
                pass

        win.protocol("WM_DELETE_WINDOW", _close_window)

        # --- Header bar ---
        header_bar = ttk.Frame(win)
        header_bar.pack(fill="x", pady=(6, 10), padx=12)
        ttk.Label(
            header_bar,
            text="Settings",
            font=(self._font_family, 11, "bold"),
        ).pack(side="left")

        # =========================
        # TOP: File viewer command/path
        # =========================
        viewer_frame = ttk.LabelFrame(win, text="File Viewer", padding=(10, 8))
        viewer_frame.pack(fill="x", padx=12, pady=(0, 8))

        ttk.Label(viewer_frame, text="Command or path:", width=22).pack(side="left")
        viewer_var = tk.StringVar(value=(self.cfg.get("file_viewer_cmd") or "gedit"))

        viewer_entry = ttk.Entry(
            viewer_frame,
            textvariable=viewer_var,
            width=48,
            style="Flat.SpecLoaderFrame.TEntry",  # reuse your flat entry style
        )
        viewer_entry.pack(side="left", padx=(8, 0), ipady=4, fill="x", expand=True)

        # Helper hint (muted)
        hint = (
            "Examples: nano   |   vim   |   gedit   |   /depot/tools/vscode/bin/vscode\n"
            "Advanced: include {file} where the file path should be inserted."
        )
        ttk.Label(viewer_frame, text=hint, style="Card.Muted.TLabel").pack(
            side="left", padx=12
        )

        # ===============================
        # BODY: Rename Table Header (unchanged)
        # ===============================

        body = ttk.Frame(win)
        body.pack(fill="both", expand=True, padx=12, pady=8)

        canvas = tk.Canvas(
            body,
            highlightthickness=0,
            bd=0,
            bg=self.colors.get("panel", "#ffffff"),
        )
        vsb = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = ttk.Frame(canvas, style="Card.TFrame")
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_mousewheel(event):
            try:
                delta = getattr(event, "delta", None)
                if delta is None:
                    return
                step = -1 if delta > 0 else 1
                canvas.yview_scroll(step, "units")
                return "break"
            except Exception:
                pass

        def _on_button4(event):
            canvas.yview_scroll(-1, "units")
            return "break"

        def _on_button5(event):
            canvas.yview_scroll(1, "units")
            return "break"

        win.bind_all("<Button-4>", _on_button4)
        win.bind_all("<Button-5>", _on_button5)

        def _on_cfg(_evt=None):
            inner.update_idletasks()
            canvas.config(scrollregion=(0, 0, inner.winfo_width(), inner.winfo_height()))
            canvas.itemconfigure(inner_id, width=canvas.winfo_width())

        inner.bind("<Configure>", _on_cfg)
        canvas.bind("<Configure>", _on_cfg)

        current_overrides = (self.cfg or {}).get("rule_label_overrides", {}) or {}
        rows_widgets: list[tuple[str, tk.BooleanVar, ttk.Entry, callable]] = []

        # Category title + rule rows (unchanged)
        for category in ordered_categories:
            if category not in rules_by_cat:
                continue

            cat_frame = ttk.Frame(inner)
            cat_frame.pack(fill="x", pady=(2, 6))
            ttk.Label(
                cat_frame,
                text=str(category),
                font=(self._font_family, 10, "bold"),
            ).pack(side="left")

            hdr = ttk.Frame(inner)
            hdr.pack(fill="x", pady=(0, 4))
            ttk.Label(hdr, text="Rule ID", width=34).pack(side="left", padx=(0, 4))
            ttk.Label(hdr, text="Short Name", width=38).pack(side="left", padx=(0, 4))

            for rule in rules_by_cat[category]:
                rid = rule.get("rule_id")
                default_short = rule.get("short_name") or rule.get("short") or rid
                effective_short = MEMPHYS_RULE_SHORT_MAP.get(rid, default_short)
                has_override = rid in current_overrides

                row = ttk.Frame(inner)
                row.pack(fill="x", pady=2)

                ttk.Label(row, text=str(rid), width=34).pack(side="left", padx=(0, 4))
                var_chk = tk.BooleanVar(value=has_override)
                chk = ttk.Checkbutton(row, variable=var_chk)
                chk.pack(side="left", padx=(0, 4))

                ent = ttk.Entry(row, width=28)
                ent.insert(0, current_overrides.get(rid, effective_short))
                try:
                    ent.configure(state=("normal" if has_override else "disabled"))
                except Exception:
                    pass
                ent.pack(side="left", padx=(0, 4), fill="x", expand=True)

                def _toggle_entry(_var=var_chk, _entry=ent, _eff=effective_short):
                    try:
                        if _var.get():
                            _entry.configure(state="normal")
                        else:
                            _entry.configure(state="disabled")
                            _entry.delete(0, tk.END)
                            _entry.insert(0, _eff)
                    except Exception:
                        pass

                chk.configure(command=_toggle_entry)

                def _resolve_default(_rid=rid, _fallback=default_short):
                    return MEMPHYS_RULE_SHORT_MAP.get(_rid, _fallback) or _rid

                rows_widgets.append((rid, var_chk, ent, _resolve_default))

        # --- Actions row ---
        actions = ttk.Frame(win)
        actions.pack(fill="x", padx=12, pady=(6, 12))

        def _rebuild_short_map_to_defaults():
            try:
                base = {}
                for r in MEMPHYS_PIN_CHECK_CONFIG.get("rule_catalog") or []:
                    rid = r.get("rule_id")
                    if not rid:
                        continue
                    base[rid] = r.get("short_name") or r.get("short") or rid
                global MEMPHYS_RULE_SHORT_MAP
                MEMPHYS_RULE_SHORT_MAP = base
            except Exception:
                pass

        def _save():
            # Collect header overrides (unchanged)
            new_overrides = {}
            for rid, var_chk, ent, _resolver in rows_widgets:
                if var_chk.get():
                    val = (ent.get() or "").strip()
                    if not val:
                        continue
                    new_overrides[rid] = val

            # Persist overrides
            try:
                self.cfg.setdefault("rule_label_overrides", {})
                self.cfg["rule_label_overrides"] = dict(new_overrides)
            except Exception:
                pass

            # Persist file viewer command/path
            try:
                self.cfg["file_viewer_cmd"] = viewer_var.get().strip()
            except Exception:
                pass

            # Save to disk & apply
            save_settings(self.cfg)
            self._apply_rule_label_overrides()
            self.analysis_tab.update_file_open_command(self.cfg["file_viewer_cmd"])

            # Close window
            _close_window()

        def _restore_defaults():
            # Clear overrides only (viewer cmd remains unchanged)
            try:
                self.cfg.setdefault("rule_label_overrides", {})
                self.cfg["rule_label_overrides"] = {}
                save_settings(self.cfg)
            except Exception:
                pass
            _rebuild_short_map_to_defaults()
            try:
                self._apply_rule_label_overrides()
            except Exception:
                pass
            # Update UI rows to reflect defaults immediately
            for rid, var_chk, ent, resolve_default in rows_widgets:
                var_chk.set(False)
                try:
                    ent.configure(state="disabled")
                    eff = resolve_default()
                    ent.delete(0, tk.END)
                    ent.insert(0, eff)
                except Exception:
                    pass

        ttk.Button(actions, text="Save", command=_save).pack(side="right", padx=(6, 0))
        ttk.Button(actions, text="Restore Defaults", command=_restore_defaults).pack(
            side="right", padx=(6, 0)
        )
        ttk.Button(actions, text="Cancel", command=_close_window).pack(side="right")

    # ---------- Load / Refresh ----------

    def _open_yaml(self):
        """
        Prompt the user to select a Pincheck YAML file and load it into the UI.
        """
        selected_path = filedialog.askopenfilename(
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")],
            title="Select a Pincheck YAML report",
        )
        if not selected_path:
            return
        self._load_yaml_path(selected_path)


    def _reload_yaml(self):
        """
        Reload the last opened YAML report and reapply table filters, overlays,
        headings, and visuals so the UI returns to a consistent state.
        """
        if not self._last_yaml_path:
            try:
                messagebox.showinfo("Reload YAML", "No previously loaded YAML.")
            except Exception:
                pass
            return

        # 1) Reload the YAML (this already rebuilds indices and table once)
        self._load_yaml_path(self._last_yaml_path)

        # 2) Reapply rule label overrides (user settings) so headers reflect current config
        try:
            self._apply_rule_label_overrides()
        except Exception:
            pass

        # 3) Reapply theme styles (safe no-op if unchanged)
        try:
            self._apply_theme()
        except Exception:
            pass

        # 4) Ensure the Rules filter UI reflects the current "Only Violations" overlay
        #    and user visibility maps (category + per-rule)
        try:
            # When "Only rows/columns with violations" is ON, the overlay map drives visibility.
            # This keeps the left filter panel synced with what the table shows.
            self._update_rules_filter_ui()
            # Also drive the RuleManager checkboxes to match overlay state
            self.rule_manager.disable_enable_rules(self.only_columes_to_show_by_click_only_violation)
        except Exception:
            pass

        # 5) Force column rebuild and row refresh so the final state is consistent
        try:
            self._rebuild_table_columns()
        except Exception:
            pass

        try:
            self._refresh_table()
        except Exception:
            pass

        # 6) Redraw the category header band and repaint badges to match current theme
        try:
            self._redraw_group_header()
        except Exception:
            pass

        try:
            self._paint_badges()
        except Exception:
            pass

        # 7) UX: Update status line
        try:
            self.status.configure(text=f"Reloaded: {self._last_yaml_path}")
        except Exception:
            pass

        # 8) Optional: keep Analysis tab toggle hidden until a cell is clicked
        try:
            if hasattr(self, "analysis_tab") and self.analysis_tab:
                self.analysis_tab.hide_details_toggle()
        except Exception:
            pass


    def _load_yaml_path(self, path: str):
        """
        Load a YAML report from `path`, normalize it into RunData, and refresh
        the UI components that depend on the data.

        This function performs the following high-level steps:
          - Parse YAML into a `RunData` structure via `load_yaml_to_rundata`.
          - Recompute indices and filters (pin list, rule catalog, violations).
          - Rebuild the visible columns and refresh the table contents.
        """
        try:
            run_data = load_yaml_to_rundata(path)
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load YAML:\n{e}")
            return
        # Persist path and store normalized run data
        self._last_yaml_path = path
        self._rundata = run_data
        # Loading a new YAML should reset any custom Analysis view state
        try:
            self._analysis_custom_view_active = False
        except Exception:
            pass
        # Build quick lookup sets used by filtering and display
        self._known_pins = {pin_rec.pin_name for pin_rec in run_data.pins}
        self._pin_types = {
            pin_rec.pin_type for pin_rec in run_data.pins if pin_rec.pin_type
        }

        if self._empty_main_frame.winfo_ismapped():
            self._empty_main_frame.pack_forget()
            # self._main_container.pack(fill="both", expand=True, padx=8, pady=(8, 8))

        
        
        #Open File Loading
        #Start
        self._main_container.pack_forget()
        self._loading_yaml_frame.pack(expand=True, fill=tk.BOTH, )
        self._loading_progressbar.start(100)

        


        def load__():
            self.analysis_tab._clean_up()

            self._rebuild_pin_type_filter()
            self._build_viol_index()
            self._compute_rules_by_category()
            self._update_header_and_badges()
            self._refresh_recent(path)
            self._rebuild_table_columns()
            self._refresh_table()
            self.status.configure(text=f"Loaded: {path}")
            self.load_rules_viewer()

            rules_by_category = getattr(self, "_rules_by_cat", {}) or {}
            group_order = list(getattr(self, "_group_order", [])) or sorted(
                rules_by_category.keys()
            )
            self.rule_manager.create_check_boxes(
                rules_by_category=rules_by_category, group_order=group_order
            )
            # Then optionally:
            try:
                if hasattr(self, "analysis_tab") and self.analysis_tab:
                    self.analysis_tab.hide_details_toggle()
            except Exception:
                pass


            

            #Close File Loading
            #Stop
            self._loading_progressbar.stop()
            self._loading_yaml_frame.pack_forget()
            self._main_container.pack(fill="both", expand=True, padx=8, pady=(8, 8))
        
        
            

        self.after(2000,load__)


    def _on_select_all_toggle(self):
        """
        Toggle all categories and rules ON/OFF based on the Select All checkbox.
        This safely updates maps and persistence first, and only refreshes UI
        when the relevant widgets are already created.
        """
        select_all = bool(self._select_all_var.get())

        # -- Update source-of-truth maps (safe at any time)
        for category in self._group_order or []:
            self._group_visible[category] = select_all

        for category, rules in (self._rules_by_cat or {}).items():
            self._rule_visible_by_cat.setdefault(category, {})
            for rule_id in rules:
                self._rule_visible_by_cat[category][rule_id] = select_all

        # -- Persist
        self.cfg.setdefault("rule_groups", {})
        self.cfg["rule_groups"]["visible"] = dict(self._group_visible)
        self.cfg["rule_groups"]["rules_visible"] = dict(self._rule_visible_by_cat)
        save_settings(self.cfg)

        # -- Sync on-screen checkbuttons only if the manager UI exists
        try:
            if hasattr(self, "inner_frame") and self.inner_frame:

                def _set_all_checkbuttons(widget):
                    if isinstance(widget, ttk.Checkbutton) and hasattr(widget, "_pc_var"):
                        try:
                            widget._pc_var.set(select_all)
                        except Exception:
                            pass
                    for child in widget.winfo_children():
                        _set_all_checkbuttons(child)

                _set_all_checkbuttons(self.inner_frame)
        except Exception:
            pass

        # -- Refresh columns/table only if the Treeview exists
        try:
            if hasattr(self, "tree") and self.tree:
                self._rebuild_table_columns()
                self._refresh_table()
        except Exception:
            pass

        # -- Optional status nudge
        try:
            self.status.configure(
                text=(
                    "All rules/categories ON"
                    if select_all
                    else "All rules/categories OFF"
                )
            )
        except Exception:
            pass

    def _on_header_right_click(self, event):
        """Context menu on the category band: resolve column under cursor."""
        # Compute which real column is under the cursor (account for xscroll)
        cols = self._measure_columns()  # [(colid, x, w), ...] in unscrolled coords
        if not cols:
            return
        offset = int(self._xscroll_first * max(1, self._col_total_width))
        x_actual = event.x + offset

        target_cid = None
        for colid, col_x, col_w in cols:
            if col_x <= x_actual <= (col_x + col_w):
                target_cid = colid
                break
        if not target_cid:
            return

        # Ignore base columns
        if target_cid in ("PIN", "DIR", "TYPE"):
            return

    def _show_header_tooltip(self, event, category: str, rule_id: str):
        """
        Show a small tooltip at the bottom-right of the mouse pointer, on header_canvas,
        with the category name (per your request).
        """
        # Ensure any previous tooltip is closed
        try:
            self._hide_header_tooltip()
        except Exception:
            pass

        try:
            tip = tk.Toplevel(self.header_canvas)
            tip.wm_overrideredirect(True)
            try:
                tip.attributes("-topmost", True)
            except Exception:
                pass

            # Bottom-right of mouse pointer
            x = event.x_root + 12
            y = event.y_root + 10
            tip.wm_geometry(f"+{x}+{y}")

            # Show only the category (you asked to show category)
            lbl = tk.Label(
                tip,
                text=f"{category}",
                background="#ffffe0",
                relief="solid",
                borderwidth=1,
                padx=6,
                pady=3,
                justify="left",
            )
            lbl.pack()

            self._header_hover_tip = tip
        except Exception:
            self._header_hover_tip = None

    def _hide_header_tooltip(self, event=None):
        """Destroy the header hover tooltip window if present."""
        tip = getattr(self, "_header_hover_tip", None)
        if tip is not None:
            try:
                tip.destroy()
            except Exception:
                pass
        self._header_hover_tip = None

    def _move_header_tooltip(self, event):
        """Reposition tooltip as the mouse moves over the same canvas item."""
        tip = getattr(self, "_header_hover_tip", None)
        if tip is not None:
            try:
                tip.wm_geometry(f"+{event.x_root + 12}+{event.y_root + 10}")
            except Exception:
                pass

    def _unhide_all_columns(self):
        """Turn ON every category and rule column, persist, and rebuild."""
        # ensure we have the latest rule map
        if not hasattr(self, "_rules_by_cat"):
            self._rules_by_cat = {}

        # flip every category ON
        for category in self._group_order:
            self._group_visible[category] = True

        # flip every rule under every category ON
        for category, rules in self._rules_by_cat.items():
            self._rule_visible_by_cat.setdefault(category, {})
            for rule_id in rules:
                self._rule_visible_by_cat[category][rule_id] = True

        # persist and rebuild UI
        self.cfg.setdefault("rule_groups", {})
        self.cfg["rule_groups"]["visible"] = dict(self._group_visible)
        self.cfg["rule_groups"]["rules_visible"] = dict(self._rule_visible_by_cat)
        save_settings(self.cfg)

        self._rebuild_table_columns()
        self._refresh_table()
        try:
            self.status.configure(text="All hidden columns restored.")
        except Exception:
            pass

    def _rebuild_pin_type_filter(self):
        """
        Refresh the Pin Type combobox options from discovered pin types and
        reset to 'ALL' if the current selection is no longer valid.
        """
        available_types = ["ALL"] + sorted(self._pin_types)
        self.cb_type.configure(values=available_types)

        current_selection = self._filter_type.get()
        if current_selection not in available_types:
            self._filter_type.set("ALL")

    def _build_viol_index(self):
        """
        Build the in-memory index: pin/entity → rule_id → [Violation].
        Clears previous state and repopulates from the loaded RunData.
        """
        self._viol_by_pin_by_rule = {}
        if not self._rundata:
            return

        for v in self._rundata.violations:
            pin_or_entity = v.pin_name or "<GLOBAL>"
            rules_map = self._viol_by_pin_by_rule.setdefault(pin_or_entity, {})
            rules_map.setdefault(v.rule_id, []).append(v)

    def _compute_rules_by_category(self):
        """
        Compute a mapping of category → [rule_id] from the rule catalog and violations,
        preserve group order/visibility, and sync the per-rule visibility map.
        """
        # Aggregate discovered rules per category from catalog and violations
        discovered: dict[str, set[str]] = {}
        for rule_id, rule_def in self._rundata.rule_catalog.items():
            category = rule_def.category or "META"
            discovered.setdefault(category, set()).add(rule_id)

        for violation in self._rundata.violations:
            category = violation.category or "META"
            discovered.setdefault(category, set()).add(violation.rule_id)

        # Initialize the public map and ensure all known groups are represented
        self._rules_by_cat = {}
        for group_name in self._group_order:
            discovered.setdefault(group_name, set())

        # Add any newly discovered categories to the end of the group order, default visible
        for group_name in sorted(set(discovered.keys())):
            if group_name not in self._group_order:
                self._group_order.append(group_name)
            self._group_visible.setdefault(group_name, True)

        # Finalize per-category sorted rule lists
        for group_name in self._group_order:
            self._rules_by_cat[group_name] = sorted(discovered.get(group_name, set()))

        # --- Keep per-rule visibility map in sync with discovered rules ---
        per_rule_visible = self._rule_visible_by_cat

        # Remove categories that no longer exist
        for stale_cat in list(per_rule_visible.keys()):
            if stale_cat not in self._rules_by_cat:
                del per_rule_visible[stale_cat]

        # Remove categories that no longer exist in discovered set
        for stale_cat in list(self._group_order):
            if stale_cat not in discovered:
                self._group_order.remove(stale_cat)

        # For existing categories: prune missing rules and add new rules with default True
        for cat_name, rule_ids in self._rules_by_cat.items():
            per_rule_visible.setdefault(cat_name, {})
            # Remove stale rules
            for stale_rule in list(per_rule_visible[cat_name].keys()):
                if stale_rule not in rule_ids:
                    del per_rule_visible[cat_name][stale_rule]
            # Add new rules defaulting to visible
            for rid in rule_ids:
                per_rule_visible[cat_name].setdefault(rid, True)

    def _update_header_and_badges(self):
        md = self._rundata.metadata

        # --- set values ---
        self.lbl_run_by_val.configure(text=(md.user or "-"))
        self.lbl_tool_val.configure(text=(md.tool or "-"))
        self.lbl_design_val.configure(text=(md.design or "-"))

        # --- set colors (not bold) ---
        # Pick any colors from your palette; these are good defaults:
        #   accent for Tool, info for Run by, and text (or another accent) for Design
        self.lbl_run_by_val.configure(
            foreground=self.colors.get("badge_info", self.colors["accent"])
        )
        self.lbl_tool_val.configure(foreground=self.colors["accent"])
        self.lbl_design_val.configure(foreground=self.colors["text"])

        # (Optional) dynamic severity-driven color for emphasis
        # err/warn/info counters still computed as before
        err = sum(
            1
            for rmap in self._viol_by_pin_by_rule.values()
            for vs in rmap.values()
            for v in vs
            if v.severity == "ERROR"
        )
        warn = sum(
            1
            for rmap in self._viol_by_pin_by_rule.values()
            for vs in rmap.values()
            for v in vs
            if v.severity == "WARNING"
        )
        info = sum(
            1
            for rmap in self._viol_by_pin_by_rule.values()
            for vs in rmap.values()
            for v in vs
            if v.severity == "INFO"
        )

        # Example: if there are errors, color Design red-ish to hint the run is problematic
        if err > 0:
            self.lbl_design_val.configure(foreground=self.colors["badge_err"])
        elif warn > 0:
            self.lbl_design_val.configure(foreground=self.colors["badge_warn"])

        # badges text update (unchanged)
        self.badge_err.configure(text=f"ERR: {err}")
        self.badge_warn.configure(text=f"WARN: {warn}")
        self.badge_info.configure(text=f"INFO: {info}")
        self._paint_badges()

    def _parse_col_id(self, colid: str):
        """Return (category, rule_id) from a column id; base cols return ("", colid)."""
        if "__" in colid:
            cat, rid = colid.split("__", 1)
            return cat, rid
        return "", colid

    # ---------- Recents ----------
    def _refresh_recent(self, path: str):
        """
        Move the given path to the top of the recent list (de-duplicated), persist, and update menu.
        """
        recent_list = self.cfg.get("recent_reports", [])
        if path in recent_list:
            recent_list.remove(path)
        recent_list.insert(0, path)

        # Keep up to 8 recents
        self.cfg["recent_reports"] = recent_list[:8]
        save_settings(self.cfg)
        self._refresh_recent_menu()

    def _refresh_recent_menu(self):
        """
        Rebuild the 'Open Recent' submenu from settings (`recent_reports`),
        showing '(empty)' when there are no recent items.
        """
        recent_menu = self._menu_recent
        recent_menu.delete(0, "end")

        recent_paths = self.cfg.get("recent_reports", [])
        if not recent_paths:
            recent_menu.add_command(label="(empty)", state="disabled")
            return

        for path in recent_paths:
            recent_menu.add_command(
                label=path, command=lambda p=path: self._load_yaml_path(p)
            )

    # ---------- Columns ----------
    def _rebuild_table_columns(self):
        """
        Recompute and apply the visible Treeview columns based on discovered rules
        and current visibility settings.

        Responsibilities:
          - Determine which categories and individual rules are currently visible.
          - Build the ordered list of dynamic rule columns (category, rule_id).
          - Configure the Treeview's columns: keep base columns wide and
            dynamic rule columns narrow (the readable rule labels are drawn
            separately on the header canvas).
          - Generate and cache rotated header images (via Pillow) for the
            header_canvas so the Treeview native heading text can remain empty.

        Notes:
          - This method updates self._col_pairs which is the canonical ordered
            list of visible (category, rule_id) pairs used elsewhere.
          - Cached rotated header images are stored in self._col_heading_imgs.
        """
        # Base (always-present) columns
        base_columns = ["PIN", "DIR", "TYPE"]

        # Collect dynamic columns (category, rule_id) that should be visible.
        visible_dynamic_columns: list[tuple[str, str]] = []

        for category_name in self._group_order:
            # Respect category-level persistent visibility
            if not self._group_visible.get(category_name, True):
                continue

            # Persistent rule visibility (user settings)
            persistent_map = self._rule_visible_by_cat.get(category_name, {})
            # Temporary overlay visibility (computed per refresh when “Only violations” is ON)
            overlay_map = self._rule_visible_overlay_by_cat.get(category_name, {})

            for rule_identifier in self._rules_by_cat.get(category_name, []):
                persistent_ok = bool(persistent_map.get(rule_identifier, True))
                overlay_ok = bool(
                    overlay_map.get(rule_identifier, True)
                )  # empty overlay -> True
                if persistent_ok and overlay_ok:
                    visible_dynamic_columns.append((category_name, rule_identifier))

        # Store the computed visible dynamic columns for the rest of the UI
        self._col_pairs = visible_dynamic_columns

        # Clear any previously cached heading images — we'll rebuild them for
        # currently visible rule columns below. Keep it as an attribute since
        # header drawing relies on it elsewhere.
        try:
            self._col_heading_imgs = {}
        except Exception:
            # Defensive fallback: ensure attribute exists even on error
            self._col_heading_imgs = {}

        # Small colored icons that appear inside the Treeview native heading
        # (these give the glyph a colored background so it's visible even when
        # the rotated text is hard to read). Keep references in an attribute
        # to prevent garbage collection by Tk.
        # No per-heading glyph icons are created here; we rely on the rotated
        # images drawn on the header canvas or the fallback heading text.

        # Compose final columns list: base columns first, then dynamic rule columns
        all_columns = base_columns + [
            self._col_id_for(cat, rid) for (cat, rid) in visible_dynamic_columns
        ]
        # Apply the new column scheme to the Treeview
        self.tree.configure(columns=all_columns)

        # Configure base columns with readable widths and centered text
        for column_name in base_columns:
            self.tree.heading(column_name, text=column_name)
            self.tree.column(
                column_name,
                width=(200 if column_name == "PIN" else 90),
                anchor="center",
                stretch="no",
            )

        # Configure dynamic rule columns:
        # - keep native Treeview headings empty (we draw rotated labels on the canvas)
        # - set a narrow column width so many rules can fit horizontally
        header_list_ = []
        for category_name, rule_identifier in visible_dynamic_columns:
            short_label = MEMPHYS_RULE_SHORT_MAP.get(rule_identifier, rule_identifier)
            header_list_.append(short_label)
        longest_header = 50 if len(header_list_) == 0 else max(header_list_, key=len)

        for category_name, rule_identifier in visible_dynamic_columns:
            column_id = self._col_id_for(category_name, rule_identifier)

            # Attempt to create a rotated, cached image for the rule label
            # (improves readability when many narrow columns are present).
            # Short label (preferred) and group glyph lookup from scoreboard config.
            short_label = MEMPHYS_RULE_SHORT_MAP.get(rule_identifier, rule_identifier)
            try:
                group_map = PINCHECK_SCOREBOARD_CONFIG.get("rule_groups", {}).get(
                    "check_group_order_map", {}
                )
            except Exception:
                group_map = {}

            # Display only the short label in headings to keep headers compact
            # and avoid visual clutter from glyphs inside rotated text.
            display_label = short_label

            # Create rotated image using the combined display label; the rotated
            # label remains the diagonal readable text. No separate native
            # heading icon is created — we prefer a cleaner look.
            rotated_image = self._make_rotated_header_image(
                display_label,
                angle=60,
                font_size=max(9, self._size_small + 4),
                icon_text=None,
                longest_header=longest_header,
            )

            if rotated_image is not None:
                self._col_heading_imgs[column_id] = rotated_image

            # If we couldn't generate an image, set the native heading text to the combined label
            # so the Treeview still shows a readable label. When image exists, keep native heading empty.

            self.tree.heading(
                column_id, text=(display_label if rotated_image is None else "")
            )

            # Use a narrow width for rule columns; compact mode reduces it further.
            # narrow_width_for_rule_column = 42 if not self._compact else 32
            narrow_width_for_rule_column = 23
            self.tree.column(
                column_id,
                width=narrow_width_for_rule_column,
                minwidth=narrow_width_for_rule_column,
                anchor="center",
                stretch="no",
            )

        # After adjusting columns, redraw the category band + rotated headers.
        # This refresh ensures the header_canvas matches the Treeview layout.
        self._redraw_group_header()

        def check_1():
            bbox_coord = self.header_canvas.bbox("all")
            if bbox_coord is not None:
                self.header_canvas.config(height=bbox_coord[3] - bbox_coord[1])

        self.header_canvas.after(200, check_1)

    def _update_rules_filter_ui(self):
        if not hasattr(self, "inner_frame") or not self.inner_frame:
            return

        for child in self.inner_frame.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass

        use_overlay = self._filter_only_viol.get()
        rules_by_category = self._rules_by_cat or {}
        group_order = self._group_order or sorted(rules_by_category.keys())
        local_category_visible = dict(self._group_visible)
        local_rule_visible_by_category = {
            cat: dict(self._rule_visible_by_cat.get(cat, {})) for cat in rules_by_category
        }

        if use_overlay:
            overlay = self._rule_visible_overlay_by_cat or {}
            for cat in local_category_visible.keys():
                local_category_visible[cat] = any(overlay.get(cat, {}).values())
            for cat, rules in local_rule_visible_by_category.items():
                overlay_rules = overlay.get(cat, {})
                for rule in rules.keys():
                    rules[rule] = overlay_rules.get(rule, False)
            self.only_columes_to_show_by_click_only_violation.update(overlay)

        def _make_category_row(parent, category_name):
            category_frame = ttk.Frame(parent)
            category_frame.pack(fill="x")
            var_category_visible = tk.BooleanVar(
                value=bool(local_category_visible.get(category_name, True))
            )

            def on_category_toggled():
                local_category_visible[category_name] = bool(var_category_visible.get())
                for child in rules_container.winfo_children():
                    if isinstance(child, ttk.Checkbutton):
                        try:
                            child._pc_var.set(var_category_visible.get())
                        except Exception:
                            pass
                on_save_action()

            category_checkbox = ttk.Checkbutton(
                category_frame,
                text=f"{category_name}",
                variable=var_category_visible,
                command=on_category_toggled,
                style="Filter.TCheckbutton",
            )
            category_checkbox.pack(anchor="w")
            category_checkbox._pc_var = var_category_visible

            rules_container = ttk.Frame(category_frame)
            rules_container.pack(fill="x", expand=True, padx=(18, 0))

            for rule_identifier in rules_by_category.get(category_name, []):
                staged_rules_map = local_rule_visible_by_category.setdefault(
                    category_name, {}
                )
                var_rule_visible = tk.BooleanVar(
                    value=bool(staged_rules_map.get(rule_identifier, True))
                )

                def make_rule_callback(rule_local_id, variable):
                    def on_rule_toggled():
                        local_rule_visible_by_category.setdefault(category_name, {})[
                            rule_local_id
                        ] = bool(variable.get())
                        on_save_action()

                    return on_rule_toggled

                rule_checkbox = ttk.Checkbutton(
                    rules_container,
                    text=rule_identifier,
                    variable=var_rule_visible,
                    command=make_rule_callback(rule_identifier, var_rule_visible),
                    style="Filter.TCheckbutton",
                )
                rule_checkbox._pc_var = var_rule_visible
                rule_checkbox.pack(anchor="w")

        def on_save_action():
            self._group_visible.update(local_category_visible)
            for category, staged_map in local_rule_visible_by_category.items():
                self._rule_visible_by_cat.setdefault(category, {}).update(staged_map)
            self.cfg.setdefault("rule_groups", {})
            self.cfg["rule_groups"]["visible"] = dict(self._group_visible)
            self.cfg["rule_groups"]["rules_visible"] = dict(self._rule_visible_by_cat)
            save_settings(self.cfg)
            self._rebuild_table_columns()
            self._refresh_table()
            try:
                self.status.configure(text="Saved column visibility.")
            except Exception:
                pass

        for category in group_order:
            if category not in rules_by_category:
                continue
            _make_category_row(self.inner_frame, category)

    def _make_rotated_header_image(
        self,
        text: str,
        angle: int = 45,
        font_size: int | None = None,
        icon_text: str | None = None,
        longest_header: str = None,
    ):
        """
        Create and return a rotated Tk image for a column header using Pillow.

        Returns:
            `tk.PhotoImage` with the rotated text, or `None` if image creation
            is not possible (Pillow missing or an error occurred).

        Caller must retain the returned image reference to avoid GC.
        """
        # Bail out early if Pillow was not importable at module import time
        if Image is None or ImageDraw is None or ImageFont is None or ImageTk is None:
            return None

        try:
            # Decide effective font size and preferred family
            effective_font_size = (
                font_size if font_size is not None else max(8, self._size_small + 2)
            )
            preferred_font_family = getattr(self, "_font_family", "DejaVu Sans")

            # Try load TrueType font, fall back to DejaVu or PIL default
            try:
                pil_font = ImageFont.truetype(
                    preferred_font_family + ".ttf", effective_font_size
                )
            except Exception:
                try:
                    pil_font = ImageFont.truetype("DejaVuSans.ttf", effective_font_size)
                except Exception:
                    pil_font = ImageFont.load_default()

            # Measure text and prepare RGBA canvas with a small padding
            text_width, text_height = pil_font.getsize(text)
            if longest_header:
                text_width, _ = pil_font.getsize(longest_header)

            padding_pixels = 6
            # We no longer render a separate circular icon; the caller provides
            # a combined `text` which already contains the glyph + separator + short_name.
            icon_space = 0
            canvas_w = text_width + padding_pixels * 2 + 20
            canvas_h = text_height + padding_pixels * 2 + icon_space
            canvas_h = 21
            rgba_canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 0))
            drawer = ImageDraw.Draw(rgba_canvas)

            # Determine text fill color from theme (hex or rgb tuple supported)
            try:
                theme_text_color = self.colors.get("text", "#000000")
                if isinstance(theme_text_color, tuple):
                    fill_rgba = tuple(int(x) for x in theme_text_color[:3]) + (255,)
                else:
                    hexstr = str(theme_text_color).lstrip("#")
                    fill_rgba = (
                        int(hexstr[0:2], 16),
                        int(hexstr[2:4], 16),
                        int(hexstr[4:6], 16),
                        255,
                    )
            except Exception:
                fill_rgba = (0, 0, 0, 255)

            # We intentionally do not draw a separate icon; `text` should already
            # contain the glyph and short_name (for example: "⚡| SHORT"). Keeping
            # rendering simple avoids overlapping visuals and font/emoji sizing
            # issues across platforms.

            # Draw main label shifted down by icon_space
            drawer.text(
                (padding_pixels + 10, padding_pixels + icon_space - 3),
                text,
                font=pil_font,
                fill=fill_rgba,
            )

            drawer.polygon(
                self.draw_rhomboid(0, 0, canvas_w - 10 - 1, canvas_h - 1, angle_deg=30)[
                    0
                ],
                outline="#b0aeaa",
                width=1,
            )
            rotated = rgba_canvas.rotate(angle, expand=1, resample=Image.BICUBIC)
            tk_img = ImageTk.PhotoImage(rotated)
            return tk_img
        except Exception:
            return None

    def draw_rhomboid(self, x1, y1, x2, y2, angle_deg=60, **kwargs):
        """
        Draws a parallelogram by transforming the rectangle defined by
        its Top-Left (x1, y1) and Bottom-Right (x2, y2) corners.
        The vertical sides are sheared by the specified angle (theta).

        :param canvas: The Tkinter Canvas widget.
        :param x1: The x-coordinate of the Top-Left corner (P1).
        :param y1: The y-coordinate of the Top-Left corner (P1).
        :param x2: The x-coordinate of the Bottom-Right corner (P4 in original bounding box).
        :param y2: The y-coordinate of the Bottom-Right corner (P4 in original bounding box).
        :param angle_deg: The shear angle (theta) in degrees (relative to vertical).
        :param kwargs: Optional drawing options (fill, outline, width, etc.)
        :return: A tuple (polygon_coords, width, height, extended_width, canvas_item_id)
        """

        # --- 1. Calculate Width (W) and Height (H) ---
        width = x2 - x1
        height = y2 - y1

        if width <= 0 or height <= 0:
            raise ValueError(
                "Invalid bounding box. Width and Height must be positive (x2 > x1 and y2 > y1)."
            )

        # --- 2. Shear Calculation ---
        angle_rad = math.radians(angle_deg)

        # Delta X: The horizontal shift applied to the bottom line (H * tan(theta))
        delta_x = height * math.tan(angle_rad)

        # --- 3. Calculate the four new vertices (P1, P3, P4_new, P2) ---

        # P1 (Top-Left Anchor): (x1, y1)
        P1_x, P1_y = x1, y1

        # P3 (Top-Right): P1 shifted right by W (no shear at the top)
        P3_x, P3_y = x1 + width, y1

        # P4_new (Bottom-Right): P3 shifted down by H and horizontally by delta_x
        P4_x_new, P4_y_new = P3_x + delta_x, P3_y + height

        # P2 (Bottom-Left): P1 shifted down by H and horizontally by delta_x
        P2_x, P2_y = P1_x + delta_x, P1_y + height

        # 4. Create the coordinate sequence (P1, P3, P4_new, P2)
        polygon_coords = (P1_x, P1_y, P3_x, P3_y, P4_x_new, P4_y_new, P2_x, P2_y)

        # 5. Calculate the extended width (bounding box width)
        # Extends from min(P1_x, P2_x) to max(P3_x, P4_x_new)
        min_x = min(P1_x, P2_x)
        max_x = max(P3_x, P4_x_new)
        extended_width = max_x - min_x

        # 6. Draw the shape on the canvas
        # item_id = canvas.create_polygon(polygon_coords, **kwargs)

        return [polygon_coords, extended_width]
        # return polygon_coords, width, height, extended_width, item_id

    def _col_id_for(self, cat: str, rid: str) -> str:
        """
        Build a stable internal column identifier for a rule column.

        Parameters:
            - cat: The rule category (group) name.
            - rid: The rule identifier within the category.

        Returns:
            A string used as the Treeview column id in the format "<category>__<rule_id>".
        """
        # Constant separator used to join category and rule id in column identifiers
        # Keeping it here keeps the format obvious when reading the function.
        SEPARATOR = "__"
        return f"{cat}{SEPARATOR}{rid}"

    # ---------- Render table ----------

    def _refresh_table(self):
        """
        Rebuild the table rows (in-memory) and insert into the Treeview.
        Steps performed:
        - Clear any cached overlay badges and the internal cell cache.
        - Compute a list of rows for inventory pins and non-inventory entities.
        - Create a compact representation for each cell (level + violations)
        stored in `self._cell_cache` for overlay rendering.
        - Insert rows in chunks to avoid UI freezes.
        """

        INSERT_CHUNK_SIZE = 500
        self._destroy_cell_badges_safe()
        self._cell_cache.clear()
        self.tree.delete(*self.tree.get_children(""))

        if not self._rundata:
            self._redraw_group_header()
            return

        # --- Read current filter values ---
        search_text = self._get_search_query()
        comparison_target = (
            search_text if self._filter_case.get() else search_text.lower()
        )
        severity_filter = self._filter_sev.get()
        pin_type_filter = self._filter_type.get()
        only_show_violated = self._filter_only_viol.get()
        options_only_failures = bool(self._rundata.options.get("only_failures", False))

        # --- Define build_cells() BEFORE using it ---
        def build_cells(record_name: str) -> tuple[dict[str, dict], str]:
            per_cell_map: dict[str, dict] = {}
            worst_severity_tag = "PASS"
            for category_name, rule_identifier in getattr(self, "_col_pairs", []):
                column_id = self._col_id_for(category_name, rule_identifier)
                violations = list(
                    self._viol_by_pin_by_rule.get(record_name, {}).get(
                        rule_identifier, []
                    )
                )
                if not violations:
                    cell_level = (
                        CellLevel.PASS_ if options_only_failures else CellLevel.NA
                    )
                else:
                    cell_level = choose_level(
                        [violation.severity for violation in violations]
                    )
                    if cell_level == CellLevel.FAIL:
                        worst_severity_tag = "FAIL"
                    elif cell_level == CellLevel.WARN and worst_severity_tag != "FAIL":
                        worst_severity_tag = "WARN"
                per_cell_map[column_id] = {
                    "level": cell_level,
                    "violations": violations,
                    "cat": category_name,
                    "rule": rule_identifier,
                }
            return per_cell_map, worst_severity_tag

        # --- Row visibility helper ---
        def row_visible(
            display_name: str, pin_type: str | None, cells: dict[str, dict]
        ) -> bool:
            if search_text:
                target_value = (
                    display_name if self._filter_case.get() else display_name.lower()
                )
                if comparison_target not in target_value:
                    return False
            if (
                pin_type is not None
                and pin_type_filter != "ALL"
                and pin_type != pin_type_filter
            ):
                return False
            if severity_filter == "ALL" and not only_show_violated:
                return True

            def has_violations(match_severity=None):
                for cell in cells.values():
                    for v in cell.get("violations", []):
                        if match_severity is None or v.severity == match_severity:
                            return True
                return False

            if only_show_violated and not has_violations():
                return False
            if severity_filter != "ALL":
                return has_violations(severity_filter)
            return True

        # --- NEW: Compute overlay visibility for columns ---
        def _violations_match_severity(violations: list[Violation]) -> bool:
            if not violations:
                return False
            if severity_filter == "ALL":
                return True
            return any(v.severity == severity_filter for v in violations)

        visible_row_names: list[str] = []
        active_rules: set[tuple[str, str]] = set()

        def _category_for_rule(rule_id: str, viols: list[Violation]) -> str:
            rd = self._rundata.rule_catalog.get(rule_id)
            if rd and rd.category:
                return rd.category
            if viols:
                return viols[0].category or "META"
            return "META"

        # --- NEW: Compute overlay columns from base dataset (ignores search) ---
        active_rules_base: set[tuple[str, str]] = set()

        if only_show_violated:
            def _pin_type_ok(pt: Optional[str]) -> bool:
                return (pin_type_filter == "ALL") or ((pt or "") == pin_type_filter)

            # Pass A: pins (ignore search; respect pin-type and severity)
            for pin_rec in self._rundata.pins:
                if not _pin_type_ok(pin_rec.pin_type):
                    continue
                per_rule_map = self._viol_by_pin_by_rule.get(pin_rec.pin_name, {})
                for rule_id, viols in per_rule_map.items():
                    if _violations_match_severity(viols):
                        cat = _category_for_rule(rule_id, viols)
                        active_rules_base.add((cat, rule_id))

            # Pass B: other entities (ignore search; respect severity)
            for entity_name, per_rule_map in self._viol_by_pin_by_rule.items():
                if entity_name in self._known_pins:
                    continue
                for rule_id, viols in per_rule_map.items():
                    if _violations_match_severity(viols):
                        cat = _category_for_rule(rule_id, viols)
                        active_rules_base.add((cat, rule_id))

            # Build overlay map using base active rules
            overlay: dict[str, dict[str, bool]] = {}
            for category_name in self._group_order:
                if not self._group_visible.get(category_name, True):
                    continue
                overlay_cat: dict[str, bool] = {}
                for rule_id in self._rules_by_cat.get(category_name, []):
                    overlay_cat[rule_id] = ((category_name, rule_id) in active_rules_base)
                overlay[category_name] = overlay_cat
            self._rule_visible_overlay_by_cat = overlay
        else:
            # No overlay when 'only violations' is OFF
            self._rule_visible_overlay_by_cat = {}

        # IMPORTANT: Rebuild columns using the overlay BEFORE inserting rows
        self._rebuild_table_columns()

        

        # Pass 1: pins
        for pin_record in self._rundata.pins:
            cells_map, _worst = build_cells(pin_record.pin_name)
            if row_visible(pin_record.pin_name, pin_record.pin_type or "", cells_map):
                visible_row_names.append(pin_record.pin_name)
                per_rule_map = self._viol_by_pin_by_rule.get(pin_record.pin_name, {})
                for rule_id, viols in per_rule_map.items():
                    if _violations_match_severity(viols):
                        cat = _category_for_rule(rule_id, viols)
                        active_rules.add((cat, rule_id))

        # Pass 1: other entities
        other_entities = [
            name
            for name in self._viol_by_pin_by_rule.keys()
            if name not in self._known_pins
        ]
        others_sorted = sorted([n for n in other_entities if n != "<GLOBAL>"]) + (
            ["<GLOBAL>"] if "<GLOBAL>" in other_entities else []
        )
        for entity_name in others_sorted:
            cells_map, _worst = build_cells(entity_name)
            display_name = (
                "[OTHER] GLOBAL"
                if entity_name == "<GLOBAL>"
                else f"[OTHER] {entity_name}"
            )
            if row_visible(display_name, None, cells_map):
                visible_row_names.append(entity_name)
                per_rule_map = self._viol_by_pin_by_rule.get(entity_name, {})
                for rule_id, viols in per_rule_map.items():
                    if _violations_match_severity(viols):
                        cat = _category_for_rule(rule_id, viols)
                        active_rules.add((cat, rule_id))

        # --- Build rows as before ---
        rows = []
        for pin_record in self._rundata.pins:
            cells_map, worst_severity = build_cells(pin_record.pin_name)
            if not row_visible(pin_record.pin_name, pin_record.pin_type or "", cells_map):
                continue
            self._cell_cache[pin_record.pin_name] = cells_map
            row_values = [pin_record.pin_name, pin_record.direction, pin_record.pin_type]
            for category_name, rule_identifier in getattr(self, "_col_pairs", []):
                column_id = self._col_id_for(category_name, rule_identifier)
                cell = cells_map.get(column_id)
                glyph = STATUS_GLYPH.get(cell["level"], " ") if cell else ""
                row_values.append(glyph)
            row_tags = ["row_even" if (len(rows) % 2 == 0) else "row_odd", worst_severity]
            rows.append((pin_record.pin_name, row_values, row_tags))

        if others_sorted:
            header_vals = ["Other Violations (Not In Pin Inventory)", "", ""] + [
                ""
            ] * len(self._col_pairs)
            rows.append(("__OTHER_HEADER__", header_vals, ["group_header"]))
        for entity_name in others_sorted:
            display_name = (
                "[OTHER] GLOBAL"
                if entity_name == "<GLOBAL>"
                else f"[OTHER] {entity_name}"
            )
            cells_map, worst_severity = build_cells(entity_name)
            if not row_visible(display_name, None, cells_map):
                continue
            self._cell_cache[entity_name] = cells_map
            row_values = [display_name, "", ""]
            for category_name, rule_identifier in getattr(self, "_col_pairs", []):
                column_id = self._col_id_for(category_name, rule_identifier)
                cell = cells_map.get(column_id)
                glyph = STATUS_GLYPH.get(cell["level"]) if cell else ""
                row_values.append(glyph)
            row_tags = ["row_even" if (len(rows) % 2 == 0) else "row_odd", worst_severity]
            rows.append((entity_name, row_values, row_tags))

        for start_index in range(0, len(rows), INSERT_CHUNK_SIZE):
            for iid, values, tags in rows[start_index : start_index + INSERT_CHUNK_SIZE]:
                self.tree.insert("", "end", iid=iid, values=values, tags=tags)

        self._redraw_group_header()
        if self._cell_color_overlays.get():
            self.after(120, self._refresh_cell_badges)
        else:
            self._destroy_cell_badges_safe()
        # self.table_card.content.config(bg="white", bd=0)

    # ---------- Interaction / Context ----------
    def _on_cell_click(self, event):
        """
        Handle left-click on a Treeview cell.

        Behavior:
          - If the click is not inside a data cell, refresh header asynchronously.
          - Identify the clicked row and column, normalize them, and show details
            for the clicked pin/entity.
        """
        # Identify which region was clicked (cell, heading, etc.)
        click_region = self.tree.identify("region", event.x, event.y)
        if click_region != "cell":
            # Not a data cell: schedule a header redraw and return early.
            self.after_idle(self._redraw_group_header)
            return

        # Row item id under cursor and the Treeview column id (like '#3')
        clicked_item = self.tree.identify_row(event.y)
        clicked_colid = self.tree.identify_column(event.x)
        if not clicked_item or not clicked_colid or clicked_item == "__OTHER_HEADER__":
            return

        # Convert '#N' column id to zero-based index and get the logical column name
        column_index = int(clicked_colid[1:]) - 1
        columns_list = list(self.tree["columns"])
        if column_index < 0 or column_index >= len(columns_list):
            return

        # For other clicks we show the details panel for the selected row.
        self._show_details_for_pin(clicked_item)
        
        try:
            if hasattr(self, "analysis_tab") and self.analysis_tab:
                self.analysis_tab.show_details_toggle()
        except Exception:
            pass


    def _show_context_menu(self, event):
        """Show a context menu at the clicked Treeview location."""
        self._ctx_item = self.tree.identify_row(event.y)
        if not self._ctx_item or self._ctx_item == "__OTHER_HEADER__":
            return
        clicked_colid = self.tree.identify_column(event.x)
        column_index = int(clicked_colid[1:]) - 1 if clicked_colid else 0
        columns_list = list(self.tree["columns"])
        self._ctx_col_name = (
            columns_list[column_index] if 0 <= column_index < len(columns_list) else "PIN"
        )

    def _popup_menu(self, menu: tk.Menu, x: int, y: int) -> None:
        """
        Show a context (popup) menu and make it disappear when clicking anywhere
        in the app or pressing Escape. Ensures grab is released and temporary
        bindings are cleaned up.
        """
        # Track whether we posted a menu; used by global handlers
        self._ctx_menu_active = True

        # Define cleanup once the menu is dismissed
        def _cleanup():
            # Unbind global handlers
            try:
                self.unbind_all("<Button-1>")
            except Exception:
                pass
            try:
                self.unbind_all("<Escape>")
            except Exception:
                pass
            # Mark inactive
            self._ctx_menu_active = False

        # Global click should unpost menu (click anywhere dismisses)
        def _global_click_dismiss(_evt=None):
            try:
                if hasattr(menu, "unpost"):
                    menu.unpost()
            except Exception:
                pass
            finally:
                _cleanup()

        # Global Escape should unpost menu
        def _global_escape_dismiss(_evt=None):
            try:
                if hasattr(menu, "unpost"):
                    menu.unpost()
            except Exception:
                pass
            finally:
                _cleanup()

        # Install temporary global bindings
        self.bind_all("<Button-1>", _global_click_dismiss, add="+")
        self.bind_all("<Escape>", _global_escape_dismiss, add="+")

        # Show the popup and ALWAYS release grab
        try:
            menu.tk_popup(x, y)
        finally:
            try:
                menu.grab_release()
            except Exception:
                pass

    def _ctx_copy(self, what: str):
        """
        Copy either the pin/entity name or consolidated cell messages to clipboard.

        Args:
          - what: either 'pin' to copy the selected row id, or 'messages' to
            copy aggregated violation messages for the selected cell.
        """
        if not getattr(self, "_ctx_item", None) or self._ctx_item == "__OTHER_HEADER__":
            return

        if what == "pin":
            self.clipboard_clear()
            self.clipboard_append(self._ctx_item)
            return

        # Aggregate messages for the selected rule column
        selected_col = getattr(self, "_ctx_col_name", "PIN")
        aggregated_text = ""
        if selected_col not in ("PIN", "DIR", "TYPE"):
            rule_identifier = (
                selected_col.split("__", 1)[1] if "__" in selected_col else selected_col
            )
            violations = self._viol_by_pin_by_rule.get(self._ctx_item, {}).get(
                rule_identifier, []
            )
            aggregated_text = (
                "\n".join(
                    f"{v.rule_id}: {v.severity} — {v.message or ''}" for v in violations
                )
                or ""
            )

        self.clipboard_clear()
        self.clipboard_append(aggregated_text)

    def _ctx_open_evidence(self):
        """
        Open the first filesystem evidence path for the selected cell, if any.

        The method inspects the violation.evidence field which can be a string,
        a list of paths, or nested dict/list structures. It collects the first
        readable filesystem path and launches the platform default opener.
        """
        if not getattr(self, "_ctx_item", None) or self._ctx_item == "__OTHER_HEADER__":
            return

        selected_col = getattr(self, "_ctx_col_name", "PIN")
        if selected_col in ("PIN", "DIR", "TYPE"):
            messagebox.showinfo("Evidence", "Right-click a rule cell to open evidence.")
            return

        rule_identifier = (
            selected_col.split("__", 1)[1] if "__" in selected_col else selected_col
        )
        violations = self._viol_by_pin_by_rule.get(self._ctx_item, {}).get(
            rule_identifier, []
        )

        found_paths: list[str] = []
        # Inspect each violation's evidence field and collect readable paths
        for violation in violations:
            evidence_obj = violation.evidence
            if isinstance(evidence_obj, dict):
                for _, nested in evidence_obj.items():
                    if isinstance(nested, dict):
                        for p, _ in nested.items():
                            if isinstance(p, str) and FileIO.is_file_readable(p, silent=True):  # type: ignore[attr-defined]
                                found_paths.append(p)
                    elif isinstance(nested, list):
                        for p in nested:
                            if isinstance(p, str) and FileIO.is_file_readable(p, silent=True):  # type: ignore[attr-defined]
                                found_paths.append(p)
            elif isinstance(evidence_obj, list):
                for p in evidence_obj:
                    if isinstance(p, str) and FileIO.is_file_readable(p, silent=True):  # type: ignore[attr-defined]
                        found_paths.append(p)
            elif isinstance(evidence_obj, str) and FileIO.is_file_readable(evidence_obj, silent=True):  # type: ignore[attr-defined]
                found_paths.append(evidence_obj)

        if not found_paths:
            messagebox.showinfo(
                "Evidence", "No existing filesystem path found in evidence."
            )
            return

        first_path = found_paths[0]
        try:
            # _open_path_async(first_path)
            self._open_with_preferred_viewer(first_path)
        except Exception as exc:
            messagebox.showerror("Open Evidence", f"Failed to open:\n{exc}")

    def _ctx_export_row(self):
        """
        Export the selected row to CSV. Prompt the user for a destination file
        and write the current row's visible values (including per-rule labels).
        """
        if (
            not self._rundata
            or not getattr(self, "_ctx_item", None)
            or self._ctx_item == "__OTHER_HEADER__"
        ):
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")]
        )
        if not save_path:
            return

        try:
            # Build CSV in-memory then write via FileIO to respect project I/O patterns
            buf = io.StringIO()
            writer = csv.writer(buf)

            # Header: name, direction, type, then each visible rule as category/rule
            header = ["name", "direction", "type"] + [
                f"{category}/{rule_id}"
                for (category, rule_id) in getattr(self, "_col_pairs", [])
            ]
            writer.writerow(header)

            row_name = self._ctx_item
            pin_obj = self._pin_record_by_name(row_name)
            direction = pin_obj.direction if pin_obj else ""
            pin_type = pin_obj.pin_type if pin_obj else ""
            row = [row_name, direction, pin_type]

            # Append per-rule summary labels for the row
            for category, rule_id in getattr(self, "_col_pairs", []):
                violations = self._viol_by_pin_by_rule.get(row_name, {}).get(rule_id, [])
                if not violations:
                    label = (
                        "PASS"
                        if self._rundata.options.get("only_failures", False)
                        else "N/A"
                    )
                else:
                    lvl = choose_level([v.severity for v in violations])
                    count = len(violations)
                    label = (
                        "FAIL"
                        if lvl == CellLevel.FAIL
                        else ("WARN" if lvl == CellLevel.WARN else "PASS")
                    )
                    if count > 1 and label in ("FAIL", "WARN"):
                        label = f"{label} ({count})"
                row.append(label)

            writer.writerow(row)
            content = buf.getvalue()
            FileIO.write_file(save_path, content.splitlines(True), mkdir=True)  # type: ignore[attr-defined]
            messagebox.showinfo("Export Row", f"Exported to {save_path}")
        except Exception as exc:
            messagebox.showerror("Export Row", str(exc))

    # ---------- Details (bottom) ----------
    def _pin_record_by_name(self, pin_name: str) -> "PinRecord | None":
        """
        Return the PinRecord object matching `pin_name` from the currently
        loaded run data.

        Steps:
          1. Guard: return None when no run data is loaded.
          2. Iterate the loaded PinRecord list and return the first match.
          3. Return None when no matching pin is found.
        """
        # Fast-exit if no run data available
        if not self._rundata:
            return None

        # Search for the PinRecord by its pin_name field
        for pin_record in self._rundata.pins:
            if pin_record.pin_name == pin_name:
                return pin_record

        # No match found
        return None

    def _show_details_for_pin(self, name: str):
        """
        Populate the details panel for a given row name (pin or entity).

        Behavior:
          - If a PinRecord exists for `name`, show all violations for that pin.
          - Otherwise create a minimal dummy PinRecord and show violations as an
            "other entity" so the details view remains consistent.

        Steps:
          1. Lookup PinRecord via _pin_record_by_name.
          2. Lookup violations map for the row name.
          3. Call DetailsBottom.show_pin_all with appropriate parameters.
        """
        # Find the PinRecord (may be None for non-inventory entities)
        pin_record = self._pin_record_by_name(name)
        violations_map_for_row = self._viol_by_pin_by_rule.get(name, {})

        if pin_record:
            # Show all violations for an inventory pin
            self.detail.show_pin_all(
                name, pin_record, self._rundata, violations_map_for_row
            )
        else:
            # Build a minimal dummy PinRecord for non-inventory entities so the UI shows consistent info
            dummy_pin = PinRecord(
                pin_name=name, direction="", pin_type="", extras={"raw": {}}
            )
            self.detail.show_pin_all(
                name, dummy_pin, self._rundata, violations_map_for_row
            )

    # ---------- Groups ----------
    def _open_group_manager(self, master):
        """
        Open a modal window that lets the user toggle visibility of entire
        categories and individual rules.

        Responsibilities:
          - Present a scrollable checklist of categories and their rules.
          - Work on a local copy of visibility state until the user clicks Save.
          - Persist chosen visibility settings on Save and rebuild the table.

        Implementation notes:
          - Uses a canvas + inner frame combination to provide a scrollable body.
          - Category checkboxes toggle all rule checkboxes underneath them.
        """

        self.rule_groups_selection_info_BoolVar = {}

        # --- scrollable area for category + rule checkboxes ---
        body_frame = ttk.Frame(
            master,
        )
        body_frame.pack(fill="both", expand=True)

        self.rule_manager_canvas = tk.Canvas(
            body_frame, highlightthickness=0, bd=0, background="#e0deda"
        )
        rule_manager_canvas_SB = ttk.Scrollbar(
            body_frame, orient="vertical", command=self.rule_manager_canvas.yview
        )
        self.rule_manager_canvas.configure(yscrollcommand=rule_manager_canvas_SB.set)

        # Inner frame placed inside the rule_manager_canvas: where checkboxes will live
        self.inner_frame = tk.Frame(
            self.rule_manager_canvas,
        )
        inner_window_id = self.rule_manager_canvas.create_window(
            (0, 0), window=self.inner_frame, anchor="nw"
        )

        # Bind mouse wheel events only to the Rules filter canvas and inner frame
        self._on_mousewheel_rule_manager_canvas_bind(self.rule_manager_canvas)
        self._on_mousewheel_rule_manager_canvas_bind(rule_manager_canvas_SB)
        self.inner_frame.bind("<MouseWheel>", self._on_mousewheel_rule_manager_canvas)
        self.inner_frame.bind("<Button-4>", self._on_mousewheel_rule_manager_canvas)
        self.inner_frame.bind("<Button-5>", self._on_mousewheel_rule_manager_canvas)

        def on_canvas_configure(_event=None):
            """
            Recompute scrollregion and ensure inner frame width tracks canvas width.
            """
            self.inner_frame.update_idletasks()
            self.rule_manager_canvas.config(
                scrollregion=(
                    0,
                    0,
                    self.inner_frame.winfo_width(),
                    self.inner_frame.winfo_height(),
                )
            )
            # Stretch inner_frame to match canvas width so checkbuttons wrap correctly
            self.rule_manager_canvas.itemconfigure(
                inner_window_id, width=self.rule_manager_canvas.winfo_width()
            )

        self.inner_frame.bind("<Configure>", on_canvas_configure)
        self.rule_manager_canvas.bind("<Configure>", on_canvas_configure)

        self._update_rules_filter_ui()

    def _on_mousewheel_rule_manager_canvas_bind(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel_rule_manager_canvas)
        widget.bind("<Button-4>", self._on_mousewheel_rule_manager_canvas)
        widget.bind("<Button-5>", self._on_mousewheel_rule_manager_canvas)

    # Bind mouse wheel events to scroll the canvas
    def _on_mousewheel_rule_manager_canvas(self, event):
        if event.delta:  # Windows/macOS
            direction = -1 if event.delta > 0 else 1
            self.rule_manager_canvas.yview_scroll(direction, "units")
        elif event.num == 4:  # Linux scroll up
            self.rule_manager_canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Linux scroll down
            self.rule_manager_canvas.yview_scroll(1, "units")
        return "break"  # Stop event propagation

    def load_rules_viewer(
        self,
    ):
        for child in self.inner_frame.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass

        def _make_category_row(parent: ttk.Frame, category_name: str):
            """
            Compose a UI row for a single category and its rule checkboxes.

            Structure:
              - Category checkbox (toggles all rules in this category)
              - Horizontal list of rule checkboxes underneath
            """

            # Container for the category group
            category_frame = ttk.Frame(
                parent,
            )
            # category_frame.pack(fill="x", pady=(6, 4))
            category_frame.pack(
                fill="x",
            )
            self._on_mousewheel_rule_manager_canvas_bind(category_frame)

            # BooleanVar that represents the category-level visibility
            var_category_visible = tk.BooleanVar(
                value=bool(local_category_visible.get(category_name, True))
            )

            if category_name not in self.rule_groups_selection_info_BoolVar:
                self.rule_groups_selection_info_BoolVar[category_name] = {"rules": {}}
            self.rule_groups_selection_info_BoolVar[category_name][
                "BooleanVar"
            ] = var_category_visible

            def on_category_toggled():
                """
                Callback when the category checkbox is toggled: update local state
                and set all child rule checkbox vars accordingly.
                """
                local_category_visible[category_name] = bool(var_category_visible.get())
                # Toggle all rule checkbuttons inside this category frame
                for child in rules_container.winfo_children():
                    if isinstance(child, ttk.Checkbutton):
                        try:
                            child_var = child._pc_var
                            child_var.set(var_category_visible.get())
                            on_save_action()
                        except Exception:
                            # Ignore if the child doesn't expose the expected attribute
                            pass

            category_checkbox = ttk.Checkbutton(
                category_frame,
                text=f"{category_name}",
                variable=self.rule_groups_selection_info_BoolVar[category_name][
                    "BooleanVar"
                ],
                command=on_category_toggled,
                style="Filter.TCheckbutton",
            )
            category_checkbox.pack(anchor="w")
            category_checkbox._pc_var = var_category_visible
            self._on_mousewheel_rule_manager_canvas_bind(category_checkbox)

            # Container for rule checkboxes
            rules_container = ttk.Frame(
                category_frame,
            )
            # rules_container.pack(fill="x", padx=(18, 0), pady=(4, 0))
            rules_container.pack(fill="x", expand=True, padx=(18, 0))
            self._on_mousewheel_rule_manager_canvas_bind(rules_container)

            # Create checkboxes for each rule in this category
            for rule_identifier in rules_by_category.get(category_name, []):
                # Ensure a mapping exists in the local staged visibility map
                staged_rules_map = local_rule_visible_by_category.setdefault(
                    category_name, {}
                )
                var_rule_visible = tk.BooleanVar(
                    value=bool(staged_rules_map.get(rule_identifier, True))
                )

                self.rule_groups_selection_info_BoolVar[category_name]["rules"][
                    rule_identifier
                ] = var_rule_visible

                def make_rule_callback(rule_local_id: str, variable: tk.BooleanVar):
                    """
                    Return a callback that updates the staged visibility for a single rule.
                    """

                    def on_rule_toggled():
                        local_rule_visible_by_category.setdefault(category_name, {})[
                            rule_local_id
                        ] = bool(variable.get())
                        on_save_action()

                    return on_rule_toggled

                rule_checkbox = ttk.Checkbutton(
                    rules_container,
                    text=rule_identifier,
                    # variable=var_rule_visible,
                    variable=self.rule_groups_selection_info_BoolVar[category_name][
                        "rules"
                    ][rule_identifier],
                    command=make_rule_callback(rule_identifier, var_rule_visible),
                    style="Filter.TCheckbutton",
                )
                # Stash the associated variable on the widget so category toggles can access it
                rule_checkbox._pc_var = var_rule_visible
                rule_checkbox.pack(anchor=tk.W)
                self._on_mousewheel_rule_manager_canvas_bind(rule_checkbox)

        # --- Build the working copies of visibility state ---
        rules_by_category = getattr(self, "_rules_by_cat", {}) or {}
        # Preserve order; fall back to sorted keys when needed
        group_order = list(getattr(self, "_group_order", [])) or sorted(
            rules_by_category.keys()
        )
        # Local copies: changes here are staged until Save
        local_category_visible: dict[str, bool] = dict(self._group_visible)
        local_rule_visible_by_category: dict[str, dict[str, bool]] = {
            category: dict(self._rule_visible_by_cat.get(category, {}))
            for category in rules_by_category
        }
        # Populate the inner_frame with categories and their rules
        for category in group_order:
            if category not in rules_by_category:
                continue
            _make_category_row(self.inner_frame, category)

        def on_save_action():
            """
            Persist the staged visibility settings to the application state,
            rebuild the table columns and refresh the table contents.
            """
            # Update the main in-memory visibility maps with staged values
            self._group_visible.update(local_category_visible)
            for category, staged_map in local_rule_visible_by_category.items():
                self._rule_visible_by_cat.setdefault(category, {})
                self._rule_visible_by_cat[category].update(staged_map)

            # Persist to user settings and rebuild UI
            self.cfg.setdefault("rule_groups", {})
            self.cfg["rule_groups"]["visible"] = dict(self._group_visible)
            self.cfg["rule_groups"]["rules_visible"] = dict(self._rule_visible_by_cat)
            save_settings(self.cfg)

            # Refresh visible columns and table rows
            self._rebuild_table_columns()
            self._refresh_table()
            try:
                self.status.configure(text="Saved column visibility.")
            except Exception:
                pass

        

        #

    # ---------- Export / Misc ----------
    def _export_csv(self):
        """
        Export the current visible table to a CSV file.

        Steps:
          1. Ensure a run is loaded.
          2. Ask the user for a destination filename.
          3. Iterate every visible row and compose a CSV row using current
             visible columns and per-rule aggregated labels.
          4. Write the CSV using FileIO.write_file to respect project I/O behavior.
        """
        # Guard: need run data to export meaningful content
        if not self._rundata:
            messagebox.showinfo("Export", "Load a YAML first.")
            return

        # Ask user for destination
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")]
        )
        if not file_path:
            return

        try:
            # Build CSV in-memory
            buffer = io.StringIO()
            csv_writer = csv.writer(buffer)

            # Header row: name/direction/type + visible category/rule pairs
            header_row = ["name", "direction", "type"] + [
                f"{category}/{rule_id}"
                for (category, rule_id) in getattr(self, "_col_pairs", [])
            ]
            csv_writer.writerow(header_row)

            # Iterate through tree rows
            for item_id in self.tree.get_children(""):
                if item_id == "__OTHER_HEADER__":
                    # Skip the synthetic group header row
                    continue
                row_name = item_id
                pin_record = self._pin_record_by_name(row_name)
                direction_value = pin_record.direction if pin_record else ""
                type_value = pin_record.pin_type if pin_record else ""

                csv_row = [row_name, direction_value, type_value]

                # Build per-rule summary labels for each visible column
                for category, rule_id in getattr(self, "_col_pairs", []):
                    violations_for_cell = self._viol_by_pin_by_rule.get(row_name, {}).get(
                        rule_id, []
                    )
                    if not violations_for_cell:
                        label = (
                            "PASS"
                            if self._rundata.options.get("only_failures", False)
                            else "N/A"
                        )
                    else:
                        level_for_cell = choose_level(
                            [violation.severity for violation in violations_for_cell]
                        )
                        count_occurrences = len(violations_for_cell)
                        if level_for_cell == CellLevel.FAIL:
                            base_label = "FAIL"
                        elif level_for_cell == CellLevel.WARN:
                            base_label = "WARN"
                        else:
                            base_label = "PASS"
                        # Append occurrence count when multiple and severity is non-PASS
                        if count_occurrences > 1 and base_label in ("FAIL", "WARN"):
                            label = f"{base_label} ({count_occurrences})"
                        else:
                            label = base_label
                    csv_row.append(label)

                csv_writer.writerow(csv_row)

            # Write to disk using project FileIO helper
            content = buffer.getvalue()
            FileIO.write_file(file_path, content.splitlines(True), mkdir=True)  # type: ignore[attr-defined]
            messagebox.showinfo("Export", f"Exported to {file_path}")
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    def _open_run_editor(self):
        """
        Launch the RunEditor to allow re-running pincheck using the recorded command.
        Preconditions:
          - A run must be loaded to reconstruct the recorded command.
        """
        if not self._rundata:
            messagebox.showinfo("Run Editor", "Load a YAML to reconstruct the command.")
            return

        metadata = self._rundata.metadata
        # RunEditor(
        #     self,
        #     metadata.command or "",
        #     getattr(metadata, "arguments", {}) or {},  # old editor compatibility
        #     self.colors,
        #     cwd=os.path.dirname(self._last_yaml_path) if self._last_yaml_path else None,
        #     yaml_path=self._last_yaml_path,
        #     _load_yaml_path=self._load_yaml_path,
        # )

    def _open_containing_folder(self):
        """
        Open the filesystem folder that contains the currently loaded YAML file.
        Uses _open_path_async to open the folder with the platform default.
        """
        if not self._last_yaml_path:
            messagebox.showinfo("Open Folder", "No YAML loaded.")
            return

        folder_path = os.path.dirname(self._last_yaml_path) or "."
        try:
            _open_path_async(folder_path)
        except Exception as exc:
            messagebox.showerror("Open Folder", f"Failed to open folder:\n{exc}")

    def _show_legend(self):
        """
        Show a small informational dialog explaining cell markers and tips.
        """
        messagebox.showinfo(
            "Legend",
            "Cell markers (row color indicates severity):\n"
            " P — PASS\n"
            " W — WARN (has at least one WARNING)\n"
            " F — FAIL (has at least one ERROR)\n"
            " - — N/A (no data when passes are not emitted)\n\n"
            "Tips:\n"
            " • Right-click a cell for actions (copy, open evidence, export row)\n"
            " • Ctrl+F focuses search, F5 reloads the last YAML\n"
            " • Use ‘Columns…’ to toggle entire categories",
        )

    def _hide_category(self, category: str):
        """
        Hide an entire category and all rules under it, persist the change and
        rebuild the table columns.

        Steps:
          1. Cancel any pending badge refresh to avoid races during rebuild.
          2. Update in-memory visibility maps and persist to settings.
          3. Rebuild table columns and refresh table rows.
        """
        # Cancel pending badge refresh if present
        if self._badge_refresh_after:
            try:
                self.after_cancel(self._badge_refresh_after)
            except Exception:
                pass

        if not category:
            return

        # Turn off the category and all its rules in the visibility maps
        self._group_visible[category] = False
        for rule_identifier in self._rules_by_cat.get(category, []):
            self._rule_visible_by_cat.setdefault(category, {})[rule_identifier] = False

        # Persist changes to config and rebuild UI
        self.cfg.setdefault("rule_groups", {})
        self.cfg["rule_groups"]["visible"] = dict(self._group_visible)
        self.cfg["rule_groups"]["rules_visible"] = dict(self._rule_visible_by_cat)
        save_settings(self.cfg)

        self._rebuild_table_columns()
        self._refresh_table()

        # Provide subtle status feedback
        try:
            self.status.configure(text=f"Hidden category: {category}")
        except Exception:
            pass

    def _hide_rule(self, category: str, rule_identifier: str):
        """
        Hide a single rule within a category, persist the change and refresh UI.

        Steps:
          1. Cancel any pending badge refresh to avoid races during rebuild.
          2. Update the rule visibility map and persist settings.
          3. Rebuild table columns and refresh rows.
        """
        if self._badge_refresh_after:
            try:
                self.after_cancel(self._badge_refresh_after)
            except Exception:
                pass

        if not category or not rule_identifier:
            return

        # Turn off the requested rule
        self._rule_visible_by_cat.setdefault(category, {})[rule_identifier] = False

        # Persist only the rule visibility map (category-level state left unchanged)
        self.cfg.setdefault("rule_groups", {})
        self.cfg["rule_groups"]["rules_visible"] = dict(self._rule_visible_by_cat)
        save_settings(self.cfg)

        self._rebuild_table_columns()
        self._refresh_table()
        try:
            self.status.configure(text=f"Hidden rule: {rule_identifier} (in {category})")
        except Exception:
            pass

    # ---------- Close & persist ----------
    def _on_close(self):
        """
        Persist window and view settings to user config and terminate the app.

        Steps:
          1. Collect window geometry and all view/filter settings.
          2. Persist settings via save_settings.
          3. Destroy the main Tk window.
        """
        try:
            # Persist window geometry and view filters
            self.cfg.setdefault("window_settings", {})["geometry"] = self.geometry()
            self.cfg.setdefault("view_filters", {})["search"] = self._get_search_query()
            self.cfg.setdefault("view_filters", {})["severity"] = self._filter_sev.get()
            self.cfg.setdefault("view_filters", {})["pin_type"] = self._filter_type.get()
            self.cfg.setdefault("view_filters", {})["case_sensitive"] = bool(
                self._filter_case.get()
            )
            self.cfg.setdefault("view_filters", {})["only_violated"] = bool(
                self._filter_only_viol.get()
            )
            # Persist rule group order and visibility state
            self.cfg.setdefault("rule_groups", {})["order"] = list(self._group_order)
            self.cfg.setdefault("rule_groups", {})["visible"] = dict(self._group_visible)
            self.cfg.setdefault("rule_groups", {})["rules_visible"] = dict(
                self._rule_visible_by_cat
            )
            # persist adjustable header height
            try:
                self.cfg.setdefault("ui_settings", {})["header_height"] = int(
                    self._header_height
                )
            except Exception:
                pass
            try:
                if hasattr(self, "_main_split"):
                    self.cfg.setdefault("ui_settings", {})["main_split"] = int(
                        self._main_split.sashpos(0)
                    )
            except Exception:
                pass
            save_settings(self.cfg)
        except Exception:
            # Swallow errors to avoid blocking shutdown
            pass
        # Close the application window
        self.destroy()

    # ---------- Category band ----------
    def _tree_xscroll(self, first_fraction, last_fraction):
        """
        Handle horizontal scrollbar updates coming from the Treeview.

        Args:
            first_fraction (str | float): Fractional position of left edge of view (0.0..1.0).
            last_fraction (str | float): Fractional position of right edge of view (0.0..1.0).

        Steps:
          1. Update stored fractional x-scroll positions used by header rendering.
          2. Update the actual horizontal scrollbar widget.
          3. Redraw the category header canvas to reflect horizontal scroll.
          4. Schedule a debounced refresh of overlay badges to keep overlays in sync.
        """
        # Parse and store fractional scroll positions used throughout the class.
        self._xscroll_first = float(first_fraction)
        self._xscroll_last = float(last_fraction)

        # Update the horizontal scrollbar visually and refresh dependent UI.
        self.xsb.set(first_fraction, last_fraction)
        self._redraw_group_header()
        self._schedule_badge_refresh()

    def _on_xscroll(self, *args):
        """
        Wrapper for horizontal scrollbar actions.

        Forwards the scrollbar command to the Treeview xview. The Treeview is
        configured with an xscrollcommand that will call `_tree_xscroll`, so
        the visual/banner refresh is handled there.
        """
        # Forward scroll command to the Treeview; no additional logic required here.
        self.tree.xview(*args)

    # vertical scroll wrappers to keep overlays in sync
    def _on_tree_yscroll(self, first_fraction, last_fraction):
        """
        Keep vertical scrollbar widget synchronized and schedule overlay refresh.

        Args:
            first_fraction (str | float): Fractional top position of viewport.
            last_fraction (str | float): Fractional bottom position of viewport.

        Steps:
          1. Update the vertical scrollbar widget.
          2. Debounce and schedule overlay badge refresh so overlays follow scrolling.
        """
        # Update vertical scrollbar thumb position
        self.ysb.set(first_fraction, last_fraction)
        # Debounced overlay refresh keeps overlays responsive without storms.
        self._schedule_badge_refresh()

    def _on_yscroll(self, *args):
        """
        Forward vertical scrollbar actions to the Treeview and schedule overlays.

        This method is bound as the command for the vertical scrollbar widget.
        """
        # Forward the action to the Treeview vertical view and schedule overlays.
        self.tree.yview(*args)
        self._schedule_badge_refresh()

    def _measure_columns(self) -> list[tuple[str, int, int]]:
        """
        Measure the Treeview columns and compute their cumulative X positions.

        Returns:
            A list of tuples (column_id, column_start_x, column_width) where
            column_start_x is the unscrolled X coordinate within the full table.

        Purpose:
          - This helper centralizes logic to measure visible column widths and
            compute the total horizontal width of the table which is used by
            header drawing and overlay placement.
        """
        # Starting X position accumulator for columns (unscrolled coordinate)
        x_position = 0
        measured_columns: list[tuple[str, int, int]] = []

        # Retrieve the ordered column ids from the Treeview
        columns_list = list(self.tree["columns"])
        for column_id in columns_list:
            # Read the column width (defensive: default to 0 when missing)
            column_width = int(self.tree.column(column_id, "width") or 0)
            measured_columns.append((column_id, x_position, column_width))
            # Advance accumulator for the next column
            x_position += column_width

        # Cache the total width for other calculations (e.g. horizontal culling)
        self._col_total_width = x_position
        return measured_columns

    def _redraw_group_header(self):
        """
        Redraw the category band and rotated-rule header images.

        Responsibilities:
          - Clear the header canvas and set background.
          - Measure the Treeview column layout and compute an X offset based on current scroll.
          - Aggregate adjacent rule columns that share the same category into a single band.
          - Draw category bands and centered category names.
          - Draw pre-rendered rotated rule header images aligned to their columns.

        Notes / Constants:
          - BAND_TOP_MARGIN: top padding inside the header canvas for category bands.
          - BAND_MIN_HEIGHT and BAND_MAX_HEIGHT: control the visual band height range.
          - EDGE_PADDING: horizontal padding to avoid drawing touching the canvas edges.
        """
        # Constants that control header geometry and safe drawing margins.
        EDGE_PADDING = 2  # avoid drawing at the absolute canvas edges

        # Quick bail-out: ensure header canvas exists and is currently mapped.
        canvas = self.header_canvas
        if not canvas.winfo_ismapped():
            return

        # Step 1: clear previous drawings
        canvas.delete("all")
        self._hide_header_tooltip()

        # Step 2: measure current column layout in unscrolled coordinates
        columns_layout = self._measure_columns()
        if not columns_layout:
            return

        # Step 3: compute horizontal scroll offset in pixels to align canvas coords
        # Use max(1, ...) to avoid division by zero when total width is zero.
        scrolled_pixel_offset = int(self._xscroll_first * max(1, self._col_total_width))

        # Canvas geometry and color palette used for drawing
        canvas_height = int(canvas.winfo_height() or 30)

        palette = self.colors
        # canvas.configure(background=palette["band_bg"])
        canvas.configure(background="#d4d4d4")

        # Step 5: aggregate contiguous columns by category to draw single bands.
        category_groups: list[tuple[str, int, int]] = []
        current_category: str | None = None
        category_start_x: int | None = None
        category_end_x: int | None = None

        for column_id, column_start_x, column_width in columns_layout:
            # Compute the column's X coordinates relative to the unscrolled table,
            # then convert to canvas coordinates by subtracting the scrolled offset.
            col_canvas_x0 = column_start_x - scrolled_pixel_offset
            col_canvas_x1 = col_canvas_x0 + column_width

            # Base columns are excluded from category bands.
            if column_id in ("PIN", "DIR", "TYPE"):
                # Flush any active accumulated category before continuing
                if current_category is not None:
                    category_groups.append(
                        (current_category, category_start_x or 0, category_end_x or 0)
                    )
                current_category = None
                category_start_x = None
                category_end_x = None
                continue

            # Extract category from the column identifier using the SEPARATOR format "<category>__<rule_id>"
            category_name = column_id.split("__", 1)[0] if "__" in column_id else ""

            if current_category is None:
                # Start a new category group
                current_category = category_name
                category_start_x = col_canvas_x0
                category_end_x = col_canvas_x1
            elif category_name == current_category:
                # Extend the current group's right edge
                category_end_x = col_canvas_x1
            else:
                # Finalize previous group and start a new one
                category_groups.append(
                    (current_category, category_start_x or 0, category_end_x or 0)
                )
                current_category = category_name
                category_start_x = col_canvas_x0
                category_end_x = col_canvas_x1

        # If a group is still active after loop, append it.
        if current_category is not None:
            category_groups.append(
                (current_category, category_start_x or 0, category_end_x or 0)
            )

        # Step 6: draw category bands in the top portion of the header canvas.
        canvas_width = canvas.winfo_width()

        for category_name, group_x0, group_x1 in category_groups:
            # Apply padding to avoid drawing flush with the edges
            band_x0 = max(int(group_x0) + EDGE_PADDING, EDGE_PADDING)
            band_x1 = min(int(group_x1) - EDGE_PADDING, canvas_width - EDGE_PADDING)

            # Skip groups that are entirely off-canvas (fast path)
            if band_x1 <= EDGE_PADDING or band_x0 >= canvas_width - EDGE_PADDING:
                continue

        # Step 7: update header signature used by the poller to detect visual changes
        header_signature = (
            tuple(
                (col_id, self.tree.column(col_id, "width"))
                for col_id, _, _ in columns_layout
            ),
            round(self._xscroll_first, 4),
            canvas.winfo_width(),
            canvas.winfo_height(),
        )
        self._last_header_signature = header_signature

        # Step 8: draw bottom-aligned rotated header images (if they were cached)
        try:
            for column_id, column_start_x, column_width in columns_layout:
                # Skip base columns
                if column_id in ("PIN", "DIR", "TYPE"):
                    continue

                # Derive category and rule from the column id once
                if "__" in column_id:
                    category_name, rule_id = column_id.split("__", 1)
                else:
                    category_name, rule_id = "", column_id

                cached_image = self._col_heading_imgs.get(column_id)
                col_canvas_x0 = column_start_x - scrolled_pixel_offset

                draw_x = int(col_canvas_x0) + EDGE_PADDING + 0
                bottom_y = canvas_height + 12

                try:
                    if cached_image is not None:
                        # Draw the rotated header image and bind hover
                        item_id = canvas.create_image(
                            draw_x, bottom_y, image=cached_image, anchor="sw"
                        )
                        canvas.tag_bind(
                            item_id,
                            "<Enter>",
                            lambda e, c=category_name, r=rule_id: self._show_header_tooltip(
                                e, c, r
                            ),
                        )
                        canvas.tag_bind(item_id, "<Leave>", self._hide_header_tooltip)
                        canvas.tag_bind(item_id, "<Motion>", self._move_header_tooltip)
                    else:
                        # Fallback: draw glyph + stacked vertical short name; bind hover on both
                        # Derive compact label text (already in your code)
                        rule_id_fallback = rule_id  # same id
                        label_text = MEMPHYS_RULE_SHORT_MAP.get(
                            rule_id_fallback, rule_id_fallback
                        )

                        # Resolve glyph token & glyph char (reuse your existing mapping)
                        try:
                            group_map = PINCHECK_SCOREBOARD_CONFIG.get(
                                "rule_groups", {}
                            ).get("check_group_order_map", {})
                        except Exception:
                            group_map = {}
                        glyph_token = group_map.get(category_name, None)
                        TOKEN_GLYPH_MAP = {
                            "tag": "#",
                            "bus": "=",
                            "info-circle": "i",
                            "microchip": "◦",
                            "bolt": "⚡",
                            "eye": "👁",
                            "clock": "⏱",
                        }
                        glyph = TOKEN_GLYPH_MAP.get(
                            glyph_token,
                            (category_name[:1].upper() if category_name else "#"),
                        )

                        icon_size = max(10, self._size_small + 6)
                        text_gap = 4
                        text_x = int(col_canvas_x0) + EDGE_PADDING + 2

                        # Glyph item
                        glyph_id = None
                        try:
                            glyph_id = canvas.create_text(
                                text_x,
                                bottom_y,
                                text=glyph,
                                font=self._tk_font(max(8, self._size_small + 2)),
                                fill=palette.get("band_fg", "#000000"),
                                anchor="sw",
                            )
                        except Exception:
                            pass

                        # Stacked vertical label item
                        stacked = "\n".join(list(label_text))
                        text_x2 = text_x + icon_size + text_gap
                        label_id = None
                        try:
                            label_id = canvas.create_text(
                                text_x2,
                                bottom_y,
                                text=stacked,
                                font=self._tk_font(max(8, self._size_small)),
                                fill=palette.get("band_fg", "#000000"),
                                anchor="sw",
                            )
                        except Exception:
                            # Fallback horizontal if stacked fails
                            try:
                                label_id = canvas.create_text(
                                    text_x2,
                                    bottom_y,
                                    text=label_text,
                                    font=self._tk_font(max(8, self._size_small)),
                                    fill=palette.get("band_fg", "#000000"),
                                    anchor="sw",
                                )
                            except Exception:
                                pass

                        # Bind hover on whichever items were created
                        for bind_id in (glyph_id, label_id):
                            if bind_id is not None:
                                canvas.tag_bind(
                                    bind_id,
                                    "<Enter>",
                                    lambda e, c=category_name, r=rule_id: self._show_header_tooltip(
                                        e, c, r
                                    ),
                                )
                                canvas.tag_bind(
                                    bind_id, "<Leave>", self._hide_header_tooltip
                                )
                                canvas.tag_bind(
                                    bind_id, "<Motion>", self._move_header_tooltip
                                )

                except Exception:
                    # Protect header drawing from any unexpected errors
                    pass

        except Exception:
            # Protect header drawing from any unexpected errors
            pass

    def _header_poller(self):
        """
        Periodically check whether header geometry or scroll state changed and redraw.

        This poller detects changes in:
          - column widths
          - horizontal scroll fraction
          - header canvas width/height

        If a mismatch with the last recorded signature is found it triggers a redraw.
        The poller reschedules itself at a fixed interval to reduce churn.
        """
        try:
            current_signature = (
                tuple(
                    (col_id, self.tree.column(col_id, "width"))
                    for col_id in self.tree["columns"]
                ),
                round(self._xscroll_first, 4),
                self.header_canvas.winfo_width(),
                self.header_canvas.winfo_height(),
            )
            if current_signature != self._last_header_signature:
                # Redraw when anything relevant changed
                self._redraw_group_header()
        except Exception:
            # Swallow exceptions to avoid stopping the periodic poller.
            pass
        finally:
            # Reschedule the poller at a modest interval to reduce CPU usage.
            self.after(800, self._header_poller)

    def _focus_search(self):
        """
        Give keyboard focus to the search Entry and select its current text.

        This convenience is bound to Ctrl+F so users can quickly start typing.
        """
        if self._search_entry:
            try:
                self._search_entry.focus_set()
                self._search_entry.select_range(0, "end")
            except Exception:
                # Ignore focus failures (widget might not be mapped yet)
                pass

    # ===============================
    # NEW: Per-cell color badges (optimized)
    # ===============================
    def _level_colors(self, lvl: CellLevel) -> tuple[str, str]:
        """Return (bg, fg) for a given cell level using current theme."""
        c = self.colors
        if lvl == CellLevel.FAIL:
            return (c["error_bg"], c["error_fg"])
        if lvl == CellLevel.WARN:
            return (c["warn_bg"], c["warn_fg"])
        # Treat N/A same as PASS
        return (c["pass_bg"], c["pass_fg"])

    def _schedule_badge_refresh(self, delay: int = 30):
        """
        Debounce overlay refresh to avoid storms during scroll/resize.

        Cancels any previously scheduled refresh and schedules a new one to run
        after `delay` milliseconds. This reduces UI churn when multiple expose
        or scroll events happen in quick succession.
        """
        if self._badge_refresh_after:
            try:
                self.after_cancel(self._badge_refresh_after)
            except Exception:
                pass
        self._badge_refresh_after = self.after(delay, self._refresh_cell_badges)

    def _get_badge_from_pool(self) -> tk.Label:
        """
        Acquire or create a pooled badge Label used as a colored overlay for a
        single rule cell in the Treeview.

        Behavior / steps:
          1. If a Label is available in the pool (self._badge_pool) pop and
             return it.
          2. Otherwise create a new tk.Label parented to the Treeview, bind
             interaction handlers (click/context/scroll forwarding) and return it.
          3. Reset widget geometry tracking attribute before returning.

        Notes:
          - Pooled badges avoid creating/destroying many widgets during fast
            scrolling which improves responsiveness.
          - Newly-created badges forward mouse-wheel events to the Treeview so
            scrolling behaves normally while the cursor is over a badge.
        """
        # No module-level constants required here; behavior is local and simple.

        # If a pooled badge exists reuse it.
        if self._badge_pool:
            badge_label = self._badge_pool.pop()
            # Reset any stale state on reuse
            badge_label._pc_geom = None
            return badge_label

        # Create a new badge label and wire event handlers.

        badge_label = tk.Label(
            self.tree,
            bd=0,
            anchor="center",
            highlightthickness=1,  # 1px border
            highlightbackground="#3E3B3B",  # border color (change as needed)
            highlightcolor="#3E3B3B",  # active/highlight border color
        )

        # Bind primary/secondary click handlers so overlays behave like cells.
        badge_label.bind("<Button-1>", self._on_badge_click_generic)
        badge_label.bind("<Button-3>", self._on_badge_right_click)
        badge_label.bind("<Button-2>", self._on_badge_right_click)

        # ---- Forwarding mouse wheel / scroll events to the Treeview ----
        # Purpose: ensure mouse wheel scrolling still works when cursor is over a badge.
        def _forward_mousewheel(event, target_tree=self.tree):
            """
            Forward vertical mouse wheel events to the Treeview to scroll rows.

            On Windows/macOS event.delta is used; on X11 Button-4/5 events are
            handled by separate bindings below.
            """
            if getattr(event, "delta", None) is not None:
                # Positive delta scrolls up; negative scrolls down.
                step_direction = -1 if event.delta > 0 else 1
                target_tree.yview_scroll(step_direction, "units")
            return "break"

        def _forward_button4(event, target_tree=self.tree):
            """Forward X11 Button-4 (wheel up) to Treeview vertical scroll."""
            target_tree.yview_scroll(-1, "units")
            return "break"

        def _forward_button5(event, target_tree=self.tree):
            """Forward X11 Button-5 (wheel down) to Treeview vertical scroll."""
            target_tree.yview_scroll(1, "units")
            return "break"

        # Horizontal scroll when Shift is held
        def _forward_shift_wheel(event, target_tree=self.tree):
            """
            When Shift+Wheel is used, scroll horizontally on the Treeview.
            This mirrors common UI behavior for wide tables.
            """
            if getattr(event, "delta", None) is not None:
                step_direction = -1 if event.delta > 0 else 1
                target_tree.xview_scroll(step_direction, "units")
            return "break"

        # Attach forwarding handlers
        badge_label.bind("<MouseWheel>", _forward_mousewheel)
        badge_label.bind("<Button-4>", _forward_button4)
        badge_label.bind("<Button-5>", _forward_button5)
        badge_label.bind("<Shift-MouseWheel>", _forward_shift_wheel)

        # Initialize geometry tracking attribute used by the placer logic.
        badge_label._pc_geom = None
        return badge_label

    def _on_badge_right_click(self, event):
        """
        Show the same context menu as the Treeview when the user right-clicks
        on a colored overlay badge.

        Steps:
          1. Identify the badge widget and retrieve the stored row and column ids.
          2. Populate the shared context menu (self.ctx) consistent with the
             cell-based menu (_show_context_menu).
          3. Display the menu at the cursor position.
        """
        badge_widget = event.widget
        row_item = getattr(badge_widget, "_pc_item", None)
        column_id = getattr(badge_widget, "_pc_cid", None)
        if not row_item or not column_id:
            return

        # Mirror context state expected by other handlers
        self._ctx_item = row_item
        self._ctx_col_name = column_id

    def _release_badge(self, badge_widget: tk.Label):
        """
        Return a badge widget to the pool for later reuse.

        Actions:
          - Hide the widget by removing it from placement.
          - Reset geometry tracking and append to the pool list.
        """
        try:
            badge_widget.place_forget()
        except Exception:
            # Ignore placement removal failures; continue returning to pool.
            pass
        badge_widget._pc_geom = None
        self._badge_pool.append(badge_widget)

    def _destroy_cell_badges(self):
        """
        Remove all active overlay badges from the UI and return them to the pool.

        This function clears the active badge registry (self._badge_widgets)
        by releasing each widget instead of destroying so they may be reused.
        """
        for badge_widget in list(self._badge_widgets.values()):
            self._release_badge(badge_widget)
        self._badge_widgets.clear()

    def _destroy_cell_badges_safe(self):
        """
        Safely attempt to destroy/release all badge overlays.

        Wraps _destroy_cell_badges in a try/except to avoid raising while
        called from toggle handlers or during teardown.
        """
        try:
            self._destroy_cell_badges()
        except Exception:
            pass

    def _refresh_cell_badges(self):
        """
        Recompute, create and position colored overlay badges for visible
        rule cells in the current Treeview viewport.

        High level steps:
          1. Clear pending refresh token.
          2. Bail out early if overlays disabled, no tree or no cell cache.
          3. Compute visible rows (vertical culling) and visible rule columns
             (horizontal culling).
          4. For each visible (row, column) that has data create or reuse a
             badge, configure its appearance and place it over the cell bbox.
          5. Release badges that are no longer needed back to the pool.

        Constants (local):
          - VIEWPORT_GUARD_BAND: small number of extra rows above/below the
            visible range to pre-warm overlays when scrolling.
          - MIN_BADGE_WIDTH / MIN_BADGE_HEIGHT: ensure badges remain visible
            even when columns are very narrow.
        """
        # Local constants that control placement safety and appearance.
        VIEWPORT_GUARD_BAND = 2  # extra rows above/below the exact visible range
        MIN_BADGE_WIDTH = 8  # minimum width of placed badge so glyph is visible
        MIN_BADGE_HEIGHT = 1  # minimum height of placed badge
        HORIZONTAL_CULL_MARGIN = 8  # pixels margin to include near-edge columns

        # Clear the scheduled refresh id (we are executing it now).
        self._badge_refresh_after = None

        # Fast exits: overlays globally disabled or tree/cell cache missing.
        if not self._cell_color_overlays.get():
            # Ensure any existing badges are cleaned up.
            self._destroy_cell_badges()
            return
        if not hasattr(self, "tree"):
            return
        if not self._cell_cache:
            self._destroy_cell_badges()
            return

        # Get full list of Treeview columns and bail if there are no dynamic columns.
        all_columns = list(self.tree["columns"])
        if len(all_columns) <= 3:
            self._destroy_cell_badges()
            return

        # ---- Vertical culling: determine which items (rows) are visible ----
        try:
            y_first_fraction, y_last_fraction = self.tree.yview()  # fractions in [0,1]
        except Exception:
            y_first_fraction, y_last_fraction = 0.0, 1.0

        all_items = list(self.tree.get_children(""))
        total_items = len(all_items)
        if total_items == 0:
            self._destroy_cell_badges()
            return

        # Compute indices with a small guard band so badges appear smoothly while scrolling.
        start_index = max(
            0,
            min(
                total_items - 1, int(y_first_fraction * total_items) - VIEWPORT_GUARD_BAND
            ),
        )
        end_index = max(
            0, min(total_items, int(y_last_fraction * total_items) + VIEWPORT_GUARD_BAND)
        )
        visible_row_items = all_items[start_index:end_index]

        # ---- Horizontal culling: determine which dynamic columns intersect viewport ----
        if self._col_total_width <= 0:
            # Ensure column width total is measured
            self._measure_columns()

        x_view_start = self._xscroll_first * max(1, self._col_total_width)
        x_view_end = self._xscroll_last * max(1, self._col_total_width)

        # Dynamic columns are the columns after the first three base columns.
        dynamic_columns = all_columns[3:]
        visible_dynamic_column_ids: list[str] = []
        x_accumulator = 0
        for column_id in all_columns:
            column_width = int(self.tree.column(column_id, "width") or 0)
            column_start_x, column_end_x = x_accumulator, x_accumulator + column_width
            x_accumulator = column_end_x
            # Only consider dynamic rule columns that intersect the visible horizontal span.
            if (
                (column_id in dynamic_columns)
                and (column_end_x >= x_view_start - HORIZONTAL_CULL_MARGIN)
                and (column_start_x <= x_view_end + HORIZONTAL_CULL_MARGIN)
            ):
                visible_dynamic_column_ids.append(column_id)

        if not visible_dynamic_column_ids:
            # Nothing to draw; cleanup and return.
            self._destroy_cell_badges()
            return

        # Track which badge keys we want to remain after this refresh.
        wanted_badge_keys: set[tuple[str, str]] = set()

        # Iterate items and visible dynamic columns to create/update overlays.
        for row_item in visible_row_items:
            if row_item == "__OTHER_HEADER__":
                continue

            # Per-row compact cell map previously populated during _refresh_table.
            row_cells_map = self._cell_cache.get(row_item, {})
            for column_id in visible_dynamic_column_ids:
                cell_info = row_cells_map.get(column_id)
                if not cell_info:
                    continue

                # Query the Treeview cell bbox for exact placement coordinates.
                try:
                    cell_bbox = self.tree.bbox(row_item, column_id)
                except Exception:
                    cell_bbox = ()

                if not cell_bbox:
                    continue

                cell_x, cell_y, cell_w, cell_h = cell_bbox
                pad = 1
                place_x = cell_x + pad
                place_y = cell_y + 1
                place_w = max(MIN_BADGE_WIDTH, cell_w - 2 * pad)
                place_h = max(MIN_BADGE_HEIGHT, cell_h - 2)

                badge_key = (row_item, column_id)
                wanted_badge_keys.add(badge_key)

                # Determine colors and glyph for this cell level
                background_color, foreground_color = self._level_colors(
                    cell_info["level"]
                )
                glyph_text = STATUS_GLYPH.get(cell_info["level"], " ")

                # Reuse existing badge widget or fetch one from the pool.
                badge_widget = self._badge_widgets.get(badge_key)
                if badge_widget is None:
                    # Acquire pooled widget and initialize identity attributes.
                    badge_widget = self._get_badge_from_pool()
                    badge_widget._pc_item = row_item
                    badge_widget._pc_cid = column_id
                    badge_widget._pc_geom = None
                    self._badge_widgets[badge_key] = badge_widget
                    badge_widget.configure(
                        bg=background_color,
                        fg=foreground_color,
                        text=glyph_text,
                        font=self._badge_font,
                    )
                else:
                    # Update identity in case widget was reused previously.
                    badge_widget._pc_item = row_item
                    badge_widget._pc_cid = column_id
                    # Update only when appearance changed to reduce widget churn.
                    if badge_widget.cget("text") != glyph_text:
                        badge_widget.configure(text=glyph_text)
                    if badge_widget.cget("bg") != background_color:
                        badge_widget.configure(bg=background_color)
                    if badge_widget.cget("fg") != foreground_color:
                        badge_widget.configure(fg=foreground_color)

                # Place the badge only when geometry changed.
                new_geometry = (place_x, place_y, place_w, place_h)
                if getattr(badge_widget, "_pc_geom", None) != new_geometry:
                    try:
                        badge_widget.place(
                            x=place_x, y=place_y, width=place_w, height=place_h
                        )
                        badge_widget._pc_geom = new_geometry
                    except Exception:
                        # Placement may fail during rapid UI changes; ignore and continue.
                        pass

        # Release any badge widgets that are no longer wanted back to pool.
        for existing_key in tuple(self._badge_widgets.keys()):
            if existing_key not in wanted_badge_keys:
                removed_widget = self._badge_widgets.pop(existing_key)
                self._release_badge(removed_widget)

    def _on_badge_click_generic(self, event):
        """
        Generic left-click handler for overlay badges.

        Extracts stored identifiers from the clicked widget and delegates to the
        badge click handler which shows details for the corresponding cell.
        """
        badge_widget = event.widget
        row_item = getattr(badge_widget, "_pc_item", None)
        column_id = getattr(badge_widget, "_pc_cid", None)
        if row_item and column_id:
            self._badge_click(row_item, column_id)

    def _badge_click(self, row_item: str, column_id: str):
        """
        Handle a logical click on a badge overlay: select the row and show the
        details pane for the associated rule (or whole pin for base columns).

        Steps:
          - If the click corresponds to a base column, show pin details.
          - Otherwise parse category/rule, select the Treeview row and call
            DetailsBottom.show_pin_rule with the violations for that cell.
        """
        # Guard: base columns should just show the pin details.
        if column_id in ("PIN", "DIR", "TYPE"):
            self._show_details_for_pin(row_item)
            return

        # Parse category and rule id from column identifier
        if "__" in column_id:
            category_name, rule_identifier = column_id.split("__", 1)
        else:
            category_name, rule_identifier = ("", column_id)

        # Ensure the row is selected in the Treeview for visual feedback.
        try:
            self.tree.focus(row_item)
            self.tree.selection_set(row_item)
        except Exception:
            pass

        # Lookup violations for this row + rule and show details.
        violations_for_cell = self._viol_by_pin_by_rule.get(row_item, {}).get(
            rule_identifier, []
        )
        self.detail.show_pin_rule(
            row_item,
            category_name,
            rule_identifier,
            violations_for_cell,
            self._pin_record_by_name(row_item),
            self._rundata,
        )
        
        # reveal the Details toggle after badge click
        try:
            if hasattr(self, "analysis_tab") and self.analysis_tab:
                self.analysis_tab.show_details_toggle()
        except Exception:
            pass
