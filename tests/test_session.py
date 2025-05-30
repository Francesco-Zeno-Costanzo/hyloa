import os
import pickle
import pytest
from unittest.mock import Mock, patch, MagicMock

from hyloa.data.session import save_current_session
from hyloa.data.session import load_previous_session

@pytest.fixture
def fake_app_instance():
    """Fake app_instance with all required attributes."""
    app              = MagicMock()
    app.logger       = "dummy_logger"
    app.dataframes   = {"df1": "data"}
    app.header_lines = ["#header"]
    app.logger_path  = "/path/to/log.txt"
    app.fit_results  = {"fit": "results"}
    app.number_plots = 1

    # plot_widgets with selected_pairs and plot_customizations
    combo_mock = MagicMock()
    combo_mock.currentText.side_effect = ["f", "x", "y"]
    plot_widget = MagicMock()
    plot_widget.selected_pairs = [(combo_mock, combo_mock, combo_mock)]
    plot_widget.plot_customizations.copy.return_value = {"style": "custom"}
    app.plot_widgets = {0: plot_widget}

    app.plot_names = {0: "Plot 0"}

    subwindow_mock                          = MagicMock()
    subwindow_mock.x.return_value           = 0
    subwindow_mock.y.return_value           = 0
    subwindow_mock.width.return_value       = 400
    subwindow_mock.height.return_value      = 300
    subwindow_mock.isMinimized.return_value = False

    app.plot_subwindows   = {0: subwindow_mock}
    app.figure_subwindows = {0: subwindow_mock}

    return app


def test_save_fails_without_logger(fake_app_instance):
    fake_app_instance.logger = None

    with patch("hyloa.data.session.QMessageBox.critical") as critical_mock:
        save_current_session(fake_app_instance)
        critical_mock.assert_called_once()
        assert "log" in critical_mock.call_args[0][2]  # check error text includes "log"


def test_save_cancelled_by_user(fake_app_instance):
    with patch("hyloa.data.session.QFileDialog.getSaveFileName", return_value=("", "")), \
         patch("hyloa.data.session.QMessageBox.warning") as warning_mock:
        save_current_session(fake_app_instance)
        warning_mock.assert_called_once()
        assert "Nessun file" in warning_mock.call_args[0][2]


def test_save_successful(tmp_path, fake_app_instance):
    test_file = tmp_path / "test_session.pkl"

    with patch("hyloa.data.session.QFileDialog.getSaveFileName", return_value=(str(test_file), "")), \
         patch("hyloa.data.session.QMessageBox.information") as info_mock:
        
        save_current_session(fake_app_instance)

        # Check file exists and is a valid pickle
        assert test_file.exists()
        with open(test_file, "rb") as f:
            data = pickle.load(f)
        
        assert isinstance(data, dict)
        assert "dataframes" in data
        info_mock.assert_called_once()


def test_save_raises_exception(fake_app_instance):
    # Force pickle to raise exception by mocking open
    with patch("hyloa.data.session.QFileDialog.getSaveFileName", return_value=("fake.pkl", "")), \
         patch("hyloa.data.session.QMessageBox.information"), \
         patch("hyloa.data.session.QMessageBox.critical") as critical_mock, \
         patch("builtins.open", side_effect=OSError("fail")):

        save_current_session(fake_app_instance)
        critical_mock.assert_called_once()
        assert "Errore" in critical_mock.call_args[0][2]



@patch("hyloa.data.session.QMessageBox.warning")
@patch("hyloa.data.session.QFileDialog.getOpenFileName", return_value=("", ""))
def test_load_session_cancelled(mock_get_open, mock_warning):
    fake_app = MagicMock()
    
    load_previous_session(fake_app)
    
    mock_warning.assert_called_once()
    mock_get_open.assert_called_once()

@patch("hyloa.data.session.QMessageBox.information")
@patch("hyloa.data.session.PlotControlWidget")
@patch("hyloa.data.session.PlotSubWindow")
@patch("hyloa.data.session.pickle.load")
@patch("builtins.open", create=True)
@patch("hyloa.data.session.QFileDialog.getOpenFileName")
def test_load_session_success(mock_get_open, mock_open, mock_pickle_load,
                               mock_plotsub, mock_plotctrl, mock_info):
    
    mock_get_open.return_value = ("dummy_path.pkl", "")
    
    
    fake_session = {
        "dataframes": ["df1", "df2"],
        "header_lines": ["h1"],
        "fit_results": {"result": 42},
        "number_plots": 2,
        "plot_widgets": {
            "0": {
                "selected_pairs": [("file.csv", "x", "y")],
                "plot_customizations": {"color": "red"}
            }
        },
        "plot_names": {
            0: "Grafico 0"
        },
        "log_filename": "log.txt"
    }
    mock_pickle_load.return_value = fake_session

    # Finto app
    fake_app = MagicMock()
    fake_app.mdi_area = MagicMock()
    fake_app.figure_subwindows = {}

    load_previous_session(fake_app)

  
    mock_open.assert_called_with("dummy_path.pkl", "rb")


    assert fake_app.dataframes == ["df1", "df2"]
    assert fake_app.header_lines == ["h1"]
    assert fake_app.fit_results == {"result": 42}
    assert fake_app.number_plots == 2

    
    mock_info.assert_called_once()


@patch("hyloa.data.session.QMessageBox.critical")
@patch("hyloa.data.session.pickle.load", side_effect=Exception("Errore fittizio"))
@patch("builtins.open", create=True)
@patch("hyloa.data.session.QFileDialog.getOpenFileName")
def test_load_session_exception(mock_get_open, mock_open, mock_pickle_load, mock_critical):
    mock_get_open.return_value = ("dummy_path.pkl", "")
    fake_app = MagicMock()

    load_previous_session(fake_app)

    mock_critical.assert_called_once()
