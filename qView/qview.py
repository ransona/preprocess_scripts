import os
import time
import getpass
import tkinter as tk
from pathlib import Path

# Editable settings
REFRESH_RATE = 1000  # Refresh every 1 second for jobs and logs
PRIORITY_REFRESH_RATE = 2000  # Refresh every 2 seconds for prioritized jobs
USER_TOTALS_REFRESH_RATE = 2000  # Refresh every 2 seconds for user totals
QUEUE_DIRECTORY = "/data/common/queues/step1"  # Queue directory path
LOG_FILE_PATH = "/data/common/queues/qlistener-log.txt"  # Log file path
PRIORITISED_JOBS_FILE = "prioritised_jobs.txt"  # Prioritised jobs file
USER_TOTALS_FILE = "user_totals.txt"  # User totals file

# Initialize global variables
last_log_size = 0
username = getpass.getuser()
MAX_LOG_LINES = 500  # Maximum number of lines to display in the log listbox
INITIAL_LOG_LINES = 100  # Number of lines to read initially from the end of the log file

# Font settings for a "techy" look
TECH_FONT = ("Courier", 10)  # Monospaced font for all list boxes

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

def refresh_prioritised_jobs():
    """Refresh the prioritized jobs list."""
    prioritised_jobs_list.delete(0, tk.END)  # Clear the list
    prioritised_file_path = Path(QUEUE_DIRECTORY) / PRIORITISED_JOBS_FILE

    if prioritised_file_path.exists():
        with open(prioritised_file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                prioritised_jobs_list.insert(tk.END, line.strip())  # Add jobs to the list box

    root.after(PRIORITY_REFRESH_RATE, refresh_prioritised_jobs)

def refresh_user_totals():
    """Refresh the user totals list."""
    user_totals_list.delete(0, tk.END)  # Clear the list
    user_totals_file_path = Path(QUEUE_DIRECTORY) / USER_TOTALS_FILE

    if user_totals_file_path.exists():
        with open(user_totals_file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                user_totals_list.insert(tk.END, line.strip()+' mins')  # Add user totals to the list box

    root.after(USER_TOTALS_REFRESH_RATE, refresh_user_totals)

def refresh_log():
    """Refresh the log, ensuring the last 500 lines are always displayed, with encoding handling."""
    global last_log_size
    auto_scroll = log_list.yview()[1] == 1.0  # Check if we're already at the bottom

    if Path(LOG_FILE_PATH).exists():
        try:
            with open(LOG_FILE_PATH, 'rb') as log_file:  # Open in binary mode
                log_file.seek(last_log_size)  # Start reading from the last known position
                data = log_file.read()  # Read new data
                try:
                    new_lines = data.decode('utf-8').splitlines()  # Attempt UTF-8 decoding
                except UnicodeDecodeError:
                    print("DEBUG: UTF-8 decoding failed, falling back to latin-1.")
                    new_lines = data.decode('latin-1').splitlines()  # Fallback to latin-1

                last_log_size += len(data)  # Update last known position

                if new_lines:
                    print(f"DEBUG: {len(new_lines)} new lines detected in log file.")

                # Add new lines to the log box
                for line in new_lines:
                    log_list.insert(tk.END, line.strip())

                # Enforce the 500-line limit by removing lines from the top
                current_line_count = len(log_list.get(0, tk.END))
                if current_line_count > MAX_LOG_LINES:
                    excess_lines = current_line_count - MAX_LOG_LINES
                    print(f"DEBUG: Removing {excess_lines} excess lines to maintain 500-line limit.")
                    log_list.delete(0, excess_lines)

                # Debugging: Output the current number of lines in the Listbox
                current_line_count = len(log_list.get(0, tk.END))
                print(f"DEBUG: Current number of lines in Listbox: {current_line_count}")

                # Scroll to the bottom only if we were already at the bottom
                if auto_scroll:
                    log_list.yview_moveto(1.0)

        except (OSError, IOError) as e:
            print(f"DEBUG: File access error: {e}")
        except Exception as e:
            print(f"DEBUG: Unexpected error: {e}")

    root.after(REFRESH_RATE, refresh_log)



# Setting up the GUI
root = tk.Tk()
root.title("Job Queue Manager")

# Adjust window size
window_width = 800
window_height = 600
root.geometry(f"{window_width}x{window_height}")

# Queue Listbox with Scrollbar
queue_frame = tk.Frame(root)
queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

tk.Label(queue_frame, text="Jobs in Queue (From Folder):", font=TECH_FONT).pack(anchor=tk.W)
queue_scrollbar = tk.Scrollbar(queue_frame)
queue_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

queue_list = tk.Listbox(queue_frame, width=80, height=10, yscrollcommand=queue_scrollbar.set, font=TECH_FONT, selectmode=tk.SINGLE)
queue_list.pack(fill=tk.BOTH, expand=True)
queue_scrollbar.config(command=queue_list.yview)

# Prioritized Jobs Listbox with Scrollbar
prioritised_frame = tk.Frame(root)
prioritised_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

tk.Label(prioritised_frame, text="Prioritized Jobs (From File):", font=TECH_FONT).pack(anchor=tk.W)
prioritised_scrollbar = tk.Scrollbar(prioritised_frame)
prioritised_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

prioritised_jobs_list = tk.Listbox(prioritised_frame, width=80, height=10, yscrollcommand=prioritised_scrollbar.set, font=TECH_FONT)
prioritised_jobs_list.pack(fill=tk.BOTH, expand=True)
prioritised_scrollbar.config(command=prioritised_jobs_list.yview)

# User Totals Listbox
user_totals_frame = tk.Frame(root)
user_totals_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

tk.Label(user_totals_frame, text="User Compute Times:", font=TECH_FONT).pack(anchor=tk.W)
user_totals_list = tk.Listbox(user_totals_frame, width=80, height=5, font=TECH_FONT)
user_totals_list.pack(fill=tk.BOTH, expand=True)

# Log List Box with Scrollbar
log_frame = tk.Frame(root)
log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

tk.Label(log_frame, text="Log Feedback:", font=TECH_FONT).pack(anchor=tk.W)
log_scrollbar = tk.Scrollbar(log_frame)
log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

log_list = tk.Listbox(log_frame, width=80, height=10, yscrollcommand=log_scrollbar.set, font=TECH_FONT)
log_list.pack(fill=tk.BOTH, expand=True)
log_scrollbar.config(command=log_list.yview)

# Load initial log lines and start refreshes
load_initial_log_lines()
refresh_queue_list()
refresh_prioritised_jobs()
refresh_user_totals()
refresh_log()

root.mainloop()
