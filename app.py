import tkinter as tk
from tkinter import ttk
from styles.styles import PinCheckScoreboardStyle
from views.main_menu import PinCheckScoreboardAppMenu
from views.window import WindowConfiguration
from views.violation_viewer import ViolationViewer
from assets.assets import *



class PinCheckScoreBoard(tk.Tk):
    def __init__(self):
        super().__init__()

        PinCheckScoreboardStyle(self)

        self._window_config()
        self._app_menu_handel()
        self._init_layout()

    def _app_menu_handel(self):
        app_menu = PinCheckScoreboardAppMenu(
            master=self, callbacks={}, initial_history=[]
        )
        self.config(menu=app_menu)  # Attach the menu to the root window
        app_menu.bind_global_accelerators()  # Call the binding method
        
    def _init_layout(self):
        vailation_viewer = ViolationViewer(self)
        

    def _window_config(self):
        app_icon = tk.PhotoImage(file=APP_ASSETS.icon.heatmap32x32)
        window_config = WindowConfiguration(self)
        window_config.title("Pin Check Scoreboard")
        window_config.geometry(align="center", width=1000, height=800)
        window_config.set_app_icon(app_icon)
        
        



if __name__ == "__main__":
    app = PinCheckScoreBoard()
    app.mainloop()
