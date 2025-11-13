import tkinter as tk
from tkinter import ttk
from app import PinCheckScoreBoard



def setup_styles() -> None:
    """Configures all custom ttk styles for the application."""
    style = ttk.Style()
    style.theme_use("clam")

    # style.configure("ViolationViewerLayoutFrame.TFrame", background="#f5f5f5")
    # style.configure(
    #     "Section.TFrame", background="#f9f9f9", borderwidth=1, relief="solid"
    # )
    # style.configure("Toolbar.TFrame", background="#e6e6e6")
    # style.configure("TLabel", background="#f9f9f9")

    # style.configure("ViolationDetails.TButton", padding=6)
    # style.map(
    #     "ViolationDetails.TButton",
    #     background=[("active", "#d9d9d9")],
    #     relief=[("pressed", "sunken"), ("!pressed", "raised")],
    # )



if __name__ == "__main__":
    app = PinCheckScoreBoard()
    setup_styles()
    app.mainloop()