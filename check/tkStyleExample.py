import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.geometry("300x200")
root.title("Styling a Button")

style = ttk.Style()

# 1. Define our new style, inheriting from TButton
# We use the options we found with the script:
# - 'background' and 'foreground' (from Button.label)
# - 'borderwidth' (from Button.border)
# - 'padding' (from Button.padding)
style.configure(
    "MyCustom.TButton",
    background="#0078D4",  # Blue background
    foreground="white",    # White text
    borderwidth=1,
    relief="solid",
    padding=10
)

# 2. We can also define a map for hover effects
# 'activebackground' is a valid option on Button.label
style.map(
    "MyCustom.TButton",
    background=[('active', '#005A9E')]  # Darker blue on hover/press
)


# 3. Create a default button for comparison
default_button = ttk.Button(root, text="Default (TButton)")
default_button.pack(pady=10)

# 4. Create our new button using the custom style
custom_button = ttk.Button(
    root, 
    text="Custom (MyCustom.TButton)",
    style="MyCustom.TButton"
)
custom_button.pack(pady=10)


root.mainloop()