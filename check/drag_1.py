
# This code allows you to make resizable sections smoothly.

import tkinter as tk
from tkinter import ttk


class PanedWindowView:
    def __init__(self,root):
        self.root = root
        
    
        # Create PanedWindow with horizontal orientation
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create three resizable sections
        frame1 = ttk.Frame(self.paned, relief="sunken", borderwidth=2)
        frame2 = ttk.Frame(self.paned, relief="sunken", borderwidth=2)  
        frame3 = ttk.Frame(self.paned, relief="sunken", borderwidth=2)
        frame4 = ttk.Frame(self.paned, relief="sunken", borderwidth=2)

        # Add some content to visualize each section
        ttk.Label(frame1, text="Section 1", anchor="center", background="#e8f4fd").pack(fill="x", pady=0)
        ttk.Label(frame2, text="Section 2", anchor="center", background="#f0f8f0").pack(fill="x", pady=0)
        ttk.Label(frame3, text="Section 3", anchor="center", background="#fef8e8").pack(fill="x", pady=0)
        ttk.Label(frame4, text="Section 4", anchor="center", background="#fea0e8").pack(fill="x", pady=0)

        # Add frames to PanedWindow
        self.paned.add(frame1, weight=1)
        self.paned.add(frame2, weight=1)
        self.paned.add(frame3, weight=1)
        self.paned.add(frame4, weight=1)

        # # Set initial sash positions (30%, 30%, 40%)
        self.root.update()
        width = self.paned.winfo_width()
        if width > 0:
            self.paned.sashpos(0, int(width * 0.20))
            self.paned.sashpos(1, int(width * 0.40))
            self.paned.sashpos(2, int(width * 0.60))
            
            
        # Add this binding after creating the self.paned window
        # self.paned.bind("<B1-Motion>", self.on_sash_drag)
    
    
    
    # def on_sash_drag(self,event):
    #     # Check all sash positions to ensure no frame is below 200px
    #     self.paned = event.widget
    #     width = self.paned.winfo_width()
        
    #     # Minimum positions for each sash to maintain 200px per frame
    #     min_sash1 = 200
    #     min_sash2 = 400
    #     min_sash3 = 600
        
    #     # Maximum positions for each sash to maintain 200px per frame
    #     max_sash1 = width - 600
    #     max_sash2 = width - 400
    #     max_sash3 = width - 200
        
    #     # Get current sash positions
    #     try:
    #         sash1 = self.paned.sashpos(0)
    #         sash2 = self.paned.sashpos(1)
    #         sash3 = self.paned.sashpos(2)
            
    #         # Constrain sash positions
    #         if sash1 < min_sash1:
    #             self.paned.sashpos(0, min_sash1)
    #         elif sash1 > max_sash1:
    #             self.paned.sashpos(0, max_sash1)
                
    #         if sash2 < min_sash2:
    #             self.paned.sashpos(1, min_sash2)
    #         elif sash2 > max_sash2:
    #             self.paned.sashpos(1, max_sash2)
                
    #         if sash3 < min_sash3:
    #             self.paned.sashpos(2, min_sash3)
    #         elif sash3 > max_sash3:
    #             self.paned.sashpos(2, max_sash3)
                
    #     except:
    #         pass




    

if __name__ == "__main__":
    # Create main window
    root = tk.Tk()
    PanedWindowView(root)
    root.title("Built-in Resizable Panes")
    root.geometry("600x300")
    root.mainloop()