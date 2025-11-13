import tkinter as tk
from tkinter import ttk
from typing import Any, List

try:
    from layouts.violation_viewer_layout import ViolationViewerLayoutFrame
    from views.violation_table import ViolationTable
    from widgets.checkbox import ColoredCheckBox
    from widgets.macro_info import MacroNameDisplayFrame
    from widgets.macro_meta_data import MacroMetaDataFrame
except:
    from ..layouts.violation_viewer_layout import ViolationViewerLayoutFrame
    from violation_table import ViolationTable
    from ..widgets.checkbox import ColoredCheckBox
    from ..widgets.macro_meta_data import MacroMetaDataFrame



LOG_LEVELS = {
    "Error": {"color": "#FF4136", "default": True},
    "Warning": {"color": "#FF851B", "default": True},
    "Fatal": {"color": "#B10DC9", "default": False},
}
        
        
        
class ViolationViewerHeaderFrame(ttk.Frame):
    def __init__(self, master: ttk.Frame, **kwargs: Any) -> None:
        super().__init__(master, style="TFrame", **kwargs)
        self.master = master

        self._init_layout()

    def _init_layout(self):
        self.macro_name_frame = MacroNameDisplayFrame( self.master, macro_data=None, tooltip_align="bottom-left"  )
        self.macro_name_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)


    
        # self.severtiy_filter_cb = ColoredCheckBox(
        #     parent=self.master,
        #     options_data=LOG_LEVELS,
        #     on_change_callback=self.print_selection_handler,
        # )
        # self.severtiy_filter_cb.pack(side=tk.LEFT)

    def print_selection_handler(self, selected_list: List[str]) -> None:
        """Callback function to print the new selection."""
        print("--- Selected Items ---")
        if not selected_list:
            print("None")
        else:
            for item in selected_list:
                print(f"- {item}")
        print("------------------------\n")


class ViolationViewer:
    def __init__(self, master):
        violation_viewr_layout = ViolationViewerLayoutFrame(master)
        violation_viewr_layout.pack(expand=True, fill=tk.BOTH)

        table_header = ViolationViewerHeaderFrame(
            violation_viewr_layout.table_top_frame
        )
        table_header.pack(expand=True, fill=tk.X)

        self.violation_table = ViolationTable(violation_viewr_layout)
        
        self.meta_data_frame = ttk.Frame(master, padding=5, style="MacroMetaDataFrame.TFrame")
        self.meta_data_frame.pack(fill="x", anchor="n")
        self.macro_meta_data = MacroMetaDataFrame(self.meta_data_frame, data=None , style="MacroMetaDataFrame.TFrame")
        self.macro_meta_data.pack(fill="x", anchor="n")

    #-----------------------------
    def callback_file_open(self, path: str):
        print(f"[ViolationViewer]: {path}")
        self.violation_table.callback_file_open(path)
        
        
        
        
        

def setup_styles() -> None:
    """Configures all custom ttk styles for the application."""
    style = ttk.Style()
    style.theme_use("clam")

    style.configure("ViolationViewerLayoutFrame.TFrame", background="#f5f5f5")
    style.configure(
        "Section.TFrame", background="#f9f9f9", borderwidth=1, relief="solid"
    )
    style.configure("Toolbar.TFrame", background="#e6e6e6")
    style.configure("TLabel", background="#f9f9f9")

    style.configure("ViolationDetails.TButton", padding=6)
    style.map(
        "ViolationDetails.TButton",
        background=[("active", "#d9d9d9")],
        relief=[("pressed", "sunken"), ("!pressed", "raised")],
    )


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Violation Viewer Demo")
    root.geometry("1000x600")

    # Set up the styles first
    setup_styles()

    # Create and pack the main widget
    ViolationViewer(root)

    root.mainloop()
