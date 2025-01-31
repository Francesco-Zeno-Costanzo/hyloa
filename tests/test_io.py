"""
Code to test input output functions
"""
import os
import unittest
import tempfile
import pandas as pd
from tkinter import Tk
from unittest.mock import MagicMock, patch

from Hysteresis.data.io import *
from Hysteresis.gui.main_window import MainApp

#==============================================================================================#
# File upload tests                                                                             #
#==============================================================================================#

class TestLoadFiles(unittest.TestCase):

    def setUp(self):
        '''
        Prepare the environment for testing:
        1) A Tkinter window to simulate the interface.
        2) An instance of the MainApp class to test the method.
        3) A temporary file to simulate a file to load.
        '''
        
        # Create a Tkinter window
        self.root = Tk()

        # Creates an instance of MainApp, simulating the main application
        self.app = MainApp(self.root)

        # Set up a simulated logger for the app
        self.app.logger = MagicMock()

        # Create a temporary file to simulate the loaded data
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".txt")
        self.temp_file.write("col1\tcol2\tcol3\n1\t2\t3\n4\t5\t6\n7\t8\t9\n")
        self.temp_file.close()

    def tearDown(self):
        '''
        Cleans up the environment after testing:
        1) Destroys the Tkinter window.
        2) Removes any temporary files created.
        '''

        self.root.destroy() # Destroy Tkinter window

        # Remove the temporary file
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    @patch("Hysteresis.data.io.filedialog.askopenfilenames")
    @patch("Hysteresis.data.io.show_column_selection")
    def test_load_files(self, mock_show_column_selection, mock_askopenfilenames):
        '''
        Test the load_files function, verifying that:
        1) The files are loaded correctly.
        2) The selected columns are added to the dataframes attribute.
        3) The logger correctly records the opening of the file.

        These unittest.mock @patch decorators are used to temporarily replace
        functions during tests, so that you can simulate their behavior without
        actually running them, i.e. without the presence of a user using tkinter windows.
        '''

        # Simulates user file selection
        mock_askopenfilenames.return_value = [self.temp_file.name]

        # Simulate the show_column_selection function. 
        # This function would allow you to select which columns of the file to load. 
        # Here only a dictionary is loaded as we do not really care what data structure is loaded.
        # We will deal with this in the specific test for this (show_column_selection) function
        def mock_show_selection(app_instance, root, file_path, header):
            app_instance.dataframes.append({"file_path": file_path, "header": header})

        # Sets the simulated behavior of the show_column_selection function
        mock_show_column_selection.side_effect = mock_show_selection

        # Call the function to test
        load_files(self.app)

        # Verify that the data has been uploaded correctly
        self.assertEqual(len(self.app.dataframes), 1)                                     # There must be only one DataFrame
        self.assertEqual(self.app.dataframes[0]["file_path"], self.temp_file.name)        # Path of the file
        self.assertListEqual(self.app.dataframes[0]["header"], ["col1", "col2", "col3"])  # Headers

        # Verify that the logger was called with the correct message
        self.app.logger.info.assert_called_once_with(f"Apertura file {self.temp_file.name}.")

#==============================================================================================#

