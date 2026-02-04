import pytest
from unittest.mock import MagicMock, patch

from hyloa.data.correction import *

#==================================================================#
# Auxiliar function for mock all inputs                            #
#==================================================================#

@pytest.fixture
def mock_window():
    return MagicMock()

@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def mock_draw_plot():
    return MagicMock()

@pytest.fixture
def mock_combo():
    combo = MagicMock()
    combo.currentIndex.return_value = 0
    combo.currentText.return_value = "col"
    return combo

@pytest.fixture
def mock_double_branch():
    combo = MagicMock()
    combo.currentText.return_value = "No"
    return combo

@pytest.fixture
def mock_lineedit():
    le = MagicMock()
    le.text.return_value = "1.5"
    return le

@pytest.fixture
def mock_fit_data():
    return MagicMock()

@pytest.fixture
def base_plot_state():
    return {
        "done_corr": True,
        "done_spl3": True,
        "x_up": np.array([1., 2.]),
        "y_up": np.array([3., 4.]),
        "x_dw": np.array([1., 2.]),
        "y_dw": np.array([3., 4.]),
        "x_up_corr": np.array([1., 2.]),
        "y_up_corr": np.array([3., 4.]),
        "x_dw_corr": np.array([1., 2.]),
        "y_dw_corr": np.array([3., 4.]),
        "e_up": np.array([0.1, 0.1]),
        "e_dw": np.array([0.1, 0.1]),
        "fit_hc_p": 1.0,
        "fit_hc_n": -1.0,
        "spline_up": ([], []),
        "spline_dw": ([], []),
        "s_data_up": ([], []),
        "s_data_dw": ([], []),
    }

#==================================================================#
# Tests                                                            #
#==================================================================#

def test_change_ps_cp(base_plot_state, mock_window, mock_draw_plot):
    change_ps(
        plot_state=base_plot_state,
        window=mock_window,
        draw_plot=mock_draw_plot,
        mode="cp"
    )

    assert base_plot_state["done_corr"] is False
    assert base_plot_state["done_spl3"] is False

    assert base_plot_state["x_up_corr"] is None
    assert base_plot_state["y_up_corr"] is None
    assert base_plot_state["x_dw_corr"] is None
    assert base_plot_state["y_dw_corr"] is None

    assert base_plot_state["spline_up"] is None
    assert base_plot_state["spline_dw"] is None

    mock_draw_plot.assert_called_once()

def test_change_ps_od(base_plot_state, mock_window, mock_draw_plot):
    change_ps(
        plot_state=base_plot_state,
        window=mock_window,
        draw_plot=mock_draw_plot,
        mode="od"
    )

    assert base_plot_state["x_up"] is None
    assert base_plot_state["y_up"] is None
    assert base_plot_state["x_dw"] is None
    assert base_plot_state["y_dw"] is None

    mock_draw_plot.assert_called_once()

def test_change_ps_sym(base_plot_state, mock_window, mock_draw_plot):
    change_ps(
        plot_state=base_plot_state,
        window=mock_window,
        draw_plot=mock_draw_plot,
        mode="sym"
    )

    assert base_plot_state["s_data_up"] is None
    assert base_plot_state["s_data_dw"] is None

    mock_draw_plot.assert_called_once()

@patch("hyloa.data.correction.QMessageBox.critical")
def test_change_ps_exception(
    mock_msgbox,
    mock_window,
    mock_draw_plot
):
    plot_state = None  # causerà AttributeError

    change_ps(
        plot_state=plot_state,
        window=mock_window,
        draw_plot=mock_draw_plot,
        mode="cp"
    )

    mock_msgbox.assert_called_once()
    mock_draw_plot.assert_not_called()

def test_flip_from_false_to_true(base_plot_state, mock_window, mock_draw_plot):
    base_plot_state["flipped"] = False

    flip(base_plot_state, mock_window, mock_draw_plot)

    assert base_plot_state["flipped"] is True
    mock_draw_plot.assert_called_once()

from unittest.mock import patch

@patch("hyloa.data.correction.QMessageBox.critical")
def test_flip_exception(mock_msgbox, mock_window, mock_draw_plot):
    plot_state = None  # TypeError

    flip(base_plot_state, mock_window, mock_draw_plot)


    mock_msgbox.assert_called_once()
    mock_draw_plot.assert_not_called()

from unittest.mock import patch

@patch("hyloa.data.correction.QMessageBox.critical")
def test_flip_data_no_corrected_data(
    mock_msgbox, mock_combo, mock_double_branch,
    base_plot_state, mock_window, mock_logger, mock_draw_plot):

    base_plot_state["x_up_corr"] = None

    mock_data_sel = MagicMock()
    mock_data_sel.currentText.return_value = "Corrected"

    flip_data(
        mock_combo, mock_combo, mock_combo, mock_combo, mock_combo, mock_data_sel,
        mock_double_branch, base_plot_state, mock_window, mock_logger,
        mock_draw_plot
    )

    mock_msgbox.assert_called_once()
    mock_draw_plot.assert_not_called()

