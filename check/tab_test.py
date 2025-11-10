import tkinter as tk
from tkinter import ttk, Menu, simpledialog

# --- TabArrangerWindow CLASS ---

class TabArrangerWindow(tk.Toplevel):
    """
    A modal Toplevel window that displays a reorderable list of all
    open tabs from a CustomNotebook. Reordering the list here
    reorders the actual tabs in the notebook in real-time.
    """
    def __init__(self, parent_notebook, tab_list):
        """
        Initializes the tab arranger window.
        
        :param parent_notebook: The CustomNotebook instance to control.
        :param tab_list: The list of current tab names.
        """
        super().__init__(parent_notebook.master)
        
        self.notebook = parent_notebook
        
        # --- Window Setup ---
        self.title("Arrange Tabs")
        self.geometry("300x250")
        
        # Make this window transient (stays on top) and modal
        self.transient(parent_notebook.master)
        self.grab_set()
        
        # This variable will store the index of the tab being dragged
        self.drag_start_index = None

        # --- Create and Populate the Listbox ---
        self.tab_listbox = tk.Listbox(self, height=10, width=40, selectmode=tk.SINGLE)
        self.tab_listbox.pack(padx=10, pady=10)

        for tab_name in tab_list:
            self.tab_listbox.insert(tk.END, tab_name)

        # --- Bind Mouse Events ---
        self.tab_listbox.bind("<Button-1>", self.on_tab_drag_start)
        self.tab_listbox.bind("<B1-Motion>", self.on_tab_drag_motion)
        self.tab_listbox.bind("<ButtonRelease-1>", self.on_tab_drag_release)
        
        # Make a sound to alert the user
        self.bell()
        
        # Wait until this window is closed before returning
        self.wait_window(self)

    def on_tab_drag_start(self, event):
        """Called when the user first clicks to start dragging a tab name."""
        
        # Find the index of the item closest to the mouse click
        index = self.tab_listbox.nearest(event.y)
        
        # Check if the click was actually on an item
        try:
            bbox = self.tab_listbox.bbox(index)
            if bbox and event.y >= bbox[1] and event.y <= bbox[1] + bbox[3]:
                # Store the index of the item we're starting to drag
                self.drag_start_index = index
                
                # Set the listbox selection to the item being dragged
                self.tab_listbox.selection_clear(0, tk.END)
                self.tab_listbox.selection_set(index)
                
                # Change the cursor to a "hand"
                self.tab_listbox.config(cursor="hand2")
            else:
                self.drag_start_index = None
        except tk.TclError:
            # This can happen if the list is empty
            self.drag_start_index = None


    def on_tab_drag_motion(self, event):
        """Called every time the mouse moves while dragging."""
        
        # We only do something if a drag is actually in progress
        if self.drag_start_index is None:
            return

        # Get the new index of the item under the mouse cursor
        new_index = self.tab_listbox.nearest(event.y)

        # If the item has been dragged to a new position...
        if new_index != self.drag_start_index:
            # Get the text of the item being dragged
            item_text = self.tab_listbox.get(self.drag_start_index)
            
            # Delete the item from its old position
            self.tab_listbox.delete(self.drag_start_index)
            
            # Insert the item at its new position
            self.tab_listbox.insert(new_index, item_text)
            
            # Keep the item selected at its new position
            self.tab_listbox.selection_set(new_index)
            
            # --- REAL-TIME UPDATE ---
            # Call the notebook's reorder method
            self.notebook.reorder_tab(self.drag_start_index, new_index)
            
            # Update the drag_start_index to the new_index
            self.drag_start_index = new_index

    def on_tab_drag_release(self, event):
        """Called when the user releases the mouse button."""
        
        # Reset the cursor
        self.tab_listbox.config(cursor="")
        
        # Reset the drag index, as the drag operation is complete
        self.drag_start_index = None

# --- END OF TabArrangerWindow CLASS ---


# +++ MODIFIED CLASS: TabMonitorWindow +++

