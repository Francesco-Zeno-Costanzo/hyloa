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
Code that manages the main screen.
It is necessary to start the log session in order to trace
everything that is done otherwise it is not possible to start
the analysis. From here the calls to the other functions branch out.
"""

from importlib import resources
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMdiArea, QMdiSubWindow, QWidget, QVBoxLayout,
    QPushButton, QMessageBox, QTextEdit, QLabel, QDockWidget, QGroupBox, QHBoxLayout,
    QListWidget, QDialog, QInputDialog
)
from PyQt5.QtGui import QPixmap

# Code for data management
from hyloa.data.io import load_files
from hyloa.data.io import duplicate_file
from hyloa.data.io import save_modified_data
from hyloa.data.session import save_current_session
from hyloa.data.session import load_previous_session

# Code for interface
from hyloa.gui.log_window import LogWindow
from hyloa.gui.plot_window import PlotSubWindow
from hyloa.gui.script_window import ScriptEditor
from hyloa.gui.command_window import CommandWindow
from hyloa.gui.plot_window import PlotControlWidget
from hyloa.gui.worksheet import WorksheetWindow

# Auxiliary code
from hyloa.utils.logging_setup import start_logging
from hyloa.utils.check_version import check_for_updates


class MainApp(QMainWindow):
    '''
    Class to handle the main window
    '''
    def __init__(self):

        super().__init__()
        self.setWindowTitle("Hysteresis Loop Analyzer - tmp session")
        self.setGeometry(100, 100, 1000, 700)

        # MDI area
        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)

        # Attributes to manage information and configuration
        self.dataframes           = []     # List to store loaded DataFrames
        self.header_lines         = []     # List to store the initial lines of files
        self.logger               = None   # Logger for the entire application
        self.logger_path          = None   # Path to the log file
        self.fit_results          = {}     # Dictionary to save fitting results
        self.number_plots         = 0      # Number of all created plots
        self.figures_map          = {}     # dict to store all figures
        self.plot_widgets         = {}     # {int: PlotControlWidget}
        self.plot_names           = {}     # {int: "name of the figure"}
        self.plot_subwindows      = {}     # {plot_index: QMdiSubWindow for control panel}
        self.figure_subwindows    = {}     # {plot_index: QMdiSubWindow for figure window}
        self.number_worksheets    = 0      # Number of all created worksheets
        self.worksheet_windows    = {}     # {int: WorksheetWindow}
        self.worksheet_names      = {}     # {int: str}
        self.worksheet_subwindows = {}     # {int: QMdiSubWindow}


        # Interface
        self.shell_sub = None
        self.log_sub   = None

        self.init_sidebar()
        self.show()

    def init_sidebar(self):
        ''' Create sidebar with buttons
        '''
        dock = QDockWidget(self)
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        control_panel = QWidget()
        layout = QVBoxLayout(control_panel)

        # === LOGO ===

        def load_icon():
            with resources.path("hyloa.resources", "icon-5.png") as p:
                pixmap = QPixmap(str(p))
            return pixmap

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)

        pixmap = load_icon()

        if pixmap.isNull():
            logo_label.setText("Logo not found")
        else:
            # Mantein proportion and visibility
            scaled = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled)

        # Avoid compression
        logo_label.setMinimumSize(128, 128)

        layout.addWidget(logo_label)
        #=========================================

        description = QLabel(
            "To start the analysis, you need to specify a name for the log file.\n"
            "For more information, use the help button.\n"
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        layout.addWidget(self.make_group("Strat", [
            ("Version",       check_for_updates),
            ("Help",          self.help),
            ("Start Logging", self.conf_logging)
        ]))

        layout.addWidget(self.make_group("File Management", [
            ("Load file",      self.load_data),
            ("Show file",      self.show_loaded_files),
            ("Save file",      self.save_data),
            ("Duplicate file", self.duplicate)
        ]))

        layout.addWidget(self.make_group("Analysis", [
            ("Create plot", self.plot),
            ("Worksheet",   self.worksheet),
            ("Script",      self.open_script_editor),
            ("Annotation",  self.open_comment_window)
        ]))

        layout.addWidget(self.make_group("Session", [
            ("Load session",    self.load_session),
            ("list of windows", self.show_window_navigator),
            ("Save session",    self.save_session)
        ]))

        layout.addWidget(self.make_group("Exit", [
            ("Exit", self.exit_app)
        ]))

        #control_panel.setMinimumWidth(140)
        #control_panel.setMaximumWidth(300)
        control_panel.setFixedWidth(160)

        dock.setWidget(control_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        
    def make_button(self, text, callback):
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        return btn

    def make_group(self, title, button_info):
        group = QGroupBox(title)
        layout = QVBoxLayout()
        for label, callback in button_info:
            btn = QPushButton(label)
            btn.clicked.connect(callback)
            layout.addWidget(btn)
        group.setLayout(layout)
        return group

    #==================== Application Functions ====================#

    def help(self):
        ''' Function show a short guide
        '''
        help_text = (
            "#==========#\n"
            " Starting \n"
            "#==========#\n"
            "In order to start the analysis, you need to specify a name for the log file. "
            "If you load a previous session, the session log file will be used. "
            "Log files and session files must be in the same folder. "
            "If the log file is no longer present, a new one will be created with the same "
            "name and path as the previous one. \n\n"
            "#=======#\n"
            " File \n"
            "#=======#\n"
            "To upload files you can use the ”Load file” button. "
            "All the names of the uploaded files with attached data names, "
            "since they are all pandas data frames, can be consulted via the show file button.\n"
            "The ”Save file” button allows you to save a file keeping the same "
            "header as the original file with which it was uploaded.\n"
            "If you want to create copies of data to do different tests you can use the ”duplicate file” button. \n\n"
            "#=========#\n"
            " Analysis \n"
            "#=========#\n"
            "In the analysis section, ”create plot” button opens a command window that allows you to create and customize a graph.\n"
            "It is also possible to write and/or load a Python file to perform further analysis of the data via the ”script” button.\n"
            "”Annotation” opens a text box that allows you to write comments that will then be saved in the log file.\n\n"
            "#=========#\n"
            " Session \n "
            "#=========#\n"
            "Is possible to use “Save Session” to store the full state: data, plots, layout, fits, etc. the data will be written in a .pkl file.\n"
            "A previous session can be restored with the “Load Session” button. \n"
            "At the same time, the button list of windows can be used to visualize a list of all windows open "
            "in the current session, also with a preview. This is useful when u have a large number of windows and/or some windows are minimized. \n\n"
            "#=====================#\n"
            " Shell and log panel \n "
            "#=====================#\n"
            " A built-in Python shell is included at the bottom of the interface. \n"
            "Thehre is also a log Panel that displays real-time logs of all operations."
        )

        QMessageBox.information(self.mdi_area, "A Short Guide to Hyloa", help_text)

    def conf_logging(self):
        ''' Function that call the logging configuration
        '''
        start_logging(self, parent_widget=self)

    def load_data(self):
        ''' call load files to load data
        '''
        load_files(self)  # Pass the class instance as an argument
        self.refresh_shell_variables()
    
    def duplicate(self):
        ''' For duplication file
        '''
        duplicate_file(self)

    def show_loaded_files(self):
        ''' Function that create a window to see all data aviable
        '''
        sub = QMdiSubWindow()
        sub.setWindowTitle("Loaded files")
        txt = QTextEdit()
        txt.setText("\n".join(
            [f'File {i+1}: '+', '.join(df.columns) for i, df in enumerate(self.dataframes)]
            ) or "No files loaded")
        sub.setWidget(txt)
        self.mdi_area.addSubWindow(sub)
        sub.show()

    def save_data(self):
        ''' Call the function to save the modified data.
        '''
        save_modified_data(self, parent_widget=self) # Pass the class instance as an argument
    

    def worksheet(self):
        ws = WorksheetWindow(self.mdi_area)
        self.mdi_area.addSubWindow(ws)
        ws.show()

    def worksheet(self):
        if self.logger is None:
            QMessageBox.critical(None, "Error", "Cannot create worksheet without starting log")
            return

        text, ok = QInputDialog.getText(self, "Worksheet name", "Enter a name for the worksheet:")
        if not ok or not text.strip():
            return
        
        self.number_worksheets += 1
        ws_idx  = self.number_worksheets
        ws_name = text.strip()

        worksheet = WorksheetWindow(self.mdi_area, name=ws_name, logger=self.logger)
        
        worksheet.setWindowTitle(f"Worksheet - {ws_name}")
        self.mdi_area.addSubWindow(worksheet)
        worksheet.show()

        # Save for session restore
        self.worksheet_subwindows[ws_idx] = worksheet
        self.worksheet_windows[ws_idx]    = worksheet
        self.worksheet_names[ws_idx]      = ws_name



    def plot(self):
        ''' Function that create a instance for plot's control panel
        '''

        if self.logger is None:
            QMessageBox.critical(None, "Error", "Cannot start analysis without starting log")
            return
        
        if len(self.dataframes) == 0:
            QMessageBox.critical(None, "Error", "No files loaded")
            return
        
        # Ask a name for the plot
        text, ok = QInputDialog.getText(self, "Plot's name", "Enter a name for the plot:")
        if not ok or not text.strip():
            return  # cancel if empty or canceled

        self.number_plots += 1
        custom_name        = text.strip()

        # Create control panel
        plot_widget = PlotControlWidget(self, self.number_plots, custom_name)
        self.plot_widgets[self.number_plots] = plot_widget
        self.plot_names[self.number_plots]   = custom_name

        sub = PlotSubWindow(self, plot_widget, self.number_plots)
        self.mdi_area.addSubWindow(sub)
        sub.show()
        # Save for session loading
        self.plot_subwindows[self.number_plots] = sub

    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.position_default_panels)

    def open_default_panels(self):
        '''
        Function for opening automatically the shell and the log panel
        in the bottom part of the main window one next to the other
        '''
        # Create shell
        self.shell_widget = CommandWindow(self)
        self.shell_sub = QMdiSubWindow()
        self.shell_sub.setWidget(self.shell_widget)
        self.shell_sub.setWindowTitle("Python Shell")
        self.shell_sub.resize(self.width() // 2, 300)
        self.mdi_area.addSubWindow(self.shell_sub)
        self.shell_sub.show()

        # Create log panel
        log_widget   = LogWindow(self)
        self.log_sub = QMdiSubWindow()
        self.log_sub.setWidget(log_widget)
        self.log_sub.setWindowTitle("Log Output")
        self.log_sub.resize(self.width() // 2, 300)
        self.mdi_area.addSubWindow(self.log_sub)
        self.log_sub.show()

        self.position_default_panels()
    
    def position_default_panels(self):
        ''' 
        Function that handle the postion and the automatic scaling
        of the log and shell panels
        '''
        if not hasattr(self, 'shell_sub') or not hasattr(self, 'log_sub'):
            return  

        if not self.shell_sub or not self.log_sub:
            return

        mdi_size     = self.mdi_area.viewport().size()
        width        = mdi_size.width()
        height       = mdi_size.height()
        half_width   = width // 2
        panel_height = 300

        # If too small adapt height
        if panel_height * 2 > height:
            panel_height = height // 2

        self.shell_sub.resize(half_width, panel_height)
        self.log_sub.resize(half_width, panel_height)

        self.shell_sub.move(0, height - panel_height)
        self.log_sub.move(half_width, height - panel_height)


    def refresh_shell_variables(self):
        ''' Function to automatically add new variables to the shell context
        '''
        for sub in self.mdi_area.subWindowList():
            widget = sub.widget()
            if isinstance(widget, CommandWindow):
                widget.refresh_variables()
    
    def open_script_editor(self):
        ''' Function to open a window to write some python code
        '''

        if self.logger is None:
            QMessageBox.critical(None, "Error", "Cannot start analysis without starting log")
            return
        
        editor = ScriptEditor(self)
        sub = QMdiSubWindow()
        sub.setWidget(editor.window)
        sub.setWindowTitle("Editor di Script")
        sub.resize(600, 600)
        self.mdi_area.addSubWindow(sub)
        sub.show()
    
    def open_comment_window(self):
        ''' Function to open a window to write some comments about the data or something else
        '''
        dialog = QDialog(self)
        dialog.setWindowTitle("Analysis notes")

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("The written notes will be saved in the log file:"))

        text_edit = QTextEdit()
        layout.addWidget(text_edit)

        btn_layout  = QHBoxLayout()
        confirm_btn = QPushButton("Save")
        cancel_btn  = QPushButton("Cancel")
        btn_layout.addWidget(confirm_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        def save_comment():
            comment = text_edit.toPlainText().strip()
            if comment:
                if self.logger:
                    self.logger.info(f"[Comment] {comment}")
                QMessageBox.information(dialog, "Saved", "Comment saved in log.")
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Empty", "The annotation is empty.")

        confirm_btn.clicked.connect(save_comment)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec_()



    def save_session(self):
        ''' Function that call save_current_session
        '''
        save_current_session(self, parent_widget=self)

    def load_session(self):
        ''' Function that call load_previous_session
        '''
        load_previous_session(self, parent_widget=self)
        self.refresh_shell_variables()
    
    def show_window_navigator(self):
        ''' Function to navigate through all open windows
        '''
        subwindows = self.mdi_area.subWindowList()
        if not subwindows:
            QMessageBox.information(self, "No Window", "There are no open windows.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Windows Navigator")
        dialog.setMinimumSize(1000, 600)
        layout = QHBoxLayout(dialog)

        # List of all windows
        left_layout = QVBoxLayout()
        list_widget = QListWidget()
        for win in subwindows:
            list_widget.addItem(win.windowTitle())
        left_layout.addWidget(QLabel("Open windows:"))
        left_layout.addWidget(list_widget)

        # Preview of selected windows
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Preview selected window:"))

        preview_label = QLabel()
        preview_label.setFixedSize(800, 500)

        preview_label.setStyleSheet("border: 1px solid gray; background: white;")
        preview_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(preview_label)

        # Button to bring window to the foreground
        activate_button = QPushButton("Activate selected window")
        right_layout.addWidget(activate_button)

        # Merge layout
        layout.addLayout(left_layout)
        layout.addLayout(right_layout)

        def update_preview():
            ''' Function to update preview
            '''
            idx = list_widget.currentRow()
            if idx >= 0:
                sub = subwindows[idx]
                pixmap = sub.grab()  # Screenshot of the window
                preview = pixmap.scaled(preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                preview_label.setPixmap(preview)

        list_widget.currentRowChanged.connect(update_preview)

        def activate_window():
            ''' Function to bring window to the foreground
            '''
            idx = list_widget.currentRow()
            if idx >= 0:
                win = subwindows[idx]
                self.mdi_area.setActiveSubWindow(win)
                win.showNormal()
                if win.isMinimized:
                    # Just some random default values to avoid problem
                    win.resize(400, 400)
                    win.move(self.width()//4, self.height()//4)
                win.raise_()
                dialog.accept()

        activate_button.clicked.connect(activate_window)
        list_widget.itemDoubleClicked.connect(lambda _: activate_window())

        dialog.exec_()



    def exit_app(self):
        ''' Function for exit button
        '''
        reply = QMessageBox.question(self, "Exit", "Do you want to exit and save your session?",
                                     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            self.save_session()
            QApplication.quit()
        elif reply == QMessageBox.No:
            QApplication.quit()
        # Otherwise (cancel) => do nothing
    
    def closeEvent(self, event):
        ''' Intercepts window closing to ask whether to save data
        '''

        if self.logger is None:
            event.accept()
            return
        
        reply = QMessageBox.question(self, "Exit", "Do you want to exit and save your session?",
                                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

        if reply == QMessageBox.Yes:
            self.save_session()
            event.accept()
        elif reply == QMessageBox.No:
            event.accept()
        else:
            event.ignore()


