import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QTextCursor
from hyloa.gui.log_window import LogWindow 

@pytest.fixture
def fake_app_with_log_path(tmp_path):
    class FakeApp:
        def __init__(self, log_file_path):
            self.logger_path = log_file_path

    # Create a temporary log file
    log_file = tmp_path / "log.txt"
    log_file.write_text("INFO - First log line\n")

    return FakeApp(str(log_file))

def test_logwindow_initialization(qtbot, fake_app_with_log_path):
    log_widget = LogWindow(fake_app_with_log_path)
    qtbot.addWidget(log_widget)
    assert log_widget.isReadOnly()
    assert log_widget.app_instance.logger_path.endswith("log.txt")
    assert isinstance(log_widget.timer, QTimer)

def test_logwindow_updates_on_new_log(qtbot, fake_app_with_log_path):
    log_widget = LogWindow(fake_app_with_log_path)
    qtbot.addWidget(log_widget)

    # First update
    log_widget.update_log()
    assert "First log line" in log_widget.toPlainText()
    assert log_widget.last_line_count == 1

    # Append new line to file
    with open(fake_app_with_log_path.logger_path, "a") as f:
        f.write("DEBUG - Second line\n")

    # Second update
    log_widget.update_log()
    content = log_widget.toPlainText()
    assert "Second line" in content
    assert log_widget.last_line_count == 2

def test_logwindow_ignores_if_no_new_lines(qtbot, fake_app_with_log_path):
    log_widget = LogWindow(fake_app_with_log_path)
    qtbot.addWidget(log_widget)

    log_widget.update_log()
    content_before = log_widget.toPlainText()
    log_widget.update_log()
    content_after = log_widget.toPlainText()

    # No change since no new lines were written
    assert content_before == content_after

def test_logwindow_handles_file_error(qtbot):
    class FakeApp:
        logger_path = "non_existent_log_file.txt"

    log_widget = LogWindow(FakeApp())
    qtbot.addWidget(log_widget)

    log_widget.update_log()

    assert "[Errore]" in log_widget.toPlainText()

def test_scroll_behavior(qtbot, fake_app_with_log_path, mocker):
    log_widget = LogWindow(fake_app_with_log_path)
    qtbot.addWidget(log_widget)

    scrollbar_mock = mocker.patch.object(log_widget, "verticalScrollBar")
    mock_scrollbar = mocker.MagicMock()
    mock_scrollbar.value.return_value = 100
    mock_scrollbar.maximum.return_value = 100
    scrollbar_mock.return_value = mock_scrollbar

    cursor_mock = mocker.patch.object(log_widget, "moveCursor")

    log_widget.update_log()
    cursor_mock.assert_called_once_with(QTextCursor.End)
