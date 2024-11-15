import os
import time
import getpass
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

# Editable settings
REFRESH_RATE = 1000  # Refresh every 1 second (1000 ms)
QUEUE_DIRECTORY = "/data/common/queues/step1"  # Queue directory path
LOG_FILE_PATH = "/data/common/queues/qlistener-log.txt"  # Log file path

# Initialize global variables
last_log_size = 0
username = getpass.getuser()
MAX_LOG_LINES = 500  # Maximum number of lines to display in the log listbox
INITIAL_LOG_LINES = 100  # Number of lines to read initially from the end of the log file
confirm_button = None  # Secondary button for delete confirmation

# Font settings for a "techy" look
TECH_FONT = ("Courier", 10)  # Monospaced font for both list boxes

def load_initial_log_lines():
    """Load the last INITIAL_LOG_LINES from the log file."""
    global last_log_size
    if Path(LOG_FILE_PATH).exists():
        with open(LOG_FILE_PATH, 'r') as log_file:
            log_file.seek(0, os.SEEK_END)
            file_size = log_file.tell()

            if file_size > 0:
                # Move to a reasonable size chunk from the end of the file
                log_file.seek(max(0, file_size - 4096))
                lines = log_file.readlines()[-INITIAL_LOG_LINES:]  # Read the last 100 lines
                last_log_size = log_file.tell()

                for line in lines:
                    log_list.insert(tk.END, line.strip())

                # Scroll to the bottom of the log list after inserting initial lines
                log_list.yview_moveto(1.0)

def refresh_queue_list():
    """Refresh the list of jobs in the queue, marking user's jobs with an asterisk (*) prefix."""
    # Remember the currently selected job
    try:
        selected_index = queue_list.curselection()[0]
        selected_job = queue_list.get(selected_index)
    except IndexError:
        selected_job = None

    # Clear existing items
    queue_list.delete(0, tk.END)
    
    # Fetch and sort queue files
    queue_files = sorted([f for f in os.listdir(QUEUE_DIRECTORY) if f.endswith('.pickle')])
    for index, job_file in enumerate(queue_files, start=1):
        # Format the index with leading zeros
        prefix = f"{index:03}."
        
        # Mark user's jobs with an asterisk for distinction, pad non-user jobs for alignment
        if username in job_file:
            job_display = f"* {prefix} {job_file}"
        else:
            job_display = f"  {prefix} {job_file}"  # Add space for alignment

        queue_list.insert(tk.END, job_display)

    # Restore selection if the previously selected job still exists
    if selected_job is not None:
        try:
            index_to_select = queue_list.get(0, tk.END).index(selected_job)
            queue_list.select_set(index_to_select)
        except ValueError:
            pass  # The previously selected item no longer exists

    # Schedule the next refresh
    root.after(REFRESH_RATE, refresh_queue_list)

def refresh_log():
    """Refresh the log, checking for new lines and scrolling if at the bottom."""
    global last_log_size
    auto_scroll = log_list.yview()[1] == 1.0  # Check if we're already at the bottom

    if Path(LOG_FILE_PATH).exists():
        with open(LOG_FILE_PATH, 'r') as log_file:
            log_file.seek(last_log_size)  # Start reading from the last known position
            new_lines = log_file.readlines()  # Read new lines
            last_log_size += sum(len(line) for line in new_lines)  # Update log size

            for line in new_lines:
                log_list.insert(tk.END, line.strip())  # Add new lines to the log box

            # Enforce the 500-line limit by removing lines from the top
            current_line_count = len(log_list.get(0, tk.END))
            if current_line_count > MAX_LOG_LINES:
                log_list.delete(0, current_line_count - MAX_LOG_LINES)

            # Scroll to the bottom only if we were already at the bottom
            if auto_scroll:
                log_list.yview_moveto(1.0)

    root.after(REFRESH_RATE, refresh_log)

def delete_selected_job():
    """Initial delete action that shows the confirm button for final confirmation."""
    global confirm_button
    try:
        selected_line = queue_list.get(queue_list.curselection())  # Get selected line
        job_file = selected_line.split('. ', 1)[-1]  # Extract job file name

        # Create and display confirm button if it's a different user's job
        if username in job_file:
            confirm_and_delete(job_file)
        else:
            # If confirm button already exists, don't create another
            if confirm_button:
                confirm_button.config(command=lambda: confirm_and_delete(job_file))
            else:
                confirm_button = tk.Button(root, text="Confirm Delete", command=lambda: confirm_and_delete(job_file))
                confirm_button.pack(pady=5)

    except tk.TclError:
        messagebox.showwarning("Warning", "No job selected. Please select a job to delete.")

def confirm_and_delete(job_file):
    """Delete the specified job file and refresh the queue list."""
    global confirm_button
    try:
        job_path = os.path.join(QUEUE_DIRECTORY, job_file)
        os.remove(job_path)
        refresh_queue_list()
    except Exception as e:
        messagebox.showerror("Error", f"Could not delete the job: {e}")
    finally:
        # Remove confirm button after deletion attempt
        if confirm_button:
            confirm_button.pack_forget()
            confirm_button = None

# Setting up the GUI
root = tk.Tk()
root.title("Job Queue Manager")

# Adjust window size
window_width = 700
window_height = 500
root.geometry(f"{window_width}x{window_height}")

# Queue Listbox with Scrollbar
queue_frame = tk.Frame(root)
queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

queue_scrollbar = tk.Scrollbar(queue_frame)
queue_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

queue_list = tk.Listbox(queue_frame, width=70, height=20, yscrollcommand=queue_scrollbar.set, font=TECH_FONT, selectmode=tk.SINGLE)
queue_list.pack(fill=tk.BOTH, expand=True)
queue_scrollbar.config(command=queue_list.yview)

# Delete Button
delete_button = tk.Button(root, text="Delete Selected Job", command=delete_selected_job)
delete_button.pack(pady=5)

# Log List Box with Scrollbar
log_frame = tk.Frame(root)
log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

log_scrollbar = tk.Scrollbar(log_frame)
log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

log_list = tk.Listbox(log_frame, width=70, height=10, yscrollcommand=log_scrollbar.set, font=TECH_FONT)
log_list.pack(fill=tk.BOTH, expand=True)
log_scrollbar.config(command=log_list.yview)

# Load initial log lines and queue
load_initial_log_lines()
refresh_queue_list()

# Start refreshing queue and log
root.after(REFRESH_RATE, refresh_queue_list)
root.after(REFRESH_RATE, refresh_log)

root.mainloop()
