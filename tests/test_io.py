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
test for IO
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, mock_open, MagicMock
from PyQt5.QtWidgets import QApplication, QPushButton, QLineEdit
from PyQt5.QtWidgets import QDialog

from hyloa.data.io import *


@pytest.fixture
def fake_app():
    return MagicMock(
        dataframes=[],
        logger=MagicMock()
    )

def test_load_files_logger_missing():
    fake_app = MagicMock()
    fake_app.logger = None

    with patch("hyloa.data.io.QMessageBox.critical") as critical_mock:
        load_files(fake_app)
        critical_mock.assert_called_once()
        assert "log" in critical_mock.call_args[0][2].lower()

@patch("hyloa.data.io.QFileDialog.getOpenFileNames")
@patch("hyloa.data.io.open", new_callable=mock_open, read_data="FieldUp\tUpRot\tUpEllipt\tIzeroUp\n")
@patch("hyloa.data.io.show_column_selection")
def test_load_files_success(mock_show_columns, mock_open_fn, mock_getfiles, fake_app):
    # Mock selection of the file
    mock_getfiles.return_value = (["/fake/path/data1.txt"], "")

    # First dataframe
    fake_app.dataframes = []

    # Logger 
    fake_app.logger = MagicMock()

    load_files(fake_app)

    # Verify call of QFileDialog
    mock_getfiles.assert_called_once()

    # Verify the opening of the file
    mock_open_fn.assert_called_once_with("/fake/path/data1.txt", "r", encoding='utf-8')

    # Verify the call of show_column_selection
    mock_show_columns.assert_called_once()
    args = mock_show_columns.call_args[0]
    assert args[0] == fake_app                                     # app_instance
    assert args[1] == "/fake/path/data1.txt"                       # file_path
    assert args[2] == ["FieldUp", "UpRot", "UpEllipt", "IzeroUp"]  # header


@patch("hyloa.data.io.QMessageBox.question")
@patch("hyloa.data.io.QFileDialog.getOpenFileNames")
@patch("hyloa.data.io.open", new_callable=mock_open, read_data="FieldUp\tUpRot\tUpEllipt\tIzeroUp\n")
@patch("hyloa.data.io.show_column_selection")
def test_load_files_file_already_loaded(
    mock_show_columns, mock_open_fn, mock_getfiles, mock_question, fake_app
):
    # Simulates selection of existing file
    mock_getfiles.return_value = (["/fake/path/data1.txt"], "")
    mock_question.return_value = QMessageBox.Yes 

    # Already loaded file
    df = pd.DataFrame([[0, 1, 1, 1]], columns=["FieldUp", "UpRot", "UpEllipt", "IzeroUp"])
    df.attrs["filename"] = "data1.txt"
    fake_app.dataframes = [df]
    fake_app.logger = MagicMock()

    load_files(fake_app)

    mock_getfiles.assert_called_once()
    mock_question.assert_called_once()
    mock_open_fn.assert_called_once_with("/fake/path/data1.txt", "r", encoding='utf-8')
    mock_show_columns.assert_called_once()

    # Button for no
    mock_question.return_value = QMessageBox.No

    load_files(fake_app)
    mock_getfiles.assert_called()
    mock_question.assert_called()


@patch("hyloa.data.io.QFileDialog.getOpenFileNames", return_value=([], ""))
def test_load_files_cancel_dialog(mock_getfiles, fake_app):
    load_files(fake_app)
    # No file selected
    mock_getfiles.assert_called_once()

@patch("hyloa.data.io.QFileDialog.getOpenFileNames")
@patch("hyloa.data.io.QMessageBox.critical")
@patch("hyloa.data.io.open", side_effect=Exception("Errore di test"))
def test_load_files_open_raises(mock_open_fn, mock_critical, mock_getfiles, fake_app):
    # Fake file
    mock_getfiles.return_value = (["/fake/path/data1.txt"], "")

    # mock logger
    fake_app.logger = MagicMock()

    load_files(fake_app)

    # exception handling test
    mock_critical.assert_called_once()
    error_message = mock_critical.call_args[0][2]
    assert "errore" in error_message.lower()
    assert "data1.txt" in error_message


