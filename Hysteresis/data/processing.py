"""
Code that contains some standard operations to do on the data.
"""
import numpy as np
import tkinter as tk
from tkinter import messagebox

#==============================================================================================#
# Function to normalize curves in the interval [-1, 1]                                         #
#==============================================================================================#

def norm(plot_data, count_plot, number_plots, selected_pairs, dataframes, plot_customizations, logger):
    '''
    Cycle normalization function.
    For each cycle the procedure implemented is the following:

    1) Compute the initial and final average values of the first and last 5 points of each branch.
    2) Reconcile the average values to correct any inconsistencies in direction.
       If both branches grow or decrease in a coherent way, the averages of the same
       branch are averaged. Otherwise, the "cross-branch" average is averaged.
    3) Compute the shift and the amplitude of the cycle.
    4) Normalize the branches so that the cycle is centered and with unit amplitude.

    Parameters
    ----------
    plot_data : callable
        function to plot data called in order to
        immediately make the plot after the changes made
    count_plot : list
        list of one element, a flag to update the same plot
    numer_plots : list
        list of one element, index of the current plot
    selected_pairs : list
        list of columns to plot
    dataframes : list
        list of loaded files, each file is a pandas dataframe
    plot_customizations : dict
        dictionary to save users customizations
    logger : instance of logging.getLogger
        logger of the app
    '''

    Y = []
    for df_choice, _, y_var in selected_pairs:
        df_idx = int(df_choice.get().split(" ")[1]) - 1  # Index of selected file
        y_col = y_var.get()
        y = dataframes[df_idx][y_col].astype(float).values
        Y.append(y)
    
    N_Y = []
    for y1, y2 in zip(Y[0::2], Y[1::2]):
        ell_up = y1
        ell_dw = y2

        # Calculate mean values ​​for normalization
        aveup1 = np.mean(ell_up[:5])
        aveup2 = np.mean(ell_up[-5:])
        avedw1 = np.mean(ell_dw[:5])
        avedw2 = np.mean(ell_dw[-5:])

        if ((aveup1 > aveup2 and avedw1 > avedw2) or (aveup1 < aveup2 and avedw1 < avedw2)):
            aveup1 = (aveup1 + avedw1) * 0.5
            avedw1 = (aveup2 + avedw2) * 0.5
        else:
            aveup1 = (aveup1 + avedw2) * 0.5
            avedw1 = (aveup2 + avedw1) * 0.5

        v_shift     =    (aveup1 + avedw1) * 0.5
        v_amplitude = abs(aveup1 - avedw1) * 0.5

        # Normalize the data
        ell_up_normalized = (ell_up - v_shift) / v_amplitude
        ell_dw_normalized = (ell_dw - v_shift) / v_amplitude
        N_Y.append(ell_up_normalized)
        N_Y.append(ell_dw_normalized)
    
    # Update normalized data in DataFrames
    for (df_choice, _, y_column), n_y in zip(selected_pairs, N_Y):
        
        df_idx     = int(df_choice.get().split(" ")[1]) - 1
        y_col_name = y_column.get()
        
        logger.info(f"Normalizzazione applicata alle colonne {y_col_name}.")
        dataframes[df_idx][y_col_name] = n_y

    plot_data(count_plot, number_plots, selected_pairs, dataframes, plot_customizations, logger)


#==============================================================================================#
# Function to close cycles                                                                     #
#==============================================================================================#

