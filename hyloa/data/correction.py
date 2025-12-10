# This file is part of HYLOA - HYsteresis LOop Analyzer.
# Copyright (C) 2024 Francesco Zeno Costanzo

# HYLOA is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# HYLOA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with HYLOA. If not, see <https://www.gnu.org/licenses/>.


"""
Code to automize and incorporate in the gui a
standard correction process for hystersis loops
"""
import numpy as np
from scipy.optimize import curve_fit
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
     QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit, QMessageBox,
     QSizePolicy, QMdiSubWindow)
from PyQt5.QtCore import Qt

from hyloa.utils.err_format import format_value_error


def correct_hysteresis_loop(app_instance):
    '''
    Opens a hysteresis loop correction window in a sub-MDI window.
    This window allows the user to set all parameters for the correction
    of a selected hysteresis loop and visualize the results.
    
    Parameters
    ----------
    app_instance : MainApp
        The main application instance containing dataframes and logger.
    '''
    dataframes  = app_instance.dataframes
    logger      = app_instance.logger

    if not dataframes:
        QMessageBox.critical(app_instance, "Error", "No data loaded!")
        return

    # Create main window layout
    window = QWidget()
    window.setWindowTitle("Loop Correction")
    root_layout = QHBoxLayout(window)
    window.setLayout(root_layout)

    #=========================================#
    # Control's panel on the left side        #
    #=========================================#
    
    left_layout = QVBoxLayout()
    root_layout.addLayout(left_layout, stretch=0)

    def show_help_dialog():
        '''
        Show a help dialog with instructions for using the correction tool.
        '''

        help_text = (
            "Help guide:\n"
            "\n"
            "• Select the main data file and choose the four X/Y columns that define the Up and Down branches of the loop.\n"
            " These selections must correspond to the same variables shown in the plotting window.\n"
            "\n"
            "• Optionally, you may choose to substitute one branch with the mirrored version of the other branch.\n"
            "\n"
            "• Optionally, you may select a second file where corrected data will be saved.\n"
            "The corrected columns will be written in the corresponding positions of the destination grid, "
            "so the layout of the two 2x2 grids matches (Up/Down x X/Y).\n"
            "\n"
            "• Set the x_start / x_end limits for each branch. If the field is scaled, remember that "
            "the fit ranges must be chosen according to the *original*, non-scaled data; the scaling will be applied later.\n"
            "\n"
            "• Configure the first fit block, which is used to correct possible drifts at the end of each branch.\n"
            "You may use any polynomial or analytical function, but it is strongly recommended to avoid excessively "
            "high polynomial orders. The constant term MUST be the first parameter, exactly as shown in the example below.\n"
            "  (e.g. 'a + b*x + c*x**2').\n"
            "\n"
            "• Configure the second fit block. This works exactly like the 'Quick Fit' window and can be used "
            "to extract properties such as coercive field or remanence. This second fit operates on the *corrected* data.\n"
            "It is recommended to use simple low-order polinomials to fit coercivity or remenance regions.\n"
            "\n"
            "• Press 'Correct' to execute both fit blocks for both branches.\n"
            "\n"
            "Examples of fit functions:\n"
            "    a + b*x\n"
            "    a + b*x + c*x**2\n"
            "    np.tanh(a*(x-b))\n"
        )

        QMessageBox.information(window, "Correction Guide", help_text)
    

    help_button = QPushButton("Help")
    help_button.clicked.connect(show_help_dialog)
    left_layout.addWidget(help_button, alignment=Qt.AlignLeft)

    # Selection of the file to process
    left_layout.addWidget(QLabel("Select data file (source):"))
    file_combo = QComboBox()
    file_combo.addItems([f"File {i+1}" for i in range(len(dataframes))])
    left_layout.addWidget(file_combo)

    # Selecetion of the columns that contain the data
    box_data = QGridLayout()
    left_layout.addLayout(box_data)

    box_data.addWidget(QLabel("up: "), 0, 0)
    x_up_combo = QComboBox(); box_data.addWidget(x_up_combo, 0, 1)
    y_up_combo = QComboBox(); box_data.addWidget(y_up_combo, 0, 2)

    box_data.addWidget(QLabel("down: "), 1, 0)
    x_down_combo = QComboBox(); box_data.addWidget(x_down_combo, 1, 1)
    y_down_combo = QComboBox(); box_data.addWidget(y_down_combo, 1, 2)

    
    box_options = QGridLayout()
    left_layout.addLayout(box_options)

    # Select option to duplicate a branch
    double_branch = QComboBox()
    double_branch.addItem("No")
    double_branch.addItem("Up")
    double_branch.addItem("Down")
    box_options.addWidget(QLabel("Duplicate branch: "), 0, 0)
    box_options.addWidget(double_branch, 0, 1)

    # Selection of the file to save corrected columns
    left_layout.addWidget(QLabel("Optional: file to save corrected data (use same order):"))
    save_file_combo = QComboBox()
    save_file_combo.addItem("No save")
    save_file_combo.addItems([f"File {i+1}" for i in range(len(dataframes))])
    left_layout.addWidget(save_file_combo)

    # Selection of destination columns
    dest_box = QGridLayout()
    left_layout.addLayout(dest_box)

    dest_box.addWidget(QLabel("Save up:"), 0, 0)
    x_up_dest = QComboBox(); dest_box.addWidget(x_up_dest, 0, 1)
    y_up_dest = QComboBox(); dest_box.addWidget(y_up_dest, 0, 2)

    dest_box.addWidget(QLabel("Save down:"), 1, 0)
    x_dw_dest = QComboBox(); dest_box.addWidget(x_dw_dest, 1, 1)
    y_dw_dest = QComboBox(); dest_box.addWidget(y_dw_dest, 1, 2)

    #===============================================#

    def update_columns_from_selected_file():
        ''' Update the column selection combos based on the selected source file.
        '''
        idx = file_combo.currentIndex()
        cols = list(dataframes[idx].columns)
        for combo in (x_up_combo, y_up_combo, x_down_combo, y_down_combo):
            combo.clear()
            combo.addItems(cols)

    file_combo.currentIndexChanged.connect(update_columns_from_selected_file)
    update_columns_from_selected_file()

    def update_dest_columns():
        ''' Update the column selection combos based on the selected save file.
        '''
        save_choice = save_file_combo.currentIndex()

        if save_choice == 0:
            # No save → empty combos
            for combo in (x_up_dest, y_up_dest, x_dw_dest, y_dw_dest):
                combo.clear()
            return

        dest_idx = save_choice - 1  
        cols = list(dataframes[dest_idx].columns)

        for combo in (x_up_dest, y_up_dest, x_dw_dest, y_dw_dest):
            combo.clear()
            combo.addItems(cols)

    save_file_combo.currentIndexChanged.connect(update_dest_columns)

    #===============================================#
    # Set parameters for the corrections            #
    #===============================================#

    st_grid = QGridLayout()
    left_layout.addWidget(QLabel("---- Field correction ----"))

    left_layout.addLayout(st_grid)
    st_grid.addWidget(QLabel("Field shift (i.e. H = H - shift)"), 0, 0)
    st_grid.addWidget(QLabel("Field scale (i.e. H = H * scale)"), 0, 1)
    
    field_shift_edit = QLineEdit("0")
    st_grid.addWidget(field_shift_edit, 1, 0)

    field_scale_edit = QLineEdit("1")
    st_grid.addWidget(field_scale_edit, 1, 1)

    
    left_layout.addWidget(QLabel("---- Fit for tail correction ----"))

    limits_grid = QGridLayout()
    left_layout.addLayout(limits_grid)

    x_start_n_edit = QLineEdit("-4000")
    x_end_n_edit   = QLineEdit("-400")
    
    limits_grid.addWidget(QLabel("x_start_neg"), 0, 0)
    limits_grid.addWidget(x_start_n_edit,        0, 1)
    limits_grid.addWidget(QLabel("x_end_neg"),   0, 2)
    limits_grid.addWidget(x_end_n_edit,          0, 3)

    x_start_p_edit = QLineEdit("400")
    x_end_p_edit   = QLineEdit("4000")

    limits_grid.addWidget(QLabel("x_start_pos"), 1, 0)
    limits_grid.addWidget(x_start_p_edit,        1, 1)
    limits_grid.addWidget(QLabel("x_end_pos"),   1, 2)
    limits_grid.addWidget(x_end_p_edit,          1, 3)

    box_fit_params = QGridLayout()
    left_layout.addLayout(box_fit_params)
    box_fit_params.addWidget(QLabel("Parameter names (e.g. a,b):"), 0, 0)
    box_fit_params.addWidget(QLabel("Initial values  (e.g. 1,1):"), 0, 1)

    tail_params_edit = QLineEdit("a,b")
    box_fit_params.addWidget(tail_params_edit, 1, 0)

    tail_initials_edit = QLineEdit("1,1")
    box_fit_params.addWidget(tail_initials_edit, 1, 1)

    left_layout.addWidget(QLabel("Function (e.g. a + b*x) :"))
    tail_function_edit = QLineEdit("a + b*x")
    left_layout.addWidget(tail_function_edit)

    #===============================================#
    # Set parameters for coercivity computation     #
    #===============================================#

    left_layout.addWidget(QLabel("---- Fit for coercivity/remenance exitamtion ----"))

    limits_grid_1 = QGridLayout()
    left_layout.addLayout(limits_grid_1)

    x_start_up_hc_edit = QLineEdit("100")
    x_end_up_hc_edit   = QLineEdit("200")
    
    limits_grid_1.addWidget(QLabel("x_start_up"), 0, 0)
    limits_grid_1.addWidget(x_start_up_hc_edit,   0, 1)
    limits_grid_1.addWidget(QLabel("x_end_up"),   0, 2)
    limits_grid_1.addWidget(x_end_up_hc_edit,     0, 3)

    x_start_dw_hc_edit = QLineEdit("-200")
    x_end_dw_hc_edit   = QLineEdit("-100")

    limits_grid_1.addWidget(QLabel("x_start_down"), 1, 0)
    limits_grid_1.addWidget(x_start_dw_hc_edit,     1, 1)
    limits_grid_1.addWidget(QLabel("x_end_down"),   1, 2)
    limits_grid_1.addWidget(x_end_dw_hc_edit,       1, 3)

    box_fit_params_1 = QGridLayout()
    left_layout.addLayout(box_fit_params_1)
    box_fit_params_1.addWidget(QLabel("Parameter names (e.g. a,b):"), 0, 0)
    box_fit_params_1.addWidget(QLabel("Initial values  (e.g. 1,1):"),  0, 1)

    hc_params_edit = QLineEdit("s,hc")
    box_fit_params_1.addWidget(hc_params_edit, 1, 0)

    hc_initials_edit = QLineEdit("1,1")
    box_fit_params_1.addWidget(hc_initials_edit, 1, 1)

    left_layout.addWidget(QLabel("Function (e.g. s*(x - hc) ):"))
    hc_function_edit = QLineEdit("s*(x - hc)")
    left_layout.addWidget(hc_function_edit)

    #===============================================#
    # Run button                                    #
    #===============================================#
    run_button = QPushButton("Correct")
    left_layout.addWidget(run_button)

    left_layout.addStretch()
   
    #===============================================#
    # ----------- RIGHT: plot + results ----------- #
    #===============================================#

    right_layout = QVBoxLayout()
    root_layout.addLayout(right_layout, stretch=1)

    # Matplotlib figure & canvas
    fig = Figure(figsize=(5,4))
    canvas = FigureCanvas(fig)

    # Toolbar Matplotlib (zoom, pan, save, coordinate)
    toolbar = NavigationToolbar(canvas, window)
    right_layout.addWidget(toolbar)

    ax = fig.add_subplot(111)
    ax.set_title("Data preview")
    ax.set_xlabel("H [Oe]", fontsize=15)
    ax.set_ylabel(r"M/M$_{sat}$", fontsize=15)
    canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    right_layout.addWidget(canvas, stretch=3)

    # Output box
    output_box = QTextEdit()
    output_box.setReadOnly(True)
    output_box.setFixedHeight(140)
    right_layout.addWidget(output_box, stretch=1)

    #================================================#
    # Helper function for plot and preview refresh   #
    #================================================#

    def refresh_preview():
        ''' Draw selected data on canvas
        '''
        try:
            ax.clear()
            idx = file_combo.currentIndex()
            df  = dataframes[idx]

            # plot both up and down raw points if available
            def plot_if_exists(xcol, ycol, label):
                if xcol and ycol and xcol in df.columns and ycol in df.columns:
                    x = df[xcol].astype(float).values
                    y = df[ycol].astype(float).values
                    ax.plot(x, y, marker='.', linestyle='-', label=label, color='k')

                    # Add horizontal line at y=0
                    ax.axhline(y=0, color='gray', linestyle='--', linewidth=1)
                    # Add vertical line at x=0
                    ax.axvline(x=0, color='gray', linestyle='--', linewidth=1)

            plot_if_exists(x_up_combo.currentText(),   y_up_combo.currentText(), "Up")
            plot_if_exists(x_down_combo.currentText(), y_down_combo.currentText(), "Down")

            
            handles, labels = ax.get_legend_handles_labels()
            if labels:
                ax.legend(handles, labels)

            ax.set_xlabel("H [Oe]", fontsize=15)
            ax.set_ylabel(r"M/M$_{sat}$", fontsize=15)
            canvas.draw()
        except Exception as e:
            QMessageBox.critical("Error refreshing preview: %s", e)

    # Connect changes to update preview
    for cb in (x_up_combo, y_up_combo, x_down_combo, y_down_combo, file_combo):
        try:
            cb.currentIndexChanged.connect(refresh_preview)
        except Exception:
            pass

    
    # Connect run button
    run_button.clicked.connect(lambda: perform_correction(
        file_combo, save_file_combo,
        x_up_combo, y_up_combo, x_down_combo, y_down_combo,
        double_branch, field_shift_edit, field_scale_edit,
        x_start_n_edit, x_end_n_edit, x_start_p_edit, x_end_p_edit,
        tail_params_edit, tail_function_edit,
        x_start_up_hc_edit, x_end_up_hc_edit, x_start_dw_hc_edit, x_end_dw_hc_edit,
        hc_params_edit, hc_function_edit,
        x_up_dest, y_up_dest, x_dw_dest, y_dw_dest,
        dataframes, logger,
        ax, canvas, output_box, window)
    )
    
    # Sub-window for fitting panel
    sub = QMdiSubWindow()
    sub.setWidget(window)
    sub.setWindowTitle("Loop Correction")
    sub.resize(1200, 800)
    app_instance.mdi_area.addSubWindow(sub)
    sub.show()

