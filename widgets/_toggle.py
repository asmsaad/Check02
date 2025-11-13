import tkinter as tk
from tkinter import ttk

class ToggleButtonApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Toggle Button Example")
        self.geometry("300x150")
        
        # Set up a clean style
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background='#F0F0F0')
        
        # Make the content centrally aligned
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        self.toggle_frame = ToggleButtonFrame(self)
        self.toggle_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

class ToggleButtonFrame(ttk.Frame):
    """A Frame containing the toggle button and a collapsible area."""
    
    # Unicode characters for the arrows
    COLLAPSED_TEXT = '\u25b6' # Right-pointing triangle (>)
    EXPANDED_TEXT = '\u25c0'  # Down-pointing triangle (v)
    
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        self.is_expanded = False 


        self._create_widgets()

    def _create_widgets(self):

        self.toggle_button = ttk.Button(
            self, 
            text=self.COLLAPSED_TEXT + " Show Details", 
            command=self.toggle,
            style="Toggle.TButton"
        )

        self.toggle_button.grid(row=0, column=0, sticky="w", pady=(0, 5))


    def toggle(self):
        """Switches the state of the panel and updates the button."""
        
        if self.is_expanded:
            self.toggle_button.config(text=self.COLLAPSED_TEXT)
            self.is_expanded = False
        else:
            self.toggle_button.config(text=self.EXPANDED_TEXT)
            self.is_expanded = True


if __name__ == "__main__":
    app = ToggleButtonApp()
    app.mainloop()