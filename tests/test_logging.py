'''
Code to test logging functions
'''
import os
import logging
import unittest
import tempfile
from tkinter import Tk
from unittest.mock import patch

from Hysteresis.utils.logging_setup import setup_logging, start_logging

class TestLoggingSetup(unittest.TestCase):
    
    def setUp(self):
        '''
        Prepare the environment for testing:
        1) Create a temporary file for logging.
        2) Initialize a simulated Tkinter window.
        3) Mock the main application.
        '''
        # Create a Tkinter window
        self.root = Tk()

        # Mock of a simulated App class
        class MockApp:
            def __init__(self):
                self.logger = None

        self.app_instance = MockApp()

    def tearDown(self):
        '''
        Cleans up the environment after testing:
        1) Destroys the Tkinter window.
        2) Removes any temporary files created.
        '''
        self.root.destroy()

    def test_setup_logging(self):
        '''
        Test that the setup_logging function:
        1) Creates a log file correctly.
        2) Writes initialization messages to the log file.
        '''
        # Creation of a temporary log file
        with tempfile.NamedTemporaryFile(delete=False) as temp_log_file:
            temp_log_path = temp_log_file.name

        try:
            # Configure logging
            setup_logging(temp_log_path)

            # Verify that the log file has been created
            self.assertTrue(os.path.exists(temp_log_path))

            # Check the contents of the log file
            with open(temp_log_path, "r") as log_file:
                content = log_file.read()
            self.assertIn("Inizio sessione di log.", content)
            self.assertIn(f"Logging configurato: scrittura su {temp_log_path}.log", content)

        finally:
            # Remove the temporary log file
            os.remove(temp_log_path)

    @patch("Hysteresis.utils.logging_setup.filedialog.asksaveasfilename")
    @patch("Hysteresis.utils.logging_setup.messagebox.showinfo")
    @patch("Hysteresis.utils.logging_setup.messagebox.showerror")
    def test_start_logging(self, mock_showerror, mock_showinfo, mock_asksaveasfilename):
        '''
        Test that the start_logging function:
        1) Opens a file selection dialog.
        2) Configures logging if a valid file is selected.
        3) Shows error messages or confirmations depending on the action.

        These unittest.mock @patch decorators are used to temporarily replace
        functions during tests, so that you can simulate their behavior without
        actually running them, i.e. without the presence of a user using tkinter windows.
        '''

        # Simulate a valid path for the log file
        with tempfile.NamedTemporaryFile(delete=False) as temp_log_file:
            temp_log_path = temp_log_file.name

        # Simulate file selection
        mock_asksaveasfilename.return_value = temp_log_path

        # Execute the function
        start_logging(self.app_instance)

        # Verify that the logger has been configured
        self.assertIsNotNone(self.app_instance.logger)
        self.assertTrue(isinstance(self.app_instance.logger, logging.Logger))

        # Verify that the confirmation message has been displayed
        mock_showinfo.assert_called_once_with(
            "Logging Avviato", f"Il log sarà scritto nel file: {temp_log_path}"
        )

        # Simulates closing the window without selecting a file
        mock_asksaveasfilename.return_value = ""
        start_logging(self.app_instance)

        # Verify that the error message was displayed
        mock_showerror.assert_called_once_with(
            "Errore", "Per favore seleziona un file valido per il log."
        )

        # Remove the temporary log file
        os.remove(temp_log_path)

if __name__ == "__main__":
    unittest.main()
