"""
Code to manage the plot window
"""
import numpy as np
import tkinter as tk
from scipy.special import *
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from tkinter import messagebox, Toplevel, StringVar, ttk, DoubleVar
from matplotlib import markers, lines as mlines, colors as mcolors

from Hysteresis.utils.scroll import ScrollableFrame
from Hysteresis.gui.command_window import open_command_window
from Hysteresis.data.processing import norm, close, inv_x, inv_y, inv_single_branch

#==============================================================================================#
# Main function for managing the plot window                                                   #
#==============================================================================================#

def open_plot_window(app_instance):
    '''
    Main function for managing the plot window

    Parameters
    ----------
    app_instance : MainApp object
        instance of MainApp from main_window.py
    '''
    
    # I unpack all the necessary application instance attributes
    root                = app_instance.root
    dataframes          = app_instance.dataframes
    count_plot          = [app_instance.count_plot]
    plot_customizations = app_instance.plot_customizations
    fit_results         = app_instance.fit_results
    logger              = app_instance.logger
    number_plots        = [app_instance.number_plots]
    list_figures        = app_instance.list_figures
    """
    Count_plot is in a list because it needs to change as the various plots
    are updated, but it is an integer, so it is immutable; 
    so we put it in a mutable container, so we will not have problems
    when we make the closure for the function call.
    Same for numebr_plots
    """
    if not dataframes:
        messagebox.showerror("Errore", "Non ci sono dati caricati!")
        return

    plot_window = tk.Toplevel(root)
    plot_window.geometry("650x300")
    plot_window.title(f"Pannello di controllo grafico figura {number_plots[0]}")

    selected_pairs = []  # List for selected pairs (file, x, y)

    # Top frame for buttons
    button_frame_0 = tk.Frame(plot_window)
    button_frame_0.pack(anchor="w", pady=10)

    # Button to create the plot
    tk.Button(button_frame_0, text="Crea Grafico",
              command=lambda : plot_data(count_plot, number_plots, selected_pairs,
                                         dataframes, plot_customizations, logger,
                                         list_figures)
             ).pack(side="left", padx=5)
    
    # Button to customize the plot style
    tk.Button(button_frame_0, text="Personalizza Stile",
              command=lambda : customize_plot_style(root, plot_customizations,
                                                    number_plots, list_figures)
             ).pack(side="left", padx=5)
    
    # Button to open the curve fitting window
    tk.Button(button_frame_0, text="Curve Fitting",
              command=lambda : open_curve_fitting_window(root, dataframes,
                                                         fit_results, number_plots,
                                                         logger, list_figures)
             ).pack(side="left", padx=5)
    
    # Button to open the command window
    tk.Button(button_frame_0, text="Esegui Comandi",
              command=lambda : open_command_window(root, dataframes, fit_results, logger)
             ).pack(side="left", pady=5)

    # Bottom frame for buttons
    button_frame_1 = tk.Frame(plot_window)
    button_frame_1.pack(anchor="w", pady=10)

    # Button to normalize data
    tk.Button(button_frame_1, text="Normalize",
              command=lambda : norm(plot_data, count_plot, number_plots, selected_pairs,
                                    dataframes, plot_customizations, logger,
                                    list_figures)
             ).pack(side="left", padx=5)
    
    # Button to close the loop
    tk.Button(button_frame_1, text="Close loop",
              command=lambda : close(root, plot_data, count_plot, number_plots,
                                     selected_pairs, dataframes, plot_customizations,
                                     logger, list_figures)
             ).pack(side="left", padx=5)
    
    # Button to invert the fields
    tk.Button(button_frame_1, text="Inverti Campi", 
              command=lambda : inv_x(root, plot_data, count_plot, number_plots,
                                     selected_pairs, dataframes, plot_customizations,
                                     logger, list_figures)
             ).pack(side="left", padx=5)
    
    # Button to invert the y-axis
    tk.Button(button_frame_1, text="Inverti asse y",
              command=lambda : inv_y(root, plot_data, count_plot, number_plots,
                                     selected_pairs, dataframes, plot_customizations,
                                     logger, list_figures)
             ).pack(side="left", padx=5)
    
     # Button to invert a single branch
    tk.Button(button_frame_1, text="Inverti ramo",
              command=lambda : inv_single_branch(root, plot_data, count_plot, number_plots,
                                                 selected_pairs, dataframes, plot_customizations,
                                                 logger, list_figures)
             ).pack(side="left", padx=5)

    # Label for selecting couples
    tk.Label(plot_window, text="Seleziona le coppie di colonne (x, y):").pack()

    # Button to add pairs
    tk.Button(plot_window, text="Aggiungi Coppia x-y",
              command=lambda : add_pair(selector_frame, dataframes, selected_pairs)
              ).pack(pady=5)
    
    # Scrollable frame for pair selectors
    scrollable = ScrollableFrame(plot_window)
    scrollable.pack(expand=True, fill="both", padx=10, pady=10)

    # Save a reference to the frame where pairs will be added
    selector_frame = scrollable.scrollable_frame

    # Add the first column pair selector
    add_pair(selector_frame, dataframes, selected_pairs)


    return plot_window

    
