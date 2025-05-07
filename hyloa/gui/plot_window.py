"""
Code to manage the plot window
"""
import numpy as np
from scipy.special import *
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from matplotlib.figure import Figure
from matplotlib import markers, lines as mlines, colors as mcolors
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QComboBox, QMessageBox, QDialog, QFormLayout,
    QLineEdit, QMdiSubWindow, QTextEdit, QSizePolicy
)

from hyloa.data.processing import inv_single_branch_dialog
from hyloa.data.processing import inv_x_dialog, inv_y_dialog
from hyloa.data.processing import norm_dialog, close_loop_dialog


#==============================================================================================#
# Main function for managing the plot window                                                   #
#==============================================================================================#

class PlotControlWidget(QWidget):

    def __init__(self, app_instance, number_plots):
        super().__init__()
        
        self.app_instance         = app_instance  # Instance of main app
        self.number_plots         = number_plots  # Index of the plot
        self.plot_customizations  = {}            # Dictionary to save graphic's customization
        self.selected_pairs       = []            # List of plotted data
        # Variables to manage figure
        self.figure               = None         
        self.ax                   = None
        self.canvas               = None
        self.toolbar              = None

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Top buttons row
        top_button_layout = QHBoxLayout()
        top_buttons = [
            ("Crea Grafico",       self.plot),
            ("Personalizza Stile", self.customize_plot_style),
            ("Curve Fitting",      self.curve_fitting),
            ("Normalize",          self.normalize),
        ]
        for text, func in top_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            top_button_layout.addWidget(btn)
        main_layout.addLayout(top_button_layout)

        # Bottom buttons row
        bottom_button_layout = QHBoxLayout()
        bottom_buttons = [
            ("Close loop",     self.close_loop),
            ("Inverti Campi",  self.x_inversion),
            ("Inverti asse y", self.y_inversion),
            ("Inverti ramo",   self.revert_branch),
        ]
        for text, func in bottom_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            bottom_button_layout.addWidget(btn)
        main_layout.addLayout(bottom_button_layout)

        # Section for adding pairs
        main_layout.addWidget(QLabel("Seleziona le coppie di colonne (x, y):"))
        add_pair_button = QPushButton("Aggiungi Coppia x-y")
        add_pair_button.clicked.connect(self.add_pair)
        main_layout.addWidget(add_pair_button)

        # Scroll area for dynamic pair selection
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.pair_container = QWidget()
        self.pair_layout = QVBoxLayout()
        self.pair_container.setLayout(self.pair_layout)
        self.scroll_area.setWidget(self.pair_container)
        main_layout.addWidget(self.scroll_area)

        # Add first pair
        self.add_pair()

    def add_pair(self, file_text=None, x_col=None, y_col=None):
        
        file_combo = QComboBox()
        file_combo.addItems([f"File {i + 1}" for i in range(len(self.app_instance.dataframes))])

        x_combo = QComboBox()
        y_combo = QComboBox()

        row = QHBoxLayout()

        def update_columns():
            index = file_combo.currentIndex()
            cols = list(self.app_instance.dataframes[index].columns)
            x_combo.clear()
            y_combo.clear()
            x_combo.addItems(cols)
            y_combo.addItems(cols)

            # Selection for loading previous session
            if x_col in cols:
                x_combo.setCurrentText(x_col)
            if y_col in cols:
                y_combo.setCurrentText(y_col)

        file_combo.currentIndexChanged.connect(update_columns)

        # Selection for loading previous session
        if file_text:
            file_combo.setCurrentText(file_text)

        update_columns()

        row.addWidget(QLabel("File:"))
        row.addWidget(file_combo)
        row.addWidget(QLabel("x:"))
        row.addWidget(x_combo)
        row.addWidget(QLabel("y:"))
        row.addWidget(y_combo)

        container = QWidget()
        container.setLayout(row)
        self.pair_layout.addWidget(container)
        self.selected_pairs.append((file_combo, x_combo, y_combo))

    def plot(self):
        ''' Call function to plot data
        '''
        plot_data(self, self.app_instance)

    def customize_plot_style(self):
        ''' Call function to customizzzation of plots
        '''
        customize_plot_style(self, self.plot_customizations,
                             self.number_plots, self.app_instance.figures_map)
    
    def curve_fitting(self):
        ''' Curve fitting window
        '''
        open_curve_fitting_window(self.app_instance, self)
       
    def normalize(self):
        ''' Call function to normalize data
        '''
        norm_dialog(self, self.app_instance)

    def close_loop(self):
        ''' Call function to close loop
        '''
        close_loop_dialog(self, self.app_instance)

    def x_inversion(self):
        ''' Call function to invert x axis
        '''
        inv_x_dialog(self, self.app_instance)

    def y_inversion(self):
        ''' Call function to invert y axis
        '''
        inv_y_dialog(self, self.app_instance)

    def revert_branch(self):
        ''' Call function to revert a branch of a cycle
        '''
        inv_single_branch_dialog(self, self.app_instance)

        
