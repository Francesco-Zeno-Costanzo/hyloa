"""
Code for logger setup
"""
import logging
from tkinter import filedialog, messagebox

def setup_logging(log_file):
    '''
    Configure the log file to track operations.

    Parameters
    ----------
    log_file : str
        Path to the log file.
    '''
    try:
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,  # Livello di log (INFO, DEBUG, ERROR, ecc.)
            format="%(asctime)s -  %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        logging.info("Inizio sessione di log.")
        logging.info(f"Logging configurato: scrittura su {log_file}.log")
    
    except Exception as e:
        raise Exception(f"Errore durante la configurazione del logging: {e}")
    


def start_logging(app_instance):
    '''
    Initializes logging by allowing a log file path to be selected via a dialog.

    Parameters
    ----------
    app_instance : MainApp object
        instance of MainApp from main_window.py
    '''

    # Open the dialog box to choose the file path
    log_file = filedialog.asksaveasfilename(
        defaultextension=".log",
        filetypes=[("Log Files", "*.log"), ("Tutti i file", "*.*")],
        title="Seleziona il file di log"
    )

    if log_file:
        # Configure logging
        setup_logging(log_file)
        app_instance.logger = logging.getLogger(__name__)
        app_instance.logger.info("Logging configurato con successo.")

        # Show a confirmation message
        messagebox.showinfo("Logging Avviato", f"Il log sarà scritto nel file: {log_file}")
    else:
        # Error message if no file is selected
        messagebox.showerror("Errore", "Per favore seleziona un file valido per il log.")
