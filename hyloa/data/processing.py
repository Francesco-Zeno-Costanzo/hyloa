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
    QMessageBox, QScrollArea, QWidget, QFormLayout
)


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
    dataframes = app_instance.dataframes
    if not dataframes:
        QMessageBox.warning(plot_instance, "Error", "No data loaded")
        return

    dialog = QDialog(plot_instance)
    dialog.setWindowTitle("Normalie Cycle")
    layout = QVBoxLayout(dialog)

    layout.addWidget(QLabel("Select the file:"))
    file_combo = QComboBox()
    file_combo.addItems([f"File {i + 1}" for i in range(len(dataframes))])
    layout.addWidget(file_combo)
    layout.addWidget(QLabel("Select Y columns to normalize (in pairs):"))


    column_checks = {}

    column_area      = QScrollArea()
    column_container = QWidget()
    column_layout    = QFormLayout(column_container)
    column_area.setWidget(column_container)
    column_area.setWidgetResizable(True)
    layout.addWidget(column_area)

    def update_column_list():
        while column_layout.count():
            item = column_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        idx = file_combo.currentIndex()
        df = dataframes[idx]
        num_cols = len(df.columns)

        # Determine the columns of the x-axis based on the number of columns. 
        # This is based on the reasonable assumption that the
        # quantities are loaded in pairs to form the entire cycle
        if num_cols >= 8:
            x_cols = [df.columns[0], df.columns[4]]
        elif num_cols == 6:
            x_cols = [df.columns[0], df.columns[3]]
        elif num_cols == 4:
            x_cols = [df.columns[0], df.columns[2]]
        else:
            x_cols = []

        column_checks.clear()

        for col in df.columns:
            if col in x_cols:
                continue
            cb = QCheckBox(col)
            column_checks[col] = cb
            column_layout.addRow(cb)

    file_combo.currentIndexChanged.connect(update_column_list)
    update_column_list()

    def on_apply():
        selected_file_idx = file_combo.currentIndex()
        selected_cols = [col for col, cb in column_checks.items() if cb.isChecked()]
        if len(selected_cols) % 2 != 0 or len(selected_cols) == 0:
            QMessageBox.critical(dialog, "Error", "Select an even number of columns.")
            return
        dialog.accept()
        apply_norm(plot_instance, app_instance, selected_file_idx, selected_cols)

    apply_button = QPushButton("Apply")
    apply_button.clicked.connect(on_apply)
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
    '''

    parent_widget  = plot_instance
    logger         = app_instance.logger

    try:
        df = app_instance.dataframes[file_index]
   
        N_Y = []
        for y1, y2 in zip(selected_cols[::2], selected_cols[1::2]):
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

            N_Y.append((y1, ell_up_normalized))
            N_Y.append((y2, ell_dw_normalized))

        for col, new_values in N_Y:
            df[col] = new_values
            logger.info(f"Normalization applied to {col}.")

        # Re-plot
        plot_instance.plot()

        QMessageBox.information(plot_instance, "Success",
                                f"Normalization applied on File {file_index + 1}.")
        
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
    dataframes = app_instance.dataframes
    if not dataframes:
        QMessageBox.warning(plot_instance, "Error", "No data loaded.")
        return

    dialog = QDialog(plot_instance)
    dialog.setWindowTitle("Close Loop")

    layout = QVBoxLayout(dialog)

    layout.addWidget(QLabel("Select the file:"))
    file_combo = QComboBox()
    file_combo.addItems([f"File {i + 1}" for i in range(len(dataframes))])
    layout.addWidget(file_combo)
    layout.addWidget(QLabel("Select Y columns to close (in pairs)::"))

    column_checks = {}  # col_name -> QCheckBox

    column_area      = QScrollArea()
    column_container = QWidget()
    column_layout    = QFormLayout(column_container)
    column_area.setWidget(column_container)
    column_area.setWidgetResizable(True)
    layout.addWidget(column_area)

    def update_column_list():
        while column_layout.count():
            item = column_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        idx = file_combo.currentIndex()
        df = dataframes[idx]
        num_cols = len(df.columns)

        # Determine the columns of the x-axis based on the number of columns. 
        # This is based on the reasonable assumption that the
        # quantities are loaded in pairs to form the entire cycle
        if num_cols >= 8:
            x_cols = [df.columns[0], df.columns[4]]
        elif num_cols == 6:
            x_cols = [df.columns[0], df.columns[3]]
        elif num_cols == 4:
            x_cols = [df.columns[0], df.columns[2]]
        else:
            x_cols = []

        column_checks.clear()
        for col in df.columns:
            if col in x_cols:
                continue
            cb = QCheckBox(col)
            column_checks[col] = cb
            column_layout.addRow(cb)

    file_combo.currentIndexChanged.connect(update_column_list)
    update_column_list()

    def on_apply():
        selected_file_idx = file_combo.currentIndex()
        selected_cols = [col for col, cb in column_checks.items() if cb.isChecked()]
        print(33, selected_cols)
        apply_loop_closure(
            plot_instance,
            app_instance,
            selected_file_idx,
            selected_cols
        )
        dialog.accept()

    apply_button = QPushButton("Apply")
    apply_button.clicked.connect(on_apply)
    layout.addWidget(apply_button)

    dialog.exec_()

def apply_loop_closure(plot_instance, app_instance, file_index, selected_cols):
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
    plot_instance : QWidget
        Calling plot widget (used for re-plotting).
    app_instance : MainApp
        Global app state.
    file_index : int
        Index of the selected DataFrame.
    selected_cols : list of str
        Columns to correct (should be pairs).
    '''
    try:
        df = app_instance.dataframes[file_index]
        logger = app_instance.logger

        if len(selected_cols) < 2:
            QMessageBox.warning(plot_instance, "Error", "You must select the data pair that creates the cycle.")
            return

        if len(selected_cols) % 2 != 0:
            QMessageBox.warning(plot_instance, "Error", "You must select the data pair that creates the cycle.")
            return

        N_Y = []
        for col1, col2 in zip(selected_cols[::2], selected_cols[1::2]):
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

            N_Y.append((col1, ell_up))
            N_Y.append((col2, ell_dw))

        for col, new_values in N_Y:
            df[col] = new_values
            logger.info(f"Loop Closure Applied to {col}.")

        # Re-plot
        plot_instance.plot()

        QMessageBox.information(plot_instance, "Success",
                                f"Closure applied on File {file_index + 1}.")

    except Exception as e:
        QMessageBox.critical(plot_instance, "Error",
                             f"Error while closing loop:\n{e}")

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

