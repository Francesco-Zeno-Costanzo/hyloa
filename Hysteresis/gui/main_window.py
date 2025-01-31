"""
Code that manages the main screen.
It is necessary to start the log session in order to trace
everything that is done otherwise it is not possible to start
the analysis. From here the calls to the other functions branch out.
"""
import tkinter as tk

from data.io import load_files
from data.show import loaded_files
from data.io import save_modified_data
from gui.plot_window import open_plot_window
from utils.logging_setup import start_logging

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
        self.plot_customizations  = {}     # Dictionary to save graphic customizations
        self.header_lines         = []     # List to store the initial lines of files
        self.logger               = None   # Logger for the entire application
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


    def create_main_window(self):
        ''' Function to create the main window
        '''
        
        description = (
            "Il codice è in grado di effettuare una serie di analisi sui cicli di Isteresi.\n"
            "Per poterlo eseguire è necessario specificare un nome per il file di log.\n"
            "In caso non venga specificato il path il file sarà salvato nella cartella corrente.\n"
            "Se si vuole cambiare file di log, bisogna far ripartire il programma"        
        )

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

        frame_bottom = tk.Frame(self.root)
        frame_bottom.pack(pady=10)

        # Main Buttons
        # First line: Upload File and View Uploaded Files
        tk.Button(frame_top, text="Carica File", command=self.load_data).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_top, text="Visualizza File Caricati", command=self.show_loaded_files).pack(side=tk.LEFT, padx=5)

        # Second line: Create plot and Save Changed Data
        tk.Button(frame_middle, text="Crea Grafico", command=self.plot).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_middle, text="Salva Dati Modificati", command=self.save).pack(side=tk.LEFT, padx=5)

        # Third line: Exit
        tk.Button(frame_bottom, text="Esci", command=self.root.quit).pack()