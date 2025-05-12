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
Code to handle data input and output, i.e. loading and saving data
"""
import os
import numpy as np
import pandas as pd

from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QWidget, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QLineEdit, QScrollArea, QTableWidget,
    QTableWidgetItem, QDialog, QVBoxLayout, QComboBox
)
from PyQt5.QtCore import Qt


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
    if app_instance.logger is None:
        QMessageBox.critical(None, "Errore", "Impossibile iniziare l'analisi senza avviare il log")
        return

    file_paths, _ = QFileDialog.getOpenFileNames(
        None,
        "Seleziona i file",
        "",
        "Text Files (*.txt);;All Files (*)"
    )

    if not file_paths:
        return

    for file_path in file_paths:

        filename = os.path.basename(file_path)

        # Check if the file is already loaded
        existing_names = [df.attrs.get("filename", "") for df in app_instance.dataframes]

        if filename in existing_names:
            reply = QMessageBox.question(
                None,
                "File già caricato",
                f"Il file '{filename}' è già stato caricato.\nVuoi sovrascriverlo?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                continue  # Skip this file
            else:
                index_to_replace = existing_names.index(filename)
        else:
            index_to_replace = None  # new file

        try:
            with open(file_path, "r", encoding='utf-8') as f:
                header = f.readline().strip().split("\t")

            app_instance.logger.info(f"Apertura file {file_path}")
            show_column_selection(app_instance, file_path, header, index_to_replace)

        except Exception as e:
            QMessageBox.critical(None, "Errore", f"Errore durante il caricamento del file: {file_path}\n{e}")

#==============================================================================================#

def show_column_selection(app_instance, file_path, header, index_to_replace=None):
    '''
    Dialog window to select columns to load.

    Parameters
    ----------
    app_instance : instance of MainApp
    file_path : string
        path of the file to read
    header : list of str
        header of the file
    '''
    # Create a dialog window
    dialog = QWidget()
    dialog.setWindowTitle(f"Seleziona Colonne: {os.path.basename(file_path)}")
    dialog.setGeometry(100, 100, 900, 750)
    main_layout = QVBoxLayout(dialog)

    # Instructions
    instructions = QLabel(
        "Seleziona le colonne da caricare e assegna un nome. Se il nome è vuoto verrà usato il default.\n"
        "Scorri in basso per visualizzare i dati."
    )
    instructions.setWordWrap(True)
    main_layout.addWidget(instructions)

    selected_columns = {}
    custom_names     = {}

    # Preview Data Table
    all_df = pd.read_csv(file_path, sep="\t").drop([0, 1, 2])
    table = QTableWidget()
    table.setRowCount(len(all_df))
    table.setColumnCount(len(all_df.columns))
    table.setHorizontalHeaderLabels(list(all_df.columns))

    for i in range(len(all_df)):
        for j, col in enumerate(all_df.columns):
            item = QTableWidgetItem(str(all_df.iloc[i, j]))
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            table.setItem(i, j, item)

    table.setFixedHeight(250)
    main_layout.addWidget(table)

    # Column selection section (in scroll area)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll_content = QWidget()
    scroll_layout = QVBoxLayout(scroll_content)

    for i, col_name in enumerate(header):
        box = QHBoxLayout()
        checkbox = QCheckBox(col_name)
        checkbox.setChecked(True)
        selected_columns[i] = checkbox
        custom_names[i] = QLineEdit()
        custom_names[i].setPlaceholderText("Nome colonna personalizzato")
        box.addWidget(checkbox)
        box.addWidget(custom_names[i])
        scroll_layout.addLayout(box)

    scroll_content.setLayout(scroll_layout)
    scroll.setWidget(scroll_content)
    main_layout.addWidget(scroll)

    # Confirm button
    def submit_selection():
        try:
            columns_to_load = [header[i] for i in range(len(header)) if selected_columns[i].isChecked()]
            column_names = [
                custom_names[i].text() or f"{os.path.splitext(os.path.basename(file_path))[0]}_{header[i]}"
                for i in range(len(header)) if selected_columns[i].isChecked()
            ]

            df_header = pd.read_csv(file_path, sep="\t", nrows=3)
            app_instance.header_lines.append(df_header)

            df_data = pd.read_csv(file_path, sep="\t", usecols=columns_to_load)
            df_data.columns = column_names
            df_data = df_data.drop([0, 1, 2])

            app_instance.logger.info(f"Dal file: {file_path}, caricate le colonne: {columns_to_load}")

            df_data.attrs["filename"] = os.path.basename(file_path)

            if index_to_replace is not None:
                app_instance.dataframes[index_to_replace]   = df_data
                app_instance.header_lines[index_to_replace] = df_header
                app_instance.logger.info(f"File '{file_path}' sovrascritto in posizione {index_to_replace}")
            else:
                app_instance.dataframes.append(df_data)
                app_instance.header_lines.append(df_header)
                app_instance.logger.info(f"File '{file_path}' aggiunto")

            QMessageBox.information(dialog, "Successo", f"Dati caricati da {file_path}!")
            app_instance.refresh_shell_variables()
            dialog.close()
        except Exception as e:
            QMessageBox.critical(dialog, "Errore", f"Errore durante il caricamento:\n{e}")

    confirm_button = QPushButton("Carica")
    confirm_button.clicked.connect(submit_selection)
    main_layout.addWidget(confirm_button)

    dialog.show()

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

def save_modified_data(app_instance, parent_widget):
    ''' 
    Allows you to choose the file and data to save, with the related headers.

    Parameters
    ----------
    app_instance : MainApp object
        instance of MainApp from main_window.py
    parent_widget : QWidget
        parent widget for the dialog
    '''

    dataframes = app_instance.dataframes

    if not dataframes:
        QMessageBox.critical(parent_widget, "Errore", "Nessun dato da salvare.")
        return
    
     # Instructions
    instructions = QLabel(
        "Selezionare i file contenente i dati da salvare, se si vuole essere sicuri si può "
        "verificare quali siano sati i file caricati vedendo anche i rispettivi dati.\n"
        "Qualora fossero sate caricate meno colonne delle 8 disponibili verrano aggiunte "
        "delle colonne di zeri per mantenere la compatibilià."
    )
    instructions.setWordWrap(True)
    
    dialog = QDialog(parent_widget)
    dialog.setWindowTitle("Seleziona il file da salvare")
    dialog.setGeometry(100, 100, 400, 200)

    layout = QVBoxLayout(dialog)
    layout.addWidget(instructions)
    layout.addWidget(QLabel("Scegli il file da salvare:"))

    combo = QComboBox()
    for i in range(len(dataframes)):
        # Add the filename to the combo box
        combo.addItem(f"File {i + 1}")

    layout.addWidget(combo)

    save_button = QPushButton("Salva")
    layout.addWidget(save_button)

    def on_save_clicked():
        df_idx = combo.currentIndex()
        save_to_file(df_idx, app_instance, parent_widget)
        dialog.accept()

    save_button.clicked.connect(on_save_clicked)

    dialog.exec_()


def save_to_file(df_idx, app_instance, parent_widget=None):
    '''
    Save the selected data to a new text file.
    If fewer columns than the 8 available are loaded,
    columns of zeros will be added to maintain compatibility.

    Parameters
    ----------
    df_idx : int
        index of the selected dataframe
    app_instance : MainApp object
        instance of MainApp from main_window.py
    save_window : Toplevel object
        window to close after saving the data
    '''  

    dataframes   = app_instance.dataframes
    header_lines = app_instance.header_lines
   
    try:
        # Retrieve the selected DataFrame
        df = dataframes[df_idx]
       
        # Retrieve the header of the selected file
        header = header_lines[df_idx]
 
        # Dialog to choose the name of the new file
        file_path, _ = QFileDialog.getSaveFileName(
            parent_widget,
            "Salva il file modificato",
            "",
            "File di Testo (*.txt);;CSV (*.csv);;Tutti i file (*)"
        )
    
        if not file_path:
            QMessageBox.warning(parent_widget, "Annullato", "Operazione annullata.")
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
                expanded_data[:, :3]  = data[:, :3]
                expanded_data[:, 4:7] = data[:, 3:]
            elif cols == 8:
                # All data
                expanded_data = data

            np.savetxt(f, expanded_data, delimiter="\t", fmt="%s")

        QMessageBox.information(parent_widget, "Successo", f"Dati salvati con successo in:\n{file_path}")

    except Exception as e:
        QMessageBox.critical(parent_widget, "Errore", f"Errore durante il salvataggio:\n{e}")