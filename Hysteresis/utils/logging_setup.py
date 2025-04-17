"""
Code for logger setup
"""
import logging
from PyQt5.QtWidgets import QFileDialog, QMessageBox


def setup_logging(log_file):
    '''
    Configures logging to the specified file.

    Parameters
    ----------
    log_file : str
        Path to the log file.
    '''
    try:
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s -  %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        logging.info("Inizio sessione di log.")
        logging.info(f"Logging configurato: scrittura su {log_file}")
    except Exception as e:
        raise Exception(f"Errore durante la configurazione del logging: {e}")


def start_logging(app_instance, parent_widget=None):
    '''
    Starts the logging session by selecting a file and configuring the logger.

    Parameters
    ----------
    app_instance : MainApp
        Instance of the main application class
    parent_widget : QWidget
        The parent window for dialog placement (optional)
    '''
    if app_instance.logger is not None:
        QMessageBox.information(
            parent_widget,
            "Info",
            "Logger già configurato."
        )
        return
    # Inform the user that the file will be appended to if it already exists
    QMessageBox.information(
        parent_widget,
        "Info",
        "Se si sceglie un file già esistente, la scrittura sarà in coda, senza sovrascrizioni."
    )

    # Let the user choose the file
    log_file, _ = QFileDialog.getSaveFileName(
        parent_widget,
        "Seleziona il file di log",
        "",
        "Log Files (*.log);;Tutti i file (*)"
    )

    if log_file:
        try:
            setup_logging(log_file)
            app_instance.logger = logging.getLogger(__name__)
            app_instance.logger.info("Logging configurato con successo.")
            app_instance.logger_path = log_file

            QMessageBox.information(
                parent_widget,
                "Logging Avviato",
                f"Il log sarà scritto nel file:\n{log_file}"
            )

            app_instance.open_default_panels()
            
        except Exception as e:
            QMessageBox.critical(
                parent_widget,
                "Errore",
                f"Errore durante la configurazione del logging:\n{e}"
            )
    else:
        QMessageBox.critical(
            parent_widget,
            "Errore",
            "Per favore seleziona un file valido per il log."
        )