import unittest
import pandas as pd
from tkinter import Tk
from unittest.mock import MagicMock, patch

from Hysteresis.data.show import loaded_files
from Hysteresis.gui.main_window import MainApp


class TestLoadedFiles(unittest.TestCase):

    def setUp(self):
        '''
        Prepare the environment for testing:
        1) A Tkinter window to simulate the interface.
        2) An instance of the MainApp class to test the method.
        '''
        # Create a Tkinter window
        self.root = Tk()

        # Creates an instance of MainApp, simulating the main application
        self.app_instance = MainApp(self.root)

        # Set up a simulated logger for the app
        self.app_instance.logger = MagicMock()

    def tearDown(self):
        '''
        Cleans up the environment after testing:
        1) Destroys the Tkinter window.
        '''
        self.root.destroy() # Destroy Tkinter window

    @patch("Hysteresis.data.show.messagebox.showerror")
    def test_loaded_files_no_data(self, mock_showerror):
        ''' Verify that an error occurs when no files ar loaded.
        '''
        self.app_instance.dataframes = []  # No files loaded

        loaded_files(self.app_instance)

        # Verify error message
        mock_showerror.assert_called_once_with("Errore", "Non ci sono file caricati!")

    @patch("Hysteresis.data.show.Toplevel")
    @patch("Hysteresis.data.show.tk.Text")
    def test_loaded_files_ui_elements(self, mock_text, mock_toplevel):
        '''
        Check that loaded_files:
        1. Create a Toplevel window.
        2. Create a Text area to show files and columns.
        3. Enter the text with file and column names correctly.
        '''
        # Simulate the loaded files
        self.app_instance.dataframes = [
            pd.DataFrame(columns=["A", "B", "C"]),
            pd.DataFrame(columns=["X", "Y", "Z"]),
        ]

        # Simulate window creation ad text area
        mock_file_window = MagicMock()
        mock_toplevel.return_value = mock_file_window
        mock_text_widget = MagicMock()
        mock_text.return_value = mock_text_widget

        # Call the function to test
        loaded_files(self.app_instance)

        # Verify that the Toplevel window has been created
        mock_toplevel.assert_called_once_with(self.root)

        # Verify that the text area has been created and packed
        mock_text.assert_called_once_with(mock_file_window, wrap="word", height=20, width=60)
        mock_text_widget.pack.assert_called()

        # Verify that al the necessary text has been inserted
        expected_text = "File 1:Colonne: A, B, C\n\nFile 2:Colonne: X, Y, Z\n\n"
        calls = [call[0][1] for call in mock_text_widget.insert.call_args_list]  # All text
        result_text = "".join(calls).replace(" ", "").replace("\n", "")

        expected_text_cleaned = expected_text.replace(" ", "").replace("\n", "")
        self.assertEqual(result_text, expected_text_cleaned)

if __name__ == "__main__":
    unittest.main()
