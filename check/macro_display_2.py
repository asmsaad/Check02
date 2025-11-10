import tkinter as tk

class HighlightedLabel:
    def __init__(self, parent, full_text, highlight_var):
        self.parent = parent
        self.full_text = full_text
        self.highlight_var = highlight_var
        
        # Create a Text widget
        self.text_widget = tk.Text(parent, height=1, width=30, font=("Arial", 12), 
                                  relief="flat", borderwidth=0, background=parent.cget('background'))
        self.text_widget.pack(pady=20)
        
        # Configure tag for highlighting
        self.text_widget.tag_configure("highlight", background="red")
        
        # Make it read-only like a label
        self.text_widget.config(state="disabled")
        
        # Trace the variable for changes
        self.highlight_var.trace_add("write", self.update_highlight)
        
        # Initial update
        self.update_highlight()
    
    def update_highlight(self, *args):
        # Enable widget to update text
        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", self.full_text)
        
        # Remove all existing tags
        self.text_widget.tag_remove("highlight", "1.0", "end")
        
        # Apply new highlight
        highlight_text = self.highlight_var.get()
        if highlight_text and highlight_text in self.full_text:
            start_index = self.full_text.find(highlight_text)
            end_index = start_index + len(highlight_text)
            self.text_widget.tag_add("highlight", f"1.{start_index}", f"1.{end_index}")
        
        # Make it read-only again
        self.text_widget.config(state="disabled")

# Usage
root = tk.Tk()

# Create a StringVar for the highlight text
highlight_var = tk.StringVar(value="i")

# Create the label
label = HighlightedLabel(root, "Walking", highlight_var)

# # Example: Change highlight text after 3 seconds
# def change_highlight():
#     highlight_var.set("alk")  # This will automatically update the label

# root.after(3000, change_highlight)

root.mainloop()