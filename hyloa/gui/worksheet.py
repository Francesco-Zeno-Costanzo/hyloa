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
Code for the worksheet window, allowing data table manipulation and plotting.
"""

import numpy as np
import pandas as pd
from scipy.special import *
from scipy.optimize import curve_fit
        
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import QItemSelectionModel


from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QMdiSubWindow, QLineEdit,
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QDialog, QLabel, QComboBox,
    QDialogButtonBox, QInputDialog, QAction, QApplication,
    QFormLayout, QTextEdit, QSizePolicy, QCheckBox,
    QListWidget, QAbstractItemView, QGridLayout,
    QGroupBox, QStackedWidget, QButtonGroup
)



from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from matplotlib.figure import Figure
from matplotlib.container import ErrorbarContainer
from matplotlib.legend_handler import HandlerErrorbar
from matplotlib import colors as mcolors, markers, lines as mlines


from hyloa.data.io import detect_header_length
from hyloa.utils.err_format import format_value_error
from hyloa.gui.worksheet_utils import ColumnSelectionDialog, ColumnMathDialog

class WorksheetWindow(QMdiSubWindow):
    ''' A worksheet subwindow for managing tabular data and plotting.
    '''
    def __init__(self, mdi_area, parent=None, name="worksheet", logger=None, app_instance=None):
        '''
        Initialize the worksheet window.

        Parameters
        ----------
        mdi_area : QMdiArea
            The main MDI area where this window will be added.
        parent : QWidget, optional
            The parent widget (default is None).
        name : str, optional
            Name of the worksheet (default is "worksheet").
        logger : logging.Logger, optional
            Logger for debug messages (default is None).
        '''
        super().__init__(parent)
        self.mdi_area = mdi_area
        self.name = name
        self.setWindowTitle(f"Worksheet - {self.name}")
        self.resize(550, 500)

        # Logger
        self.logger = logger
        # App instance
        self.app_instance = app_instance
        
        # Create an initial table with 20 rows and 4 columns
        self.table = QTableWidget(20, 4) 
        self.table.setHorizontalHeaderLabels([f"Col {i+1}" for i in range(4)])
        self.table.cellChanged.connect(self.auto_expand_rows)

        # Enable copy/paste functionality with ctrl+c / ctrl+v
        self.table.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)

        copy_action = QAction("Copy", self.table)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy_selection)
        self.table.addAction(copy_action)

        paste_action = QAction("Paste", self.table)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste_selection)
        self.table.addAction(paste_action)


        # Allow to rename columns by double-clicking header
        self.table.horizontalHeader().setSectionsClickable(True)
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)

        # Makes title editable
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.horizontalHeader().sectionDoubleClicked.connect(self.edit_column_name)

        # Selection of a single or several columns
        self._column_selection_anchor = None
        self.table.horizontalHeader().sectionClicked.connect(
            self.on_column_header_clicked
        )

        self.btn_add_col    = QPushButton("Add column")
        self.btn_rmv_col    = QPushButton("Remove column")
        self.btn_load       = QPushButton("Load from file")
        self.btn_plot       = QPushButton("Create Plot")
        self.btn_math       = QPushButton("Column Math")
        self.btn_custom     = QPushButton("Customization")
        self.btn_fit        = QPushButton("Fit Data")
        self.btn_appearance = QPushButton("Appearance")
        self.btn_import_col = QPushButton("Import Column")
        self.btn_export     = QPushButton("Save Data")
        
        # ---------- DATA GROUP ----------
        data_group  = QGroupBox("Data manipulation")
        data_layout = QHBoxLayout()
        data_group.setLayout(data_layout)

        data_layout.addWidget(self.btn_load)
        data_layout.addWidget(self.btn_import_col)
        data_layout.addWidget(self.btn_add_col)
        data_layout.addWidget(self.btn_rmv_col)
        data_layout.addWidget(self.btn_export)
        data_layout.addStretch()

        # ---------- PLOT GROUP ----------
        plot_group  = QGroupBox("Create and customize plots")
        plot_layout = QHBoxLayout()
        plot_group.setLayout(plot_layout)

        plot_layout.addWidget(self.btn_plot)
        plot_layout.addWidget(self.btn_custom)
        plot_layout.addWidget(self.btn_appearance)
        plot_layout.addStretch()

        # ---------- ANALYSIS GROUP ----------
        analysis_group  = QGroupBox("Analysis tools")
        analysis_layout = QHBoxLayout()
        analysis_group.setLayout(analysis_layout)

        analysis_layout.addWidget(self.btn_math)
        analysis_layout.addWidget(self.btn_fit)
        analysis_layout.addStretch()

        self.tools_stack = QStackedWidget()
        self.tools_stack.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        self.tools_stack.addWidget(data_group)
        self.tools_stack.addWidget(plot_group)
        self.tools_stack.addWidget(analysis_group)


        self.btn_data_tab     = QPushButton("Data")
        self.btn_plot_tab     = QPushButton("Plot")
        self.btn_analysis_tab = QPushButton("Analysis")
        self.btn_help         = QPushButton("Help")

        tab_layout = QHBoxLayout()
        tab_layout.addWidget(self.btn_data_tab)
        tab_layout.addWidget(self.btn_plot_tab)
        tab_layout.addWidget(self.btn_analysis_tab)
        tab_layout.addWidget(self.btn_help)
        tab_layout.addStretch()

        for btn in [self.btn_data_tab, self.btn_plot_tab, self.btn_analysis_tab]:
            btn.setCheckable(True)
        
        
        layout = QVBoxLayout()
        layout.addLayout(tab_layout)            # Buttons to switch between sections
        layout.addWidget(self.tools_stack)      # Stacked widget with different sections
        layout.addWidget(self.table, stretch=1) # Table takes remaining space

        container = QWidget()
        container.setLayout(layout)
        self.setWidget(container)

        def show_help_dialog():
            help_text = (
                "Worksheet Guide:\n\n"
                "- Use the 'Data' tab to load data from files, add/remove columns, or import columns from loaded data.\n"
                "- Use the 'Plot' tab to create and customize plots.\n"
                "- Use the 'Analysis' tab to perform mathematical operations and curve fitting."
            )
            QMessageBox.information(self, "Worksheet Guide", help_text)

        # Connect button actions
        self.btn_plot.clicked.connect(self.create_plot)
        self.btn_export.clicked.connect(self.export_data)
        self.btn_add_col.clicked.connect(self.add_column)
        self.btn_rmv_col.clicked.connect(self.remove_column)
        self.btn_math.clicked.connect(self.open_math_dialog)
        self.btn_custom.clicked.connect(self.customize_plot)
        self.btn_load.clicked.connect(self.load_file_into_table)
        self.btn_fit.clicked.connect(self.open_curve_fitting_window)
        self.btn_import_col.clicked.connect(self.import_column_from_main)
        self.btn_appearance.clicked.connect(self.customize_plot_appearance)

        self.section_group = QButtonGroup(self)
        self.section_group.setExclusive(True)

        self.section_group.addButton(self.btn_data_tab, 0)
        self.section_group.addButton(self.btn_plot_tab, 1)
        self.section_group.addButton(self.btn_analysis_tab, 2)

        self.section_group.buttonClicked[int].connect(self.tools_stack.setCurrentIndex)
        self.btn_data_tab.setChecked(True)

        self.btn_help.clicked.connect(show_help_dialog)

        # Attributes to memorize plot windows
        self.plots              = {}   # {int: {"x":..., "y":..., "x_err":..., "y_err":..., "geom":...}}
        self.plot_count         = 0    # to assign unique plot IDs
        self.plot_subwindows    = {}   # {int: QMdiSubWindow}
        self._plot_widgets      = {}   # {plot_id: {"sub": sub, "container": widget, "canvas": canvas, "toolbar": toolbar}}
        self.figure             = {}   # {plot_id: {"figure": Figure, "ax": Axes,}
        self.plot_customization = {}   # {"figure":..., "ax":..., "canvas":..., "customizations": {...}}

    
    def sync_to_data(self):
        '''
        Function to update dataframe storage
        '''
        if self.app_instance and hasattr(self.app_instance, "worksheet_dfs"):
            df = self.to_dataframe()
            self.app_instance.worksheet_dfs.add(self.name, df)

    
    def closeEvent(self, event):
        '''
        Cleanup when the worksheet window is closed.
        Parameters
        ----------
        event : QCloseEvent
            The close event.
        '''
        # Close all plot subwindows linked to this worksheet
        try:
            for pid, sub in list(self.plot_subwindows.items()):
                try:
                    sub.close()
                except Exception:
                    pass
            self.plot_subwindows.clear()
            self._plot_widgets.clear()
            self.figure.clear()
            self.plot_customization.clear()
            self.plots.clear()

            # Remove self from parent's worksheet tracking
            if hasattr(self, "mdi_area") and self.mdi_area is not None:
                 
                parent = self.mdi_area.parent()
                if parent is not None:
                    for idx, ws in list(parent.worksheet_windows.items()):
                        if ws is self:
                            parent.worksheet_windows.pop(idx, None)
                            parent.worksheet_names.pop(idx, None)
                            parent.worksheet_subwindows.pop(idx, None)
                            break
            # Remove associated dataframe
            if self.app_instance and hasattr(self.app_instance, "worksheet_dfs"):
                self.app_instance.worksheet_dfs.remove(self.name)

        except Exception as e:
            print(f"[DEBUG] Error during worksheet cleanup: {e}")

        super().closeEvent(event)

    def on_column_header_clicked(self, col):
        '''
        Handle column header click for selection with modifiers.

        Parameters
        ----------
        col : int
            The index of the clicked column.
        '''
        modifiers = QApplication.keyboardModifiers()

        sel_model = self.table.selectionModel()
        col_index = self.table.model().index(0, col)

        if modifiers & Qt.ControlModifier:
            sel_model.select(
                col_index,
                QItemSelectionModel.Select | QItemSelectionModel.Columns
            )
        elif modifiers & Qt.ShiftModifier:
            sel_model.select(
                col_index,
                QItemSelectionModel.SelectCurrent | QItemSelectionModel.Columns
            )
        else:
            sel_model.clearSelection()
            sel_model.select(
                col_index,
                QItemSelectionModel.Select | QItemSelectionModel.Columns
            )


    def copy_selection(self):
        '''
        Copy selected columns or selected cells to clipboard
        in tab-delimited format.
        '''

        clipboard       = QApplication.clipboard()
        selection_model = self.table.selectionModel()

        selected_columns = selection_model.selectedColumns()

        # Case 1: Selection of the columns
        if selected_columns:
            cols   = sorted(c.column() for c in selected_columns)
            copied = []

            for row in range(self.table.rowCount()):
                row_data = []
                for col in cols:
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                copied.append("\t".join(row_data))

            clipboard.setText("\n".join(copied))
            return

        # Case 2: Selection of the cells
        selection = self.table.selectedRanges()
        if not selection:
            return

        r = selection[0]
        copied = []
        for row in range(r.topRow(), r.bottomRow() + 1):
            row_data = []
            for col in range(r.leftColumn(), r.rightColumn() + 1):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            copied.append("\t".join(row_data))
        
        clipboard.setText("\n".join(copied))
    
    def paste_selection(self):
        ''' 
        Paste tab-delimited data from clipboard into
        the table starting at current cell.
        '''
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            return

        # Remove empty line (clipboard behaviour)
        rows = [r for r in text.split("\n")  if r.strip("\t ") != ""]
        data = [row.split("\t") for row in rows] 
        
        start_col = self.table.currentColumn()
        start_row = self.table.currentRow()

        num_cols  = max(len(r) for r in data)

        # Ensure enough columns
        while start_col + num_cols > self.table.columnCount():
            c = self.table.columnCount()
            self.table.insertColumn(c)
            self.table.setHorizontalHeaderItem(
                c, QTableWidgetItem(f"Col {c+1}")
            )

        # Ensure enough rows
        while start_row + len(data) > self.table.rowCount():
            self.table.insertRow(self.table.rowCount())

        for i, row in enumerate(data):
            for j, cell in enumerate(row):
                r = start_row + i
                c = start_col + j
                self.table.setItem(r, c, QTableWidgetItem(cell))
        
        self.sync_to_data()


    def load_file_into_table(self):
        '''
        Load data from a text file into the table.

        The function automatically detects header rows
        and populates the QTableWidget with the parsed data.
        '''
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load file", "", "Text Files (*.txt);;All Files (*)"
        )
        if not file_path:
            return

        try:
            header_length = detect_header_length(file_path)
            
            # Handle different header scenarios
            if header_length > 0:
                df = pd.read_csv(file_path, sep="\t").drop(list(range(header_length)))
                
            elif header_length == -1:
                data     = np.loadtxt(file_path)
                _, n_col = data.shape
                col      = [f"col_{i}" for i in range(n_col)]
                df       = pd.DataFrame(data, columns=col)
            else:
                df = pd.read_csv(file_path, sep="\t")

            # Update table size
            self.table.setRowCount(len(df))
            self.table.setColumnCount(len(df.columns))
            self.table.setHorizontalHeaderLabels([str(c) for c in df.columns])

            #Log loaded data info
            if self.logger is not None:
                self.logger.info(f"Loaded file '{file_path}' in worksheet with {len(df)} rows and {len(df.columns)} columns.")
            
            # Populate table with data
            for r in range(len(df)):
                for c in range(len(df.columns)):
                    val = df.iat[r, c]
                    if pd.isna(val):
                        item = QTableWidgetItem("")
                    else:
                        item = QTableWidgetItem(str(val))
                    self.table.setItem(r, c, item)
            
            self.sync_to_data()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error in loading file:\n{e}")
    
    def export_data(self):
        '''
        Export current worksheet data to file.
        '''
        df = self.to_dataframe()

        if df.empty:
            QMessageBox.warning(self, "Error", "Worksheet is empty.")
            return

        options = QFileDialog.Options()
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Worksheet Data",
            f"{self.name}.txt",
            "CSV files (*.csv);;Text files (*.txt)",
            options=options
        )

        if not file_path:
            return

        try:
            if selected_filter.startswith("CSV"):
                df.to_csv(file_path, index=False)

            elif selected_filter.startswith("Text"):
                df.to_csv(file_path, sep="\t", index=False)

            QMessageBox.information(self, "Success", f"Data exported to:\n{file_path}")

            if self.logger:
                self.logger.info(f"Worksheet '{self.name}' exported to {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export data:\n{e}")


    def add_column(self):
        ''' Add a new empty column to the table.
        '''
        col_count = self.table.columnCount()
        self.table.insertColumn(col_count)
        self.table.setHorizontalHeaderItem(col_count, QTableWidgetItem(f"Col {col_count+1}"))
        self.sync_to_data()

    def remove_column(self):
        ''' Remove the currently selected column(s) from the table.
        '''
        selected = self.table.selectionModel().selectedColumns()
        if not selected:
            return  # Nothing selected to remove so return
        
        if len(selected) > 1:
            reply = QMessageBox.question(
                self,
                "Remove columns",
                f"Remove {len(selected)} columns?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        
        # Remove columns in reverse order to avoid index shifting
        for col in sorted([c.column() for c in selected], reverse=True):
            self.table.removeColumn(col)
        
        self.sync_to_data()

    def auto_expand_rows(self, row, col):
        '''
        Automatically add a new row if the user edits the last row.

        Parameters
        ----------
        row : int
            The row index that was edited.
        col : int
            The column index that was edited.
        '''
        if row == self.table.rowCount() - 1:
            self.table.insertRow(self.table.rowCount())

    def edit_column_name(self, index):
        '''
        Open a dialog to edit the name of the column at the given index.

        Parameters
        ----------
        index : int
            The index of the column to rename.
        '''
        current_name = self.table.horizontalHeaderItem(index).text()
        new_name, ok = QInputDialog.getText(
            self, "Rename column", "New column name:", text=current_name
        )
        if ok and new_name.strip():
            self.table.setHorizontalHeaderItem(index, QTableWidgetItem(new_name.strip()))


    def import_column_from_main(self):
        '''
        Import a column from one of the DataFrames loaded in MainApp.
        The worksheet will know the dataframes only if they are loaded
        before creating the worksheet.
        '''
        data = self.app_instance
        
        if len(data.dataframes) == 0:
            msg  = "No DataFrames in this woorksheet. "
            msg += "The worksheet will know the dataframes only if "
            msg += "they are loaded before creating the worksheet. "
            msg += "So you need to create a new one."
            QMessageBox.warning(self, "Error", msg)
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Import column from loaded data")
        dialog.resize(500, 200)

        layout = QHBoxLayout(dialog)

        # Left list = dataframe names
        df_list = QListWidget()
        df_list.addItems([f"File {i+1}" for i in range(len(data.dataframes))])
        layout.addWidget(df_list)

        # Right list = columns of selected dataframe
        col_list = QListWidget()
        col_list.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(col_list)

        # Update columns when a dataframe is selected
        def update_columns():
            col_list.clear()
            idx = df_list.currentRow()
            if idx >= 0:
                df = data.dataframes[idx]
                col_list.addItems(df.columns)

        df_list.currentRowChanged.connect(update_columns)
        df_list.setCurrentRow(0)  # show first dataframe by default

        # Buttons
        btn_box = QVBoxLayout()
        layout.addLayout(btn_box)

        import_btn = QPushButton("Import")
        cancel_btn = QPushButton("Cancel")
        btn_box.addWidget(import_btn)
        btn_box.addWidget(cancel_btn)
        btn_box.addStretch()

        # === When Import is clicked ===
        def do_import():
            df_idx     = df_list.currentRow()
            selections = col_list.selectedItems()

            if df_idx < 0 or not selections:
                QMessageBox.warning(dialog, "Error", "Please select a dataframe and a column.")
                return

            df = data.dataframes[df_idx]
            # Determine max length first
            max_len = max(len(df[item.text()]) for item in selections)

            # Ensure table has enough rows
            while self.table.rowCount() < max_len:
                self.table.insertRow(self.table.rowCount())
                
            # Import each selected column
            for item in selections:

                col_name = item.text()
                values   = df[col_name].values

                new_col_index = self.table.columnCount()
                self.table.insertColumn(new_col_index)
                self.table.setHorizontalHeaderItem(
                    new_col_index,
                    QTableWidgetItem(col_name)
                )

                for r, val in enumerate(values):
                    self.table.setItem(
                        r,
                        new_col_index,
                        QTableWidgetItem(str(val))
                    )
            
            self.sync_to_data()

            dialog.accept()

        import_btn.clicked.connect(do_import)
        cancel_btn.clicked.connect(dialog.reject)

       

        dialog.exec_()

    def to_dataframe(self):
        '''
        Convert the table contents to a pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the numeric values from the table.
            Non-numeric values are replaced with an empty string.
        '''
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        data = {}

        for vc in range(cols):
            lc       = self.table.horizontalHeader().logicalIndex(vc)
            col_name = self.table.horizontalHeaderItem(lc).text()
            values = []
            for r in range(rows):
                item = self.table.item(r, lc)
                if item is None or item.text().strip() == "":
                    values.append(np.nan)
                else:
                    try:
                        values.append(float(item.text()))
                    except ValueError:
                        values.append(np.nan)
            data[col_name] = values
        return pd.DataFrame(data)
    

    def open_math_dialog(self):
        ''' Open a dialog to perform arithmetic operations between columns.
        '''
        columns = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
        if not columns:
            return

        dlg = ColumnMathDialog(columns, self)
        if dlg.exec_() != QDialog.Accepted:
            return

        sel      = dlg.get_selection()
        mode     = sel["mode"]
        new_name = sel["new_name"]

        if not new_name:
            QMessageBox.warning(self, "Error", "Please enter a name for the new column.")
            return

        df = self.to_dataframe()

        try:
            # Operation between two columns or column and constant
            if mode == "Arithmetic between columns":
                col_a, op, col_b, const_str = sel["col_a"], sel["op"], sel["col_b"], sel["const"]
                series_a = df[col_a].astype(float)
                
                if col_b:
                    series_b = df[col_b].astype(float)
                else:
                    if not const_str:
                        raise ValueError("Constant value required.")
                    series_b = float(const_str)
                
                result = {
                    "+": series_a + series_b,
                    "-": series_a - series_b,
                    "*": series_a * series_b,
                    "/": series_a / series_b,
                    "mean": (series_a + series_b) / 2.0
                }.get(op)
                if result is None:
                    raise ValueError("Unknown operation")
            
            elif mode == "Custom expression between columns":
                expr = sel["expr"]

                allowed_dict = {
                    "np": np,
                    **{col: df[col].values for col in df.columns}
                }

                try:
                    result = eval(expr, {"__builtins__": {}}, allowed_dict)
                except Exception as e:
                    QMessageBox.warning(self, "Error", str(e))
                    return
            
            # Generate linspace
            elif mode in ("Generate linspace", "Generate logspace"):
                start, stop, num = float(sel["start"]), float(sel["stop"]), int(sel["num"])
                result = np.linspace(start, stop, num) if mode == "Generate linspace" else np.logspace(start, stop, num)

            # Generate custom function
            elif mode == "Generate function from linspace/logspace":
                
                start, stop, num = float(sel["start"]), float(sel["stop"]), int(sel["num"])
                func_str   = sel["func"]
                space_type = sel.get("space_type", "linspace")
                
                if not func_str:
                    raise ValueError("Please provide a function f(x).")

                # Generate indipendent variable x
                if space_type == "linspace":
                    x = np.linspace(start, stop, num)
                else:
                    x = np.logspace(start, stop, num)
                
                # Compute the function
                safe_env = {"np": np, "x": x}
                y        = eval(func_str, {"__builtins__": {}}, safe_env)

                # Naming the new columns
                x_name = new_name + "_x"
                y_name = new_name + "_y"
                for col_name, data in [(x_name, x), (y_name, y)]:
                    new_col_index = self.table.columnCount()
                    self.table.insertColumn(new_col_index)
                    self.table.setHorizontalHeaderItem(new_col_index, QTableWidgetItem(col_name))
                    for r, val in enumerate(data):
                        self.table.setItem(r, new_col_index, QTableWidgetItem(str(val)))
                
                self.sync_to_data()
                return  # Avoid adding extra column below

            else:
                raise ValueError(f"Unknown mode {mode}")


            # Add new single column to the table
            new_col_index = self.table.columnCount()
            self.table.insertColumn(new_col_index)
            self.table.setHorizontalHeaderItem(new_col_index, QTableWidgetItem(new_name))
            for r, val in enumerate(result):
                if pd.notna(val):
                    self.table.setItem(r, new_col_index, QTableWidgetItem(str(val)))

            self.sync_to_data()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Operation failed:\n{e}")


    def create_plot(self):
        '''
        Open a dialog to select columns and create a plot.

        The user chooses X, Y, and optionally error bar columns.
        '''
       
        data      = self.app_instance.worksheet_dfs
        flat_cols = list(data.get_all_columns().keys())

        if not flat_cols:
            QMessageBox.warning(self, "Error", "No data available.")
            return

        dialog = ColumnSelectionDialog(flat_cols, self)

        if dialog.exec_() == QDialog.Accepted:
            selections = dialog.get_selection()
            self.open_plot_window(selections)


    def open_plot_window(self, selections, show=True, plot_id=None, customizations=None):
        '''
        Open a new subwindow with a plot of the selected columns.

        Parameters
        ----------
        selections : list of dict
            List of selections, each a dict with keys:
            'x', 'y', 'x_err', 'y_err' for column names.
        show : bool, optional
            Whether to show the plot window immediately (default is True).
        plot_id : int or None, optional
            If provided, use this as the plot ID; otherwise, auto-increment (default is
        customizations : dict or None, optional
            Customization settings for the plot (default is None).
        
        Returns
        -------
        QMdiSubWindow
            The subwindow containing the plot.
        '''

        # --- handle plot_id ---
        if plot_id is None:
            self.plot_count += 1
            plot_id = self.plot_count
        else:
            # keep track of highest id
            try:
                pid_int = int(plot_id)
                if pid_int > self.plot_count:
                    self.plot_count = pid_int
            except Exception:
                pass

        fig = Figure(figsize=(6, 4))
        ax  = fig.add_subplot(111)

        self.figure[plot_id] = {
            "figure": fig, "ax": ax, 
            "sub": None, "curves": []
        }

        data     = self.app_instance.worksheet_dfs
        flat_map = data.get_all_columns()
        
        def resolve_column(col_name):
            '''
            Simple function to ensure retrocompatibility
            '''
            # New format with flat mapping → directly resolve
            if col_name in flat_map:
                return flat_map[col_name]

            # Legacy format without flat mapping
            current_ws = self.name 

            df = data.get(current_ws)
            if df is not None and col_name in df.columns:
                return current_ws, col_name
            

        for i, sel in enumerate(selections, start=1):

            x_ws, x_col = resolve_column(sel["x"])
            x = data.get(x_ws)[x_col].values

            y_ws, y_col = resolve_column(sel["y"])
            y = data.get(y_ws)[y_col].values

            xerr = None
            if sel["x_err"]:
                dx_ws, dx_col = resolve_column(sel["x_err"])
                xerr = data.get(dx_ws)[dx_col].values
            
            yerr = None
            if sel["y_err"]:
                dy_ws, dy_col = resolve_column(sel["y_err"])
                yerr = data.get(dy_ws)[dy_col].values


            label = sel["y"] if len(selections) == 1 else f"{sel['y']}"

            if xerr is not None or yerr is not None:
                # Plot with error bars
                err_c = ax.errorbar(x, y, xerr=xerr, yerr=yerr, fmt="o-")
                # Store the output for customization
                if not hasattr(ax, "_err_c"):
                    ax._err_c = {}
                ax._err_c[i-1] = err_c
                # Set label for legend
                err_c[0].set_label(label)

                # Save data in figure fot fitting
                line_obj = err_c[0]
                self.figure[plot_id]["curves"].append({
                    "line": line_obj,
                    "x": np.array(x),
                    "y": np.array(y),
                    "xerr": np.array(xerr) if xerr is not None else None,
                    "yerr": np.array(yerr) if yerr is not None else None,
                    "x_ws": x_ws,
                    "y_ws": y_ws,
                    "x_col": x_col,
                    "y_col": y_col
                })

            else:
                line_obj, = ax.plot(x, y, "o-", label=label)

                self.figure[plot_id]["curves"].append({
                    "line": line_obj,
                    "x": np.array(x),
                    "y": np.array(y),
                    "xerr": None,
                    "yerr": None,
                    "x_ws": x_ws,
                    "y_ws": y_ws,
                    "x_col": x_col,
                    "y_col": y_col
                })

        # Log the creation of the plot with selcected columns
        if self.logger is not None:
            msg = f"Created plot (ID: {plot_id if plot_id is not None else self.plot_count + 1}) with selections: "
            msg += ", ".join([f"(X: {s['x']}, Y: {s['y']})" for s in selections])
            self.logger.info(msg)


        lines = [ln for ln in ax.lines if ln.get_gid() != "fit"]
        if customizations:
            for idx, style in customizations.items():
                try:
                    idx = int(idx)
                    if idx >= len(lines):
                        continue
                    line = lines[idx]

                    color     = style.get("color")
                    marker    = style.get("marker")
                    linestyle = style.get("linestyle")
                    label     = style.get("label")

                    line.set_color(color)
                    line.set_marker(marker)
                    line.set_linestyle(linestyle)
                    line.set_label(label)

                    if hasattr(ax, "_err_c"):
                        err_collections = ax._err_c
                        if idx in err_collections.keys():
                            err_c = err_collections[idx]
                            err_c[0].set_marker(marker)
                            err_c[0].set_linestyle(linestyle)
                            err_c[0].set_label(label)
                            err_c[0].set_color(color)
                            err_c[2][0].set_color(color)

                except Exception:
                    continue

            
            fig.canvas.draw_idle()

        # Store customization settings
        self.plot_customization[plot_id] = customizations or {}

        ax.set_xlabel(selections[0]["x"]) 
        ax.set_ylabel("Values")
        ax.grid(True)

        # Legend
        err_c_vals = list(ax._err_c.values()) if hasattr(ax, "_err_c") else []
        handles = [ln for ln in ax.lines if all(ln is not e[0] for e in err_c_vals)] + err_c_vals

        labels = []
        for h in handles:
            if isinstance(h, ErrorbarContainer):
                labels.append(h[0].get_label())
            else:
                labels.append(h.get_label())

        ax.legend(handles, labels, handler_map={ErrorbarContainer: HandlerErrorbar()})


        canvas = FigureCanvas(fig)
        plot_container = QWidget()
        vlayout = QVBoxLayout(plot_container)
        vlayout.setContentsMargins(0, 0, 0, 0)

        toolbar = NavigationToolbar(canvas, plot_container)
        vlayout.addWidget(toolbar)
        vlayout.addWidget(canvas)
        plot_container.setLayout(vlayout)

        
        sub = QMdiSubWindow()
        sub.setWindowTitle(f"From {self.name} plot {plot_id}")
        sub.setWidget(plot_container)
        self.mdi_area.addSubWindow(sub)

        self._plot_widgets[plot_id] = {
            "sub": sub,
            "container": plot_container,
            "canvas": canvas,
            "toolbar": toolbar
        }

        self.figure[plot_id]["sub"] = sub

        self.plot_customization[plot_id] = {
            "figure": fig,
            "ax": ax,
            "canvas": canvas,
            "customizations": customizations or {}
        }

        canvas.draw_idle()
        # show only if requested
        if show:
            # show after addSubWindow: the MDI may apply a default cascading; caller can still reposition if desired
            sub.show()

        # Cleanup references when the subwindow is closed
        def _cleanup(pid=plot_id):
            self._plot_widgets.pop(pid, None)
            self.plot_subwindows.pop(pid, None)
            self.figure.pop(pid, None)
            self.plot_customization.pop(pid, None)
            self.plots.pop(pid, None)

        # Connect the destroyed signal to cleanup
        sub.destroyed.connect(lambda _=None, pid=plot_id: _cleanup(pid))

        # Save plot info for session management
        self.plot_subwindows[plot_id] = sub
        self.plots[plot_id] = {
            "selections": selections,
            "geometry": {
                "x": sub.x(),
                "y": sub.y(),
                "width": sub.width(),
                "height": sub.height(),
                "minimized": sub.isMinimized()
            }
        }

        def on_subwindow_close(event, pid=plot_id):
            self._plot_widgets.pop(pid, None)
            self.plot_subwindows.pop(pid, None)
            self.figure.pop(pid, None)
            self.plot_customization.pop(pid, None)
            self.plots.pop(pid, None)
            event.accept()

        sub.closeEvent = lambda event, pid=plot_id: on_subwindow_close(event, pid)

        return sub
    
    def customize_plot(self):
        '''
        Open a dialog to customize plot styles (color, marker, linestyle, label).
        '''
        if not self.figure:
            QMessageBox.critical(self, "Error", "No plot open! Create a plot first.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Customize Plot Style")
        dialog.setFixedSize(420, 360)

        layout      = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        layout.addLayout(form_layout)

        # Choose plot to customize
        plot_combo = QComboBox()
        for pid, info in self.figure.items():
            title = info["sub"].windowTitle()
            plot_combo.addItem(f"Plot {pid}: {title}", pid)

        form_layout.addRow("Select Plot:", plot_combo)


        line_combo      = QComboBox()
        color_combo     = QComboBox()
        marker_combo    = QComboBox()
        linestyle_combo = QComboBox()
        label_edit      = QLineEdit()

        color_combo.addItems(list(mcolors.TABLEAU_COLORS) + list(mcolors.CSS4_COLORS))
        color_combo.setEditable(True)
        marker_combo.addItems([m for m in markers.MarkerStyle.markers.keys() if isinstance(m, str) and len(m) == 1])
        marker_combo.setEditable(True)
        linestyle_combo.addItems(list(mlines.Line2D.lineStyles.keys()))
        linestyle_combo.setEditable(True)

        form_layout.addRow("Line:", line_combo)
        form_layout.addRow("Color:", color_combo)
        form_layout.addRow("Marker:", marker_combo)
        form_layout.addRow("Linestyle:", linestyle_combo)
        form_layout.addRow("Legend label:", label_edit)

        def update_lines():
            pid   = plot_combo.currentData()
            ax    = self.figure[pid]["ax"]
            lines = [ln for ln in ax.lines if ln.get_gid() != "fit"]
            line_combo.clear()
            
            for i, ln in enumerate(lines):
                line_combo.addItem(ln.get_label() or f"Line {i+1}", i)
            
            if lines:
                label_edit.setText(lines[0].get_label() or "")

        plot_combo.currentIndexChanged.connect(update_lines)
        update_lines()

        apply_button = QPushButton("Apply")
        layout.addWidget(apply_button)

        def apply_style():
            try:
                pid      = plot_combo.currentData()
                line_idx = line_combo.currentData()
                ax       = self.figure[pid]["ax"]
                fig      = self.figure[pid]["figure"]
                line     = [ln for ln in ax.lines if ln.get_gid() != "fit"][line_idx]
                
                color        = color_combo.currentText()
                marker       = marker_combo.currentText()
                linestyle    = linestyle_combo.currentText()
                legend_label = label_edit.text() or line.get_label()

                line.set_color(color)
                line.set_marker(marker)
                line.set_linestyle(linestyle)
                line.set_label(legend_label)

                # Customization for error bars if present
                if hasattr(ax, "_err_c"):
                    err_collections = ax._err_c
                   
                    if line_idx in err_collections.keys():
                        err_c = err_collections[line_idx]
                        err_c[0].set_color(color)
                        err_c[0].set_marker(marker)
                        err_c[0].set_linestyle(linestyle)
                        err_c[0].set_label(legend_label)
                        err_c[2][0].set_color(color)
                       
                    

                self.plot_customization[pid]["customizations"][line_idx] = {
                    "color":     color,
                    "marker":    marker,
                    "linestyle": linestyle,
                    "label":     legend_label,
                }

                # Legend update
                err_c_vals = list(ax._err_c.values()) if hasattr(ax, "_err_c") else []
                handles = [ln for ln in ax.lines if all(ln is not e[0] for e in err_c_vals)] + err_c_vals

                labels = []
                for h in handles:
                    if isinstance(h, ErrorbarContainer):
                        labels.append(h[0].get_label())
                    else:
                        labels.append(h.get_label())

                ax.legend(handles, labels, handler_map={ErrorbarContainer: HandlerErrorbar()})

                fig.canvas.draw_idle()
                dialog.accept()

            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Error applying style:\n{e}")

        apply_button.clicked.connect(apply_style)
        dialog.exec_()
    
    def customize_plot_appearance(self):
        ''' Open a dialog to customize the appearance of the plot (font sizes, minor ticks).
        '''
        if not self.figure:
            QMessageBox.warning(self, "Error", "No plots available! Create a plot first.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Plot Appearance")
        dialog.setFixedSize(400, 280)
        layout = QFormLayout(dialog)

        # Select plot
        layout.addRow(QLabel("Select plot:"))
        plot_combo = QComboBox()
        for pid, info in self.figure.items():
            sub_title = info["sub"].windowTitle()
            plot_combo.addItem(f"Plot {pid}: {sub_title}", pid)
        layout.addRow(plot_combo)

        # Font sizes
        label_fontsize_edit  = QLineEdit("14")
        tick_fontsize_edit   = QLineEdit("10")
        legend_fontsize_edit = QLineEdit("10")

        # Minor ticks (safe)
        minor_ticks_checkbox = QCheckBox("Show minor ticks")
        minor_ticks_checkbox.setChecked(True)

        layout.addRow("Axis label fontsize:", label_fontsize_edit)
        layout.addRow("Tick label fontsize:", tick_fontsize_edit)
        layout.addRow("Legend fontsize:",     legend_fontsize_edit)
        layout.addRow(minor_ticks_checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        def apply_changes():
            try:
                pid = plot_combo.currentData()
                if pid not in self.figure:
                    QMessageBox.warning(dialog, "Error", "Selected plot not found!")
                    return

                fig_info = self.figure[pid]
                ax = fig_info["ax"]
                canvas = self.plot_customization[pid]["canvas"]

                label_fs  = float(label_fontsize_edit.text())
                tick_fs   = float(tick_fontsize_edit.text())
                legend_fs = float(legend_fontsize_edit.text())

                # --- Axis labels ---
                ax.xaxis.label.set_fontsize(label_fs)
                ax.yaxis.label.set_fontsize(label_fs)

                # --- Tick labels ---
                for label in ax.get_xticklabels() + ax.get_yticklabels():
                    label.set_fontsize(tick_fs)

                # --- Legend ---
                leg = ax.get_legend()
                if leg:
                    for text in leg.get_texts():
                        text.set_fontsize(legend_fs)

                # --- Minor ticks ---
                if minor_ticks_checkbox.isChecked():
                    ax.minorticks_on()
                else:
                    ax.minorticks_off()

                canvas.draw_idle()
                dialog.accept()

            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Error applying appearance settings:\n{e}")

        buttons.accepted.connect(apply_changes)
        buttons.rejected.connect(dialog.reject)
        dialog.exec_()



    def open_curve_fitting_window(self):
        '''
        Open a window to perform quick curve fitting on selected data.
        The user selects X and Y columns, fitting function, initial parameters, and range.
        The fit result is displayed and the fitted curve is plotted on the selected graph.
        '''
        df = self.to_dataframe()
        if df.empty:
            QMessageBox.warning(self, "Error", "No data in the worksheet!")
            return

        if not self.figure:
            QMessageBox.warning(self, "Error", "No plots available! Create a plot first.")
            return

        # Create the fitting window
        window = QWidget()
        window.setWindowTitle("Quick Curve Fitting")
        layout = QVBoxLayout(window)
        window.setLayout(layout)


        def show_help_dialog():
            help_text = (
                "The fit function must be a function of the variable 'x' and "
                "the parameter names must be specified in the appropriate field.\n\n"
                "To establish the range, just read the cursor on the graph, the values are at the top right.\n\n"
                "ACHTUNG: the function must be written in Python, so for example |x| is abs(x), x^2 is x**2, and all "
                "other functions must be written with np. in front (i.e. np.cos(x), np.exp(x)), except for special functions, "
                "for which you must use the name used by the scipy.special library (i.e. scipy.special.erf becomes erf)."
            )
            QMessageBox.information(window, "Fitting Guide", help_text)

        help_button = QPushButton("Help")
        help_button.clicked.connect(show_help_dialog)
        layout.addWidget(help_button, alignment=Qt.AlignLeft)

        # === left column fit parameter ===      
        selection_layout = QHBoxLayout()
        layout.addLayout(selection_layout)

        
        param_layout = QGridLayout()
        selection_layout.addLayout(param_layout)

        # Select target plot
        param_layout.addWidget(QLabel("Select target plot:"), 0, 0)
        plot_combo = QComboBox()

        for pid, info in self.figure.items():
            sub_title = info["sub"].windowTitle()
            plot_combo.addItem(f"Plot {pid}: {sub_title}", pid)
        param_layout.addWidget(plot_combo, 0, 1)

        param_layout.addWidget(QLabel("Select curve:"), 1, 0)
        curve_combo = QComboBox()
        param_layout.addWidget(curve_combo, 1, 1)

        param_layout.addWidget(QLabel("x_start:"), 2, 0)
        x_start_edit = QLineEdit("-10")
        param_layout.addWidget(x_start_edit, 2, 1)

        param_layout.addWidget(QLabel("x_end:"), 3, 0)
        x_end_edit = QLineEdit("10")
        param_layout.addWidget(x_end_edit, 3, 1)

        param_layout.addWidget(QLabel("Parameter names (e.g. a,b):"), 4, 0)
        param_names_edit = QLineEdit("a,b")
        param_layout.addWidget(param_names_edit, 4, 1)

        param_layout.addWidget(QLabel("Initial values (e.g. 1,1):"), 5, 0)
        initial_params_edit = QLineEdit("1,1")
        param_layout.addWidget(initial_params_edit, 5, 1)

        param_layout.addWidget(QLabel("Fitting function (e.g. a*x + b):"), 6, 0)
        function_edit = QLineEdit("a*x + b")
        param_layout.addWidget(function_edit, 6, 1)

        #======================================================================#

        def update_range():
            pid = plot_combo.currentData()
            curve_index = curve_combo.currentData()

            if pid not in self.figure:
                return

            curves = self.figure[pid]["curves"]
            if not curves:
                return

            if curve_index is None:
                return

            curve_data = curves[curve_index]
            x_vals = np.array(curve_data["x"], dtype=float)
            x_vals = x_vals[np.isfinite(x_vals)]

            if len(x_vals) > 0:
                x_start_edit.setText(str(np.min(x_vals)))
                x_end_edit.setText(str(np.max(x_vals)))

        def update_curves():
            curve_combo.clear()
            pid = plot_combo.currentData()
            if pid not in self.figure:
                return
            for i, curve in enumerate(self.figure[pid]["curves"]):
                label = curve["line"].get_label()
                curve_combo.addItem(f"Curve {i+1}: {label}", i)
            
            update_range()
            

        plot_combo.currentIndexChanged.connect(update_curves)
        curve_combo.currentIndexChanged.connect(update_range)
        update_curves()

        #======================================================================#

        # Output 
        output_box = QTextEdit()
        output_box.setReadOnly(True)
        output_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        selection_layout.addWidget(output_box)

        def perform_fit():
            ''' Perform the curve fitting and update the plot.
            '''
            try:
                # Retrieve data and parameters
                pid = plot_combo.currentData()
                curve_index = curve_combo.currentData()

                if pid not in self.figure:
                    QMessageBox.warning(window, "Error", "Plot not found!")
                    return

                curve_data = self.figure[pid]["curves"][curve_index]

                x = np.array(curve_data["x"], dtype=float)
                y = np.array(curve_data["y"], dtype=float)

                x_start = float(x_start_edit.text())
                x_end   = float(x_end_edit.text())
                mask    = (x >= x_start) & (x <= x_end)
                x_fit, y_fit = x[mask], y[mask]

                if len(x_fit) == 0:
                    QMessageBox.warning(window, "Error", "No data in selected range!")
                    return

                param_names    = [p.strip() for p in param_names_edit.text().split(",")]
                initial_params = [float(p.strip()) for p in initial_params_edit.text().split(",")]

                func_code = f"lambda x, {', '.join(param_names)}: {function_edit.text()}"
                fit_func = eval(func_code)

                # Execute the fit
                params, pcov = curve_fit(fit_func, x_fit, y_fit, p0=initial_params)
                y_model = fit_func(np.linspace(x_start, x_end, 500), *params)

                # Show fit results
                lines = []
                for p, val, err in zip(param_names, params, np.sqrt(np.diag(pcov))):
                    try:
                        lines.append(f"{p} = {format_value_error(val, err)}")    
                    except Exception as e:
                        lines.append(f"{p} = {val:.6f} ± {err:.6f}")
                
                for i , pi in zip(range(len(params)), param_names):
                    for j , pj in zip(range(i+1, len(params)), param_names[i+1:]):
                        corr_ij = pcov[i, j]/np.sqrt(pcov[i, i]*pcov[j, j])
                        lines.append(f"corr({pi}, {pj}) = {corr_ij:.3f}")

                result_text = "\n".join(lines)
                output_box.setPlainText(result_text)

                # Log fit data and results
                if self.logger is not None:
                    self.logger.info(
                        f"Performed curve fit on columns X: '{curve_data['x_col']}', Y: '{curve_data['y_col']}' "
                        f"with range [{x_start}, {x_end}] "
                        f"with function: {function_edit.text()} "
                        f"and parameters: {', '.join(param_names)}. Results:\n{str(result_text).replace(chr(10), ' ')}")

                # Draw fit on the plot
                pid = plot_combo.currentData()
                if pid not in self.figure:
                    QMessageBox.warning(window, "Error", "Selected plot not found!")
                    return

                ax = self.figure[pid]["ax"]
                canvas = self.plot_customization[pid]["canvas"]

                fit_line, = ax.plot(np.linspace(x_start, x_end, 500), y_model, linestyle="--", color="red", label="fit")
                fit_line.set_gid("fit")
                ax.legend()
                canvas.draw_idle()

            except Exception as e:
                QMessageBox.critical(window, "Error", f"Fit failed:\n{e}")

        fit_button = QPushButton("Run Fit")
        fit_button.clicked.connect(perform_fit)
        param_layout.addWidget(fit_button, 7, 0, 1, 2, alignment=Qt.AlignCenter)

        # Show the fitting window as a subwindow
        sub = QMdiSubWindow()
        sub.setWidget(window)
        sub.setWindowTitle("Quick Curve Fitting")
        sub.resize(550, 300)
        self.mdi_area.addSubWindow(sub)
        sub.show()


    
    def to_session_data(self):
        ''' Function to store all information needed to restore the worksheet session.
        '''
        # Current geometry of the worksheet window
        ws_geom = {
            "x": self.x(),
            "y": self.y(),
            "width":  self.width(),
            "height": self.height(),
            "minimized": self.isMinimized()
        }


        # Retrieve geometry of all plot windows
        for pid, sub in list(self.plot_subwindows.items()):
            if sub is None:
                continue
            geom = sub.geometry()
            if pid not in self.plots:
                continue
            self.plots[pid]["geometry"] = {
                "x": geom.x(),
                "y": geom.y(),
                "width": geom.width(),
                "height": geom.height(),
                "minimized": sub.isMinimized()
            }

        
        # Extract only the serializable part of customizations
        customizations_serializable = {}
        for pid, info in self.plot_customization.items():
            customizations_serializable[pid] = info.get("customizations", {})

        return {
            "name":           self.name,
            "data":           self.to_dataframe(),
            "geometry":       ws_geom,
            "plots":          self.plots,
            "customizations": customizations_serializable
        }


    def from_session_data(self, data_dict):
        ''' Function to restore the worksheet from saved session data.
        '''
        df = data_dict.get("data")
        if df is not None:
            self.table.setRowCount(len(df))
            self.table.setColumnCount(len(df.columns))
            self.table.setHorizontalHeaderLabels([str(c) for c in df.columns])
            for r in range(len(df)):
                # Counter to check an empty row
                count = 0
                for c in range(len(df.columns)):
                    val = df.iat[r, c]
                    if pd.isna(val):
                        item = QTableWidgetItem("")
                        count += 1
                    else:
                        item = QTableWidgetItem(str(val))
                    self.table.setItem(r, c, item)
                if count == len(df.columns):
                    # All empty, remove the row
                    self.table.removeRow(r)

        # Sync with central data model BEFORE recreating plots
        if self.app_instance and hasattr(self.app_instance, "worksheet_dfs"):
            self.app_instance.worksheet_dfs.add(self.name, df)

        # Restore worksheet geometry: apply move/resize after being added to MDI
        geom = data_dict.get("geometry")
        if geom:
            # Ensure no special window states interfere
            self.setWindowState(Qt.WindowNoState)
            # Move/resize while hidden or already in MDI; if needed, delay minimize
            self.move(geom["x"], geom["y"])
            self.resize(geom["width"], geom["height"])
            if geom.get("minimized"):
                QTimer.singleShot(0, self.showMinimized)
            else:
                # Ensure it's visible in normal state
                QTimer.singleShot(0, self.showNormal)

        # Recreate plots (do not show immediately; set geometry then show)
        plots_dict = data_dict.get("plots", {}) or {}
        
        # Sort by numeric plot id if possible
        def keyf(k):
            try:
                return int(k)
            except:
                return k
        
        for plot_id in sorted(plots_dict.keys(), key=keyf):
            plot_info  = plots_dict[plot_id]
            selections = plot_info.get("selections", [])
            if not selections:
                continue

            # Create sub but don't show it yet
            cst = data_dict.get("customizations", {}).get(plot_id, {})
            sub = self.open_plot_window(
                selections, show=False,
                plot_id=int(plot_id),
                customizations=cst
            )


            # Apply geometry (do this before showing to avoid MDI cascading override)
            pgeom = plot_info.get("geometry")
            if pgeom and sub:
                def apply_geom_and_show(sub=sub, pgeom=pgeom):
                    try:
                        sub.setWindowState(Qt.WindowNoState)
                        sub.setGeometry(pgeom["x"], pgeom["y"], pgeom["width"], pgeom["height"])
                        if pgeom.get("minimized"):
                            sub.showMinimized()
                        else:
                            sub.showNormal()
                    except Exception:
                        # fallback: show normally
                        sub.show()
                # Schedule after event loop to be sure MDI is ready
                QTimer.singleShot(0, apply_geom_and_show)
            else:
                # If no geom info, just show it
                QTimer.singleShot(0, sub.show)
