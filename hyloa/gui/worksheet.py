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

from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QMdiSubWindow, QLineEdit,
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QDialog, QLabel, QComboBox,
    QDialogButtonBox, QInputDialog, QAction, QApplication,
    QFormLayout, QTextEdit, QSizePolicy, QCheckBox 
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from matplotlib.figure import Figure
from matplotlib import colors as mcolors, markers, lines as mlines


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

        # Enable copy/paste functionality with ctrl+c / ctrl+v
        self.table.setContextMenuPolicy(Qt.ActionsContextMenu)

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

        self.btn_add_col    = QPushButton("Add column")
        self.btn_rmv_col    = QPushButton("Remove column")
        self.btn_load       = QPushButton("Load Data")
        self.btn_plot       = QPushButton("Create Plot")
        self.btn_math       = QPushButton("Column Math")
        self.btn_custom     = QPushButton("Customization")
        self.btn_fit        = QPushButton("Fit Data")
        self.btn_appearance = QPushButton("Appearance")



        btn_layout_top = QHBoxLayout()
        btn_layout_bot = QHBoxLayout()

        btn_layout_top.addWidget(self.btn_add_col)
        btn_layout_top.addWidget(self.btn_rmv_col)
        btn_layout_top.addWidget(self.btn_load)
        btn_layout_top.addWidget(self.btn_math)

        btn_layout_bot.addWidget(self.btn_plot)
        btn_layout_bot.addWidget(self.btn_custom)
        btn_layout_bot.addWidget(self.btn_fit)
        btn_layout_bot.addWidget(self.btn_appearance)
        
        layout = QVBoxLayout()
        layout.addLayout(btn_layout_top)
        layout.addLayout(btn_layout_bot)
        layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(layout)
        self.setWidget(container)

        # Connect button actions
        self.btn_plot.clicked.connect(self.create_plot)
        self.btn_add_col.clicked.connect(self.add_column)
        self.btn_rmv_col.clicked.connect(self.remove_column)
        self.btn_load.clicked.connect(self.load_file_into_table)
        self.btn_math.clicked.connect(self.open_math_dialog)
        self.btn_custom.clicked.connect(self.customize_plot)
        self.btn_fit.clicked.connect(self.open_curve_fitting_window)
        self.btn_appearance.clicked.connect(self.customize_plot_appearance)


        # Attributes to memorize plot windows
        self.plots              = {}   # {int: {"x":..., "y":..., "x_err":..., "y_err":..., "geom":...}}
        self.plot_count         = 0    # to assign unique plot IDs
        self.plot_subwindows    = {}   # {int: QMdiSubWindow}
        self._plot_widgets      = {}   # {plot_id: {"sub": sub, "container": widget, "canvas": canvas, "toolbar": toolbar}}
        self.figure             = {}   # {plot_id: {"figure": Figure, "ax": Axes,}
        self.plot_customization = {}   # {"figure":..., "ax":..., "canvas":..., "customizations": {...}}

    
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
        except Exception as e:
            print(f"[DEBUG] Error during worksheet cleanup: {e}")

        super().closeEvent(event)

    def copy_selection(self):
        ''' Copy selected cells to clipboard in tab-delimited format.
        '''
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
        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(copied))
    
    def paste_selection(self):
        ''' Paste tab-delimited data from clipboard into the table starting at current cell.
        '''
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            return

        rows = text.split("\n")
        start = self.table.currentRow(), self.table.currentColumn()

        for i, row in enumerate(rows):
            cells = row.split("\t")
            for j, cell in enumerate(cells):
                r = start[0] + i
                c = start[1] + j
                # Expand table if needed
                if r >= self.table.rowCount():
                    self.table.insertRow(self.table.rowCount())
                if c >= self.table.columnCount():
                    self.table.insertColumn(self.table.columnCount())
                self.table.setItem(r, c, QTableWidgetItem(cell))


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
                    val = df.iat[r, c]
                    if pd.isna(val):
                        item = QTableWidgetItem("")
                    else:
                        item = QTableWidgetItem(str(val))
                    self.table.setItem(r, c, item)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error in loading file:\n{e}")


    def add_column(self):
        """ Add a new empty column to the table.
        """
        col_count = self.table.columnCount()
        self.table.insertColumn(col_count)
        self.table.setHorizontalHeaderItem(col_count, QTableWidgetItem(f"Col {col_count+1}"))

    def remove_column(self):
        """ Remove the currently selected column(s) from the table.
        """
        selected = self.table.selectionModel().selectedColumns()
        if not selected:
            return  # Nothing selected to remove so return
        
        # Remove columns in reverse order to avoid index shifting
        for col in sorted([c.column() for c in selected], reverse=True):
            self.table.removeColumn(col)

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

    def edit_column_name(self, index):
        """
        Open a dialog to edit the name of the column at the given index.

        Parameters
        ----------
        index : int
            The index of the column to rename.
        """
        current_name = self.table.horizontalHeaderItem(index).text()
        new_name, ok = QInputDialog.getText(
            self, "Rename column", "New column name:", text=current_name
        )
        if ok and new_name.strip():
            self.table.setHorizontalHeaderItem(index, QTableWidgetItem(new_name.strip()))



    def to_dataframe(self):
        """
        Convert the table contents to a pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the numeric values from the table.
            Non-numeric values are replaced with an empty string.
        """
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        data = {}

        for c in range(cols):
            col_name = self.table.horizontalHeaderItem(c).text()
            values = []
            for r in range(rows):
                item = self.table.item(r, c)
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
        """ Open a dialog to perform arithmetic operations between columns.
        """
        columns = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
        if not columns:
            return

        dlg = ColumnMathDialog(columns, self)
        if dlg.exec_() != QDialog.Accepted:
            return

        col_a, op, col_b, const_str, new_name = dlg.get_selection()
        if not new_name:
            QMessageBox.warning(self, "Error", "Please enter a name for the new column.")
            return

        df = self.to_dataframe()

        try:
            if col_b:
                series_b = df[col_b].astype(float)
            else:
                const    = float(const_str)
                series_b = const

            series_a = df[col_a].astype(float)

            if op == "+":
                result = series_a + series_b
            elif op == "-":
                result = series_a - series_b
            elif op == "*":
                result = series_a * series_b
            elif op == "/":
                result = series_a / series_b
            elif op == "mean":
                result = (series_a + series_b) / 2.
            else:
                raise ValueError("Unknown operation")

            # Add new column to the table
            new_col_index = self.table.columnCount()
            self.table.insertColumn(new_col_index)
            self.table.setHorizontalHeaderItem(new_col_index, QTableWidgetItem(new_name))
            for r, val in enumerate(result):
                if pd.notna(val):
                    self.table.setItem(r, new_col_index, QTableWidgetItem(str(val)))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Operation failed:\n{e}")


    def create_plot(self):
        """
        Open a dialog to select columns and create a plot.

        The user chooses X, Y, and optionally error bar columns.
        """
        df = self.to_dataframe()
        dialog = ColumnSelectionDialog(df.columns, self)
        if dialog.exec_() == QDialog.Accepted:
            selections = dialog.get_selection()
            self.open_plot_window(df, selections)


    def open_plot_window(self, df, selections, show=True, plot_id=None, customizations=None):
        """
        Open a new subwindow with a plot of the selected columns.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame containing the data.
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
        """
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)

        for i, sel in enumerate(selections, start=1):
            x = df[sel["x"]].values
            y = df[sel["y"]].values
            xerr = df[sel["x_err"]].values if sel["x_err"] else None
            yerr = df[sel["y_err"]].values if sel["y_err"] else None

            label = sel["y"] if len(selections) == 1 else f"{sel['y']}"

            if xerr is not None or yerr is not None:
                ax.errorbar(x, y, xerr=xerr, yerr=yerr, fmt="o-", label=label)
            else:
                ax.plot(x, y, "o-", label=label)

        
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

                    if color:     line.set_color(color)
                    if marker:    line.set_marker(marker)
                    if linestyle: line.set_linestyle(linestyle)
                    if label:     line.set_label(label)

                except Exception:
                    continue

            ax.legend()
            fig.canvas.draw_idle()

        # Store customization settings
        self.plot_customization[plot_id] = customizations or {}

        ax.set_xlabel(selections[0]["x"]) 
        ax.set_ylabel("Values")
        ax.legend()
        ax.grid(True)

        canvas = FigureCanvas(fig)
        plot_container = QWidget()
        vlayout = QVBoxLayout(plot_container)
        vlayout.setContentsMargins(0, 0, 0, 0)

        toolbar = NavigationToolbar(canvas, plot_container)
        vlayout.addWidget(toolbar)
        vlayout.addWidget(canvas)
        plot_container.setLayout(vlayout)

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
        sub.setWindowTitle(f"From {self.name} plot {plot_id}")
        sub.setWidget(plot_container)
        self.mdi_area.addSubWindow(sub)

        self._plot_widgets[plot_id] = {
            "sub": sub,
            "container": plot_container,
            "canvas": canvas,
            "toolbar": toolbar
        }

        self.figure[plot_id]             = {"figure": fig, "ax": ax, "sub": sub}
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

        return sub
    
    def customize_plot(self):
        """
        Open a dialog to customize plot styles (color, marker, linestyle, label).
        """
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

                self.plot_customization[pid]["customizations"][line_idx] = {
                    "color":     color,
                    "marker":    marker,
                    "linestyle": linestyle,
                    "label":     legend_label,
                }

                ax.legend()
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
        layout = QHBoxLayout(window)
        window.setLayout(layout)

        # === Left column: select data and plot ===
        selection_layout = QVBoxLayout()
        layout.addLayout(selection_layout)

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
        selection_layout.addWidget(help_button, alignment=Qt.AlignLeft)

        # Select target plot
        selection_layout.addWidget(QLabel("Select target plot:"))
        plot_combo = QComboBox()
        for pid, info in self.figure.items():
            sub_title = info["sub"].windowTitle()
            plot_combo.addItem(f"Plot {pid}: {sub_title}", pid)
        selection_layout.addWidget(plot_combo)

        # Select X and Y columns
        selection_layout.addWidget(QLabel("Column X:"))
        x_combo = QComboBox(); x_combo.addItems(df.columns)
        selection_layout.addWidget(x_combo)

        selection_layout.addWidget(QLabel("Column Y:"))
        y_combo = QComboBox(); y_combo.addItems(df.columns)
        selection_layout.addWidget(y_combo)

        # === Right column fit parameter ===
        param_layout = QVBoxLayout()
        layout.addLayout(param_layout)

        param_layout.addWidget(QLabel("x_start:"))
        x_start_edit = QLineEdit(str(df[x_combo.currentText()].min()))
        param_layout.addWidget(x_start_edit)

        param_layout.addWidget(QLabel("x_end:"))
        x_end_edit = QLineEdit(str(df[x_combo.currentText()].max()))
        param_layout.addWidget(x_end_edit)

        param_layout.addWidget(QLabel("Parameter names (e.g. a,b):"))
        param_names_edit = QLineEdit("a,b")
        param_layout.addWidget(param_names_edit)

        param_layout.addWidget(QLabel("Initial values (e.g. 1,1):"))
        initial_params_edit = QLineEdit("1,1")
        param_layout.addWidget(initial_params_edit)

        param_layout.addWidget(QLabel("Fitting function (e.g. a*x + b):"))
        function_edit = QLineEdit("a*x + b")
        param_layout.addWidget(function_edit)

        # Output 
        output_box = QTextEdit()
        output_box.setReadOnly(True)
        output_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(output_box)

        def perform_fit():
            ''' Perform the curve fitting and update the plot.
            '''
            try:
                # Retrieve data and parameters
                x = df[x_combo.currentText()].astype(float).values
                y = df[y_combo.currentText()].astype(float).values

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
                    lines.append(f"{p} = {val:.3e} ± {err:.3e}")
                result_text = "\n".join(lines)
                output_box.setPlainText(result_text)

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
        param_layout.addWidget(fit_button)

        # Show the fitting window as a subwindow
        sub = QMdiSubWindow()
        sub.setWidget(window)
        sub.setWindowTitle("Quick Curve Fitting")
        sub.resize(700, 350)
        self.mdi_area.addSubWindow(sub)
        sub.show()


    
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
                df, selections, show=False,
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

