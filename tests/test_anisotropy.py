import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch

from hyloa.data.anisotropy import *

#==================================================================#
# Auxiliar function for mock all inputs                            #
#==================================================================#

@pytest.fixture
def mock_combo():
    combo = MagicMock()
    combo.currentIndex.return_value = 0
    combo.currentText.return_value = "H"
    return combo

@pytest.fixture
def mock_save_combo_no_save():
    combo = MagicMock()
    combo.currentIndex.return_value = 0  # No save
    return combo

@pytest.fixture
def mock_save_combo_file1():
    combo = MagicMock()
    combo.currentIndex.return_value = 1  # File 1
    return combo

@pytest.fixture
def mock_lineedit():
    le = MagicMock()
    le.text.return_value = "0.0"
    return le

@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_window():
    return MagicMock()


@pytest.fixture
def mock_draw_plot():
    return MagicMock()

@pytest.fixture
def mock_thr_edit():
    edit = MagicMock()
    edit.text.return_value = "0.05"
    return edit

@pytest.fixture
def mock_window():
    return MagicMock()


@pytest.fixture
def mock_output_box():
    box = MagicMock()
    return box


@pytest.fixture
def valid_plot_state():
    x    = np.linspace(-10, 10, 50)
    y_up = np.tanh(x)
    y_dw = -np.tanh(x)

    return {
        "x_up_corr": x,
        "y_up_corr": y_up,
        "x_dw_corr": x,
        "y_dw_corr": y_dw,
        "e_up": np.full_like(x, 0.01),
        "e_dw": np.full_like(x, 0.01),
        "fit_hc_n": None,
        "fit_hc_p": None,
        "done_spl3": False,
        "spline_up": None,
        "spline_dw": None,
    }

@pytest.fixture
def plot_state_with_splines():
    x = np.linspace(-10, 10, 5000)

    # Up / down branches with small difference near saturation
    y_up = np.tanh(x)
    y_dw = np.tanh(x) * 0.98

    return {
        "spline_up": (x, y_up),
        "spline_dw": (x, y_dw),
    }

@pytest.fixture
def plot_state_with_splines_and_corr():
    x = np.linspace(-10, 10, 500)
    y_up = np.tanh(x)
    y_dw = np.tanh(x) * 0.95

    return {
        "spline_up": (x, y_up),
        "spline_dw": (x, y_dw),
        "x_up_corr": x,
        "x_dw_corr": x,
        "y_up_corr": y_up,
        "y_dw_corr": y_dw,
    }

@pytest.fixture
def dataframes():
    df1 = pd.DataFrame({
        "H": np.zeros(500),
        "M": np.zeros(500),
    })

    df2 = pd.DataFrame({
        "H": np.zeros(500),
        "M": np.zeros(500),
    })

    return [df1, df2]

#==================================================================#
# Tests                                                            #
#==================================================================#


def test_compute_b_spline_success(
    mock_combo, mock_lineedit, mock_logger, mock_window, mock_draw_plot, valid_plot_state):
    # Act
    compute_b_spline(
        mock_combo, mock_combo, mock_combo,
        mock_combo, mock_combo,
        mock_lineedit, mock_lineedit,
        valid_plot_state,
        mock_logger,
        mock_window,
        mock_draw_plot
    )

    # Assert
    assert valid_plot_state["done_spl3"] is True
    assert valid_plot_state["spline_up"] is not None
    assert valid_plot_state["spline_dw"] is not None

    x_up, y_up = valid_plot_state["spline_up"]
    x_dw, y_dw = valid_plot_state["spline_dw"]

    assert len(x_up) == 5000
    assert len(y_up) == 5000
    assert len(x_dw) == 5000
    assert len(y_dw) == 5000

    mock_draw_plot.assert_called_once()
    mock_logger.info.assert_called_once()


