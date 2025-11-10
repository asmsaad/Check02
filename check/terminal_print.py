import tkinter as tk
from tkinter import ttk
import time

class Terminal(tk.Frame):
    """
    A class to encapsulate the terminal display.
    It uses a Text widget with tags for styling.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # --- Theme Color Definitions ---
        self.themes = {
            "dark": {
                "bg": "black",
                "fg": "white",
                "error": "#FF4136",
                "warning": "#FFDC00",
                "highlight": "#7FDBFF",
                "time": "#2ECC40"
            },
            "light": {
                "bg": "white",
                "fg": "black",
                "error": "#D32F2F",    # Darker red
                "warning": "#FFA000",  # Darker amber
                "highlight": "#0277BD", # Darker blue
                "time": "#388E3C"     # Darker green
            }
        }
        self.current_theme = "dark"
        
        # Configure the frame
        self.config(bg=self.themes["dark"]["bg"])
        
        # Create a scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        
        # Create the Text widget
        self.text_area = tk.Text(
            self,
            bg=self.themes["dark"]["bg"],
            fg=self.themes["dark"]["fg"],
            font=("Consolas", 10),
            yscrollcommand=self.scrollbar.set,
            wrap=tk.WORD
        )
        
        # --- Bindings to make read-only but allow copy ---
        self.text_area.bind("<KeyPress>", self._on_key_press) # Block typing/deletion
        self.text_area.bind("<<Paste>>", lambda e: "break")     # Block paste
        self.text_area.bind("<<Cut>>", lambda e: "break")       # Block cut
        
        self.scrollbar.config(command=self.text_area.yview)
        
        # --- Layout ---
        # Use grid for robust resizing
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        
        self.text_area.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # --- Configure Tags for Styling ---
        # Initialize with dark theme
        self._configure_tags(self.themes["dark"])

    def _configure_tags(self, palette):
        """Internal method to set all tag colors."""
        self.text_area.tag_config(
            "normal",
            foreground=palette["fg"]
        )
        self.text_area.tag_config(
            "error",
            foreground=palette["error"]
        )
        self.text_area.tag_config(
            "warning",
            foreground=palette["warning"]
        )
        self.text_area.tag_config(
            "highlight",
            foreground=palette["highlight"],
            font=("Consolas", 10, "bold")
        )
        self.text_area.tag_config(
            "time",
            foreground=palette["time"],
            font=("Consolas", 10, "italic")
        )

    def set_theme(self, theme_name):
        """Public method to switch the terminal's color theme."""
        if theme_name not in self.themes or theme_name == self.current_theme:
            return
            
        palette = self.themes[theme_name]
        
        # Update frame and text area background
        self.config(bg=palette["bg"])
        self.text_area.config(bg=palette["bg"], fg=palette["fg"])
        
        # Re-configure all tags with new colors
        self._configure_tags(palette)
        
        self.current_theme = theme_name

    def _on_key_press(self, event):
        """
        Internal method to make the Text widget read-only.
        Blocks modifications but allows navigation, selection, and copy.
        """
        
        # Block typing printable characters
        # event.char is the character, but is empty for special keys
        if event.char and event.char.isprintable():
            return "break"
            
        # Block modification keys by name
        if event.keysym in ("BackSpace", "Delete"):
            return "break"

        # Allow all other keys (Ctrl, Shift, Arrows, Home, End, Ctrl+C, Ctrl+A, Command+C, etc.)
        # to pass through, enabling selection and copying.
        return

    def log(self, message, style="normal"):
        """
        Public method to add a styled log message to the terminal.
        This is the "real-time" part.
        """
        # Check if scrollbar is at the bottom *before* inserting text
        # .get() returns (top_fraction, bottom_fraction)
        scroll_pos = self.scrollbar.get()
        # Use a tolerance check for floating point imprecision
        is_at_bottom = (scroll_pos[1] >= 0.999)
        
        # We no longer need to toggle state since widget is always NORMAL
        
        # Add a timestamp for time text
        if style == "time":
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            full_message = f"[{timestamp}] {message}\n"
            self.text_area.insert(tk.END, full_message, (style,))
        else:
            full_message = f"{message}\n"
            self.text_area.insert(tk.END, full_message, (style,))
        
        # --- Auto-scrolling ---
        # Only scroll to the end if we were already at the bottom
        if is_at_bottom:
            self.text_area.see(tk.END)