#===========================================================================================#
#===========================================================================================#
#===========================================================================================#


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

        self.columns = columns
        self.curve_rows = []

        self.layout = QVBoxLayout()

        # Area for curve selections
        self.curves_layout = QVBoxLayout()
        self.layout.addLayout(self.curves_layout)

        # Button to add more curves
        btn_add = QPushButton("Add curve")
        btn_add.clicked.connect(self.add_curve_row)
        self.layout.addWidget(btn_add)

        # OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

        self.setLayout(self.layout)

        # Add the first curve selection row
        self.add_curve_row()
    
    def add_curve_row(self):
        ''' Add a new row for selecting X, Y, Xerr, Yerr columns.
        '''
        row_layout = QHBoxLayout()

        x_combo = QComboBox(); x_combo.addItems(self.columns)
        y_combo = QComboBox(); y_combo.addItems(self.columns)

        xerr_combo = QComboBox(); xerr_combo.addItem("None"); xerr_combo.addItems(self.columns)
        yerr_combo = QComboBox(); yerr_combo.addItem("None"); yerr_combo.addItems(self.columns)

        row_layout.addWidget(QLabel("X:")); row_layout.addWidget(x_combo)
        row_layout.addWidget(QLabel("Y:")); row_layout.addWidget(y_combo)
        row_layout.addWidget(QLabel("Xerr:")); row_layout.addWidget(xerr_combo)
        row_layout.addWidget(QLabel("Yerr:")); row_layout.addWidget(yerr_combo)

        self.curves_layout.addLayout(row_layout)
        self.curve_rows.append((x_combo, y_combo, xerr_combo, yerr_combo))


    def get_selection(self):
        ''' Get the list of selected columns for all curves.
        '''
        selections = []
        for x_combo, y_combo, xerr_combo, yerr_combo in self.curve_rows:
            x = x_combo.currentText()
            y = y_combo.currentText()
            x_err = xerr_combo.currentText()
            y_err = yerr_combo.currentText()

            selections.append({
                "x": x,
                "y": y,
                "x_err": None if x_err == "None" else x_err,
                "y_err": None if y_err == "None" else y_err,
            })
        return selections

