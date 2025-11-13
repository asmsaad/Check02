import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Dict, Tuple, Any, Literal 




class PinCheckScoreboardStyleTheme(ttk.Style):
    """Sets the foundational 'clam' theme for the application."""
    
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)
        self.theme_use("clam")


class PinCheckScoreboardStyle(PinCheckScoreboardStyleTheme):
    """Applies all custom widget styles for the application."""
    
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)       
        self._configure_all_widgets()

    def _configure_all_widgets(self) -> None:
        # self.configure("TButton", background="orange")
        
        
        # Style From ViolationTable
        self.configure("Tiny.TButton", padding=(3,6))  # (x, y)
        self.configure("ViolationTable.Placeholder.HScroll.TFrame", background="#dcdad5" )  # (x, y)
        
        self.configure( "ViolationTable.PinInfo.Header.TFrame", background="#ffffff", borderwidth=0, relief="solid" )
        self.configure( "ViolationTable.PinInfo.Data.TFrame", background="#ffffff", borderwidth=0, relief="solid" )
        self.configure( "ViolationTable.Rules.Header.TFrame", background="#ffffff", borderwidth=0, relief="solid" )
        self.configure( "ViolationTable.Rules.Status.TFrame", background="#ffffff", borderwidth=0, relief="solid" )
        
        
        self.configure("Violation.Status.Passed.TButton", background="#6BC5A0", foreground="#0E2A20")
        self.configure("Violation.Status.Faield.TButton", background="#FF9E8C", foreground="#3D0E07")
        self.configure("Violation.Status.N/A.TButton", background="#AFC3D6", foreground="#1A242E")

        self.map("Violation.Status.Passed.TButton",
            background=[('disabled', '#DCE0E3'), ('pressed', 'hover', '#28A06E'), ('pressed', '#34B27E'), ('hover', '#5ABF91')],
            foreground=[('disabled', '#A6AFB8'), ('pressed', 'hover', '#E8FFF4'), ('pressed', '#FFFFFF'), ('hover', '#082018')]
        )
        self.map("Violation.Status.Faield.TButton",
            background=[('disabled', '#DCE0E3'), ('pressed', 'hover', '#E74B3C'), ('pressed', '#F35C4A'), ('hover', '#FF8A75')],
            foreground=[('disabled', '#A6AFB8'), ('pressed', 'hover', '#FFF3F1'), ('pressed', '#FFFFFF'), ('hover', '#2A0A05')]
        )
        self.map("Violation.Status.N/A.TButton",
            background=[('disabled', '#DCE0E3'), ('pressed', 'hover', '#6C88A1'), ('pressed', '#7E9AB3'), ('hover', '#A2B8CD')],
            foreground=[('disabled', '#A6AFB8'), ('pressed', 'hover', '#F0F6FA'), ('pressed', '#FFFFFF'), ('hover', '#141E26')]
        )
        
        
        #Style for ColumnFilter Class
        self.configure("CollumnFilter.Content.TFrame", background="#ffffff")
        self.configure("CollumnFilter.Filter.TFrame", background="#e0e0e0")   
        self.configure("CollumnFilter.Content.TCheckbutton", background="#ffffff")
        self.configure( "CollumnFilter.TLabelframe.Label", background="#e0e0e0", font=("Helvetica", 10, "bold") )
        
        
        #Style for MacroMetaDataFrame
        self.configure("MacroMetaDataFrame.TFrame", background="#e0e0e0")
        self.configure("MacroMetaDataFrame.TLabel", background="#e0e0e0")
        self.configure( "MacroMetaDataFrame.InputFile.TFrame", background="#ebebeb", borderwidth=0)
        self.configure("MacroMetaDataFrame.InputFile.TLabel", background="#ebebeb")
        
        # Style from FindWidget Class
        self.configure("FindWidget.TFrame", background="#F3F3F3")
        
        self.configure("FindWidget.TEntry", fieldbackground="#FFFFFF", bordercolor="#CECECE", lightcolor="#CECECE", darkcolor="#CECECE", borderwidth=1, font=("Segoe UI", 11))
        self.map("FindWidget.TEntry", 
                bordercolor=[('focus', "#005A9E")]
        )
        
        self.configure("FindWidget.TButton", background="#E7E7E7", foreground="#666666", borderwidth=1, relief="flat", padding=2, width=3, font=("Segoe UI", 9))
        self.map("FindWidget.TButton", 
                background=[('active', "#E0E0E0")], 
                relief=[('pressed', 'flat'), ('!pressed', 'flat')]
        )
        
        self.layout("FindWidget.TButton.Selected", self.layout("TButton"))
        self.configure("FindWidget.TButton.Selected", background="#D6EBFF", foreground="#005A9E", borderwidth=1, relief="flat", padding=2, width=3, font=("Segoe UI", 9))
        self.map("FindWidget.TButton.Selected", background=[('active', "#C8E6FF")], relief=[('pressed', 'flat'), ('!pressed', 'flat')])

        
        
        
        
        

        
        
        