#==============================================================================================#
# Function that creates the plot with the chosen data                                          #
#==============================================================================================#

def plot_data(plot_window_instance, app_instance):
    '''
    Create the plot with the selected pairs using matplotlib.
   
    Parameters
    ----------
    plot_window_instance : PlotControlWidget
        Instance of the plot control widget containing the selected pairs.
    app_instance : MainApp
        Main application instance containing the session data.
    '''

    # Extracting data from the plot window instance
    selected_pairs      = plot_window_instance.selected_pairs
    number_plots        = plot_window_instance.number_plots
    dataframes          = app_instance.dataframes
    plot_customizations = plot_window_instance.plot_customizations
    logger              = app_instance.logger
    
    # Create a figure
    if plot_window_instance.figure is None:
        fig = Figure(figsize=(10, 6))
        ax  = fig.add_subplot(111)

        # Save objects in the instance
        plot_window_instance.figure = fig
        plot_window_instance.ax     = ax

        app_instance.figures_map[number_plots] = (fig, ax)

        # Create canvas and show in sub-window
        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, plot_window_instance)

        # Create layout
        plot_area = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        plot_area.setLayout(layout)

        # Save 
        plot_window_instance.canvas  = canvas
        plot_window_instance.toolbar = toolbar 

        # Sub-window
        sub = QMdiSubWindow()
        sub.setWindowTitle(f"Grafico {number_plots}")
        sub.setWidget(plot_area)
        sub.resize(800, 600)
        app_instance.mdi_area.addSubWindow(sub)
        sub.show()


    else:
        # Retrieve existing objects
        fig     = plot_window_instance.figure
        ax      = plot_window_instance.ax
        canvas  = plot_window_instance.canvas
        toolbar = plot_window_instance.toolbar

        # Clear for new plot
        ax.clear()

    try:

        X = []
        Y = []

        for df_choice, x_var, y_var in selected_pairs:
            df_idx = int(df_choice.currentText().split(" ")[1]) - 1 
            x_col = x_var.currentText()
            y_col = y_var.currentText()

            if not x_col or not y_col:
                QMessageBox.critical(None, "Errore", "Devi selezionare tutte le coppie di colonne!")
                return

            X.append(dataframes[df_idx][x_col].astype(float).values)
            Y.append(dataframes[df_idx][y_col].astype(float).values)
            logger.info(f"Plot di: {x_col} vs {y_col}")

        if not plot_customizations:
            col = plt.cm.jet(np.linspace(0, 1, len(X)))
            for i in range(0, len(X), 2):
                ax.plot(X[i],   Y[i],   color=col[i], marker="o", label=f"Ciclo {i//2 + 1}")
                ax.plot(X[i+1], Y[i+1], color=col[i], marker="o")


        else:
            for i, (x, y) in enumerate(zip(X, Y)):
                if i % 2 == 0:
                    line1, = ax.plot(x, y, label=f"Ciclo {i // 2 + 1}")
                else:
                    line2, = ax.plot(x, y)

                try:
                    customization = plot_customizations.get(i // 2, {})

                    line1.set_color(customization.get("color", line1.get_color()))
                    line1.set_marker(customization.get("marker", line1.get_marker()))
                    line1.set_linestyle(customization.get("linestyle", line1.get_linestyle()))
                    line1.set_label(customization.get("label", f"Ciclo {i // 2 + 1}"))

                    if i % 2 == 1:
                        line2.set_color(customization.get("color", line1.get_color()))
                        line2.set_marker(customization.get("marker", line1.get_marker()))
                        line2.set_linestyle(customization.get("linestyle", line1.get_linestyle()))
                        line2.set_label("_nolegend_")

                except Exception as e:
                    print(f"Errore applicando lo stile: {e}")

        ax.set_xlabel("H [Oe]", fontsize=15)
        ax.set_ylabel(r"M/M$_{sat}$", fontsize=15)
        ax.legend()
        ax.grid()
        canvas.draw()

    except Exception as e:
        QMessageBox.critical(None, "Errore", f"Errore durante la creazione del grafico: {e}")

#==============================================================================================#
# Function to customize the style of the plot                                                  #
#==============================================================================================#

def customize_plot_style(parent_widget, plot_customizations, number_plots, figures_map):
    '''
    Opens a PyQt5 dialog to customize color, marker, and line style of a cycle in the plot.

    Parameters
    ----------
    parent_widget : QWidget
        parent PyQt5 window
    plot_customizations : dict
        dictionary to save users customizations
    number_plots : list
        list with one element, current plot number
    figures_map : dict
        dictionary to store all the matplotlib figures
    '''
    
    if parent_widget.figure is None:
        QMessageBox.critical(parent_widget, "Errore", "Nessun grafico aperto! Crea prima un grafico.")
        return

    fig, ax = figures_map[number_plots]

    lines = ax.lines

    if not lines:
        QMessageBox.critical(parent_widget, "Errore", "Nessuna linea presente nel grafico!")
        return

    # === All possible customization options ===
    colors       = list(mcolors.TABLEAU_COLORS) + list(mcolors.CSS4_COLORS)
    markers_list = [m for m in markers.MarkerStyle.markers.keys() if isinstance(m, str) and len(m) == 1]
    linestyles   = list(mlines.Line2D.lineStyles.keys())

    # === Cycle names ===
    cycles = []
    label_to_index = {}
    for i in range(0, len(lines), 2):
        label = plot_customizations.get(i // 2, {}).get("label", f"Ciclo {i // 2 + 1}")
        cycles.append(label)
        label_to_index[label] = i // 2

    # === Dialog ===
    dialog = QDialog(parent_widget)
    dialog.setWindowTitle("Personalizza Stile Grafico")
    dialog.setFixedSize(400, 360)

    layout = QVBoxLayout(dialog)
    form_layout = QFormLayout()
    layout.addLayout(form_layout)

    # === Widgets ===
    cycle_combo = QComboBox()
    cycle_combo.addItems(cycles)

    color_combo = QComboBox()
    color_combo.addItems(colors)
    color_combo.setEditable(True)

    marker_combo = QComboBox()
    marker_combo.addItems(markers_list)
    marker_combo.setEditable(True)

    linestyle_combo = QComboBox()
    linestyle_combo.addItems(linestyles)
    linestyle_combo.setEditable(True)

    label_edit = QLineEdit()
    label_edit.setText(cycles[0])

    # === Add to form ===
    form_layout.addRow("Ciclo:", cycle_combo)
    form_layout.addRow("Colore:", color_combo)
    form_layout.addRow("Marker:", marker_combo)
    form_layout.addRow("Stile Linea:", linestyle_combo)
    form_layout.addRow("Nome in legenda:", label_edit)

    # === Apply button ===
    apply_button = QPushButton("Applica")
    layout.addWidget(apply_button)

    def apply_style():
        try:
            idx = label_to_index[cycle_combo.currentText()]
            line1 = lines[idx * 2]
            line2 = lines[idx * 2 + 1]

            color = color_combo.currentText()
            marker = marker_combo.currentText()
            linestyle = linestyle_combo.currentText()
            legend_label = label_edit.text() or cycle_combo.currentText()

            # Apply style to both lines
            for line in (line1, line2):
                line.set_color(color)
                line.set_marker(marker)
                line.set_linestyle(linestyle)

            line1.set_label(legend_label)
            line2.set_label("_nolegend_")
            
            # Save customization's 
            plot_customizations[idx] = {
                "color": color,
                "marker": marker,
                "linestyle": linestyle,
                "label": legend_label,
            }

            ax.legend()
            fig.canvas.draw_idle()
            dialog.accept()

        except Exception as e:
            QMessageBox.critical(dialog, "Errore", f"Errore durante l'applicazione dello stile:\n{e}")

    apply_button.clicked.connect(apply_style)

    dialog.exec_()

#==============================================================================================#
# Curve fitting function                                                                       #
#==============================================================================================#

def open_curve_fitting_window(app_instance, plot_widget):
    '''
    Apre una finestra per configurare il fitting dei dati.
    
    Parameters
    ----------
    app_instance : MainApp
        Istanza principale dell'applicazione.
    plot_widget : PlotControlWidget
        Istanza della finestra di controllo del plot corrente.
    '''
    dataframes    = app_instance.dataframes
    fit_results   = app_instance.fit_results
    logger        = app_instance.logger

    if not dataframes:
        QMessageBox.critical(app_instance, "Errore", "Non ci sono dati caricati!")
        return

    window = QWidget()
    window.setWindowTitle("Curve Fitting")
    layout = QHBoxLayout(window)
    window.setLayout(layout)

    def show_help_dialog():
        help_text = (
            "La funzione di fit deve essere una funzione della variabile 'x' e "
            "i nomi dei parametri devono essere specificati nel campo apposito.\n\n"
            "Per stabilire il range basta la lettura del cursore sul grafico, i valori sono in alto a destra.\n\n"
            "Come PROMEMORIA, il ramo 'Up' è quello più a destra a meno che non si sia invertito l'asse x; "
            "in tal caso sarà quello a sinistra.\n\n"
            "ACHTUNG: la funzione va scritta in Python, quindi ad esempio |x| è abs(x), x^2 è x**2, e tutte "
            "le altre funzioni vanno scritte con np. davanti (i.e. np.cos(x), np.exp(x)), tranne per le funzioni speciali, "
            "per le quali va usato il nome che usa la libreria scipy.special (i.e. scipy.special.erf diventa erf)"
        )

        QMessageBox.information(window, "Guida al Fitting", help_text)

    # Left: selection
    selection_layout = QVBoxLayout()
    layout.addLayout(selection_layout)

    help_button = QPushButton("Help")
    help_button.clicked.connect(show_help_dialog)
    selection_layout.addWidget(help_button, alignment=Qt.AlignLeft)


    selection_layout.addWidget(QLabel("Seleziona il file:"))
    file_combo = QComboBox()
    file_combo.addItems([f"File {i+1}" for i in range(len(dataframes))])
    selection_layout.addWidget(file_combo)

    selection_layout.addWidget(QLabel("Colonna X:"))
    x_combo = QComboBox()
    selection_layout.addWidget(x_combo)

    selection_layout.addWidget(QLabel("Colonna Y:"))
    y_combo = QComboBox()
    selection_layout.addWidget(y_combo)

    def update_columns():
        idx = file_combo.currentIndex()
        cols = list(dataframes[idx].columns)
        x_combo.clear()
        y_combo.clear()
        x_combo.addItems(cols)
        y_combo.addItems(cols)

    file_combo.currentIndexChanged.connect(update_columns)
    update_columns()

    # Right: parameters
    param_layout = QVBoxLayout()
    layout.addLayout(param_layout)

    param_layout.addWidget(QLabel("x_start:"))
    x_start_edit = QLineEdit("0")
    param_layout.addWidget(x_start_edit)

    param_layout.addWidget(QLabel("x_end:"))
    x_end_edit = QLineEdit("1")
    param_layout.addWidget(x_end_edit)

    param_layout.addWidget(QLabel("Nomi parametri (es. a,b):"))
    param_names_edit = QLineEdit("a,b")
    param_layout.addWidget(param_names_edit)

    param_layout.addWidget(QLabel("Parametri iniziali (es. 1,1):"))
    initial_params_edit = QLineEdit("1,1")
    param_layout.addWidget(initial_params_edit)

    param_layout.addWidget(QLabel("Funzione di fitting (es. a*(x-b)):"))
    function_edit = QLineEdit("a*(x - b)")
    param_layout.addWidget(function_edit)

    output_box = QTextEdit()
    output_box.setReadOnly(True)
    output_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    layout.addWidget(output_box)

    def perform_fit():
        try:

            df_idx  = file_combo.currentIndex()
            df      = dataframes[df_idx]
            x_col   = x_combo.currentText()
            y_col   = y_combo.currentText()

            x_data  = df[x_col].astype(float).values
            y_data  = df[y_col].astype(float).values

            x_start = float(x_start_edit.text())
            x_end   = float(x_end_edit.text())
            mask    = (x_data >= x_start) & (x_data <= x_end)
            x_fit   = x_data[mask]
            y_fit   = y_data[mask]

            if len(x_fit) == 0:
                QMessageBox.warning(window, "Errore", "Nessun dato nel range selezionato!")
                return

            param_names    = [p.strip() for p in param_names_edit.text().split(",")]
            initial_params = [float(p.strip()) for p in initial_params_edit.text().split(",")]

            func_code = f"lambda x, {', '.join(param_names)}: {function_edit.text()}"
            fit_func  = eval(func_code)

            params, pcov = curve_fit(fit_func, x_fit, y_fit, p0=initial_params)
            y_plot = fit_func(np.linspace(x_start, x_end, 500), *params)

            fig = plot_widget.figure
            ax  = plot_widget.ax
            ax.plot(np.linspace(x_start, x_end, 500), y_plot, linestyle="--", color="green")
            plot_widget.canvas.draw()

            result_lines = []
            for p, val, err in zip(param_names, params, np.sqrt(np.diag(pcov))):
                result_lines.append(f"{p} = {val:.3e} ± {err:.3e}")
                fit_results[p] = val
                fit_results[f"error_{p}"] = err

            result = "\n".join(result_lines)
            output_box.setPlainText(result)
            logger.info("Fit completato con successo.")
            # Explicit cast to avoid newline issues in log file
            logger.info(f"Il fit ha portato i seguenti risultati: {str(result).replace(chr(10), ' ')}.")
            app_instance.refresh_shell_variables()

        except Exception as e:
            QMessageBox.critical(window, "Errore", f"Errore durante il fitting: {e}")
           
    fit_button = QPushButton("Esegui Fit")
    fit_button.clicked.connect(perform_fit)
    param_layout.addWidget(fit_button)

    # Sub-window for fitting panel
    sub = QMdiSubWindow()
    sub.setWidget(window)
    sub.setWindowTitle("Curve Fitting")
    sub.resize(600, 300)
    app_instance.mdi_area.addSubWindow(sub)
    sub.show()