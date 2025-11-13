import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Any

class FindWidget(ttk.Frame):
    """
    A Tkinter frame that mimics the VS Code find widget (light theme).
    
    Uses ttk.Button and manual state management for toggles.
    """
    
    def __init__(
        self, 
        master: tk.Widget, 
        on_change_callback: Callable[[Dict[str, Any]], None], 
        **kwargs: Any
    ) -> None:
        super().__init__(master, **kwargs)
        self.on_change = on_change_callback

        # --- 2. Create Control Variables ---
        self.text_var = tk.StringVar()
        self.case_var = tk.BooleanVar(value=False)
        self.word_var = tk.BooleanVar(value=False)
        self.regex_var = tk.BooleanVar(value=False)

        # --- 3. Create Widgets ---
        # self.entry = ttk.Entry(
        #     self, 
        #     textvariable=self.text_var,
        #     # width=40,
        #     style="FindWidget.TEntry"
        # )
        self.entry = tk.Entry(
            self, 
            textvariable=self.text_var,
            font=("Arial","10")
            # width=40,
            # style="FindWidget.TEntry"
        )

        # Use ttk.Button and link to a command
        self.btn_case = ttk.Button(
            self,
            text="Aa",
            command=self._toggle_case,
            style="FindWidget.TButton"  # Use the base style
        )
        
        self.btn_word = ttk.Button(
            self,
            text="ab|",
            command=self._toggle_word,
            style="FindWidget.TButton"
        )
        
        self.btn_regex = ttk.Button(
            self,
            text=".*",
            command=self._toggle_regex,
            style="FindWidget.TButton"
        )

        # --- 4. Layout Widgets ---
        self.entry.pack(
            side=tk.LEFT, 
            fill=tk.X, 
            expand=True, 
            padx=(0, 5), 
             pady=5,
            ipadx=2
        )
        # self.btn_case.pack(side=tk.LEFT, padx=1, pady=5)
        # self.btn_word.pack(side=tk.LEFT, padx=1, pady=5)
        # self.btn_regex.pack(side=tk.LEFT, padx=(1, 5), pady=5)
        
        self.btn_case.pack(side=tk.LEFT, padx=1, pady=0)
        self.btn_word.pack(side=tk.LEFT, padx=1, pady=0)
        self.btn_regex.pack(side=tk.LEFT, padx=(1, 5), pady=0)

        # --- 5. Bind Callbacks ---
        
        # When text changes, trigger the callback
        self.text_var.trace_add("write", self._trigger_callback)
        
        # When variables change, update button styles AND trigger callback
        self.case_var.trace_add("write", self._on_toggle_change)
        self.word_var.trace_add("write", self._on_toggle_change)
        self.regex_var.trace_add("write", self._on_toggle_change)

    # --- 6. New Toggle Handlers ---
    
    def _toggle_case(self) -> None:
        """Invert the case_var boolean."""
        self.case_var.set(not self.case_var.get())
        
    def _toggle_word(self) -> None:
        """Invert the word_var boolean."""
        self.word_var.set(not self.word_var.get())

    def _toggle_regex(self) -> None:
        """Invert the regex_var boolean."""
        self.regex_var.set(not self.regex_var.get())

    def _on_toggle_change(self, *args: Any) -> None:
        """
        Called by the trace when a boolean variable changes.
        Updates styles and then fires the main callback.
        """
        self._update_button_styles()
        self._trigger_callback()

    def _update_button_styles(self) -> None:
        """Manually set the style of each button based on its variable."""
        
        # Style for 'Case' button
        case_style = "FindWidget.TButton.Selected" if self.case_var.get() else "FindWidget.TButton"
        self.btn_case.config(style=case_style)
        
        # Style for 'Word' button
        word_style = "FindWidget.TButton.Selected" if self.word_var.get() else "FindWidget.TButton"
        self.btn_word.config(style=word_style)
        
        # Style for 'RegEx' button
        regex_style = "FindWidget.TButton.Selected" if self.regex_var.get() else "FindWidget.TButton"
        self.btn_regex.config(style=regex_style)

    def _trigger_callback(self, *args: Any) -> None:
        """
        Internal function to gather state and call the external callback.
        """
        state = self.get_state()
        self.on_change(state)

    def get_state(self) -> Dict[str, Any]:
        """Public method to manually get the current state."""
        return {
            "text": self.text_var.get(),
            "CA": self.case_var.get(),
            "MW": self.word_var.get(),
            "RegEx": self.regex_var.get(),
        }

# --- Styling Function ---

# def setup_styles() -> None:
#     """
#     Configures the ttk styles for the FindWidget
#     to match a VS Code light theme.
#     """
#     style = ttk.Style()
#     style.theme_use("clam")

#     # --- Colors ---
#     BG_COLOR = "#F3F3F3"
#     ENTRY_BG = "#FFFFFF"
#     BORDER_COLOR = "#CECECE"
#     TOGGLE_FG = "#666666"
    
