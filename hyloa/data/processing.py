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
Code that contains some standard operations to do on the data.
"""
import numpy as np
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton,
    QMessageBox, QScrollArea, QWidget, QHBoxLayout, QMdiSubWindow, QLineEdit,
    QRadioButton, QButtonGroup
)

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

#==============================================================================================#
# Function to normalize curves in the interval [-1, 1]                                         #
#==============================================================================================#

def norm_dialog(plot_instance, app_instance):
    '''
    Qt window to select file and columns for normalization.

    Parameters
    ----------
    plot_instance : QWidget
        Widget that called this dialog (usually the plot panel).
    app_instance : MainApp
        Main application instance containing the session.
    '''
    
    if not hasattr(plot_instance, "figure") or plot_instance.figure is None:
        QMessageBox.critical(plot_instance, "Error", "No plot open!")
        return

    fig = plot_instance.figure
    ax = plot_instance.ax

    lines = ax.lines

    # === Remove grid ===
    filtered_lines = []
    for line in lines:
        x_data, y_data = line.get_xdata(), line.get_ydata()
        if not (
            (all(y == 0 for y in y_data) and len(set(x_data)) > 1) or
            (all(x == 0 for x in x_data) and len(set(y_data)) > 1) or
            (line.get_gid() == "fit")
        ):
            filtered_lines.append(line)

    lines = filtered_lines
    

    if not lines:
        QMessageBox.critical(plot_instance, "Error", "No valid cycles in plot!")
        return

    cycles       = []
    cycle_map    = {}    # label -> index
    cycle_checks = {}

    for i in range(0, len(lines), 2):
        idx = i // 2

        label = plot_instance.plot_customizations.get(
            idx, {}
        ).get("label", f"Cycle {idx + 1}")

        cycles.append(label)
        cycle_map[label] = idx
    
    # === Dialog ===
    dialog = QDialog(plot_instance)
    dialog.setWindowTitle("Normalize Cycles")

    layout = QVBoxLayout(dialog)

    layout.addWidget(QLabel("Select cycles to normalize:"))

    scroll_area   = QScrollArea()
    scroll_widget = QWidget()
    scroll_layout = QVBoxLayout(scroll_widget)

    # Checkbox cicli
    for label in cycles:
        cb = QCheckBox(label)
        scroll_layout.addWidget(cb)
        cycle_checks[label] = cb

    scroll_widget.setLayout(scroll_layout)
    scroll_area.setWidget(scroll_widget)
    scroll_area.setWidgetResizable(True)

    layout.addWidget(scroll_area)

    # === BUtton apply ===
    def apply():
        selected_cols      = []
        selected_files_idx = []

        try:
            for label, cb in cycle_checks.items():
                if cb.isChecked():

                    idx   = cycle_map[label]
                    line1 = lines[idx * 2]
                    line2 = lines[idx * 2 + 1]

                    cols1 = getattr(line1, "_cols", None)
                    cols2 = getattr(line2, "_cols", None)
                    index = getattr(line1, "_file_index", None)

                    if index:
                        selected_files_idx.append(index)

                    if cols1:
                        selected_cols.append(cols1[1]) # Y column of the first branch
                    if cols2:
                        selected_cols.append(cols2[1]) # Y column of the second branch

        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Selection error:\n{e}")
            return

        if not selected_cols:
            QMessageBox.critical(dialog, "Error", "Select at least one cycle.")
            return

        dialog.accept()
        
        apply_norm(plot_instance, app_instance, selected_files_idx, selected_cols)

    apply_button = QPushButton("Apply")
    apply_button.setObjectName("apply_button")
    apply_button.clicked.connect(apply)

    layout.addWidget(apply_button)

    dialog.exec_()

def apply_norm(plot_instance, app_instance, file_index, selected_cols):
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
    plot_instance : instance of the plot class
        Instance of the plot class
    app_instance : MainApp
        Main application instance containing the session data.
    file_index : list
        list of indices of the selected DataFrames.
    selected_cols : list
        List of columns to normalize (should be pairs).
    '''

    parent_widget  = plot_instance
    logger         = app_instance.logger

    try:
        for idx, y1, y2 in zip(file_index, selected_cols[::2], selected_cols[1::2]):
            df = app_instance.dataframes[idx]
        
            ell_up = df[y1].astype(float).values
            ell_dw = df[y2].astype(float).values

            # Compute averages at start/end
            aveup1 = np.mean(ell_up[:5])
            aveup2 = np.mean(ell_up[-5:])
            avedw1 = np.mean(ell_dw[:5])
            avedw2 = np.mean(ell_dw[-5:])

            # Branch direction correction
            if ((aveup1 > aveup2 and avedw1 > avedw2) or (aveup1 < aveup2 and avedw1 < avedw2)):
                aveup1 = (aveup1 + avedw1) * 0.5
                avedw1 = (aveup2 + avedw2) * 0.5
            else:
                aveup1 = (aveup1 + avedw2) * 0.5
                avedw1 = (aveup2 + avedw1) * 0.5

            v_shift = (aveup1 + avedw1) * 0.5
            v_amplitude = abs(aveup1 - avedw1) * 0.5

            # Normalize
            ell_up_normalized = (ell_up - v_shift) / v_amplitude
            ell_dw_normalized = (ell_dw - v_shift) / v_amplitude

            df[y1] = ell_up_normalized
            df[y2] = ell_dw_normalized
            logger.info(f"Normalization applied to {y1}.")
            logger.info(f"Normalization applied to {y2}.")
        
        # Re-plot
        plot_instance.plot()

        QMessageBox.information(plot_instance, "Success",
            f"Normalization applied on Files {[idx + 1 for idx in file_index]} and columns {selected_cols}"
        )
        
    except Exception as e:
        QMessageBox.critical(parent_widget, "Error", f"Error during normalization:\n{e}")
        
    

#==============================================================================================#
# Function to close cycles                                                                     #
#==============================================================================================#

def close_loop_dialog(plot_instance, app_instance):
    '''
    Qt window to select file and columns for loop closure.

    Parameters
    ----------
    plot_instance : QWidget
        Widget from which this dialog is called (usually the plot panel).
    app_instance : MainApp
        Main application instance with session state.
    '''
    
    if plot_instance.figure is None:
        QMessageBox.critical(plot_instance, "Error", "No plot open!")
        return

    fig = plot_instance.figure
    ax  = plot_instance.ax
    lines = ax.lines

    #===============================
    # Extract valid lines 
    #===============================
    filtered_lines = []
    for line in lines:
        x_data, y_data = line.get_xdata(), line.get_ydata()
        if not (
            (all(y == 0 for y in y_data) and len(set(x_data)) > 1) or
            (all(x == 0 for x in x_data) and len(set(y_data)) > 1) or
            (line.get_gid() == "fit")
        ):
            filtered_lines.append(line)

    lines = filtered_lines

    if not lines:
        QMessageBox.critical(plot_instance, "Error", "No valid cycles!")
        return

    #===============================
    # Window
    #===============================
    window = QWidget()
    window.setWindowTitle("Cycle Closure")

    root_layout = QHBoxLayout(window)

    #===============================
    # Plot preview functions
    #===============================
    def get_selected_cycle():
        for label, cb in cycle_checks.items():
            if cb.isChecked():
                idx = cycle_map[label]
                l1 = lines[idx*2]
                l2 = lines[idx*2 + 1]

                return l1, l2
        return None, None

    def update_preview():

        l1, l2 = get_selected_cycle()
        if l1 is None:
            return

        x1 = l1.get_xdata()
        y1 = l1.get_ydata()
        x2 = l2.get_xdata()
        y2 = l2.get_ydata()

        field = 0.0

        if global_radio.isChecked():

            y1_new, y2_new = apply_loop_closure(y1, y2)

        else:
            try:
                field = float(field_edit.text())
            except:
                return

            i_up = np.argmin(np.abs(x1 - field))
            i_dw = np.argmin(np.abs(x2 - field))
            
            y1_new, y2_new = apply_loop_closure(y1, y2, i_up, i_dw)


        preview_ax.clear()

        preview_ax.plot(x1, y1, 'k-', alpha=0.3)
        preview_ax.plot(x2, y2, 'k-', alpha=0.3)
        preview_ax.plot(field*np.ones(10), np.linspace(-1, 1, 10), '--')

        preview_ax.plot(x1, y1_new, 'r-')
        preview_ax.plot(x2, y2_new, 'r-')

        preview_canvas.draw_idle()

    #===============================
    # Left panel for selections
    #===============================
    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(left_widget)

    root_layout.addWidget(scroll_area, 0)

    cycle_checks = {}
    cycle_map    = {}

    for i in range(0, len(lines), 2):
        idx = i // 2

        label = plot_instance.plot_customizations.get(
            idx, {}
        ).get("label", f"Cycle {idx + 1}")

        cb = QCheckBox(label)
        left_layout.addWidget(cb)

        cycle_checks[label] = cb
        cycle_map[label]    = idx
        cb.stateChanged.connect(update_preview)

    #===============================
    # Parameters
    #===============================
    mode_group = QButtonGroup(window)

    global_radio = QRadioButton("Global closure")
    field_radio  = QRadioButton("Closure at field")

    global_radio.setChecked(True)

    mode_group.addButton(global_radio)
    mode_group.addButton(field_radio)

    left_layout.addWidget(global_radio)
    left_layout.addWidget(field_radio)

    # Usable only in field mode
    left_layout.addWidget(QLabel("Field:"))
    field_edit = QLineEdit("0.0")
    field_edit.setEnabled(False)
    left_layout.addWidget(field_edit)

    apply_btn = QPushButton("Apply")
    left_layout.addWidget(apply_btn)

    #===============================
    # Right field (plot)
    #===============================
    right_layout = QVBoxLayout()
    root_layout.addLayout(right_layout, 1)

   
    preview_fig    = Figure(figsize=(5,4))
    preview_canvas = FigureCanvas(preview_fig)
    preview_ax     = preview_fig.add_subplot(111)

    right_layout.addWidget(preview_canvas)

    state = {
        "x_up": None,
        "y_up": None,
        "x_dw": None,
        "y_dw": None,
    }

    field_edit.textChanged.connect(update_preview)

    for cb in cycle_checks.values():
        cb.stateChanged.connect(update_preview)

    #===============================
    # Apply closure function
    #===============================
    def apply_closure():

        selected_file_idx = None
        use_global = global_radio.isChecked()

        if not use_global:
            try:
                field = float(field_edit.text())
            except:
                QMessageBox.critical(window, "Error", "Invalid field")
                return

        for label, cb in cycle_checks.items():
            if cb.isChecked():

                idx = cycle_map[label]

                l1 = lines[idx*2]
                l2 = lines[idx*2+1]

                if selected_file_idx is None:
                    selected_file_idx = getattr(l1, "_file_index", None)
                
                df = app_instance.dataframes[selected_file_idx]

                cols1 = l1._cols
                cols2 = l2._cols

                x1 = df[cols1[0]].astype(float).values
                y1 = df[cols1[1]].astype(float).values
                x2 = df[cols2[0]].astype(float).values
                y2 = df[cols2[1]].astype(float).values
               

                if use_global:
                    y1_new, y2_new = apply_loop_closure(y1, y2)
                else:
                    i_up = np.argmin(np.abs(x1 - field))
                    i_dw = np.argmin(np.abs(x2 - field))

                    y1_new, y2_new = apply_loop_closure(y1, y2, i_up, i_dw)

                df[cols1[1]] = y1_new
                df[cols2[1]] = y2_new

        plot_instance.plot()

    def update_mode():
        field_edit.setEnabled(field_radio.isChecked())
        update_preview()

    global_radio.toggled.connect(update_mode)
    field_radio.toggled.connect(update_mode)
    apply_btn.clicked.connect(apply_closure)

    #===============================
    # Show window
    #===============================
    sub = QMdiSubWindow()
    sub.setWidget(window)
    sub.setWindowTitle("Cycle Closure")

    app_instance.mdi_area.addSubWindow(sub)
    sub.show()



def apply_loop_closure(ell_up, ell_dw, i_up=None, i_dw=None):
    '''
    Apply a linear drift correction to close an hysteresis loop.

    The function corrects the mismatch between the two branches of a loop
    (`ell_up` and `ell_dw`) by applying a symmetric, point-wise correction.

    Two modes are available:

    1) Local correction (pivot-based)
    ---------------------------------
    If `i_up` and `i_dw` are provided, a local linear correction is applied.

    - The correction is anchored to a pivot index (`i_up`), which defines
      where the two branches are forced to match.
    - The magnitude of the correction is determined by the difference
      between the two branches at the selected indices:
          delta = |ell_up[i_up] - ell_dw[i_dw]|
    - A linear correction profile is applied from one end of the loop
      (`slope`) to the pivot:
          - zero correction at the slope
          - maximum correction (±0.5 * delta) at the pivot
    - The sign of the correction is determined by the relative position
      of the two branches (i.e. which one is higher in value), ensuring
      a physically consistent closure:
          - the upper branch is shifted downward
          - the lower branch is shifted upward

    NOTE:
    The pivot index is taken from `i_up`. The index `i_dw` is used only
    to evaluate the mismatch (`delta`), not to define the correction shape.

    2) Global correction
    --------------------
    If no indices are provided, a global linear correction is applied.

    - The function compares the mismatch at the beginning and at the end
      of the loop.
    - The dominant mismatch is selected (either start or end).
    - A linear correction is applied across the entire loop, gradually
      reducing the mismatch:
          - maximum correction at the dominant end
          - zero correction at the opposite end
    - The correction is applied symmetrically to the two branches.

    Parameters
    ----------
    ell_up : numpy.ndarray
        Values of the increasing (upper) branch.
    ell_dw : numpy.ndarray
        Values of the decreasing (lower) branch.
    i_up : int, optional
        Pivot index on the increasing branch used to anchor the local correction.
    i_dw : int, optional
        Index on the decreasing branch used only to evaluate the mismatch
        at the pivot location.

    Returns
    -------
    ell_up_corr : numpy.ndarray
        Corrected increasing branch.
    ell_dw_corr : numpy.ndarray
        Corrected decreasing branch.
    '''
    
    ell_up = ell_up.copy()
    ell_dw = ell_dw.copy()

    num = len(ell_up)

    #=================================================
    # Local case: if the field value is within
    # the loop, apply a local correction
    #=================================================
    if i_up is not None and i_dw is not None:

        v_up = ell_up[i_up]
        v_dw = ell_dw[i_dw]
        sign = 1 if v_up > v_dw else -1
        delta = abs(v_up - v_dw)

        if i_up < (0.5 * num):
            slope = num - 1
        else:
            slope = 0


        for i in range(num):
            correction = 0.5 * delta * (i - slope) / (i_up - slope)
            ell_up[i] -= correction*sign
            ell_dw[i] += correction*sign

        return ell_up, ell_dw

    #=================================================
    # Global case: apply correction on the whole loop,
    # based on the initial and final misalignment.
    #=================================================
    dy_start = abs(ell_up[0] - ell_dw[0])
    dy_stop  = abs(ell_up[-1] - ell_dw[-1])

    if dy_start > dy_stop:
        if ell_up[0] > ell_dw[0]:
            for i in range(num):
                delta = (0.5 * (num - 1 - i) * dy_start) / (num - 1)
                ell_up[i] -= delta
                ell_dw[i] += delta
        else:
            for i in range(num):
                delta = (0.5 * (num - 1 - i) * dy_start) / (num - 1)
                ell_up[i] += delta
                ell_dw[i] -= delta

    else:
        if ell_up[-1] > ell_dw[-1]:
            for i in range(num):
                delta = (0.5 * i * dy_stop) / (num - 1)
                ell_up[i] -= delta
                ell_dw[i] += delta
        else:
            for i in range(num):
                delta = (0.5 * i * dy_stop) / (num - 1)
                ell_up[i] += delta
                ell_dw[i] -= delta

    return ell_up, ell_dw

#==============================================================================================#
# Function to invert axis                                                                      #
#==============================================================================================#

def apply_inversion(axis, file_index, selected_pairs, dataframes, logger, plot_instance):
    '''
    Function to invert the x or y axis of the selected file.

    Parameters
    ----------
    axis : str
        axis to invert, can be "x", "y" or "both"
    file_index : int
        Index of the selected DataFrame.
    selected_pairs : list
        list of columns to plot
    dataframes : list
        list of loaded files, each file is a pandas dataframe
    logger : instance of logging.getLogger
        logger of the app
    plot_instance : QWidget
        Widget from which this dialog is called (usually the plot panel).
    '''
    try:
        df = dataframes[file_index]

        for _, x_combo, y_combo in selected_pairs:
            if axis in ("x", "both"):
                x_col = x_combo.currentText()
                if x_col in df.columns:
                    df[x_col] = df[x_col].astype(float) * -1
                    logger.info(f"Flip x-axis -> column {x_col}.")

            if axis in ("y", "both"):
                y_col = y_combo.currentText()
                if y_col in df.columns:
                    df[y_col] = df[y_col].astype(float) * -1
                    logger.info(f"Flip y-axis -> column {y_col}.")

        plot_instance.plot()

        QMessageBox.information(plot_instance, "Success",
                                f"Axis flip {axis.upper()} applied on File {file_index + 1}")

    except Exception as e:
        QMessageBox.critical(plot_instance, "Error",
                             f"Error while reversing:\n{e}")

def inv_x_dialog(plot_instance, app_instance):
    '''
    Dialog to select a file and invert the x-axis.

    Parameters
    ----------
    plot_instance : QWidget
        Widget from which this dialog is called (usually the plot panel).
    app_instance : MainApp
        Main application instance with session state.
    '''
    dataframes = app_instance.dataframes
    
    dialog = QDialog(plot_instance)
    dialog.setWindowTitle("Flip X-Axis")
    layout = QVBoxLayout(dialog)

    layout.addWidget(QLabel("Select the file:"))
    file_combo = QComboBox()
    file_combo.addItems([f"File {i + 1}" for i in range(len(dataframes))])
    layout.addWidget(file_combo)

    apply_btn = QPushButton("Apply")
    layout.addWidget(apply_btn)

    def on_apply():
        file_index = file_combo.currentIndex()
        apply_inversion(
            "x", file_index, plot_instance.selected_pairs, app_instance.dataframes,
            app_instance.logger, plot_instance
        )
        dialog.accept()

    apply_btn.clicked.connect(on_apply)
    dialog.exec_()


def inv_y_dialog(plot_instance, app_instance):
    '''
    Dialog to select a file and invert the y-axis.

    Parameters
    ----------
    plot_instance : QWidget
        Widget from which this dialog is called (usually the plot panel).
    app_instance : MainApp
        Main application instance with session state.
    '''
    dataframes = app_instance.dataframes
 
    dialog = QDialog(plot_instance)
    dialog.setWindowTitle("Flip Y-Axis")
    layout = QVBoxLayout(dialog)

    layout.addWidget(QLabel("Select the file:"))
    file_combo = QComboBox()
    file_combo.addItems([f"File {i + 1}" for i in range(len(dataframes))])
    layout.addWidget(file_combo)

    apply_btn = QPushButton("Apply")
    layout.addWidget(apply_btn)

    def on_apply():
        file_index = file_combo.currentIndex()
        apply_inversion(
            "y", file_index, plot_instance.selected_pairs, app_instance.dataframes,
            app_instance.logger, plot_instance
        )
        dialog.accept()

    apply_btn.clicked.connect(on_apply)
    dialog.exec_()

#==============================================================================================#
# Function to invert a single branch of the cycle                                              #
#==============================================================================================#

def inv_single_branch_dialog(parent_widget, app_instance):
    '''
    Creates the window to select the file and columns to reverse.

    Parameters
    ----------
    plot_instance : QWidget
        Widget from which this dialog is called (usually the plot panel).
    app_instance : MainApp
        Main application instance with session state.
    '''

    dataframes = app_instance.dataframes

    dialog = QDialog(parent_widget)
    dialog.setWindowTitle("Flip Single Branch")
    layout = QVBoxLayout(dialog)

    layout.addWidget(QLabel("Select the file:"))
    file_combo = QComboBox()
    file_combo.addItems([f"File {i + 1}" for i in range(len(dataframes))])
    layout.addWidget(file_combo)

    checkbox_container = QWidget()
    checkbox_layout = QVBoxLayout()
    checkbox_container.setLayout(checkbox_layout)
    layout.addWidget(checkbox_container)

    selected_columns = {}

    def update_checkboxes():
        # Clean old checkbox
        for i in reversed(range(checkbox_layout.count())):
            widget = checkbox_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        selected_columns.clear()

        idx = file_combo.currentIndex()
        if idx < 0 or idx >= len(dataframes):
            return

        cols = dataframes[idx].columns
        for col in cols:
            cb = QCheckBox(col)
            checkbox_layout.addWidget(cb)
            selected_columns[col] = cb

    file_combo.currentIndexChanged.connect(update_checkboxes)
    update_checkboxes()

    apply_btn = QPushButton("Apply")
    layout.addWidget(apply_btn)

    apply_btn.clicked.connect(
        lambda: apply_column_inversion(
            file_index=file_combo.currentIndex(),
            selected_columns=selected_columns,
            dataframes=app_instance.dataframes,
            logger=app_instance.logger,
            plot_instance=parent_widget,
        )
    )

    dialog.exec_()

def apply_column_inversion(file_index, selected_columns, dataframes, logger, plot_instance):
    '''
    Inverts the sign of selected columns in the given DataFrame.
    
    Parameters
    ----------
    file_index : int
        Index of the selected DataFrame.
    selected_columns : dict
        dict of selected colums for inversion
    dataframes : list
        list of loaded files, each file is a pandas dataframe
    logger : instance of logging.getLogger
        logger of the app
    plot_instance : QWidget
        Widget from which this dialog is called (usually the plot panel).
    '''
    try:
        df = dataframes[file_index]
        selected = [col for col, cb in selected_columns.items() if cb.isChecked()]

        if not selected:
            QMessageBox.warning(plot_instance, "Error", "Select at least one column.")
            return

        for col in selected:
            if col in df.columns:
                df[col] = df[col].astype(float) * -1
                logger.info(f"Reversing column {col} in file {file_index + 1}.")

        plot_instance.plot()
        QMessageBox.information(plot_instance, "Success",
                                f"Inversion applied on: {', '.join(selected)}")
    except Exception as e:
        QMessageBox.critical(plot_instance, "Error", f"Error while reversing:\n{e}")

