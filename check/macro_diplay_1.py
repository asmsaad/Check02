import tkinter as tk
from tkinter import ttk
import random






class HighlightedLabel:
    def __init__(self, parent, full_text, highlight_var=None):
        self.parent = parent
        self.full_text = full_text
        self.highlight_var = highlight_var 
        
        # Create a Text widget
        self.text_widget = tk.Text(parent, height=1, width=30, font=("Arial", 12), 
                                  relief="flat", borderwidth=0, background=parent.cget('background'))
        self.text_widget.pack(fill=tk.X, expand=True)
        
        # Configure tag for highlighting
        self.text_widget.tag_configure("highlight", background="red")
        
        # Make it read-only like a label
        self.text_widget.config(state="disabled")
        
        # Trace the variable for changes
        # self.highlight_var.trace_add("write", self.update_highlight) #!
        
        # Initial update
        # self.update_highlight() #!
    
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
        
        
        

class TaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Manager")
        self.root.geometry("800x500")
        
        # Sample tasks
        self.tasks = [
            "Jogging", "Walking", "Running", "Swimming", "Cycling",
            "Reading", "Writing", "Coding", "Drawing", "Painting",
            "Cooking", "Cleaning", "Shopping", "Gardening", "Studying",
            "Meditating", "Yoga", "Stretching", "Dancing", "Singing",
            "Gaming", "Watching TV", "Listening Music", "Photography", "Traveling",
            "Working", "Meeting", "Presenting", "Planning", "Organizing",
            "Sleeping", "Eating", "Drinking", "Baking", "Fishing",
            "Hiking", "Climbing", "Skiing", "Surfing", "Skating",
            "Driving", "Flying", "Sailing", "Riding", "Exploring",
            "Learning", "Teaching", "Coaching", "Mentoring", "Volunteering"
        ]
        
        self.filtered_tasks = self.tasks.copy()
        self.sort_ascending = True
        self.filter_text = ""
        self.case_sensitive = False
        self.regex_mode = False
        self.whole_word = False
        self.selected_task = None
        
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header row
        self.setup_header(main_frame)
        
        # Status label
        self.status_var = tk.StringVar()
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=(5, 10))
        
        # Task list with scrollbar
        self.setup_task_list(main_frame)
    
    def setup_header(self, parent):
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Column 1: Sort button (fixed width)
        sort_frame = ttk.Frame(header_frame)
        sort_frame.pack(side=tk.LEFT, )
        # sort_frame.pack_propagate(False)
        
        self.sort_btn = ttk.Button(sort_frame, text="Sort A-Z", command=self.toggle_sort, )
        self.sort_btn.pack(fill=tk.BOTH, expand=True)
        self.create_tooltip(self.sort_btn, "Toggle between ascending and descending alphabetical order")
        
        # Column 2: Filter controls (expanding)
        filter_frame = ttk.Frame(header_frame)
        filter_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Filter entry with icon
        entry_frame = ttk.Frame(filter_frame)
        entry_frame.pack(fill=tk.X)
        
        ttk.Label(entry_frame, text="🔍").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(entry_frame, textvariable=self.filter_var)
        self.filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.filter_entry.bind("<KeyRelease>", self.on_filter_change)
        
        # Clear button
        clear_btn = ttk.Button(entry_frame, text="Clear", command=self.clear_filter)
        clear_btn.pack(side=tk.LEFT, padx=(5, 0))
        self.create_tooltip(clear_btn, "Clear current filter")
        
        # Filter options
        options_frame = ttk.Frame(filter_frame)
        options_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.cs_btn = ttk.Button(options_frame, text="CS", command=self.toggle_case_sensitive)
        self.cs_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.create_tooltip(self.cs_btn, "Case Sensitive: Match exact case")
        
        self.regex_btn = ttk.Button(options_frame, text="RegEx", command=self.toggle_regex)
        self.regex_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.create_tooltip(self.regex_btn, "Regular Expression mode")
        
        self.whole_btn = ttk.Button(options_frame, text="mhw", command=self.toggle_whole_word)
        self.whole_btn.pack(side=tk.LEFT)
        self.create_tooltip(self.whole_btn, "Match Whole Word only")
        
        # Column 3: Run All button (fixed width)
        run_all_frame = ttk.Frame(header_frame, width=100)
        run_all_frame.pack(side=tk.RIGHT)
        # run_all_frame.pack_propagate(False)
        
        self.run_all_btn = ttk.Button(run_all_frame, text="Run All", command=self.run_all_tasks)
        self.run_all_btn.pack(fill=tk.BOTH, expand=True)
        self.create_tooltip(self.run_all_btn, "Run all visible filtered tasks")
    
    def setup_task_list(self, parent):
        # Create frame with scrollbar
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(list_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(list_frame, yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.canvas.yview)
        
        # Scrollable frame inside canvas
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Bind events for scrolling and resize
        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Bind mouse wheel to canvas and all children
        self.bind_mousewheel(self.canvas)
        self.bind_mousewheel(self.scrollable_frame)
        
        # Placeholder for no data
        self.no_data_label = ttk.Label(self.scrollable_frame, text="NO DATA Available", font=("Arial", 16))
    
    def bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self.on_mousewheel)
        for child in widget.winfo_children():
            self.bind_mousewheel(child)
    
    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def create_tooltip(self, widget, text):
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttk.Label(tooltip, text=text, background="yellow", relief="solid", borderwidth=1)
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def toggle_sort(self):
        self.sort_ascending = not self.sort_ascending
        self.sort_btn.config(text="Sort Z-A" if self.sort_ascending else "Sort A-Z")
        self.update_display()
    
    def toggle_case_sensitive(self):
        self.case_sensitive = not self.case_sensitive
        self.cs_btn.config(style="Accent.TButton" if self.case_sensitive else "TButton")
        self.update_display()
    
    def toggle_regex(self):
        self.regex_mode = not self.regex_mode
        self.regex_btn.config(style="Accent.TButton" if self.regex_mode else "TButton")
        self.update_display()
    
    def toggle_whole_word(self):
        self.whole_word = not self.whole_word
        self.whole_btn.config(style="Accent.TButton" if self.whole_word else "TButton")
        self.update_display()
    
    def on_filter_change(self, event):
        self.filter_text = self.filter_var.get()
        self.update_display()
    
    def clear_filter(self):
        self.filter_var.set("")
        self.filter_text = ""
        self.update_display()
    
    def filter_tasks(self):
        if not self.filter_text:
            return self.tasks.copy()
        
        filtered = []
        for task in self.tasks:
            text_to_search = task if self.case_sensitive else task.lower()
            filter_to_use = self.filter_text if self.case_sensitive else self.filter_text.lower()
            
            if self.regex_mode:
                try:
                    import re
                    if re.search(filter_to_use, text_to_search):
                        filtered.append(task)
                except:
                    # If regex is invalid, fall back to simple search
                    if filter_to_use in text_to_search:
                        filtered.append(task)
            elif self.whole_word:
                words = text_to_search.split()
                if filter_to_use in words:
                    filtered.append(task)
            else:
                if filter_to_use in text_to_search:
                    filtered.append(task)
        
        return filtered
    
    def update_display(self):
        # Clear existing task rows
        for widget in self.scrollable_frame.winfo_children():
            if widget != self.no_data_label:
                widget.destroy()
        
        # Apply filter and sort
        self.filtered_tasks = self.filter_tasks()
        
        if self.sort_ascending:
            self.filtered_tasks.sort()
        else:
            self.filtered_tasks.sort(reverse=True)
        
        # Show placeholder if no tasks
        if not self.filtered_tasks:
            self.no_data_label.pack(expand=True, fill=tk.BOTH, pady=50)
            self.status_var.set("Displaying 0 results out of 50")
            return
        else:
            self.no_data_label.pack_forget()
        
        # Create task rows
        for task in self.filtered_tasks:
            self.create_task_row(task)
        
        # Update status
        self.status_var.set(f"Displaying {len(self.filtered_tasks)} results out of {len(self.tasks)}")
        
        # Update scroll region and rebind mousewheel
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.bind_mousewheel(self.scrollable_frame)
    
    def create_task_row(self, task):
        row_frame = ttk.Frame(self.scrollable_frame, relief="solid", borderwidth=1)
        row_frame.pack(fill=tk.X, pady=1)
        
        # Bind mouse events for hover and click to entire row frame
        self.bind_row_events(row_frame)
        
        # Column 1: Empty (fixed width - same as header)
        empty_frame = ttk.Frame(row_frame, width=100)
        empty_frame.pack(side=tk.LEFT)
        # empty_frame.pack_propagate(False)
        self.bind_row_events(empty_frame)
        
        # Column 2: Task name (expanding - same as header)
        task_frame = ttk.Frame(row_frame)
        task_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.bind_row_events(task_frame)
        
        task_label = ttk.Label(task_frame, text=task, anchor="w")
        task_label.pack(fill=tk.X, expand=True)
        # task_label_ = HighlightedLabel(task_frame, task)
       
        self.bind_row_events(task_label)
        
        # Column 3: Run button (fixed width - same as header)
        btn_frame = ttk.Frame(row_frame, width=100)
        btn_frame.pack(side=tk.RIGHT)
        # btn_frame.pack_propagate(False)
        self.bind_row_events(btn_frame)
        
        run_btn = ttk.Button(btn_frame, text="Run", width=8)
        run_btn.pack(fill=tk.BOTH, expand=True)
        self.bind_row_events(run_btn)
        
        # Store references for styling        
        row_frame.task_label = task_label
        row_frame.empty_frame = empty_frame
        row_frame.task_frame = task_frame
        row_frame.btn_frame = btn_frame
        row_frame.task_text = task
        
        # Set initial background
        if row_frame == self.selected_task:
            self.select_row(row_frame)
            
            
        for child in row_frame.winfo_children():
            child.bind("<Enter>",      lambda e: self.on_row_enter(child))
            child.bind("<Leave>",      lambda e: self.on_row_leave(child))
            child.bind("<Button-1>",   lambda e: self.on_row_click(child))
            
    
    def bind_row_events(self, widget):
        ...
        # widget.bind("<Enter>",      lambda e: self.on_row_enter(e.widget.master.master if isinstance(e.widget, ttk.Button) else e.widget.master))
        # widget.bind("<Leave>",      lambda e: self.on_row_leave(e.widget.master.master if isinstance(e.widget, ttk.Button) else e.widget.master))
        # widget.bind("<Button-1>",   lambda e: self.on_row_click(e.widget.master.master if isinstance(e.widget, ttk.Button) else e.widget.master))
    
    def on_row_enter(self, row_frame):
        if not hasattr(row_frame, 'task_label'):
            return
        # Hover effect - light blue background
        if row_frame != self.selected_task:
            row_frame.configure(style="Hover.TFrame")
            row_frame.task_label.configure(background="#e6f3ff")
    
    def on_row_leave(self, row_frame):
        if not hasattr(row_frame, 'task_label'):
            return
        # Remove hover effect
        if row_frame != self.selected_task:
            row_frame.configure(style="TFrame")
            row_frame.task_label.configure(background="")
    
    def on_row_click(self, row_frame):
        if not hasattr(row_frame, 'task_text'):
            return
        # Remove selection from previous row
        if self.selected_task:
            self.deselect_row(self.selected_task)
        
        # Select new row
        self.select_row(row_frame)
        self.selected_task = row_frame
        print(f"Selected: {row_frame.task_text}")
        
        
        
        
        
        
            
    
    def select_row(self, row_frame):
        # Selection effect - light green background
        row_frame.configure(style="Selected.TFrame")
        row_frame.task_label.configure(background="#d4edda")
    
    def deselect_row(self, row_frame):
        # Remove selection effect
        row_frame.configure(style="TFrame")
        row_frame.task_label.configure(background="")
    
    def run_all_tasks(self):
        # Simple run all functionality
        print("Run All clicked")

if __name__ == "__main__":
    root = tk.Tk()
    


    
    # Configure styles for hover and selection
    style = ttk.Style()
    style.configure("Hover.TFrame", background="#e6f3ff")
    style.configure("Selected.TFrame", background="#d4edda")
    
    
    
    app = TaskManager(root)
    root.mainloop()