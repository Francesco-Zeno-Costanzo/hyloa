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
        # Remove any existing handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            encoding="utf-8",
            format="%(asctime)s -  %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        logging.info("Start of log session.")
        logging.info(f"Logging configured: write on {log_file}")
    except Exception as e:
        raise Exception(f"Error while configuring logging: {e}")


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
            "Logger already configured."
        )
        return
    # Inform the user that the file will be appended to if it already exists
    QMessageBox.information(
        parent_widget,
        "Info",
        "If you choose an existing file, writing will be queued, without overwriting."
    )

    # Let the user choose the file
    log_file, _ = QFileDialog.getSaveFileName(
        parent_widget,
        "Select the log file",
        "",
        "Log Files (*.log);;Tutti i file (*)"
    )

    if log_file:
        try:
            setup_logging(log_file)
            app_instance.logger = logging.getLogger(__name__)
            app_instance.logger.info("Logging configured successfully.")
            app_instance.logger_path = log_file

            QMessageBox.information(
                parent_widget,
                "Logging Started",
                f"The log will be written on the file:\n{log_file}"
            )

            app_instance.open_default_panels()
            
        except Exception as e:
            QMessageBox.critical(
                parent_widget,
                "Error",
                f"Error while configuring logging:\n{e}"
            )
    else:
        QMessageBox.critical(
            parent_widget,
            "Error",
            "Please select a valid file for the log."
        )