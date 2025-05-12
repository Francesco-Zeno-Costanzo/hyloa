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
from PyQt5.QtWidgets import ( QWidget, QVBoxLayout, QPushButton,
                              QPlainTextEdit, QFileDialog, QMessageBox,
                              QHBoxLayout
)


class ScriptEditor(QWidget):
    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance

        self.setWindowTitle("Editor di Script Python")

        layout = QVBoxLayout(self)

        self.editor = QPlainTextEdit(self)
        self.editor.setPlaceholderText("# Scrivi qui il tuo script Python...")
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
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
        path, _ = QFileDialog.getOpenFileName(self, "Carica Script", "", "Python Files (*.py)")
        if path:
            try:
                with open(path, 'r') as f:
                    self.editor.setPlainText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "Errore", str(e))