def close(root, plot_data, count_plot, number_plots, selected_pairs, dataframes, plot_customizations, logger):
    '''
    Function to manage the window to select the specific cycle to close.

    Parameters
    ----------
    root : instance of TK class from tkinter
        toplevel Tk widget, main window of the application
    plot_data : callable
        function to plot data called in order to
        immediately make the plot after the changes made
    count_plot : list
        list of one element, a flag to update the same plot
    number_plots : list
        list of one element, index of the current plot
    selected_pairs : list
        list of columns to plot
    dataframes : list
        list of loaded files, each file is a pandas dataframe
    plot_customizations : dict
        dictionary to save users customizations
    logger : instance of logging.getLogger
        logger of the app
    '''
    operation_window = tk.Toplevel(root)
    operation_window.title("Chiudi loop")

    file_choice = tk.StringVar()
    selected_columns = {}  # Dictionary for tracking column selections

    # Dropdown to choose file
    tk.Label(operation_window, text="Seleziona il file:").pack(pady=5)
    file_menu = tk.OptionMenu(operation_window, file_choice, *[f"File {i + 1}" for i in range(len(dataframes))])
    file_menu.pack()

    def update_column_selection(*args):
        ''' Updates the column list based on the selected file, excluding the x-axis.
        '''
        # Remove all existing column widgets
        for widget in operation_window.pack_slaves():
            if isinstance(widget, tk.Checkbutton):
                widget.destroy()

        if not file_choice.get():
            return

        selected_idx = int(file_choice.get().split(" ")[1]) - 1
        df = dataframes[selected_idx]  # The selected DataFrame
        num_cols = len(df.columns)     # Total number of columns in the DataFrame

        # Determine the columns of the x-axis based on the number of columns. 
        # This is based on the reasonable assumption that the
        # quantities are loaded in pairs to form the entire cycle
        if num_cols >= 8:
            x_columns = [df.columns[0], df.columns[4]]  # First and fifth columns
        elif num_cols == 6:
            x_columns = [df.columns[0], df.columns[3]]  # First and fourth columns
        elif num_cols == 4:
            x_columns = [df.columns[0], df.columns[2]]  # First and third column
        else:
            pass # The minimum value for a whole cycle is 4 columns

        # Create checkboxes for columns, excluding x-axis ones
        for col in df.columns:
            if col in x_columns:
                continue  # Skip x-axis columns

            selected_columns[col] = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(operation_window, text=col, variable=selected_columns[col])
            cb.pack(anchor="w")


    file_choice.trace_add("write", update_column_selection)

    tk.Button(operation_window, text="Applica",
              command=lambda : apply_close(plot_data, file_choice, selected_columns, count_plot,
                                           selected_pairs, dataframes, plot_customizations,
                                           logger, number_plots)
            ).pack(pady=10)
    
    tk.Label(operation_window,
             text="Selezionare la coppia (una alla volta) di curve da chiudere:"
            ).pack(pady=5)


def apply_close(plot_data, file_choice, selected_columns, count_plot,
                selected_pairs, dataframes, plot_customizations, logger,
                number_plots):
    '''
    Function that corrects the effects of instrumental drift and closes the loop.

    A gradual correction is applied to the data to reduce the misalignments
    at the ends of the loop, caused precisely by instrumental drift.

    For each loop the procedure is:
    
    1) Calculate the difference in absolute value between the initial and final values of the branches.
    2) Determine which difference (initial or final) is dominant.
    3) Apply a linear correction to reduce the misalignment:
        This correction is applied only on the dominant difference and its intensity
        decreases linearly while iterating on the points of the loop:
        - The values of the increasing branch are incremented or decremented.
        - The values of the decreasing branch are corrected symmetrically.
    
    Parameters
    ----------
    plot_data : callable
        function to plot data called in order to
        immediately make the plot after the changes made
    file_choice : instance of tkinter.StringVar
        variable to store the selected file
    selected_columns : dict
        coloumns , that form the loop, to close
    count_plot : list
        list of one element, a flag to update the same plot
    selected_pairs : list
        list of columns to plot
    dataframes : list
        list of loaded files, each file is a pandas dataframe
    plot_customizations : dict
        dictionary to save users customizations
    logger : instance of logging.getLogger
        logger of the app
    number_plots : list
        list of one element, index of the current plot
    '''
    try:
        if not file_choice.get():
            messagebox.showerror("Errore", "Devi selezionare un file!")
            return

        selected_idx = int(file_choice.get().split(" ")[1]) - 1
        df = dataframes[selected_idx]  # The selected DataFrame

        # Filter selected columns
        selected_cols = [col for col, is_selected in selected_columns.items() if is_selected.get()]
        if not selected_cols:
            messagebox.showerror("Errore", "Devi selezionare la coppia di dati che crea il ciclo")
            return
        if len(selected_cols) == 1:
            messagebox.showerror("Errore", "Devi selezionare la coppia di dati che crea il ciclo")
            return
        
        # Close the loop
        N_Y = []
        for col1, col2 in zip(selected_cols[0::2], selected_cols[1::2]):
            ell_up = df[col1].astype(float).values
            ell_dw = df[col2].astype(float).values

            num = len(ell_up)
            dy_start = abs(ell_up[0] - ell_dw[0])
            dy_stop = abs(ell_up[-1] - ell_dw[-1])

            if dy_start > dy_stop:
                if ell_up[0] > ell_dw[0]:
                    for i in range(num):
                        ell_up[i] -= (0.5 * (num - 1 - i) * dy_start) / (num - 1)
                        ell_dw[i] += (0.5 * (num - 1 - i) * dy_start) / (num - 1)
                else:
                    for i in range(num):
                        ell_up[i] += (0.5 * (num - 1 - i) * dy_start) / (num - 1)
                        ell_dw[i] -= (0.5 * (num - 1 - i) * dy_start) / (num - 1)

            if dy_start < dy_stop:
                if ell_up[-1] > ell_dw[-1]:
                    for i in range(num - 1, -1, -1):
                        ell_up[i] -= (0.5 * i * dy_stop) / (num - 1)
                        ell_dw[i] += (0.5 * i * dy_stop) / (num - 1)
                else:
                    for i in range(num - 1, -1, -1):
                        ell_up[i] += (0.5 * i * dy_stop) / (num - 1)
                        ell_dw[i] -= (0.5 * i * dy_stop) / (num - 1)

            N_Y.append(ell_up)
            N_Y.append(ell_dw)

        # Update normalized data in the selected DataFrame
        for col, n_y in zip(selected_cols, N_Y):
            df[col] = n_y
            logger.info(f"Chiusura del ciclo applicata a {col}.")

        plot_data(count_plot, number_plots, selected_pairs, dataframes, plot_customizations, logger)

        messagebox.showinfo("Successo", f"Operazione applicata su File {selected_idx + 1}!")
    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante l'operazione: {e}")

