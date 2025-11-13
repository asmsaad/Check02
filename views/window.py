import tkinter as tk
import os
from typing import Optional, Union, Literal


class WindowConfiguration:
    """
    A helper class to configure a tk.Tk or tk.Toplevel window.
    Applies settings to a provided window instance.
    """

    def __init__(self, window: Union[tk.Tk, tk.Toplevel]):
        self.window = window

    def geometry(
        self, width: int = 500, height: int = 500, align: Literal["center"] = "center"
    ) -> None:
        if align == "center":
            self.center_window(width=width, height=height)

    def center_window(self, width: int, height: int) -> None:
        self.window.update_idletasks()  # Force update to get accurate screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def resizeable(self, width: bool = True, height: bool = True) -> None:
        self.window.resizable(width, height)

    def title(self, title: str) -> None:
        self.window.title(title)

    def set_app_icon(self, image: tk.PhotoImage) -> None:
        """
        Sets the app icon for this window and all future Toplevels.

        Note: The calling code must hold a reference to the PhotoImage
        to prevent it from being garbage collected.
        """
        self.window.iconphoto(
            True, image
        )  # True = set icon for this window and all future Toplevels

    def set_topmost(self, is_topmost: bool = True):
        """Forces the window to stay on top of all others."""
        self.window.wm_attributes("-topmost", 1 if is_topmost else 0)


if __name__ == "__main__":

    root = tk.Tk()
    root.withdraw()

    config = WindowConfiguration(root)
    config.title("My Configured App")
    config.resizeable(False, False)
    app_icon: Optional[tk.PhotoImage] = None
    ICON_FILE = "temp_icon.png"   
    app_icon = tk.PhotoImage(file=ICON_FILE)
    config.set_app_icon(app_icon)
    
    root.deiconify()
    root.mainloop()
