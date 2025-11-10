




from tkinter import *
from tkinter import ttk







root  = Tk()
style = ttk.Style()
style.configure("test.TFrame",background="#f9f9f9", borderwidth=1, relief="solid")

a = ttk.Frame(root, style="test.TFrame", height=200, width=300, padding=(1, 1))
a.pack(expand=True, fill=X)

ttk.Button(a, width= 20).pack(expand=True, fill=X)


root.geometry("800x800")
root.mainloop()