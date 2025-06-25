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
@patch("hyloa.data.io.open", side_effect=Exception("Test error"))
def test_load_files_open_raises(mock_open_fn, mock_critical, mock_getfiles, fake_app):
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
    """Fake app_instance with minimal structure."""
    def __init__(self, dataframe, header_lines):
        self.dataframes = [dataframe]
        self.header_lines = [header_lines]
        self.logger = MagicMock()


@patch("hyloa.data.io.QFileDialog.getSaveFileName")
@patch("hyloa.data.io.QMessageBox.information")
@patch("hyloa.data.io.QMessageBox.warning")
@patch("hyloa.data.io.QMessageBox.critical")
@patch("hyloa.data.io.save_header")
def test_save_to_file_success(mock_save_header, mock_critical, mock_warning, mock_info, mock_dialog, tmp_path):
    # Arrange
    test_df = pd.DataFrame({
        "A": [1.0, 2.0],
        "B": [3.0, 4.0]
    })
    header_lines = ["# test header\n"]
    app_instance = DummyApp(test_df, header_lines)

    fake_file = tmp_path / "output.txt"
    mock_dialog.return_value = (str(fake_file), "Text file (*.txt)")

    # Call function to test
    save_to_file(0, app_instance, parent_widget=None)

    # Assert all is working fine
    assert fake_file.exists()

    with open(fake_file, encoding="utf-8") as f:
        content = f.read()
        assert "1.0" in content
        assert "3.0" in content

    # Assert: save_header was called
    mock_save_header.assert_called_once_with(app_instance, header_lines, str(fake_file))
    mock_info.assert_called_once()
    mock_warning.assert_not_called()
    mock_critical.assert_not_called()


@patch("hyloa.data.io.QFileDialog.getSaveFileName")
@patch("hyloa.data.io.QMessageBox.warning")
def test_save_to_file_cancel(mock_warning, mock_dialog):
    # Arrange: simulate user cancels dialog
    mock_dialog.return_value = ("", "")
    df = pd.DataFrame({"A": [1, 2]})
    app = DummyApp(df, ["# header\n"])

    # Act
    save_to_file(0, app, parent_widget=None)

    # Assert: warning called, no file created
    mock_warning.assert_called_once()



def test_save_header_success(tmp_path):
    # Arrange
    df = pd.DataFrame({
        "col1": ["val1", "val2"],
        "col2": ["val3", np.nan],
    })
    app = DummyApp(None, None)
    file_path = tmp_path / "output.txt"

    # Call
    save_header(app, df, str(file_path))

    # Assert
    assert file_path.exists()

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert lines[0].strip() == "col1\tcol2"
    assert lines[1].strip() == "val1\tval3"
    assert lines[2].strip() == "val2"  # la col2 era NaN → deve risultare vuoto

    # Logger call
    app.logger.info.assert_called_with(f"File saved successfully in: {file_path}")


def test_save_header_exception(tmp_path):
    
    app = DummyApp(None, None)
    bad_path = tmp_path / "nonexistent" / "file.txt"
    df = pd.DataFrame({"col": ["val"]})

    # Call
    save_header(app, df, str(bad_path))

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