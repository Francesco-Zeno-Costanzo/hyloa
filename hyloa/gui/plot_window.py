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
Code to manage the plot window
"""
import numpy as np
from scipy.special import *
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from matplotlib.figure import Figure
from matplotlib import markers, lines as mlines, colors as mcolors
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QComboBox, QMessageBox, QDialog, QFormLayout,
    QLineEdit, QMdiSubWindow, QTextEdit, QSizePolicy, QFrame,
    QCheckBox, QDialogButtonBox

)

from hyloa.utils.err_format import format_value_error
from hyloa.data.processing import inv_single_branch_dialog
from hyloa.data.processing import inv_x_dialog, inv_y_dialog
from hyloa.data.processing import norm_dialog, close_loop_dialog
from hyloa.gui.correction_window import correct_hysteresis_loop

#==============================================================================================#
# Main class for managing the plot window                                                      #
#==============================================================================================#

class PlotControlWidget(QWidget):
    '''
    Main widget for managing a single plot's interface and user interactions.

    Allows the user to configure and customize data visualization options, including
    selecting datasets, customizing styles, fitting curves, and toggling data visibility.
    '''

    def __init__(self, app_instance, number_plots, plot_name="Graph"):
        '''
        Initialize the plot control widget and build the GUI layout.
        
        Parameters
        ----------
        app_instance : object
            The main application instance that contains shared data and methods.
        number_plots : int
            Index or identifier of the current plot.
        plot_name : str, optional
            The display name of the plot window (default is "Graph").
        '''
        super().__init__()
        
        self.app_instance         = app_instance  # Instance of main app
        self.number_plots         = number_plots  # Index of the plot
        self.plot_customizations  = {}            # Dictionary to save graphic's customization
        self.selected_pairs       = []            # List of plotted data
        # Variables to manage figure
        self.figure               = None         
        self.ax                   = None
        self.canvas               = None
        self.toolbar              = None
        self.plot_name            = plot_name

        self.init_ui()

    def init_ui(self):
        '''
        Construct the user interface for the plot control panel.

        Creates button layouts for plot interaction, including creation, customization,
        and manipulation of data cycles. Also builds a scrollable area to add and manage
        cycle pairs dynamically.
        '''
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Top buttons row
        top_button_layout = QHBoxLayout()
        top_buttons = [
            ("Create plot",   self.plot),
            ("Customization", self.customize_plot_style),
            ("Appearance",    self.customize_plot_appearance),
            ("Curve Fitting", self.curve_fitting),
            ("Normalize",     self.normalize),
        ]
        for text, func in top_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            top_button_layout.addWidget(btn)
        main_layout.addLayout(top_button_layout)

        # Bottom buttons row
        bottom_button_layout = QHBoxLayout()
        bottom_buttons = [
            ("Close loop",   self.close_loop),
            ("Flip x axis",  self.x_inversion),
            ("Flip y axis",  self.y_inversion),
            ("Flip a branch", self.revert_branch),
            ("Correct loop", self.correction)
        ]
        for text, func in bottom_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            bottom_button_layout.addWidget(btn)
        main_layout.addLayout(bottom_button_layout)

        
        main_layout.addWidget(QLabel("Select data, add to or hide cycles:"))
        # Section for adding data
        add_pair_button = QPushButton("Add cycle")
        add_pair_button.clicked.connect(lambda: [self.add_pair(), self.add_pair()])
        # Section for remove data
        remove_cycle_button = QPushButton("Remove last cycle")
        remove_cycle_button.clicked.connect(self.remove_last_cycle)
        # Section for hide data
        toggle_cycle_button = QPushButton("Hide cycle")
        toggle_cycle_button.clicked.connect(self.toggle_cycle_visibility)

        # Row with button
        cycle_buttons_layout = QHBoxLayout()
        cycle_buttons_layout.addWidget(add_pair_button)
        cycle_buttons_layout.addWidget(remove_cycle_button)
        cycle_buttons_layout.addWidget(toggle_cycle_button)
        main_layout.addLayout(cycle_buttons_layout)


        # Scroll area for dynamic pair selection
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.pair_container = QWidget()
        self.pair_layout = QVBoxLayout()
        self.pair_container.setLayout(self.pair_layout)
        self.scroll_area.setWidget(self.pair_container)
        main_layout.addWidget(self.scroll_area)

        # Add first pair
        self.add_pair()
        self.add_pair()

    def add_pair(self, file_text=None, x_col=None, y_col=None):
        '''
        Add a new data pair selector to the interface.

        Each pair consists of a file selection dropdown and corresponding x/y column selectors.
        Optionally pre-selects values for restoring saved sessions.

        Parameters
        ----------
        file_text : str, optional
            The name of the file to be preselected.
        x_col : str, optional
            The x-axis column name to be preselected.
        y_col : str, optional
            The y-axis column name to be preselected.
        '''

        if len(self.selected_pairs) % 2 == 0:
            num   = len(self.selected_pairs) // 2 + 1
            title = QLabel(f"Cycle {num}")
            title.setStyleSheet("font-weight: bold; margin-top: 10px; margin-bottom: 5px;")
            self.pair_layout.addWidget(title)

        
        file_combo = QComboBox()
        file_combo.addItems([f"File {i + 1}" for i in range(len(self.app_instance.dataframes))])

        x_combo = QComboBox()
        y_combo = QComboBox()

        row = QHBoxLayout()

        def update_columns():
            index = file_combo.currentIndex()
            cols = list(self.app_instance.dataframes[index].columns)
            x_combo.clear()
            y_combo.clear()
            x_combo.addItems(cols)
            y_combo.addItems(cols)

            # Selection for loading previous session
            if x_col in cols:
                x_combo.setCurrentText(x_col)
            if y_col in cols:
                y_combo.setCurrentText(y_col)

        file_combo.currentIndexChanged.connect(update_columns)

        # Selection for loading previous session
        if file_text:
            file_combo.setCurrentText(file_text)

        update_columns()

        row.addWidget(QLabel("File:"))
        row.addWidget(file_combo)
        row.addWidget(QLabel("x:"))
        row.addWidget(x_combo)
        row.addWidget(QLabel("y:"))
        row.addWidget(y_combo)

        container = QWidget()
        container.setLayout(row)
        self.pair_layout.addWidget(container)
        self.selected_pairs.append((file_combo, x_combo, y_combo))

        if len(self.selected_pairs) % 2 == 0:
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("margin: 8px 0px;")
            self.pair_layout.addWidget(separator)
    
    def remove_last_cycle(self):
        ''' Remove the last added cycle (pair of file/x/y selectors) from the layout
        '''
        if not self.selected_pairs:
            return
        
        for _ in range(2):
            
            file_combo, _, _ = self.selected_pairs.pop()
            parent_widget = file_combo.parent()  # QWidget that contains the row
            self.pair_layout.removeWidget(parent_widget)
            parent_widget.deleteLater()


        count = self.pair_layout.count()
        if count >= 1:
            last_item = self.pair_layout.itemAt(count - 1).widget()
            if isinstance(last_item, QFrame):
                self.pair_layout.takeAt(count - 1)
                last_item.deleteLater()
                count -= 1

        if count >= 1:
            last_item = self.pair_layout.itemAt(count - 1).widget()
            if isinstance(last_item, QLabel) and last_item.text().startswith("Cycle"):
                self.pair_layout.takeAt(count - 1)
                last_item.deleteLater()



    def toggle_cycle_visibility(self):
        ''' Call function to toggle the visibility of the data
        '''
        cycle_visibility(self, self.number_plots, 
                         self.app_instance.figures_map,
                         self.plot_customizations)

    def plot(self):
        ''' Call function to plot data
        '''
        plot_data(self, self.app_instance)

    def customize_plot_style(self):
        ''' Call function to customizzzation of plots
        '''
        customize_plot_style(self, self.plot_customizations,
                             self.number_plots, self.app_instance.figures_map)
    
    def customize_plot_appearance(self):
        ''' Call function to customize the appearance of the plot window
        '''
        customize_plot_appearance(self)

    def curve_fitting(self):
        ''' Curve fitting window
        '''
        open_curve_fitting_window(self.app_instance, self)
       
    def normalize(self):
        ''' Call function to normalize data
        '''
        norm_dialog(self, self.app_instance)

    def close_loop(self):
        ''' Call function to close loop
        '''
        close_loop_dialog(self, self.app_instance)

    def x_inversion(self):
        ''' Call function to invert x axis
        '''
        inv_x_dialog(self, self.app_instance)

    def y_inversion(self):
        ''' Call function to invert y axis
        '''
        inv_y_dialog(self, self.app_instance)

    def revert_branch(self):
        ''' Call function to revert a branch of a cycle
        '''
        inv_single_branch_dialog(self, self.app_instance)
    
    def correction(self):
        ''' Call function to correct a hysteresis loop
        '''
        correct_hysteresis_loop(self.app_instance)


#==============================================================================================#
# Class to overwrite close event to remove discarded figures                                   #
#==============================================================================================#

class PlotSubWindow(QMdiSubWindow):
    ''' 
    Class to overwrite close event to remove discarded figures
    Associates a plot widget with a subwindow and handles cleanup upon closing by 
    removing internal references to the widget and its figure.
    '''

    def __init__(self, app_instance, plot_widget, plot_id):
        '''
        Parameters
        ----------
        app_instance : MainApp
            Main application instance containing the session data.
        plot_widget : QWidget
            The widget containing the plot to be displayed.
        plot_id : int
            current plot number
        '''
        super().__init__()
        self.app_instance = app_instance
        self.plot_widget  = plot_widget
        self.plot_id      = plot_id
        self.setWidget(plot_widget)
        self.setWindowTitle(f"Control - {plot_widget.plot_name}")
        self.resize(600, 300)

    def closeEvent(self, event):
        '''
        Handle the window close event and remove associated plot references.

        Removes the control widget and its corresponding figure
        from the application's internal mappings.
        Logs the removal of the figure.

        Parameters
        ----------
        event : QCloseEvent
            The close event triggered when the window is closed.
        '''
        # Remove the control widget
        if self.plot_id in self.app_instance.plot_widgets:
            del self.app_instance.plot_widgets[self.plot_id]
            del self.app_instance.plot_names[self.plot_id]

        # Remove the associated figure
        if self.plot_id in self.app_instance.figures_map:
            del self.app_instance.figures_map[self.plot_id]
            self.app_instance.logger.info(f"Figure {self.plot_id} removed from figures_map.")

        event.accept()
        
#==============================================================================================#
# Function that creates the plot with the chosen data                                          #
#==============================================================================================#

def plot_data(plot_window_instance, app_instance):
    '''
    Create the plot with the selected pairs using matplotlib.
   
    Parameters
    ----------
    plot_window_instance : PlotControlWidget
        Instance of the plot control widget containing the selected pairs.
    app_instance : MainApp
        Main application instance containing the session data.
    '''

    # Extracting data from the plot window instance
    selected_pairs      = plot_window_instance.selected_pairs
    number_plots        = plot_window_instance.number_plots
    plot_name           = plot_window_instance.plot_name    
    dataframes          = app_instance.dataframes
    plot_customizations = plot_window_instance.plot_customizations
    logger              = app_instance.logger

    # For Normalization or loop closure
    app_instance.refresh_shell_variables()
    
    # Create a figure
    if plot_window_instance.figure is None:
        fig = Figure(figsize=(10, 6))
        ax  = fig.add_subplot(111)

        # Save objects in the instance
        plot_window_instance.figure = fig
        plot_window_instance.ax     = ax

        app_instance.figures_map[number_plots] = (fig, ax)

        # Create canvas and show in sub-window
        canvas  = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, plot_window_instance)

        # Create layout
        plot_area = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        plot_area.setLayout(layout)

        # Save 
        plot_window_instance.canvas  = canvas
        plot_window_instance.toolbar = toolbar 

        # Sub-window
        sub = QMdiSubWindow()
        sub.setWindowTitle(f"Plot - {plot_name}")
        sub.setWidget(plot_area)
        sub.resize(800, 600)
        app_instance.mdi_area.addSubWindow(sub)
        sub.show()
        # Save for session loading
        app_instance.figure_subwindows[number_plots] = sub


    else:
        # Retrieve existing objects
        fig     = plot_window_instance.figure
        ax      = plot_window_instance.ax
        canvas  = plot_window_instance.canvas
        toolbar = plot_window_instance.toolbar

        # Clear for new plot
        ax.clear()

    try:

        X = []
        Y = []

        for df_choice, x_var, y_var in selected_pairs:
            df_idx = int(df_choice.currentText().split(" ")[1]) - 1 
            x_col = x_var.currentText()
            y_col = y_var.currentText()

            if not x_col or not y_col:
                QMessageBox.critical(None, "Error", "You must select all column pairs!")
                return

            X.append(dataframes[df_idx][x_col].astype(float).values)
            Y.append(dataframes[df_idx][y_col].astype(float).values)
            logger.info(f"Plot of: {x_col} vs {y_col}")

        if not plot_customizations:
            col = plt.cm.jet(np.linspace(0, 1, len(X)))
            for i in range(0, len(X), 2):
                ax.plot(X[i],   Y[i],   color=col[i], marker=".", label=f"Cycle {i//2 + 1}")
                ax.plot(X[i+1], Y[i+1], color=col[i], marker=".")


        else:
            for i, (x, y) in enumerate(zip(X, Y)):
                if i % 2 == 0:
                    line1, = ax.plot(x, y, label=f"Cycle {i // 2 + 1}")
                else:
                    line2, = ax.plot(x, y)

                try:
                    customization = plot_customizations.get(i // 2, {})

                    line1.set_color(customization.get("color", line1.get_color()))
                    line1.set_marker(customization.get("marker", line1.get_marker()))
                    line1.set_linestyle(customization.get("linestyle", line1.get_linestyle()))
                    line1.set_label(customization.get("label", f"Cycle {i // 2 + 1}"))

                    if i % 2 == 1:
                        line2.set_color(customization.get("color", line1.get_color()))
                        line2.set_marker(customization.get("marker", line1.get_marker()))
                        line2.set_linestyle(customization.get("linestyle", line1.get_linestyle()))
                        line2.set_label("_nolegend_")

                except Exception as e:
                    print(f"Error applying style: {e}")

        ax.set_xlabel("H [Oe]", fontsize=15)
        ax.set_ylabel(r"M/M$_{sat}$", fontsize=15)
        ax.legend()
        
        # Add horizontal line at y=0
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=1)
        # Add vertical line at x=0
        ax.axvline(x=0, color='gray', linestyle='--', linewidth=1)
                        
        canvas.draw()

    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error creating plot: {e}")

#==============================================================================================#
# Function to customize the style of the plot                                                  #
#==============================================================================================#

def customize_plot_style(parent_widget, plot_customizations, number_plots, figures_map):
    '''
    Opens a PyQt5 dialog to customize color, marker, and line style of a cycle in the plot.

    Parameters
    ----------
    parent_widget : QWidget
        parent PyQt5 window
    plot_customizations : dict
        dictionary to save users customizations
    number_plots : list
        list with one element, current plot number
    figures_map : dict
        dictionary to store all the matplotlib figures
    '''
    
    if parent_widget.figure is None:
        QMessageBox.critical(parent_widget, "Error", "No plot open! Create a plot first.")
        return

    fig, ax = figures_map[number_plots]

    lines = ax.lines

    # Remove grid 
    filtered_lines = []
    for line in lines:
        x_data, y_data = line.get_xdata(), line.get_ydata()
       
        if not (
            (all(y == 0 for y in y_data) and len(set(x_data)) > 1) or  # axhline(0)
            (all(x == 0 for x in x_data) and len(set(y_data)) > 1) or  # axvline(0)
            (line.get_gid() == "fit")
        ):
            filtered_lines.append(line)
            
    lines = filtered_lines

    if not lines:
        QMessageBox.critical(parent_widget, "Error", "No lines present in the graph!")
        return

    # === All possible customization options ===
    colors       = list(mcolors.TABLEAU_COLORS) + list(mcolors.CSS4_COLORS)
    markers_list = [m for m in markers.MarkerStyle.markers.keys() if isinstance(m, str) and len(m) == 1]
    linestyles   = list(mlines.Line2D.lineStyles.keys())

    # === Cycle names ===
    cycles = []
    label_to_index = {}
    for i in range(0, len(lines), 2):
        label = plot_customizations.get(i // 2, {}).get("label", f"Cycle {i // 2 + 1}")
        cycles.append(label)
        label_to_index[label] = i // 2

    # === Dialog ===
    dialog = QDialog(parent_widget)
    dialog.setWindowTitle("Customize Graphic Style")
    dialog.setFixedSize(400, 360)

    layout = QVBoxLayout(dialog)
    form_layout = QFormLayout()
    layout.addLayout(form_layout)

    # === Widgets ===
    cycle_combo = QComboBox()
    cycle_combo.addItems(cycles)

    color_combo = QComboBox()
    color_combo.addItems(colors)
    color_combo.setEditable(True)

    marker_combo = QComboBox()
    marker_combo.addItems(markers_list)
    marker_combo.setEditable(True)

    linestyle_combo = QComboBox()
    linestyle_combo.addItems(linestyles)
    linestyle_combo.setEditable(True)

    label_edit = QLineEdit()
    label_edit.setText(cycles[0])

    # === Add to form ===
    form_layout.addRow("Cycle:", cycle_combo)
    form_layout.addRow("Color:", color_combo)
    form_layout.addRow("Marker:", marker_combo)
    form_layout.addRow("Linestyle:", linestyle_combo)
    form_layout.addRow("Legend label:", label_edit)

    # === Apply button ===
    apply_button = QPushButton("Apply")
    layout.addWidget(apply_button)

    def apply_style():
        try:
            idx = label_to_index[cycle_combo.currentText()]
            line1 = lines[idx * 2]
            line2 = lines[idx * 2 + 1]

            color = color_combo.currentText()
            marker = marker_combo.currentText()
            linestyle = linestyle_combo.currentText()
            legend_label = label_edit.text() or cycle_combo.currentText()

            # Apply style to both lines
            for line in (line1, line2):
                line.set_color(color)
                line.set_marker(marker)
                line.set_linestyle(linestyle)

            line1.set_label(legend_label)
            line2.set_label("_nolegend_")
            
            # Save customization's 
            plot_customizations[idx] = {
                "color": color,
                "marker": marker,
                "linestyle": linestyle,
                "label": legend_label,
            }

            ax.legend()
            fig.canvas.draw_idle()
            dialog.accept()

        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Error applying style:\n{e}")

    apply_button.clicked.connect(apply_style)

    dialog.exec_()

def customize_plot_appearance(parent_widget):
    '''
    Function to customize the appearance of the plot (font sizes, minor ticks).

    Parameters
    ----------
    parent_widget : QWidget
        parent PyQt5 window
    '''
    if parent_widget.figure is None:
        QMessageBox.critical(parent_widget, "Error", "No plot open! Create a plot first.")
        return

    fig, ax = parent_widget.figure, parent_widget.ax

    dialog = QDialog(parent_widget)
    dialog.setWindowTitle("Plot Appearance")
    dialog.setFixedSize(350, 250)
    layout = QFormLayout(dialog)

    # Font sizes
    label_fontsize_edit  = QLineEdit(str(ax.xaxis.label.get_size()))
    tick_fontsize_edit   = QLineEdit(str(ax.xaxis.get_ticklabels()[0].get_size()) if ax.xaxis.get_ticklabels() else "10")
    legend_fontsize_edit = QLineEdit("10")

    # Minor ticks (safe check)
    minor_ticks_checkbox = QCheckBox("Show minor ticks")
    minor_ticks_checkbox.setChecked(any(tick.tick1line.get_visible() for tick in ax.xaxis.get_minor_ticks()))


    layout.addRow("Axis label fontsize:", label_fontsize_edit)
    layout.addRow("Tick label fontsize:", tick_fontsize_edit)
    layout.addRow("Legend fontsize:",     legend_fontsize_edit)
    layout.addRow(minor_ticks_checkbox)

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    layout.addWidget(buttons)

    def apply_changes():
        try:
            label_fs  = float(label_fontsize_edit.text())
            tick_fs   = float(tick_fontsize_edit.text())
            legend_fs = float(legend_fontsize_edit.text())

            ax.xaxis.label.set_fontsize(label_fs)
            ax.yaxis.label.set_fontsize(label_fs)

            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontsize(tick_fs)

            # Legend update
            leg = ax.get_legend()
            if leg:
                for text in leg.get_texts():
                    text.set_fontsize(legend_fs)

            # Minor ticks
            if minor_ticks_checkbox.isChecked():
                ax.minorticks_on()
            else:
                ax.minorticks_off()

            parent_widget.canvas.draw_idle()
            dialog.accept()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", str(e))

    buttons.accepted.connect(apply_changes)
    buttons.rejected.connect(dialog.reject)
    dialog.exec_()


#==============================================================================================#
# Function to hide a plotted cycle                                                             #
#==============================================================================================#

def cycle_visibility(parent_widget, number_plots, figures_map, plot_customizations):
    '''
    Opens a dialog to select which cycles to show/hide in the plot.

    Parameters
    ----------
    parent_widget : QWidget
        parent PyQt5 window
    number_plots : list
        list with one element, current plot number
    figures_map : dict
        dictionary to store all the matplotlib figures
    plot_customizations : dict
        dictionary with customizations (used to get labels)
    '''

    if parent_widget.figure is None:
        QMessageBox.critical(parent_widget, "Error", "No plot open! Create a plot first.")
        return

    fig, ax = figures_map[number_plots]
    lines = ax.lines

    # Remove grid
    filtered_lines = []
    for line in lines:
        x_data, y_data = line.get_xdata(), line.get_ydata()
        if not (
            (all(y == 0 for y in y_data) and len(set(x_data)) > 1) or  # axhline(0)
            (all(x == 0 for x in x_data) and len(set(y_data)) > 1) or  # axvline(0)
            (line.get_gid() == "fit")
        ):
            filtered_lines.append(line)

    lines = filtered_lines
    if not lines:
        QMessageBox.critical(parent_widget, "Error", "No lines present in the graph!")
        return

    # === Cycle labels ===
    cycles = []
    label_to_index = {}
    visibility_map = {}

    for i in range(0, len(lines), 2): 
        label = plot_customizations.get(i // 2, {}).get("label", f"Cycle {i // 2 + 1}")
        cycles.append(label)
        label_to_index[label] = i // 2
        visibility_map[label] = lines[i].get_visible()

    # === Dialog ===
    dialog = QDialog(parent_widget)
    dialog.setWindowTitle("Show/Hide Cycles")

    layout        = QVBoxLayout(dialog)
    scroll_area   = QScrollArea()
    scroll_widget = QWidget()
    scroll_layout = QVBoxLayout(scroll_widget)

    layout.addWidget(QLabel("Select data to display:"))

    checkboxes = {}

    for label in cycles:
        cb = QCheckBox(label)
        cb.setChecked(visibility_map[label])
        scroll_layout.addWidget(cb)
        checkboxes[label] = cb

    scroll_widget.setLayout(scroll_layout)
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(scroll_widget)
    layout.addWidget(scroll_area)

    # Buttons
    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    layout.addWidget(buttons)

    def apply_visibility():
        try : 
            for label, cb in checkboxes.items():
                idx = label_to_index[label]
                visible = cb.isChecked()
                # To avoid some problems with fit's plot
                lines[idx * 2 + 1].set_visible(visible)
                lines[idx * 2].set_visible(visible)

        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Visibility setting error:\n{e}")
        

        # Recreate legend only for visible objects
        handles, labels = ax.get_legend_handles_labels()
        visible_handles_labels = [(h, l) for h, l in zip(handles, labels) if h.get_visible()]
        if visible_handles_labels:
            handles, labels = zip(*visible_handles_labels)
            ax.legend(handles, labels)
        else:
            ax.legend().remove()  # No visible line => remove legend

        fig.canvas.draw_idle()
        dialog.accept()

    buttons.accepted.connect(apply_visibility)
    buttons.rejected.connect(dialog.reject)

    dialog.exec_() 

#==============================================================================================#
# Curve fitting function                                                                       #
#==============================================================================================#

def open_curve_fitting_window(app_instance, plot_widget):
    '''
    Apre una finestra per configurare il fitting dei dati.
    
    Parameters
    ----------
    app_instance : MainApp
        Istanza principale dell'applicazione.
    plot_widget : PlotControlWidget
        Istanza della finestra di controllo del plot corrente.
    '''
    dataframes    = app_instance.dataframes
    fit_results   = app_instance.fit_results
    logger        = app_instance.logger

    if not dataframes:
        QMessageBox.critical(app_instance, "Error", "No data loaded!")
        return

    window = QWidget()
    window.setWindowTitle("Quick Curve Fitting")
    layout = QHBoxLayout(window)
    window.setLayout(layout)

    def show_help_dialog():
        help_text = (
            "The fit function must be a function of the variable 'x' and "
            "the parameter names must be specified in the appropriate field.\n\n"
            "To establish the range, just read the cursor on the graph, the values are at the top right.\n\n"
            "AS A REMINDER, the 'Up' branch is the one on the right unless the x-axis has been inverted; "
            "in that case it will be the one on the left.\n\n"
            "ACHTUNG: the function must be written in Python, so for example |x| is abs(x), x^2 is x**2, and all "
            "other functions must be written with np. in front (i.e. np.cos(x), np.exp(x)), except for special functions, "
            "for which you must use the name used by the scipy.special library (i.e. scipy.special.erf becomes erf)"
        )

        QMessageBox.information(window, "Fitting Guide", help_text)

    # Left: selection
    selection_layout = QVBoxLayout()
    layout.addLayout(selection_layout)

    help_button = QPushButton("Help")
    help_button.clicked.connect(show_help_dialog)
    selection_layout.addWidget(help_button, alignment=Qt.AlignLeft)


    selection_layout.addWidget(QLabel("Select the file:"))
    file_combo = QComboBox()
    file_combo.addItems([f"File {i+1}" for i in range(len(dataframes))])
    selection_layout.addWidget(file_combo)

    selection_layout.addWidget(QLabel("Column X:"))
    x_combo = QComboBox()
    selection_layout.addWidget(x_combo)

    selection_layout.addWidget(QLabel("Column Y:"))
    y_combo = QComboBox()
    selection_layout.addWidget(y_combo)

    def update_columns():
        idx = file_combo.currentIndex()
        cols = list(dataframes[idx].columns)
        x_combo.clear()
        y_combo.clear()
        x_combo.addItems(cols)
        y_combo.addItems(cols)

    file_combo.currentIndexChanged.connect(update_columns)
    update_columns()

    # Right: parameters
    param_layout = QVBoxLayout()
    layout.addLayout(param_layout)

    param_layout.addWidget(QLabel("x_start:"))
    x_start_edit = QLineEdit("0")
    param_layout.addWidget(x_start_edit)

    param_layout.addWidget(QLabel("x_end:"))
    x_end_edit = QLineEdit("1")
    param_layout.addWidget(x_end_edit)

    param_layout.addWidget(QLabel("Parameter names (es. a,b):"))
    param_names_edit = QLineEdit("a,b")
    param_layout.addWidget(param_names_edit)

    param_layout.addWidget(QLabel("Initial values (es. 1,1):"))
    initial_params_edit = QLineEdit("1,1")
    param_layout.addWidget(initial_params_edit)

    param_layout.addWidget(QLabel("Fitting function (es. a*(x-b)):"))
    function_edit = QLineEdit("a*(x - b)")
    param_layout.addWidget(function_edit)

    output_box = QTextEdit()
    output_box.setReadOnly(True)
    output_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    layout.addWidget(output_box)

    def perform_fit():
        try:

            df_idx  = file_combo.currentIndex()
            df      = dataframes[df_idx]
            x_col   = x_combo.currentText()
            y_col   = y_combo.currentText()

            x_data  = df[x_col].astype(float).values
            y_data  = df[y_col].astype(float).values

            x_start = float(x_start_edit.text())
            x_end   = float(x_end_edit.text())
            mask    = (x_data >= x_start) & (x_data <= x_end)
            x_fit   = x_data[mask]
            y_fit   = y_data[mask]

            if len(x_fit) == 0:
                QMessageBox.warning(window, "Error", "No data in the selected range!")
                return

            param_names    = [p.strip() for p in param_names_edit.text().split(",")]
            initial_params = [float(p.strip()) for p in initial_params_edit.text().split(",")]

            func_code = f"lambda x, {', '.join(param_names)}: {function_edit.text()}"
            fit_func  = eval(func_code)

            params, pcov = curve_fit(fit_func, x_fit, y_fit, p0=initial_params)
            y_plot = fit_func(np.linspace(x_start, x_end, 500), *params)

            fig = plot_widget.figure
            ax  = plot_widget.ax
            fit_line, = ax.plot(np.linspace(x_start, x_end, 500), y_plot, linestyle="--", color="green")
            fit_line.set_gid("fit")
            plot_widget.canvas.draw()

            result_lines = []
            for p, val, err in zip(param_names, params, np.sqrt(np.diag(pcov))):
                
                result_lines.append(f"{p} = {format_value_error(val, err)}")    
                fit_results[p] = val
                fit_results[f"error_{p}"] = err

            for i , pi in zip(range(len(params)), param_names):
                for j , pj in zip(range(i+1, len(params)), param_names[i+1:]):
                    corr_ij = pcov[i, j]/np.sqrt(pcov[i, i]*pcov[j, j])
                    result_lines.append(f"corr({pi}, {pj}) = {corr_ij:.3f}")

            result = "\n".join(result_lines)
            output_box.setPlainText(result)
            logger.info("Fit completed successfully.")
            logger.info(f"Fitting function: {function_edit.text()}")
            logger.info(f"Fitting on data from File {df_idx + 1}, x: {x_col}, y: {y_col}, range: [{x_start}, {x_end}]")
            # Explicit cast to avoid newline issues in log file
            logger.info(f"The fit brought the following results: {str(result).replace(chr(10), ' ')}.")
            app_instance.refresh_shell_variables()

        except Exception as e:
            QMessageBox.critical(window, "Error", f"Error in fitting: {e}")
           
    fit_button = QPushButton("Run Fit")
    fit_button.clicked.connect(perform_fit)
    param_layout.addWidget(fit_button)

    # Sub-window for fitting panel
    sub = QMdiSubWindow()
    sub.setWidget(window)
    sub.setWindowTitle("Quick Curve Fitting")
    sub.resize(600, 300)
    app_instance.mdi_area.addSubWindow(sub)
    sub.show()