import tkinter as tk
from tkinter import ttk
from pygments import lex
from pygments.lexers import get_lexer_by_name, get_all_lexers
from pygments.styles import get_all_styles, get_style_by_name


class SyntaxHighlightingTextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Syntax Highlighting Editor")
        self.root.geometry("800x600")

        # Configure grid weights for proper resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        # Get available lexers and styles
        self.lexers = self.get_available_lexers()
        self.styles = list(get_all_styles())
        self.bg_colors = {
            "Dark": "#1E1E1E",
            "Light": "#FFFFFF",
            "Solarized Dark": "#002B36",
            "Solarized Light": "#FDF6E3",
            "Monokai": "#272822",
            "GitHub": "#FFFFFF",
            "Blue": "#1E3A5F",
            "Gray": "#2D2D2D",
        }

        self.current_lexer = get_lexer_by_name("python")
        self.current_style = "monokai"
        self.current_bg_color = "#1E1E1E"

        self.setup_ui()
        self.apply_theme()

    def get_available_lexers(self):
        """Get all available lexers from Pygments"""
        lexers = []
        for lexer in get_all_lexers():
            # Use the first name as the display name
            lexers.append(lexer[0])
        return sorted(lexers)

    def setup_ui(self):
        """Setup the UI elements: dropdowns and text area"""

        # Control frame for dropdowns
        control_frame = ttk.Frame(self.root)
        control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)

        # 1. Language selection dropdown
        ttk.Label(control_frame, text="Language:").grid(
            row=0, column=0, sticky="w", padx=(0, 5)
        )
        self.language_var = tk.StringVar(value="Python")
        self.language_combo = ttk.Combobox(
            control_frame,
            textvariable=self.language_var,
            values=self.lexers,
            state="readonly",
            width=20,
        )
        self.language_combo.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self.language_combo.bind("<<ComboboxSelected>>", self.on_language_change)

        # 2. Theme selection dropdown
        ttk.Label(control_frame, text="Theme:").grid(
            row=0, column=1, sticky="w", padx=(0, 5)
        )
        self.theme_var = tk.StringVar(value="monokai")
        self.theme_combo = ttk.Combobox(
            control_frame,
            textvariable=self.theme_var,
            values=self.styles,
            state="readonly",
            width=20,
        )
        self.theme_combo.grid(row=1, column=1, sticky="ew")
        self.theme_combo.bind("<<ComboboxSelected>>", self.on_theme_change)

        # 3. Background color dropdown
        bg_control_frame = ttk.Frame(self.root)
        bg_control_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        bg_control_frame.columnconfigure(0, weight=1)

        ttk.Label(bg_control_frame, text="Background:").grid(
            row=0, column=0, sticky="w"
        )
        self.bg_color_var = tk.StringVar(value="Dark")
        self.bg_color_combo = ttk.Combobox(
            bg_control_frame,
            textvariable=self.bg_color_var,
            values=list(self.bg_colors.keys()),
            state="readonly",
            width=20,
        )
        self.bg_color_combo.grid(row=1, column=0, sticky="ew")
        self.bg_color_combo.bind("<<ComboboxSelected>>", self.on_bg_color_change)

        # 4. Text editor area with syntax highlighting
        self.text_area = tk.Text(
            self.root,
            wrap=tk.WORD,
            font=("Courier New", 12),
            undo=True,
            maxundo=-1,
            selectbackground="#4A4A4A",
            insertbackground="#FFFFFF",
            borderwidth=2,
            relief="sunken",
        )
        self.text_area.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Configure default tags first
        self.setup_default_tags()

        # Bind events for real-time syntax highlighting
        self.text_area.bind("<KeyRelease>", self.on_text_change)

        # Add some sample code
        self.insert_sample_code()
        self.highlight_syntax()

    def setup_default_tags(self):
        """Setup default text tags for syntax highlighting"""
        # Clear existing tags
        for tag in self.text_area.tag_names():
            self.text_area.tag_delete(tag)

        # Default dark theme tags
        default_tags = {
            "Token.Comment": {"foreground": "#6A9955"},
            "Token.Keyword": {
                "foreground": "#C586C0",
                "font": ("Courier New", 12, "bold"),
            },
            "Token.Keyword.Constant": {
                "foreground": "#C586C0",
                "font": ("Courier New", 12, "bold"),
            },
            "Token.Keyword.Declaration": {
                "foreground": "#C586C0",
                "font": ("Courier New", 12, "bold"),
            },
            "Token.Keyword.Namespace": {
                "foreground": "#C586C0",
                "font": ("Courier New", 12, "bold"),
            },
            "Token.Keyword.Pseudo": {
                "foreground": "#C586C0",
                "font": ("Courier New", 12, "bold"),
            },
            "Token.Keyword.Reserved": {
                "foreground": "#C586C0",
                "font": ("Courier New", 12, "bold"),
            },
            "Token.Keyword.Type": {
                "foreground": "#4EC9B0",
                "font": ("Courier New", 12, "bold"),
            },
            "Token.String": {"foreground": "#CE9178"},
            "Token.String.Single": {"foreground": "#CE9178"},
            "Token.String.Double": {"foreground": "#CE9178"},
            "Token.String.Escape": {"foreground": "#D7BA7D"},
            "Token.Name": {"foreground": "#9CDCFE"},
            "Token.Name.Builtin": {"foreground": "#4EC9B0"},
            "Token.Name.Function": {"foreground": "#DCDCAA"},
            "Token.Name.Class": {"foreground": "#4EC9B0"},
            "Token.Name.Decorator": {"foreground": "#DCDCAA"},
            "Token.Name.Namespace": {"foreground": "#4EC9B0"},
            "Token.Name.Exception": {"foreground": "#4EC9B0"},
            "Token.Number": {"foreground": "#B5CEA8"},
            "Token.Number.Integer": {"foreground": "#B5CEA8"},
            "Token.Number.Float": {"foreground": "#B5CEA8"},
            "Token.Number.Hex": {"foreground": "#B5CEA8"},
            "Token.Operator": {"foreground": "#D4D4D4"},
            "Token.Operator.Word": {
                "foreground": "#C586C0",
                "font": ("Courier New", 12, "bold"),
            },
            "Token.Punctuation": {"foreground": "#D4D4D4"},
            "Token.Generic": {"foreground": "#D4D4D4"},
            "Token.Generic.Deleted": {"foreground": "#F44747"},
            "Token.Generic.Emph": {"font": ("Courier New", 12, "italic")},
            "Token.Generic.Error": {"foreground": "#F44747"},
            "Token.Generic.Heading": {
                "foreground": "#000080",
                "font": ("Courier New", 12, "bold"),
            },
            "Token.Generic.Inserted": {"foreground": "#608B4E"},
            "Token.Generic.Output": {"foreground": "#808080"},
            "Token.Generic.Prompt": {"foreground": "#808080"},
            "Token.Generic.Strong": {"font": ("Courier New", 12, "bold")},
            "Token.Generic.Subheading": {
                "foreground": "#800000",
                "font": ("Courier New", 12, "bold"),
            },
            "Token.Generic.Traceback": {"foreground": "#F44747"},
        }

        for tag_name, style in default_tags.items():
            self.text_area.tag_configure(tag_name, **style)

    def apply_theme(self):
        """Apply the current theme to the text area"""
        try:
            # Set background color
            self.text_area.configure(
                bg=self.current_bg_color,
                fg=self.get_foreground_color(),
                insertbackground=self.get_foreground_color(),
            )

            # Apply Pygments theme if available
            self.apply_pygments_theme()

        except Exception as e:
            print(f"Theme application error: {e}")
            # Fallback to default theme
            self.setup_default_tags()

    def get_foreground_color(self):
        """Get appropriate foreground color based on background"""
        dark_backgrounds = ["Dark", "Solarized Dark", "Monokai", "Blue", "Gray"]
        if self.bg_color_var.get() in dark_backgrounds:
            return "#FFFFFF"
        else:
            return "#000000"

    # def apply_pygments_theme(self):
    #     """Apply Pygments theme colors"""
    #     try:
    #         style = get_style_by_name(self.current_style)

    #         # Map Pygments style to our tags
    #         for token_type, style_def in style.styles.items():
    #             tag_name = str(token_type)
    #             config = {}

    #             if style_def:
    #                 # Handle color
    #                 if hasattr(style_def, "color") and style_def.color:
    #                     config["foreground"] = f"#{style_def.color:06x}"

    #                 # Handle bold and italic
    #                 font_elements = []
    #                 if style_def["bold"]:
    #                     font_elements.append("bold")
    #                 if style_def["italic"]:
    #                     font_elements.append("italic")

    #                 if font_elements:
    #                     config["font"] = ("Courier New", 12, " ".join(font_elements))
    #                 else:
    #                     config["font"] = ("Courier New", 12)

    #                 # Apply the configuration
    #                 self.text_area.tag_configure(tag_name, **config)

    #     except Exception as e:
    #         print(f"Pygments theme error: {e}")
    #         # Continue with default tags
    def apply_pygments_theme(self):
        """Apply Pygments theme colors"""
        try:
            style = get_style_by_name(self.current_style)

            # Each style entry is a string like "bold #ff0000 bg:#000000 italic"
            for token_type, style_def in style.styles.items():
                tag_name = str(token_type)
                config = {}

                if style_def:  # Only process non-empty styles
                    # Split style string into attributes
                    parts = style_def.split()
                    fg_color = None
                    bg_color = None
                    font_elements = []

                    for part in parts:
                        if part.startswith('bg:'):
                            # bg_color = f"#{part[3:]}"
                            bg_color = f"{part[3:]}"
                        elif part.startswith('#'):
                            fg_color = part
                        elif part.lower() in ('bold', 'italic', 'underline'):
                            font_elements.append(part.lower())

                    # Apply foreground color
                    if fg_color:
                        config['foreground'] = fg_color

                    # Apply background color if needed
                    if bg_color:
                        config['background'] = bg_color
                    # print("------------->",bg_color)

                    # Build font tuple
                    font_style = ' '.join(font_elements) if font_elements else ''
                    config['font'] = ('Courier New', 12, font_style)

                    # Apply the configuration to the tag
                    self.text_area.tag_configure(tag_name, **config)

        except Exception as e:
            print(f"Pygments theme error: {e}")
            # Continue with default tags if theme parsing fails
            self.setup_default_tags()
            self.update_background_from_theme(style)


    def update_background_from_theme(self, style):
        """Update background color based on the current theme."""
        try:
            theme_bg = getattr(style, 'background_color', None)
            if theme_bg:
                # Update Tkinter text widget
                self.text_area.configure(bg=theme_bg)

                # Prevent triggering the background dropdown event
                self.bg_color_combo.unbind('<<ComboboxSelected>>')
                self.bg_color_var.set(f"Theme: {self.current_style.title()}")
                self.bg_color_combo.bind('<<ComboboxSelected>>', self.on_bg_color_change)

                # Update the internal current_bg_color
                self.current_bg_color = theme_bg
        except Exception as e:
            print(f"Theme background update error: {e}")


    def on_language_change(self, event):
        """Handle language selection change"""
        selected_language = self.language_var.get()
        try:
            self.current_lexer = get_lexer_by_name(selected_language.lower())
            self.highlight_syntax()
        except Exception as e:
            print(f"Language error: {e}")
            # Fallback to plain text if lexer not found
            self.current_lexer = get_lexer_by_name("text")

    def on_theme_change(self, event):
        """Handle theme selection change"""
        self.current_style = self.theme_var.get().lower()
        print(f"Applying theme: {self.current_style}")  # Debug
        self.apply_theme()
        self.highlight_syntax()

    def on_bg_color_change(self, event):
        """Handle background color change"""
        selected_bg = self.bg_color_var.get()
        self.current_bg_color = self.bg_colors.get(selected_bg, "#1E1E1E")
        print(
            f"Changing background to: {selected_bg} -> {self.current_bg_color}"
        )  # Debug
        self.apply_theme()
        self.highlight_syntax()

    def on_text_change(self, event):
        """Handle text changes for real-time syntax highlighting"""
        if event.keysym not in [
            "Shift_L",
            "Shift_R",
            "Control_L",
            "Control_R",
            "Alt_L",
            "Alt_R",
        ]:
            self.highlight_syntax()

    def highlight_syntax(self):
        """Apply syntax highlighting to the entire text"""
        # Get all text content
        content = self.text_area.get("1.0", tk.END)

        if not content.strip():
            return

        # Remove all existing tags
        for tag in self.text_area.tag_names():
            if tag.startswith("Token."):
                self.text_area.tag_remove(tag, "1.0", tk.END)

        try:
            # Tokenize the content
            tokens = lex(content, self.current_lexer)

            # Apply highlighting
            start_index = "1.0"
            for token_type, token_value in tokens:
                if token_value:  # Process all tokens including whitespace
                    end_index = self.text_area.index(
                        f"{start_index}+{len(token_value)}c"
                    )

                    # Use the full token type name for tagging
                    tag_name = str(token_type)

                    # Apply the tag if it exists in our configured tags
                    if tag_name in self.text_area.tag_names():
                        self.text_area.tag_add(tag_name, start_index, end_index)

                # Move start index forward
                start_index = self.text_area.index(f"{start_index}+{len(token_value)}c")

        except Exception as e:
            print(f"Highlighting error: {e}")
            # Silently handle highlighting errors

    def insert_sample_code(self):
        """Insert sample code based on selected language"""
        sample_code = '''# Python Sample Code
def fibonacci(n):
    """Calculate fibonacci sequence"""
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

class MathOperations:
    def __init__(self):
        self.result = 0
    
    def add(self, x, y):
        self.result = x + y
        return self.result

# Main execution
if __name__ == "__main__":
    math = MathOperations()
    print(f"Fibonacci of 10: {fibonacci(10)}")
    print(f"Addition: {math.add(5, 3)}")'''

        self.text_area.insert("1.0", sample_code)


def main():
    root = tk.Tk()
    app = SyntaxHighlightingTextEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
