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
Test log window widget.
"""
import os
import tempfile
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import QTimer


from hyloa.gui.log_window import LogWindow

class DummyApp:
    def __init__(self, logger_path=None):
        self.logger_path = logger_path


def test_initialization(qtbot):
    app = DummyApp()
    widget = LogWindow(app)
    qtbot.addWidget(widget)

    assert widget.isReadOnly()
    assert widget.styleSheet() != ""
    assert widget.timer.isActive()
    assert widget.last_line_count == 0


def test_update_log_no_path(qtbot):
    app = DummyApp(logger_path=None)
    widget = LogWindow(app)
    qtbot.addWidget(widget)

    widget.setPlainText("initial")
    widget.update_log()

    assert widget.toPlainText() == "initial"
    assert widget.last_line_count == 0


def test_update_log_new_lines(qtbot):
    # Create a tmp file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        tmp.write("INFO - first line\n")
        tmp.write("DEBUG - second line\n")
        tmp_path = tmp.name

    app = DummyApp(logger_path=tmp_path)
    widget = LogWindow(app)
    qtbot.addWidget(widget)

    widget.update_log()

    # The displayed text should be cleaned after " - "
    assert "first line" in widget.toPlainText()
    assert "second line" in widget.toPlainText()
    assert widget.last_line_count == 2

    os.remove(tmp_path)


def test_update_log_no_new_lines(qtbot):
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        tmp.write("INFO - hello\n")
        tmp_path = tmp.name

    app = DummyApp(logger_path=tmp_path)
    widget = LogWindow(app)
    qtbot.addWidget(widget)

    widget.update_log()
    first_text = widget.toPlainText()

    # No new lines added
    widget.update_log()
    second_text = widget.toPlainText()

    assert first_text == second_text
    assert widget.last_line_count == 1

    os.remove(tmp_path)


def test_update_log_scroll_behavior(qtbot):
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        tmp.write("INFO - line1\n")
        tmp.write("INFO - line2\n")
        tmp.write("INFO - line3\n")
        tmp_path = tmp.name

    app = DummyApp(logger_path=tmp_path)
    widget = LogWindow(app)
    qtbot.addWidget(widget)

    # first update
    widget.update_log()

    # scroll to top
    sb = widget.verticalScrollBar()
    sb.setValue(0)

    with open(tmp_path, "a") as f:
        f.write("INFO - new line\n")

    widget.update_log()
    # scrollbar should remain at top
    assert sb.value() == 0

    os.remove(tmp_path)


def test_update_log_error_handling(qtbot):
    # Non-existent file path should trigger error handling
    app = DummyApp(logger_path="/nonexistent/path/log.txt")
    widget = LogWindow(app)
    qtbot.addWidget(widget)

    widget.update_log()

    assert "[Error]" in widget.toPlainText()
