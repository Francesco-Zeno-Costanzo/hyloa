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
            try :
                with open(self.app_instance.logger_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                with open(self.app_instance.logger_path, "r", encoding="cp1252") as f:
                    lines = f.readlines()
            
            if len(lines) == self.last_line_count:
                return

            # Show only new lines
            new_lines = lines[self.last_line_count:]
            self.last_line_count = len(lines)

            cleaned = [line.split(" INFO - ")[-1] for line in new_lines]

            # Scroll on bottom
            scrollbar = self.verticalScrollBar()
            at_bottom = scrollbar.value() == scrollbar.maximum()

            self.appendPlainText("".join(cleaned))

            if at_bottom:
                self.moveCursor(QTextCursor.End)

        except Exception as e:
            self.appendPlainText(f"\n[Error] {e}")
