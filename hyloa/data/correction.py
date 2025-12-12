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

    Help guide:

    • Select the main data file and choose the four X/Y columns that define the Up and Down branches of the loop.
    These selections must correspond to the same variables shown in the plotting window.

    • Optionally, you may select a second file where corrected data will be saved.
    The corrected columns will be written in the corresponding positions of the destination grid,
    so the layout of the two 2x2 grids matches (Up/Down x X/Y).

    • You can shift and scale the field array. Remember that the first change that is applied is the shift and then the scaling.
    These changes are not incremental, so you can safely change the value and press the button again.

    • Set the x_start / x_end limits for each branch. If the field is scaled, remember that
    the fit ranges must be chosen according to the *original*, non-scaled data; the scaling will be applied later.

    • Configure the first fit block, which is used to correct possible drifts at the end of each branch.
    You may use any polynomial or analytical function, but it is strongly recommended to avoid excessively
    high polynomial orders. The constant term MUST be the first parameter, exactly as shown in the example below.
    (e.g. 'a + b*x + c*x**2').
    To proceed with the fit of the physical quantities, you must first press the button to perform the drift correction.

    • Configure the second fit block. This works exactly like the 'Quick Fit' window and can be used
    to extract properties such as coercive field or remanence. This second fit operates on the *corrected* data.
    So in this case the fit ranges must be chosen according to the *scaled* data.
    It is recommended to use simple low-order polynomials to fit coercivity or remanence regions.
    If there's a significant discrepancy between the coercives, you can shift the field values and rerun the fit by pressing the appropriate button.
    Note that this time the shift is incremental, so a second shift will be applied to data already shifted by the first shift.

    
    Parameters
    ----------
    app_instance : MainApp
        The main application instance containing dataframes and logger.
    '''
    dataframes  = app_instance.dataframes
    logger      = app_instance.logger

    # Variables to store last preview of selected data
    last_x_up = None
    last_y_up = None
    last_x_dw = None
    last_y_dw = None

    plot_state = {
        "flipped"   : False,
        "done_corr" : False,
        "x_up"      : None,
        "y_up"      : None,
        "x_dw"      : None,
        "y_dw"      : None,
        "x_up_corr" : None,
        "y_up_corr" : None,
        "x_dw_corr" : None,
        "y_dw_corr" : None,
        "e_up"      : None,
        "e_dw"      : None,
        "fit_hc_n"  : None,
        "fit_hc_p"  : None
    }


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
            "• Optionally, you may select a second file where corrected data will be saved.\n"
            "The corrected columns will be written in the corresponding positions of the destination grid, "
            "so the layout of the two 2x2 grids matches (Up/Down x X/Y).\n"
            "\n"
            "• You can shift and scale the field array, remember that the first change that is applied is the shift and then the scaling. \n"
            " These changes are not incremental, so you can safely change the value and press the button again."
            "\n"
            "• Set the x_start / x_end limits for each branch. If the field is scaled, remember that "
            "the fit ranges must be chosen according to the *original*, non-scaled data; the scaling will be applied later.\n"
            "\n"
            "• Configure the first fit block, which is used to correct possible drifts at the end of each branch.\n"
            "You may use any polynomial or analytical function, but it is strongly recommended to avoid excessively "
            "high polynomial orders. The constant term MUST be the first parameter, exactly as shown in the example below.\n"
            "  (e.g. 'a + b*x + c*x**2').\n"
            "To proceed with the fit of the physical quantities, you must first press the button to perform the drift correction.\n"
            "\n"
            "• Configure the second fit block. This works exactly like the 'Quick Fit' window and can be used "
            "to extract properties such as coercive field or remanence. This second fit operates on the *corrected* data.\n"
            "So in this case the fit ranges must be chosen according to the *scaled* data.\n"
            "It is recommended to use simple low-order polinomials to fit coercivity or remenance regions.\n"
            "If there's a significant discrepancy between the coercives, you can shift the field values and rerun the fit by pressing the appropriate button.\n"
            "Note that this time the shift is incremental, so a second shift will be applied to data already shifted by the first shift."
            "\n"
        )

        QMessageBox.information(window, "Correction Guide", help_text)
    

    help_button = QPushButton("Help")
    help_button.clicked.connect(show_help_dialog)
    left_layout.addWidget(help_button, alignment=Qt.AlignLeft)

    #===============================================#
    # Load data                                     #
    #===============================================#

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

    #===============================================#
    # Store data                                    #
    #===============================================#
    
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
    # Set parameters for the field corrections      #
    #===============================================#

    left_layout.addWidget(QLabel("-------- Preliminary field changes --------"))

    st_grid = QGridLayout()
    left_layout.addLayout(st_grid)
    st_grid.addWidget(QLabel("Shift (i.e. H = H - shift)"), 0, 0)
    st_grid.addWidget(QLabel("Scale (i.e. H = H * scale)"), 0, 1)
    st_grid.addWidget(QLabel("Revert a branch"),            0, 2)

    
    field_shift_edit = QLineEdit("0")
    st_grid.addWidget(field_shift_edit, 1, 0)

    field_scale_edit = QLineEdit("1")
    st_grid.addWidget(field_scale_edit, 1, 1)

    flip_btn         = QPushButton("Check Symmetry")
    st_grid.addWidget(flip_btn, 1, 2)

    #===============================================#
    # Set parameters for the mag corrections        #
    #===============================================#

    left_layout.addWidget(QLabel("-------- Fit for tail correction --------"))

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

    box_fit_params.addWidget(QLabel("Function (e.g. a + b*x) :"), 2, 0)
    tail_function_edit = QLineEdit("a + b*x")
    box_fit_params.addWidget(tail_function_edit, 2, 1)

    #===============================================#
    # Correction buttons                            #
    #===============================================#

    corr_btn_box = QGridLayout()
    left_layout.addLayout(corr_btn_box)
    
    run_button = QPushButton("Apply drift correction")
    corr_btn_box.addWidget(run_button, 0, 0)

    del_cp_btn = QPushButton("Remove ccorrections")
    corr_btn_box.addWidget(del_cp_btn, 0, 1)

    #===============================================#
    # Set parameters for coercivity computation     #
    #===============================================#

    left_layout.addWidget(QLabel("-------- Fit for coercivity/remenance estimation --------"))

    limits_grid_1 = QGridLayout()
    left_layout.addLayout(limits_grid_1)

    x_start_up_hc_edit = QLineEdit("100")
    x_end_up_hc_edit   = QLineEdit("300")
    
    limits_grid_1.addWidget(QLabel("x_start_up"), 0, 0)
    limits_grid_1.addWidget(x_start_up_hc_edit,   0, 1)
    limits_grid_1.addWidget(QLabel("x_end_up"),   0, 2)
    limits_grid_1.addWidget(x_end_up_hc_edit,     0, 3)

    x_start_dw_hc_edit = QLineEdit("-300")
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

    fit_btn_box = QGridLayout()
    left_layout.addLayout(fit_btn_box)

    fit_btn_box.addWidget(QLabel("Function (e.g. s*(x - hc) ):"), 0, 0)
    hc_function_edit = QLineEdit("s*(x - hc)")
    fit_btn_box.addWidget(hc_function_edit, 0, 1)

    fit_btn = QPushButton("fit")
    fit_btn_box.addWidget(fit_btn, 0, 2)

    #===============================================#
    # Correction buttons                            #
    #===============================================#

    fit_btn_box = QGridLayout()
    left_layout.addLayout(fit_btn_box)
    
    fit_btn_box.addWidget(QLabel("Shift (i.e. H = H - shift)"), 0, 1)
    
    field_shift_pc_edit = QLineEdit("0")
    fit_btn_box.addWidget(field_shift_pc_edit, 0, 2)

    field_shift_btn = QPushButton("Apply shift and fit again")
    fit_btn_box.addWidget(field_shift_btn, 0, 3)


    #===============================================#
    # 
    #===============================================#


    left_layout.addWidget(QLabel("-------- Symmetrization and estimation of the anisotropy field --------"))

    """
    # Select option to duplicate a branch
    double_branch = QComboBox()
    double_branch.addItem("No")
    double_branch.addItem("Up")
    double_branch.addItem("Down")
    box_options.addWidget(QLabel("Duplicate branch: "), 0, 2)
    box_options.addWidget(double_branch, 0, 3)
    """

    #===============================================#

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

    def draw_plot():
        ax.clear()

        # flip factor (non altera i dati direttamente)
        mul = -1 if plot_state["flipped"] else 1

        #==========================================================#
        # Raw data                                                 #
        #==========================================================#
        if plot_state["x_up"] is not None and plot_state["y_up"] is not None:

            ax.plot(plot_state["x_up"] * mul, plot_state["y_up"] * mul, 'k.-',
                    label="Up raw", alpha=0.5 if plot_state["done_corr"] else 1)
            
        if plot_state["x_dw"] is not None and plot_state["y_dw"] is not None:

            ax.plot(plot_state["x_dw"], plot_state["y_dw"], 'k.-', 
                    label="Down raw", alpha=0.5 if plot_state["done_corr"] else 1)

        #==========================================================#
        # Corrected data                                           #    
        #==========================================================#
        if plot_state.get("x_up_corr") is not None:

            ax.errorbar(
                plot_state["x_up_corr"] * mul, plot_state["y_up_corr"] * mul,
                yerr=plot_state["e_up"], linestyle='-', 
                fmt='.', color='r', label="Up corrected"
            )

        if plot_state.get("x_dw_corr") is not None:

            ax.errorbar(
                plot_state["x_dw_corr"], plot_state["y_dw_corr"],
                yerr=plot_state["e_dw"], linestyle='-', 
                fmt='.', color='r', label="Down corrected"
            )

        #==========================================================#
        # Fit lines                                                #
        #==========================================================#
        if plot_state.get("fit_hc_n") is not None:
            xfit, yfit = plot_state["fit_hc_n"]
            ax.plot(xfit, yfit, 'b--', label="HC neg fit")

        if plot_state.get("fit_hc_p") is not None:
            xfit, yfit = plot_state["fit_hc_p"]
            ax.plot(xfit, yfit, 'b--', label="HC pos fit")

        #==========================================================#
        ax.axhline(0, color='gray', linestyle='--', linewidth=1)
        ax.axvline(0, color='gray', linestyle='--', linewidth=1)

        if ax.get_legend_handles_labels()[1]:
            ax.legend()

        ax.set_xlabel("H [Oe]", fontsize=15)
        ax.set_ylabel("M/M$_{sat}$", fontsize=15)

        fig.tight_layout()
        canvas.draw()


    #================================================#
    # Helper function for plot and preview refresh   #
    #================================================#
    def get_preview_data():
        ''' Get initial data for preview plot
        '''
        idx = file_combo.currentIndex()
        df  = dataframes[idx]

        x_up = df[x_up_combo.currentText()].astype(float).values
        y_up = df[y_up_combo.currentText()].astype(float).values
        x_dw = df[x_down_combo.currentText()].astype(float).values
        y_dw = df[y_down_combo.currentText()].astype(float).values

        return x_up, y_up, x_dw, y_dw

    def refresh_preview(x_up, y_up, x_dw, y_dw):
        ''' Draw selected data on canvas
        '''
        nonlocal last_x_up, last_y_up, last_x_dw, last_y_dw
        # Local savaing to concatenate changes
        last_x_up = x_up
        last_y_up = y_up
        last_x_dw = x_dw
        last_y_dw = y_dw

        try:
            plot_state.update({
                "x_up": x_up,
                "y_up": y_up,
                "x_dw": x_dw,
                "y_dw": y_dw,
            })
            draw_plot()

        except Exception as e:
            QMessageBox.critical("Error refreshing preview: %s", e)


    # Connect changes to update preview
    for cb in (x_up_combo, y_up_combo, x_down_combo, y_down_combo, file_combo):
        try:
            cb.currentIndexChanged.connect(
                lambda : refresh_preview(*get_preview_data())
            )
        except Exception:
            pass

    #================================================#
    # Button connections                             #
    #================================================#
    
    # Connect run button
    run_button.clicked.connect(lambda: perform_correction(
            file_combo, save_file_combo,
            x_up_combo, y_up_combo, x_down_combo, y_down_combo,
            field_shift_edit, field_scale_edit,
            x_start_n_edit, x_end_n_edit, x_start_p_edit, x_end_p_edit,
            tail_params_edit, tail_function_edit,
            x_up_dest, y_up_dest, x_dw_dest, y_dw_dest,
            dataframes, logger, plot_state, draw_plot,
            window, 
        )
    )

    flip_btn.clicked.connect(lambda: flip(
            plot_state, window, draw_plot
        )
    ) 

    del_cp_btn.clicked.connect(lambda: change_ps(
            plot_state, window, draw_plot
        )
    )

    fit_btn.clicked.connect(lambda : fit_data(
            file_combo,
            x_up_combo, y_up_combo, x_down_combo, y_down_combo,
            x_start_up_hc_edit, x_end_up_hc_edit, x_start_dw_hc_edit, x_end_dw_hc_edit,
            hc_params_edit, hc_function_edit, logger, plot_state, draw_plot,
            output_box, window
        )
    )
    
    field_shift_btn.clicked.connect(lambda: apply_shift(
            field_shift_pc_edit, plot_state, window, fit_data, args=(
                file_combo,
                x_up_combo, y_up_combo, x_down_combo, y_down_combo,
                x_start_up_hc_edit, x_end_up_hc_edit, x_start_dw_hc_edit, x_end_dw_hc_edit,
                hc_params_edit, hc_function_edit, logger, plot_state, draw_plot,
                output_box, window
            )
        )
    )
        
    # Sub-window for fitting panel
    sub = QMdiSubWindow()
    sub.setWidget(window)
    sub.setWindowTitle("Loop Correction")
    sub.resize(1200, 800)
    app_instance.mdi_area.addSubWindow(sub)
    sub.show()

#================================================#
# Function to chek simmetry by flipping a branch #
#================================================#

def change_ps(plot_state, window, draw_plot):

    try:
        plot_state.update({
            "done_corr": False,
            "x_up_corr": None,
            "y_up_corr": None,
            "e_up"     : None,
            "x_dw_corr": None,
            "y_dw_corr": None,
            "e_dw"     : None,
            "fit_hc_p" : None,
            "fit_hc_n" : None
        })
        draw_plot()

    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error during flip:\n{e}")

#================================================#
# Function to chek simmetry by flipping a branch #
#================================================#

def flip(plot_state, window, draw_plot):
    '''
    Function to flip a brach to ensure simmetricity of the loop.

    Parameters
    ----------
    plot_state : dict
        dictionary of the plotted data
    window : QWidget
        The main window widget.
    draw_plot : callable
        Function to update the preview
    '''
    try:
        plot_state["flipped"] = not plot_state["flipped"]
        draw_plot()

    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error during flip:\n{e}")

#================================================#
# Function to correct field                      #
#================================================#

def apply_shift(field_shift_pc_edit, plot_state, window, fit_data, args=()):
    '''
    Function add a field shift after the corrections

    Parameters
    ----------
    field_shift_pc_edit : QLineEdit
        Value for field shifting
    window : QWidget
        The main window widget.
    plot_state : dict
        dictionary of the plotted data
    fit_data : callable
        Function for fitting data
    args : tuple
        Argumets to pass to fit_data
    '''
    try:

        field_shift = float(field_shift_pc_edit.text())
        plot_state["x_up_corr"] -= field_shift
        plot_state["x_dw_corr"] -= field_shift

        fit_data(*args)

    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error applying shift:\n{e}")


#================================================#
# MAIN CORRECTION FUNCTION                       #
#================================================#

def perform_correction(file_combo, save_file_combo,
                       x_up_combo, y_up_combo, x_down_combo, y_down_combo,
                       field_shift_edit, field_scale_edit,
                       x_start_n_edit, x_end_n_edit, x_start_p_edit, x_end_p_edit,
                       tail_params_edit, tail_function_edit,
                       x_up_dest, y_up_dest, x_dw_dest, y_dw_dest,
                       dataframes, logger, plot_state, draw_plot,
                       window):
    ''' 
    Perform the loop correction using the parameters from the UI.
    The correction involves fitting the saturation parts (tails) of the hystersis loop
    to remove drifts.

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
    dataframes : list of pd.DataFrame
        List of dataframes containing loaded data.
    logger : Logger
        Logger of the application.
    plot_state : dict
        dictionary of the plotted data
    draw_plot : callable
        Function to update the preview
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

        """
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
        """

        # Read tail ranges
        try:
            x_n_start = float(x_start_n_edit.text()) * field_scale # For up negative region
            x_n_end   = float(x_end_n_edit.text()) * field_scale
        except Exception:
            # fallback
            x_n_start, x_n_end = -4000,  -1000

        try:
            x_p_start = float(x_start_p_edit.text()) * field_scale # For up positive region
            x_p_end   = float(x_end_p_edit.text()) * field_scale 
        except Exception:
            x_p_start, x_p_end = 1000, 4000

        # Masks for up/down tails split by sign
        mask_n_up = (x_up >= x_n_start) & (x_up <= x_n_end)
        mask_p_up = (x_up >= x_p_start) & (x_up <= x_p_end)
        mask_n_dw = (x_dw >= x_n_start) & (x_dw <= x_n_end)
        mask_p_dw = (x_dw >= x_p_start) & (x_dw <= x_p_end)
        
        #=========================================#
        # Auxiliary functions for fitting         #
        #=========================================#

        try:
            tail_param_names = [p.strip() for p in tail_params_edit.text().split(",") if p.strip() != ""]
            func_code_tail   = f"lambda x, {', '.join(tail_param_names)}: {tail_function_edit.text()}"
            f_func           = eval(func_code_tail, {"np": np, "__builtins__": {}})
        
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Invalid function for tail fit:\n{e}")
            return
        
        s2 = lambda x, y, f, popt: sum((y-f(x, *popt))**2)/(len(x)-len(popt))

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

        #=========================================#

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

        plot_state.update({
            "done_corr": True,
            "x_up_corr": x_up,
            "y_up_corr": y_up_closed,
            "e_up"     : e_up,
            "x_dw_corr": x_dw,
            "y_dw_corr": y_dw_closed,
            "e_dw"     : e_dw,
        })
        draw_plot()

        # Summary of results
        log_results_lines = []
        log_results_lines.append(f"Summary of correction for data in file {idx_src + 1}, columns {x_up_col}/{y_up_col} and {x_dw_col}/{y_dw_col}:")
        log_results_lines.append(f"Corrected data with field shift = {field_shift} and scale = {field_scale}")
        log_results_lines.append(f"Using tail fit function: {tail_function_edit.text()}")
        log_results_lines.append(f"Using range limits (neg): {x_n_start/field_scale} to {x_n_end/field_scale}")
        log_results_lines.append(f"Using range limits (pos): {x_p_start/field_scale} to {x_p_end/field_scale}\n")
        logger.info("Loop correction completed. Summary:\n" + "\n".join(log_results_lines))

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
    

