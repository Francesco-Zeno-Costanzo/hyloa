"""
Code that manages the main screen.
It is necessary to start the log session in order to trace
everything that is done otherwise it is not possible to start
the analysis. From here the calls to the other functions branch out.
"""
import tkinter as tk
from tkinter import ttk
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
        self.count_plot           = 0      # Counter to update the graphs
        self.plot_customizations  = {}     # Dictionary to save graphic's customization
        self.header_lines         = []     # List to store the initial lines of files
        self.logger               = None   # Logger for the entire application
        self.logger_path          = None   # Path to the log file
        self.fit_results          = {}     # Dictionary to save fitting results

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

    def show_loaded_files(self):
        ''' Call the function to display the uploaded files.
        '''
        loaded_files(self) # Pass the class instance as an argument
    
    def save(self):
        ''' Call the function to save the modified data.
        '''
        save_modified_data(self) # Pass the class instance as an argument


    def plot(self):
        ''' Call the function to create a graph.
        '''
        open_plot_window(self) # Pass the class instance as an argument

    
    def save_session(self):
        ''' Call the function to save the session.
        '''
        save_current_session(self)

    def load_session(self):
        ''' Call the function to load a previous session.
        '''
        load_previous_session(self)

    

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
        ttk.Button(self.root, text="Esci", command=self.root.quit).pack(pady=20)

    """
    def create_main_window(self):
        ''' Function to create the main window
        '''
        
        

        # Using Message to automatically fit text
        tk.Message(self.root, text=description, width=480).pack()

        # Button to start logging
        log_button = tk.Button(self.root, text="Avvia Logging",
                               command=self.conf_logging)
        log_button.pack(pady=20)

        # Frame to organize buttons in rows
        frame_top = tk.Frame(self.root)
        frame_top.pack(pady=10)

        frame_middle = tk.Frame(self.root)
        frame_middle.pack(pady=10)

        frame_middle_2 = tk.Frame(self.root)
        frame_middle_2.pack(pady=10)

        frame_bottom = tk.Frame(self.root)
        frame_bottom.pack(pady=10)

        # Main Buttons
        # First line: Upload File and View Uploaded Files
        tk.Button(frame_top, text="Carica File", command=self.load_data).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_top, text="Visualizza File Caricati", command=self.show_loaded_files).pack(side=tk.LEFT, padx=5)

        # Second line: Create plot and Save Changed Data
        tk.Button(frame_middle, text="Crea Grafico", command=self.plot).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_middle, text="Salva Dati Modificati", command=self.save).pack(side=tk.LEFT, padx=5)

        # Third line: Save and Load Session
        tk.Button(frame_middle_2, text="Salva Sessione", command=self.save_session).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_middle_2, text="Carica Sessione", command=self.load_session).pack(side=tk.LEFT, padx=5)

        # Final line: Exit
        tk.Button(frame_bottom, text="Esci", command=self.root.quit).pack()"""