#================================================#
# Helper function for removing old lines         #
#================================================#

def clear_fit_lines(ax):
    ''' 
    Helper function clear previous fit lines from axes (gid startswith "fit")

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes from which to remove fit lines.
    '''
    to_remove = [ln for ln in ax.lines if getattr(ln, "get_gid", lambda: None)() and str(ln.get_gid()).startswith("fit")]
    for ln in to_remove:
        ln.remove()

#================================================#
# MAIN CORRECTION FUNCTION                       #
#================================================#

def perform_correction(file_combo, save_file_combo,
                       x_up_combo, y_up_combo, x_down_combo, y_down_combo,
                       double_branch, field_shift_edit, field_scale_edit,
                       x_start_n_edit, x_end_n_edit, x_start_p_edit, x_end_p_edit,
                       tail_params_edit, tail_function_edit,
                       x_start_up_hc_edit, x_end_up_hc_edit, x_start_dw_hc_edit, x_end_dw_hc_edit,
                       hc_params_edit, hc_function_edit,
                       x_up_dest, y_up_dest, x_dw_dest, y_dw_dest,
                       dataframes, logger,
                       ax, canvas, output_box, window):
    ''' 
    Perform the loop correction using the parameters from the UI.
    The correction involves fitting the saturation parts (tails) of the hystersis loop
    to remove drifts; then there is the possibilty to fit a region of the loop to
    extract the values of the coercive field and/ore the remenance.
    The anisotropy filed is computed by integrating the area between the up and down branches,
    and selected the field where the area il below/above a certain threshold.

    Parameters
    ----------
    file_combo : QComboBox
        Combo box to select source data file.
    save_file_combo : QComboBox
        Combo box to select destination data file.
    x_up_combo : QComboBox
        Combo box to select X column for Up branch.
    y_up_combo : QComboBox
        Combo box to select Y column for Up branch.
    x_down_combo : QComboBox
        Combo box to select X column for Down branch.
    y_down_combo : QComboBox
        Combo box to select Y column for Down branch.
    double_branch : QComboBox
        Combo box to select branch duplication option.
    field_shift_edit : QLineEdit
        Line edit for field shift value.
    field_scale_edit : QLineEdit
        Line edit for field scale value.
    x_start_n_edit : QLineEdit
        Line edit for negative tail start limit.
    x_end_n_edit : QLineEdit
        Line edit for negative tail end limit.
    x_start_p_edit : QLineEdit
        Line edit for positive tail start limit.
    x_end_p_edit : QLineEdit
        Line edit for positive tail end limit.
    tail_params_edit : QLineEdit
        Line edit for tail fit parameter names.
    tail_function_edit : QLineEdit
        Line edit for tail fit function.
    x_start_up_hc_edit : QLineEdit
        Line edit for Up branch coercive fit start limit.
    x_end_up_hc_edit : QLineEdit
        Line edit for Up branch coercive fit end limit.
    x_start_dw_hc_edit : QLineEdit
        Line edit for Down branch coercive fit start limit.
    x_end_dw_hc_edit : QLineEdit
        Line edit for Down branch coercive fit end limit.
    hc_params_edit : QLineEdit
        Line edit for coercive fit parameter names.
    hc_function_edit : QLineEdit
        Line edit for coercive fit function.
    dataframes : list of pd.DataFrame
        List of dataframes containing loaded data.
    logger : Logger
        Logger of the application.
    ax : matplotlib.axes.Axes
        Axes for plotting.
    canvas : FigureCanvas
        Canvas for rendering the plot.
    output_box : QTextEdit
        Text edit for displaying output results.
    window : QWidget
        The main window widget.
    '''
    try:
        idx_src      = file_combo.currentIndex()
        df_src       = dataframes[idx_src].copy()      # working copy
        save_choice  = save_file_combo.currentIndex()  # 0 = No save, >0 => file index adjust
        
        if save_choice == 0:
            save_idx = None
        else:
            # save_file_combo items: ["No save", "File 1", "File 2"...]
            save_idx = save_choice - 1

        results_text_lines = []

        # Read field shift/scale
        field_shift = float(field_shift_edit.text())
        field_scale = float(field_scale_edit.text())

        # Read x/y column names
        x_up_col = x_up_combo.currentText()
        y_up_col = y_up_combo.currentText()
        x_dw_col = x_down_combo.currentText()
        y_dw_col = y_down_combo.currentText()

        
        # Prepare arrays: apply shift and scale
        x_up = np.copy(df_src[x_up_col].astype(float).values) - field_shift
        x_up = x_up * field_scale
        y_up = np.copy(df_src[y_up_col].astype(float).values)

        x_dw = np.copy(df_src[x_dw_col].astype(float).values) - field_shift
        x_dw = x_dw * field_scale
        y_dw = np.copy(df_src[y_dw_col].astype(float).values)

        # Read duplication branch
        db = double_branch.currentText()
        if db == "Original":
            pass
        elif db == "Up":
            x_dw, y_dw = -np.copy(x_up), -np.copy(y_up)
            x_dw, y_dw = x_dw[::-1], y_dw[::-1]  # reverse to maintain order
        elif db == "Down":
            x_up, y_up = -np.copy(x_dw), -np.copy(y_dw)
            x_up, y_up = x_up[::-1], y_up[::-1]  # reverse to maintain order


        # Read tail ranges
        try:
            x_n_start = float(x_start_n_edit.text()) * field_scale  # For up negative region
            x_n_end   = float(x_end_n_edit.text())   * field_scale
        except Exception:
            # fallback
            x_n_start, x_n_end = -4000 * field_scale, -1000 * field_scale

        try:
            x_p_start = float(x_start_p_edit.text()) * field_scale  # For up positive region
            x_p_end   = float(x_end_p_edit.text()) * field_scale
        except Exception:
            x_p_start, x_p_end = 1000 * field_scale, 4000 * field_scale

        # Masks for up/down tails split by sign
        mask_n_up = (x_up >= x_n_start) & (x_up <= x_n_end)
        mask_p_up = (x_up >= x_p_start) & (x_up <= x_p_end)
        mask_n_dw = (x_dw >= x_n_start) & (x_dw <= x_n_end)
        mask_p_dw = (x_dw >= x_p_start) & (x_dw <= x_p_end)
        
        #===================================================================#
        # Auxiliary functions for fitting
        #===================================================================#

        try:
            tail_param_names = [p.strip() for p in tail_params_edit.text().split(",") if p.strip() != ""]
            func_code_tail   = f"lambda x, {', '.join(tail_param_names)}: {tail_function_edit.text()}"
            f_func           = eval(func_code_tail, {"np": np, "__builtins__": {}})
        
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Invalid function for tail fit:\n{e}")
            return

        try:
            hc_param_names = [p.strip() for p in hc_params_edit.text().split(",") if p.strip() != ""]
            func_code_hc   = f"lambda x, {', '.join(hc_param_names)}: {hc_function_edit.text()}"
            g_func         = eval(func_code_hc, {"np": np, "__builtins__": {}})
        
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Invalid function for coercive fit:\n{e}")
            return
        
        s2 = lambda x, y, f, popt: sum((y-f(x, *popt))**2)/(len(x)-len(popt))

        # Fit linear tails (four fits)
        p_up_1, c_up_1 = curve_fit(f_func, x_up[mask_n_up], y_up[mask_n_up])
        p_up_2, c_up_2 = curve_fit(f_func, x_up[mask_p_up], y_up[mask_p_up])
        p_dw_1, c_dw_1 = curve_fit(f_func, x_dw[mask_n_dw], y_dw[mask_n_dw])
        p_dw_2, c_dw_2 = curve_fit(f_func, x_dw[mask_p_dw], y_dw[mask_p_dw])

        # Parameter errors
        dp_up_1 = np.sqrt(np.diag(c_up_1))
        dp_up_2 = np.sqrt(np.diag(c_up_2))
        dp_dw_1 = np.sqrt(np.diag(c_dw_1))
        dp_dw_2 = np.sqrt(np.diag(c_dw_2))

        # Model dispersion error
        e_up_1 = s2(x_up[mask_n_up], y_up[mask_n_up], f_func, p_up_1)
        e_up_2 = s2(x_up[mask_p_up], y_up[mask_p_up], f_func, p_up_2)
        e_dw_1 = s2(x_dw[mask_n_dw], y_dw[mask_n_dw], f_func, p_dw_1)
        e_dw_2 = s2(x_dw[mask_p_dw], y_dw[mask_p_dw], f_func, p_dw_2)

        e_up = (e_up_1 + e_up_2) * 0.5
        e_dw = (e_dw_1 + e_dw_2) * 0.5

        # Corrections
        corr_up = np.where(
            x_up < 0,
            f_func(x_up, *p_up_1) - p_up_1[0],
            f_func(x_up, *p_up_2) - p_up_2[0]
        )

        corr_dw = np.where(
            x_dw < 0,
            f_func(x_dw, *p_dw_1) - p_dw_1[0],
            f_func(x_dw, *p_dw_2) - p_dw_2[0]
        )

        def poly_error(x, params, dparams):
            '''
            params: [a0, a1, a2, ...]
            dparams: relative uncertainties
            '''
            total = 0.0
            # Skip i=0 because a0 is the constant term
            for i in range(1, len(params)):
                total += ( (x**i) * dparams[i] )**2
            return np.sqrt(total)
        
        d_corr_up = np.where(
            x_up < 0,
            poly_error(x_up, p_up_1, dp_up_1),
            poly_error(x_up, p_up_2, dp_up_2)
        )

        d_corr_dw = np.where(
            x_dw < 0,
            poly_error(x_dw, p_dw_1, dp_dw_1),
            poly_error(x_dw, p_dw_2, dp_dw_2)
        )

        # Total error = dispersion + abs(d_corr)
        e_up = e_up + np.abs(d_corr_up)
        e_dw = e_dw + np.abs(d_corr_dw)

        # Apply correction to data
        y_up_corr = y_up - corr_up
        y_dw_corr = y_dw - corr_dw

        def close_fun(up_arr, q1, q2):
            ''' Close the loop using intercepts q1 and q2
            '''
            up_c  = np.copy(up_arr) - q1
            up_c *= 2/(abs(q2)+abs(q1))
            up_c  = up_c + q1/abs(q1) #- 1 if q1 < 0 else + 1
            return up_c

        # Apply close operation using intercepts q = intercept of negative and positive tail fits
        y_up_closed = close_fun(y_up_corr, p_up_1[0], p_up_2[0])
        y_dw_closed = close_fun(y_dw_corr, p_dw_1[0], p_dw_2[0])

        # Plot original data (black), corrected (red) and errors
        clear_fit_lines(ax)
        ax.clear()
        ax.plot(x_up/field_scale, y_up, 'k.-', label='Up raw',   markersize=3, alpha=0.5)
        ax.plot(x_dw/field_scale, y_dw, 'k.-', label='Down raw', markersize=3, alpha=0.5)
        
        # Add horizontal line at y=0
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=1)
        # Add vertical line at x=0
        ax.axvline(x=0, color='gray', linestyle='--', linewidth=1)

        # Plot corrected closed data with errorbars (use error arrays e_up, e_dw)
        ax.errorbar(x_up, y_up_closed, e_up, fmt='.', color='r', linestyle='-', label='Up corrected',   alpha=0.8)
        ax.errorbar(x_dw, y_dw_closed, e_dw, fmt='.', color='r', linestyle='-', label='Down corrected', alpha=0.8)

        # Fit coercivity
        try:
            x_n_start_hc = float(x_start_dw_hc_edit.text()) * field_scale
            x_n_end_hc   = float(x_end_dw_hc_edit.text())   * field_scale
            x_p_start_hc = float(x_start_up_hc_edit.text()) * field_scale
            x_p_end_hc   = float(x_end_up_hc_edit.text())   * field_scale
        except Exception:
            QMessageBox.critical(window, "Error", f"Invalid value for Hc range:\n{e}")
            return
        
        mask_n = (x_dw >= x_n_start_hc) & (x_dw <= x_n_end_hc)
        mask_p = (x_up >= x_p_start_hc) & (x_up <= x_p_end_hc)

        if mask_n.sum() < 2 or mask_p.sum() < 2:
            QMessageBox.critical(window, "Error", "Not enough points in coercive fit ranges.")
            return
        else :
            # Perform weighted fits
            popt_n, covm_n = curve_fit(g_func, x_dw[mask_n], y_dw_closed[mask_n], sigma=e_dw[mask_n], absolute_sigma=False)
            popt_p, covm_p = curve_fit(g_func, x_up[mask_p], y_up_closed[mask_p], sigma=e_up[mask_p], absolute_sigma=False)

            # Plot coercive fit lines
            t1 = np.linspace(x_n_start_hc, x_n_end_hc, 400)
            t2 = np.linspace(x_p_start_hc, x_p_end_hc, 400)
            ln, = ax.plot(t1, g_func(t1, *popt_n), 'b--', label='HC neg fit')
            ln.set_gid(f"fit_hc_neg")
            ln, = ax.plot(t2, g_func(t2, *popt_p), 'b--', label='HC pos fit')
            ln.set_gid(f"fit_hc_pos")

        # Store numerical results
        results_text_lines.append("Coercive fit results:")
        for p, val, err in zip(hc_param_names, popt_n, np.sqrt(np.diag(covm_n))):
            results_text_lines.append(f"{p} = {format_value_error(val, err)}")    
            
        for i , pi in zip(range(len(popt_n)), hc_param_names):
            for j , pj in zip(range(i+1, len(popt_n)), hc_param_names[i+1:]):
                corr_ij = covm_n[i, j]/np.sqrt(covm_n[i, i]*covm_n[j, j])
                results_text_lines.append(f"corr({pi}, {pj}) = {corr_ij:.3f}")
        
        for p, val, err in zip(hc_param_names, popt_p, np.sqrt(np.diag(covm_p))):
            results_text_lines.append(f"{p} = {format_value_error(val, err)}")    
            
        for i , pi in zip(range(len(popt_p)), hc_param_names):
            for j , pj in zip(range(i+1, len(popt_p)), hc_param_names[i+1:]):
                corr_ij = covm_n[i, j]/np.sqrt(covm_p[i, i]*covm_p[j, j])
                results_text_lines.append(f"corr({pi}, {pj}) = {corr_ij:.3f}")
    
        # Redraw legend and canvas
        ax.set_xlabel("H [Oe]", fontsize=15)
        ax.set_ylabel(r"M/M$_{sat}$", fontsize=15)
        # Add horizontal line at y=0
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=1)
        # Add vertical line at x=0
        ax.axvline(x=0, color='gray', linestyle='--', linewidth=1)
        ax.legend()
        canvas.draw()

        # Show textual results
        output_box.setPlainText("\n".join(results_text_lines))

        # Summary of results
        log_results_lines = []
        log_results_lines.append(f"Summary of correction for data in file {idx_src + 1}, columns {x_up_col}/{y_up_col} and {x_dw_col}/{y_dw_col}:")
        log_results_lines.append(f"Corrected data with field shift = {field_shift} and scale = {field_scale}")
        log_results_lines.append(f"Using tail fit function: {tail_function_edit.text()}")
        log_results_lines.append(f"Using coercive fit function: {hc_function_edit.text()}")
        log_results_lines.append(f"Using range limits (neg): {x_n_start/field_scale} to {x_n_end/field_scale}")
        log_results_lines.append(f"Using range limits (pos): {x_p_start/field_scale} to {x_p_end/field_scale}")
        log_results_lines.append(f"Using coercive fit ranges (down): {x_n_start_hc/field_scale} to {x_n_end_hc/field_scale}")
        log_results_lines.append(f"Using coercive fit ranges (up): {x_p_start_hc/field_scale} to {x_p_end_hc/field_scale}\n")
        logger.info("Loop correction completed. Summary:\n" + "\n".join(log_results_lines) +"\n".join(results_text_lines))

        # Save corrected columns if requested
        if save_idx is not None:
            df_dest = dataframes[save_idx]

            df_dest[x_up_dest.currentText()] = x_up
            df_dest[y_up_dest.currentText()] = y_up_closed

            df_dest[x_dw_dest.currentText()] = x_dw
            df_dest[y_dw_dest.currentText()] = y_dw_closed

            logger.info("Corrected columns saved to destination file.")

    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error running fits: {e}")
        logger.exception("Unhandled error in perform_all_fits: %s", e) 
    
        


