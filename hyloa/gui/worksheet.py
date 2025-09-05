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

        
from PyQt5.QtCore import QTimer, Qt

from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QMdiSubWindow,
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QDialog, QLabel, QComboBox, QDialogButtonBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from hyloa.data.io import detect_header_length

class WorksheetWindow(QMdiSubWindow):
    """ A worksheet subwindow for managing tabular data and plotting.
    """
    def __init__(self, mdi_area, parent=None, name="worksheet"):
        """
        Initialize the worksheet window.

        Parameters
        ----------
        mdi_area : QMdiArea
            The main MDI area where this window will be added.
        parent : QWidget, optional
            The parent widget (default is None).
        name : str, optional
            Name of the worksheet (default is "worksheet").
        """
        super().__init__(parent)
        self.mdi_area = mdi_area
        self.name = name
        self.setWindowTitle(f"Worksheet - {self.name}")
        self.resize(600, 600)

        # Create an initial table with 20 rows and 4 columns
        self.table = QTableWidget(20, 4) 
        self.table.setHorizontalHeaderLabels([f"Col {i+1}" for i in range(4)])
        self.table.cellChanged.connect(self.auto_expand_rows)

        self.btn_add_col = QPushButton("Add column")
        self.btn_load    = QPushButton("Load Data")
        self.btn_plot    = QPushButton("Create Plot")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_add_col)
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_plot)

        layout = QVBoxLayout()
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(layout)
        self.setWidget(container)

        # Connect button actions
        self.btn_plot.clicked.connect(self.create_plot)
        self.btn_add_col.clicked.connect(self.add_column)
        self.btn_load.clicked.connect(self.load_file_into_table)

        # Attributes to memorize plot windows
        self.plots      = {}      # {int: {"x":..., "y":..., "x_err":..., "y_err":..., "geom":...}}
        self.plot_count = 0
        self.plot_subwindows = {} # {int: QMdiSubWindow}


    def load_file_into_table(self):
        """
        Load data from a text file into the table.

        The function automatically detects header rows
        and populates the QTableWidget with the parsed data.
        """
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
            
            # Populate table with data
            for r in range(len(df)):
                for c in range(len(df.columns)):
                    val = str(df.iat[r, c])
                    self.table.setItem(r, c, QTableWidgetItem(val))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error in loading file:\n{e}")


    def add_column(self):
        """ Add a new empty column to the table.
        """
        col_count = self.table.columnCount()
        self.table.insertColumn(col_count)
        self.table.setHorizontalHeaderItem(col_count, QTableWidgetItem(f"Col {col_count+1}"))


    def auto_expand_rows(self, row, col):
        """
        Automatically add a new row if the user edits the last row.

        Parameters
        ----------
        row : int
            The row index that was edited.
        col : int
            The column index that was edited.
        """
        if row == self.table.rowCount() - 1:
            self.table.insertRow(self.table.rowCount())


    def to_dataframe(self):
        """
        Convert the table contents to a pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the numeric values from the table.
            Non-numeric values are replaced with NaN.
        """
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        data = {}

        for c in range(cols):
            col_name = self.table.horizontalHeaderItem(c).text()
            values = []
            for r in range(rows):
                item = self.table.item(r, c)
                try:
                    val = float(item.text()) if item else np.nan
                except:
                    val = np.nan
                values.append(val)
            data[col_name] = values
        return pd.DataFrame(data)


    def create_plot(self):
        """
        Open a dialog to select columns and create a plot.

        The user chooses X, Y, and optionally error bar columns.
        """
        df = self.to_dataframe()
        dialog = ColumnSelectionDialog(df.columns, self)
        if dialog.exec_() == QDialog.Accepted:
            x_col, y_col, y_err_col, x_err_col = dialog.get_selection()
            self.open_plot_window(df, x_col, y_col, y_err_col, x_err_col)


    def open_plot_window(self, df, x_col, y_col, y_err_col=None, x_err_col=None, show=True, plot_id=None):
        """
        Open a new subwindow with a plot of the selected columns.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame containing the data.
        x_col : str
            Column name for X-axis values.
        y_col : str
            Column name for Y-axis values.
        y_err_col : str, optional
            Column name for Y-axis error bars (default is None).
        x_err_col : str, optional
            Column name for X-axis error bars (default is None).
        
        Returns
        -------
        QMdiSubWindow
            The subwindow containing the plot.
        """
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)

        x = df[x_col].values
        y = df[y_col].values

        if y_err_col or x_err_col:
            xerr = df[x_err_col].values if x_err_col else None
            yerr = df[y_err_col].values if y_err_col else None
            ax.errorbar(x, y, xerr=xerr, yerr=yerr, fmt="o", linestyle='--', label=y_col)
        else:
            ax.plot(x, y, "o-", label=y_col)

        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.legend()
        ax.grid(True)

        canvas = FigureCanvas(fig)

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

        sub = QMdiSubWindow()
        sub.setWindowTitle(f"From {self.name} plot {plot_id}: {y_col} vs {x_col}")
        sub.setWidget(canvas)
        self.mdi_area.addSubWindow(sub)
        
        # show only if requested
        if show:
            # show after addSubWindow: the MDI may apply a default cascading; caller can still reposition if desired
            sub.show()


        # Save plot info for session management
        self.plot_subwindows[plot_id] = sub
        self.plots[plot_id] = {
            "x_col": x_col,
            "y_col": y_col,
            "x_err_col": x_err_col,
            "y_err_col": y_err_col,
            "geometry": {
                "x": sub.x(),
                "y": sub.y(),
                "width": sub.width(),
                "height": sub.height(),
                "minimized": sub.isMinimized()
            }
        }

        return sub
    
    def to_session_data(self):
        # Current geometry of the worksheet window
        ws_geom = {
            "x": self.x(),
            "y": self.y(),
            "width":  self.width(),
            "height": self.height(),
            "minimized": self.isMinimized()
        }

        # Retrieve geometry of all plot windows
        for pid, sub in self.plot_subwindows.items():
            if sub is None:
                continue
            self.plots.setdefault(pid, {})
            self.plots[pid]["geometry"] = {
                "x": sub.x(),
                "y": sub.y(),
                "width":  sub.width(),
                "height": sub.height(),
                "minimized": sub.isMinimized()
            }

        return {
            "name": self.name,
            "data": self.to_dataframe(),
            "geometry": ws_geom,
            "plots": self.plots
        }


    def from_session_data(self, data_dict):
        df = data_dict.get("data")
        if df is not None:
            self.table.setRowCount(len(df))
            self.table.setColumnCount(len(df.columns))
            self.table.setHorizontalHeaderLabels([str(c) for c in df.columns])
            for r in range(len(df)):
                for c in range(len(df.columns)):
                    val = str(df.iat[r, c])
                    self.table.setItem(r, c, QTableWidgetItem(val))


        # restore worksheet geometry: apply move/resize after being added to MDI
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
                # ensure it's visible in normal state
                QTimer.singleShot(0, self.showNormal)

        # recreate plots (do not show immediately; set geometry then show)
        plots_dict = data_dict.get("plots", {}) or {}
        # sort by numeric plot id if possible
        def keyf(k):
            try:
                return int(k)
            except:
                return k
        for plot_id in sorted(plots_dict.keys(), key=keyf):
            plot_info = plots_dict[plot_id]
            x_col = plot_info.get("x_col")
            y_col = plot_info.get("y_col")
            x_err = plot_info.get("x_err_col")
            y_err = plot_info.get("y_err_col")

            # create sub but don't show it yet
            sub = self.open_plot_window(df, x_col, y_col, y_err, x_err, show=False, plot_id=int(plot_id))

            # apply geometry (do this before showing to avoid MDI cascading override)
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
                # schedule after event loop to be sure MDI is ready
                QTimer.singleShot(0, apply_geom_and_show)
            else:
                # if no geom info, just show it
                QTimer.singleShot(0, sub.show)


                


