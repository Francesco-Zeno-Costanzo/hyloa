"""
Code for creation of the log panel in the main window
"""
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QPlainTextEdit


class LogWindow(QPlainTextEdit):
    ''' Class to handle the log panel
    '''
    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance
        self.setReadOnly(True)
        self.setStyleSheet("background-color: white; color: black; font-family: monospace;")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_log)
        self.timer.start(1000)    # Update each seconds

        self.last_line_count = 0  # track last line shown

    def update_log(self):
        ''' Function that update the window
        '''
        if not self.app_instance.logger_path:
            return

        try:
            with open(self.app_instance.logger_path, "r") as f:
                lines = f.readlines()

            if len(lines) == self.last_line_count:
                return

            # Show only new lines
            new_lines = lines[self.last_line_count:]
            self.last_line_count = len(lines)

            cleaned = [line.split(" - ")[-1] for line in new_lines]

            # Scroll on bottom
            scrollbar = self.verticalScrollBar()
            at_bottom = scrollbar.value() == scrollbar.maximum()

            self.appendPlainText("".join(cleaned))

            if at_bottom:
                self.moveCursor(QTextCursor.End)

        except Exception as e:
            self.appendPlainText(f"\n[Errore] {e}")