#     # Selected/Active (Blue)
#     ACTIVE_BG = "#D6EBFF"       # Background when selected
#     ACTIVE_FG = "#005A9E"       # Foreground when selected
#     HOVER_BG = "#E0E0E0"        # Background on hover (normal)
#     ACTIVE_HOVER_BG = "#C8E6FF" # Background on hover (selected)

#     # --- Configure Styles ---
    
#     style.configure("FindWidget.TFrame", background=BG_COLOR)

#     style.configure(
#         "FindWidget.TEntry",
#         fieldbackground=ENTRY_BG,
#         bordercolor=BORDER_COLOR,
#         lightcolor=BORDER_COLOR,
#         darkcolor=BORDER_COLOR,
#         borderwidth=0,
#         bd=0,
#         font=("Segoe UI", 120),
#     )
#     style.map("FindWidget.TEntry",
#         bordercolor=[('focus', ACTIVE_FG)]
#     )

#     # --- Define the Toggle Button Styles ---

#     # 1. Base style (FindWidget.TButton)
#     style.configure(
#         "FindWidget.TButton",
#         background="#E7E7E7",
#         foreground=TOGGLE_FG,
#         borderwidth=1,
#         relief="flat",
#         padding=2,
#         width= 3,
#         font=("Segoe UI", 9)
#     )
#     style.map(
#         "FindWidget.TButton",
#         background=[('active', HOVER_BG)],
#         relief=[('pressed', 'flat'), ('!pressed', 'flat')]
#     )

#     # 2. Selected style (FindWidget.TButton.Selected)
#     #    First, create the new style layout by copying the TButton layout
#     try:
#         style.layout("FindWidget.TButton.Selected", style.layout("TButton"))
#     except tk.TclError:
#         print("Error creating style layout. This can happen on some systems.")
        
#     #    Now, configure the colors for the new "Selected" style
#     style.configure(
#         "FindWidget.TButton.Selected",
#         background=ACTIVE_BG,
#         foreground=ACTIVE_FG,
#         borderwidth=1,
#         relief="flat",
#         padding=2,
#         width= 3,
#         font=("Segoe UI", 9)
#     )
#     style.map(
#         "FindWidget.TButton.Selected",
#         background=[('active', ACTIVE_HOVER_BG)],
#         relief=[('pressed', 'flat'), ('!pressed', 'flat')]
#     )






def setup_styles() -> None:
    style = ttk.Style()
    style.theme_use("clam")
    
    # Style from FindWidget Class
    style.configure("FindWidget.TFrame", background="#F3F3F3")
    
    style.configure("FindWidget.TEntry", fieldbackground="#FFFFFF", bordercolor="#CECECE", lightcolor="#CECECE", darkcolor="#CECECE", borderwidth=1, font=("Segoe UI", 11))
    style.map("FindWidget.TEntry", 
              bordercolor=[('focus', "#005A9E")]
    )
    
    style.configure("FindWidget.TButton", background="#E7E7E7", foreground="#666666", borderwidth=1, relief="flat", padding=2, width=3, font=("Segoe UI", 9))
    style.map("FindWidget.TButton", 
              background=[('active', "#E0E0E0")], 
              relief=[('pressed', 'flat'), ('!pressed', 'flat')]
    )
    
    style.layout("FindWidget.TButton.Selected", style.layout("TButton"))
    style.configure("FindWidget.TButton.Selected", background="#D6EBFF", foreground="#005A9E", borderwidth=1, relief="flat", padding=2, width=3, font=("Segoe UI", 9))
    style.map("FindWidget.TButton.Selected", background=[('active', "#C8E6FF")], relief=[('pressed', 'flat'), ('!pressed', 'flat')])


if __name__ == "__main__":

    root = tk.Tk()
    root.title("Find Widget Demo (Using ttk.Button)")
    root.geometry("700x500")

    # --- 1. Setup Styles ---
    setup_styles()
    root.configure(background="#F3F3F3")

    # --- 2. Define the callback function ---
    def on_find_change(state: Dict[str, Any]):
        """This function is passed to the widget and gets called on any change."""
        print("Find widget state changed:")
        print(f"  Text:   {state['text']}")
        print(f"  Case:   {state['CA']}")
        print(f"  Word:   {state['MW']}")
        print(f"  RegEx:  {state['RegEx']}")
        print("-" * 20)
        
        status_label.config(text=f"Current State: {state}")


    find_frame = FindWidget(root, on_change_callback=on_find_change)
    find_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(5,0))

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # --- 4. Create other widgets for demonstration ---
    status_label = ttk.Label(
        root, 
        text="Current State: (No changes yet)",
        anchor="w",
        style="FindWidget.TFrame"
    )
    status_label.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
    
    text_widget = tk.Text(
        root, 
        wrap=tk.WORD, 
        font=("Consolas", 11),
        background="#FFFFFF",
        borderwidth=1,
        relief="solid",
        highlightthickness=0,
        fg="#333333"
    )
    text_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
    text_widget.insert(tk.END, "This version uses ttk.Button widgets.\n\n")
    text_widget.insert(tk.END, "Clicking them toggles their BooleanVar, which triggers "
                               "a trace. The trace updates the button's style and "
                               "fires the main callback.")

    root.mainloop()