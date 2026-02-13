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
    QFrame, QDialog, QLabel, QComboBox, QGridLayout,
    QDialogButtonBox, QStackedWidget, QScrollArea,
    QHBoxLayout, QGroupBox, QFormLayout
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
        self.setMinimumWidth(500)

        self.columns = columns
        self.curve_rows = []

        main_layout = QVBoxLayout(self)

        # Create a scroll area for curve selections
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.scroll_widget = QWidget()
        self.curves_layout = QVBoxLayout(self.scroll_widget)
        self.curves_layout.setSpacing(10)

        self.scroll_area.setWidget(self.scroll_widget)
        main_layout.addWidget(self.scroll_area)

        # Button to add more curves
        btn_add = QPushButton("Add curve")
        btn_add.clicked.connect(self.add_curve_row)
        main_layout.addWidget(btn_add)

        # OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        # Add the first curve selection row
        self.add_curve_row()
    
    def add_curve_row(self):
        ''' Add a new row for selecting X, Y, Xerr, Yerr columns.
        '''
        curve_index = len(self.curve_rows) + 1

         # === Main container for one curve ===
        container = QFrame()
        container.setFrameShape(QFrame.StyledPanel)

        container_layout = QVBoxLayout(container)

        # ---- Header row (Curve X + Remove button) ----
        header_layout = QHBoxLayout()

        title_label = QLabel(f"Curve {curve_index}")
        title_label.setStyleSheet("font-weight: bold;")

        remove_btn = QPushButton("Remove")
        remove_btn.setMaximumWidth(80)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(remove_btn)

        container_layout.addLayout(header_layout)

        grid  = QGridLayout()

        x_combo = QComboBox(); x_combo.addItems(self.columns)
        y_combo = QComboBox(); y_combo.addItems(self.columns)

        xerr_combo = QComboBox(); xerr_combo.addItem("None"); xerr_combo.addItems(self.columns)
        yerr_combo = QComboBox(); yerr_combo.addItem("None"); yerr_combo.addItems(self.columns)

        # Layout grid (clean and aligned)
        grid.addWidget(QLabel("x:"),     0, 0)
        grid.addWidget(x_combo,          0, 1)

        grid.addWidget(QLabel("y:"),     1, 0)
        grid.addWidget(y_combo,          1, 1)

        grid.addWidget(QLabel("xerr:"),  0, 2)
        grid.addWidget(xerr_combo,       0, 3)

        grid.addWidget(QLabel("yerr:"),  1, 2)
        grid.addWidget(yerr_combo,       1, 3)

        container_layout.addLayout(grid)
        self.curves_layout.addWidget(container)

        remove_btn.clicked.connect(
            lambda: self.remove_curve(container)
        )

        self.curve_rows.append({
            "container" : container,
            "title"     : title_label,
            "x"         : x_combo,
            "y"         : y_combo,
            "xerr"      : xerr_combo,
            "yerr"      : yerr_combo
        })

    def remove_curve(self, container):
        '''Remove a curve container.'''

        # Remove from layout
        container.setParent(None)
        container.deleteLater()

        # Remove from internal list
        self.curve_rows = [
            row for row in self.curve_rows
            if row["container"] != container
        ]

        # Renumber remaining curves
        for i, row in enumerate(self.curve_rows):
            row["title"].setText(f"Curve {i+1}")

    def get_selection(self):
        ''' 
        Get the list of selected columns for all curves.

        Return
        ------
        selections : list
            A list of dictionaries, each containing:
            - x: selected X column
            - y: selected Y column
            - x_err: selected X error column or None 
        '''
        selections = []
        
        for row in self.curve_rows:

            x = row["x"].currentText()
            y = row["y"].currentText()

            x_err = row["xerr"].currentText()
            y_err = row["yerr"].currentText()

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

        main_layout = QVBoxLayout(self)

        # Mode selection
        mode_group  = QGroupBox("Operation mode")
        mode_layout = QVBoxLayout()
        self.mode   = QComboBox()
        self.mode.addItems([
            "Arithmetic between columns",
            "Custom expression between columns",
            "Generate linspace",
            "Generate logspace",
            "Generate function from linspace/logspace"
        ])
        mode_layout.addWidget(self.mode)
        mode_group.setLayout(mode_layout)
        main_layout.addWidget(mode_group)


        # Create the stcack area for dynamic widgets
        self.stack = QStackedWidget()
        self.pages = {
            "Arithmetic between columns": self.create_arithmetic_page(columns),
            "Custom expression between columns": self.create_expression_page(columns),
            "Generate linspace": self.create_space_page(),
            "Generate logspace": self.create_space_page(),
            "Generate function from linspace/logspace": self.create_function_page()
        }

        # Add pages to stack
        for page in self.pages.values():
            self.stack.addWidget(page)
        
        content_group  = QGroupBox("Parameters")
        content_layout = QVBoxLayout()
        content_layout.addWidget(self.stack)
        content_group.setLayout(content_layout)

        main_layout.addWidget(content_group)
        
        # Name new column
        name_layout   = QFormLayout()
        self.new_name = QLineEdit()
        self.new_name.setPlaceholderText("New column name")
        name_layout.addRow("New column name:", self.new_name)
        main_layout.addLayout(name_layout)

        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)

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
        page = QWidget()
        form = QFormLayout(page)

        self.col_a         = QComboBox(); self.col_a.addItems(columns)
        self.op            = QComboBox(); self.op.addItems(["+", "-", "*", "/", "mean"])
        self.col_b         = QComboBox(); self.col_b.addItems(["<Constant>"] + list(columns))
        self.constant_edit = QLineEdit(); self.constant_edit.setPlaceholderText("Constant value")
        self.col_b.currentTextChanged.connect(self.toggle_constant)

        form.addRow("Column A:", self.col_a)
        form.addRow("Operation:", self.op)
        form.addRow("Column B:", self.col_b)
        form.addRow("Constant:", self.constant_edit)
        return page
    
    def create_expression_page(self, columns):

        page = QWidget()
        form = QFormLayout(page)

        info = QLabel(
            "Write a numpy-compatible expression.\n"
            "Available variables: " + ", ".join(columns)
        )
        info.setWordWrap(True)

        self.expr_edit = QLineEdit()
        self.expr_edit.setPlaceholderText(
            "(col1 - col2) / col3"
        )

        form.addRow(info)
        form.addRow("Expression:", self.expr_edit)

        return page
    
    def create_space_page(self):
        '''
        Create the page for generating linspace or logspace.
        
        Returns
        -------
        QWidget
            The created page widget.
        '''
        page = QWidget()
        form = QFormLayout(page)

        self.start_edit = QLineEdit(); self.start_edit.setPlaceholderText("Start value")
        self.stop_edit  = QLineEdit(); self.stop_edit.setPlaceholderText("Stop value")
        self.num_edit   = QLineEdit(); self.num_edit.setPlaceholderText("Number of points")

        form.addRow("Start:", self.start_edit)
        form.addRow("Stop:", self.stop_edit)
        form.addRow("Number of points:", self.num_edit)
        
        return page
    
    def create_function_page(self):
        '''
        Create the page for generating a function from linspace/logspace.

        Returns
        -------
        QWidget
            The created page widget.
        '''
        page = QWidget()
        form = QFormLayout(page)

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
            ("Function f(x):", self.func_edit)]:

            form.addRow(label, widget)

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
            "expr":       self.expr_edit.text().strip() if hasattr(self, "expr_edit") else "",
            "space_type": self.space_type.currentText() if hasattr(self, "space_type") else "linspace",
            "start":      self.start_edit.text() if hasattr(self, "start_edit") else "",
            "stop":       self.stop_edit.text() if hasattr(self, "stop_edit") else "",
            "num":        self.num_edit.text() if hasattr(self, "num_edit") else "",
            "func":       self.func_edit.text().strip() if hasattr(self, "func_edit") else "",
            "new_name":   self.new_name.text().strip()
        }