#==============================================================================================#
# Function to invert axis                                                                      #
#==============================================================================================#

def apply_inversion(axis, file_choice, selected_pairs, dataframes, logger,
                    plot_data, count_plot, number_plots, plot_customizations):
    '''
    Function to invert the x or y axis of the selected file.

    Parameters
    ----------
    axis : str
        axis to invert, can be "x", "y" or "both"
    file_choice : instance of tkinter.StringVar
        variable to store the selected file
    selected_pairs : list
        list of columns to plot
    dataframes : list
        list of loaded files, each file is a pandas dataframe
    logger : instance of logging.getLogger
        logger of the app
    plot_data : callable
        function to plot data called in order to
        immediately make the plot after the changes made
    count_plot : list
        list of one element, a flag to update the same plot
    number_plots : list
        list of one element, index of the current plot
    plot_customizations : dict
        dictionary to save users customizations
    '''
    try:
        if not file_choice.get():
            messagebox.showerror("Errore", "Devi selezionare un file!")
            return

        selected_idx = int(file_choice.get().split(" ")[1]) - 1
        df = dataframes[selected_idx]

        for _, x_var, y_var in selected_pairs:
            if axis in ("x", "both"):
                x_col = x_var.get()
                if x_col in df.columns:
                    df[x_col] = df[x_col].astype(float) * -1
                    logger.info(f"Inversione asse x -> colonna {x_col}.")

            if axis in ("y", "both"):
                y_col = y_var.get()
                if y_col in df.columns:
                    df[y_col] = df[y_col].astype(float) * -1
                    logger.info(f"Inversione asse y -> colonna {y_col}.")

        plot_data(count_plot, number_plots, selected_pairs, dataframes, plot_customizations, logger)
        messagebox.showinfo("Successo", f"Inversione asse {axis.upper()} applicata su File {selected_idx + 1}!")

    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante l'inversione: {e}")


def inv_x(root, plot_data, count_plot, number_plots, selected_pairs, dataframes, plot_customizations, logger):
    ''' 
    Window to select a file and invert the x-axis.

    Parameters
    ----------
    root : instance of TK class from tkinter
        toplevel Tk widget, main window of the application
    plot_data : callable
        function to plot data called in order to
        immediately make the plot after the changes made
    count_plot : list
        list of one element, a flag to update the same plot
    number_plots : list
        list of one element, index of the current plot
    selected_pairs : list
        list of columns to plot
    dataframes : list
        list of loaded files, each file is a pandas dataframe
    plot_customizations : dict
        dictionary to save users customizations
    logger : instance of logging.getLogger
        logger of the app
    '''
    operation_window = tk.Toplevel(root)
    operation_window.title("Inverti Asse x")
    file_choice = tk.StringVar()

    tk.Label(operation_window, text="Seleziona il file:").pack(pady=5)
    tk.OptionMenu(operation_window, file_choice, *[f"File {i + 1}" for i in range(len(dataframes))]).pack()

    tk.Button(operation_window, text="Applica",
                command=lambda: apply_inversion(
                    "x", file_choice, selected_pairs, dataframes, logger,
                    plot_data, count_plot, number_plots, plot_customizations)
                ).pack(pady=10)


def inv_y(root, plot_data, count_plot, number_plots, selected_pairs, dataframes, plot_customizations, logger):
    '''
    Window to select a file and invert the y-axis.

    Parameters
    ----------
    root : instance of TK class from tkinter
        toplevel Tk widget, main window of the application
    plot_data : callable
        function to plot data called in order to
        immediately make the plot after the changes made
    count_plot : list
        list of one element, a flag to update the same plot
    number_plots : list
        list of one element, index of the current plot
    selected_pairs : list
        list of columns to plot
    dataframes : list
        list of loaded files, each file is a pandas dataframe
    plot_customizations : dict
        dictionary to save users customizations
    logger : instance of logging.getLogger
        logger of the app
    '''
    operation_window = tk.Toplevel(root)
    operation_window.title("Inverti Asse Y")
    file_choice = tk.StringVar()

    tk.Label(operation_window, text="Seleziona il file:").pack(pady=5)
    tk.OptionMenu(operation_window, file_choice, *[f"File {i + 1}" for i in range(len(dataframes))]).pack()

    tk.Button(operation_window, text="Applica",
                command=lambda: apply_inversion(
                    "y", file_choice, selected_pairs, dataframes, logger,
                    plot_data, count_plot, number_plots, plot_customizations)
                ).pack(pady=10)

