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
    QDialog
)

from hyloa.data.io import load_files
from hyloa.gui.log_window import LogWindow
from hyloa.data.io import save_modified_data
from hyloa.gui.script_window import ScriptEditor
from hyloa.gui.command_window import CommandWindow
from hyloa.gui.plot_window import PlotControlWidget
from hyloa.utils.logging_setup import start_logging
from hyloa.data.session import save_current_session
from hyloa.data.session import load_previous_session


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
            "Se si carica una sessione precedente verrà usato il file di log di quella sessione.\n"
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        layout.addWidget(self.make_button("Avvia Logging", self.conf_logging))

        layout.addWidget(self.make_group("Gestione File", [
            ("Carica File", self.load_data),
            ("Visualizza File", self.show_loaded_files)
        ]))

        layout.addWidget(self.make_group("Analisi", [
            ("Crea Grafico", self.plot),
            ("Salva Dati", self.save_data),
            ("Script", self.open_script_editor),
            ("Appunti", self.open_comment_window)
        ]))

        layout.addWidget(self.make_group("Sessione", [
            ("Salva Sessione", self.save_session),
            ("Carica Sessione", self.load_session)
        ]))

        layout.addWidget(self.make_button("Esci", self.exit_app))

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

        sub = QMdiSubWindow()
        sub.setWidget(plot_widget)
        sub.setWindowTitle(f"Controllo grafico {self.number_plots}")
        sub.resize(600, 300)
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
        editor = ScriptEditor(self)
        sub = QMdiSubWindow()
        sub.setWidget(editor)
        sub.setWindowTitle("Editor di Script")
        sub.resize(600, 300)
        self.mdi_area.addSubWindow(sub)
        sub.show()
    
    def open_comment_window(self):
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
        reply = QMessageBox.question(self, "Esci", "Vuoi uscire e salvare la sessione?",
                                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

        if reply == QMessageBox.Yes:
            self.save_session()
            event.accept()
        elif reply == QMessageBox.No:
            event.accept()
        else:
            event.ignore()


