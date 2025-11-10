import tkinter as tk
from tkinter import ttk

# --- Function to handle the "action" ---
def start_selected_workout(event):
    """
    This function is triggered by an event (like a double-click).
    It gets the currently selected item(s) from the listbox and prints one.
    """
    # 'curselection()' returns a tuple of selected line indices (e.g., (3,))
    selected_indices = listbox.curselection()
    
    if not selected_indices:
        # If nothing is selected, do nothing
        return
        
    # Get the index of the first selected item
    selected_index = selected_indices[0]
    
    # Get the text string at that index
    workout_name = listbox.get(selected_index)
    
    print(f"Starting workout: {workout_name}!")

# --- Main Application Window ---
root = tk.Tk()
root.title("Listbox Workout List")
root.geometry("400x400") # Set a starting size

# --- Create a frame to hold the listbox and scrollbar ---
frame = ttk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# --- Create a Scrollbar ---
# The scrollbar will be placed *next to* the listbox
scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# --- Create the Listbox ---
listbox = tk.Listbox(
    frame, 
    yscrollcommand=scrollbar.set, # Link scrollbar to listbox
    selectmode=tk.SINGLE,         # Only allow one item to be selected
    height=20                     # Show 20 items before scrolling
)
listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# --- Link the scrollbar back to the listbox ---
scrollbar.config(command=listbox.yview)

# --- Populate the Listbox with workout items ---
workout_list = [
    "Push-ups", "Squats", "Plank", "Jumping Jacks", "Lunges",
    "Burpees", "Mountain Climbers", "Crunches", "Leg Raises", "Bicep Curls",
    "Tricep Dips", "Overhead Press", "Deadlifts", "Bench Press", "Rows",
    "Pull-ups", "Chin-ups", "Calf Raises", "Glute Bridges", "Bird-dog",
    "Russian Twists", "Side Plank", "Flutter Kicks", "High Knees", "Box Jumps",
    "Kettlebell Swings","Dumbbell Flyes", "Lateral Raises", "Front Raises", "Shrugs",
    "Woodchoppers", "Wall Sits", "Inchworms", "Spiderman Push-ups", "Pistol Squats",
    "Good Mornings", "Hip Thrusts", "Reverse Crunches", "Hanging Knee Raises", "Sprints",
    "Jump Rope", "Shadow Boxing", "Yoga Sun Salutation", "Stretching Routine", "Foam Rolling",
    "Cycling (Stationary)", "Rowing Machine", "Stair Climber", "Elliptical", "Treadmill Run"
]

# Ensure we have 50 items for the example
if len(workout_list) < 50:
    workout_list.extend([f"Extra Workout {i+1}" for i in range(50 - len(workout_list))])

# Add each item to the end of the listbox
for workout in workout_list:
    listbox.insert(tk.END, workout)

# --- Bind the Events ---
# Bind the <Double-Button-1> (left double-click) event to our function
listbox.bind("<Double-Button-1>", start_selected_workout)

# Bind the <Return> (Enter key) event to our function
listbox.bind("<Return>", start_selected_workout)

# --- Add a label to instruct the user ---
info_label = ttk.Label(root, text="Double-click or press Enter on an item to start.")
info_label.pack(pady=5)

# --- Start the application ---
root.mainloop()