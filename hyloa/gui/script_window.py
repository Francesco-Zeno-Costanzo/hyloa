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
import numpy as np

from PyQt5.QtCore import QRegExp, QSize, Qt, QRect
from PyQt5.QtGui import (
    QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QPainter,
    QTextFormat
)
from PyQt5.QtWidgets import ( 
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
    QPlainTextEdit, QFileDialog, QMessageBox, QTextEdit
)


class ScriptEditor(QPlainTextEdit):
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
        self.line_number_area = LineNumberArea(self)

        self.setFont(QFont("Courier", 10))
        self.setPlaceholderText("# Scrivi qui il tuo script Python...")
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.highlighter = PythonHighlighter(self.document())

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # Layout (buttons)
        self.window = QWidget()
        self.window.setWindowTitle("Editor di Script Python")
        layout = QVBoxLayout(self.window)

        layout.addWidget(self)

        button_layout = QHBoxLayout()
        for text, slot in [
            ("Esegui Script", self.run_script),
            ("Salva Script", self.save_script),
            ("Carica Script", self.load_script)
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            button_layout.addWidget(btn)

        layout.addLayout(button_layout)
        self.window.setLayout(layout)


    def run_script(self):
        ''' Function to run the script
        '''
        script_text = self.toPlainText()

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

        for idx, df in enumerate(self.app_instance.dataframes):
            for column in df.columns:
                if column in shell.local_vars:
                    modified_array = shell.local_vars[column]
                    if not np.array_equal(df[column].values, modified_array):
                        df[column] = modified_array

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
                    f.write(self.toPlainText())
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
                    self.setPlainText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "Errore", str(e))
    
    def line_number_area_width(self):
        '''
        Calculate the width required for the line number area.

        Returns
        -------
        space : int
            The width in pixels needed to display the line numbers
            based on the current number of text blocks (lines).
        '''
        digits = len(str(self.blockCount()))
        space  = 3 + self.fontMetrics().width('9') * digits
        return space

    def update_line_number_area_width(self, _):
        '''
        Update the viewport margins to account for the line number area width.

        Parameters
        ----------
        _ : Any
            Unused parameter, often a placeholder for a signal.
        '''
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        '''
        Update the display of the line number area
        when the editor is scrolled or updated.

        Parameters
        ----------
        rect : QRect
            The region of the editor that needs updating.
        dy : int
            The number of pixels the view was vertically scrolled by
        '''
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        '''
        Handle resize events and reposition the line number area accordingly.

        Parameters
        ----------
        event : QResizeEvent
            The event triggered when the editor is resized.
        '''
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint(self, event):
        '''
        Paint the line number area.

        Parameters
        ----------
        event : QPaintEvent
            The paint event containing the area to be redrawn.

        Notes
        -----
        This method paints line numbers aligned to the right of the line number area,
        highlighting only visible blocks.
        '''
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#f0f0f0"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.line_number_area.width(), self.fontMetrics().height(),
                                Qt.AlignRight, number)

            block  = block.next()
            top    = bottom
            bottom = top + int(self.blockBoundingRect(block).height()
            )
            block_number += 1

    def highlight_current_line(self):
        '''
        Highlight the background of the current line where the cursor is.

        Notes
        -----
        Applies a translucent yellow background to the current line to help visually
        locate the text cursor position. This does not affect the selection state.
        '''
        extra_selections = []
        if not self.isReadOnly():
            selection  = QTextEdit.ExtraSelection()
            line_color = QColor(Qt.yellow).lighter(160)
            line_color.setAlpha(100)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)



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
            r"\bfinally\b", r"\blambda\b",
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


class LineNumberArea(QWidget):
    """
    A QWidget that displays line numbers for a code editor.

    This widget is used to provide a visual line number area on the left.
    """
    def __init__(self, editor):
        '''
        Initialize the line number area.

        Parameters
        ----------
        editor : QWidget
            The code editor widget to which this line number area is attached.
        '''
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        '''
        Return the recommended size for the line number area.

        Returns
        -------
        QSize
            The preferred width calculated by the code editor and a height of 0.
        '''
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        '''
        Paint the contents of the line number area.

        Parameters
        ----------
        event : QPaintEvent
            The paint event containing the region to be updated.

        Notes
        -----
        This method delegates the painting logic to the parent code editor's
        `line_number_area_paint` method.
        '''
        self.code_editor.line_number_area_paint(event)