class TestShowColumnSelection(unittest.TestCase):

    def setUp(self):
        '''
        Prepare the environment for testing:
        1) A Tkinter window to simulate the interface.
        2) An instance of the MainApp class to test the method.
        3) A temporary file to simulate a file to load.
        '''

        # Create a Tkinter window
        self.root = Tk()

        # Creates an instance of MainApp, simulating the main application
        self.app_instance = MainApp(self.root)

        # Set up a simulated logger for the app
        self.app_instance.logger = MagicMock()

        # Create a temporary file to simulate the loaded data
        self.file_path = "dummy_file.txt"
        self.header    = ["col1", "col2", "col3"]

        self.test_data = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": [4, 5, 6],
            "col3": [7, 8, 9]
        })
        self.test_data.to_csv(self.file_path, sep="\t", index=False)

    def tearDown(self):
        '''
        Cleans up the environment after testing:
        1) Destroys the Tkinter window.
        2) Removes any temporary files created.
        '''
        self.root.destroy() # Destroy Tkinter window

        # Remove the temporary file
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

    @patch("Hysteresis.data.io.tk.Toplevel")
    @patch("Hysteresis.data.io.tk.Checkbutton")
    @patch("Hysteresis.data.io.tk.Entry")
    @patch("Hysteresis.data.io.tk.Button")
    @patch("Hysteresis.data.io.tk.Message")
    def test_show_column_selection(self, mock_message, mock_button, mock_entry, mock_checkbutton, mock_toplevel):
        '''
        Test that the show_column_selection function:
        1) Correctly creates the column selection window.
        2) Correctly loads data from the selected file.
        3) Correctly updates the dataframes and header_lines attributes.

        These unittest.mock @patch decorators are used to temporarily replace
        functions during tests, so that you can simulate their behavior without
        actually running them, i.e. without the presence of a user using tkinter windows.
        '''

        # Emulates the secondary window created by show_column_selection
        mock_toplevel.return_value = MagicMock()
        mock_message.return_value  = MagicMock()

        # Emulate columns selection
        selected_columns = {i: MagicMock(get=MagicMock(return_value=True)) for i in range(len(self.header))}
        custom_names     = {i: MagicMock(get=MagicMock(return_value=f"custom_col_{i}")) for i in range(len(self.header))}

        # Emulation of checkbutton via MagicMock
        def mock_checkbutton_side_effect(*args, **kwargs):
            return MagicMock(pack=MagicMock())

        mock_checkbutton.side_effect = mock_checkbutton_side_effect

        # Emulation of entry box via MagicMock
        def mock_entry_side_effect(*args, **kwargs):
            return MagicMock(pack=MagicMock())

        mock_entry.side_effect = mock_entry_side_effect

        # Emulation of button via MagicMock
        def mock_button_side_effect(*args, **kwargs):
            return MagicMock(pack=MagicMock())

        mock_button.side_effect = mock_button_side_effect

        
        def mock_submit():
            ''' Function to emulate the behavior of the load button
            '''
            columns_to_load = [
                self.header[i]
                for i in range(len(self.header))
                if selected_columns[i].get()
            ]

            custom_column_names = [
                custom_names[i].get() or f"{self.file_path.split('/')[-1][:-4]}_{self.header[i]}"
                for i in range(len(self.header))
                if selected_columns[i].get()
            ]
            
            df = pd.read_csv(self.file_path, sep="\t", usecols=columns_to_load)
            df.columns = custom_column_names
            self.app_instance.dataframes.append(df)
            self.app_instance.logger.info(
                f"Dal file: {self.file_path}, caricate le colonne: {columns_to_load}."
            )

        mock_button.side_effect = lambda *args, **kwargs: MagicMock(command=mock_submit())

        # Call the function to test
        show_column_selection(self.app_instance, self.root, self.file_path, self.header)

        # Verify that the DataFrame has been added correctly
        self.assertEqual(len(self.app_instance.dataframes), 1)
        df = self.app_instance.dataframes[0]
        self.assertIsInstance(df, pd.DataFrame)

        # Verify that the selected columns are correct
        self.assertListEqual(list(df.columns), [f"custom_col_{i}" for i in range(len(self.header))])

        # Verify that the logger was called with the correct message
        self.app_instance.logger.info.assert_called_once_with(
            f"Dal file: {self.file_path}, caricate le colonne: {self.header}."
        )

#==============================================================================================#
# Save data tests                                                                              #
#==============================================================================================#

