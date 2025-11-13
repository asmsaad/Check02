import tkinter as tk
from tkinter import ttk
from typing import Literal


class TableHeaderMenu(tk.Menu):
    def __init__(self, master=None, menu_items=None, *args, **kargs):
        super().__init__(master, *args, **kargs)
        self.active_text = None

        if menu_items:
            self.build_menu(menu_items)

    def build_menu(self, items):
        """Dynamically builds menu from a list of dicts and strings."""
        for item in items:
            if isinstance(item, dict):
                # This is a menu item
                name = item.get("menu_name")
                callback = item.get("on_call")

                if name and callback:
                    # Use a lambda to wrap the callback.
                    # This wrapper calls our intermediate function,
                    # which in turn calls the *user's* function.
                    self.add_command(
                        label=name,
                        command=lambda cb=callback: self.execute_callback(cb),
                    )
            elif isinstance(item, str) and item.lower() == "separator":
                # This is a separator
                self.add_separator()

    def execute_callback(self, user_callback_func):
        """
        This is the crucial step. It calls the user's function
        (e.g., on_cut) and passes it the stored active_text.
        """
        if self.active_text:
            user_callback_func(self.active_text)



MenuPosition = Literal[
    "bottom_left", "bottom_right", "bottom_middle",
    "left", "right", 
    "top_left", "top_right", "top_middle"
]
def show_menu(event, menu, raw_text, position: MenuPosition = "bottom_left"):
    # Updated to accept 'raw_text' as an argument
    widget = event.widget
    
    # Store the passed-in raw text
    menu.active_text = raw_text

    x = widget.winfo_rootx()
    y = widget.winfo_rooty()
    widget_height = widget.winfo_height()

    menu_x = x
    menu_y = y + widget_height

    try:
        menu.post(menu_x, menu_y)
    finally:
        menu.grab_release()


if __name__ == "__main__":
    root = tk.Tk()

    def on_cut(text):
        print(f"Cut clicked by {text}")

    def on_copy(text):
        print(f"Copy clicked by {text}")

    def on_peast(text):
        print(f"Peast clicked by {text}")

    def on_delete(text):
        print(f"Delete clicked by {text}")

    menu_item_list = [
        {"menu_name": "Cut", "on_call": on_cut},
        {"menu_name": "Copy", "on_call": on_copy},
        {"menu_name": "Peast", "on_call": on_peast},  # Spelled as requested
        "separator",
        {"menu_name": "Delete", "on_call": on_delete},
    ]

    column_control_menu = TableHeaderMenu(root, menu_items=menu_item_list, tearoff=0)

    a = ttk.Button(root, text="Jom")
    a.pack(pady=5, padx=20)
    a.bind("<Button-3>", lambda e, m=column_control_menu, t="Jom": show_menu(e, m, t))

    b = ttk.Button(root, text="Tom")
    b.pack(pady=5, padx=20)
    b.bind("<Button-3>", lambda e, m=column_control_menu, t="Tom": show_menu(e, m, t))

    root.mainloop()
