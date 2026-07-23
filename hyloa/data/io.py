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
import shutil
import numpy as np
import pandas as pd

from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QWidget, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QLineEdit, QScrollArea, QTableWidget,
    QTableWidgetItem, QDialog, QVBoxLayout, QComboBox, QListWidget,
    QSpinBox
)
from PyQt5.QtCore import Qt


#==============================================================================================#
# File upload functions                                                                        #
#==============================================================================================#

def load_files(app_instance):
    '''
    Function to upload a file chosen by the user.
    If the file has an header, this will be preserved when the data is
    saved to a new file.

    Parameters
    ----------
    app_instance : instance of MainApp from main_window.py
    '''
    if app_instance.logger is None:
        QMessageBox.critical(None, "Error", "Cannot start analysis without starting log")
        return

    file_paths, _ = QFileDialog.getOpenFileNames(
        None,
        "Select a file",
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
                "File already uploaded",
                f"The file '{filename}' has already been uploaded.\nDo you want to overwrite it?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                continue  # Skip this file
            else:
                index_to_replace = existing_names.index(filename)
        else:
            index_to_replace = None  # new file

        try:
            if detect_header_length(file_path) == -1:
                data   = np.loadtxt(file_path, max_rows=1)
                n_col  = data.size
                header = [f"col_{i}" for i in range(n_col)]
            else:
                with open(file_path, "r", encoding='utf-8') as f:
                    header = f.readline().strip().split("\t")

            app_instance.logger.info(f"Opening file {file_path}")
            show_column_selection(app_instance, file_path, header, index_to_replace)

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error loading file: {file_path}\n{e}")

#==============================================================================================#

def detect_header_length(file_path, sep='\t'):
    '''
    Function to compute the length of the header and therefore,
    the number of rows to exclude from the dataframe to obtain a
    dataframe that has for each column only the data of interest.

    Parameters
    ----------
    file_path : string
        path of the file to read
    sep : string
        separetor, optional, default a tabulation

    Return
    ------
    data_start : int
        number of the not empty lines of the file's header
    '''
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    data_start  = None
    empty_lines = 0
    
    def is_float(s):
        try:
            float(s)
            return True
        except Exception:
            return False

    # Find the first row with no letter
    for i, line in enumerate(lines):
        parts         = [x.strip() for x in line.strip().split(sep)]
        numeric_parts = [x for x in parts if is_float(x)]
        
        if parts[0] == '':
            empty_lines += 1
        
        if len(numeric_parts) == len(parts) and len(parts) > 1:
            data_start = i
            break

    if data_start is None:
        raise ValueError("No valid data found.")
    
    data_start = data_start - 1 - empty_lines
    
    return data_start

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
    dialog.setWindowTitle(f"Select Columns: {os.path.basename(file_path)}")
    dialog.move(100, 100)
    dialog.setMinimumSize(900, 750)
    dialog.adjustSize()
    main_layout = QVBoxLayout(dialog)

    # Instructions
    instructions = QLabel(
        "Select columns to load and name them. If the name is empty, the default will be used.\n"
        "Scroll down to view data."
    )
    instructions.setWordWrap(True)
    main_layout.addWidget(instructions)

    selected_columns = {}
    custom_names     = {}
    duplicate_counts = {}

    header_length = detect_header_length(file_path)

    # Preview Data Table
    if header_length > 0:
        all_df = pd.read_csv(file_path, sep="\t").drop(list(range(header_length)))
        
    elif header_length == -1:
        data     = np.loadtxt(file_path)
        _, n_col = data.shape
        col      = [f"col_{i}" for i in range(n_col)]
        all_df   = pd.DataFrame(data, columns=col)
    else:
        all_df = pd.read_csv(file_path, sep="\t")

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
        custom_names[i].setPlaceholderText("Custom column name")

        duplicate_counts[i] = QSpinBox()
        duplicate_counts[i].setMinimum(1)
        duplicate_counts[i].setMaximum(20)
        duplicate_counts[i].setValue(1)

        duplicate_label = QLabel("Copies")

        box.addWidget(checkbox)
        box.addWidget(custom_names[i])
        box.addWidget(duplicate_label)
        box.addWidget(duplicate_counts[i])

        scroll_layout.addLayout(box)

    scroll_content.setLayout(scroll_layout)
    scroll.setWidget(scroll_content)
    main_layout.addWidget(scroll)

    # Confirm button
    def submit_selection():
        try:

            #=========================================
            # Build selected columns and names
            #=========================================

            columns_to_load = []
            column_names    = []

            base_filename = os.path.splitext(os.path.basename(file_path))[0]

            for i in range(len(header)):
                if not selected_columns[i].isChecked():
                    continue

                original_col = header[i]
                base_name = (
                    custom_names[i].text()
                    or f"{base_filename}_{original_col}"
                )

                n_copies = duplicate_counts[i].value()

                for k in range(n_copies):
                    columns_to_load.append(original_col)

                    if n_copies == 1:
                        column_names.append(base_name)
                    else:
                        column_names.append(f"{base_name}_{k+1}")
            
            #=========================================
            # Read source dataframe
            #=========================================

            header_length = detect_header_length(file_path)

            if header_length >= 0:
                df_header = pd.read_csv(file_path, sep="\t", nrows=header_length)
                full_df   = pd.read_csv(file_path, sep="\t")

            elif header_length == -1:
                df_header = header
                data      = np.loadtxt(file_path)
                full_df   = pd.DataFrame(data, columns=header)
            
            #=========================================
            # Build duplicated/custom dataframe
            #=========================================
            
            data_dict      = {}
            idx_name       = 0
            col_source_map = {}

            for i in range(len(header)):
                if not selected_columns[i].isChecked():
                    continue

                original_col = header[i]
                n_copies     = duplicate_counts[i].value()

                for k in range(n_copies):
                    new_name                 = column_names[idx_name]
                    data_dict[new_name]      = full_df[original_col].values.copy()
                    idx_name                += 1
                    col_source_map[new_name] = original_col

            df_data = pd.DataFrame(data_dict)
            df_data.attrs["column_source_map"] = col_source_map  
            df_data.attrs["filename"] = os.path.basename(file_path)

            if header_length >= 0 :
                df_data = df_data.drop(list(range(header_length)))

            app_instance.logger.info(f"From: {file_path}, load: {columns_to_load}")

            if index_to_replace is not None:
                app_instance.dataframes[index_to_replace]   = df_data
                app_instance.header_lines[index_to_replace] = df_header
                app_instance.logger.info(f"File '{file_path}' overwrite in position {index_to_replace}")
                app_instance.dataframes_changed.emit()  # Emit the signal to notify that dataframes have changed
            else:
                app_instance.dataframes.append(df_data)
                app_instance.header_lines.append(df_header)
                app_instance.logger.info(f"File '{file_path}' added")
                app_instance.dataframes_changed.emit()  # Emit the signal to notify that dataframes have changed

            QMessageBox.information(dialog, "Success", f"Data loaded form {file_path}!")
            app_instance.refresh_shell_variables()
            dialog.close()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Error while loading:\n{e}")

    confirm_button = QPushButton("Load")
    confirm_button.clicked.connect(submit_selection)
    main_layout.addWidget(confirm_button)

    dialog.show()

#==============================================================================================#
# Functions to save modified data                                                              #
#==============================================================================================#

def clean_column_name(name, filename):
    '''
    Clean the column name by removing the filename prefix if it exists.

    Parameters
    ----------
    name : string
        column name to clean
    filename : string
        filename to remove from the column name if it is a prefix   
    Return
    ------
    cleaned_name : string
        cleaned column name without the filename prefix
    '''
    prefix = f"{filename}_"

    if name.startswith(prefix):
        return name[len(prefix):]

    return name

def save_header(app_instance, header_df, df, file_path):
    '''
    Save the header in the final text file,
    to provide compatibility in case you want to
    reopen it for further analysis.

    Parameters
    ----------
    app_instance : MainApp object
        instance of MainApp from main_window.py
    header_df : pandas dataframe
        dataframe containing the header of the data file
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
            if isinstance(header_df, pd.DataFrame):
                for _, row in header_df.iterrows():
                    line = "\t".join(row.astype(str).fillna("").replace("nan", "").values)
                    f.write(line.strip() + "\n")
        app_instance.logger.info(f"File saved successfully in: {file_path}")

    except Exception as e:
        app_instance.logger.info(f"Error while saving: {e}")

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
        QMessageBox.critical(parent_widget, "Error", "No data aviable.")
        return
    
    instructions = QLabel(
        "Select the files containing the data you want to save.\n"
        "You can see the available columns for each selected file."
    )
    instructions.setWordWrap(True)
    
    dialog = QDialog(parent_widget)
    dialog.setWindowTitle("Select the file to save")
    dialog.move(100, 100)
    dialog.setMinimumSize(500, 300)
    dialog.adjustSize()
    
    layout = QVBoxLayout(dialog)
    layout.addWidget(instructions)
    layout.addWidget(QLabel("Select the file to save:"))

    combo = QComboBox()
    for i in range(len(dataframes)):
        combo.addItem(f"File {i + 1}")
    layout.addWidget(combo)

    layout.addWidget(QLabel("Columns of the selected file:"))
    column_list = QListWidget()
    layout.addWidget(column_list)

    def update_column_list(index):
        ''' Function to update the list of the columns
        '''
        column_list.clear()
        if index < len(dataframes):
            columns = dataframes[index].columns
            for col in columns:
                column_list.addItem(str(col))

    # Connect file selection and columns list
    combo.currentIndexChanged.connect(update_column_list)
    
    # Initialize the list
    update_column_list(0)

    save_button = QPushButton("Save")
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

        source_name = df.attrs.get("filename")

        df = df.copy()
        df.columns = [
            clean_column_name(col, source_name[:-4]) # remove .txt
            for col in df.columns
        ]
       
        # Retrieve the header of the selected file
        header = header_lines[df_idx]
 
        # Dialog to choose the name of the new file
        file_path, _ = QFileDialog.getSaveFileName(
            parent_widget,
            "Save modified file",
            "",
            "Text file (*.txt);;CSV (*.csv);;Tutti i file (*)"
        )
        
        # ensure .txt extension
        if file_path and not file_path.lower().endswith('.txt'):
            file_path += '.txt'
    
        if not file_path:
            file_path = ""
            QMessageBox.warning(parent_widget, "Canceled", "Operation cancelled.")
            return

        save_header(app_instance, header, df, file_path)
        # Save the data in the new file in text format
        with open(file_path, "a", encoding='utf-8') as f:

            np.savetxt(f, np.array(df), delimiter="\t", fmt="%s")

        QMessageBox.information(parent_widget, "Success", f"Data successfully saved in:\n{file_path}")

    except Exception as e:
        QMessageBox.critical(parent_widget, "Error", f"Error while saving:\n{e}")

#==============================================================================================#
# Function that create a copy of a given file                                                  #
#==============================================================================================#

def duplicate_file(parent_widget=None):
    '''
    Duplicates a selected file by creating a copy named <original>_copy.ext.
    Opens a file dialog to select a file and creates a duplicate
    of it with '_copy' appended to the name.

    Parameters:
    -----------
    parent_widget : (QWidget, optional)
        The parent widget for dialogs. Defaults to None.
    '''
    file_path, _ = QFileDialog.getOpenFileName(
        parent_widget,
        "Select the file to duplicate",
        "",
        "Text Files (*.txt);;All Files (*)"
    )

    if not file_path:
        return

    base, ext = os.path.splitext(file_path)
    copy_path = f"{base}_copy{ext}"

    try:
        shutil.copy2(file_path, copy_path)
        QMessageBox.information(parent_widget, "Copy completed",
                                f"File copied as:\n{copy_path}")
    except Exception as e:
        QMessageBox.critical(parent_widget, "Error",
                             f"Error copying file:\n{e}")