@patch("hyloa.data.io.QMessageBox.information")
@patch("hyloa.data.io.QMessageBox.critical")
@patch("hyloa.data.io.pd.read_csv")
@patch("hyloa.data.io.QWidget.show")  # prevent dialog from being shown
def test_show_column_selection_success(
    mock_show,
    mock_read_csv,
    mock_critical,
    mock_info,
    qtbot,
    ):
    # Create a dummy app instance with logger and data storage
    app_instance = MagicMock()
    app_instance.logger = MagicMock()
    app_instance.dataframes = []
    app_instance.header_lines = []
    app_instance.refresh_shell_variables = MagicMock()

    # Prepare mock return values for pd.read_csv
    header_df = pd.DataFrame(
        [["h1"], ["h2"], ["h3"]],
        columns=["FieldUp"]
    )

    data_df = pd.DataFrame(
        [[0, 1, 1, 1], [1, 2, 2, 2], [2, 3, 3, 3]],
        columns=["FieldUp", "UpRot", "UpEllipt", "IzeroUp"]
    )

    # Define sequence of calls to pd.read_csv
    def side_effect_read_csv(filepath, sep="\t", **kwargs):
        if kwargs.get("nrows") == 3:
            return header_df
        elif "usecols" in kwargs:
            # simulate selected columns
            return data_df[kwargs["usecols"]]
        else:
            return data_df

    mock_read_csv.side_effect = side_effect_read_csv

    # Input values
    file_path = "/fake/path/data1.txt"
    header = ["FieldUp", "UpRot", "UpEllipt", "IzeroUp"]

    # Run the GUI function
    show_column_selection(app_instance, file_path, header)

    # Get the dialog instance from QApplication's topLevelWidgets
    dialog = next(w for w in QApplication.topLevelWidgets() if w.windowTitle().startswith("Seleziona Colonne"))

    # Find the 'Carica' button in the dialog and simulate clicking it
    button = dialog.findChild(QPushButton, "")
    assert button is not None
    qtbot.mouseClick(button, Qt.LeftButton)

    # Check that pd.read_csv was called with correct params
    assert mock_read_csv.call_count >= 3
    mock_read_csv.assert_any_call(file_path, sep="\t", nrows=3)

    # Check that the dataframe was added to app_instance
    assert len(app_instance.dataframes) == 1
    df = app_instance.dataframes[0]
    assert list(df.columns) == [
        f"data1_{col}" for col in header  # since no custom name was typed in
    ]
    assert df.attrs["filename"] == "data1.txt"

    # Check logging and QMessageBox were triggered
    app_instance.logger.info.assert_any_call(f"Dal file: {file_path}, caricate le colonne: {header}")
    mock_info.assert_called_once()
    assert "Dati caricati" in mock_info.call_args[0][2]

    # Check that refresh_shell_variables was called
    app_instance.refresh_shell_variables.assert_called_once()

    # Check the dialog was closed
    assert not dialog.isVisible()

@pytest.fixture
def fake_app():
    # Fake app_instance with a mocked logger
    app = MagicMock()
    app.logger = MagicMock()
    return app


@pytest.fixture
def header_df():
    # Fake header DataFrame to be saved
    return pd.DataFrame([
        ["val1", "val2", "val3"],
        ["a", np.nan, "c"]
    ], columns=["Col1", "Col2", "Col3"])

def test_save_header_success(fake_app, header_df):
    # Mock the open() function and simulate file writing
    m = mock_open()
    with patch("builtins.open", m):
        save_header(fake_app, header_df, "fake_path/file.txt")

    # Check that open was called correctly
    m.assert_called_once_with("fake_path/file.txt", "w", encoding="utf-8")

    # Access the mock file handle to assert writes
    handle = m()

    # Check the header line was written
    handle.write.assert_any_call("Col1\tCol2\tCol3\n")

    # Check that the data rows were written (and NaN handled properly)
    handle.write.assert_any_call("val1\tval2\tval3\n")
    handle.write.assert_any_call("a\t\tc\n")

    # Check logging was performed correctly
    fake_app.logger.info.assert_any_call("File salvato correttamente in: fake_path/file.txt")

