
import tkinter as tk
from tkinter import ttk



from bin.layout.violation_viewer import ViolationViewer
from bin.widgets.violation_table import ViolationTable
from bin.widgets.app_menu import AppMenu
from bin.widgets.macro_info import MacroMetaDataFrame





sample_data = {
    'run_by': 'jdoe',
    'host': 'lab-server-12',
    'tool_name': 'MyToolSuite 4.2',
    'version': 'v1.2.345-gHjK',
    'start_time': '10:12:35 10 Oct 2025 (Utc)',
    'duration': '96.95s',
    'checks': {
        'Lef': [1, 0],      
        'Libarty': [0, 15], 
        'Verilog': [1, 100],
        'GDS': [0, 0]       
    },
    'links': {
        'yaml_config': 's3://bucket/config.yaml',
        'repo_link': 'https://git.corp/project/macro',
        'pin_info': None
    }
}


class RuleViewTable:
    def __init__(self, root):
        self.root = root

        style = ttk.Style()
        style.configure("RuleViewTable.TFrame",
                        background = "#FFFFFF",
                        )
        
        self.master = ttk.Frame(self.root, style="RuleViewTable.TFrame")
        self.master.pack(expand=True, fill=tk.BOTH)
        
        # # -------------------------------
        # # Scrollbars
        # # -------------------------------
        # v_scroll = tk.Scrollbar(self.master, orient=tk.VERTICAL)
        # v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # h_scroll = tk.Scrollbar(self.master, orient=tk.HORIZONTAL)
        # h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # -------------------------------
        # Top PanedWindow: Header
        # -------------------------------
        header_pane = ttk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        header_pane.pack(side=tk.TOP, fill=tk.X)
                
        # Frozen Header
        header_left_canvas = tk.Canvas(header_pane, width=150, height=30, bg="lightgray")
        header_left_frame = tk.Frame(header_left_canvas, bg="lightgray")
        header_left_canvas.create_window((0, 0), window=header_left_frame, anchor="nw")
        header_pane.add(header_left_canvas, weight=0)

        # Scrollable Header
        header_right_canvas = tk.Canvas(header_pane, height=30, bg="lightblue")
        header_right_frame = tk.Frame(header_right_canvas, bg="lightblue")
        header_right_canvas.create_window((0, 0), window=header_right_frame, anchor="nw")
        header_pane.add(header_right_canvas, weight=1)
        
        
        
        # -------------------------------
        # Scrollbars
        # -------------------------------
        v_scroll = tk.Scrollbar(self.master, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        
        
        # -------------------------------
        # Bottom PanedWindow: Body
        # -------------------------------
        body_pane = ttk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        body_pane.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Frozen Columns
        body_left_canvas = tk.Canvas(body_pane, width=150, bg="lightgray", yscrollcommand=v_scroll.set)
        body_left_frame = tk.Frame(body_left_canvas, bg="lightgray")
        body_left_canvas.create_window((0, 0), window=body_left_frame, anchor="nw")
        body_pane.add(body_left_canvas, weight=0)

        # Scrollable Columns
        body_right_canvas = tk.Canvas(body_pane, bg="white", yscrollcommand=v_scroll.set)
        body_right_frame = tk.Frame(body_right_canvas, bg="white")
        body_right_canvas.create_window((0, 0), window=body_right_frame, anchor="nw")
        body_pane.add(body_right_canvas, weight=1)
        
        
        
        # -------------------------------
        # Scrollbars
        # -------------------------------
        # v_scroll = tk.Scrollbar(self.master, orient=tk.VERTICAL)
        # v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        h_scroll = tk.Scrollbar(body_right_canvas, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        body_right_canvas.configure( xscrollcommand=h_scroll.set)
        
        
        
        

        
        
        
        # -------------------------------
        # Update scroll regions
        # -------------------------------
        def update_scroll_regions(event=None):
            body_left_canvas.configure(scrollregion=body_left_canvas.bbox("all"))
            body_right_canvas.configure(scrollregion=body_right_canvas.bbox("all"))
            header_right_canvas.configure(scrollregion=header_right_canvas.bbox("all"))

        body_left_frame.bind("<Configure>", update_scroll_regions)
        body_right_frame.bind("<Configure>", update_scroll_regions)
        header_right_frame.bind("<Configure>", update_scroll_regions)

        # -------------------------------
        # Synchronize scrolling
        # -------------------------------
        def on_vertical_scroll(*args):
            body_left_canvas.yview(*args)
            body_right_canvas.yview(*args)

        v_scroll.config(command=on_vertical_scroll)

        def on_horizontal_scroll(*args):
            body_right_canvas.xview(*args)
            header_right_canvas.xview(*args)

        h_scroll.config(command=on_horizontal_scroll)

        # Sync vertical scrolling with mouse wheel
        def _on_mousewheel(event):
            delta = int(-1*(event.delta/120))
            body_left_canvas.yview_scroll(delta, "units")
            body_right_canvas.yview_scroll(delta, "units")
            return "break"





        # -------------------------------
        # Synchronize PanedWindow sash
        # -------------------------------

        def sync_sash_from_header(event=None):
            """Sync body pane sash when header pane is dragged"""
            body_pane.sashpos(0, header_pane.sashpos(0))
            print(header_pane.sashpos(0) , body_pane.sashpos(0))
            # header_pane.update()
            


        def sync_sash_from_body(event=None):
            """Sync header pane sash when body pane is dragged"""
            header_pane.sashpos(0, body_pane.sashpos(0))
            print(header_pane.sashpos(0) , body_pane.sashpos(0))
            # header_pane.update()


        # Bind dragging events
        header_pane.bind("<B1-Motion>", sync_sash_from_header)
        body_pane.bind("<B1-Motion>", sync_sash_from_body)




        body_left_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        body_right_canvas.bind_all("<MouseWheel>", _on_mousewheel)
                



class MainWindow:
    def __init__(self):

        self.root = tk.Tk()

        self.root.title("Pin Check ScoreBoard")
        self.root.geometry("900x700")
        
        
        self.layout()
         
         
        self.root.mainloop()



       
         
    def layout(self):
        self.menu = AppMenu(self.root)
        
        # ttk.Button(self.root, text="Check0").pack()
        # ttk.Button(self.root, text="Check1").pack()
        
        a_frame = ttk.Frame(self.root, padding=(8,8))
        a_frame.pack(expand=True, fill=tk.BOTH)
        
        
        # RuleViewTable(self.root)
        viewer_layout = ViolationViewer(a_frame)
        ViolationTable(viewer_layout)
        
        macro_details_frame = MacroMetaDataFrame(self.root, data=sample_data)
        macro_details_frame.pack(expand=True, fill=tk.X)


        
        # ttk.Button(self.root, text="Check2").pack()
        # ttk.Button(self.root, text="Check3").pack()
        
    
    
    
    
if __name__ == "__main__":
    pass