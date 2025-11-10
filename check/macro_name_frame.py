import tkinter as tk
from tkinter import ttk, Menu 
from typing import Dict, Any, Callable, Optional 

# --- CustomTooltip Class (Restored with Type Hinting) ---
class CustomTooltip:
    """A minimal, professional Tooltip implementation for modern Tkinter UIs."""
    def __init__(self, widget: tk.Widget, text: str, align_widget: tk.Widget) -> None:
        self.widget = widget
        self.text = text
        self.align_widget = align_widget
        self.tip_window: Optional[tk.Toplevel] = None

    def showtip(self, event=None) -> None:
        if self.tip_window or not self.text:
            return
        x = self.align_widget.winfo_rootx()
        y = self.align_widget.winfo_rooty() + self.align_widget.winfo_height() + 2 

        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(self.tip_window, text=self.text, justify=tk.LEFT,
                          background="#FFFFE0", foreground="#333333",
                          relief=tk.SOLID, borderwidth=1,
                          font=("Segoe UI", 9))
        label.pack(ipadx=4, ipady=4)

    def hidetip(self, event=None) -> None:
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None

# --- Main Frame Widget (Fixed and Complete) ---
class MacroNameFrame(ttk.Frame):
    
    def __init__(self, 
                 master: tk.Tk | ttk.Frame, 
                 macro_name: str, 
                 macro_path: str, 
                 **kwargs: Any) -> None:
        
        # 🔑 FIX: Explicitly remove borders from the main frame
        super().__init__(master, padding="10", relief='flat', borderwidth=0, **kwargs)
        
        self.macro_name: str = macro_name
        self.macro_path: str = macro_path
        self.copy_button: Optional[ttk.Button] = None
        self._hide_id: Optional[str] = None
        
        self.columnconfigure(0, weight=0) 
        self.columnconfigure(1, weight=1) 
        self.columnconfigure(2, weight=0)
        
        self._create_widgets()
        
    def _create_widgets(self) -> None:
        style = ttk.Style(self.master)
        style.configure("Copy.TButton", font=("Segoe UI", 9), foreground="#111111", padding=(0,0,0,0))
        
        # Static Label
        self.name_label = ttk.Label(self, text="Macro:", font=("Segoe UI", 10, "bold"), foreground="#4A4A4A")
        self.name_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Nested frame (also flat/borderless)
        self.macro_name_frame: ttk.Frame = ttk.Frame(self, relief='flat', borderwidth=0)
        self.macro_name_frame.pack(side=tk.LEFT)
        
        # Macro Name Display
        self.macro_display: ttk.Label = ttk.Label(self.macro_name_frame, text=self.macro_name, 
                                       font=("Segoe UI", 10), foreground="#007ACC")
        self.macro_display.pack(side=tk.LEFT, padx=(0, 0))
        
        # Copy button (initially hidden)
        self.copy_button = ttk.Button(self.macro_name_frame, text="⧉", command=self._copy_name, 
                                      width=1, style="Copy.TButton")
        
        # Tooltip Setup
        self.tooltip: CustomTooltip = CustomTooltip(
            self.master, 
            text=f"Full Location: {self.macro_path}", 
            align_widget=self.macro_display
        )
        
        # Bind Events
        self.macro_name_frame.bind("<Enter>", self._on_enter)
        self.macro_name_frame.bind("<Leave>", self._on_leave)
        self.macro_display.bind("<Enter>", self._on_enter)
        self.macro_display.bind("<Leave>", self._on_leave)
        
    def _on_enter(self, event: tk.Event) -> None:
        if self._hide_id:
             self.master.after_cancel(self._hide_id)
        self.tooltip.showtip()
        self._show_copy_button()

    def _on_leave(self, event: tk.Event) -> None:
        self._hide_copy_button_after_delay()
        self.tooltip.hidetip()
        
    def _show_copy_button(self) -> None:
        if self.copy_button and self.copy_button.winfo_ismapped() == 0:
            self.copy_button.pack(side=tk.LEFT, ipadx=4) 
            self.copy_button.bind("<Enter>", self._on_button_enter)
            self.copy_button.bind("<Leave>", self._on_button_leave)
            
    def _on_button_enter(self, event: tk.Event) -> None:
        if self._hide_id:
            self.master.after_cancel(self._hide_id)

    def _on_button_leave(self, event: tk.Event) -> None:
        self._hide_copy_button_after_delay()

    def _hide_copy_button_after_delay(self, event: Optional[tk.Event] = None) -> None:
        self._hide_id = self.master.after(50, self._remove_copy_button)
        
    def _remove_copy_button(self) -> None:
        if self.copy_button and self.copy_button.winfo_ismapped():
            self.copy_button.pack_forget()

    def _copy_name(self) -> None:
        """Copies the macro name (the text) and shows the tick mark."""
        self.clipboard_clear()
        self.clipboard_append(self.macro_name)
        self.update() 
        print(f"Copied to clipboard: {self.macro_name}")
        
        # 🟢 RESTORED: Visual feedback (tick mark)
        if self.copy_button and self.copy_button.winfo_ismapped():
            original_text = self.copy_button.cget("text")
            self.copy_button.config(text="✓", state=tk.DISABLED) # Show tick mark
            # Schedule a function to revert the button state after 800ms
            self.master.after(800, 
                              lambda: self.copy_button and self.copy_button.config(text=original_text, state=tk.NORMAL))


# --- Main Application Setup ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Dynamic UI Example (Functional)")
    root.geometry("480x150")

    macro_full_path = "/Users/Developer/Projects/Automation/dc_asdfk__asjdfkk.py"
    macro_display_name = "dc_asdfk__asjdfkk"
    
    macro_frame = MacroNameFrame(
        root,
        macro_name=macro_display_name,
        macro_path=macro_full_path
    )
    macro_frame.pack(pady=20, padx=20, fill='x')

    ttk.Label(root, text="Click the button for the copy action and visual feedback.", 
              font=("Segoe UI", 9, "italic")).pack(pady=10)

    root.mainloop()