#==============================================================================================#
# Function to add data to plot                                                                 #
#==============================================================================================#

def add_pair(plot_window, dataframes, selected_pairs):
    ''' 
    Adds a new row to select a pair (x, y)

    Parameters
    ----------
    plot_window : instance of tk.Toplevel
        window of the plot
    dataframes : list
        list of loaded files, each file is a pandas dataframe
    selected_pairs : list
        list of columns to plot
    '''
    pair_frame = tk.Frame(plot_window)
    pair_frame.pack(anchor="w", pady=5)

    df_choice = tk.StringVar()
    x_column = tk.StringVar()
    y_column = tk.StringVar()

    # Dropdown to choose file
    tk.Label(pair_frame, text="File:").pack(side="left", padx=5)
    file_menu = tk.OptionMenu(pair_frame, df_choice, *[f"File {i + 1}" for i in range(len(dataframes))])
    file_menu.variable = df_choice  # 👈 permette l'accesso esterno alla variabile
    #file_menu = tk.OptionMenu(pair_frame, df_choice, *[f"File {i + 1}" for i in range(len(dataframes))])
    file_menu.pack(side="left")

    if not hasattr(plot_window, "file_menus"):
        plot_window.file_menus = []
    plot_window.file_menus.append(file_menu)


    # Dropdown by columns x
    tk.Label(pair_frame, text="x:").pack(side="left", padx=5)
    x_menu = tk.OptionMenu(pair_frame, x_column, "")
    x_menu.pack(side="left")

    # Dropdown by columns y
    tk.Label(pair_frame, text="y:").pack(side="left", padx=5)
    y_menu = tk.OptionMenu(pair_frame, y_column, "")
    y_menu.pack(side="left")

    def update_columns(*args):
        ''' Update columns based on selected file
        '''
        try:
            df_idx = int(df_choice.get().split(" ")[1]) - 1  # Index of the selected file
            columns = list(dataframes[df_idx].columns)
            x_column.set(columns[0])
            y_column.set(columns[0])

            # Update dropdown menus with columns from the selected DataFrame
            x_menu["menu"].delete(0, "end")
            y_menu["menu"].delete(0, "end")
            for col in columns:
                x_menu["menu"].add_command(label=col, command=lambda value=col: x_column.set(value))
                y_menu["menu"].add_command(label=col, command=lambda value=col: y_column.set(value))
        except Exception:
            pass

    # Link column update to file selection
    df_choice.trace_add("write", update_columns)

    # Set default file
    df_choice.set(f"File 1")
    
    # Load columns from the first file immediately
    update_columns()

    # Add to couples list
    selected_pairs.append((df_choice, x_column, y_column))
    return file_menu


#==============================================================================================#
# Function that creates the plot with the chosen data                                          #
#==============================================================================================#

