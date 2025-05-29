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
test for logger
"""
import time
import pytest
import logging
from hyloa.utils.logging_setup import setup_logging, start_logging

# Test setup_logging() to ensure it creates a file and logs messages to it
def test_setup_logging(tmp_path):
    # Define a temporary log file path
    log_file = tmp_path / "test.log"

    # Setup the logger with this path
    setup_logging(str(log_file))

    # Get the root logger and write a test message
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info("Test message")

    # Give the file system a moment to write (sometimes needed on CI)
    time.sleep(0.1)

    # Flush all handlers to ensure writing is complete
    for handler in logger.handlers:
        handler.flush()

    # Assert the file exists and contains the test message
    assert log_file.exists(), "Log file was not created"
    content = log_file.read_text()
    assert "Test message" in content, "Log message not found in file"

    with pytest.raises(Exception) as e_info:
        setup_logging(7)


# Test start_logging() with QFileDialog mocked to return a known path
def test_start_logging_success(monkeypatch, tmp_path):
    selected_file = tmp_path / "selected.log"

    # Mock QFileDialog.getSaveFileName to return a known path
    monkeypatch.setattr(
        "PyQt5.QtWidgets.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(selected_file), None)
    )

    # Mock QMessageBox methods to avoid GUI interruption
    monkeypatch.setattr("PyQt5.QtWidgets.QMessageBox.information", lambda *args, **kwargs: None)
    monkeypatch.setattr("PyQt5.QtWidgets.QMessageBox.critical", lambda *args, **kwargs: None)

    # Create a fake app object with a logger attribute
    class FakeApp:
        def __init__(self):
            self.logger = None
    app = FakeApp()

    # Call start_logging, which should assign the logger and create the file
    start_logging(app)

    # Write a log message to trigger file creation
    app.logger.info("Test entry for file creation")

    time.sleep(0.1)
    for handler in app.logger.handlers:
        handler.flush()

    # Assert the log file was created and contains the test message
    assert selected_file.exists(), "Selected log file was not created"
    content = selected_file.read_text()
    assert "Test entry for file creation" in content, "Expected log content missing"

    # Test for existing logger
    start_logging(app)

    # Test invalid file
    selected_file = False
    # Mock QFileDialog.getSaveFileName to return a known path
    monkeypatch.setattr(
        "PyQt5.QtWidgets.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (selected_file, None)
    )
    app = FakeApp()
    start_logging(app)

