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
Code for the worksheet's windows.
"""

from PyQt5.QtWidgets import (
    QLineEdit, QWidget, QVBoxLayout, QPushButton, 
    QHBoxLayout, QDialog, QLabel, QComboBox,
    QDialogButtonBox, QStackedWidget
)


class ColumnSelectionDialog(QDialog):
    '''
    Dialog for selecting columns to plot.
    '''
    def __init__(self, columns, parent=None):
        '''
        Initialize the column selection dialog.

        Parameters
        ----------
        columns : list of str
            List of column names available for selection.
        parent : QWidget, optional
            The parent widget (default is None).
        '''
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
    ''' Dialog for performing arithmetic operations between columns.
    '''
    def __init__(self, columns, parent=None):
        '''
        Initialize the column math dialog.

        Parameters
        ----------
        columns : list of str
            List of column names available for selection.
        parent : QWidget, optional
            The parent widget (default is None).
        '''
        super().__init__(parent)
        self.setWindowTitle("Column Math")

        self.mode = QComboBox()
        self.mode.addItems([
            "Arithmetic between columns",
            "Generate linspace",
            "Generate logspace",
            "Generate function from linspace/logspace"
        ])

        # Create the stcack area for dynamic widgets
        self.stack = QStackedWidget()
        self.pages = {
            "Arithmetic between columns": self.create_arithmetic_page(columns),
            "Generate linspace": self.create_space_page(),
            "Generate logspace": self.create_space_page(),
            "Generate function from linspace/logspace": self.create_function_page()
        }

        # Add pages to stack
        for page in self.pages.values():
            self.stack.addWidget(page)
        
        # Name new column
        self.new_name = QLineEdit()
        self.new_name.setPlaceholderText("New column name")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Mode:"))
        layout.addWidget(self.mode)
        layout.addWidget(self.stack)
        layout.addWidget(QLabel("New column name:"))
        layout.addWidget(self.new_name)

        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self.setLayout(layout)

        # Connections
        self.mode.currentTextChanged.connect(self.switch_page)

    def switch_page(self, mode):
        '''
        Switch the displayed page based on selected mode.

        Parameters
        ----------
        mode : str
            The selected mode.
        '''
        self.stack.setCurrentWidget(self.pages[mode])

    def create_arithmetic_page(self, columns):
        '''
        Create the page for arithmetic operations between columns.

        Parameters
        ----------
        columns : list of str
            List of column names available for selection.
        
        Returns
        -------
        QWidget
            The created page widget.
        '''
        page   = QWidget()
        layout = QVBoxLayout(page)

        self.col_a         = QComboBox(); self.col_a.addItems(columns)
        self.op            = QComboBox(); self.op.addItems(["+", "-", "*", "/", "mean"])
        self.col_b         = QComboBox(); self.col_b.addItems(["<Constant>"] + list(columns))
        self.constant_edit = QLineEdit(); self.constant_edit.setPlaceholderText("Constant value")
        self.col_b.currentTextChanged.connect(self.toggle_constant)

        layout.addWidget(QLabel("Column A:")); layout.addWidget(self.col_a)
        layout.addWidget(QLabel("Operation:")); layout.addWidget(self.op)
        layout.addWidget(QLabel("Column B or constant:"))
        layout.addWidget(self.col_b); layout.addWidget(self.constant_edit)
        return page
    
    def create_space_page(self):
        '''
        Create the page for generating linspace or logspace.
        
        Returns
        -------
        QWidget
            The created page widget.
        '''
        page   = QWidget()
        layout = QVBoxLayout(page)

        self.start_edit = QLineEdit(); self.start_edit.setPlaceholderText("Start value")
        self.stop_edit  = QLineEdit(); self.stop_edit.setPlaceholderText("Stop value")
        self.num_edit   = QLineEdit(); self.num_edit.setPlaceholderText("Number of points")

        layout.addWidget(QLabel("Start:")); layout.addWidget(self.start_edit)
        layout.addWidget(QLabel("Stop:")); layout.addWidget(self.stop_edit)
        layout.addWidget(QLabel("Number of points:")); layout.addWidget(self.num_edit)
        return page
    
    def create_function_page(self):
        '''
        Create the page for generating a function from linspace/logspace.

        Returns
        -------
        QWidget
            The created page widget.
        '''
        page   = QWidget()
        layout = QVBoxLayout(page)

        self.space_type = QComboBox()
        self.space_type.addItems(["linspace", "logspace"])

        self.start_edit = QLineEdit(); self.start_edit.setPlaceholderText("Start value")
        self.stop_edit  = QLineEdit(); self.stop_edit.setPlaceholderText("Stop value")
        self.num_edit   = QLineEdit(); self.num_edit.setPlaceholderText("Number of points")
        self.func_edit  = QLineEdit(); self.func_edit.setPlaceholderText("Must be numpy function, e.g. np.sin(x)")

        for label, widget in [
            ("Space type:", self.space_type),
            ("Start:", self.start_edit),
            ("Stop:", self.stop_edit),
            ("Number of points:", self.num_edit),
            ("Function f(x):", self.func_edit)
        ]:
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)

        return page
        
    def toggle_constant(self, text):
        '''
        Enable/disable constant input based on selection.

        Parameters
        ----------
        text : str
            The current text of the col_b combo box.
        '''
        self.constant_edit.setEnabled(text == "<Constant>")

    def get_selection(self):
        '''
        Get the selected columns, operation, constant, and new column name.
        
        Returns
        -------
        dict
            A dictionary with keys:
            - mode: selected mode
            - col_a: first column
            - op: operation
            - col_b: second column or None
            - const: constant value or None
            - space_type: linspace or logspace
            - start: start value for linspace/logspace
            - stop: stop value for linspace/logspace
            - num: number of points for linspace/logspace
            - func: function for generating new column
            - new_name: name of the new column
        '''
        mode = self.mode.currentText()
        return {
            "mode":       mode,
            "col_a":      getattr(self, "col_a", None).currentText() if hasattr(self, "col_a") else None,
            "op":         getattr(self, "op", None).currentText() if hasattr(self, "op") else None,
            "col_b":      None if not hasattr(self, "col_b") or self.col_b.currentText() == "<Constant>" else self.col_b.currentText(),
            "const":      self.constant_edit.text() if hasattr(self, "constant_edit") else "",
            "space_type": self.space_type.currentText() if hasattr(self, "space_type") else "linspace",
            "start":      self.start_edit.text() if hasattr(self, "start_edit") else "",
            "stop":       self.stop_edit.text() if hasattr(self, "stop_edit") else "",
            "num":        self.num_edit.text() if hasattr(self, "num_edit") else "",
            "func":       self.func_edit.text().strip() if hasattr(self, "func_edit") else "",
            "new_name":   self.new_name.text().strip()
        }