@patch("hyloa.data.correction.QMessageBox.critical")
def test_compute_b_spline_negative_smoothing(
    mock_msgbox, mock_combo, mock_lineedit, mock_logger, mock_window, mock_draw_plot,
    valid_plot_state):

    mock_lineedit.text.return_value = "-1.0"

    compute_b_spline(
        mock_combo, mock_combo, mock_combo,
        mock_combo, mock_combo,
        mock_lineedit, mock_lineedit,
        valid_plot_state,
        mock_logger,
        mock_window,
        mock_draw_plot
    )

    mock_msgbox.assert_called_once()
    mock_draw_plot.assert_not_called()
    assert valid_plot_state["done_spl3"] is False


@patch("hyloa.data.correction.QMessageBox.critical")
def test_compute_b_spline_without_correction(
    mock_msgbox, mock_combo, mock_lineedit, mock_logger, mock_window, mock_draw_plot):
    plot_state = {
        "x_up_corr": None,
        "y_up_corr": None,
        "x_dw_corr": None,
        "y_dw_corr": None,
        "e_up": None,
        "e_dw": None,
    }

    compute_b_spline(
        mock_combo, mock_combo, mock_combo,
        mock_combo, mock_combo,
        mock_lineedit, mock_lineedit,
        plot_state,
        mock_logger,
        mock_window,
        mock_draw_plot
    )

    mock_msgbox.assert_called_once()
    mock_draw_plot.assert_not_called()


def test_compute_hk_success(
    mock_combo, mock_thr_edit, mock_logger, mock_window, mock_output_box, plot_state_with_splines):

    compute_Hk(
        mock_combo, mock_combo, mock_combo, mock_combo, mock_combo,
        mock_thr_edit, plot_state_with_splines, mock_logger, mock_window,
        mock_output_box
    )

    # Output box updated
    mock_output_box.setPlainText.assert_called_once()
    text = mock_output_box.setPlainText.call_args[0][0]

    assert "Negative anisotropy field" in text
    assert "Positive anisotropy field" in text
    assert "Mean:" in text

    # Logger called
    mock_logger.info.assert_called_once()

@patch("hyloa.data.correction.QMessageBox.critical")
def test_compute_hk_missing_splines(
    mock_msgbox, mock_combo, mock_thr_edit, mock_logger, mock_window, mock_output_box):

    plot_state = {
        "spline_up": None,
        "spline_dw": None,
    }

    compute_Hk(
        mock_combo, mock_combo, mock_combo, mock_combo, mock_combo,
        mock_thr_edit, plot_state, mock_logger, mock_window,
        mock_output_box
    )

    mock_msgbox.assert_called_once()
    mock_output_box.setPlainText.assert_not_called()

@patch("hyloa.data.correction.QMessageBox.critical")
def test_compute_hk_invalid_threshold(
    mock_msgbox, mock_combo, mock_logger, mock_window, mock_output_box, plot_state_with_splines):
    
    bad_thr = MagicMock()
    bad_thr.text.return_value = "not_a_number"

    compute_Hk(
        mock_combo, mock_combo, mock_combo, mock_combo, mock_combo,
        bad_thr, plot_state_with_splines, mock_logger, mock_window,
        mock_output_box
    )

    mock_msgbox.assert_called_once()
    mock_output_box.setPlainText.assert_not_called()


def test_symmetrize_with_save(
    mock_combo, mock_save_combo_file1, mock_logger, mock_draw_plot,
    mock_window, plot_state_with_splines_and_corr, dataframes):

    # Dest columns
    x_up_dest = MagicMock()
    y_up_dest = MagicMock()
    x_dw_dest = MagicMock()
    y_dw_dest = MagicMock()

    x_up_dest.currentText.return_value = "H"
    y_up_dest.currentText.return_value = "M"
    x_dw_dest.currentText.return_value = "H"
    y_dw_dest.currentText.return_value = "M"

    symmetrize(
        mock_combo, mock_save_combo_file1,
        mock_combo, mock_combo, mock_combo, mock_combo,
        x_up_dest, y_up_dest, x_dw_dest, y_dw_dest,
        dataframes, mock_logger, plot_state_with_splines_and_corr,
        mock_draw_plot, mock_window
    )

    df_dest = dataframes[0]

    assert not np.all(df_dest["H"] == 0)
    assert not np.all(df_dest["M"] == 0)

    mock_logger.info.assert_called()