class ColumnSelectionDialog(QDialog):
    """
    Dialog for selecting columns to plot.
    """
    def __init__(self, columns, parent=None):
        """
        Initialize the column selection dialog.

        Parameters
        ----------
        columns : list of str
            List of column names available for selection.
        parent : QWidget, optional
            The parent widget (default is None).
        """
        super().__init__(parent)
        self.setWindowTitle("Select columns for Plotting")

        self.x_combo = QComboBox()
        self.x_combo.addItems(columns)

        self.y_combo = QComboBox()
        self.y_combo.addItems(columns)

        self.y_err_combo = QComboBox()
        self.y_err_combo.addItem("None")
        self.y_err_combo.addItems(columns)

        self.x_err_combo = QComboBox()
        self.x_err_combo.addItem("None")
        self.x_err_combo.addItems(columns)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("X axis:"))
        layout.addWidget(self.x_combo)
        layout.addWidget(QLabel("Y axis"))
        layout.addWidget(self.y_combo)
        layout.addWidget(QLabel("Y error (optional):"))
        layout.addWidget(self.y_err_combo)
        layout.addWidget(QLabel("X error (optional):"))
        layout.addWidget(self.x_err_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_selection(self):
        """
        Get the selected columns.

        Returns
        -------
        tuple
            (x, y, y_err, x_err), where `y_err` and `x_err` are None if not selected.
        """
        x     = self.x_combo.currentText()
        y     = self.y_combo.currentText()
        y_err = self.y_err_combo.currentText()
        x_err = self.x_err_combo.currentText()

        return x, y, (None if y_err == "None" else y_err), (None if x_err == "None" else x_err)