class TestSaveHeader(unittest.TestCase):

    def setUp(self):
        '''
        Prepare the environment for testing:
        1) A Tkinter window to simulate the interface.
        2) An instance of the MainApp class to test the method.
        3) A temporary file to simulate a file to load.
        4) An example of DataFrame with nan values
        '''

        # Create a Tkinter window
        self.root = Tk()

        # Creates an instance of MainApp, simulating the main application
        self.app_instance = MainApp(self.root)

        # Set up a simulated logger for the app
        self.app_instance.logger = MagicMock()

        # Create a temporary file to save data
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()

        # DataFrame for the test, with the same structure of a tipical header
        self.df = pd.DataFrame({
            "col1": ["val1", "val2", "nan"],  
            "col2": ["val3", "nan", "val5"],  
            "col3": ["nan", "val6", "val7"]
        })

    def tearDown(self):
        '''
        Cleans up the environment after testing:
        1) Destroys the Tkinter window.
        2) Removes any temporary files created.
        '''
        self.root.destroy() # Destroy Tkinter window

        # Remove the temporary file
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)

    def test_save_header_success(self):
        '''
        Test that save_header works properly 
        '''
        
        # Call the function to test
        save_header(self.app_instance, self.df, self.temp_file_path)

        # Verify that the logger was called with the correct message
        self.app_instance.logger.info.assert_called_once_with(
            f"File salvato correttamente in: {self.temp_file_path}"
        )

        # Read the saved file
        with open(self.temp_file_path, "r") as f:
            lines = f.readlines()

        # Verify the header
        expected_header = "col1\tcol2\tcol3\n"
        self.assertEqual(lines[0], expected_header)

        # Verify the data with nan values
        expected_lines = [
            "val1\tval3\n",
            "val2\t\tval6\n",
            "val5\tval7\n"
        ]

        self.assertListEqual(lines[1:], expected_lines)
    
    def test_save_header_error(self):
        '''
        Test that save_header coorectly handle the exception
        '''

        # Writing error for invalid path
        invalid_path = "/cartella_non_esistente/file.txt"

        save_header(self.app_instance, self.df, invalid_path)

        # Verify the presence of the error in the log file
        self.app_instance.logger.info.assert_called_with(
            f"Errore durante il salvataggio: [Errno 2] No such file or directory: '{invalid_path}'"
        )

#==============================================================================================#

