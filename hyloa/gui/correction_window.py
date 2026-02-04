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

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
     QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit, QMessageBox,
     QSizePolicy, QMdiSubWindow)
from PyQt5.QtWidgets import QScrollArea

from PyQt5.QtCore import Qt

from hyloa.data.correction import *
from hyloa.data.anisotropy import *

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

    • There is also the option to replace one branch by duplicating the other. This operation can only be performed on the correct data.

    • Configure the second fit block. This works exactly like the 'Quick Fit' window and can be used
    to extract properties such as coercive field or remanence. This second fit operates on the *corrected* data.
    So in this case the fit ranges must be chosen according to the *scaled* data.
    It is recommended to use simple low-order polynomials to fit coercivity or remanence regions.
    If there's a significant discrepancy between the coercives, you can shift the field values and rerun the fit by pressing the appropriate button.
    Note that this time the shift is incremental, so a second shift will be applied to data already shifted by the first shift.

    • Cubic spline fitting and symmetrization:
    After the drift correction, you may fit each branch using a cubic B-spline.
    This step is mainly intended for data symmetrization and for the estimation of the anisotropy field.
    The smoothing parameter controls how closely the spline follows the data:
    - s = 0 corresponds to an exact interpolation of the points;
    - s > 0 allows for smoothing and helps reduce the impact of noise.
    A reasonable value depends on the data quality and on the estimated experimental error.

    
    Parameters
    ----------
    app_instance : MainApp
        The main application instance containing dataframes and logger.
    '''
    dataframes  = app_instance.dataframes
    logger      = app_instance.logger

    plot_state = {
        "flipped"   : False,
        "done_corr" : False,
        "done_spl3" : False,
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
        "fit_hc_p"  : None,
        "spline_up" : None,
        "spline_dw" : None,
        "s_data_up" : None,
        "s_data_dw" : None
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
    
    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(left_widget)

    root_layout.addWidget(scroll_area, stretch=0)


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
            " These changes are not incremental, so you can safely change the value and press the button again.\n"
            "\n"
            "• Set the x_start / x_end limits for each branch. If the field is scaled, remember that "
            "the fit ranges must be chosen according to the *original*, non-scaled data; the scaling will be applied later.\n"
            "\n"
            "• Configure the first fit block, which is used to correct possible drifts at the end of each branch.\n"
            "You may use any polynomial or analytical function, but it is strongly recommended to avoid excessively "
            "high polynomial orders. The constant term MUST be the first parameter, exactly as shown in the example below.\n"
            "  (e.g. 'a + b*x + c*x**2').\n"
            "To proceed with the fit of the physical quantities, you must first press the button to perform the drift correction."
            "If a file has been selected for saving, the corrected data will be saved.\n"
            "\n"
            "• There is also the option to replace one branch by duplicating the other. This operation can only be performed on the correct data.\n"
            "\n"
            "• Configure the second fit block. This works exactly like the 'Quick Fit' window and can be used "
            "to extract properties such as coercive field or remanence. This second fit operates on the *corrected* data.\n"
            "So in this case the fit ranges must be chosen according to the *scaled* data.\n"
            "It is recommended to use simple low-order polinomials to fit coercivity or remenance regions.\n"
            "If there's a significant discrepancy between the coercives, you can shift the field values and rerun the fit by pressing the appropriate button.\n"
            "Note that this time the shift is incremental, so a second shift will be applied to data already shifted by the first shift.\n"
            "\n"
            "• Cubic spline fitting and symmetrization:\n"
            "After the drift correction, you may fit each branch using a cubic B-spline. "
            "This step is mainly intended for data symmetrization and for the estimation of the anisotropy field.\n"
            "The smoothing parameter controls how closely the spline follows the data:\n"
            "  - s = 0 corresponds to an exact interpolation of the points;\n"
            "  - s > 0 allows for smoothing and helps reduce the impact of noise.\n"
            "A reasonable value depends on the data quality and on the estimated experimental error.\n"
            "If you press the button to symmetrize the data and a file has been selected for saving, the symmetrized data will be saved.\n"
            "\n"
            "• By moving the mouse over the various boxes, a tooltip appears with information relating to them."
        )

        msg = QMessageBox(window)
        msg.setWindowTitle("Correction Guide")
        msg.setIcon(QMessageBox.Information)

        text = QTextEdit()
        text.setPlainText(help_text)
        text.setReadOnly(True)
        text.setMinimumSize(700, 500)

        layout = msg.layout()
        layout.addWidget(text, 0, 0, 1, layout.columnCount())

        msg.exec_()

    

    help_button = QPushButton("Help")
    help_button.setToolTip("Press for a quick user guide")
    help_button.clicked.connect(show_help_dialog)
    left_layout.addWidget(help_button, alignment=Qt.AlignLeft)

    #===============================================#
    # Load data                                     #
    #===============================================#

    # Selection of the file to process
    left_layout.addWidget(QLabel("Select data file (source):"))
    file_combo = QComboBox()
    file_combo.addItems([f"File {i+1}" for i in range(len(dataframes))])
    file_combo.setToolTip("File from which load data")
    left_layout.addWidget(file_combo)

    # Selecetion of the columns that contain the data
    box_data = QGridLayout()
    left_layout.addLayout(box_data)

    box_data.addWidget(QLabel("up: "), 0, 0)
    x_up_combo = QComboBox(); box_data.addWidget(x_up_combo, 0, 1)
    y_up_combo = QComboBox(); box_data.addWidget(y_up_combo, 0, 2)
    x_up_combo.setToolTip("x data for up branch")
    y_up_combo.setToolTip("y data for up branch")

    box_data.addWidget(QLabel("down: "), 1, 0)
    x_down_combo = QComboBox(); box_data.addWidget(x_down_combo, 1, 1)
    y_down_combo = QComboBox(); box_data.addWidget(y_down_combo, 1, 2)
    x_down_combo.setToolTip("x data for down branch")
    y_down_combo.setToolTip("y data for down branch")

    def update_columns_from_selected_file():
        ''' Update the column selection combos based on the selected source file.
        '''
        idx  = file_combo.currentIndex()
        cols = [c for c in list(dataframes[idx].columns) if str(c) != '']

        for combo in (x_up_combo, y_up_combo, x_down_combo, y_down_combo):
            # Block signals to avoid too rapid changes
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(cols)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)

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
    save_file_combo.setToolTip("File to store data. Suggest to use duplicate file to create it.")
    left_layout.addWidget(save_file_combo)

    # Selection of destination columns
    dest_box = QGridLayout()
    left_layout.addLayout(dest_box)

    dest_box.addWidget(QLabel("Save up:"), 0, 0)
    x_up_dest = QComboBox(); dest_box.addWidget(x_up_dest, 0, 1)
    y_up_dest = QComboBox(); dest_box.addWidget(y_up_dest, 0, 2)
    x_up_dest.setToolTip("In this variable the data on the x of the up branch will be stored.")
    y_up_dest.setToolTip("In this variable the data on the y of the up branch will be stored.")


    dest_box.addWidget(QLabel("Save down:"), 1, 0)
    x_dw_dest = QComboBox(); dest_box.addWidget(x_dw_dest, 1, 1)
    y_dw_dest = QComboBox(); dest_box.addWidget(y_dw_dest, 1, 2)
    x_dw_dest.setToolTip("In this variable the data on the x of the down branch will be stored.")
    y_dw_dest.setToolTip("In this variable the data on the y of the down branch will be stored.")


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
    field_shift_edit.setToolTip("Both field arrays will be shifted by this value. "
                                "The shift is applied before scaling.")
    st_grid.addWidget(field_shift_edit, 1, 0)

    field_scale_edit = QLineEdit("1")
    field_scale_edit.setToolTip("Both field arrays will be scaled by this value."
                                "The scaling will be applied after the shift")
    st_grid.addWidget(field_scale_edit, 1, 1)

    flip_btn = QPushButton("Check Symmetry")
    flip_btn.setToolTip("Revert up branch to visually check the symmetry.")
    st_grid.addWidget(flip_btn, 1, 2)

    #===============================================#
    # Set parameters for the mag corrections        #
    #===============================================#

    left_layout.addWidget(QLabel("-------- Fit for tail correction --------"))

    limits_grid = QGridLayout()
    left_layout.addLayout(limits_grid)

    x_start_n_edit = QLineEdit("-4000")
    x_end_n_edit   = QLineEdit("-400")

    x_start_n_edit.setToolTip("Left limit for fit in the negative field saturation zone.\n"
                              "If greater than the largest value of the fields, "
                              "data will be taken starting from the largest existing value.")
    x_end_n_edit.setToolTip("Right limit for fit in the negative field saturation zone.\n"
                            "Choose carefully based on the data.")
    
    limits_grid.addWidget(QLabel("x_start_neg:"), 0, 0)
    limits_grid.addWidget(x_start_n_edit,         0, 1)
    limits_grid.addWidget(QLabel("x_end_neg:"),   0, 2)
    limits_grid.addWidget(x_end_n_edit,           0, 3)

    x_start_p_edit = QLineEdit("400")
    x_end_p_edit   = QLineEdit("4000")

    x_start_p_edit.setToolTip("Left limit for fit in the positive field saturation zone.\n"
                              "Choose carefully based on the data.")
    x_end_p_edit.setToolTip("Right limit for fit in the positive field saturation zone.\n"
                            "If greater than the largest value of the fields, "
                            "data will be taken starting from the largest existing value.")
                            

    limits_grid.addWidget(QLabel("x_start_pos:"), 1, 0)
    limits_grid.addWidget(x_start_p_edit,         1, 1)
    limits_grid.addWidget(QLabel("x_end_pos:"),   1, 2)
    limits_grid.addWidget(x_end_p_edit,           1, 3)

    box_fit_params = QGridLayout()
    left_layout.addLayout(box_fit_params)
    box_fit_params.addWidget(QLabel("Parameter names (e.g. a,b):"), 0, 0)
    box_fit_params.addWidget(QLabel("Initial fit values (e.g. 1,1):"), 0, 1)

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
    run_button.setToolTip("Remove drift in the saturation zone")
    corr_btn_box.addWidget(run_button, 0, 0)

    del_cp_btn = QPushButton("Remove corrections")
    del_cp_btn.setToolTip("Remove from all done corrections from plot and delete them")
    corr_btn_box.addWidget(del_cp_btn, 0, 1)

    del_od_btn = QPushButton("Remove original data")
    del_od_btn.setToolTip("Remove original data from plot")
    corr_btn_box.addWidget(del_od_btn, 0, 2)

    box_options = QGridLayout()
    left_layout.addLayout(box_options)
    # Select option to duplicate a branch
    double_branch = QComboBox()
    double_branch.addItem("No")
    double_branch.addItem("Up")
    double_branch.addItem("Down")
    box_options.addWidget(QLabel("Duplicate branch: "), 0, 0)
    box_options.addWidget(double_branch, 0, 1)
    double_btn = QPushButton("Duplicate")
    box_options.addWidget(double_btn, 0, 2)

    #===============================================#
    # Data selection for parameter estimations      #
    #===============================================#

    data_used = QGridLayout()
    left_layout.addLayout(data_used)
    # Select option to duplicate a branch
    data_sel = QComboBox()
    data_sel.addItem("Original")
    data_sel.addItem("Corrected")
    data_used.addWidget(QLabel("Select data for fit: "), 0, 0)
    data_used.addWidget(data_sel, 0, 1)

    #===============================================#
    # Set parameters for coercivity computation     #
    #===============================================#

    left_layout.addWidget(QLabel("-------- Fit for coercivity/remenance estimation --------"))

    limits_grid_1 = QGridLayout()
    left_layout.addLayout(limits_grid_1)

    x_start_up_hc_edit = QLineEdit("100")
    x_end_up_hc_edit   = QLineEdit("300")

    x_start_up_hc_edit.setToolTip("Left limit for fit for up branch.\n"
                                  "Choose carefully based on the data.")
    x_end_up_hc_edit.setToolTip("Right limit for fit for up branch.\n"
                                "Choose carefully based on the data.")
    
    limits_grid_1.addWidget(QLabel("x_start_up:"), 0, 0)
    limits_grid_1.addWidget(x_start_up_hc_edit,    0, 1)
    limits_grid_1.addWidget(QLabel("x_end_up:"),   0, 2)
    limits_grid_1.addWidget(x_end_up_hc_edit,      0, 3)

    x_start_dw_hc_edit = QLineEdit("-300")
    x_end_dw_hc_edit   = QLineEdit("-100")

    x_start_dw_hc_edit.setToolTip("Left limit for fit for down branch.\n"
                                  "Choose carefully based on the data.")
    x_end_dw_hc_edit.setToolTip("Right limit for fit for down branch.\n"
                                "Choose carefully based on the data.")

    limits_grid_1.addWidget(QLabel("x_start_down:"), 1, 0)
    limits_grid_1.addWidget(x_start_dw_hc_edit,      1, 1)
    limits_grid_1.addWidget(QLabel("x_end_down:"),   1, 2)
    limits_grid_1.addWidget(x_end_dw_hc_edit,        1, 3)

    box_fit_params_1 = QGridLayout()
    left_layout.addLayout(box_fit_params_1)
    box_fit_params_1.addWidget(QLabel("Parameter names (e.g. a,b):"), 0, 0)
    box_fit_params_1.addWidget(QLabel("Initial fit values (e.g. 1,1):"),  0, 1)

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

    left_layout.addWidget(QLabel("-------- Final correction of the fields a posterior --------"))

    fit_btn_box = QGridLayout()
    left_layout.addLayout(fit_btn_box)
    
    fit_btn_box.addWidget(QLabel("Shift (i.e. H = H - shift)"), 0, 1)
    
    field_shift_pc_edit = QLineEdit("0")
    field_shift_pc_edit.setToolTip("This shift will be applied to the correct data.")
    fit_btn_box.addWidget(field_shift_pc_edit, 0, 2)

    field_shift_btn = QPushButton("Apply shift and fit again")
    field_shift_btn.setToolTip("Fit again corrected data after the shift.")
    fit_btn_box.addWidget(field_shift_btn, 0, 3)


    #===============================================#
    # Anisotropy Field estimation                   #
    #===============================================#

    left_layout.addWidget(QLabel("-------- Symmetrization and estimation of the anisotropy field --------"))

    box_spline = QGridLayout()
    left_layout.addWidget(QLabel("Smothing factor for up and down brach cubic spline fitting:"))

    left_layout.addLayout(box_spline)

    box_spline.addWidget(QLabel("Up branch:"), 0, 0)
    smooth_up_edit = QLineEdit("0.01")
    smooth_up_edit.setToolTip("Smoothing Bsline parameter for the up branch.\n"
                              "After correcting the data, the value is automatically changed, "
                              "providing a more accurate estimate based on the data error. \n"
                              "If 0 normal interpolation.")
    box_spline.addWidget(smooth_up_edit, 0, 1)

    box_spline.addWidget(QLabel("Dw branch:"), 0, 2)
    smooth_dw_edit = QLineEdit("0.01")
    smooth_up_edit.setToolTip("Smoothing Bspline parameter for the down branch.\n"
                              "After correcting the data, the value is automatically changed, "
                              "providing a more accurate estimate based on the data error.\n"
                              "If 0, normal interpolation.")
    box_spline.addWidget(smooth_dw_edit, 0, 3)

    spl3_btn_box = QGridLayout()
    left_layout.addLayout(spl3_btn_box)
    
    spl3_btn = QPushButton("Create spline")
    spl3_btn.setToolTip("Fit data with a cubic spline.")
    spl3_btn_box.addWidget(spl3_btn, 0, 0)

    sym_btn = QPushButton("Symmetrize loop")
    sym_btn.setToolTip("Create a new loop strating form the preconstructed spline.")
    spl3_btn_box.addWidget(sym_btn, 0, 1)

    del_sym_btn = QPushButton("Remove sym loop")
    del_sym_btn.setToolTip("Remove new loop form the plot and delete them.")
    spl3_btn_box.addWidget(del_sym_btn, 0, 2)

    hk_box = QGridLayout()
    left_layout.addLayout(hk_box)

    hk_box.addWidget(QLabel("Closure threshold:"), 0, 0)
    hk_thr_edit = QLineEdit("0.02")
    hk_thr_edit.setToolTip("Threshold below which the relative difference of the branches must be to find the closing point.")
    hk_box.addWidget(hk_thr_edit, 0, 1)
    hk_btn = QPushButton("Compute anisotropy field")
    hk_box.addWidget(hk_btn, 0, 2)
    

    #===============================================#

    left_layout.addStretch(1)
   
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
    output_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    output_box.setMaximumHeight(140)

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
                fmt='.', color='r', label="Up corrected",
                alpha=0.5 if plot_state["done_spl3"] else 1
            )

        if plot_state.get("x_dw_corr") is not None:

            ax.errorbar(
                plot_state["x_dw_corr"], plot_state["y_dw_corr"],
                yerr=plot_state["e_dw"], linestyle='-', 
                fmt='.', color='r', label="Down corrected",
                alpha=0.5 if plot_state["done_spl3"] else 1
            )

        #==========================================================#
        # Fit lines                                                #
        #==========================================================#
        if plot_state.get("fit_hc_n") is not None:
            ax.plot(*plot_state["fit_hc_n"], 'b--', label="HC neg fit")

        if plot_state.get("fit_hc_p") is not None:
            ax.plot(*plot_state["fit_hc_p"], 'b--', label="HC pos fit")

        #==========================================================#
        # Spline lines                                             #
        #==========================================================#
        if plot_state.get("spline_up") is not None:
            ax.plot(*plot_state["spline_up"], '-', color='navy', label="spl3 Up")

        if plot_state.get("spline_dw") is not None:
            ax.plot(*plot_state["spline_dw"], '-', color='navy', label="spl3 Dw")

        #==========================================================#
        # Symmetrizied data                                        #
        #==========================================================#
        if plot_state.get("s_data_up") is not None:
            ax.plot(*plot_state["s_data_up"], 'k.-', label="sym Up")

        if plot_state.get("s_data_dw") is not None:
            ax.plot(*plot_state["s_data_dw"], 'k.-', label="sym Dw")

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
            smooth_up_edit, smooth_dw_edit,
            dataframes, logger, plot_state, draw_plot,
            window, 
        )
    )

    flip_btn.clicked.connect(lambda: flip(
            plot_state, window, draw_plot
        )
    ) 

    del_cp_btn.clicked.connect(lambda: change_ps(
            plot_state, window, draw_plot, mode="cp"
        )
    )

    del_od_btn.clicked.connect(lambda:change_ps(
            plot_state, window, draw_plot, mode="od"
        )
    )

    fit_btn.clicked.connect(lambda : fit_data(
            file_combo,
            x_up_combo, y_up_combo, x_down_combo, y_down_combo, data_sel,
            x_start_up_hc_edit, x_end_up_hc_edit, x_start_dw_hc_edit, x_end_dw_hc_edit,
            hc_params_edit, hc_function_edit, logger, plot_state, draw_plot,
            output_box, window
        )
    )

    double_btn.clicked.connect(lambda : flip_data(
            file_combo,
            x_up_combo, y_up_combo, x_down_combo, y_down_combo, data_sel,
            double_branch, plot_state,
            window, logger, draw_plot
        )
    )
    
    field_shift_btn.clicked.connect(lambda: apply_shift(
            x_up_dest, y_up_dest, x_dw_dest, y_dw_dest, dataframes, save_file_combo, data_sel,
            field_shift_pc_edit, plot_state, window, fit_data, args=(
                file_combo,
                x_up_combo, y_up_combo, x_down_combo, y_down_combo, data_sel,
                x_start_up_hc_edit, x_end_up_hc_edit, x_start_dw_hc_edit, x_end_dw_hc_edit,
                hc_params_edit, hc_function_edit, logger, plot_state, draw_plot,
                output_box, window
            ),
            logger=logger)
    )

    spl3_btn.clicked.connect(lambda: compute_b_spline(
            file_combo, x_up_combo, y_up_combo, x_down_combo, y_down_combo, data_sel,
            smooth_up_edit, smooth_dw_edit,
            plot_state, logger, window, draw_plot

        )
    )

    sym_btn.clicked.connect(lambda: symmetrize(
            file_combo, save_file_combo,
            x_up_combo, y_up_combo, x_down_combo, y_down_combo, data_sel,
            x_up_dest,  y_up_dest,  x_dw_dest,    y_dw_dest,
            dataframes, logger, plot_state, draw_plot,
            window, 
        )
    )

    del_sym_btn.clicked.connect(lambda:change_ps(
            plot_state, window, draw_plot, mode="sym"
        )
    )

    hk_btn.clicked.connect(lambda: compute_Hk(
            file_combo, x_up_combo, y_up_combo, x_down_combo, y_down_combo,
            hk_thr_edit, plot_state, logger, window, output_box
        )
    )
        
    # Sub-window for fitting panel
    sub = QMdiSubWindow()
    sub.setWidget(window)
    sub.setWindowTitle("Loop Correction")
    #sub.resize(1200, 900)
    sub.resize(window.sizeHint())

    app_instance.mdi_area.addSubWindow(sub)
    sub.show()