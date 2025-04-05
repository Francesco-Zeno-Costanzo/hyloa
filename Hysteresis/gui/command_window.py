"""
Code to manage the window where you can
run code to make changes to the data
"""
import io
import sys
import numpy as np
import tkinter as tk
from scipy.special import *
from scipy.optimize import *
import matplotlib.pyplot as plt
from tkinter import Toplevel, messagebox


def open_command_window(root, dataframes, fit_results, logger):
    ''' 
    Opens an interactive Python shell to run commands on the data and view the output.

    Parameters
    ----------
    root : instance of TK class from tkinter
        toplevel Tk widget, main window of the application
    dataframes : list
        list of loaded files, each file is a pandas dataframe
    fit_results : dict
        dictionary to store the results
    logger : instance of logging.getLogger
        logger of the app
    '''

    if not dataframes:
        messagebox.showerror("Errore", "Non ci sono dati caricati!")
        return

    # Create a new window
    command_window = Toplevel(root)
    command_window.title("Shell Interattiva Python")
    command_window.geometry("800x600")

    tk.Label(command_window, text="Shell Python interattiva:", font=("Helvetica", 12)).pack(pady=5)

    # Text area for input/output
    shell_text = tk.Text(command_window, wrap="word", height=30, width=80)
    shell_text.pack(pady=5, padx=10)
    shell_text.insert("end", ">>> ")  # Initial prompt

    # Local dictionary to store generated variables
    local_vars = {}

    # Populate `local_vars` with DataFrame columns as NumPy arrays
    for idx, df in enumerate(dataframes):
        for column in df.columns:
            # The variable name will be the column name
            local_vars[column] = df[column].astype(float).values
    
    # Add the fit results
    local_vars = {**local_vars, **fit_results}

    # Command history variables
    command_history = []
    history_index = -1


    def execute_command(event=None):
        ''' Executes the entered command and displays input/output in the shell.
        '''
        global history_index
        # Get the command from the current line
        command_start = shell_text.index("insert linestart")
        command_end   = shell_text.index("insert lineend")
        command       = shell_text.get(command_start, command_end).strip(">>> ").strip()

        logger.info(f"Esecuzione del comando: {command}")

        # Save command to history
        if command :
            command_history.append(command)
            history_index = len(command_history)  # Reset history index

        # Redirect stdout and stderr
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = output_capture = io.StringIO()
        sys.stderr = output_capture

        try:
            # Run the command
            exec(command, globals(), local_vars)
            output = output_capture.getvalue()

        except Exception as e:
            output = f"Errore: {str(e)}\n"

        finally:
            # Restore original stdout and stderr
            sys.stdout, sys.stderr = old_stdout, old_stderr
        
        # Synchronize changes from local_vars to dataframes
        for idx, df in enumerate(dataframes):
            for column in df.columns:
                if column in local_vars:
                    modified_array = local_vars[column]
                    if not np.array_equal(df[column].values, modified_array):
                        df[column] = modified_array

        # View command and output
        shell_text.configure(state="normal")     # Re-enable the text area
        shell_text.insert("end", f"\n{output}")  # Add output
        shell_text.insert("end", ">>> ")         # and new prompt
        shell_text.see("end")                    # Scroll to the bottom

        # Move the cursor immediately after the new prompt
        shell_text.mark_set("insert", f"{shell_text.index('end-1c')}")  # Index of the cursor
        
        # Prevents the default behavior of adding a new carriage return 
        # caused by executing the command via enter key
        return "break"  
    
    def on_key_press(event):
        ''' Allows writing only after the >>> prompt and prevents unwanted changes.
        '''
        try:
            # Get the index of the last prompt
            last_prompt_index = shell_text.search(">>> ", "end-1c", backwards=True)
            if not last_prompt_index:  # If the prompt is not found
                return "break"         # Block any input

            # Compute the end position of the prompt
            prompt_end_index = f"{last_prompt_index} + 4c"
            cursor_index = shell_text.index("insert")

            # Prevents navigation before prompt
            if event.keysym in ("Left", "BackSpace") and shell_text.compare(cursor_index, "<=", prompt_end_index):
                return "break"

            # Block typing before the end of the prompt
            if shell_text.compare(cursor_index, "<", prompt_end_index):
                return "break"

            # Prevents prompt from being deleted with Delete key
            if event.keysym == "Delete" and shell_text.compare(cursor_index, "<=", prompt_end_index):
                return "break"

        except tk.TclError as e:
            # Log for any errors in the indexes
            logger.error(f"Errore in on_key_press: {e}")
            return "break"

        return  # Allow other events
    

    def navigate_history(event):
        ''' Navigate between commands with the up and down keys
        '''
        global history_index

        if event.keysym == "Up":      # Navigate back in history
            try :
                if history_index > 0:
                    history_index -= 1
                elif history_index == -1 and command_history:  # Initial case
                    history_index = len(command_history) - 1

            except NameError:
                pass

        elif event.keysym == "Down":  # Navigate forward in history
            try:
                if history_index < len(command_history) - 1:
                    history_index += 1
                elif history_index == len(command_history) - 1:
                    history_index = -1
            
            except NameError:
                pass

        # Show the current command in the shell
        try :
            if history_index >= 0:
                command = command_history[history_index]
            else:
                command = ""
        
        except NameError:
                command = ""

        # Replace the current command with the one in the history
        current_line_start = shell_text.index("insert linestart")
        shell_text.delete(current_line_start, "insert lineend")
        shell_text.insert(current_line_start, f">>> {command}")

        # Place the cursor at the end of the line
        shell_text.mark_set("insert", "end-1c")
        return "break"

    
    # Link Enter to Command Execution
    shell_text.bind("<Return>", execute_command)

    # Block typing before prompt
    shell_text.bind("<KeyPress>", on_key_press)

    # Link arrow keys to history navigation
    shell_text.bind("<Up>", navigate_history)
    shell_text.bind("<Down>", navigate_history)

    shell_text.focus_set()                   # Initial focus
    shell_text.mark_set("insert", "end-1c")  # Place the cursor at the prompt
