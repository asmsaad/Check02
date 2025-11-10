import tkinter as tk

class ReorderableListbox(tk.Tk):
    """
    A simple Tkinter application with a drag-and-drop
    reorderable listbox.
    
    MODIFICATION:
    - The cursor changes to a "hand" during the drag.
    - The item moves "live" during the drag (no ghost window).
    """
    def __init__(self, tasks):
        super().__init__()

        self.title("Drag-and-Drop (Simple Move)")
        self.geometry("300x250")

        self.tasks = tasks
        
        # This variable will store the index of the item being dragged
        self.drag_start_index = None

        # --- Create and Populate the Listbox ---
        self.listbox = tk.Listbox(self, height=10, width=40, selectmode=tk.SINGLE)
        self.listbox.pack(padx=10, pady=10)

        for task in self.tasks:
            self.listbox.insert(tk.END, task)

        # --- Bind Mouse Events ---
        self.listbox.bind("<Button-1>", self.on_drag_start)
        self.listbox.bind("<B1-Motion>", self.on_drag_motion)
        self.listbox.bind("<ButtonRelease-1>", self.on_drag_release)

    def on_drag_start(self, event):
        """Called when the user first clicks to start dragging."""
        
        # Find the index of the item closest to the mouse click
        index = self.listbox.nearest(event.y)
        
        # Check if the click was actually on an item
        try:
            bbox = self.listbox.bbox(index)
            if bbox and event.y >= bbox[1] and event.y <= bbox[1] + bbox[3]:
                # Store the index of the item we're starting to drag
                self.drag_start_index = index
                
                # Set the listbox selection to the item being dragged
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(index)
                
                # --- MODIFICATION: Change the cursor ---
                self.listbox.config(cursor="hand2")
            else:
                self.drag_start_index = None
        except tk.TclError:
            # This can happen if the list is empty
            self.drag_start_index = None


    def on_drag_motion(self, event):
        """Called every time the mouse moves while dragging."""
        
        # We only do something if a drag is actually in progress
        if self.drag_start_index is None:
            return

        # Get the new index of the item under the mouse cursor
        new_index = self.listbox.nearest(event.y)

        # If the item has been dragged to a new position...
        if new_index != self.drag_start_index:
            # Get the text of the item being dragged
            item_text = self.listbox.get(self.drag_start_index)
            
            # Delete the item from its old position
            self.listbox.delete(self.drag_start_index)
            
            # Insert the item at its new position
            self.listbox.insert(new_index, item_text)
            
            # Keep the item selected at its new position
            self.listbox.selection_set(new_index)
            
            # Update the drag_start_index to the new_index
            self.drag_start_index = new_index

    def on_drag_release(self, event):
        """Called when the user releases the mouse button."""
        
        # --- MODIFICATION: Reset the cursor ---
        self.listbox.config(cursor="")
        
        # Reset the drag index, as the drag operation is complete
        self.drag_start_index = None
        
        # --- Print the Current Order ---
        print("--- Current Task Order ---")
        
        current_order_list = self.listbox.get(0, tk.END)
        
        if not current_order_list:
            print("[Empty]")
        else:
            for i, task in enumerate(current_order_list):
                print(f"{i+1}: {task}")
        
        print("----------------------------\n")


# --- Main part of the script ---
if __name__ == "__main__":
    # Your initial list of tasks
    initial_tasks = [
        "Task 1: Buy groceries",
        "Task 2: Finish report",
        "Task 3: Call dentist",
        "Task 4: Go to the gym",
        "Task 5: Plan weekend trip"
    ]

    # Create the application instance
    app = ReorderableListbox(initial_tasks)
    
    # Start the Tkinter main event loop
    app.mainloop()