#==============================================================================================#
# Function to invert a single branch of the cycle                                              #
#==============================================================================================#

def inv_single_branch(root, plot_data, count_plot, number_plots,
                      selected_pairs, dataframes, plot_customizations, logger):
    '''
    GUI window to select a file and invert specific branches (columns)
    of a cycle by applying a sign inversion (-1).

    Parameters
    ----------
    root : instance of TK class from tkinter
        toplevel Tk widget, main window of the application
    plot_data : callable
        function to plot data called in order to
        immediately make the plot after the changes made
    count_plot : list
        list of one element, a flag to update the same plot
    number_plots : list
        list of one element, index of the current plot
    selected_pairs : list
        list of columns to plot
    dataframes : list
        list of loaded files, each file is a pandas dataframe
    plot_customizations : dict
        dictionary to save users customizations
    logger : instance of logging.getLogger
        logger of the app
    '''
    operation_window = tk.Toplevel(root)
    operation_window.title("Inverti Singolo Ramo")

    file_choice = tk.StringVar()
    selected_columns = {}  # Dictionary of {col_name: tk.BooleanVar}

    # File selection dropdown
    tk.Label(operation_window, text="Seleziona il file:").pack(pady=5)
    file_menu = tk.OptionMenu(
        operation_window, file_choice, *[f"File {i + 1}" for i in range(len(dataframes))]
    )
    file_menu.pack()

    def update_column_selection(*args):
        # Remove existing checkboxes
        for widget in operation_window.pack_slaves():
            if isinstance(widget, tk.Checkbutton):
                widget.destroy()

        if not file_choice.get():
            return

        selected_idx = int(file_choice.get().split(" ")[1]) - 1
        df = dataframes[selected_idx]

        for col in df.columns:
            selected_columns[col] = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(operation_window, text=col, variable=selected_columns[col])
            cb.pack(anchor="w")

    file_choice.trace_add("write", update_column_selection)

    # Apply button that directly calls the inversion
    tk.Button(
        operation_window,
        text="Applica",
        command=lambda: apply_column_inversion(
            file_choice=file_choice,
            selected_columns=selected_columns,
            dataframes=dataframes,
            logger=logger,
            plot_data=plot_data,
            count_plot=count_plot,
            number_plots=number_plots,
            selected_pairs=selected_pairs,
            plot_customizations=plot_customizations
        )
    ).pack(pady=10)

    tk.Label(
        operation_window,
        text="Seleziona le colonne da invertire:"
    ).pack(pady=5)

def apply_column_inversion(file_choice, selected_columns, dataframes, logger,
                           plot_data, count_plot, number_plots, selected_pairs,
                           plot_customizations):
    '''
    Inverts only the selected columns of a selected file.

    Parameters
    ----------
    file_choice : tk.StringVar
        Variable containing the selected file (e.g., "File 1")
    selected_columns : dict
        Dictionary mapping column names to tk.BooleanVar()
    dataframes : list
        list of loaded files, each file is a pandas dataframe
    logger : instance of logging.getLogger
        logger of the app
    plot_data : callable
        function to plot data called in order to
        immediately make the plot after the changes made
    count_plot : list
        list of one element, a flag to update the same plot
    number_plots : list
        list of one element, index of the current plot
    selected_pairs : list
        list of columns to plot
    plot_customizations : dict
        dictionary to save users customizations
    '''
    try:
        if not file_choice.get():
            messagebox.showerror("Errore", "Nessun file selezionato.")
            return

        idx = int(file_choice.get().split(" ")[1]) - 1
        df = dataframes[idx]

        selected_cols = [col for col, var in selected_columns.items() if var.get()]
        if not selected_cols:
            messagebox.showerror("Errore", "Seleziona almeno una colonna da invertire.")
            return

        for col in selected_cols:
            if col in df.columns:
                df[col] = df[col].astype(float) * -1
                logger.info(f"Inversione colonna {col} nel file {idx + 1}.")

        plot_data(count_plot, number_plots, selected_pairs, dataframes, plot_customizations, logger)
        messagebox.showinfo("Successo", f"Inversione applicata su: {', '.join(selected_cols)}")
    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante l'inversione: {e}")