def test_flip_data_no_action(
    mock_combo, mock_double_branch, base_plot_state,
    mock_window, mock_logger, mock_draw_plot):

    mock_double_branch.currentText.return_value = "No"

    # Original State
    x_up_orig = base_plot_state["x_up_corr"].copy()

    mock_data_sel = MagicMock()
    mock_data_sel.currentText.return_value = "Corrected"

    flip_data(
        mock_combo, mock_combo, mock_combo, mock_combo, mock_combo, mock_data_sel,
        mock_double_branch, base_plot_state, mock_window, mock_logger,
        mock_draw_plot
    )

    assert (base_plot_state["x_up_corr"] == x_up_orig).all()
    mock_draw_plot.assert_not_called()

def test_flip_data_duplicate_up_branch(
    mock_combo, mock_double_branch, base_plot_state,
      mock_window, mock_logger, mock_draw_plot):
    
    mock_double_branch.currentText.return_value = "Up"

    x_up = base_plot_state["x_up_corr"].copy()
    y_up = base_plot_state["y_up_corr"].copy()
    e_up = base_plot_state["e_up"].copy()

    mock_data_sel = MagicMock()
    mock_data_sel.currentText.return_value = "Corrected"

    flip_data(
        mock_combo, mock_combo, mock_combo, mock_combo, mock_combo, mock_data_sel,
        mock_double_branch, base_plot_state, mock_window, mock_logger,
        mock_draw_plot
    )

    assert (base_plot_state["x_dw_corr"] == -x_up[::-1]).all()
    assert (base_plot_state["y_dw_corr"] == -y_up[::-1]).all()
    assert (base_plot_state["e_dw"] == e_up[::-1]).all()

    mock_draw_plot.assert_called_once()
    mock_logger.info.assert_called_once()

def test_apply_shift_ok(mock_lineedit,base_plot_state,mock_window,mock_fit_data):
    
    x_up_orig = base_plot_state["x_up_corr"].copy()
    x_dw_orig = base_plot_state["x_dw_corr"].copy()

    save_file_combo = MagicMock()
    save_file_combo.currentIndex.return_value = 0

    mock_data_sel = MagicMock()
    mock_data_sel.currentText.return_value = "Corrected"

    logger = MagicMock()

    apply_shift(
        MagicMock(), MagicMock(), MagicMock(), MagicMock(),
        MagicMock(),
        save_file_combo,
        mock_data_sel,
        mock_lineedit,
        base_plot_state,
        mock_window,
        mock_fit_data,
        args=("a", "b"),
        logger=logger
    )

    assert (base_plot_state["x_up_corr"] == x_up_orig - 1.5).all()
    assert (base_plot_state["x_dw_corr"] == x_dw_orig - 1.5).all()

    mock_fit_data.assert_called_once_with(*("a", "b"))

from unittest.mock import patch

@patch("hyloa.data.correction.QMessageBox.critical")
def test_apply_shift_invalid_value(
    mock_msgbox, mock_lineedit, base_plot_state, mock_window, mock_fit_data):

    mock_lineedit.text.return_value = "abc"

    save_file_combo = MagicMock()
    save_file_combo.currentIndex.return_value 

    mock_data_sel = MagicMock()
    mock_data_sel.currentText.return_value = "Corrected"

    logger = MagicMock()

    apply_shift(
        MagicMock(), MagicMock(), MagicMock(), MagicMock(),
        MagicMock(),
        save_file_combo,
        mock_data_sel,
        mock_lineedit,
        base_plot_state,
        mock_window,
        mock_fit_data,
        args=("a", "b"),
        logger=logger
    )

    mock_msgbox.assert_called_once()
    mock_fit_data.assert_not_called()

@patch("hyloa.data.correction.QMessageBox.critical")
def test_apply_shift_fit_raises(mock_msgbox, mock_lineedit, base_plot_state, mock_window):

    x_up_orig = base_plot_state["x_up_corr"].copy()
    x_dw_orig = base_plot_state["x_dw_corr"].copy()

    def failing_fit(*args):
        raise RuntimeError("fit failed")

    save_file_combo = MagicMock()
    save_file_combo.currentIndex.return_value 

    mock_data_sel = MagicMock()
    mock_data_sel.currentText.return_value = "Corrected"

    logger = MagicMock()

    apply_shift(
        MagicMock(), MagicMock(), MagicMock(), MagicMock(),
        MagicMock(),
        save_file_combo,
        mock_data_sel,
        mock_lineedit,
        base_plot_state,
        mock_window,
        failing_fit,
        args=("a", "b"),
        logger=logger
    )

    assert (base_plot_state["x_up_corr"] == x_up_orig).all()
    assert (base_plot_state["x_dw_corr"] == x_dw_orig).all()

    mock_msgbox.assert_called_once()

