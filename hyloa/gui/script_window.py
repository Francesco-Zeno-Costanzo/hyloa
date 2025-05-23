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
Code for manage script's window
"""
import io
import sys

from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt5.QtWidgets import ( 
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
    QPlainTextEdit, QFileDialog, QMessageBox,
)

class ScriptEditor(QWidget):
    ''' Class to handle the scripting window
    '''
    def __init__(self, app_instance):
        ''' 
        Parameters
        ----------
        app_instance : MainApp
            Main application instance containing the session data.
        '''
        super().__init__()
        self.app_instance = app_instance

        self.setWindowTitle("Editor di Script Python")

        layout = QVBoxLayout(self)

        self.editor = QPlainTextEdit(self)
        self.editor.setFont(QFont("Courier", 10))
        self.editor.setPlaceholderText("# Scrivi qui il tuo script Python...")
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.highlighter = PythonHighlighter(self.editor.document())
        layout.addWidget(self.editor)

        # Buttons
        button_layout = QHBoxLayout()

        run_button = QPushButton("Esegui Script", self)
        run_button.clicked.connect(self.run_script)
        button_layout.addWidget(run_button)

        save_button = QPushButton("Salva Script", self)
        save_button.clicked.connect(self.save_script)
        button_layout.addWidget(save_button)

        load_button = QPushButton("Carica Script", self)
        load_button.clicked.connect(self.load_script)
        button_layout.addWidget(load_button)

        layout.addLayout(button_layout)


    def run_script(self):
        ''' Function to run the script
        '''
        script_text = self.editor.toPlainText()

        # Find the shell of the app
        shell = self.app_instance.shell_widget if hasattr(self.app_instance, 'shell_widget') else None
        if not shell:
            QMessageBox.critical(self, "Errore", "Shell non trovata.")
            return

        # Redirection of standard output and error
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = output_capture = io.StringIO()
        sys.stderr = output_capture

        try:
            exec(script_text, globals(), shell.local_vars)
        except Exception as e:
            output_capture.write(f"\nErrore: {str(e)}\n")
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        output = output_capture.getvalue()

        if output.strip():
            # Write over the prompt
            text = shell.shell_text.toPlainText()
            last_prompt_index = text.rfind(">>> ")

            if last_prompt_index != -1:
                # Take all except the prompt
                before_prompt = text[:last_prompt_index]

                # Build the final output
                new_text = before_prompt + output + "\n>>> "

                # Overwrite in the shell
                shell.shell_text.setPlainText(new_text)
                shell.shell_text.moveCursor(shell.shell_text.textCursor().End)



    def save_script(self):
        ''' Function for save the script
        '''
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salva Script",
            "",
            "Python Files (*.py)",
            options=QFileDialog.Options()
        )

        if path:
            if not path.endswith(".py"):
                path += ".py"
            try:
                with open(path, 'w') as f:
                    f.write(self.editor.toPlainText())
                QMessageBox.information(self, "Salvato", f"Script salvato in:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Errore", str(e))

    def load_script(self):
        ''' Function to load a pre written script
        '''
        path, _ = QFileDialog.getOpenFileName(self, "Carica Script", "", "Python Files (*.py)")
        if path:
            try:
                with open(path, 'r') as f:
                    self.editor.setPlainText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "Errore", str(e))


class PythonHighlighter(QSyntaxHighlighter):
    ''' Class to adorn script window with highliter
    '''
    def __init__(self, document):
        '''
        Initializes the syntax highlighter with Python-specific highlighting rules.

        Defines formatting for keywords, strings, single-line comments, and 
        multi-line string blocks using regular expressions and `QTextCharFormat`.
        The highlighter supports highlighting of Python constructs such as 
        keywords (`def`, `class`, etc.), quoted strings, `#` comments, and 
        multi-line string literals using triple quotes.

        Parameters
        ----------
        document : QTextDocument
            The text document to which the syntax highlighting will be applied.
        '''
        super().__init__(document)

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("blue"))
        keyword_format.setFontWeight(QFont.Bold)

        keyword_patterns = [
            r"\bdef\b", r"\bclass\b", r"\breturn\b", r"\bif\b", r"\belse\b",
            r"\belif\b", r"\bwhile\b", r"\bfor\b", r"\bin\b", r"\bimport\b",
            r"\bfrom\b", r"\bas\b", r"\bpass\b", r"\bNone\b", r"\bTrue\b", r"\bFalse\b",
            r"\band\b", r"\bnot\b", r"\bor\b", r"\bwith\b", r"\btry\b", r"\bexcept\b",
            r"\bfinally\b",
        ]

        self.highlighting_rules = [(QRegExp(pattern), keyword_format) for pattern in keyword_patterns]

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("darkGreen"))
        self.highlighting_rules.append((QRegExp(r'"[^"]*"'), string_format))
        self.highlighting_rules.append((QRegExp(r"'[^']*'"), string_format))

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("darkGray"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegExp(r"#.*"), comment_format))

        #self.triple_single = QRegExp(r"\'\'\'")
        self.triple_double = QRegExp(r'"""')

        self.multi_line_format = QTextCharFormat()
        self.multi_line_format.setForeground(QColor("darkGray"))
        self.multi_line_format.setFontItalic(True)

    def highlightBlock(self, text):
        '''
        Applies syntax highlighting to a single block of text.

        This method highlights all matching patterns defined in 
        `self.highlighting_rules` as well as multi-line string blocks 
        (e.g., delimited by triple single or double quotes). It is 
        intended to be called automatically by the QSyntaxHighlighter 
        for each block of text.

        Parameters
        ----------
        text : str
            The block of text to be highlighted.
        '''
        # Simple highlighting
        for pattern, fmt in self.highlighting_rules:
            index = pattern.indexIn(text)
            while index >= 0:
                length = pattern.matchedLength()
                self.setFormat(index, length, fmt)
                index = pattern.indexIn(text, index + length)

        # Multi-line highlighting '''...'''
        self.setCurrentBlockState(0)

        #self.highlight_multiline(text, self.triple_single, self.triple_single, self.multi_line_format)
        self.highlight_multiline(text, self.triple_double, self.triple_double, self.multi_line_format)

    def highlight_multiline(self, text, start_expr, end_expr, format):
        '''
        Applies formatting to multi-line text sections matching given delimiters.

        Highlights text between `start_expr` and `end_expr`, which can span 
        multiple blocks (e.g., for triple-quoted strings). If the end delimiter 
        is not found in the current block, the state is set to continue 
        highlighting in the next block.

        Parameters
        ----------
        text : str
            The current block of text to search for multi-line expressions.
        start_expr : QRegExp
            Regular expression defining the start of the multi-line section.
        end_expr : QRegExp
            Regular expression defining the end of the multi-line section.
        format : QTextCharFormat
            The text format to apply to the matched multi-line section.
        '''
        # Previous state: 1 = inside a multi-line block
        if self.previousBlockState() == 1:
            start_index = 0
        else:
            start_index = start_expr.indexIn(text)

        while start_index >= 0:
           
            if self.previousBlockState() == 1:
                end_index = end_expr.indexIn(text)
                if end_index >= 0:
                    end_index += end_expr.matchedLength()
                    self.setCurrentBlockState(0)
                else:
                    end_index = len(text)
                    self.setCurrentBlockState(1)
            else:
                end_index = end_expr.indexIn(text, start_index + start_expr.matchedLength())
                if end_index >= 0:
                    end_index += end_expr.matchedLength()
                    self.setCurrentBlockState(0)
                else:
                    self.setCurrentBlockState(1)
                    end_index = len(text)

            length = end_index - start_index
            self.setFormat(start_index, length, format)

            # Find another block in the same row
            if self.currentBlockState() == 1:
                break
            start_index = start_expr.indexIn(text, end_index)