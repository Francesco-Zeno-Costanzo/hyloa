import time
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

