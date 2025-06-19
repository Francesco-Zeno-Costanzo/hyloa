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
        if isinstance(btn, QPushButton) and btn.text() == "Applica":
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
    assert "numero pari di colonne" in args[2]


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