class Poster(tk.Toplevel):
    """
    The Toplevel window for posting messages to the terminal.
    """
    def __init__(self, parent, log_callback):
        super().__init__(parent)
        self.title("Message Poster")
        self.geometry("400x300")
        
        # This is the function we'll call, e.g., terminal.log
        self.log_callback = log_callback
        
        # This variable will store the selected radio button's value
        self.style_var = tk.StringVar(value="normal")
        
        # --- Layout Frames ---
        controls_frame = ttk.Frame(self, padding=10)
        controls_frame.pack(side="left", fill="y")
        
        text_frame = ttk.Frame(self, padding=10)
        text_frame.pack(side="right", fill="both", expand=True)
        
        # --- Controls (Left Side) ---
        ttk.Label(controls_frame, text="Message Style:").pack(anchor="w")
        
        # Radio buttons
        styles = [
            ("Normal", "normal"),
            ("Error", "error"),
            ("Warning", "warning"),
            ("Highlighted", "highlight"),
            ("Time Text", "time")
        ]
        
        for text, value in styles:
            ttk.Radiobutton(
                controls_frame,
                text=text,
                variable=self.style_var,
                value=value
            ).pack(anchor="w", padx=10, pady=2)
            
        # Post Button
        self.post_button = ttk.Button(
            controls_frame,
            text="Post to Terminal",
            command=self.post_message
        )
        self.post_button.pack(anchor="w", pady=20)
        
        # --- Text Area (Right Side) ---
        self.message_text = tk.Text(text_frame, height=10, width=40, wrap=tk.WORD)
        self.message_text.pack(fill="both", expand=True)
        
        # Make the poster window stay on top
        self.transient(parent)
        # self.grab_set() # This line was removed to make the window non-modal

    def post_message(self):
        """
        Gets text and style, then calls the callback function.
        """
        # Get message, preserving all internal whitespace and newlines
        # "end-1c" gets all text *except* the final newline tk.Text adds
        message = self.message_text.get("1.0", "end-1c")
        
        # Get the selected style from the radio variable
        style = self.style_var.get()
        
        if message and self.log_callback:
            # Call the function we were given (terminal.log)
            self.log_callback(message, style)
            
            # Clear the text area for the next message
            self.message_text.delete("1.0", tk.END)


class App(tk.Tk):
    """
    The main application class that ties everything together.
    """
    def __init__(self):
        super().__init__()
        self.title("Main Application Window")
        self.geometry("900x700")
        
        # --- Configure Main Window Layout ---
        # We'll make two rows, each taking 50% of the height
        self.rowconfigure(0, weight=1)  # Top half
        self.rowconfigure(1, weight=1)  # Bottom half (for terminal)
        self.columnconfigure(0, weight=1)
        
        # --- Top Frame (Placeholder) ---
        top_frame = ttk.Frame(self, borderwidth=2, relief="ridge")
        top_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        
        # --- Top Frame Contents ---
        main_label = ttk.Label(
            top_frame,
            text="This is the top half of the application.",
            font=("Arial", 14)
        )
        main_label.pack(expand=True)
        
        # Frame to hold the control buttons
        controls_frame = ttk.Frame(top_frame)
        controls_frame.pack(fill="x", side="bottom", pady=10)
        
        # --- Terminal (Bottom Half) ---
        # Create the Terminal instance
        self.terminal = Terminal(self)
        self.terminal.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        # --- Poster Window Button ---
        self.open_poster_btn = ttk.Button(
            controls_frame,
            text="Open Poster Window",
            command=self.open_poster
        )
        self.open_poster_btn.pack(side="left", padx=(10, 5))
        
        # --- Theme Toggle Button ---
        self.theme_var = tk.StringVar(value="dark")
        self.theme_toggle = ttk.Checkbutton(
            controls_frame,
            text="Enable Light Mode",
            variable=self.theme_var,
            onvalue="light",
            offvalue="dark",
            command=self.toggle_theme
        )
        self.theme_toggle.pack(side="left", padx=5)
        
        # Handle closing the window
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.poster_window = None

    def toggle_theme(self):
        """
        Called by the theme Checkbutton.
        Tells the terminal to change its theme.
        """
        theme_name = self.theme_var.get()
        self.terminal.set_theme(theme_name)

    def open_poster(self):
        # Only open one poster window at a time
        if self.poster_window is None or not self.poster_window.winfo_exists():
            self.poster_window = Poster(self, log_callback=self.terminal.log)
        else:
            self.poster_window.lift() # Bring to front

    def on_exit(self):
        """
        Custom exit handler to gracefully close all windows.
        """
        # Explicitly destroy the poster window if it exists
        if self.poster_window:
            self.poster_window.destroy()
        # Destroy the main window
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()