class TabMonitorWindow(tk.Toplevel):
    """
    A non-modal Toplevel window that displays a real-time list
    of all open tabs and all "windowed" (detached) tabs
    from a CustomNotebook.
    """
    def __init__(self, parent_notebook):
        """
        Initializes the tab monitor window.
        
        :param parent_notebook: The CustomNotebook instance to monitor.
        """
        super().__init__(parent_notebook.master)
        
        self.notebook = parent_notebook
        
        # --- Window Setup ---
        self.title("Tab Monitor")
        self.geometry("300x400")
        
        # --- Register with Notebook ---
        self.notebook.monitor_window = self
        
        # --- Style for Active Tab Button ---
        self.style = ttk.Style(self)
        self.style.configure(
            "ActiveTab.TButton",
            foreground="#00008B", # Dark Blue
            font=("Arial", 9, "bold")
        )
        
        # --- Create Sections ---
        tabs_section = ttk.LabelFrame(self, text="All Available Tabs")
        tabs_section.pack(padx=10, pady=10, fill="x")
        
        self.tabs_list_frame = ttk.Frame(tabs_section)
        self.tabs_list_frame.pack(padx=5, pady=5)

        windows_section = ttk.LabelFrame(self, text="All Available Windowed Tabs")
        windows_section.pack(padx=10, pady=10, fill="x")

        self.windows_list_frame = ttk.Frame(windows_section)
        self.windows_list_frame.pack(padx=5, pady=5)
        
        # --- Handle Closing ---
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # --- Initial Population ---
        self.update_lists()

    def update_lists(self):
        """
        Clears and rebuilds the button lists for both sections.
        This is called by the CustomNotebook in real-time.
        """
        
        # --- 1. Clear Old Buttons ---
        for widget in self.tabs_list_frame.winfo_children():
            widget.destroy()
            
        for widget in self.windows_list_frame.winfo_children():
            widget.destroy()

        # --- 2. Rebuild "Available Tabs" List ---
        try:
            try:
                current_tab_index = self.notebook.index("current")
            except tk.TclError:
                current_tab_index = -1 

            content_tabs = self.notebook.tabs()[:-1]
            tab_names = [self.notebook.tab(tab_id, "text") for tab_id in content_tabs]
            
            if not tab_names:
                ttk.Label(self.tabs_list_frame, text="(No tabs open)").pack()
            else:
                for i, name in enumerate(tab_names):
                    button_style = "TButton"
                    
                    # +++ THIS IS THE NEW LOGIC +++
                    if i == current_tab_index:
                        button_style = "ActiveTab.TButton"
                        # Only show star if notebook is focused (no window is active)
                        if self.notebook.active_detached_window is None:
                            name = f"* {name}"
                    # +++ END OF NEW LOGIC +++
                    
                    btn = ttk.Button(
                        self.tabs_list_frame, 
                        text=name, # Use the (potentially modified) name
                        command=lambda idx=i: self.notebook.select(idx),
                        style=button_style
                    )
                    btn.pack(fill="x", pady=2)
            
            # +++ REMOVED the "A tab window is focused" label +++
                    
        except Exception as e:
            print(f"Error updating tab list: {e}")


        # --- 3. Rebuild "Windowed Tabs" List ---
        try:
            detached_items = self.notebook.detached_windows.items()
            
            if not detached_items:
                ttk.Label(self.windows_list_frame, text="(No windowed tabs)").pack()
            else:
                for window, frame in detached_items:
                    name = frame.original_tab_name
                    
                    # This logic remains: show star if window is active
                    if window == self.notebook.active_detached_window:
                        name = f"* {name}" # Add the star
                    
                    btn = ttk.Button(
                        self.windows_list_frame, 
                        text=name,
                        command=lambda w=window: self.focus_window(w)
                    )
                    btn.pack(fill="x", pady=2)

        except Exception as e:
            print(f"Error updating windowed list: {e}")

    def focus_window(self, window_to_focus):
        """
        Brings the specified Toplevel window to the front and gives it focus.
        """
        try:
            window_to_focus.lift()
            window_to_focus.focus_force()
            window_to_focus.bell()
        except tk.TclError:
            print("Could not focus window; it may no longer exist.")
            self.notebook._notify_monitor() # Trigger a refresh


    def on_close(self):
        """
        Called when the user clicks the 'X' button on this window.
        """
        if self.notebook.monitor_window == self:
            self.notebook.monitor_window = None
            
        self.destroy()

# +++ END OF TabMonitorWindow CLASS +++


# +++ MODIFIED CLASS: CustomNotebook +++

