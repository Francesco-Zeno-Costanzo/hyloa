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

def norm(plot_instance, app_instance):
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

    parent_widget  = app_instance
    dataframes     = app_instance.dataframes
    logger         = app_instance.logger
    selected_pairs = plot_instance.selected_pairs


    try:
        Y = []
        for df_choice, _, y_var in selected_pairs:
            df_idx = int(df_choice.currentText().split(" ")[1]) - 1
            y_col = y_var.currentText()
            y = dataframes[df_idx][y_col].astype(float).values
            Y.append(y)

        N_Y = []
        for y1, y2 in zip(Y[0::2], Y[1::2]):
            ell_up = y1
            ell_dw = y2

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

            N_Y.append(ell_up_normalized)
            N_Y.append(ell_dw_normalized)

        # Update DataFrames
        for (df_choice, _, y_var), n_y in zip(selected_pairs, N_Y):
            df_idx = int(df_choice.currentText().split(" ")[1]) - 1
            y_col  = y_var.currentText()
            logger.info(f"Normalizzazione applicata alle colonne {y_col}.")
            dataframes[df_idx][y_col] = n_y

        #plot_data(plot_instance, app_instance)
        plot_instance.plot()
    except Exception as e:
        QMessageBox.critical(parent_widget, "Errore", f"Errore durante la normalizzazione:\n{e}")


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
        QMessageBox.warning(plot_instance, "Errore", "Non ci sono dati caricati.")
        return

    dialog = QDialog(plot_instance)
    dialog.setWindowTitle("Chiudi Loop")

    layout = QVBoxLayout(dialog)

    layout.addWidget(QLabel("Seleziona il file:"))
    file_combo = QComboBox()
    file_combo.addItems([f"File {i + 1}" for i in range(len(dataframes))])
    layout.addWidget(file_combo)

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
        apply_loop_closure(
            plot_instance,
            app_instance,
            selected_file_idx,
            selected_cols
        )
        dialog.accept()

    layout.addWidget(QLabel("Seleziona le colonne da correggere (una coppia alla volta):"))
    apply_button = QPushButton("Applica")
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
            QMessageBox.warning(plot_instance, "Errore", "Devi selezionare la coppia di dati che crea il ciclo")
            return

        if len(selected_cols) % 2 != 0:
            QMessageBox.warning(plot_instance, "Errore", "Devi selezionare la coppia di dati che crea il ciclo.")
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
            logger.info(f"Chiusura del ciclo applicata a {col}.")

        # Re-plot
        plot_instance.plot()

        QMessageBox.information(plot_instance, "Successo",
                                f"Correzione applicata su File {file_index + 1}.")

    except Exception as e:
        QMessageBox.critical(plot_instance, "Errore",
                             f"Errore durante la chiusura del ciclo:\n{e}")

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
                    logger.info(f"Inversione asse x -> colonna {x_col}.")

            if axis in ("y", "both"):
                y_col = y_combo.currentText()
                if y_col in df.columns:
                    df[y_col] = df[y_col].astype(float) * -1
                    logger.info(f"Inversione asse y -> colonna {y_col}.")

        plot_instance.plot()

        QMessageBox.information(plot_instance, "Successo",
                                f"Inversione asse {axis.upper()} applicata su File {file_index + 1}!")

    except Exception as e:
        QMessageBox.critical(plot_instance, "Errore",
                             f"Errore durante l'inversione:\n{e}")

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
    if not dataframes:
        QMessageBox.warning(plot_instance, "Errore", "Non ci sono dati caricati.")
        return

    dialog = QDialog(plot_instance)
    dialog.setWindowTitle("Inverti Asse X")
    layout = QVBoxLayout(dialog)

    layout.addWidget(QLabel("Seleziona il file:"))
    file_combo = QComboBox()
    file_combo.addItems([f"File {i + 1}" for i in range(len(dataframes))])
    layout.addWidget(file_combo)

    apply_btn = QPushButton("Applica")
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
    if not dataframes:
        QMessageBox.warning(plot_instance, "Errore", "Non ci sono dati caricati.")
        return

    dialog = QDialog(plot_instance)
    dialog.setWindowTitle("Inverti Asse Y")
    layout = QVBoxLayout(dialog)

    layout.addWidget(QLabel("Seleziona il file:"))
    file_combo = QComboBox()
    file_combo.addItems([f"File {i + 1}" for i in range(len(dataframes))])
    layout.addWidget(file_combo)

    apply_btn = QPushButton("Applica")
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
    Crea la finestra per selezionare il file e le colonne da invertire.

    Parameters
    ----------
    plot_instance : QWidget
        Widget from which this dialog is called (usually the plot panel).
    app_instance : MainApp
        Main application instance with session state.
    '''

    dataframes = app_instance.dataframes

    dialog = QDialog(parent_widget)
    dialog.setWindowTitle("Inverti Singolo Ramo")
    layout = QVBoxLayout(dialog)

    layout.addWidget(QLabel("Seleziona il file:"))
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

    apply_btn = QPushButton("Applica")
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
            QMessageBox.warning(plot_instance, "Errore", "Seleziona almeno una colonna.")
            return

        for col in selected:
            if col in df.columns:
                df[col] = df[col].astype(float) * -1
                logger.info(f"Inversione colonna {col} nel file {file_index + 1}.")

        plot_instance.plot()
        QMessageBox.information(plot_instance, "Successo",
                                f"Inversione applicata su: {', '.join(selected)}")
    except Exception as e:
        QMessageBox.critical(plot_instance, "Errore", f"Errore durante l'inversione:\n{e}")

