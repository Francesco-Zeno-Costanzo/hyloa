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
from unittest.mock import patch, mock_open, MagicMock

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
@patch("hyloa.data.io.detect_header_length", return_value=2)
def test_load_files_success(mock_dhl, mock_show_columns, mock_open_fn, mock_getfiles, fake_app):
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
@patch("hyloa.data.io.detect_header_length", return_value=2)
def test_load_files_file_already_loaded(
    mock_dhl, mock_show_columns, mock_open_fn, mock_getfiles, mock_question, fake_app
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
@patch("hyloa.data.io.open", side_effect=Exception("Test error"))
@patch("hyloa.data.io.detect_header_length", return_value=2)
def test_load_files_open_raises(mock_dhl, mock_open_fn, mock_critical, mock_getfiles, fake_app):
    # Fake file
    mock_getfiles.return_value = (["/fake/path/data1.txt"], "")

    # mock logger
    fake_app.logger = MagicMock()

    load_files(fake_app)

    # exception handling test
    mock_critical.assert_called_once()
    error_message = mock_critical.call_args[0][2]
    assert "error" in error_message.lower()
    assert "data1.txt" in error_message


def test_detect_header_length_with_clean_header(tmp_path):
    #Create a tmp file
    content = """
        # File example
        # created: 2024
        # columns: time\tvalue
        1.0\t2.0
        2.0\t3.0
    """
    file = tmp_path / "test1.txt"
    file.write_text(content)

    result = detect_header_length(file)
    # Header with 3 rows, no empty row → data_start = 3 - 1 - 0 = 2
    assert result == 2

def test_detect_header_length_with_empty_lines(tmp_path):
    #Create a tmp file
    content = """
        # Header line
        # Unit: s\tm
            
        0.0\t0.5
        1.0\t0.6
    """
    file = tmp_path / "test2.txt"
    file.write_text(content)

    result = detect_header_length(file)
    # Header with 2 rows, 1 empty row → data_start = 3 - 1 - 1 = 1
    assert result == 1

def test_detect_header_length_with_no_numeric_data(tmp_path):
    # Create a tmp file with no numerical values
    content = """
        # just text
        text\tmoretext
        ---\t---
        nope\tagain
    """
    file = tmp_path / "test3.txt"
    file.write_text(content)

    with pytest.raises(ValueError, match="No valid data found"):
        detect_header_length(file)

def test_detect_header_length_custom_separator(tmp_path):
    # Create a tmp file csv
    content = """
        #Header A,B,C
        #units,V,A
        1.0,2.0,3.0
        4.0,5.0,6.0
    """
    file = tmp_path / "test4.csv"
    file.write_text(content)

    result = detect_header_length(file, sep=',')
    # Header with 2 rows, no empty row → data_start = 2 - 1 - 0 = 1
    assert result == 1

def test_detect_header_is_numeric_row(tmp_path):
    # Create a tmp file only numeric
    content = "1.0\t2.0\t3.0\n4.0\t5.0\t6.0\n"
    file = tmp_path / "numeric_data.txt"
    file.write_text(content)

    result = detect_header_length(file)
    # No header, no empty lines → 0 - 1 - 0 = -1
    assert result == -1

#======================================================================#
#======================================================================#
#======================================================================#

class DummyApp:
    """Mock MainApp instance for testing."""
    def __init__(self, dataframes, header_lines):
        self.dataframes = dataframes if isinstance(dataframes, list) else [dataframes]
        self.header_lines = header_lines
        self.logger = MagicMock()


@patch("hyloa.data.io.clean_column_name")
@patch("hyloa.data.io.save_header")
@patch("hyloa.data.io.np.savetxt")
@patch("hyloa.data.io.QFileDialog.getSaveFileName")
@patch("hyloa.data.io.QMessageBox.information")
def test_save_to_file_success(
    mock_info, mock_dialog, mock_savetxt, mock_save_header, mock_clean_col, tmp_path
):
    """Test successful save operation."""
    # Arrange
    test_df = pd.DataFrame({
        "A": [1.0, 2.0],
        "B": [3.0, 4.0]
    })
    test_df.attrs["filename"] = "test_file.txt"
    
    header_lines = ["# test header\n"]
    app_instance = DummyApp([test_df], header_lines)

    fake_file = tmp_path / "output.txt"
    mock_dialog.return_value = (str(fake_file), "")
    
    # Mock clean_column_name to return the column name unchanged for simplicity
    mock_clean_col.side_effect = lambda x, y: x

    # Act
    save_to_file(0, app_instance, parent_widget=None)

    # Assert: file dialog was called
    mock_dialog.assert_called_once()

    # Assert: save_header was called with correct arguments
    mock_save_header.assert_called_once()
    args = mock_save_header.call_args[0]
    
    assert args[0] == app_instance
    assert args[1] == "# test header\n"  
    assert isinstance(args[2], pd.DataFrame)
    assert args[3] == str(fake_file)

    # Assert: np.savetxt was called
    mock_savetxt.assert_called_once()
    savetxt_args = mock_savetxt.call_args[0]
    assert savetxt_args[1].shape == (2, 2)  # 2 rows, 2 columns

    # Assert: success message shown
    mock_info.assert_called_once()
    assert str(fake_file) in mock_info.call_args[0][2]


@patch("hyloa.data.io.QFileDialog.getSaveFileName")
@patch("hyloa.data.io.QMessageBox.warning")
def test_save_to_file_cancel(mock_warning, mock_dialog):
    """Test when user cancels the save dialog."""
    # Arrange: simulate user cancels dialog
    mock_dialog.return_value = ("", "")
    
    test_df = pd.DataFrame({"A": [1, 2]})
    test_df.attrs["filename"] = "test.txt"
    
    app = DummyApp([test_df], ["# header\n"])

    # Act
    save_to_file(0, app, parent_widget=None)

    # Assert: warning called, operation cancelled
    mock_warning.assert_called_once()
    assert "Canceled" in mock_warning.call_args[0][1]


@patch("hyloa.data.io.clean_column_name")
@patch("hyloa.data.io.save_header")
@patch("hyloa.data.io.np.savetxt")
@patch("hyloa.data.io.QFileDialog.getSaveFileName")
@patch("hyloa.data.io.QMessageBox.information")
def test_save_to_file_adds_txt_extension(
    mock_info, mock_dialog, mock_savetxt, mock_save_header, mock_clean_col, tmp_path
):
    """Test that .txt extension is added if missing."""
    # Arrange
    test_df = pd.DataFrame({"A": [1.0, 2.0]})
    test_df.attrs["filename"] = "test.txt"
    
    app_instance = DummyApp([test_df], ["# header\n"])
    
    fake_file = tmp_path / "output"  # without .txt extension
    mock_dialog.return_value = (str(fake_file), "")
    mock_clean_col.side_effect = lambda x, y: x

    # Act
    save_to_file(0, app_instance, parent_widget=None)

    # Assert: .txt extension was added
    args = mock_save_header.call_args[0]
    file_path = args[3]
    assert file_path.endswith(".txt")


@patch("hyloa.data.io.clean_column_name")
@patch("hyloa.data.io.save_header")
@patch("hyloa.data.io.np.savetxt", side_effect=IOError("Permission denied"))
@patch("hyloa.data.io.QFileDialog.getSaveFileName")
@patch("hyloa.data.io.QMessageBox.critical")
def test_save_to_file_error_handling(
    mock_critical, mock_dialog, mock_savetxt, mock_save_header, mock_clean_col
):
    """Test error handling when save fails."""
    # Arrange
    test_df = pd.DataFrame({"A": [1.0, 2.0]})
    test_df.attrs["filename"] = "test.txt"

    app_instance = DummyApp([test_df], ["# header\n"])

    mock_dialog.return_value = ("/path/to/file.txt", "")
    mock_clean_col.side_effect = lambda x, y: x

    # Act
    save_to_file(0, app_instance, parent_widget=None)

    # Assert
    mock_critical.assert_called_once()
    _, _, error_message = mock_critical.call_args[0]
    
    assert "Error while saving" in error_message

@patch("hyloa.data.io.clean_column_name")
@patch("hyloa.data.io.save_header")
@patch("hyloa.data.io.np.savetxt")
@patch("hyloa.data.io.QFileDialog.getSaveFileName")
@patch("hyloa.data.io.QMessageBox.information")
def test_save_to_file_correct_dataframe_passed(
    mock_info, mock_dialog, mock_savetxt, mock_save_header, mock_clean_col
):
    """Test that the correct dataframe is passed to save_header."""
    # Arrange
    test_df = pd.DataFrame({
        "col1": [1.0, 2.0],
        "col2": [3.0, 4.0],
        "col3": [5.0, 6.0]
    })
    test_df.attrs["filename"] = "source_file.txt"
    
    app_instance = DummyApp([test_df], ["# header\n"])
    
    mock_dialog.return_value = ("/tmp/output.txt", "")
    mock_clean_col.side_effect = lambda x, y: f"cleaned_{x}"

    # Act
    save_to_file(0, app_instance, parent_widget=None)

    # Assert: save_header received the dataframe with cleaned columns
    args = mock_save_header.call_args[0]
    df_passed = args[2]
    
    expected_cols = ["cleaned_col1", "cleaned_col2", "cleaned_col3"]
    assert list(df_passed.columns) == expected_cols



def test_save_header_success(tmp_path):
    # Arrange
    df = pd.DataFrame({
        "col1": ["val1", "val2"],
        "col2": ["val3", np.nan],
    })
    app = DummyApp(None, None)
    file_path = tmp_path / "output.txt"
    header = ["# This is a header line\n"]
    # Call
    save_header(app, header ,df, str(file_path))

    # Assert
    assert file_path.exists()

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    

    assert lines[0].strip() == "col1\tcol2"
    

    # Logger call
    app.logger.info.assert_called_with(f"File saved successfully in: {file_path}")


def test_save_header_exception(tmp_path):
    
    app = DummyApp(None, None)
    bad_path = tmp_path / "nonexistent" / "file.txt"
    df = pd.DataFrame({"col": ["val"]})
    header = ["# header\n"]
    # Call
    save_header(app, header, df, str(bad_path))

    # Assert "Error while saving"
    called_msg = app.logger.info.call_args[0][0]
    assert "Error while saving" in called_msg


def test_duplicate_file_success(tmp_path):
    # create a tmp file
    original_file = tmp_path / "example.txt"
    original_file.write_text("Test content")

    expected_copy = tmp_path / "example_copy.txt"

    with patch("hyloa.data.io.QFileDialog.getOpenFileName") as mock_dialog, \
         patch("hyloa.data.io.QMessageBox.information") as mock_info, \
         patch("hyloa.data.io.QMessageBox.critical") as mock_critical :

        mock_dialog.return_value = (str(original_file), "Text Files (*.txt)")

        # Call
        duplicate_file()

        # Assert
        assert expected_copy.exists()
        assert expected_copy.read_text() == "Test content"
        mock_info.assert_called_once()
        mock_critical.assert_not_called()

def test_duplicate_file_cancel():
    with patch("hyloa.data.io.QFileDialog.getOpenFileName") as mock_dialog, \
         patch("hyloa.data.io.QMessageBox.information") as mock_info, \
         patch("hyloa.data.io.QMessageBox.critical") as mock_critical:

        mock_dialog.return_value = ("", "")  # Cancel dialog
        duplicate_file()

        mock_info.assert_not_called()
        mock_critical.assert_not_called()