def test_save_header_failure(fake_app, header_df):
    # Simulate an IOError during file open
    with patch("builtins.open", side_effect=IOError("Mocked failure")):
        save_header(fake_app, header_df, "fake_path/file.txt")

    # Assert that an error was logged
    fake_app.logger.info.assert_any_call("Errore durante il salvataggio: Mocked failure")



@pytest.fixture
def dummy_dataframes():
    import pandas as pd
    df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pd.DataFrame({"x": [5, 6], "y": [7, 8]})
    return [df1, df2]

@pytest.fixture
def app_with_dataframes(dummy_dataframes):
    app_instance = MagicMock()
    app_instance.dataframes = dummy_dataframes
    return app_instance


def test_save_modified_data_opens_dialog(qtbot, app_with_dataframes):
    parent_widget = QWidget()
    qtbot.addWidget(parent_widget)

    # Patcher to intercept the function to test
    with patch("hyloa.data.io.save_to_file") as mock_save_to_file:

        # We build the dialogue inside a wrapper function that we can control
        def run_dialog():
            save_modified_data(app_with_dataframes, parent_widget)

        # Let's simulate the user interaction (click on the Save button)
        # Using QTimer.singleShot to make sure the click happens after the dialog opens
        from PyQt5.QtCore import QTimer
        def click_save():
            for w in parent_widget.findChildren(QPushButton):
                if w.text() == "Salva":
                    qtbot.mouseClick(w, Qt.LeftButton)
                    break

        QTimer.singleShot(100, click_save)

        run_dialog()

        assert mock_save_to_file.called, "La funzione save_to_file non è stata chiamata"


def test_save_modified_data_no_data_shows_error(qtbot):
    app_instance = MagicMock()
    app_instance.dataframes = []

    parent_widget = QWidget()
    qtbot.addWidget(parent_widget)

    with patch("hyloa.data.io.QMessageBox.critical") as mock_critical:
        save_modified_data(app_instance, parent_widget)
        mock_critical.assert_called_once_with(parent_widget, "Errore", "Nessun dato da salvare.")


@pytest.fixture
def dummy_app():
    app = MagicMock()
    app.dataframes = [
        pd.DataFrame([[1., 2., 3., 4.]]),
        pd.DataFrame([[1., 2., 3., 4., 5., 6.]]),
        pd.DataFrame([[1., 2., 3., 4., 5., 6., 7., 8.]])
    ]
    app.header_lines = ["# header1\n", "# header2\n", "# header3\n"]
    return app

@pytest.mark.parametrize("df_idx, expected_data", [
    (0, "1.0\t0.0\t2.0\t0.0\t3.0\t0.0\t4.0\t0.0\n"),
    (1, "1.0\t2.0\t3.0\t0.0\t4.0\t5.0\t6.0\t0.0\n"),
    (2, "1.0\t2.0\t3.0\t4.0\t5.0\t6.0\t7.0\t8.0\n"),
])
def test_save_to_file_expands_columns_correctly(df_idx, expected_data, dummy_app):
    # Patcher to really prevent windows from opening
    with patch("hyloa.data.io.QFileDialog.getSaveFileName", return_value=("fake_path.txt", None)), \
         patch("hyloa.data.io.save_header") as mock_save_header, \
         patch("builtins.open", mock_open()) as mock_file, \
         patch("hyloa.data.io.QMessageBox.information"), \
         patch("hyloa.data.io.QMessageBox.warning"), \
         patch("hyloa.data.io.QMessageBox.critical"):

        # Call the function
        save_to_file(df_idx, dummy_app)

        # Verify that save_header has been called
        mock_save_header.assert_called_once_with(dummy_app, dummy_app.header_lines[df_idx], "fake_path.txt")

        # Get the handle of the file open for writing
        handle = mock_file()

        # Verify that the written data is correct
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        assert expected_data in written
