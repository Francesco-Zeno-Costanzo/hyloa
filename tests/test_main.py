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
Test entry point
"""
import pytest
from PyQt5.QtWidgets import QApplication

from hyloa.main import main
from hyloa.gui.main_window import MainApp

@pytest.fixture(scope="module")
def app():
    """ Create a single QApplication for all module tests.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_launch(app):
    """ Verify that the main window is created correctly.
    """
    window = MainApp()
    
    assert window is not None
    assert window.windowTitle() == "Hysteresis Loop Analyzer"
    
    # Verify that the MDI area is set correctly
    assert window.centralWidget() is window.mdi_area

    # Close the window after the test
    window.close()


def test_main_entrypoint(monkeypatch):
    """ Test that main starts without errors (without launching app.exec_()).
    """
    # Block app.exec_() to prevent the interactive GUI from starting
    class DummyApp:
        def __init__(self, *args):
            pass
        def exec_(self): return 0

    monkeypatch.setattr("hyloa.main.QApplication", DummyApp)
    monkeypatch.setattr("hyloa.main.MainApp", lambda: None)

    with pytest.raises(SystemExit) as e:
        main()
    assert e.value.code == 0