#===================================================================#
# Function to fit for physiscal quantities                          #
#===================================================================#       

def fit_data(file_combo,
             x_up_combo, y_up_combo, x_down_combo, y_down_combo,
             x_start_up_hc_edit, x_end_up_hc_edit, x_start_dw_hc_edit, x_end_dw_hc_edit,
             hc_params_edit, hc_function_edit, logger, plot_state, draw_plot,
             output_box, window):
    '''
    Parameters
    ----------
    file_combo : QComboBox
        Combo box to select source data file.
    x_up_combo : QComboBox
        Combo box to select X column for Up branch.
    y_up_combo : QComboBox
        Combo box to select Y column for Up branch.
    x_down_combo : QComboBox
        Combo box to select X column for Down branch.
    y_down_combo : QComboBox
        Combo box to select Y column for Down branch.
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
    logger : Logger
        Logger of the application.
    plot_state : dict
        dictionary of the plotted data
    draw_plot : callable
        Function to update the preview
    output_box : QTextEdit
        Text edit for displaying output results.
    window : QWidget
        The main window widget.
    '''
    try : 
        idx_src = file_combo.currentIndex()
    
        # Read x/y column names
        x_up_col = x_up_combo.currentText()
        y_up_col = y_up_combo.currentText()
        x_dw_col = x_down_combo.currentText()
        y_dw_col = y_down_combo.currentText()

        #Read data
        x_up = plot_state["x_up_corr"]
        y_up = plot_state["y_up_corr"]
        x_dw = plot_state["x_dw_corr"]
        y_dw = plot_state["y_dw_corr"]
        e_up = plot_state["e_up"]
        e_dw = plot_state["e_dw"]
        
        if e_up is None:
            QMessageBox.critical(window, "Error", f"You need to correct data first")
            return

        
        results_text_lines =  []
        try:
            hc_param_names = [p.strip() for p in hc_params_edit.text().split(",") if p.strip() != ""]
            func_code_hc   = f"lambda x, {', '.join(hc_param_names)}: {hc_function_edit.text()}"
            g_func         = eval(func_code_hc, {"np": np, "__builtins__": {}})
        
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Invalid function for coercive fit:\n{e}")
            return
        
        # Fit coercivity
        try:
            x_n_start_hc = float(x_start_dw_hc_edit.text())
            x_n_end_hc   = float(x_end_dw_hc_edit.text())
            x_p_start_hc = float(x_start_up_hc_edit.text())
            x_p_end_hc   = float(x_end_up_hc_edit.text())
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Invalid value for Hc range:\n{e}")
            return
        
        mask_n = (x_dw >= x_n_start_hc) & (x_dw <= x_n_end_hc)
        mask_p = (x_up >= x_p_start_hc) & (x_up <= x_p_end_hc)

        if mask_n.sum() < 2 or mask_p.sum() < 2:
            QMessageBox.critical(window, "Error", "Not enough points in coercive fit ranges.")
            return
        else :
            # Perform weighted fits
            popt_n, covm_n = curve_fit(g_func, x_dw[mask_n], y_dw[mask_n], sigma=e_dw[mask_n])
            popt_p, covm_p = curve_fit(g_func, x_up[mask_p], y_up[mask_p], sigma=e_up[mask_p])

        
        t1 = np.linspace(x_n_start_hc, x_n_end_hc, 400)
        t2 = np.linspace(x_p_start_hc, x_p_end_hc, 400)

        plot_state.update({
            "fit_hc_p" : (t1, g_func(t1, *popt_n)),
            "fit_hc_n" : (t2, g_func(t2, *popt_p))
        })
        draw_plot()

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

        # Show textual results
        output_box.setPlainText("\n".join(results_text_lines))

        # Summary of results
        log_results_lines = []
        log_results_lines.append(f"Summary of fit for data in file {idx_src + 1}, columns {x_up_col}/{y_up_col} and {x_dw_col}/{y_dw_col}:")
        log_results_lines.append(f"Using fit function: {hc_function_edit.text()}")
        log_results_lines.append(f"Using fit ranges (down): {x_n_start_hc} to {x_n_end_hc}")
        log_results_lines.append(f"Using fit ranges (up): {x_p_start_hc} to {x_p_end_hc}\n")
        logger.info("Fit completed. Summary:\n" + "\n".join(log_results_lines) +"\n".join(results_text_lines))
    
    except Exception as e:
        QMessageBox.critical(window, "Error", f"Error during fitting:\n{e}")
        return