class CustomNotebook(ttk.Notebook):
    """
    A custom ttk.Notebook widget that includes features like a
    permanent '+' tab for adding new tabs, a right-click context menu
    for closing and renaming, and double-click-to-rename.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # --- Configuration ---
        self.tab_counter = 1
        self.monitor_window = None 
        self.detached_windows = {}
        
        # +++ This variable now controls all focus logic +++
        self.active_detached_window = None
        
        # --- Setup ---
        self._setup_styles()
        self._create_plus_tab() 
        self._create_context_menu()
        self._bind_events()

    def _setup_styles(self):
        """
        Sets up the global font styles for the notebook tabs.
        """
        style = ttk.Style()
        
        style.configure(
            "TNotebook.Tab",
            font=("Arial", 10),
            foreground="red",
            padding=[10, 2]
        )
        
        style.map(
            "TNotebook.Tab",
            font=[("selected", ("Arial", 10, "bold"))],
            foreground=[("selected", "#00008B")]
        )
        
        style.configure("Content.TFrame", background="white")
        style.configure("Content.TLabel", background="white")


    def _bind_events(self):
        """Binds all the necessary events for custom functionality."""
        self.bind("<Button-1>", self.on_tab_click) 
        self.bind("<Button-3>", self.on_tab_right_click)
        self.bind("<Double-1>", self.on_tab_double_click)
        self.bind("<<NotebookTabChanged>>", self.on_tab_selection_changed)


    def _create_plus_tab(self):
        """Creates the permanent, disabled '+' tab."""
        plus_frame = ttk.Frame(self)
        self.add(plus_frame, text="+", state="disabled")
    
    def _create_context_menu(self):
        """Creates the right-click context menu (initially hidden)."""
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Close", command=lambda: None)
        self.context_menu.add_command(label="Rename", command=lambda: None)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Windowed", command=lambda: None)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Arrange Tabs...", command=self.open_tab_arranger)
        
    def _notify_monitor(self):
        """
        If the monitor window is open, tells it to update its lists.
        """
        if self.monitor_window:
            try:
                self.monitor_window.update_lists()
            except tk.TclError:
                self.monitor_window = None
    
    def on_tab_selection_changed(self, event):
        """
        Called by the <<NotebookTabChanged>> event.
        """
        # If notebook tab is changed, it means notebook is focused
        self.active_detached_window = None
        self._notify_monitor()
        
    # --- Methods for focus tracking ---
    def set_active_detached_window(self, window):
        """Sets the currently focused detached window."""
        self.active_detached_window = window
        self._notify_monitor()

    def clear_active_detached_window(self, window):
        """Clears the focused detached window if it matches."""
        if self.active_detached_window == window:
            self.active_detached_window = None
            self._notify_monitor()
        
    def add_new_tab(self):
        """
        Adds a new content tab.
        """
        tab_name = f"Tab {self.tab_counter}"
        self.tab_counter += 1
        
        frame = ttk.Frame(self, padding=10, style="Content.TFrame")
        frame.original_tab_name = tab_name

        lbl = ttk.Label(frame, text=f"This is content for {tab_name}", style="Content.TLabel")
        lbl.pack(padx=20, pady=20)
        
        plus_tab_index = self.index("end") - 1 
        self.insert(plus_tab_index, frame, text=tab_name) 
        
        self.select(frame) # This triggers on_tab_selection_changed

        return frame

    def on_tab_click(self, event):
        """Handles clicks on the notebook to add new tabs."""
        try:
            clicked_tab_index = self.index(f"@{event.x},{event.y}")
            plus_tab_index = self.index("end") - 1
            
            if clicked_tab_index == plus_tab_index:
                self.add_new_tab()
                return "break"
            else:
                # Click on a tab means notebook is focused
                self.active_detached_window = None
                # Let <<NotebookTabChanged>> handle the notify
                pass
        except tk.TclError:
            pass

    def on_tab_right_click(self, event):
        """
        Shows the context menu on right-click if on a valid tab.
        """
        try:
            clicked_tab_index = self.index(f"@{event.x},{event.y}")
            plus_tab_index = self.index("end") - 1 

            if clicked_tab_index != plus_tab_index: 
                self.context_menu.entryconfigure(
                    "Close",
                    command=lambda idx=clicked_tab_index: self.close_tab(idx)
                )
                self.context_menu.entryconfigure(
                    "Rename",
                    command=lambda idx=clicked_tab_index: self.start_rename(idx)
                )
                self.context_menu.entryconfigure(
                    "Windowed",
                    command=lambda idx=clicked_tab_index: self.detach_tab(idx)
                )
                
                # Right-click means notebook is focused
                self.active_detached_window = None
                self.select(clicked_tab_index) # This triggers on_tab_selection_changed
                self.context_menu.tk_popup(event.x_root, event.y_root)
                
        except tk.TclError:
            pass

    def on_tab_double_click(self, event):
        """
        Handles double-click to start renaming.
        """
        try:
            clicked_tab_index = self.index(f"@{event.x},{event.y}")
            plus_tab_index = self.index("end") - 1 

            if clicked_tab_index != plus_tab_index: 
                self.start_rename(clicked_tab_index)
                
        except tk.TclError:
            pass

    
    def close_tab(self, tab_index):
        """
        Closes the tab at the specified index.
        """
        try:
            self.forget(tab_index)
            # self.forget() triggers a tab change, so no extra notify needed
            self._notify_monitor() # Call just in case last tab is closed
            
        except tk.TclError:
            pass


    def start_rename(self, tab_index):
        """
        Starts the renaming process for the specified tab.
        """
        try:
            current_text = self.tab(tab_index, "text")
            
            self.bell()
            
            new_text = simpledialog.askstring(
                "Rename Tab",
                "Enter new tab name:",
                initialvalue=current_text,
                parent=self
            )
            
            if new_text:
                self.tab(tab_index, text=new_text)
                
                frame_widget = self.nametowidget(self.tabs()[tab_index])
                frame_widget.original_tab_name = new_text

                self._notify_monitor()
                
        except Exception as e:
            print(f"Error starting rename: {e}")

    
    def open_tab_arranger(self):
        """
        Opens the modal TabArrangerWindow to allow reordering
        of the currently open tabs.
        """
        try:
            content_tabs = self.tabs()[:-1]
            tab_names = [self.tab(tab_id, "text") for tab_id in content_tabs]
            
            TabArrangerWindow(parent_notebook=self, tab_list=tab_names)
            
        except Exception as e:
            print(f"Error opening tab arranger: {e}")


    def reorder_tab(self, from_index, to_index):
        """
        Moves a tab from one index to another. This is called
        by the TabArrangerWindow in real-time.
        """
        try:
            tab_to_move = self.tabs()[from_index]
            self.insert(to_index, tab_to_move)

            self._notify_monitor()
            
        except Exception as e:
            print(f"Error reordering tab: {e}")

    def detach_tab(self, tab_index):
        """
        Removes a tab and places its content into a new Toplevel window.
        """
        try:
            frame_id = self.tabs()[tab_index]
            frame_widget = self.nametowidget(frame_id)
            tab_text = frame_widget.original_tab_name
            
            # 1. Forget the tab
            self.forget(tab_index)
            frame_widget.place_forget() 
            
            # 2. Create the new Toplevel window
            new_window = tk.Toplevel(self.master)
            new_window.title(tab_text)
            new_window.geometry("400x300")
            new_window.config(background="white")
            
            self.detached_windows[new_window] = frame_widget
            
            # 3. Create the menu bar
            menubar = Menu(new_window)
            new_window.config(menu=menubar)
            
            # 4. Add "Return" command
            menubar.add_command(
                label="Return to Tab",
                command=lambda w=new_window, f=frame_widget: self.attach_tab(w, f)
            )
            
            # 5. Move the frame into the new window
            # frame_widget.pack(in_=new_window, expand=True, fill="both")
            
            # 6. Set the window's close ('X') button
            new_window.protocol(
                "WM_DELETE_WINDOW",
                lambda w=new_window, f=frame_widget: self.attach_tab(w, f)
            )
            
            # +++ Bind focus events +++
            new_window.bind("<FocusIn>", lambda e, w=new_window: self.set_active_detached_window(w))
            new_window.bind("<FocusOut>", lambda e, w=new_window: self.clear_active_detached_window(w))
            # +++ END +++

            # Give the new window focus, which will trigger <FocusIn>
            new_window.focus_set()
            
        except Exception as e:
            print(f"Error detaching tab: {e}")

    def attach_tab(self, window, frame):
        """Moves the content frame back into the notebook and destroys the window."""
        try:
            # Explicitly clear focus
            self.clear_active_detached_window(window)
            
            tab_name = frame.original_tab_name
            
            self.detached_windows.pop(window, None)
            
            # 1. Remove frame from the Toplevel window
            frame.pack_forget()
            
            # 2. Re-insert the frame into the notebook
            plus_tab_index = self.index("end") - 1 
            self.insert(plus_tab_index, frame, text=tab_name) 
            
            # 3. Select the re-inserted tab
            self.select(frame) # This triggers on_tab_selection_changed
            
            # 4. Destroy the Toplevel window
            window.destroy()
            
        except Exception as e:
            print(f"Error attaching tab: {e}")


# --- open_monitor_window FUNCTION (Unchanged) ---

def open_monitor_window(notebook_instance):
    """
    Opens the TabMonitorWindow.
    If one is already open, it just brings it to the front.
    """
    if notebook_instance.monitor_window:
        try:
            # If window exists, bring it to the front
            notebook_instance.monitor_window.lift()
            notebook_instance.monitor_window.bell()
        except tk.TclError:
            # The window was destroyed without un-registering
            notebook_instance.monitor_window = None
            TabMonitorWindow(notebook_instance) # Create a new one
    else:
        # No monitor window exists, so create one
        TabMonitorWindow(notebook_instance)


# --- Main application setup ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Advanced Tab Interface Demo")
    
    root.geometry("700x500") # Fixed typo from previous version

    main_frame = ttk.Frame(root)
    main_frame.pack(expand=True, fill="both", padx=5, pady=5)

    monitor_button = ttk.Button(
        main_frame, 
        text="Open Tab Monitor",
        command=lambda: open_monitor_window(notebook) 
    )
    monitor_button.pack(pady=(5, 10))

    main_label = ttk.Label(main_frame, text="My Application", font=("Arial", 16))
    main_label.pack(pady=0)

    notebook = CustomNotebook(main_frame)
    notebook.pack(expand=True, fill="both", pady=(10, 0))
    
    notebook.add_new_tab()

    root.mainloop()