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
Code to manage the window where you can
run code to make changes to the data
"""

import io
import sys
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit
)
from PyQt5.QtCore import Qt

from scipy.special import *
from scipy.optimize import *
import matplotlib.pyplot as plt

class ShellEditor(QTextEdit):
    ''' Class for wrinting in the shell
    '''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFontFamily("Courier")
        self.setFontPointSize(10)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setText(">>> ")

    def keyPressEvent(self, event):
        ''' Function to handle events from key pressing
        '''
        cursor = self.textCursor() 
        cursor_pos = cursor.position()
        prompt_pos = self.toPlainText().rfind(">>> ") + 4

        # Protection against Backspace and Delete on the prompt
        if cursor_pos <= prompt_pos and event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            return 

        # Block left arrow cursor movement before prompt
        if cursor_pos <= prompt_pos and event.key() == Qt.Key_Left:
            return

        # If I type before the prompt, I go back to the end of the text
        if cursor_pos < prompt_pos:
            cursor.setPosition(len(self.toPlainText()))
            self.setTextCursor(cursor)

        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        ''' Function to handle events from mouse pressing
        '''
        cursor = self.cursorForPosition(event.pos())
        cursor_pos = cursor.position()
        prompt_pos = self.toPlainText().rfind(">>> ") + 4

        if cursor_pos < prompt_pos:
            # Force cursor after prompt
            cursor.setPosition(len(self.toPlainText()))
            self.setTextCursor(cursor)
        else:
            super().mousePressEvent(event)


class CommandWindow(QWidget):
    ''' 
    Class for all the window, 
    for comand history navigation and evaluation
    '''

    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance
        self.dataframes = app_instance.dataframes
        self.fit_results = app_instance.fit_results
        self.logger = app_instance.logger

        self.setWindowTitle("Python shell")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Only in-line command", self))

        self.shell_text = ShellEditor(self)
        layout.addWidget(self.shell_text)

        self.local_vars = self._initialize_local_vars()
        self.command_history = []
        self.history_index = -1

        self.shell_text.installEventFilter(self)
        self.shell_text.moveCursor(self.shell_text.textCursor().End)

    def _initialize_local_vars(self):
        ''' Function to initialize the varibales konwn by the shell
        '''
        local_vars = {}

        for idx, df in enumerate(self.dataframes):
            for column in df.columns:
                local_vars[column] = df[column].astype(float).values

        local_vars.update(self.fit_results)
        return local_vars

    def refresh_variables(self):
        ''' Function to update the varibales konwn by the shell
        '''
        self.local_vars.clear()

        for idx, df in enumerate(self.app_instance.dataframes):
            for column in df.columns:
                self.local_vars[column] = df[column].astype(float).values

        self.local_vars.update(self.app_instance.fit_results)


    def eventFilter(self, obj, event):
        ''' Handle switch for navigation in command's history or execute command
        '''
        if obj is self.shell_text:
            if event.type() == event.KeyPress:
                key = event.key()

                if key == Qt.Key_Return:
                    self.execute_command()
                    return True

                elif key == Qt.Key_Up:
                    self.navigate_history(-1)
                    return True

                elif key == Qt.Key_Down:
                    self.navigate_history(1)
                    return True

        return super().eventFilter(obj, event)

    def execute_command(self):
        ''' Function that execute the command
        '''
        text = self.shell_text.toPlainText()
        last_prompt = text.rfind(">>> ")
        command = text[last_prompt + 4:].strip()

        if not command:
            self.shell_text.append(">>> ")
            return

        self.command_history.append(command)
        self.history_index = len(self.command_history)

        if self.logger:
            self.logger.info(f"Execution of the command: {command}")

        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = output_capture = io.StringIO()
        sys.stderr = output_capture

        try:
            # First try to execute as expression
            try:
                code = compile(command, "<input>", "eval")
                res  = eval(code, globals(), self.local_vars)

                if res is not None:
                    print(repr(res))
            except SyntaxError:
                # If not possible, execute as statement
                exec(command, globals(), self.local_vars)

            output = output_capture.getvalue()

        except Exception as e:
            output = f"Error: {str(e)}\n"
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

        # Update dataframes with modified variables
        for idx, df in enumerate(self.dataframes):
            for column in df.columns:
                if column in self.local_vars:
                    modified_array = self.local_vars[column]
                    if not np.array_equal(df[column].values, modified_array):
                        df[column] = modified_array

        self.shell_text.append(output)
        self.shell_text.append(">>> ")
        self.shell_text.moveCursor(self.shell_text.textCursor().End)

    def navigate_history(self, direction):
        ''' Function for navigating in all command's history
        '''
        if not self.command_history:
            return

        self.history_index += direction
        self.history_index = max(0, min(self.history_index, len(self.command_history) - 1))

        command = self.command_history[self.history_index]

        text = self.shell_text.toPlainText()
        last_prompt = text.rfind(">>> ")
        new_text = text[:last_prompt + 4] + command
        self.shell_text.setText(new_text)
        self.shell_text.moveCursor(self.shell_text.textCursor().End)
    
    def append_text(self, text):
        cursor = self.shell_text.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        self.shell_text.setTextCursor(cursor)
        self.shell_text.ensureCursorVisible()

