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

import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMdiArea, QMdiSubWindow, QWidget, QVBoxLayout,
    QPushButton, QMessageBox, QTextEdit, QLabel, QDockWidget, QGroupBox, QHBoxLayout,
    QListWidget, QDialog
)

# Code for data management
from hyloa.data.io import load_files
from hyloa.data.io import save_modified_data
from hyloa.data.session import save_current_session
from hyloa.data.session import load_previous_session

# Code for interface
from hyloa.gui.log_window import LogWindow
from hyloa.gui.plot_window import PlotSubWindow
from hyloa.gui.script_window import ScriptEditor
from hyloa.gui.command_window import CommandWindow
from hyloa.gui.plot_window import PlotControlWidget

# Auxiliary code
from hyloa.utils.logging_setup import start_logging



class MainApp(QMainWindow):
    '''
    Class to handle the main window
    '''
    def __init__(self):

        super().__init__()
        self.setWindowTitle("Analisi Cicli di Isteresi")
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

        description = QLabel(
            "Per poter inziare l'analisi è necessario specificare un nome per il file di log.\n"
            "Per maggiori informazioni usare il tasto help.\n"
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        layout.addWidget(self.make_group("Inizio", [
            ("Help", self.help),
            ("Avvia Logging", self.conf_logging)
        ]))

        layout.addWidget(self.make_group("Gestione File", [
            ("Carica File", self.load_data),
            ("Visualizza File", self.show_loaded_files),
            ("Salva Dati", self.save_data)
        ]))

        layout.addWidget(self.make_group("Analisi", [
            ("Crea Grafico", self.plot),
            ("Script", self.open_script_editor),
            ("Appunti", self.open_comment_window)
        ]))

        layout.addWidget(self.make_group("Sessione", [
            ("Carica Sessione", self.load_session),
            ("Elenco finestre", self.show_window_navigator),
            ("Salva Sessione", self.save_session)
        ]))

        layout.addWidget(self.make_group("Exit", [
            ("Esci", self.exit_app)
        ]))

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
        help_text = (
            "Per poter inziare l'analisi è necessario specificare un nome per il file di log. "
            "Se si carica una sessione precedente verrà usato il file di log della sessione. "
            "File di log e file della sessione devono essere nella stessa cartella. "
            "In caso il file di log non fosse più presente ne verrà creato uno nuovo con lo stesso "
            "nome e stesso path del precedente. \n\n"

        )

        QMessageBox.information(self.mdi_area, "Breve guida ad hyloa", help_text)

    def conf_logging(self):
        ''' Function that call the logging configuration
        '''
        start_logging(self, parent_widget=self)

    def load_data(self):
        ''' call load file to load data
        '''
        load_files(self)  # Pass the class instance as an argument
        self.refresh_shell_variables()

    def show_loaded_files(self):
        ''' Function that create a window to see all data aviable
        '''
        sub = QMdiSubWindow()
        sub.setWindowTitle("File Caricati")
        txt = QTextEdit()
        txt.setText("\n".join(
            [f'File {i+1}: '+', '.join(df.columns) for i, df in enumerate(self.dataframes)]
            ) or "Nessun file caricato")
        sub.setWidget(txt)
        self.mdi_area.addSubWindow(sub)
        sub.show()

    def save_data(self):
        ''' Call the function to save the modified data.
        '''
        save_modified_data(self, parent_widget=self) # Pass the class instance as an argument
    
    def plot(self):
        ''' Function that create a instance for plot's control panel
        '''

        if self.logger is None:
            QMessageBox.critical(None, "Errore", "Impossibile iniziare l'analisi senza avviare il log")
            return
        
        if len(self.dataframes) == 0:
            QMessageBox.critical(None, "Errore", "Nessun file caricato")
            return
        
        self.number_plots += 1
        plot_widget = PlotControlWidget(self, self.number_plots)
        self.plot_widgets[self.number_plots] = plot_widget

        sub = PlotSubWindow(self, plot_widget, self.number_plots)
        self.mdi_area.addSubWindow(sub)
        sub.show()
    
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
        editor = ScriptEditor(self)
        sub = QMdiSubWindow()
        sub.setWidget(editor)
        sub.setWindowTitle("Editor di Script")
        sub.resize(600, 300)
        self.mdi_area.addSubWindow(sub)
        sub.show()
    
    def open_comment_window(self):
        ''' Function to open a window to write some comments about the data or something else
        '''
        dialog = QDialog(self)
        dialog.setWindowTitle("Appunti dell'analisi")

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Gli appunti scritti verranno salvati nel file di log:"))

        text_edit = QTextEdit()
        layout.addWidget(text_edit)

        btn_layout  = QHBoxLayout()
        confirm_btn = QPushButton("Salva")
        cancel_btn  = QPushButton("Annulla")
        btn_layout.addWidget(confirm_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        def save_comment():
            comment = text_edit.toPlainText().strip()
            if comment:
                if self.logger:
                    self.logger.info(f"[Commento] {comment}")
                QMessageBox.information(dialog, "Salvato", "Commento salvato nel log.")
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Vuoto", "Il commento è vuoto.")

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
            QMessageBox.information(self, "Nessuna Finestra", "Non ci sono finestre aperte.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Navigatore Finestre")
        dialog.setMinimumSize(600, 400)
        layout = QHBoxLayout(dialog)

        # List of all windows
        left_layout = QVBoxLayout()
        list_widget = QListWidget()
        for win in subwindows:
            list_widget.addItem(win.windowTitle())
        left_layout.addWidget(QLabel("Finestre aperte:"))
        left_layout.addWidget(list_widget)

        # Preview of selected windows
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Anteprima finestra selezionata:"))

        preview_label = QLabel()
        preview_label.setFixedSize(280, 220)
        preview_label.setStyleSheet("border: 1px solid gray; background: white;")
        preview_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(preview_label)

        # Button to bring window to the foreground
        activate_button = QPushButton("Attiva finestra selezionata")
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
                win.raise_()
                dialog.accept()

        activate_button.clicked.connect(activate_window)
        list_widget.itemDoubleClicked.connect(lambda _: activate_window())

        dialog.exec_()



    def exit_app(self):
        ''' Function for exit button
        '''
        reply = QMessageBox.question(self, "Esci", "Vuoi uscire e salvare la sessione?",
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
        
        reply = QMessageBox.question(self, "Esci", "Vuoi uscire e salvare la sessione?",
                                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

        if reply == QMessageBox.Yes:
            self.save_session()
            event.accept()
        elif reply == QMessageBox.No:
            event.accept()
        else:
            event.ignore()


