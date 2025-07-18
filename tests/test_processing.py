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
Test data Processing
"""
import pytest
import numpy as np
import pandas as pd

from unittest.mock import patch, MagicMock
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QCheckBox
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt


from hyloa.data.processing import *

@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@patch("hyloa.data.processing.apply_norm")
def test_norm_dialog_even_columns(mock_apply_norm, qapp):
    # Create a dummy DataFrame with 4 columns (2 x columns, 2 y columns)
    df = pd.DataFrame(np.random.rand(10, 4), columns=["X1", "Y1", "X2", "Y2"])
    
    # Mock the app instance with one DataFrame
    app_instance = MagicMock()
    app_instance.dataframes = [df]

    # Dummy QWidget as parent
    plot_instance = QWidget()

    # Patch QDialog.exec_ to allow dialog interaction
    with patch("PyQt5.QtWidgets.QDialog.exec_", side_effect=lambda self=None: _click_apply_button()):
        norm_dialog(plot_instance, app_instance)

    # Check that apply_norm was called once
    assert mock_apply_norm.called
    args, _ = mock_apply_norm.call_args

    assert args[2] == 0  # selected file index
    assert args[3] == ["Y1", "Y2"]  # selected columns

    # I don't know but work
    del df, app_instance, plot_instance


# Helper to simulate clicking checkboxes and the apply button
def _click_apply_button():
    # Find all checkboxes and click them if their text starts with Y
    for cb in QApplication.allWidgets():
        if isinstance(cb, QCheckBox) and cb.text().startswith("Y"):
            cb.setChecked(True)
    
    # Find the "Applica" button and click it
    for btn in QApplication.allWidgets():
        if isinstance(btn, QPushButton) and btn.text() == "Apply":
            QTest.mouseClick(btn, Qt.LeftButton)
            break
    return 1 # simulate dialog accepted

@patch("PyQt5.QtWidgets.QMessageBox.critical")
def test_norm_dialog_odd_columns(mock_critical, qapp):
    # Create a dummy DataFrame with 3 columns (2 x, 1 y)
    df = pd.DataFrame(np.random.rand(10, 3), columns=["X1", "Y1", "X2"])
    
    app_instance = MagicMock()
    app_instance.dataframes = [df]

    plot_instance = QWidget()

    # Patch exec_ to click only one checkbox (Y1)
    with patch("PyQt5.QtWidgets.QDialog.exec_", side_effect=lambda self=None: _click_apply_button()):
        norm_dialog(plot_instance, app_instance)

    # Check that error message was shown
    assert mock_critical.called
    args, _ = mock_critical.call_args
    assert "even number of columns" in args[2]


@patch("hyloa.data.processing.apply_loop_closure")
def test_close_loop_dialog(mock_apply_loop_closure, qapp):
    # Create a dummy DataFrame with 4 columns (2 x columns, 2 y columns)
    df = pd.DataFrame(np.random.rand(10, 4), columns=["X1", "Y1", "X2", "Y2"])
    
    # Mock the app instance with one DataFrame
    app_instance = MagicMock()
    app_instance.dataframes = [df]

    # Dummy QWidget as parent
    plot_instance = QWidget()

    # Patch QDialog.exec_ to allow dialog interaction
    with patch("PyQt5.QtWidgets.QDialog.exec_", side_effect=lambda self=None: _click_apply_button()):
        close_loop_dialog(plot_instance, app_instance)

    # Check that apply_loop_closure was called once
    assert mock_apply_loop_closure.called
    args, _ = mock_apply_loop_closure.call_args

    assert args[2] == 0  # selected file index
    assert args[3] == ["Y1", "Y2"]  # selected columns



@patch("hyloa.data.processing.QMessageBox.information")
def test_apply_norm_applies_normalization(mock_info):
    # Data simulation
    x = np.linspace(-1, 1, 200)  # Magnetic field
    np.random.seed(69420)        # For reproducibility
    noise = np.random.normal(0, 0.0005, size=x.shape)  # Gaussian error
    """
    # Creation of the two branches of the hysteresis loop
    # The sigmoid function is used to simulate the hysteresis loop
    # The noise is added to simulate the experimental error
    # The last term is a linear trend to simulate a drift
    # The -0.003 is due to the fact that the loop is always closed at one of the extreme points.
    """
    y_up = 0.025 + 0.015 * (1 / (1 + np.exp(-10 * (x-0.25)))) + noise + (0.003*x - 0.003)
    y_dw = 0.025 + 0.015 * (1 / (1 + np.exp( 10 * (x-0.25))))[::-1] + noise[::-1]

    df = pd.DataFrame({"Y1": y_up, "Y2": y_dw})

    # Create mock app_instance with logger and dataframes
    mock_logger = MagicMock()
    app_instance = MagicMock()
    app_instance.dataframes = [df.copy()]  # Use a copy to verify modification
    app_instance.logger = mock_logger

    # Create mock plot_instance with a plot method
    plot_instance = MagicMock()

    # Apply normalization
    apply_norm(plot_instance, app_instance, file_index=0, selected_cols=["Y1", "Y2"])

    # Assert that values have been updated in the dataframe
    normed_y1 = app_instance.dataframes[0]["Y1"].values
    normed_y2 = app_instance.dataframes[0]["Y2"].values
    ampl_up   = abs(np.mean(normed_y1[:5])  + np.mean(normed_y2[:5]))/2
    ampl_dw   = abs(np.mean(normed_y1[-5:]) + np.mean(normed_y2[-5:]))/2
    assert ampl_up == pytest.approx(1, rel=1e-5)
    assert ampl_dw == pytest.approx(1, rel=1e-5)

    # Assert that plot was called
    plot_instance.plot.assert_called_once()

    # Assert that logger.info was called at least once for each column
    assert mock_logger.info.call_count == 2
    mock_logger.info.assert_any_call("Normalization applied to Y1.")
    mock_logger.info.assert_any_call("Normalization applied to Y2.")

    # Assert that success message was shown
    mock_info.assert_called_once()
    args, _ = mock_info.call_args
   
    assert "Normalization applied on File 1" in args[2]

@patch("hyloa.data.processing.QMessageBox.critical")
def test_apply_norm_handles_exception(mock_critical):
    # App instance with no dataframe
    app_instance = MagicMock()
    app_instance.logger = MagicMock()
    app_instance.dataframes = [None]  

    # Create mock plot_instance with a plot method
    plot_instance = MagicMock()

    # selected_cols
    selected_cols = ["Y1", "Y2"]

    # Try to apply normalization
    apply_norm(plot_instance, app_instance, file_index=0, selected_cols=selected_cols)

    # Assert failure message
    mock_critical.assert_called_once()
    args, _ = mock_critical.call_args
    assert "Error during normalization" in args[2]


@patch("hyloa.data.processing.QMessageBox.information")
def test_apply_loop_closure_success(mock_info):

    # Data simulation
    x = np.linspace(-1, 1, 200)  # Magnetic field
    np.random.seed(69420)        # For reproducibility
    noise = np.random.normal(0, 0.0005, size=x.shape)  # Gaussian error
    """
    # Creation of the two branches of the hysteresis loop
    # The sigmoid function is used to simulate the hysteresis loop
    # The noise is added to simulate the experimental error
    # The last term is a linear trend to simulate a drift
    # The -0.003 is due to the fact that the loop is always closed at one of the extreme points.
    """
    y_up = 0.025 + 0.015 * (1 / (1 + np.exp(-10 * (x-0.25)))) + noise + (0.003*x - 0.003)
    y_dw = 0.025 + 0.015 * (1 / (1 + np.exp( 10 * (x-0.25))))[::-1] + noise[::-1]

    # Create a sample dataframe with a simple loop structure
    df = pd.DataFrame({
        "Y1": y_up,
        "Y2": y_dw
    })

    # Prepare the mock application instance
    app_instance = MagicMock()
    app_instance.logger = MagicMock()
    app_instance.dataframes = [df.copy()]

    # Plot instance mock
    plot_instance = MagicMock()

    # Call the function
    apply_loop_closure(plot_instance, app_instance, file_index=0, selected_cols=["Y1", "Y2"])

    # Ensure that values have been updated
    assert app_instance.dataframes[0]["Y1"].values[0] == pytest.approx(
           app_instance.dataframes[0]["Y2"].values[0], rel=1e-3)

    # Check that the plot was called
    plot_instance.plot.assert_called_once()

    # Check if the success message was shown
    mock_info.assert_called_once()
    args, _ = mock_info.call_args
    assert "Closure applied on File 1" in args[2]

@patch("hyloa.data.processing.QMessageBox.information")
def test_applay_inversion(mock_info):
    # Data simulation
    x = np.linspace(-1, 1, 200)  # Magnetic field
    np.random.seed(69420)        # For reproducibility
    noise = np.random.normal(0, 0.0005, size=x.shape)  # Gaussian error
    """
    # Creation of the two branches of the hysteresis loop
    # The sigmoid function is used to simulate the hysteresis loop
    # The noise is added to simulate the experimental error
    # The last term is a linear trend to simulate a drift
    # The -0.003 is due to the fact that the loop is always closed at one of the extreme points.
    """
    y_up = 0.025 + 0.015 * (1 / (1 + np.exp(-10 * (x-0.25)))) + noise + (0.003*x - 0.003)
    y_dw = 0.025 + 0.015 * (1 / (1 + np.exp( 10 * (x-0.25))))[::-1] + noise[::-1]

    # Create a sample dataframe with a simple loop structure
    df = pd.DataFrame({
        "X1": x,
        "Y1": y_up,
        "X2": x,
        "Y2": y_dw
    })

    # Prepare the mock application instance
    app_instance = MagicMock()
    app_instance.logger = MagicMock()
    app_instance.dataframes = [df.copy()]

    # Plot instance mock
    plot_instance = MagicMock()


    # Mock combo box for column names
    x_combo1 = MagicMock()
    x_combo1.currentText.return_value = "X1"
    y_combo1 = MagicMock()
    y_combo1.currentText.return_value = "Y1"
    x_combo2 = MagicMock()
    x_combo2.currentText.return_value = "X2"
    y_combo2 = MagicMock()
    y_combo2.currentText.return_value = "Y2"

    selected_pairs = [("", x_combo1, y_combo1), ("", x_combo2, y_combo2)]

    # Call the function
    apply_inversion("both", 0, selected_pairs, app_instance.dataframes, 
                    app_instance.logger, plot_instance)

    # Ensure that values have been updated
    assert np.all(app_instance.dataframes[0]["Y1"].values == -y_up)
    assert np.all(app_instance.dataframes[0]["Y2"].values == -y_dw)
    assert np.all(app_instance.dataframes[0]["X1"].values == -x)
    assert np.all(app_instance.dataframes[0]["X2"].values == -x)

    # Check logger
    app_instance.logger.info.assert_any_call("Flip x-axis -> column X1.")
    app_instance.logger.info.assert_any_call("Flip y-axis -> column Y1.")
    app_instance.logger.info.assert_any_call("Flip x-axis -> column X2.")
    app_instance.logger.info.assert_any_call("Flip y-axis -> column Y2.")
            
    # Check that the plot was called
    plot_instance.plot.assert_called_once()

    # Check if the success message was shown
    mock_info.assert_called_once()
    args, _ = mock_info.call_args
    assert "Axis flip BOTH applied on File 1" in args[2]


@patch("hyloa.data.processing.QMessageBox.information")
@patch("hyloa.data.processing.QMessageBox.warning")
def test_apply_column_inversion_valid(mock_warning, mock_info):
    
    # Data simulation
    x = np.linspace(-1, 1, 200)  # Magnetic field
    np.random.seed(69420)        # For reproducibility
    noise = np.random.normal(0, 0.0005, size=x.shape)  # Gaussian error
    """
    # Creation of the two branches of the hysteresis loop
    # The sigmoid function is used to simulate the hysteresis loop
    # The noise is added to simulate the experimental error
    # The last term is a linear trend to simulate a drift
    # The -0.003 is due to the fact that the loop is always closed at one of the extreme points.
    """
    y_up = 0.025 + 0.015 * (1 / (1 + np.exp(-10 * (x-0.25)))) + noise + (0.003*x - 0.003)
    y_dw = 0.025 + 0.015 * (1 / (1 + np.exp( 10 * (x-0.25))))[::-1] + noise[::-1]

    # Create a sample dataframe with a simple loop structure
    df = pd.DataFrame({
        "X1": x,
        "Y1": y_up,
        "X2": x,
        "Y2": y_dw
    })

    # Simulate checkbox: 
    cb_x1 = MagicMock()
    cb_x1.isChecked.return_value = True
    cb_y1 = MagicMock()
    cb_y1.isChecked.return_value = True

    cb_x2 = MagicMock()
    cb_x2.isChecked.return_value = False
    cb_y2 = MagicMock()
    cb_y2.isChecked.return_value = False

    selected_columns = {
        "X1": cb_x1,
        "Y1": cb_y1,
        "X2": cb_x2,
        "Y2": cb_y2
    }

    # Prepare the mock application instance
    app_instance = MagicMock()
    app_instance.logger = MagicMock()
    app_instance.dataframes = [df.copy()]

    # Plot instance mock
    plot_instance = MagicMock()

    apply_column_inversion(0, selected_columns, app_instance.dataframes,
                            app_instance.logger, plot_instance)

    # Ensure that values have been updated
    assert np.all(app_instance.dataframes[0]["Y1"].values == -y_up)
    assert np.all(app_instance.dataframes[0]["Y2"].values == y_dw)
    assert np.all(app_instance.dataframes[0]["X1"].values == -x)
    assert np.all(app_instance.dataframes[0]["X2"].values == x)

    # Check logger
    app_instance.logger.info.assert_any_call("Reversing column X1 in file 1.")
    app_instance.logger.info.assert_any_call("Reversing column Y1 in file 1.")

    # Check that the plot was called
    plot_instance.plot.assert_called_once()

    # QMessageBox success 
    mock_info.assert_called_once()

    # QMessageBox warning not called
    mock_warning.assert_not_called()

@patch("hyloa.data.processing.QMessageBox.warning")
def test_apply_column_inversion_no_selection(mock_warning):
    df = pd.DataFrame({
        "A": [1.0, 2.0]
    })

    cb = MagicMock()
    cb.isChecked.return_value = False

    selected_columns = {"A": cb}
    dataframes = [df.copy()]
    logger = MagicMock()
    plot_instance = MagicMock()

    apply_column_inversion(0, selected_columns, dataframes, logger, plot_instance)

    # no inversion
    assert list(dataframes[0]["A"]) == [1.0, 2.0]

    # QMessageBox.warning 
    mock_warning.assert_called_once_with(plot_instance, "Error", "Select at least one column.")

    # plot not called
    plot_instance.plot.assert_not_called()
