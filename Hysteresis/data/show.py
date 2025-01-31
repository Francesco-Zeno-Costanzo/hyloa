'''
Code to see which files have been uploaded and which variables we have
'''
import tkinter as tk
from tkinter import Toplevel, messagebox

#==============================================================================================#
# Function to see all uploaded data                                                            #
#==============================================================================================#

def loaded_files(app_instance):
    ''' 
    Opens a window to view the uploaded files and their columns.

    Parameters
    ----------
    app_instance : MainApp object
        instance of MainApp from main_window.py
    '''

    root       = app_instance.root
    dataframes = app_instance.dataframes

    if not dataframes:
        messagebox.showerror("Errore", "Non ci sono file caricati!")
        return

    # Create a new window
    file_window = Toplevel(root)
    file_window.title("File Caricati")
    file_window.geometry("500x400")

    tk.Label(file_window, text="File Caricati e Colonne", font=("Helvetica", 14)).pack(pady=10)

    # Text area to show files and columns
    text_area = tk.Text(file_window, wrap="word", height=20, width=60)
    text_area.pack(pady=10, padx=10)

    # Add file and column information
    for idx, df in enumerate(dataframes):
        text_area.insert("end", f"File {idx + 1}:")
        text_area.insert("end", f"Colonne: {', '.join(df.columns)}\n\n")

    # Make the text area non-editable
    text_area.configure(state="disabled")