#===========================================================================================#
#===========================================================================================#
#===========================================================================================#

class ColumnMathDialog(QDialog):
    """ Dialog for performing arithmetic operations between columns.
    """
    def __init__(self, columns, parent=None):
        """
        Initialize the column math dialog.

        Parameters
        ----------
        columns : list of str
            List of column names available for selection.
        parent : QWidget, optional
            The parent widget (default is None).
        """
        super().__init__(parent)
        self.setWindowTitle("Column Math")

        self.col_a = QComboBox(); self.col_a.addItems(columns)
        self.col_b = QComboBox(); self.col_b.addItems(["<Constant>"] + list(columns))
        self.constant_edit = QLineEdit(); self.constant_edit.setPlaceholderText("Constant value")

        self.op       = QComboBox(); self.op.addItems(["+", "-", "*", "/", "mean"])
        self.new_name = QLineEdit(); self.new_name.setPlaceholderText("New column name")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Column A:")) ; layout.addWidget(self.col_a)
        layout.addWidget(QLabel("Operation:")); layout.addWidget(self.op)
        layout.addWidget(QLabel("Column B or constant:")); layout.addWidget(self.col_b)
        layout.addWidget(self.constant_edit)
        layout.addWidget(QLabel("New column name:")); layout.addWidget(self.new_name)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        
        self.setLayout(layout)

        self.col_b.currentTextChanged.connect(self._toggle_constant)

    def _toggle_constant(self, text):
        """ 
        Enable/disable constant input based on selection.

        Parameters
        ----------
        text : str
            The current text of the col_b combo box.
        """
        self.constant_edit.setEnabled(text == "<Constant>")

    def get_selection(self):
        """
        Get the selected columns, operation, constant, and new column name.
        
        Returns
        -------
        tuple
            (col_a, operation, col_b or None, constant or None, new_name)
        """
        return (
            self.col_a.currentText(),
            self.op.currentText(),
            None if self.col_b.currentText() == "<Constant>" else self.col_b.currentText(),
            self.constant_edit.text(),
            self.new_name.text().strip()
        )
