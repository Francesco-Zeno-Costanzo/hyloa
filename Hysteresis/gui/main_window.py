"""
Code that manages the main screen.
It is necessary to start the log session in order to trace
everything that is done otherwise it is not possible to start
the analysis. From here the calls to the other functions branch out.
"""
import tkinter as tk
import matplotlib.pyplot as plt
from tkinter import ttk, messagebox

from Hysteresis.data.io import load_files
from Hysteresis.data.show import loaded_files
from Hysteresis.data.io import save_modified_data
from Hysteresis.gui.plot_window import open_plot_window
from Hysteresis.utils.logging_setup import start_logging
from Hysteresis.data.session import save_current_session
from Hysteresis.data.session import load_previous_session


class MainApp:
    
    def __init__(self, root):
        '''
        Class constructor, rather than global variables,
        define attributes to manage the information and 
        configurations

        Parameters
        ----------
        root : instance of TK class from tkinter
            toplevel Tk widget, main window of the application
        '''
        
        # Attributes to manage information and configuration
        self.dataframes           = []     # List to store loaded DataFrames
        self.count_plot           = 0      # Counter to update the single plot
        self.plot_customizations  = {}     # Dictionary to save graphic's customization
        self.header_lines         = []     # List to store the initial lines of files
        self.logger               = None   # Logger for the entire application
        self.logger_path          = None   # Path to the log file
        self.fit_results          = {}     # Dictionary to save fitting results
        self.number_plots         = 0      # Number of all created plots
        self.list_figures         = []     # List to store all figures
        self.plot_window_ref      = None   # Reference to the plot window



        # Initialize main window
        self.root = root
        self.root.title("Analisi Cicli di Isteresi")
        self.root.geometry("500x500")
        self.create_main_window()
    

    def conf_logging(self):
        ''' Initializes logging.
        '''
        start_logging(self)
    

    def load_data(self):
        ''' Call the function to load the data and update the interface.
        '''
        load_files(self)  # Pass the class instance as an argument

        # Check if the plot window is already open
        # If the plot window is open, refresh the data in it
        if self.plot_window_ref is not None and self.plot_window_ref.winfo_exists():
            self.refresh_plot_window_data()

    def show_loaded_files(self):
        ''' Call the function to display the uploaded files.
        '''
        loaded_files(self) # Pass the class instance as an argument
    
    def save(self):
        ''' Call the function to save the modified data.
        '''
        save_modified_data(self) # Pass the class instance as an argument


    def plot(self):
        ''' Create a new plot window
        '''
        self.number_plots += 1
        self.plot_window_ref = open_plot_window(self)  # Save the reference

    
    def refresh_plot_window_data(self):
        ''' Update the open plot window with newly loaded files. '''
        if self.plot_window_ref is None:
            return
        
        # Cerca tutti i widget OptionMenu nella finestra e aggiorna le opzioni dei file
        for widget in self.plot_window_ref.winfo_children():
            if isinstance(widget, tk.Frame) or isinstance(widget, tk.LabelFrame):
                for subwidget in widget.winfo_children():
                    if isinstance(subwidget, tk.OptionMenu):
                        menu = subwidget["menu"]
                        menu.delete(0, "end")
                        for i in range(len(self.dataframes)):
                            menu.add_command(
                                label=f"File {i + 1}",
                                command=lambda value=f"File {i + 1}": subwidget.variable.set(value)
                            )

    
    def save_session(self):
        ''' Call the function to save the session.
        '''
        save_current_session(self)

    def load_session(self):
        ''' Call the function to load a previous session.
        '''
        load_previous_session(self)

    def exit_app(self):
        ''' Function to exit the application
        '''
        risposta = messagebox.askyesnocancel("Uscita", "Vuoi salvare la sessione prima di uscire?")
        if risposta is True:
            save_current_session(self)
            self.root.quit()
            self.root.destroy()
        elif risposta is False:
            plt.close("all")
            self.root.quit()
            self.root.destroy()

    def create_main_window(self):
        ''' Function to create the main window with improved layout and style '''
        
        style = ttk.Style()
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))
        
        self.root.configure(bg="#f0f0f0")

        description = (
            "Il codice è in grado di effettuare una serie di analisi sui cicli di Isteresi.\n"
            "Per poterlo eseguire è necessario specificare un nome per il file di log.\n"
            "In caso non venga specificato il path il file sarà salvato nella cartella corrente.\n"
            "Se si vuole cambiare file di log, riavviare il programma"        
        )

        tk.Label(self.root, text=description, justify="center", wraplength=480,
                bg="#f0f0f0", font=("Segoe UI", 10)).pack(pady=10)

        ttk.Button(self.root, text="Avvia Logging", command=self.conf_logging).pack(pady=10)

        # Frame to organize buttons in sections
        sections = [
            ("Gestione File", [
                ("Carica File", self.load_data),
                ("Visualizza File Caricati", self.show_loaded_files)
            ]),
            ("Analisi e Salvataggio", [
                ("Crea Grafico", self.plot),
                ("Salva Dati Modificati", self.save)
            ]),
            ("Gestione Sessione", [
                ("Salva Sessione", self.save_session),
                ("Carica Sessione", self.load_session)
            ])
        ]

        for section_title, buttons in sections:
            frame = ttk.LabelFrame(self.root, text=section_title)
            frame.pack(pady=10, padx=10, fill="x")

            for label, command in buttons:
                ttk.Button(frame, text=label, command=command).pack(side=tk.LEFT, padx=10, pady=5, expand=True)

        # Exit Button
        ttk.Button(self.root, text="Esci", command=self.exit_app).pack(pady=20)