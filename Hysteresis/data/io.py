"""
Code to handle data input and output, i.e. loading and saving data
"""
import os
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, StringVar

from Hysteresis.data.show import loaded_files
from Hysteresis.utils.scroll import ScrollableFrame

#==============================================================================================#
# File upload functions                                                                        #
#==============================================================================================#

def load_files(app_instance):
    '''
    Function to upload one or more files chosen by the user.
    The code is currently designed to read data files created
    by labview that have the following structure:

    ::

        FieldUp	UpRot	UpEllipt	IzeroUp	FieldDw	DwRot	DwEllipt	IzeroDw
        MaxV 30.00	V_bias 0.00	Steps 180	Loops 10
        Sen1(mV) 5.0E-1	Sen2(mV) 2.0E-2	TC(ms) 10	Scaling 0.0E+0	ThetaPol 5.0	Polarization s
        Rot Ell Izero Parameters3.478239E-3	-1.249859E-2	3.036712E-1

        -2682.1	6.775420E-1	4.515580E-2	0.30287	-2665.8	6.798780E-1	4.842054E-2	0.30286
        -2668.2	6.778833E-1	4.509845E-2	0.30275	-2635.3	6.794771E-1	4.826985E-2	0.30291
        -2641.9	6.778411E-1	4.516041E-2	0.30290	-2605.8	6.798262E-1	4.843232E-2	0.30289

    This same structure will then be preserved when the data is saved
    to a new file, so that it can be reopened for further analysis.

    Parameters
    ----------
    app_instance : instance of MainApp from main_window.py
    '''
    
    root = app_instance.root
    
    if app_instance.logger is None:
        messagebox.showerror("Errore", "Impossibile iniziare l'analisi senza avviare il log")
        return

    file_paths = filedialog.askopenfilenames(
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if not file_paths:
        return

    for file_path in file_paths:
        try:
            # Reads the file and displays a secondary window to select columns
            with open(file_path, "r", encoding='utf-8') as f:
                header = f.readline().strip().split("\t")  # Assumes that columns are separated by tabs
            app_instance.logger.info(f"Apertura file {file_path}.")

            show_column_selection(app_instance, root, file_path, header)
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il caricamento del file: {file_path}\n{e}")

#==============================================================================================#

def show_column_selection(app_instance, root, file_path, header):
    '''
    Show a window to select columns and names.

    Parameters
    ----------
    app_instance : MainApp object
        instance of MainApp from main_window.py
    root : instance of TK class fro tkinter
        toplevel Tk widget, main window of the application
    file_path : string
        path of the file to read
    header : list
        first line of the file to select columns to read
    '''
    selection_window = tk.Toplevel(root)
    selection_window.title(f"Seleziona Colonne: {os.path.basename(file_path)}")
    selection_window.geometry("800x750")

    # Create a frame with a scrollbar for columns
    frame = tk.Frame(selection_window)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Usage
    description = (
        "Seleziona le colonne da caricare e assegna un nome, oppure lascia vuota la casella "
        "il nome assegnato di default sarà: nome file + nome colonna.\n"
        "Scorrere con la barra laterale per visualizzare i dati caricabili."
       )

    # Using Message to automatically fit text
    tk.Message(frame, text=description, width=780).pack()

    # Top Canvas for the top line
    top_canvas = tk.Canvas(frame, height=10)
    top_canvas.pack(fill="x")
    top_canvas.create_line(5, 5, 790, 5, fill="black", width=2)  # Horizontal line

    selected_columns = {}
    custom_names = {}

    def submit_selection():
        ''' Save the selection of columns and names.
        '''

        columns_to_load = [
            header[i]
            for i in range(len(header))
            if selected_columns.get(i).get()
        ]
        custom_column_names = [
            custom_names[i].get() or f"{os.path.splitext(os.path.basename(file_path))[0]}_{header[i]}"
            for i in range(len(header))
            if selected_columns.get(i).get()
        ]

        try:
            # Load the DataFrame and add it to the list
            df = pd.read_csv(file_path, sep="\t", nrows=3)
            app_instance.header_lines.append(df)

            df = pd.read_csv(file_path, sep="\t", usecols=columns_to_load)

            df.columns = custom_column_names
            df = df.drop([0, 1, 2])  # Ignore any extra lines of header
            
            app_instance.dataframes.append(df)

            app_instance.logger.info(f"Dal file: {file_path}, caricate le colonne: {columns_to_load}.")

            messagebox.showinfo("Successo", f"Dati caricati da {file_path}!")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il caricamento dei dati: {e}")

        selection_window.destroy()

    # Load the DataFrame to show the columns
    all_df = pd.read_csv(file_path, sep="\t")
    all_df = all_df.drop([0, 1, 2])  # Ignore any extra lines of header

    # I show the values ​​of the all_df columns in the upper
    # part of the window via a scrolling sub-window
    """canvas = tk.Canvas(frame)
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")

    inner_frame = tk.Frame(canvas)
    inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner_frame, anchor="nw")

    # I show the values ​​of the columns of all_df as if I were seeing a table
    for i, col_name in enumerate(all_df.columns):
        tk.Label(inner_frame, text=col_name).grid(row=0, column=i, sticky="w")
        
        # Box in which the numeric values ​​of the columns appear
        for j, value in enumerate(all_df[col_name].values):
            tk.Label(inner_frame, text=value).grid(row=j + 1, column=i, sticky="w")

    
    canvas.configure(yscrollcommand=scrollbar.set)
    """
    # Usa ScrollableFrame per i dati tabellari
    scrollable = ScrollableFrame(frame)
    scrollable.pack(fill="both", expand=True)

    # Ottieni il frame scrollabile vero e proprio
    inner_frame = scrollable.scrollable_frame

    # Visualizza i dati come tabella
    for i, col_name in enumerate(all_df.columns):
        tk.Label(inner_frame, text=col_name, font=("Arial", 10, "bold")).grid(row=0, column=i, sticky="w", padx=5)
        for j, value in enumerate(all_df[col_name].values):
            tk.Label(inner_frame, text=value, font=("Courier", 9)).grid(row=j + 1, column=i, sticky="w", padx=5)

    # Bottom Canvas for the bottom line
    bottom_canvas = tk.Canvas(selection_window, height=10)
    bottom_canvas.pack(fill="x")
    bottom_canvas.create_line(10, 5, 790, 5, fill="black", width=2)  # Linea orizzontale

    # Interface to select columns
    tk.Label(selection_window, text="Seleziona le colonne da caricare:").pack(anchor="w")

    for i, col_name in enumerate(header):
    
        selected_columns[i] = tk.BooleanVar(value=True)
        custom_names[i] = tk.StringVar()

        frame = tk.Frame(selection_window)
        frame.pack(anchor="w")

        tk.Checkbutton(frame, text=col_name, variable=selected_columns[i]).pack(side="left")
        tk.Entry(frame, textvariable=custom_names[i], width=20).pack(side="left")

    tk.Button(selection_window, text="Carica", command=submit_selection).pack(pady=10)

#==============================================================================================#
# Functions to save modified data                                                              #
#==============================================================================================#

def save_header(app_instance, df, file_path):
    '''
    Save the header in the final text file,
    to provide compatibility in case you want to
    reopen it for further analysis.

    Parameters
    ----------
    app_instance : MainApp object
        instance of MainApp from main_window.py
    df : pandas dataframe
        dataframe containing only the header of the data file
    file_path : string
        path of the file to save
    '''
    try:
        with open(file_path, "w", encoding='utf-8') as f:
            # Write the names of the columns
            f.write("\t".join(df.columns) + "\n")
            
            # Writes every row of the DataFrame, ignoring NaNs
            for _, row in df.iterrows():
                line = "\t".join(row.astype(str).fillna("").replace("nan", "").values)
                f.write(line.strip() + "\n")
        app_instance.logger.info(f"File salvato correttamente in: {file_path}")

    except Exception as e:
        app_instance.logger.info(f"Errore durante il salvataggio: {e}")

#==============================================================================================#

def save_modified_data(app_instance):
    ''' 
    Allows you to choose the file and data to save, with the related headers.

    Parameters
    ----------
    app_instance : MainApp object
        instance of MainApp from main_window.py
    '''
    root         = app_instance.root
    dataframes   = app_instance.dataframes

    if not dataframes:
        messagebox.showerror("Errore", "Non ci sono dati caricati!")
        return

    save_window = Toplevel(root)
    save_window.title("Salva Dati Modificati")
    save_window.geometry("500x400")

    # Variables for selection
    selected_df = StringVar(value=f"File 1")  # File selected by default

    tk.Label(save_window, text="Seleziona il file da salvare:").pack(pady=5)
    file_menu = tk.OptionMenu(save_window, selected_df, *[f"File {i + 1}" for i in range(len(dataframes))])
    file_menu.pack(pady=5)

    description = (
        "Selezionare i file contenente i dati da salvare, se si vuole essere sicuri si può "
        "verificare quali siano sati i file caricati vedendo anche i rispettivi dati.\n"
        "Qualora fossero sate caricate meno colonne delle 8 disponibili verrano aggiunte "
        "delle colonne di zeri per mantenere la compatibilià."     
    )
    
    # Using Message to automatically fit text
    tk.Message(save_window, text=description, width=480).pack()

    tk.Button(save_window, text="Salva",
              command=lambda : save_to_file(selected_df, app_instance, save_window)
             ).pack(pady=20)

    tk.Button(save_window, text="Visualizza File Caricati",
              command=lambda : loaded_files(app_instance)
             ).pack(pady=10)


def save_to_file(selected_df, app_instance, save_window):
    '''
    Save the selected data to a new text file.
    If fewer columns than the 8 available are loaded,
    columns of zeros will be added to maintain compatibility.

    Parameters
    ----------
    selected_df : StringVar
        variable containing the name of the selected file
    app_instance : MainApp object
        instance of MainApp from main_window.py
    save_window : Toplevel object
        window to close after saving the data
    '''

    dataframes   = app_instance.dataframes
    header_lines = app_instance.header_lines
   
    try:
        df_idx = int(selected_df.get().split(" ")[1]) - 1
        df = dataframes[df_idx]
       
        # Retrieve the header of the selected file

        header = header_lines[df_idx]
 
        # Dialog to choose the name of the new file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"dati_modificati_file_{df_idx + 1}.txt",
        )
    
        if not file_path:
            return 

        save_header(app_instance, header, file_path)
        # Save the data in the new file in text format
        with open(file_path, "a", encoding='utf-8') as f:

            data = np.array(df)
            rows, cols = data.shape

            # Create a zero matrix with 8 columns
            expanded_data = np.zeros((rows, 8))

            if cols == 4:
                # Intersperses each original column with a column of zeros
                expanded_data[:, ::2] = data
            elif cols == 6:
                # Inserts a column of zeros as the fourth and final column
                expanded_data[:, :3] = data[:, :3]
                expanded_data[:, 4:7] = data[:, 3:]
            elif cols == 8:
                # All data
                expanded_data = data

            np.savetxt(f, expanded_data, delimiter="\t", fmt="%s")

        messagebox.showinfo("Salvataggio completato", f"Dati salvati in {os.path.basename(file_path)}")
        save_window.destroy()
    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante il salvataggio: {e}")