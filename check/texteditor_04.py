import tkinter as tk
from tkinter import Toplevel

class Tooltip:
    """Simple tooltip that appears near the mouse cursor."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None

    def show(self, x, y):
        """Show tooltip at given coordinates."""
        if self.tip_window or not self.text:
            return
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # No window borders
        tw.wm_geometry(f"+{x + 20}+{y + 20}")
        label = tk.Label(
            tw, text=self.text, background="#FFFFE0",
            relief="solid", borderwidth=1, font=("Segoe UI", 10)
        )
        label.pack(ipadx=5, ipady=2)

    def hide(self):
        """Hide tooltip."""
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


class TextViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter Text Viewer with Links")
        self.root.geometry("600x400")

        # Create text widget
        self.text = tk.Text(root, wrap="word", font=("Consolas", 12))
        self.text.pack(expand=True, fill="both", padx=10, pady=10)

        # Example text
        content = (
            "This is a sample text viewer.\n\n"
            "Hover over the word Python to see details.\n"
            "Click it to open a detail window.\n"
            "You can also hover over Tkinter for info."
        )
        self.text.insert("1.0", content)

        # Configure tags for links
        self.create_link("Python", "1.38", "1.44", "Python is a powerful programming language.")
        self.create_link("Tkinter", "4.18", "4.25", "Tkinter is Python's standard GUI library.")

        # Disable editing
        self.text.config(state="disabled")

        # Active tooltip reference
        self.active_tooltip = None

    def create_link(self, word, start, end, tooltip_text):
        """Add a clickable, hoverable link to the text widget."""
        tag_name = f"link_{word.lower()}"
        self.text.tag_add(tag_name, start, end)
        self.text.tag_config(
            tag_name, foreground="blue", underline=True
        )

        # Bind events
        self.text.tag_bind(tag_name, "<Enter>", lambda e, t=tooltip_text: self.show_tooltip(e, t))
        self.text.tag_bind(tag_name, "<Leave>", self.hide_tooltip)
        self.text.tag_bind(tag_name, "<Button-1>", lambda e, w=word: self.open_popup(w))

    def show_tooltip(self, event, text):
        """Display tooltip near cursor."""
        self.active_tooltip = Tooltip(self.text, text)
        self.active_tooltip.show(event.x_root, event.y_root)

    def hide_tooltip(self, event):
        """Hide tooltip when mouse leaves."""
        if self.active_tooltip:
            self.active_tooltip.hide()
            self.active_tooltip = None

    def open_popup(self, word):
        """Open a new Toplevel window when link is clicked."""
        popup = Toplevel(self.root)
        popup.title(f"{word} Details")
        popup.geometry("300x200")
        tk.Label(
            popup,
            text=f"This is a popup for {word}.",
            font=("Segoe UI", 12),
            wraplength=250
        ).pack(expand=True, fill="both", padx=10, pady=10)
        tk.Button(popup, text="Close", command=popup.destroy).pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = TextViewer(root)
    root.mainloop()