def plot_data(count_plot, number_plots, selected_pairs, dataframes, plot_customizations, logger, list_figures):
    '''
    Create the chart with the selected pairs.
    If there are customizations for a given file use those,
    otherwise, use the default choices.

    Parameters
    ----------
    count_plot : list
        list of one element, a flag to update the same plot
    numer_plots : list
        list of one element, the number of the current plot
    selected_pairs : list
        list of columns to plot
    dataframes : list
        list of loaded files, each file is a pandas dataframe
    plot_customizations : dict
        dictionary to save users customizations
    logger : instance of logging.getLogger
        logger of the app
    list_figures : list
        list to store the figures
    '''

    fig = plt.figure(number_plots[0], figsize=(10, 6))
    list_figures.append(fig)

    if count_plot[0] >0 :
        plt.cla()
    try:

        count_plot[0] += 1

        X = []
        Y = []
        for df_choice, x_var, y_var in selected_pairs:
            df_idx = int(df_choice.get().split(" ")[1]) - 1  # Index of the selected file
            x_col = x_var.get()
            y_col = y_var.get()

            if not x_col or not y_col:
                messagebox.showerror("Errore", "Devi selezionare tutte le coppie di colonne!")
                return

            X.append(dataframes[df_idx][x_col].astype(float).values)
            Y.append(dataframes[df_idx][y_col].astype(float).values)
            logger.info(f"Plot di: {x_col} vs {y_col}")

        if not plot_customizations:
            col =  plt.cm.jet(np.linspace(0, 1, len(X)))
            for i in range(0, len(X), 2):
                
                plt.plot(X[i],   Y[i],   color=col[i], marker="o", label=f"Ciclo {i//2 + 1}")
                plt.plot(X[i+1], Y[i+1], color=col[i], marker="o")

        else :
            # Plot the lines as before
            for i, (x, y) in enumerate(zip(X, Y)):
                if i % 2 == 0:
                    line1, = plt.plot(x, y, label=f"Ciclo {i // 2 + 1}")
                else:
                    line2, = plt.plot(x, y)

               # Apply saved customization
                customization = plot_customizations.get(i // 2, {})

                line1.set_color(customization.get("color", line1.get_color()))
                line1.set_marker(customization.get("marker", line1.get_marker()))
                line1.set_linestyle(customization.get("linestyle", line1.get_linestyle()))
                line1.set_label(customization.get("label", f"Ciclo {i // 2 + 1}"))

                if i % 2 == 1:  # Second branch of the cycle
                    line2.set_color(customization.get("color", line2.get_color()))
                    line2.set_marker(customization.get("marker", line2.get_marker()))
                    line2.set_linestyle(customization.get("linestyle", line2.get_linestyle()))
                    line2.set_label("_nolegend_")  # Prevent duplicate in legend

        plt.xlabel("H [Oe]", fontsize=15)
        plt.ylabel(r"M/M$_{sat}$", fontsize=15)
        plt.legend()
        plt.grid()
        plt.show()

    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante la creazione del grafico: {e}")

#==============================================================================================#
# Function to customize the style of the plot                                                  #
#==============================================================================================#

def customize_plot_style(root, plot_customizations, number_plots, list_figures):
    ''' 
    Opens a window to customize color, marker, and line style of a cycle in the plot.

    Parameters
    ----------
    root : instance of TK class from tkinter
        toplevel Tk widget, main window of the application
    plot_customizations : dict
        dictionary to save users customizations
    number_plots : list
        list of one elemente, number of the current plot
    list_figures : list
        list to store the figures
    '''
    
    if not plt.get_fignums():
        messagebox.showerror("Errore", "Nessun grafico aperto! Crea prima un grafico.")
        return

    fig = list_figures[number_plots[0] - 1]
    ax = fig.gca()
    lines = ax.lines
    if not lines:
        messagebox.showerror("Errore", "Nessuna linea presente nel grafico!")
        return

    style_window = Toplevel(root)
    style_window.title("Personalizza Stile Grafico")
    style_window.geometry("420x450")
    style_window.resizable(False, False)

    # All possible options
    colors       = list(mcolors.TABLEAU_COLORS) + list(mcolors.CSS4_COLORS)
    markers_list = [m for m in markers.MarkerStyle.markers.keys() if isinstance(m, str) and len(m) == 1]
    linestyles   = list(mlines.Line2D.lineStyles.keys())   
   
    cycles         = []
    label_to_index = {}
    for i in range(0, len(lines), 2):
        label = plot_customizations.get(i // 2, {}).get("label", f"Ciclo {i // 2 + 1}")
        cycles.append(label)
        label_to_index[label] = i // 2


    # Variables for selection
    cycle_var     = StringVar(value=cycles[0])
    color_var     = StringVar(value=colors[0])
    marker_var    = StringVar(value=markers_list[0])
    linestyle_var = StringVar(value='-')
    label_var     = StringVar(value=cycle_var.get())


    def labeled_dropdown(parent, label, variable, options):
        ttk.Label(parent, text=label).pack(pady=(10, 2))
        ttk.Combobox(parent, textvariable=variable, values=options, state="readonly").pack(pady=(0, 5), fill='x', padx=40)

    # Interface for customization
    ttk.Label(style_window, text="Personalizzazione Ciclo", font=("Helvetica", 14, "bold")).pack(pady=(15, 10))
    labeled_dropdown(style_window, "Ciclo", cycle_var, cycles)
    labeled_dropdown(style_window, "Colore", color_var, colors)
    labeled_dropdown(style_window, "Marker", marker_var, markers_list)
    labeled_dropdown(style_window, "Stile linea", linestyle_var, linestyles)

    # Entry for custom label
    ttk.Label(style_window, text="nome in legenda").pack(pady=(10, 2))
    ttk.Entry(style_window, textvariable=label_var).pack(pady=(0, 5), fill='x', padx=40)


    def apply_style():
        try:
            idx   = label_to_index[cycle_var.get()]
            line1 = lines[idx * 2]
            line2 = lines[idx * 2 + 1]

            # Apply the changes
            for line in (line1, line2):
                line.set_color(color_var.get())
                line.set_marker(marker_var.get())
                line.set_linestyle(linestyle_var.get())

            line1.set_label(label_var.get() or cycle_var.get())
            line2.set_label("_nolegend_")

            # Save the changes
            plot_customizations[idx] = {
                "color":     color_var.get(),
                "marker":    marker_var.get(),
                "linestyle": linestyle_var.get(),
                "label":     label_var.get() or cycle_var.get(),
            }

            ax.legend()
            plt.draw()
            style_window.destroy()
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante l'applicazione dello stile:\n{e}")

    ttk.Button(style_window, text="Applica", command=apply_style).pack(pady=20)

#==============================================================================================#
# Curve fitting function                                                                       #
#==============================================================================================#

def open_curve_fitting_window(root, dataframes, fit_results, number_plots, logger, list_figures):
    '''
    Opens a window to configure the operations to be performed.

    Parameters
    ----------
    root : instance of TK class from tkinter
        toplevel Tk widget, main window of the application
    dataframes : list
        list of loaded files, each file is a pandas dataframe
    fit_results : dict
        dictionary to store the results
    number_plots : list
        list of one element, the number of the current plot
    logger : instance of logging.getLogger
        logger of the app
    list_figures : list
        list to store the figures
    '''
    if not dataframes:
        messagebox.showerror("Errore", "Non ci sono dati caricati!")
        return

    fit_window = Toplevel(root)
    fit_window.title("Curve Fitting")
    fit_window.geometry("700x600")

    # Variables 
    function_var       = StringVar(value="a*(x - b)") # Fit function
    x_start            = DoubleVar(value=0)           # Data start point
    x_end              = DoubleVar(value=1)           # Data end point
    initial_params_var = StringVar(value="1, 1")      # Initial parameters
    param_names_var    = StringVar(value="a, b")      # Fit function parameter names
    selected_df        = StringVar(value=f"File 1")   # File containing the data to be fitted
    selected_x_col     = StringVar()                  # x_data
    selected_y_col     = StringVar()                  # y_data


    # Usage
    description = (
        "La funzione di fit deve essere una funzione della variabile 'x' e "
        "i nomi dei parametri devono essere specificati nel campo apposito.\n"
        "Per stabilire il range basta la lettura del cursore sul grafico, i valori sono in basso a destra.\n"
        "In caso di non convergenza del fit conviene selezionare accuratamente i parametri iniziali.\n"
        "Se il fit non è andato a buon fine viene plottata la curva calcolata nei parametri inziali "
        "per aiutare nella regolazione degli stessi.\n"
        "Come PROMEMORIA, il ramo 'Up' è quello più a destra a meno che non si sia invertito l'asse x; "
        "in tal caso sarà quello a sinistra.\n"
        "ACTHUNG: la funzione va scritta in python, quindi ad esempio |x| è abs(x), x^2 è x**2, e tutte "
        "le altre funzioni vanno scritte con np. davanti i.e. np.cos(x), np.exp(x) fuorchè le funzioni speciali."
    )

    # Using Message to automatically fit text
    tk.Message(fit_window, text=description, width=680).pack()

    # Window layout
    frame_selection = tk.Frame(fit_window)
    frame_selection.pack(side="left", padx=10, pady=10)

    frame_parameters = tk.Frame(fit_window)
    frame_parameters.pack(side="left", padx=10, pady=10)


    # Selection of columns
    tk.Label(frame_selection, text="Seleziona il file:").grid(row=0, column=0, sticky="w", pady=5)
    file_menu = tk.OptionMenu(frame_selection, selected_df, *[f"File {i + 1}" for i in range(len(dataframes))])
    file_menu.grid(row=0, column=1, sticky="w")

    tk.Label(frame_selection, text="Colonna X:").grid(row=1, column=0, sticky="w", pady=5)
    x_menu = tk.OptionMenu(frame_selection, selected_x_col, "")
    x_menu.grid(row=1, column=1, sticky="w")

    tk.Label(frame_selection, text="Colonna Y:").grid(row=2, column=0, sticky="w", pady=5)
    y_menu = tk.OptionMenu(frame_selection, selected_y_col, "")
    y_menu.grid(row=2, column=1, sticky="w")


    def update_columns(*args):
        ''' Update available columns based on the selected file
        '''
        try:
            df_idx = int(selected_df.get().split(" ")[1]) - 1
            columns = list(dataframes[df_idx].columns)
            selected_x_col.set(columns[0])
            selected_y_col.set(columns[0])

            x_menu["menu"].delete(0, "end")
            y_menu["menu"].delete(0, "end")
            for col in columns:
                x_menu["menu"].add_command(label=col, command=lambda value=col: selected_x_col.set(value))
                y_menu["menu"].add_command(label=col, command=lambda value=col: selected_y_col.set(value))
        except Exception:
            pass

    selected_df.trace_add("write", update_columns)
    update_columns()  # Initialize with the first file

    # Selection of range, parameters, and fit function
    tk.Label(frame_parameters, text="Inserisci il range di fitting:").grid(row=0, column=0, columnspan=2, pady=5)

    tk.Label(frame_parameters, text="x_start:").grid(row=1, column=0, sticky="w", pady=2)
    tk.Entry(frame_parameters, textvariable=x_start, width=20).grid(row=1, column=1, pady=2)

    tk.Label(frame_parameters, text="x_end:").grid(row=2, column=0, sticky="w", pady=2)
    tk.Entry(frame_parameters, textvariable=x_end, width=20).grid(row=2, column=1, pady=2)

    tk.Label(frame_parameters, text="Inserisci i nomi dei parametri (separati da virgola):").grid(row=3, column=0, columnspan=2, pady=5)
    tk.Entry(frame_parameters, textvariable=param_names_var, width=40).grid(row=4, column=0, columnspan=2, pady=5)

    tk.Label(frame_parameters, text="Inserisci i parametri iniziali:").grid(row=5, column=0, columnspan=2, pady=5)
    tk.Entry(frame_parameters, textvariable=initial_params_var, width=40).grid(row=6, column=0, columnspan=2, pady=5)

    tk.Label(frame_parameters, text="Inserisci la funzione di fitting:").grid(row=7, column=0, columnspan=2, pady=5)
    tk.Entry(frame_parameters, textvariable=function_var, width=40).grid(row=8, column=0, columnspan=2, pady=5)


    def perform_fitting():
        ''' Performs fitting on the selected function and range.
        '''

        df_idx = int(selected_df.get().split(" ")[1]) - 1
        df = dataframes[df_idx]
        x_col = selected_x_col.get()
        y_col = selected_y_col.get()
        logger.info(f"Fit da eseguire per i dati {y_col} in funzione di {x_col}.")

        if x_col not in df.columns or y_col not in df.columns:
            messagebox.showerror("Errore", "Colonne non valide selezionate!")
            return

        # Extract the data
        x_data = df[x_col].astype(float).values
        y_data = df[y_col].astype(float).values

        # Filter data in the selected range
        mask = (x_data >= x_start.get()) & (x_data <= x_end.get())
        x_fit = x_data[mask]
        y_fit = y_data[mask]

        if len(x_fit) == 0 or len(y_fit) == 0:
            messagebox.showerror("Errore", "Nessun dato nel range selezionato!")
            return

        # Define the fit function
        param_names = [p.strip() for p in param_names_var.get().split(",")]
        fit_func_code = f"lambda x, {', '.join(param_names)}: {function_var.get()}"            
        part_after_colon = fit_func_code.split(":")[1].strip()  # Extract the part after the colon
        logger.info(f"Si vuole usare come funzione di fit: {part_after_colon}.")
        fit_func = eval(fit_func_code)

        # Retrieve initial parameters
        initial_params = [float(p.strip()) for p in initial_params_var.get().split(",")]
        try :
            # Perform the fit
            params, pcovm = curve_fit(fit_func, x_fit, y_fit, p0=initial_params)

            # Draw the fitted curve
            x_plot = np.linspace(x_start.get(), x_end.get(), 500)
            y_plot = fit_func(x_plot, *params)
            fig = list_figures[number_plots[0] - 1]
            plt.plot(x_plot, y_plot, label=f"Fit: {y_col} vs {x_col}", linestyle="--", color="green")
            plt.legend()
            plt.show()
            
            result = ";\n".join([f"{p} = {xi:.3e} +- {dxi:.3e}" 
                                 for p, xi, dxi in zip(param_names, params, np.sqrt(pcovm.diagonal()))])
            
            # Explicit cast to avoid newline issues in log file
            logger.info(f"Il fit ha portato i seguenti risultati: {str(result).replace(chr(10), ' ')}.")
            messagebox.showinfo("Fit Completato", f"I risultati per i parametri del fit sono:\n{result}")

            # Save on the dictionary for the command window
            for p, xi, dxi in zip(param_names, params, np.sqrt(pcovm.diagonal())):
                fit_results[p] = xi
                fit_results[f"error_{p}"] = dxi

        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il fitting: {e}")
            
            # Draw the curve calculated with the initial parameters
            x_plot = np.linspace(x_start.get(), x_end.get(), 500)
            y_plot = fit_func(x_plot, *initial_params)
            fig = list_figures[number_plots[0] - 1]
            plt.plot(x_plot, y_plot, label="initial guess curve", linestyle="--", color="green")
            plt.legend()
            plt.show()

    tk.Button(frame_parameters, text="Execute curve fitting",
              command=perform_fitting).grid(row=9, column=0, columnspan=2, pady=10)