class TestSaveModifiedData(unittest.TestCase):

    def setUp(self):
        '''
        Prepare the environment for testing:
        1) A Tkinter window to simulate the interface.
        2) An instance of the MainApp class to test the method.
        3) A temporary file to simulate a file to load.
        4) Several DataFrame
        '''
          
        # Create a Tkinter window
        self.root = Tk()

        # Creates an instance of MainApp, simulating the main application
        self.app_instance = MainApp(self.root)

        # Set up a simulated logger for the app
        self.app_instance.logger = MagicMock()

        # Crea DataFrame con 4, 6 e 8 colonne
        self.df_4_col = pd.DataFrame(np.arange(12).reshape(3, 4))  # 3 rows, 4 columns
        self.df_6_col = pd.DataFrame(np.arange(18).reshape(3, 6))  # 3 rows, 6 columns
        self.df_8_col = pd.DataFrame(np.arange(24).reshape(3, 8))  # 3 rows, 8 columns

        # Store all DataFrames
        self.app_instance.dataframes = [self.df_4_col, self.df_6_col, self.df_8_col]

        # Header for the DataFrames
        self.app_instance.header_lines = [
            pd.DataFrame({"A":[], "B":[], "C":[], "D":[], "E":[], "F":[], "G":[], "H":[]})
        ]*3

        # Create a temporary file to save data
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()
    
    def tearDown(self):
        '''
        Cleans up the environment after testing:
        1) Destroys the Tkinter window.
        2) Removes any temporary files created.
        '''
        self.root.destroy() # Destroy Tkinter window

        # Remove the temporary file
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
    
    @patch("Hysteresis.data.io.messagebox.showerror")
    def test_save_modified_data_no_data(self, mock_showerror):
        ''' Test error with no data
        '''
        self.app_instance.dataframes = [] 

        save_modified_data(self.app_instance)

        # Verify error message
        mock_showerror.assert_called_once_with("Errore", "Non ci sono dati caricati!")

    @patch("Hysteresis.data.io.Toplevel")
    @patch("Hysteresis.data.io.StringVar")
    @patch("Hysteresis.data.io.tk.OptionMenu")
    @patch("Hysteresis.data.io.tk.Button")
    @patch("Hysteresis.data.io.tk.Message")
    def test_save_modified_data_ui_elements(self, mock_message, mock_button, mock_optionmenu, mock_stringvar, mock_toplevel):
        '''
        Check that save_modified_data:
        1) Create a dialog box.
        2) Create a drop-down menu to select the file.
        3) Create buttons to save and view uploaded files.
        4) Create the descriptive message
        '''
        self.app_instance.dataframes = ["fake_df1", "fake_df2"]  # Simula due file caricati

        mock_save_window = MagicMock()
        mock_toplevel.return_value = mock_save_window

        save_modified_data(self.app_instance)

        #Verify that the dialog box has been created
        mock_toplevel.assert_called_once_with(self.root)

        # Verify that the drop-down menu has been created
        mock_optionmenu.assert_called_once()

        # Verify that the buttons have been created
        self.assertEqual(mock_button.call_count, 2)

        # Verify that the message has been created
        mock_message.assert_called_once()

        # Verify the call to save_to_file
        _, kwargs = mock_button.call_args_list[0]  # Parameters of the first button
        self.assertIn("command", kwargs, "The value of command is missing")
        self.assertTrue(callable(kwargs["command"]), "The value of command is not a function")


    @patch("Hysteresis.data.io.filedialog.asksaveasfilename")
    @patch("Hysteresis.data.io.messagebox.showinfo")
    def test_save_to_file(self, mock_showinfo, mock_asksaveasfilename):
        '''
        Check that save_to_file
        1) Create the save window.
        2) Save the file with 8 columns.
        3) Show the confirmation message.
        '''
        # Simulate the user's choice of file
        mock_asksaveasfilename.return_value = self.temp_file_path

        # Create the window
        save_window = Toplevel(self.root)

        # For all files (to test different number of columns)
        for idx in [1, 2, 3]:
            
            selected_df = StringVar(value=f"File {idx}")

            # Call the function to test
            save_to_file(selected_df, self.app_instance, save_window)

            # Verify the message
            if idx==1:
                mock_showinfo.assert_called_once_with("Salvataggio completato",
                f"Dati salvati in {os.path.basename(self.temp_file_path)}")
            
            # Verify the content of the saved file
            data = pd.read_csv(self.temp_file_path, sep="\t")

            expected_header = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

            self.assertListEqual(list(data.columns), expected_header)
            self.assertTupleEqual(data.shape, (3, 8))

            if idx == 1:
                for col in ["B", "D", "F", "H"]:
                    self.assertListEqual(list(data[col]), [0]*3)
            elif idx == 2:
                for col in ["D", "H"]:
                    self.assertListEqual(list(data[col]), [0]*3)
            else :
                df = pd.DataFrame(np.arange(24).reshape(3, 8), columns=list('ABCDEFGH'))
                self.assertEqual(data.equals(df), True)

    @patch("Hysteresis.data.io.filedialog.asksaveasfilename", return_value="/fake/path/dati_modificati.txt")
    @patch("Hysteresis.data.io.messagebox.showerror")
    @patch("Hysteresis.data.io.save_header")  # Mock save_header to avoid writing to file
    def test_save_to_file_error(self, mock_save_header, mock_showerror, mock_asksaveasfilename):
        ''' Verify that save_to_file correctly handles exceptions
        '''
        selected_df = StringVar(value="File 1")

        # Simulate an exception during np.savetxt execution
        with patch("data.io.np.savetxt", side_effect=Exception("Errore di test")):
            save_to_file(selected_df, self.app_instance, self.root)

        # Verify the error message
        mock_showerror.assert_called_once()
        args, _ = mock_showerror.call_args
        self.assertTrue("Errore durante il salvataggio" in args[1])